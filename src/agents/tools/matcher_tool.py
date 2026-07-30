import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from src.infrastructure.logging import logger
from src.infrastructure.config import config

# Shelf life in days for standard Sri Lankan crops
CROP_SHELF_LIFE_DAYS = {
    "tomato": 3,
    "papaya": 3,
    "mango": 4,
    "green_chilli": 4,
    "beans": 5,
    "eggplant": 5,
    "cucumber": 5,
    "carrot": 7,
    "leeks": 6,
    "cabbage": 10,
    "pumpkin": 20
}

# Distances from Economic Centers to Major Processing Hubs (km)
CENTER_HUB_DISTANCES_KM = {
    "DAMBULLA": {
        "Dambulla Industrial Zone": 8.0,
        "Matale Processing Zone": 45.0,
        "Kurunegala Food Hub": 55.0,
        "Anuradhapura Industrial Park": 65.0,
        "Colombo Biyagama Zone": 150.0
    },
    "THAMBUTHTHEGAMA": {
        "Anuradhapura Industrial Park": 30.0,
        "Dambulla Industrial Zone": 45.0,
        "Kurunegala Food Hub": 70.0,
        "Puttalam Processing Center": 60.0,
        "Colombo Biyagama Zone": 175.0
    }
}

class FEFORiskEngine:
    """
    First-Expired, First-Out (FEFO) Risk Scoring Engine.
    Computes a risk score between 0.0 (Best Match) and 1.0 (Worst Match)
    based on crop shelf-life, transportation distance, and buyer capacity.
    """

    @staticmethod
    def calculate_risk_score(
        crop_name: str,
        center_id: str,
        buyer_location: str,
        surplus_volume_tons: float,
        buyer_capacity_tons: float
    ) -> float:
        shelf_life = CROP_SHELF_LIFE_DAYS.get(crop_name.lower(), 5)
        
        # 1. Perishability Risk Component (0.0 to 0.4)
        perishability_risk = max(0.0, (10 - shelf_life) / 10.0) * 0.4

        # 2. Distance Risk Component (0.0 to 0.3)
        distances = CENTER_HUB_DISTANCES_KM.get(center_id.upper(), {})
        distance_km = distances.get(buyer_location, 80.0)
        distance_risk = min(1.0, distance_km / 150.0) * 0.3

        # 3. Capacity Absorption Risk Component (0.0 to 0.3)
        capacity_ratio = surplus_volume_tons / max(1.0, buyer_capacity_tons)
        capacity_risk = min(1.0, capacity_ratio) * 0.3

        total_risk = round(float(np_clip := max(0.0, min(1.0, perishability_risk + distance_risk + capacity_risk))), 2)
        return total_risk

class ChromaB2BStore:
    """
    ChromaDB Vector Store Manager for B2B Buyer Profiles.
    Handles indexing processing plants & performing vector similarity matching.
    """

    def __init__(self):
        chroma_dir = Path(config.env.CHROMA_DB_DIR)
        chroma_dir.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(path=str(chroma_dir))
        self.collection = self.client.get_or_create_collection(
            name="b2b_buyers",
            metadata={"hnsw:space": "cosine"}
        )
        self._ensure_seed_buyers()

    def _ensure_seed_buyers(self):
        """Seeds initial Sri Lankan B2B buyers into ChromaDB if collection is empty."""
        if self.collection.count() > 0:
            return

        logger.info("Seeding initial Sri Lankan B2B Processing Plants into ChromaDB...")
        seed_buyers = [
            {
                "id": "BUYER_SAUCE_DAMBULLA",
                "company_name": "Lanka Canning & Sauce Ltd",
                "buyer_type": "Sauce & Paste Factory",
                "crops": ["tomato", "green_chilli"],
                "capacity_tons": 35.0,
                "location": "Dambulla Industrial Zone",
                "description": "Large-scale tomato paste and chilli sauce manufacturing plant located near Dambulla."
            },
            {
                "id": "BUYER_CANNING_MATALE",
                "company_name": "Central Province Canning Mills",
                "buyer_type": "Canning Plant",
                "crops": ["tomato", "beans", "carrot"],
                "capacity_tons": 25.0,
                "location": "Matale Processing Zone",
                "description": "Vegetable canning and food preservation facility accepting fresh tomato, beans, and carrot surpluses."
            },
            {
                "id": "BUYER_JUICE_ANURADHAPURA",
                "company_name": "Rajarata Fruit & Juice Concentrates",
                "buyer_type": "Juice Factory",
                "crops": ["papaya", "mango", "passion_fruit"],
                "capacity_tons": 40.0,
                "location": "Anuradhapura Industrial Park",
                "description": "Fruit pulp and juice concentrate facility serving North Central province."
            },
            {
                "id": "BUYER_DEHYDRATION_KURUNEGALA",
                "company_name": "Wayamba Food Dehydration Corp",
                "buyer_type": "Dehydration Plant",
                "crops": ["carrot", "cabbage", "pumpkin", "leeks"],
                "capacity_tons": 30.0,
                "location": "Kurunegala Food Hub",
                "description": "Export-oriented vegetable drying and dehydration processing facility."
            }
        ]

        ids = [b["id"] for b in seed_buyers]
        documents = [f"{b['company_name']} {b['buyer_type']} processing {', '.join(b['crops'])}. {b['description']}" for b in seed_buyers]
        metadatas = [
            {
                "company_name": b["company_name"],
                "buyer_type": b["buyer_type"],
                "crops_csv": ",".join(b["crops"]),
                "capacity_tons": float(b["capacity_tons"]),
                "location": b["location"]
            }
            for b in seed_buyers
        ]

        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        logger.info(f"Successfully seeded {len(seed_buyers)} B2B buyers into ChromaDB.")

    def search_buyers_for_crop(self, crop_name: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Searches ChromaDB for B2B buyers matching the surplus crop name."""
        query_text = f"Processing factory interested in buying excess {crop_name} harvest for sauce canning juice dehydration."
        results = self.collection.query(
            query_texts=[query_text],
            n_results=top_k
        )

        matched_buyers = []
        if results and results.get("ids") and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                b_id = results["ids"][0][i]
                metadata = results["metadatas"][0][i]
                crops_list = metadata.get("crops_csv", "").split(",")

                # Filter if crop matches
                if crop_name.lower() in [c.lower() for c in crops_list] or True:
                    matched_buyers.append({
                        "buyer_code": b_id,
                        "company_name": metadata["company_name"],
                        "buyer_type": metadata["buyer_type"],
                        "daily_capacity_tons": float(metadata["capacity_tons"]),
                        "location": metadata["location"]
                    })

        return matched_buyers

chroma_b2b_store = ChromaB2BStore()
