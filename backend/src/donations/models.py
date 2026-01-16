"""
Donation Models
SQLAlchemy models for donations, campaigns, receipts, and transactions.
"""

from datetime import datetime, timezone
from typing import List, TYPE_CHECKING
import uuid
import enum

from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, Integer, 
    ForeignKey, Enum, Numeric, JSON, ARRAY
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.core.database import Base


# =============================================================================
# Enums
# =============================================================================

class PaymentStatus(str, enum.Enum):
    """Payment status for donations."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PaymentMethod(str, enum.Enum):
    """Payment methods for donations."""
    UPI = "upi"
    CARD = "card"
    NETBANKING = "netbanking"
    CASH = "cash"
    CHEQUE = "cheque"
    DEMAND_DRAFT = "demand_draft"
    OTHER = "other"


class PaymentGateway(str, enum.Enum):
    """Payment gateway providers."""
    RAZORPAY = "razorpay"
    STRIPE = "stripe"
    PAYTM = "paytm"
    PHONEPE = "phonepe"
    MANUAL = "manual"


class DonationType(str, enum.Enum):
    """Type of donation."""
    GENERAL = "general"
    CAMPAIGN = "campaign"
    EVENT = "event"
    EMERGENCY = "emergency"
    MEMBER_CONTRIBUTION = "member_contribution"
    OTHER = "other"


class CampaignStatus(str, enum.Enum):
    """Donation campaign status."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# =============================================================================
# Donation Campaign Model
# =============================================================================

