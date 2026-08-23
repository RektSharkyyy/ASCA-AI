"""
Domain Intent Guardrail - Binary Intent Classifier
Filters queries by business domain scope (invoices, clients, financial reports for Sri Lankan agriculture)
with fail-open strategy for network failures.
"""

from typing import Literal, Optional
from enum import Enum
from pydantic import BaseModel, Field
from src.infrastructure.logging import logger
from src.infrastructure.llm_loader import get_llm

# Static refusal message for out-of-scope queries
OUT_OF_SCOPE_REPLY = """
I'm specialized in Sri Lankan agricultural supply chain advisory, focusing on:
- Market price forecasting for crops at Dambulla and Thambuththegama economic centers
- Surplus detection and B2B buyer matching
- Agricultural invoice and client management
- Financial reports for farmers and processing plants

Your question appears to be outside my domain expertise. Please ask about agricultural market insights, crop pricing, or supply chain advisory for Sri Lankan farmers.
"""


class IntentClassification(str, Enum):
    """Binary classification for query intent."""
    IN_SCOPE = "in_scope"
    OUT_OF_SCOPE = "out_of_scope"


class IntentResult(BaseModel):
    """Result of intent classification."""
    classification: IntentClassification
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0.0 to 1.0")
    reasoning: Optional[str] = Field(default=None, description="Brief explanation of classification")


