import enum
import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, 
    Numeric, Enum, JSON
)
from sqlalchemy.orm import relationship
from app.core.database import Base, engine
from app.core.config import settings

# If running on Postgres, import Vector; on sqlite fallback, use JSON or Text representation
is_postgres = "postgresql" in str(engine.url)
if is_postgres:
    from pgvector.sqlalchemy import Vector
    VectorType = Vector(settings.VECTOR_DIMENSION)
else:
    VectorType = JSON

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    AGENT = "agent"
    SUPERVISOR = "supervisor"

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"

class PaymentStatus(str, enum.Enum):
    INITIATED = "initiated"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"

class TicketStatus(str, enum.Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    PENDING_CUSTOMER = "pending_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"

class TicketPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"

class ReviewDecision(str, enum.Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.AGENT, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    reviews = relationship("ResolutionReview", back_populates="agent")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(64), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), index=True, nullable=False)
    phone = Column(String(32), nullable=True)
    account_status = Column(String(32), default="active")
    kyc_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    orders = relationship("Order", back_populates="customer")
    tickets = relationship("SupportTicket", back_populates="customer")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(64), unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(8), default="INR")
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    items_summary = Column(Text, nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    order_date = Column(DateTime, default=datetime.datetime.utcnow)
    cancelled_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    customer = relationship("Customer", back_populates="orders")
    payments = relationship("Payment", back_populates="order")
    tickets = relationship("SupportTicket", back_populates="order")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(128), unique=True, index=True, nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    gateway = Column(String(64), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(8), default="INR")
    status = Column(Enum(PaymentStatus), nullable=False)
    payment_method = Column(String(64), nullable=True)
    refund_reference = Column(String(128), nullable=True)
    refunded_amount = Column(Numeric(12, 2), default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    order = relationship("Order", back_populates="payments")


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(64), unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    subject = Column(String(255), nullable=False)
    initial_question = Column(Text, nullable=False)
    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN, nullable=False)
    priority = Column(Enum(TicketPriority), default=TicketPriority.MEDIUM, nullable=False)
    category = Column(String(64), default="refunds")
    channel = Column(String(32), default="web_chat")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    customer = relationship("Customer", back_populates="tickets")
    order = relationship("Order", back_populates="tickets")
    recommendations = relationship("ResolutionRecommendation", back_populates="ticket")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(32), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    doc_category = Column(String(64), default="policy")
    status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING, nullable=False)
    total_chunks = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    indexed_at = Column(DateTime, nullable=True)

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    chunk_metadata = Column(JSON, default=dict)
    embedding = Column(VectorType, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    document = relationship("Document", back_populates="chunks")


class ResolutionRecommendation(Base):
    __tablename__ = "resolution_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False)
    prompt_used = Column(Text, nullable=False)
    issue_summary = Column(Text, nullable=False)
    verified_business_facts = Column(JSON, nullable=False)
    recommended_resolution = Column(Text, nullable=False)
    action_steps = Column(JSON, nullable=False)
    citations = Column(JSON, nullable=False)
    uncertainties = Column(Text, nullable=True)
    review_required = Column(Boolean, default=True)
    retrieved_chunk_ids = Column(JSON, default=list)
    generation_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    ticket = relationship("SupportTicket", back_populates="recommendations")
    reviews = relationship("ResolutionReview", back_populates="recommendation")


class ResolutionReview(Base):
    __tablename__ = "resolution_reviews"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(Integer, ForeignKey("resolution_recommendations.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    decision = Column(Enum(ReviewDecision), nullable=False)
    agent_notes = Column(Text, nullable=True)
    modified_resolution = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    recommendation = relationship("ResolutionRecommendation", back_populates="reviews")
    agent = relationship("User", back_populates="reviews")
