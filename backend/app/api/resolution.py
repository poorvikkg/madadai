from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.core.database import get_db
from app.models.entities import (
    SupportTicket, Order, Payment, Customer, ResolutionRecommendation, 
    ResolutionReview, User
)
from app.schemas.api_schemas import (
    ResolutionRecommendationResponse, ReviewSubmission, ReviewResponse, 
    VerifiedBusinessFacts
)
from app.services.retrieval_service import retrieval_service
from app.services.llm_service import llm_service
from app.api.auth import get_current_user

router = APIRouter(prefix="/resolution", tags=["Resolution & Recommendations"])

@router.post("/generate/{ticket_id}", response_model=ResolutionRecommendationResponse)
def generate_recommendation_for_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    customer = ticket.customer
    order = ticket.order

    # Assemble authoritative business facts
    payments_info = []
    if order and order.payments:
        for p in order.payments:
            payments_info.append({
                "transaction_id": p.transaction_id,
                "amount": str(p.amount),
                "gateway": p.gateway,
                "status": p.status.value,
                "payment_method": p.payment_method or "Online",
                "refund_reference": p.refund_reference
            })

    verified_facts = {
        "customer_name": customer.full_name if customer else "N/A",
        "customer_email": customer.email if customer else "N/A",
        "order_number": order.order_number if order else "N/A",
        "order_status": order.status.value if order else "unknown",
        "total_amount": str(order.total_amount) if order else "0.00",
        "currency": order.currency if order else "INR",
        "payments": payments_info,
        "cancellation_date": order.cancelled_at.isoformat() if order and order.cancelled_at else None,
        "authoritative_note": "Facts directly queried from PostgreSQL database records. Status and amounts are verified."
    }

    # Hybrid retrieve relevant policy and documentation chunks
    query_text = f"{ticket.subject} {ticket.initial_question}"
    retrieved_passages = retrieval_service.hybrid_search(query_text, db, top_k=4)

    # Synthesize resolution recommendation
    gen_result = llm_service.generate_resolution(
        customer_question=ticket.initial_question,
        verified_facts=verified_facts,
        retrieved_passages=retrieved_passages
    )

    # Store in database
    rec_obj = ResolutionRecommendation(
        ticket_id=ticket.id,
        prompt_used=query_text,
        issue_summary=gen_result["issue_summary"],
        verified_business_facts=verified_facts,
        recommended_resolution=gen_result["recommended_resolution"],
        action_steps=gen_result["action_steps"],
        citations=gen_result["citations"],
        uncertainties=gen_result.get("uncertainties"),
        review_required=gen_result.get("review_required", True),
        retrieved_chunk_ids=[p["id"] for p in retrieved_passages],
        generation_metadata={"model": gen_result.get("model_used", "MadadAI-LLM")}
    )
    db.add(rec_obj)
    db.commit()
    db.refresh(rec_obj)

    return rec_obj

@router.get("/recommendations/{ticket_id}", response_model=List[ResolutionRecommendationResponse])
def get_recommendations(
    ticket_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return (
        db.query(ResolutionRecommendation)
        .filter(ResolutionRecommendation.ticket_id == ticket_id)
        .order_by(ResolutionRecommendation.created_at.desc())
        .all()
    )

@router.post("/review/{recommendation_id}", response_model=ReviewResponse)
def submit_resolution_review(
    recommendation_id: int,
    review_sub: ReviewSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rec = db.query(ResolutionRecommendation).filter(ResolutionRecommendation.id == recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    review = ResolutionReview(
        recommendation_id=rec.id,
        agent_id=current_user.id,
        decision=review_sub.decision,
        agent_notes=review_sub.agent_notes,
        modified_resolution=review_sub.modified_resolution
    )
    db.add(review)

    # If approved and review was required, mark review status
    if review_sub.decision == "approved":
        rec.review_required = False

    db.commit()
    db.refresh(review)

    return {
        "id": review.id,
        "recommendation_id": review.recommendation_id,
        "agent_id": current_user.id,
        "agent_name": current_user.full_name,
        "decision": review.decision,
        "agent_notes": review.agent_notes,
        "modified_resolution": review.modified_resolution,
        "created_at": review.created_at
    }

@router.get("/reviews/{recommendation_id}", response_model=List[ReviewResponse])
def get_reviews_for_recommendation(
    recommendation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    reviews = (
        db.query(ResolutionReview)
        .filter(ResolutionReview.recommendation_id == recommendation_id)
        .order_by(ResolutionReview.created_at.desc())
        .all()
    )
    results = []
    for r in reviews:
        results.append({
            "id": r.id,
            "recommendation_id": r.recommendation_id,
            "agent_id": r.agent_id,
            "agent_name": r.agent.full_name if r.agent else "System Agent",
            "decision": r.decision,
            "agent_notes": r.agent_notes,
            "modified_resolution": r.modified_resolution,
            "created_at": r.created_at
        })
    return results