class DomainGuardrail:
    """
    Fast binary intent classifier using lightweight LLM (Llama 3.1 8B or GPT-4o-mini).
    Implements fail-open strategy: network failures default to 'in_scope' to avoid blocking legitimate users.
    """

    def __init__(
        self,
        provider: str = "openrouter",
        model_name: str = "meta-llama/llama-3.1-8b-instruct",
        fail_open: bool = True
    ):
        """
        Initialize Domain Guardrail with lightweight model.
        
        Args:
            provider: LLM provider (openrouter, openai, google)
            model_name: Specific model for intent classification
            fail_open: If True, defaults to 'in_scope' on errors (safety for legitimate users)
        """
        self.provider = provider
        self.model_name = model_name
        self.fail_open = fail_open
        self.llm = None
        
        # Business domain keywords for fast pre-filtering
        self.in_scope_keywords = {
            # Core domain
            "crop", "tomato", "carrot", "beans", "vegetable", "fruit", "harvest",
            "price", "market", "wholesale", "dambulla", "thambuththegama",
            "surplus", "forecast", "supply", "demand", "buyer", "farmer",
            # Financial/Business
            "invoice", "client", "payment", "financial", "report", "revenue",
            "factory", "processing", "b2b", "matcher", "advisory",
            # Sri Lankan context
            "lanka", "sri lanka", "lkr", "rupee", "economic center"
        }
        
        self.out_of_scope_keywords = {
            # General knowledge
            "coding", "programming", "python", "javascript", "debug",
            "movie", "song", "recipe",
            "history", "geography", "physics", "chemistry",
            # Unrelated domains
            "car", "vehicle", "travel", "hotel", "flight",
            "sports", "football", "cricket"
        }

        # Greetings and pleasantries are ALWAYS in-scope: they are served by the
        # `direct` route of the DirectAgent, not refused as off-domain.
        self.greeting_keywords = {
            "hi", "hii", "hey", "hello", "helo", "yo", "hiya",
            "thanks", "thank you", "thankyou", "ty", "cheers",
            "bye", "goodbye", "good bye", "see you",
            "good morning", "good afternoon", "good evening", "good night",
            "how are you", "how r u", "whats up", "what's up", "sup",
            "ok", "okay", "cool", "nice", "great", "awesome",
            "who are you", "what can you do", "help",
            # Sinhala transliterations commonly typed by users
            "ayubowan", "stuti", "istuti", "hari", "hondai",
        }

    def _lazy_load_llm(self):
        """Lazy load LLM only when needed (saves initialization time)."""
        if self.llm is None:
            try:
                self.llm = get_llm(
                    provider=self.provider,
                    model_name=self.model_name,
                    temperature=0.0  # Deterministic classification
                )
                logger.info(f"Domain Guardrail loaded LLM: {self.provider}/{self.model_name}")
            except Exception as e:
                logger.error(f"Failed to load LLM for Domain Guardrail: {str(e)}")
                if not self.fail_open:
                    raise

    def _fast_keyword_check(self, query: str) -> Optional[IntentClassification]:
        """
        Fast keyword-based pre-filter before expensive LLM call.
        Returns classification if confident, None if uncertain (requires LLM).
        """
        query_lower = " ".join((query or "").lower().split())
        stripped = query_lower.strip(" .!?,")

        # Greetings / pleasantries are always in-scope (handled by the `direct` route)
        if stripped in self.greeting_keywords:
            logger.info("Fast keyword match: IN_SCOPE (greeting/pleasantry)")
            return IntentClassification.IN_SCOPE
        if len(stripped.split()) <= 4 and any(stripped.startswith(g) for g in self.greeting_keywords):
            logger.info("Fast keyword match: IN_SCOPE (short greeting phrase)")
            return IntentClassification.IN_SCOPE

        # Count keyword matches
        in_scope_matches = sum(1 for kw in self.in_scope_keywords if kw in query_lower)
        out_scope_matches = sum(1 for kw in self.out_of_scope_keywords if kw in query_lower)
        
        # Strong signal: 3+ in-scope keywords, no out-of-scope
        if in_scope_matches >= 3 and out_scope_matches == 0:
            logger.info(f"Fast keyword match: IN_SCOPE (matches={in_scope_matches})")
            return IntentClassification.IN_SCOPE
        
        # Strong signal: 2+ out-of-scope keywords, no in-scope
        if out_scope_matches >= 2 and in_scope_matches == 0:
            logger.info(f"Fast keyword match: OUT_OF_SCOPE (matches={out_scope_matches})")
            return IntentClassification.OUT_OF_SCOPE
        
        # Uncertain - requires LLM
        return None

    def _classify_with_llm(self, query: str) -> IntentResult:
        """
        Uses lightweight LLM to classify query intent.
        Implements fail-open: returns IN_SCOPE on network errors.
        """
        self._lazy_load_llm()
        
        if self.llm is None:
            # Fail-open: assume in_scope if LLM unavailable
            logger.warning("LLM unavailable, failing open to IN_SCOPE")
            return IntentResult(
                classification=IntentClassification.IN_SCOPE,
                confidence=0.5,
                reasoning="LLM unavailable, defaulted to in_scope (fail-open strategy)"
            )

        system_prompt = """You are a binary intent classifier for an Agricultural Supply Chain Advisory AI serving Sri Lankan farmers.

**IN-SCOPE queries:**
- Crop prices, market forecasting, harvest planning
- Surplus detection, B2B buyer matching, processing plants
- Agricultural invoices, client management, financial reports for farmers
- Economic centers (Dambulla, Thambuththegama), supply chain advisory
- Vegetable/fruit markets in Sri Lanka
- Greetings, thanks, small talk and questions about what you can do
- Real-time info that affects farming economics (exchange rates, tax/government
  updates, fuel or fertilizer prices, weather and monsoon forecasts)

**OUT-OF-SCOPE queries:**
- General coding, programming help, debugging
- World news, trivia, entertainment, recipes
- Unrelated domains: travel, sports, vehicles, general education

Respond ONLY with JSON:
{
  "classification": "in_scope" or "out_of_scope",
  "confidence": 0.0 to 1.0,
  "reasoning": "brief explanation"
}"""

        try:
            response = self.llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Classify this query:\n\n{query}"}
            ])
            
            raw_text = getattr(response, "content", str(response)).strip()
            
            # Parse JSON response
            import json
            # Clean markdown if present
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(raw_text)
            result = IntentResult(**data)
            
            logger.info(f"LLM classified query as {result.classification.value} (confidence={result.confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Domain Guardrail LLM error: {str(e)}")
            
            if self.fail_open:
                # Fail-open: assume legitimate user query
                logger.warning("Failing open to IN_SCOPE due to LLM error")
                return IntentResult(
                    classification=IntentClassification.IN_SCOPE,
                    confidence=0.5,
                    reasoning=f"LLM error, defaulted to in_scope: {str(e)}"
                )
            else:
                # Fail-closed: reject on error
                return IntentResult(
                    classification=IntentClassification.OUT_OF_SCOPE,
                    confidence=1.0,
                    reasoning=f"System error: {str(e)}"
                )

    def check_intent(self, query: str) -> IntentResult:
        """
        Main entry point: classifies query as in_scope or out_of_scope.
        Uses fast keyword pre-filter, then LLM if needed.
        
        Args:
            query: User's input query
            
        Returns:
            IntentResult with classification and confidence
        """
        if not query or not query.strip():
            return IntentResult(
                classification=IntentClassification.OUT_OF_SCOPE,
                confidence=1.0,
                reasoning="Empty query"
            )
        
        # Try fast keyword match first
        quick_result = self._fast_keyword_check(query)
        if quick_result is not None:
            return IntentResult(
                classification=quick_result,
                confidence=0.9,
                reasoning="Matched domain keywords"
            )
        
        # Fall back to LLM classification
        return self._classify_with_llm(query)

    def should_proceed(self, query: str) -> bool:
        """
        Convenience method: returns True if query is in_scope.
        Use this to short-circuit downstream processing.
        
        Example:
            if not guardrail.should_proceed(user_query):
                return OUT_OF_SCOPE_REPLY
        """
        result = self.check_intent(query)
        return result.classification == IntentClassification.IN_SCOPE


# Singleton instance
domain_guardrail = DomainGuardrail(
    provider="openrouter",
    model_name="meta-llama/llama-3.1-8b-instruct",
    fail_open=True
)
