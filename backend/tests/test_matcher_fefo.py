import pytest
from src.agents.tools.matcher_tool import FEFORiskEngine, CROP_SHELF_LIFE_DAYS, chroma_b2b_store
from src.services.b2b_service import b2b_service

def test_fefo_risk_score_calculation():
    """Test FEFO decay score computation based on shelf life, distance, and buyer capacity."""
    tomato_score = FEFORiskEngine.calculate_risk_score(
        crop_name="tomato",
        center_id="DAMBULLA",
        buyer_location="Dambulla Industrial Zone", # 8 km away
        surplus_volume_tons=10.0,
        buyer_capacity_tons=35.0
    )
    
    pumpkin_score = FEFORiskEngine.calculate_risk_score(
        crop_name="pumpkin",
        center_id="DAMBULLA",
        buyer_location="Colombo Biyagama Zone", # 150 km away
        surplus_volume_tons=10.0,
        buyer_capacity_tons=35.0
    )
    
    assert 0.0 <= tomato_score <= 1.0
    assert 0.0 <= pumpkin_score <= 1.0
    assert CROP_SHELF_LIFE_DAYS["tomato"] == 3
    assert CROP_SHELF_LIFE_DAYS["pumpkin"] == 20

@pytest.mark.asyncio
async def test_b2b_buyer_registry_structure():
    """Test standard registered buyers have valid capacity and distance constraints."""
    res = await b2b_service.list_buyers("DAMBULLA")
    assert res.total > 0
    assert len(res.buyers) > 0
    
    for b in res.buyers:
        assert b.company_name
        assert b.buyer_type
        assert b.daily_capacity_tons > 0
        assert b.location
