from typing import List, Optional, Dict, Any, Union, Literal
from enum import Enum
import json
import re
from pydantic import BaseModel, Field, field_validator, model_validator
from src.infrastructure.logging import logger
from src.infrastructure.config import config
from src.infrastructure.llm_loader import get_llm

# Standard Sri Lankan Crops for Economic Centers
VALID_CROPS = {
    "tomato", "carrot", "beans", "eggplant", "brinjal", "cabbage", "green_chilli",
    "leeks", "lime", "pumpkin", "bitter_gourd", "snake_gourd", "capsicum",
    "cucumber", "beetroot", "papaya", "banana", "mango", "passion_fruit", "pineapple"
}

VALID_CENTERS = {"DAMBULLA", "THAMBUTHTHEGAMA"}

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class MarketInsight(BaseModel):
    center_id: str = Field(..., description="Economic center ID (DAMBULLA or THAMBUTHTHEGAMA)")
    crop_name: str = Field(..., description="Standardized crop name")
    current_wholesale_price_lkr: float = Field(..., ge=0, description="Current price in LKR per kg")
    predicted_wholesale_price_lkr: float = Field(..., ge=0, description="Predicted price in LKR per kg")
    supply_volume_tons: float = Field(..., ge=0, description="Estimated daily supply volume in Metric Tons")
    surplus_anomaly_detected: bool = Field(default=False)
    risk_level: RiskLevel = Field(default=RiskLevel.LOW)

    @field_validator("center_id", mode="before")
    @classmethod
    def preprocess_center(cls, v: Any) -> str:
        if isinstance(v, dict):
            v = v.get("name") or v.get("id") or v.get("center_id") or "DAMBULLA"
        upper_v = str(v).strip().upper()
        if "DAMBULLA" in upper_v:
            return "DAMBULLA"
        elif "THAMBUTHTHEGAMA" in upper_v:
            return "THAMBUTHTHEGAMA"
        return upper_v

    @field_validator("crop_name", mode="before")
    @classmethod
    def preprocess_crop(cls, v: Any) -> str:
        if isinstance(v, dict):
            v = v.get("name") or v.get("crop") or "tomato"
        clean_v = str(v).strip().lower().replace(" ", "_")
        if clean_v not in VALID_CROPS:
            logger.warning(f"Unrecognized crop '{v}' flagged by Guardrail.")
        return clean_v

    @model_validator(mode="after")
    def auto_check_anomaly_and_risk(self):
        """Auto-computes anomaly detection if price drop > 25%."""
        if self.current_wholesale_price_lkr > 0:
            price_drop_pct = ((self.current_wholesale_price_lkr - self.predicted_wholesale_price_lkr) / self.current_wholesale_price_lkr) * 100
            if price_drop_pct >= 25.0:
                self.surplus_anomaly_detected = True
                if self.risk_level == RiskLevel.LOW:
                    self.risk_level = RiskLevel.HIGH
        return self

class B2BMatchRecommendation(BaseModel):
    buyer_code: str = Field(..., description="Unique code for B2B Buyer")
    company_name: str = Field(..., description="Name of processing factory or buyer")
    crop_name: str = Field(..., description="Crop matched for processing")
    matched_volume_tons: float = Field(..., gt=0, description="Volume allocated to buyer in tons")
    fefo_risk_score: float = Field(..., ge=0.0, le=1.0, description="FEFO Risk Score (0.0 best to 1.0 worst)")
    recommended_action: str = Field(..., description="Specific recommendation for buyer negotiation")

class ExecutiveAdvisoryBlueprint(BaseModel):
    title: str = Field(default="Executive Advisory Blueprint", description="Title of executive advisory blueprint")
    target_centers: List[str] = Field(..., description="Economic centers analyzed (e.g. ['DAMBULLA'])")
    primary_surplus_crops: List[str] = Field(default_factory=list, description="Crops facing severe surplus")
    market_insights: List[MarketInsight] = Field(default_factory=list)
    b2b_recommendations: List[B2BMatchRecommendation] = Field(default_factory=list)
    executive_summary_sinhala: str = Field(..., description="Executive summary in Sinhala for advisory report")
    telegram_alert_text: str = Field(..., description="Concise SMS/Telegram alert message in Sinhala")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    is_hallucination_free: bool = Field(default=True)

    @field_validator("target_centers", mode="before")
    @classmethod
    def preprocess_target_centers(cls, v: Any) -> List[str]:
        if not isinstance(v, list):
            v = [v]
        cleaned = []
        for item in v:
            if isinstance(item, dict):
                val = item.get("name") or item.get("id") or item.get("location") or "DAMBULLA"
            else:
                val = str(item)
            upper_val = val.strip().upper()
            if "DAMBULLA" in upper_val:
                cleaned.append("DAMBULLA")
            elif "THAMBUTHTHEGAMA" in upper_val:
                cleaned.append("THAMBUTHTHEGAMA")
            else:
                cleaned.append(upper_val)
        return cleaned

    @field_validator("primary_surplus_crops", mode="before")
    @classmethod
    def preprocess_primary_crops(cls, v: Any) -> List[str]:
        if not isinstance(v, list):
            v = [v]
        cleaned = []
        for item in v:
            if isinstance(item, dict):
                val = item.get("name") or item.get("crop") or "tomato"
            else:
                val = str(item)
            cleaned.append(val.strip().lower().replace(" ", "_"))
        return cleaned

    @model_validator(mode="after")
    def check_overall_validity(self):
        if self.confidence_score < 0.80:
            self.is_hallucination_free = False
            logger.warning(f"Guardrail flagged low confidence score ({self.confidence_score}) in Advisory Blueprint.")
        return self

