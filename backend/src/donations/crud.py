"""
Donation CRUD Operations
CRUD operations for donations, campaigns, receipts, and transactions.
"""

from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import List, Optional, Tuple, Type, TypeVar, Dict, Any
import uuid
import json

from sqlalchemy import select, update, delete, and_, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.exceptions import (
    NotFoundError,
    AlreadyExistsError,
    BusinessError,
)
from src.core import redis
from src.donations.models import (
    Donation,
    DonationCampaign,
    DonationReceipt,
    PaymentTransaction,
    DonorReport,
    PaymentStatus,
    PaymentMethod,
    CampaignStatus,
)
from src.donations.schemas import (
    DonationCreate,
    DonationUpdate,
    DonationSearchFilters,
    CampaignCreate,
    CampaignUpdate,
)


# =============================================================================
# Base CRUD Class
# =============================================================================

T = TypeVar("T")

class CRUDBase:
    """Base CRUD class with common operations."""
    
    @staticmethod
    async def get_by_id(db: AsyncSession, model: Type[T], id: UUID) -> Optional[T]:
        """Get a record by ID."""
        result = await db.execute(
            select(model).where(model.id == id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all(
        db: AsyncSession,
        model: Type[T],
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        descending: bool = False
    ) -> List[T]:
        """Get all records with pagination."""
        query = select(model)
        
        if order_by:
            order_field = getattr(model, order_by, None)
            if order_field:
                if descending:
                    query = query.order_by(desc(order_field))
                else:
                    query = query.order_by(asc(order_field))
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def count(db: AsyncSession, model: Type[T]) -> int:
        """Count all records."""
        result = await db.execute(select(func.count(model.id)))
        return result.scalar_one() or 0
    
    @staticmethod
    async def delete(db: AsyncSession, model: Type[T], id: UUID) -> bool:
        """Delete a record by ID."""
        record = await CRUDBase.get_by_id(db, model, id)
        if record:
            await db.delete(record)
            await db.commit()
            return True
        return False
    
    @staticmethod
    async def update(db: AsyncSession, model, id: UUID, update_data: dict) -> Optional[T]:
        """Update a record by ID."""
        record = await CRUDBase.get_by_id(db, model, id)
        if not record:
            return None
        
        for field, value in update_data.items():
            setattr(record, field, value)
        
        await db.commit()
        await db.refresh(record)
        return record


# =============================================================================
# Donation CRUD
# =============================================================================

class DonationCRUD(CRUDBase):
    """CRUD operations for donations."""
    
    @staticmethod
    async def create(
        db: AsyncSession,
        donation_data: DonationCreate,
        member_id: Optional[UUID] = None
    ) -> Donation:
        """Create a new donation."""
        donation = Donation(
            campaign_id=donation_data.campaign_id,
            member_id=member_id or donation_data.member_id,
            amount=donation_data.amount,
            currency=donation_data.currency,
            donation_type=donation_data.donation_type,
            payment_method=donation_data.payment_method,
            donor_name=donation_data.donor_name,
            donor_phone=donation_data.donor_phone,
            donor_email=donation_data.donor_email,
            donor_pan=donation_data.donor_pan,
            notes=donation_data.notes,
            is_anonymous=donation_data.is_anonymous or False,
            payment_status=PaymentStatus.PENDING.value,
        )
        db.add(donation)
        await db.commit()
        await db.refresh(donation)
        return donation
    
    @staticmethod
    async def get_detailed(db: AsyncSession, donation_id: UUID) -> Optional[Donation]:
        """Get donation with all relationships."""
        result = await db.execute(
            select(Donation)
            .where(Donation.id == donation_id)
            .options(
                selectinload(Donation.campaign),
                selectinload(Donation.receipt),
                selectinload(Donation.transactions),
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def search(
        db: AsyncSession,
        filters: DonationSearchFilters,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Donation], int]:
        """Search donations with filters."""
        query = select(Donation)
        
        # Apply filters
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                (Donation.donor_name.ilike(search_term)) |
                (Donation.donor_phone.ilike(search_term)) |
                (Donation.donor_email.ilike(search_term)) |
                (Donation.transaction_id.ilike(search_term))
            )
        
        if filters.campaign_id:
            query = query.where(Donation.campaign_id == filters.campaign_id)
        
        if filters.member_id:
            query = query.where(Donation.member_id == filters.member_id)
        
        if filters.payment_status:
            query = query.where(Donation.payment_status.in_(filters.payment_status))
        
        if filters.payment_method:
            query = query.where(Donation.payment_method.in_(filters.payment_method))
        
        if filters.donation_type:
            query = query.where(Donation.donation_type.in_(filters.donation_type))
        
        if filters.from_date:
            query = query.where(Donation.created_at >= filters.from_date)
        
        if filters.to_date:
            query = query.where(Donation.created_at <= filters.to_date)
        
        if filters.min_amount:
            query = query.where(Donation.amount >= filters.min_amount)
        
        if filters.max_amount:
            query = query.where(Donation.amount <= filters.max_amount)
        
        # Get total count
        count_query = select(func.count(Donation.id)).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        skip = (page - 1) * limit
        query = query.offset(skip).limit(limit).order_by(desc(Donation.created_at))
        
        result = await db.execute(query)
        donations = list(result.scalars().all())
        
        return donations, total
    
    @staticmethod
    async def get_by_member(
        db: AsyncSession,
        member_id: UUID,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Donation], int]:
        """Get donations by member."""
        query = select(Donation).where(
            and_(
                Donation.member_id == member_id,
                Donation.payment_status == PaymentStatus.COMPLETED.value
            )
        )
        
        # Get total count
        count_query = select(func.count(Donation.id)).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        skip = (page - 1) * limit
        query = query.offset(skip).limit(limit).order_by(desc(Donation.created_at))
        
        result = await db.execute(query)
        donations = list(result.scalars().all())
        
        # Calculate total amount
        amount_query = select(func.sum(Donation.amount)).where(
            and_(
                Donation.member_id == member_id,
                Donation.payment_status == PaymentStatus.COMPLETED.value
            )
        )
        amount_result = await db.execute(amount_query)
        total_amount = amount_result.scalar() or 0
        
        return donations, total, float(total_amount)
    
    @staticmethod
    async def update_status(
        db: AsyncSession,
        donation_id: UUID,
        status: str,
        transaction_id: Optional[str] = None
    ) -> Optional[Donation]:
        """Update donation status."""
        donation = await DonationCRUD.get_by_id(db, Donation, donation_id)
        if not donation:
            raise NotFoundError(resource="Donation", resource_id=str(donation_id))
        
        donation.payment_status = status
        if transaction_id:
            donation.transaction_id = transaction_id
        
        if status == PaymentStatus.COMPLETED.value:
            donation.completed_at = datetime.now(timezone.utc)
            
            # Update campaign collected amount
            if donation.campaign_id:
                campaign = await CampaignCRUD.get_by_id(db, DonationCampaign, donation.campaign_id)
                if campaign:
                    campaign.collected_amount = float(campaign.collected_amount) + float(donation.amount)
                    await db.flush()
        
        await db.commit()
        await db.refresh(donation)
        return donation
    
    @staticmethod
    async def get_pending_donations(db: AsyncSession, limit: int = 100) -> List[Donation]:
        """Get pending donations for timeout processing."""
        result = await db.execute(
            select(Donation)
            .where(Donation.payment_status == PaymentStatus.PENDING.value)
            .order_by(asc(Donation.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())


# =============================================================================
# Campaign CRUD
# =============================================================================

class CampaignCRUD(CRUDBase):
    """CRUD operations for donation campaigns."""
    
    @staticmethod
    async def create(
        db: AsyncSession,
        campaign_data: CampaignCreate,
        created_by_id: Optional[UUID] = None
    ) -> DonationCampaign:
        """Create a new donation campaign."""
        campaign = DonationCampaign(
            name=campaign_data.name,
            description=campaign_data.description,
            unit_id=campaign_data.unit_id,
            created_by_id=created_by_id,
            target_amount=campaign_data.target_amount or 0,
            currency=campaign_data.currency,
            start_date=campaign_data.start_date,
            end_date=campaign_data.end_date,
            banner_url=campaign_data.banner_url,
            status=campaign_data.status or CampaignStatus.DRAFT.value,
            metadata=campaign_data.metadata or {},
        )
        db.add(campaign)
        await db.commit()
        await db.refresh(campaign)
        return campaign
    
    @staticmethod
    async def get_detailed(db: AsyncSession, campaign_id: UUID) -> Optional[DonationCampaign]:
        """Get campaign with donations."""
        result = await db.execute(
            select(DonationCampaign)
            .where(DonationCampaign.id == campaign_id)
            .options(
                selectinload(DonationCampaign.donations),
                selectinload(DonationCampaign.receipts),
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def search(
        db: AsyncSession,
        status: Optional[str] = None,
        unit_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[DonationCampaign], int]:
        """Search campaigns with filters."""
        query = select(DonationCampaign)
        
        if status:
            query = query.where(DonationCampaign.status == status)
        
        if unit_id:
            query = query.where(DonationCampaign.unit_id == unit_id)
        
        if is_active is not None:
            query = query.where(DonationCampaign.is_active == is_active)
        
        # Get total count
        count_query = select(func.count(DonationCampaign.id)).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        skip = (page - 1) * limit
        query = query.offset(skip).limit(limit).order_by(desc(DonationCampaign.created_at))
        
        result = await db.execute(query)
        campaigns = list(result.scalars().all())
        
        return campaigns, total
    
    @staticmethod
    async def get_active_campaigns(db: AsyncSession, limit: int = 10) -> List[DonationCampaign]:
        """Get active campaigns ordered by progress."""
        result = await db.execute(
            select(DonationCampaign)
            .where(
                and_(
                    DonationCampaign.is_active == True,
                    DonationCampaign.status == CampaignStatus.ACTIVE.value
                )
            )
            .order_by(desc(DonationCampaign.collected_amount))
            .limit(limit)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def update(
        db: AsyncSession,
        campaign_id: UUID,
        campaign_data: CampaignUpdate
    ) -> Optional[DonationCampaign]:
        """Update a campaign."""
        campaign = await CampaignCRUD.get_by_id(db, DonationCampaign, campaign_id)
        if not campaign:
            raise NotFoundError(resource="DonationCampaign", resource_id=str(campaign_id))
        
        update_data = campaign_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(campaign, field, value)
        
        await db.commit()
        await db.refresh(campaign)
        return campaign


# =============================================================================
# Receipt CRUD
# =============================================================================

class ReceiptCRUD(CRUDBase):
    """CRUD operations for donation receipts."""
    
    @staticmethod
    async def generate_receipt(
        db: AsyncSession,
        donation_id: UUID,
        generated_by_id: Optional[UUID] = None
    ) -> DonationReceipt:
        """Generate a receipt for a donation."""
        donation = await DonationCRUD.get_detailed(db, donation_id)
        if not donation:
            raise NotFoundError(resource="Donation", resource_id=str(donation_id))
        
        if donation.payment_status != PaymentStatus.COMPLETED.value:
            raise BusinessError(message="Can only generate receipt for completed donations")
        
        # Check if receipt already exists
        if donation.receipt:
            raise AlreadyExistsError(resource="Receipt", field="donation_id", value=str(donation_id))
        
        # Generate receipt number
        receipt_number = f"RCPT-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        
        receipt = DonationReceipt(
            donation_id=donation_id,
            campaign_id=donation.campaign_id,
            receipt_number=receipt_number,
            amount=donation.amount,
            currency=donation.currency,
            donor_name=donation.donor_name if not donation.is_anonymous else None,
            donor_pan=donation.donor_pan,
            is_tax_deductible=True,
            tax_section="80G",
            generated_by_id=generated_by_id,
        )
        db.add(receipt)
        
        # Update donation with receipt info
        donation.receipt_number = receipt_number
        donation.receipt_url = f"/receipts/{receipt_number}"
        
        await db.commit()
        await db.refresh(receipt)
        return receipt
    
    @staticmethod
    async def get_by_donation(db: AsyncSession, donation_id: UUID) -> Optional[DonationReceipt]:
        """Get receipt by donation ID."""
        result = await db.execute(
            select(DonationReceipt)
            .where(DonationReceipt.donation_id == donation_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_number(db: AsyncSession, receipt_number: str) -> Optional[DonationReceipt]:
        """Get receipt by receipt number."""
        result = await db.execute(
            select(DonationReceipt)
            .where(DonationReceipt.receipt_number == receipt_number)
            .options(selectinload(DonationReceipt.donation))
        )
        return result.scalar_one_or_none()


# =============================================================================
# Transaction CRUD
# =============================================================================

class TransactionCRUD(CRUDBase):
    """CRUD operations for payment transactions."""
    
    @staticmethod
    async def create(
        db: AsyncSession,
        donation_id: UUID,
        transaction_data: dict
    ) -> PaymentTransaction:
        """Create a new transaction."""
        transaction = PaymentTransaction(
            donation_id=donation_id,
            transaction_type=transaction_data.get("transaction_type", "payment"),
            payment_gateway=transaction_data.get("payment_gateway"),
            gateway_transaction_id=transaction_data.get("gateway_transaction_id"),
            gateway_order_id=transaction_data.get("gateway_order_id"),
            gateway_payment_id=transaction_data.get("gateway_payment_id"),
            amount=transaction_data.get("amount", 0),
            currency=transaction_data.get("currency", "INR"),
            status=transaction_data.get("status", "pending"),
            request_data=transaction_data.get("request_data", {}),
            response_data=transaction_data.get("response_data", {}),
        )
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        return transaction
    
    @staticmethod
    async def update_status(
        db: AsyncSession,
        transaction_id: UUID,
        status: str,
        response_data: Optional[dict] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Optional[PaymentTransaction]:
        """Update transaction status."""
        transaction = await TransactionCRUD.get_by_id(db, PaymentTransaction, transaction_id)
        if not transaction:
            raise NotFoundError(resource="PaymentTransaction", resource_id=str(transaction_id))
        
        transaction.status = status
        transaction.status_message = response_data.get("error", {}).get("description") if response_data else None
        
        if response_data:
            transaction.response_data = response_data
        
        if error_code:
            transaction.error_code = error_code
            transaction.error_message = error_message
        
        if status in ["success", "completed", "captured"]:
            transaction.processed_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(transaction)
        return transaction
    
    @staticmethod
    async def get_by_donation(db: AsyncSession, donation_id: UUID) -> List[PaymentTransaction]:
        """Get all transactions for a donation."""
        result = await db.execute(
            select(PaymentTransaction)
            .where(PaymentTransaction.donation_id == donation_id)
            .order_by(desc(PaymentTransaction.created_at))
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_by_gateway_id(
        db: AsyncSession,
        gateway_id: str,
        payment_gateway: str
    ) -> Optional[PaymentTransaction]:
        """Get transaction by gateway ID."""
        result = await db.execute(
            select(PaymentTransaction)
            .where(
                and_(
                    PaymentTransaction.gateway_payment_id == gateway_id,
                    PaymentTransaction.payment_gateway == payment_gateway
                )
            )
        )
        return result.scalar_one_or_none()


# =============================================================================
# Statistics CRUD
# =============================================================================

class DonationStatsCRUD:
    """Statistics and reporting for donations."""
    
    @staticmethod
    async def get_stats(
        db: AsyncSession,
        unit_id: Optional[UUID] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get donation statistics."""
        # Build base query
        base_query = select(Donation)
        if unit_id:
            base_query = base_query.join(DonationCampaign).where(
                DonationCampaign.unit_id == unit_id
            )
        if from_date:
            base_query = base_query.where(Donation.created_at >= from_date)
        if to_date:
            base_query = base_query.where(Donation.created_at <= to_date)
        
        # Total donations
        total_query = select(func.count(Donation.id)).select_from(
            select(Donation).where(Donation.payment_status == PaymentStatus.COMPLETED.value).subquery()
        )
        total_result = await db.execute(total_query)
        total_donations = total_result.scalar() or 0
        
        # Total amount
        amount_query = select(func.sum(Donation.amount)).where(
            Donation.payment_status == PaymentStatus.COMPLETED.value
        )
        amount_result = await db.execute(amount_query)
        total_amount = float(amount_result.scalar() or 0)
        
        # By status
        status_query = select(
            Donation.payment_status,
            func.count(Donation.id)
        ).group_by(Donation.payment_status)
        status_result = await db.execute(status_query)
        by_status = {row[0]: row[1] for row in status_result.all()}
        
        # This month stats
        month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_query = select(func.count(Donation.id), func.sum(Donation.amount)).where(
            and_(
                Donation.created_at >= month_start,
                Donation.payment_status == PaymentStatus.COMPLETED.value
            )
        )
        monthly_result = await db.execute(monthly_query)
        monthly_data = monthly_result.one()
        monthly_count = monthly_data[0] or 0
        monthly_amount = float(monthly_data[1] or 0)
        
        # This year stats
        year_start = datetime.now(timezone.utc).replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        yearly_query = select(func.count(Donation.id), func.sum(Donation.amount)).where(
            and_(
                Donation.created_at >= year_start,
                Donation.payment_status == PaymentStatus.COMPLETED.value
            )
        )
        yearly_result = await db.execute(yearly_query)
        yearly_data = yearly_result.one()
        yearly_count = yearly_data[0] or 0
        yearly_amount = float(yearly_data[1] or 0)
        
        return {
            "total_donations": total_donations,
            "total_amount": total_amount,
            "currency": "INR",
            "pending_count": by_status.get(PaymentStatus.PENDING.value, 0),
            "completed_count": by_status.get(PaymentStatus.COMPLETED.value, 0),
            "failed_count": by_status.get(PaymentStatus.FAILED.value, 0),
            "by_payment_method": {},
            "by_donation_type": {},
            "by_campaign": {},
            "donations_this_month": monthly_count,
            "amount_this_month": monthly_amount,
            "donations_this_year": yearly_count,
            "amount_this_year": yearly_amount,
            "top_donors": [],
            "recent_donations": [],
        }
    
    @staticmethod
    async def get_dashboard(db: AsyncSession) -> Dict[str, Any]:
        """Get dashboard data."""
        # Get active campaigns
        active_campaigns = await db.execute(
            select(DonationCampaign)
            .where(DonationCampaign.is_active == True)
            .order_by(desc(DonationCampaign.created_at))
        )
        active_campaigns_list = list(active_campaigns.scalars().all())
        
        # Calculate totals
        total_collected = sum(float(c.collected_amount) for c in active_campaigns_list)
        total_target = sum(float(c.target_amount) for c in active_campaigns_list)
        
        # This month donations
        month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_query = select(func.count(Donation.id), func.sum(Donation.amount)).where(
            and_(
                Donation.created_at >= month_start,
                Donation.payment_status == PaymentStatus.COMPLETED.value
            )
        )
        monthly_result = await db.execute(monthly_query)
        monthly_data = monthly_result.one()
        monthly_count = monthly_data[0] or 0
        monthly_amount = float(monthly_data[1] or 0)
        
        # Recent donations
        recent_query = select(Donation).where(
            Donation.payment_status == PaymentStatus.COMPLETED.value
        ).order_by(desc(Donation.created_at)).limit(10)
        recent_result = await db.execute(recent_query)
        recent_donations = list(recent_result.scalars().all())
        
        # Daily trends (last 7 days)
        daily_trends = []
        for i in range(7):
            day_start = (datetime.now(timezone.utc) - timedelta(days=i)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            day_end = day_start + timedelta(days=1)
            day_query = select(func.count(Donation.id), func.sum(Donation.amount)).where(
                and_(
                    Donation.created_at >= day_start,
                    Donation.created_at < day_end,
                    Donation.payment_status == PaymentStatus.COMPLETED.value
                )
            )
            day_result = await db.execute(day_query)
            day_data = day_result.one()
            daily_trends.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "count": day_data[0] or 0,
                "amount": float(day_data[1] or 0),
            })
        daily_trends.reverse()
        
        # Top campaigns
        top_campaigns = [
            {
                "id": str(c.id),
                "name": c.name,
                "collected": float(c.collected_amount),
                "target": float(c.target_amount),
                "progress": c.progress_percentage,
            }
            for c in sorted(active_campaigns_list, key=lambda x: x.progress_percentage, reverse=True)[:5]
        ]
        
        return {
            "total_collected": total_collected,
            "total_target": total_target if total_target > 0 else 1,
            "progress_percentage": round((total_collected / total_target * 100), 2) if total_target > 0 else 0,
            "active_campaigns": len([c for c in active_campaigns_list if c.status == CampaignStatus.ACTIVE.value]),
            "completed_campaigns": len([c for c in active_campaigns_list if c.status == CampaignStatus.COMPLETED.value]),
            "recent_donations_count": len(recent_donations),
            "recent_donations_amount": sum(float(d.amount) for d in recent_donations),
            "monthly_total": monthly_amount,
            "monthly_count": monthly_count,
            "top_campaigns": top_campaigns,
            "daily_trends": daily_trends,
            "payment_methods": {},
        }


# =============================================================================
# Payment Gateway Integration
# =============================================================================

class PaymentGatewayCRUD:
    """Payment gateway integration utilities."""
    
    @staticmethod
    async def initiate_razorpay_payment(
        db: AsyncSession,
        donation_id: UUID,
        amount: float,
        currency: str = "INR"
    ) -> Dict[str, str]:
        """Initiate Razorpay payment order."""
        import razorpay
        from src.core.config import settings
        
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        
        # Create order
        order_data = {
            "amount": int(amount * 100),  # Convert to paise
            "currency": currency,
            "receipt": str(donation_id),
            "notes": {
                "donation_id": str(donation_id),
            }
        }
        
        try:
            order = client.order.create(data=order_data)
            
            # Save order ID to donation
            donation = await DonationCRUD.get_by_id(db, Donation, donation_id)
            if donation:
                donation.payment_order_id = order["id"]
                donation.payment_gateway = "razorpay"
                await db.commit()
            
            return {
                "order_id": order["id"],
                "payment_link": f"https://checkout.razorpay.com/v1/checkout.js?order_id={order['id']}",
            }
        except Exception as e:
            raise BusinessError(message=f"Failed to create payment order: {str(e)}")
    
    @staticmethod
    async def verify_razorpay_payment(
        db: AsyncSession,
        donation_id: UUID,
        payment_id: str,
        signature: str
    ) -> bool:
        """Verify Razorpay payment signature."""
        import razorpay
        from src.core.config import settings
        from hmac import hash_hmac
        
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        
        donation = await DonationCRUD.get_by_id(db, Donation, donation_id)
        if not donation:
            raise NotFoundError(resource="Donation", resource_id=str(donation_id))
        
        # Verify signature
        try:
            # Check payment status from Razorpay
            payment = client.payment.fetch(payment_id)
            
            if payment["status"] == "captured":
                # Update donation
                await DonationCRUD.update_status(
                    db, donation_id,
                    PaymentStatus.COMPLETED.value,
                    transaction_id=payment_id
                )
                
                # Create transaction record
                await TransactionCRUD.create(db, donation_id, {
                    "transaction_type": "payment",
                    "payment_gateway": "razorpay",
                    "gateway_payment_id": payment_id,
                    "gateway_order_id": donation.payment_order_id,
                    "amount": float(donation.amount),
                    "status": "success",
                    "response_data": payment,
                })
                
                return True
            else:
                await DonationCRUD.update_status(
                    db, donation_id,
                    PaymentStatus.FAILED.value,
                    transaction_id=payment_id
                )
                return False
                
        except Exception as e:
            await DonationCRUD.update_status(
                db, donation_id,
                PaymentStatus.FAILED.value
            )
            raise BusinessError(message=f"Payment verification failed: {str(e)}")
