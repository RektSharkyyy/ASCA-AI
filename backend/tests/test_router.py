import pytest
from src.agents.router import QueryRouter, RouteDecision, QueryRoute

@pytest.fixture
def router():
    return QueryRouter()

def test_heuristic_market_price_query(router: QueryRouter):
    """Test router classifies price forecasting queries."""
    res = router._heuristic_route("tomato price forecast for Dambulla")
    assert res is not None
    assert res.route == QueryRoute.RAG
    assert res.confidence >= 0.8

def test_heuristic_b2b_matching_query(router: QueryRouter):
    """Test router classifies B2B buyer inquiries."""
    res = router._heuristic_route("match buyers for 20 tons of surplus tomato")
    assert res is not None
    assert res.route == QueryRoute.RAG

def test_heuristic_greeting_query(router: QueryRouter):
    """Test router classifies simple greetings as direct route."""
    res = router._heuristic_route("hello ASCA AI")
    assert res is not None
    assert res.route == QueryRoute.DIRECT

def test_economic_centre_detection():
    """Test extraction of Dambulla vs Thambuththegama."""
    from src.services.crop_catalog import detect_centre
    assert detect_centre("price at Dambulla market") == "DAMBULLA"
    assert detect_centre("prices at Thambuththegama hub") == "THAMBUTHTHEGAMA"
    assert detect_centre("prices at thg") == "THAMBUTHTHEGAMA"
    assert detect_centre("prices at dam") == "DAMBULLA"
