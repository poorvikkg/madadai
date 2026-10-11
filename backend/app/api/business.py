from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.entities import Customer, Order, Payment, SupportTicket
from app.schemas.api_schemas import CustomerResponse, OrderResponse, TicketResponse
from app.api.auth import get_current_user

router = APIRouter(prefix="/business", tags=["Business Data"])

@router.get("/tickets", response_model=List[TicketResponse])
def list_tickets(
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(SupportTicket)
    if status:
        query = query.filter(SupportTicket.status == status)
    return query.order_by(SupportTicket.created_at.desc()).limit(limit).all()

@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@router.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
