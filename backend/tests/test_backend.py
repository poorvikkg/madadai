import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.ingestion_service import ingestion_service
from app.services.embedding_service import embedding_service
from app.services.retrieval_service import retrieval_service
from app.services.llm_service import llm_service
from app.core.database import SessionLocal

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data

def test_login_and_auth_flow():
    # Login with seeded agent
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "agent@madadai.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "agent@madadai.com"
    token = data["access_token"]

    # Test /me endpoint
    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "agent@madadai.com"

def test_document_chunking():
    sample_text = "This is a sentence. " * 50
    chunks = ingestion_service.chunk_text(sample_text, chunk_size=20, overlap=5, page_number=1)
    assert len(chunks) > 1
    assert "content" in chunks[0]
    assert chunks[0]["page_number"] == 1

def test_embedding_generation_consistency():
    text1 = "Cancellation and refund policy for Indian e-commerce orders"
    vec1 = embedding_service.embed_text(text1)
    vec2 = embedding_service.embed_text(text1)
    assert len(vec1) == 384
    # Determinism test
    assert vec1 == vec2

def test_authoritative_business_lookup_and_resolution():
    # Login to get token
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "agent@madadai.com", "password": "password123"}
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch tickets
    tickets_resp = client.get("/api/v1/business/tickets", headers=headers)
    assert tickets_resp.status_code == 200
    tickets = tickets_resp.json()
    assert len(tickets) >= 1

    # Find the primary ₹2,000 cancelled order ticket
    target_ticket = next((t for t in tickets if "2,000" in t["initial_question"] or "refund" in t["initial_question"].lower()), tickets[0])

    # Generate resolution recommendation
    gen_resp = client.post(
        f"/api/v1/resolution/generate/{target_ticket['id']}",
        headers=headers
    )
    assert gen_resp.status_code == 200
    recommendation = gen_resp.json()

    # Grounding validations
    assert "verified_business_facts" in recommendation
    assert recommendation["verified_business_facts"]["order_status"].lower() == "cancelled"
    assert "2000.00" in recommendation["verified_business_facts"]["total_amount"]
    assert len(recommendation["citations"]) > 0
    assert recommendation["review_required"] is True

    # Submit human review approval
    rec_id = recommendation["id"]
    review_resp = client.post(
        f"/api/v1/resolution/review/{rec_id}",
        headers=headers,
        json={
            "decision": "approved",
            "agent_notes": "Verified gateway Razorpay transaction ID. Authorized for 5-7 day bank payout."
        }
    )
    assert review_resp.status_code == 200
    assert review_resp.json()["decision"] == "approved"

def test_retrieval_inspector():
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "agent@madadai.com", "password": "password123"}
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get(
        "/api/v1/retrieval/inspect?q=refund+for+cancelled+order&top_k=3",
        headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "fused_candidates" in data
    assert len(data["fused_candidates"]) > 0
    assert data["fused_candidates"][0]["rrf_score"] > 0

def test_evaluation_run():
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "agent@madadai.com", "password": "password123"}
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    eval_resp = client.post("/api/v1/evaluation/run", headers=headers)
    assert eval_resp.status_code == 200
    eval_data = eval_resp.json()
    assert eval_data["total_queries"] > 0
    assert len(eval_data["strategies_compared"]) == 3