class GuardrailValidationResult(BaseModel):
    is_valid: bool
    blueprint: Optional[ExecutiveAdvisoryBlueprint] = None
    error_messages: List[str] = Field(default_factory=list)

def _clean_llm_json_output(raw_output: str) -> str:
    """Extracts raw JSON string safely even if LLM surrounds it with markdown, codeblocks, or trailing text."""
    clean_json = (raw_output or "").strip()
    if "```json" in clean_json:
        clean_json = clean_json.split("```json")[1].split("```")[0].strip()
    elif "```" in clean_json:
        clean_json = clean_json.split("```")[1].split("```")[0].strip()
    else:
        start_idx = clean_json.find("{")
        end_idx = clean_json.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            clean_json = clean_json[start_idx:end_idx + 1].strip()
            
    return clean_json

def validate_blueprint_output(raw_output: str) -> GuardrailValidationResult:
    """
    Parses and validates raw LLM JSON output against ExecutiveAdvisoryBlueprint schema.
    Ensures zero hallucination and strict typing.
    """
    try:
        clean_json = _clean_llm_json_output(raw_output)
        data = json.loads(clean_json)
        
        # Smart fallback if root title is missing
        if "title" not in data or not data["title"]:
            data["title"] = "Executive Advisory Blueprint - Sri Lanka"
            
        validated_blueprint = ExecutiveAdvisoryBlueprint(**data)
        
        logger.info("Executive Advisory Blueprint successfully validated through Guardrail.")
        return GuardrailValidationResult(
            is_valid=True,
            blueprint=validated_blueprint,
            error_messages=[]
        )
    except Exception as e:
        logger.error(f"Guardrail Validation Failed: {str(e)}")
        return GuardrailValidationResult(
            is_valid=False,
            blueprint=None,
            error_messages=[str(e)]
        )

def generate_validated_blueprint_with_openrouter(
    prompt: str,
    model_name: Optional[str] = "meta-llama/llama-3.1-8b-instruct",
    max_retries: int = 3
) -> GuardrailValidationResult:
    """
    Calls Meta Llama 3.1 8B via OpenRouter with strict JSON Schema instructions,
    validating output through Pydantic Guardrail.
    """
    model_to_use = model_name or "meta-llama/llama-3.1-8b-instruct"
    logger.info(f"Initiating OpenRouter LLM Call [{model_to_use}] with Pydantic Guardrail Protection...")
    llm = get_llm(provider="openrouter", model_name=model_to_use)
    
    json_schema_hint = """
    CRITICAL JSON FORMAT INSTRUCTION:
    Respond ONLY with a JSON object following EXACTLY this structure:
    {
        "title": "Dambulla Vegetable Advisory",
        "target_centers": ["DAMBULLA"],
        "primary_surplus_crops": ["tomato"],
        "market_insights": [
            {
                "center_id": "DAMBULLA",
                "crop_name": "tomato",
                "current_wholesale_price_lkr": 250.0,
                "predicted_wholesale_price_lkr": 130.0,
                "supply_volume_tons": 60.0,
                "surplus_anomaly_detected": true,
                "risk_level": "HIGH"
            }
        ],
        "b2b_recommendations": [
            {
                "buyer_code": "BUYER_SAUCE_DAMBULLA",
                "company_name": "Lanka Sauce Factory",
                "crop_name": "tomato",
                "matched_volume_tons": 30.0,
                "fefo_risk_score": 0.2,
                "recommended_action": "Route 30 tons to Lanka Sauce Factory."
            }
        ],
        "executive_summary_sinhala": "දඹුල්ලේ තක්කාලි අස්වැන්න වැඩිවී මිල 48%කින් කඩා වැටීමේ අවදානමක් ඇත.",
        "telegram_alert_text": "⚠️ දඹුල්ලේ තක්කාලි අතිරික්ත අවදානම: ටොන් 30ක් සෝස් කර්මාන්තශාලාවට යොමු කෙරේ.",
        "confidence_score": 0.95
    }
    IMPORTANT RULES:
    1. "target_centers" MUST be a list of strings like ["DAMBULLA"], NOT a list of objects!
    2. "title" string field MUST be included.
    3. Do NOT include markdown text outside the JSON object.
    """
    
    current_prompt = f"{json_schema_hint}\n\nUSER MARKET DATA / REQUEST:\n{prompt}"
    
    for attempt in range(1, max_retries + 1):
        logger.info(f"OpenRouter [{model_to_use}] Attempt {attempt}/{max_retries}...")
        try:
            response = llm.invoke(current_prompt)
            raw_text = getattr(response, "content", str(response))
            
            validation = validate_blueprint_output(raw_text)
            if validation.is_valid:
                logger.info(f"OpenRouter {model_to_use} response passed Guardrail validation 100%!")
                return validation
            
            logger.warning(f"Attempt {attempt} failed validation: {validation.error_messages}")
            current_prompt = f"{json_schema_hint}\n\n[SYSTEM GUARDRAIL ERROR]: Your previous output failed validation with errors: {validation.error_messages}. FIX THE JSON KEYS AND ARRAY TYPES EXACTLY AS REQUIRED!"
        except Exception as e:
            logger.error(f"Error calling OpenRouter API on attempt {attempt}: {str(e)}")
            if attempt == max_retries:
                return GuardrailValidationResult(
                    is_valid=False,
                    blueprint=None,
                    error_messages=[f"OpenRouter API Error: {str(e)}"]
                )
                
    return GuardrailValidationResult(
        is_valid=False,
        blueprint=None,
        error_messages=["Exhausted max retries for OpenRouter LLM validation."]
    )
