"""
Crop & economic-centre catalogue shared by the API services.

Keeps crop normalisation (`Green Chilli` -> `green_chilli`), display labels and
free-text detection in ONE place so the chat service, market service and B2B
service always agree on identifiers.
"""

from typing import Dict, List, Optional

from src.infrastructure.config import config

# Standard basket scouted by default (matches the frontend crop tabs).
DEFAULT_CROP_BASKET: List[str] = [
    "tomato",
    "carrot",
    "beans",
    "eggplant",
    "cabbage",
    "green_chilli",
]

# Free-text aliases -> canonical snake_case crop key.
# Includes common Sinhala transliterations typed by farmers.
CROP_ALIASES: Dict[str, str] = {
    "tomato": "tomato",
    "tomatoes": "tomato",
    "thakkali": "tomato",
    "carrot": "carrot",
    "carrots": "carrot",
    "beans": "beans",
    "bean": "beans",
    "bonchi": "beans",
    "eggplant": "eggplant",
    "brinjal": "eggplant",
    "wambatu": "eggplant",
    "cabbage": "cabbage",
    "gova": "cabbage",
    "green chilli": "green_chilli",
    "green chili": "green_chilli",
    "chilli": "green_chilli",
    "chili": "green_chilli",
    "miris": "green_chilli",
    "leeks": "leeks",
    "lime": "lime",
    "pumpkin": "pumpkin",
    "wattakka": "pumpkin",
    "bitter gourd": "bitter_gourd",
    "karawila": "bitter_gourd",
    "snake gourd": "snake_gourd",
    "capsicum": "capsicum",
    "cucumber": "cucumber",
    "beetroot": "beetroot",
    "papaya": "papaya",
    "banana": "banana",
    "mango": "mango",
    "passion fruit": "passion_fruit",
    "pineapple": "pineapple",
}

# Longest aliases first so "green chilli" wins over "chilli".
_ORDERED_ALIASES = sorted(CROP_ALIASES.items(), key=lambda kv: len(kv[0]), reverse=True)

# Centre id -> short badge used by the UI.
CENTRE_SHORT_CODES: Dict[str, str] = {
    "DAMBULLA": "DMB",
    "THAMBUTHTHEGAMA": "THG",
}

DEFAULT_CENTRE_ID = "DAMBULLA"


def normalise_crop(raw: Optional[str]) -> str:
    """`'Green Chilli '` -> `'green_chilli'`. Unknown crops pass through cleaned."""
    cleaned = " ".join((raw or "").strip().lower().split())
    if not cleaned:
        return "tomato"
    return CROP_ALIASES.get(cleaned, cleaned.replace(" ", "_"))


def crop_label(crop_name: Optional[str]) -> str:
    """`'green_chilli'` -> `'Green Chilli'` for display in the UI."""
    return " ".join(part.capitalize() for part in (crop_name or "").split("_")) or "Tomato"


def detect_crop(text: str) -> Optional[str]:
    """Extracts the first crop mentioned in free text, or None."""
    haystack = " ".join((text or "").lower().split())
    if not haystack:
        return None
    for alias, canonical in _ORDERED_ALIASES:
        if alias in haystack:
            return canonical
    return None


def normalise_centre(raw: Optional[str]) -> str:
    """Maps loose centre input onto a valid centre id, defaulting to Dambulla."""
    upper = (raw or "").strip().upper().replace("-", "").replace(" ", "")
    if "THAMBU" in upper:
        return "THAMBUTHTHEGAMA"
    if "DAMBULLA" in upper or "DMB" in upper:
        return "DAMBULLA"
    return DEFAULT_CENTRE_ID


def detect_centre(text: str, default: str = DEFAULT_CENTRE_ID) -> str:
    """Prefers a centre named in the message, otherwise keeps the UI selection."""
    lowered = (text or "").lower()
    if "thambuththegama" in lowered or "thambuthegama" in lowered or "thg" in lowered:
        return "THAMBUTHTHEGAMA"
    if "dambulla" in lowered:
        return "DAMBULLA"
    return normalise_centre(default)


def list_centres() -> List[Dict[str, str]]:
    """Reads the configured economic centres from `config/param.yaml`."""
    raw_centres = config.params.get("economic_centers", []) or []
    centres: List[Dict[str, str]] = []
    for entry in raw_centres:
        centre_id = str(entry.get("id", "")).upper()
        if not centre_id:
            continue
        centres.append(
            {
                "id": centre_id,
                "name": entry.get("name", centre_id.title()),
                "location": entry.get("location", "Sri Lanka"),
                "short": CENTRE_SHORT_CODES.get(centre_id, centre_id[:3]),
            }
        )
    if not centres:  # Defensive fallback if the YAML is missing.
        centres = [
            {
                "id": "DAMBULLA",
                "name": "Dambulla Dedicated Economic Centre",
                "location": "Dambulla, Central Province",
                "short": "DMB",
            },
            {
                "id": "THAMBUTHTHEGAMA",
                "name": "Thambuththegama Economic Centre",
                "location": "Thambuththegama, North Central Province",
                "short": "THG",
            },
        ]
    return centres


def forecast_horizon_days() -> int:
    """Forecast horizon from `config/param.yaml` (defaults to 14 days)."""
    return int((config.params.get("forecasting", {}) or {}).get("horizon_days", 14))
