import os
import sys
import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import text

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.entities import (
    User, UserRole, Customer, Order, Payment, SupportTicket,
    OrderStatus, PaymentStatus, TicketStatus, TicketPriority,
    Document, DocumentChunk, DocumentStatus
)
from app.services.embedding_service import embedding_service
from app.services.ingestion_service import ingestion_service

def init_db_and_seed():
    print("Ensuring pgvector extension if PostgreSQL...")
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
    except Exception as e:
        print(f"Note on vector extension: {e}")

    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # 1. Seed Support Agents and Admins
        if not db.query(User).filter(User.email == "agent@madadai.com").first():
            print("Seeding default agent user...")
            agent = User(
                email="agent@madadai.com",
                hashed_password=get_password_hash("password123"),
                full_name="Priya Sharma (Senior Agent)",
                role=UserRole.AGENT,
                is_active=True
            )
            admin = User(
                email="admin@madadai.com",
                hashed_password=get_password_hash("admin123"),
                full_name="Rajesh Kumar (Operations Admin)",
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add_all([agent, admin])
            db.commit()

        # 2. Seed Realistic Customer Records
        c1 = db.query(Customer).filter(Customer.email == "rohit.verma@example.com").first()
        if not c1:
            print("Seeding realistic customers, orders, and payments...")
            c1 = Customer(
                external_id="CUST-IN-9081",
                full_name="Rohit Verma",
                email="rohit.verma@example.com",
                phone="+91-9876543210",
                account_status="active",
                kyc_verified=True
            )
            c2 = Customer(
                external_id="CUST-IN-4421",
                full_name="Ananya Desai",
                email="ananya.desai@example.com",
                phone="+91-9123456789",
                account_status="active",
                kyc_verified=True
            )
            db.add_all([c1, c2])
            db.commit()
            db.refresh(c1)
            db.refresh(c2)

            # Order 1: Cancelled order with ₹2,000 successful payment (The exact scenario from the prompt!)
            order1 = Order(
                order_number="ORD-2026-8812",
                customer_id=c1.id,
                total_amount=Decimal("2000.00"),
                currency="INR",
                status=OrderStatus.CANCELLED,
                items_summary="boAt Rockerz 450 Bluetooth On-Ear Headphones with Mic (Matte Black)",
                cancellation_reason="Customer requested cancellation before dispatch due to accidental order.",
                order_date=datetime.datetime.utcnow() - datetime.timedelta(days=2),
                cancelled_at=datetime.datetime.utcnow() - datetime.timedelta(days=1, hours=22)
            )
            db.add(order1)
            db.commit()
            db.refresh(order1)

            # Payment for Order 1: Captured ₹2,000 via UPI
            pay1 = Payment(
                transaction_id="TXN-UPI-9821447012",
                order_id=order1.id,
                gateway="Razorpay UPI",
                amount=Decimal("2000.00"),
                currency="INR",
                status=PaymentStatus.SUCCESS,
                payment_method="GooglePay UPI (axisbank@okhdfc)",
                refund_reference=None,
                refunded_amount=Decimal("0.00")
            )
            db.add(pay1)

            # Support Ticket for Order 1
            ticket1 = SupportTicket(
                ticket_number="TCK-9901",
                customer_id=c1.id,
                order_id=order1.id,
                subject="Deducted ₹2,000 for cancelled order - refund status inquiry",
                initial_question="My order was cancelled, but ₹2,000 was deducted from my account. Where is my refund?",
                status=TicketStatus.OPEN,
                priority=TicketPriority.HIGH,
                category="refunds",
                channel="web_chat",
                created_at=datetime.datetime.utcnow() - datetime.timedelta(hours=4)
            )
            db.add(ticket1)

            # Order 2: Delivered order with return inquiry
            order2 = Order(
                order_number="ORD-2026-5541",
                customer_id=c2.id,
                total_amount=Decimal("4599.00"),
                currency="INR",
                status=OrderStatus.DELIVERED,
                items_summary="Noise ColorFit Pro 5 Smart Watch with Amoled Display",
                order_date=datetime.datetime.utcnow() - datetime.timedelta(days=5),
                delivered_at=datetime.datetime.utcnow() - datetime.timedelta(days=1)
            )
            db.add(order2)
            db.commit()
            db.refresh(order2)

            pay2 = Payment(
                transaction_id="TXN-CC-771239841",
                order_id=order2.id,
                gateway="HDFC Card Gateway",
                amount=Decimal("4599.00"),
                currency="INR",
                status=PaymentStatus.SUCCESS,
                payment_method="Visa Credit Card ending in 4092",
                refunded_amount=Decimal("0.00")
            )
            db.add(pay2)

            ticket2 = SupportTicket(
                ticket_number="TCK-9902",
                customer_id=c2.id,
                order_id=order2.id,
                subject="Received smart watch has scratches on screen",
                initial_question="I received my order ORD-2026-5541 yesterday, but there are scratches on the dial. How can I get a replacement?",
                status=TicketStatus.OPEN,
                priority=TicketPriority.MEDIUM,
                category="replacement",
                channel="email",
                created_at=datetime.datetime.utcnow() - datetime.timedelta(hours=2)
            )
            db.add(ticket2)
            db.commit()

        # 3. Seed Realistic Policies & Ingest with Embeddings
        policy_files = [
            {
                "title": "Cancellation & Refund Policy",
                "filename": "cancellation_and_refund_policy.md",
                "category": "policy",
                "content": """# MadadAI E-Commerce Customer Cancellation and Refund Policy

## 1. Pre-Dispatch Order Cancellations
When an order is cancelled prior to shipment or dispatch from our fulfillment centers:
- A 100% full refund is issued automatically to the original source payment method (UPI, NetBanking, Credit/Debit card).
- For UPI payments (Google Pay, PhonePe, Paytm, BHIM), the standard banking settlement timeframe is 5 to 7 business days from the cancellation timestamp.
- For Credit/Debit Card transactions, refunds typically reflect on the customer's card statement within 7 to 10 working days, subject to the issuing bank's settlement cycle.
- Authoritative database confirmation: Support agents must verify that the order has the status 'cancelled' and the payment has the status 'success' before recommending refund dispatch.

## 2. In-Transit and Delivered Orders
Orders that have already been dispatched or delivered cannot be cancelled outright. Customers must wait for delivery and initiate a Return Request via their dashboard.

## 3. Human Agent Review Required
AI resolution recommendations do not directly execute fund transfers. A qualified support specialist or finance supervisor must approve the refund resolution after confirming transaction IDs."""
            },
            {
                "title": "Damaged & Defective Items Policy",
                "filename": "damaged_and_defective_items_policy.md",
                "category": "policy",
                "content": """# Damaged, Defective or Incorrect Items Policy

## 1. 7-Day Replacement Window
Customers must report physically damaged items, manufacturing defects, or wrong item shipments within 7 calendar days of delivery.

## 2. Required Verification
- Photographs of the outer packaging, barcode label, and clear images of the damaged product or screen scratches.
- Once verified by the agent, a free reverse pickup will be scheduled within 24 to 48 hours.
- A replacement item of the same SKU will be dispatched immediately upon pickup scan by the courier partner."""
            },
            {
                "title": "Payment Failure & Auto-Reversal Guidelines",
                "filename": "payment_failure_guidelines.md",
                "category": "faq",
                "content": """# Payment Failure, Auto-Reversals and UPI Reconciliation

## 1. Amount Deducted but Order Not Placed
If money has been debited from a customer's bank account or UPI application but no order confirmation was generated:
- The payment gateway holds the transaction in an uncaptured pending state.
- Automated bank reconciliation will reverse the funds back to the remitting bank account within T+2 banking days.
- If the refund is not reflected after 48 banking hours, advise the customer to provide their UPI 12-digit UTR/RRN number for priority gateway trace."""
            }
        ]

        upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        for p_info in policy_files:
            existing = db.query(Document).filter(Document.title == p_info["title"]).first()
            if not existing:
                print(f"Indexing seed policy: {p_info['title']}...")
                file_path = os.path.join(upload_dir, p_info["filename"])
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(p_info["content"])

                doc = Document(
                    title=p_info["title"],
                    filename=p_info["filename"],
                    file_path=file_path,
                    file_type="md",
                    file_size_bytes=len(p_info["content"].encode("utf-8")),
                    doc_category=p_info["category"],
                    status=DocumentStatus.PROCESSING
                )
                db.add(doc)
                db.commit()
                db.refresh(doc)

                # Chunk and embed
                chunks = ingestion_service.chunk_text(p_info["content"], chunk_size=350, overlap=60, page_number=1)
                texts = [c["content"] for c in chunks]
                embeddings = embedding_service.embed_batch(texts)

                for idx, (c_data, emb) in enumerate(zip(chunks, embeddings)):
                    chunk_rec = DocumentChunk(
                        document_id=doc.id,
                        chunk_index=idx,
                        content=c_data["content"],
                        page_number=c_data["page_number"],
                        chunk_metadata={"word_count": c_data["word_count"]},
                        embedding=emb
                    )
                    db.add(chunk_rec)

                doc.total_chunks = len(chunks)
                doc.status = DocumentStatus.INDEXED
                doc.indexed_at = datetime.datetime.utcnow()
                db.commit()

        print("Seeding completed successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    init_db_and_seed()
