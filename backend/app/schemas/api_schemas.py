from typing import List, Optional, Any, Dict
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from decimal import Decimal
from app.models.entities import UserRole, OrderStatus, PaymentStatus, TicketStatus, TicketPriority, DocumentStatus, ReviewDecision

# User & Auth
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.AGENT

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Customer
class CustomerResponse(BaseModel):
    id: int
    external_id: str
    full_name: str
    email: str
    phone: Optional[str] = None
    account_status: str
    kyc_verified: bool
    created_at: datetime
    class Config:
        from_attributes = True

# Payment
class PaymentResponse(BaseModel):
    id: int
    transaction_id: str
    gateway: str
    amount: Decimal
    currency: str
    status: PaymentStatus
    payment_method: Optional[str] = None
    refund_reference: Optional[str] = None
    refunded_amount: Decimal
    created_at: datetime
    class Config:
        from_attributes = True

# Order
class OrderResponse(BaseModel):
    id: int
    order_number: str
    customer_id: int
    total_amount: Decimal
    currency: str
    status: OrderStatus
    items_summary: Optional[str] = None
    cancellation_reason: Optional[str] = None
    order_date: datetime
    cancelled_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    payments: List[PaymentResponse] = []
    class Config:
        from_attributes = True

# Support Ticket
class TicketResponse(BaseModel):
    id: int
    ticket_number: str
    customer_id: int
    order_id: Optional[int] = None
    subject: str
    initial_question: str
    status: TicketStatus
    priority: TicketPriority
    category: str
    channel: str
    created_at: datetime
    customer: Optional[CustomerResponse] = None
    order: Optional[OrderResponse] = None
    class Config:
        from_attributes = True

# Document & Ingestion
class DocumentChunkResponse(BaseModel):
    id: int
    chunk_index: int
    content: str
    page_number: Optional[int] = None
    chunk_metadata: Dict[str, Any] = {}
    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: int
    title: str
    filename: str
    file_type: str
    file_size_bytes: int
    doc_category: str
    status: DocumentStatus
    total_chunks: int
    error_message: Optional[str] = None
    created_at: datetime
    indexed_at: Optional[datetime] = None
    class Config:
        from_attributes = True

# Retrieval schemas
class RetrievedChunk(BaseModel):
    id: int
    document_id: int
    document_title: str
    doc_category: str
    content: str
    page_number: Optional[int] = None
    semantic_score: Optional[float] = None
    keyword_score: Optional[float] = None
    rrf_score: float
    rerank_score: Optional[float] = None
    source_passage_label: str

class RetrievalInspectResponse(BaseModel):
    query: str
    semantic_candidates: List[Dict[str, Any]]
    keyword_candidates: List[Dict[str, Any]]
    fused_candidates: List[RetrievedChunk]
    reranked_candidates: List[RetrievedChunk]

# Resolution & Generation
class Citation(BaseModel):
    citation_id: str
    document_id: int
    document_title: str
    passage_snippet: str
    page_number: Optional[int] = None

class VerifiedBusinessFacts(BaseModel):
    customer_name: str
    customer_email: str
    order_number: Optional[str] = None
    order_status: Optional[str] = None
    total_amount: Optional[str] = None
    currency: Optional[str] = None
    payments: List[Dict[str, Any]] = []
    cancellation_date: Optional[str] = None
    authoritative_note: str

class ResolutionRecommendationResponse(BaseModel):
    id: Optional[int] = None
    ticket_id: int
    issue_summary: str
    verified_business_facts: VerifiedBusinessFacts
    recommended_resolution: str
    action_steps: List[str]
    citations: List[Citation]
    uncertainties: Optional[str] = None
    review_required: bool
    retrieved_chunk_ids: List[int] = []
    created_at: Optional[datetime] = None
    generation_metadata: Dict[str, Any] = {}
    class Config:
        from_attributes = True

class ReviewSubmission(BaseModel):
    decision: ReviewDecision
    agent_notes: Optional[str] = None
    modified_resolution: Optional[str] = None

class ReviewResponse(BaseModel):
    id: int
    recommendation_id: int
    agent_id: Optional[int] = None
    agent_name: Optional[str] = None
    decision: ReviewDecision
    agent_notes: Optional[str] = None
    modified_resolution: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

# Evaluation
class EvaluationQuery(BaseModel):
    query: str
    expected_doc_title: str
    expected_ground_truth: str

class RetrievalMetric(BaseModel):
    strategy: str
    recall_at_1: float
    recall_at_3: float
    recall_at_5: float
    mrr: float
    mean_latency_ms: float

class EvaluationRunResponse(BaseModel):
    run_timestamp: datetime
    total_queries: int
    strategies_compared: List[RetrievalMetric]
    sample_evaluations: List[Dict[str, Any]]
