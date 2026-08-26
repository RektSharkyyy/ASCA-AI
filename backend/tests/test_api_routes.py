import pytest
import httpx

@pytest.mark.asyncio
async def test_health_endpoint(async_client: httpx.AsyncClient):
    """Test GET /health returns ok status."""
    res = await async_client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["app"] == "ASCA AI"

@pytest.mark.asyncio
async def test_meta_endpoint(async_client: httpx.AsyncClient):
    """Test GET /api/meta returns centres and crops list."""
    res = await async_client.get("/api/meta")
    assert res.status_code == 200
    data = res.json()
    assert "centres" in data
    assert "crops" in data
    assert len(data["centres"]) >= 2
    assert len(data["crops"]) >= 6

@pytest.mark.asyncio
async def test_b2b_buyers_endpoint(async_client: httpx.AsyncClient, auth_headers: dict):
    """Test GET /api/b2b/buyers returns registered buyer catalog."""
    res = await async_client.get("/api/b2b/buyers?centre_id=DAMBULLA", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "buyers" in data
    assert len(data["buyers"]) > 0

@pytest.mark.asyncio
async def test_b2b_match_endpoint(async_client: httpx.AsyncClient, auth_headers: dict):
    """Test POST /api/b2b/match returns FEFO-ranked buyer matches."""
    payload = {
        "centre_id": "DAMBULLA",
        "crops": ["tomato"]
    }
    res = await async_client.post("/api/b2b/match", headers=auth_headers, json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "matches" in data

@pytest.mark.asyncio
async def test_cultivation_crops_endpoint(async_client: httpx.AsyncClient, auth_headers: dict):
    """Test GET /api/cultivation/crops returns agronomy crop profiles."""
    res = await async_client.get("/api/cultivation/crops", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "crops" in data
    assert len(data["crops"]) >= 6

@pytest.mark.asyncio
async def test_cultivation_guide_endpoint(async_client: httpx.AsyncClient, auth_headers: dict):
    """Test GET /api/cultivation/guide/{crop_id} returns detailed fertilizer & pest guide."""
    res = await async_client.get("/api/cultivation/guide/tomato", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "tomato"
    assert "fertilizer_schedule" in data
    assert "pests_and_diseases" in data

@pytest.mark.asyncio
async def test_chat_endpoint_authenticated(async_client: httpx.AsyncClient, auth_headers: dict):
    """Test POST /api/chat with valid JWT auth token."""
    res = await async_client.post(
        "/api/chat",
        headers=auth_headers,
        json={"message": "hello ASCA AI", "centre": "DAMBULLA"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert len(data["answer"]) > 0
    assert "session_id" in data

@pytest.mark.asyncio
async def test_chat_endpoint_unauthorized(async_client: httpx.AsyncClient):
    """Test POST /api/chat rejects requests without JWT token."""
    res = await async_client.post(
        "/api/chat",
        json={"message": "hello", "centre": "DAMBULLA"}
    )
    assert res.status_code == 401

@pytest.mark.asyncio
async def test_blueprints_list_endpoint(async_client: httpx.AsyncClient, auth_headers: dict):
    """Test GET /api/blueprints returns executive dossiers list."""
    res = await async_client.get("/api/blueprints", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "blueprints" in data
    assert "total" in data
    assert data["total"] >= 4

@pytest.mark.asyncio
async def test_blueprints_generate_endpoint(async_client: httpx.AsyncClient, auth_headers: dict):
    """Test POST /api/blueprints/generate creates a new dynamic executive blueprint."""
    payload = {
        "centre": "DAMBULLA",
        "crop": "tomato",
        "horizon_days": 14
    }
    res = await async_client.post("/api/blueprints/generate", headers=auth_headers, json=payload)
    assert res.status_code == 201
    data = res.json()
    assert "id" in data
    assert "title" in data
    assert "riskLevel" in data
    assert "forecastData" in data
    assert "quotaData" in data
    assert "directives" in data