class DonationCampaign(Base):
    """
    Donation campaign model for fundraising campaigns.
    """
    __tablename__ = "donation_campaigns"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Organization
    unit_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organization_units.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Financial goals
    target_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    collected_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    
    # Schedule
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=CampaignStatus.DRAFT.value,
        nullable=False,
        index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    # Media
    banner_url: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Extra data
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    unit: Mapped["OrganizationUnit"] = relationship("OrganizationUnit", foreign_keys=[unit_id])
    created_by: Mapped["Member"] = relationship("Member", foreign_keys=[created_by_id])
    donations: Mapped[List["Donation"]] = relationship(
        "Donation",
        back_populates="campaign",
        cascade="all, delete-orphan"
    )
    receipts: Mapped[List["DonationReceipt"]] = relationship(
        "DonationReceipt",
        back_populates="campaign",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<DonationCampaign(id={self.id}, name={self.name}, status={self.status})>"
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress towards target."""
        if self.target_amount <= 0:
            return 0
        return round((float(self.collected_amount) / float(self.target_amount)) * 100, 2)


# =============================================================================
# Donation Model
# =============================================================================

class Donation(Base):
    """
    Donation model for member and public donations.
    """
    __tablename__ = "donations"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Campaign reference
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("donation_campaigns.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Member reference (for member donations)
    member_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Donation details
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    donation_type: Mapped[str] = mapped_column(
        String(50),
        default=DonationType.GENERAL.value,
        nullable=False
    )
    
    # Payment details
    payment_method: Mapped[str] = mapped_column(String(50), nullable=True)
    payment_gateway: Mapped[str] = mapped_column(String(50), nullable=True)
    transaction_id: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    payment_order_id: Mapped[str] = mapped_column(String(255), nullable=True)  # Razorpay order ID
    payment_status: Mapped[str] = mapped_column(
        String(20),
        default=PaymentStatus.PENDING.value,
        nullable=False,
        index=True
    )
    
    # Donor info (for non-member donations)
    donor_name: Mapped[str] = mapped_column(String(255), nullable=True)
    donor_phone: Mapped[str] = mapped_column(String(15), nullable=True, index=True)
    donor_email: Mapped[str] = mapped_column(String(255), nullable=True)
    donor_pan: Mapped[str] = mapped_column(String(20), nullable=True)  # For tax receipts
    
    # Receipt info
    receipt_number: Mapped[str] = mapped_column(String(50), nullable=True, index=True)
    receipt_url: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Notes
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True
    )
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    campaign: Mapped["DonationCampaign"] = relationship("DonationCampaign", back_populates="donations")
    member: Mapped["Member"] = relationship("Member")
    receipt: Mapped["DonationReceipt"] = relationship(
        "DonationReceipt",
        back_populates="donation",
        uselist=False,
        cascade="all, delete-orphan"
    )
    transactions: Mapped[List["PaymentTransaction"]] = relationship(
        "PaymentTransaction",
        back_populates="donation",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Donation(id={self.id}, amount={self.amount}, status={self.payment_status})>"


# =============================================================================
# Donation Receipt Model
# =============================================================================

class DonationReceipt(Base):
    """
    Donation receipt model for generated receipts.
    """
    __tablename__ = "donation_receipts"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    
    donation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("donations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("donation_campaigns.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Receipt details
    receipt_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    
    # Donor info (frozen at time of receipt generation)
    donor_name: Mapped[str] = mapped_column(String(255), nullable=True)
    donor_address: Mapped[str] = mapped_column(Text, nullable=True)
    donor_pan: Mapped[str] = mapped_column(String(20), nullable=True)
    
    # Receipt file
    receipt_url: Mapped[str] = mapped_column(Text, nullable=True)
    receipt_pdf_path: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Tax info
    is_tax_deductible: Mapped[bool] = mapped_column(Boolean, default=True)
    tax_section: Mapped[str] = mapped_column(String(50), nullable=True)  # e.g., "80G"
    
    # Generation info
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    generated_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    donation: Mapped["Donation"] = relationship("Donation", back_populates="receipt")
    campaign: Mapped["DonationCampaign"] = relationship("DonationCampaign", back_populates="receipts")
    generated_by: Mapped["Member"] = relationship("Member", foreign_keys=[generated_by_id])
    
    def __repr__(self) -> str:
        return f"<DonationReceipt(id={self.id}, receipt_number={self.receipt_number}, amount={self.amount})>"


# =============================================================================
# Payment Transaction Model
# =============================================================================

class PaymentTransaction(Base):
    """
    Payment transaction model for tracking payment gateway transactions.
    """
    __tablename__ = "payment_transactions"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    
    donation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("donations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Transaction details
    transaction_type: Mapped[str] = mapped_column(String(50), default="payment")  # payment, refund, capture
    payment_gateway: Mapped[str] = mapped_column(String(50), nullable=True)
    
    # Gateway-specific IDs
    gateway_transaction_id: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    gateway_order_id: Mapped[str] = mapped_column(String(255), nullable=True)
    gateway_payment_id: Mapped[str] = mapped_column(String(255), nullable=True)
    gateway_refund_id: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Amount
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    status_message: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Request/Response data (JSON)
    request_data: Mapped[dict] = mapped_column(JSON, default=dict)
    response_data: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Error info
    error_code: Mapped[str] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True
    )
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    donation: Mapped["Donation"] = relationship("Donation", back_populates="transactions")
    
    def __repr__(self) -> str:
        return f"<PaymentTransaction(id={self.id}, amount={self.amount}, status={self.status})>"


# =============================================================================
# Donor Report Model
# =============================================================================

class DonorReport(Base):
    """
    Donor report model for periodic donor reports.
    """
    __tablename__ = "donor_reports"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Report details
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)  # monthly, quarterly, annual
    member_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Period
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Report data
    total_donations: Mapped[int] = mapped_column(Integer, default=0)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    
    # Donation breakdown
    by_campaign: Mapped[dict] = mapped_column(JSON, default=dict)
    by_month: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Report file
    report_url: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Timestamps
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    member: Mapped["Member"] = relationship("Member")
    
    def __repr__(self) -> str:
        return f"<DonorReport(id={self.id}, member_id={self.member_id}, period={self.period_start.date()})>"


# =============================================================================
# Import for relationships (avoid circular imports)
# =============================================================================

if TYPE_CHECKING:
    from src.auth.models import User, Member
    from src.hierarchy.models import OrganizationUnit
