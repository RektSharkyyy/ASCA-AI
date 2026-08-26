import pytest
from src.agents.rag_agent import _extract_land_area_acres, _calculate_scaled_fertilizer
from src.services.cultivation_service import get_crop_guide

def test_land_area_unit_extraction():
    """Test regex extraction of acres, fractions, hectares, and perches."""
    assert _extract_land_area_acres("how much fertilizer for 2.5 acres of tomato?") == 2.5
    assert _extract_land_area_acres("fertilizer calculation for 3 acre") == 3.0
    assert _extract_land_area_acres("half acre carrot requirement") == 0.5
    assert _extract_land_area_acres("1/2 acre tomato") == 0.5
    assert _extract_land_area_acres("quarter acre chilli") == 0.25
    assert _extract_land_area_acres("1 ha of cabbage") == 2.47 # 1 ha = 2.471 acres rounded
    assert _extract_land_area_acres("80 perches eggplant") == 0.5 # 80/160 = 0.5 acres
    assert _extract_land_area_acres("general tomato advice without numbers") is None

def test_scaled_fertilizer_calculation_tomato_2_5_acres():
    """Test scaling 1-acre benchmarks to 2.5 acres for Tomato."""
    guide = get_crop_guide("tomato")
    assert guide is not None
    
    scaled = _calculate_scaled_fertilizer(guide, acres=2.5)
    assert scaled["acres"] == 2.5
    assert "phases" in scaled
    assert "procurement" in scaled
    
    # Check phases
    phases = scaled["phases"]
    assert any("Basal" in p for p in phases.keys())
    assert any("Top Dressing 1" in p for p in phases.keys())
    assert any("Top Dressing 2" in p for p in phases.keys())
    
    # Check procurement summary has 50kg bag calculations
    proc = {item["item"]: item for item in scaled["procurement"]}
    assert "Urea (46% N)" in proc
    assert "TSP (Triple Super Phosphate)" in proc
    assert "MOP (Muriate of Potash)" in proc
    
    # Urea total should be ~250 kg = 5 bags (50kg each)
    assert "5 bags" in proc["Urea (46% N)"]["bags_50kg"]
    # TSP total should be 150 kg = 3 bags (50kg each)
    assert "3 bags" in proc["TSP (Triple Super Phosphate)"]["bags_50kg"]

def test_scaled_fertilizer_calculation_half_acre():
    """Test scaling down to 0.5 acre."""
    guide = get_crop_guide("carrot")
    assert guide is not None
    
    scaled = _calculate_scaled_fertilizer(guide, acres=0.5)
    assert scaled["acres"] == 0.5
    assert len(scaled["procurement"]) > 0
