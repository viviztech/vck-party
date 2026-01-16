"""
Donation Dependencies
FastAPI dependencies for donation routes.
"""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import (
    NotFoundError,
    AuthorizationError,
    BusinessError,
)
from src.core.security import get_current_user
from src.auth.models import User

from src.donations.models import Donation, DonationCampaign, PaymentStatus
from src.donations.crud import DonationCRUD, CampaignCRUD


# =============================================================================
# Donation Dependencies
# =============================================================================

async def get_donation_by_id(
    donation_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Donation:
    """
    Get a donation by ID.
    
    Raises:
        NotFoundError: If donation not found
    """
    donation = await DonationCRUD.get_detailed(db, donation_id)
    if not donation:
        raise NotFoundError(resource="Donation", resource_id=str(donation_id))
    return donation


async def check_donation_view_permission(
    request: Request,
    donation: Donation = Depends(get_donation_by_id),
    current_user: User = Depends(get_current_user),
) -> Donation:
    """
    Check if user can view a donation.
    
    - Users can view their own donations
    - Admins can view all donations
    - Donations with anonymous flag have limited info visible
    """
    # Admin has access to all donations
    if current_user.is_admin():
        return donation
    
    # Check if user owns the donation (through member profile)
    if hasattr(current_user, 'member_profile') and current_user.member_profile:
        if donation.member_id == current_user.member_profile.id:
            return donation
    
    # Check if user is the donor (phone match for non-member donations)
    if donation.donor_phone and hasattr(current_user, 'phone'):
        if donation.donor_phone == current_user.phone:
            return donation
    
    # If donation is anonymous, only return limited info
    if donation.is_anonymous:
        raise AuthorizationError(message="Access denied to this donation")
    
    # For other cases, require admin role
    raise AuthorizationError(message="You don't have permission to view this donation")


async def check_donation_edit_permission(
    request: Request,
    donation: Donation = Depends(get_donation_by_id),
    current_user: User = Depends(get_current_user),
) -> Donation:
    """
    Check if user can edit a donation.
    
    - Only admins can edit donations
    - Cannot edit completed donations (except status)
    """
    # Only admins can edit donations
    if not current_user.is_admin():
        raise AuthorizationError(message="Only admins can edit donations")
    
    # Cannot edit completed donations (except status changes)
    if donation.payment_status == PaymentStatus.COMPLETED.value:
        raise BusinessError(message="Cannot edit completed donations")
    
    return donation


async def check_donation_delete_permission(
    request: Request,
    donation: Donation = Depends(get_donation_by_id),
    current_user: User = Depends(get_current_user),
) -> Donation:
    """
    Check if user can delete a donation.
    
    - Only admins can delete donations
    - Cannot delete completed donations
    """
    # Only admins can delete donations
    if not current_user.is_admin():
        raise AuthorizationError(message="Only admins can delete donations")
    
    # Cannot delete completed donations
    if donation.payment_status == PaymentStatus.COMPLETED.value:
        raise BusinessError(message="Cannot delete completed donations")
    
    return donation


# =============================================================================
# Campaign Dependencies
# =============================================================================

async def get_campaign_by_id(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> DonationCampaign:
    """
    Get a campaign by ID.
    
    Raises:
        NotFoundError: If campaign not found
    """
    campaign = await CampaignCRUD.get_detailed(db, campaign_id)
    if not campaign:
        raise NotFoundError(resource="DonationCampaign", resource_id=str(campaign_id))
    return campaign


async def check_campaign_view_permission(
    request: Request,
    campaign: DonationCampaign = Depends(get_campaign_by_id),
    current_user: User = Depends(get_current_user),
) -> DonationCampaign:
    """
    Check if user can view a campaign.
    
    - All authenticated users can view active campaigns
    - Only admins can view draft campaigns
    """
    # Draft campaigns are only visible to admins
    if campaign.status == "draft" and not current_user.is_admin():
        raise AuthorizationError(message="Cannot view draft campaigns")
    
    return campaign


async def check_campaign_edit_permission(
    request: Request,
    campaign: DonationCampaign = Depends(get_campaign_by_id),
    current_user: User = Depends(get_current_user),
) -> DonationCampaign:
    """
    Check if user can edit a campaign.
    
    - Only admins can edit campaigns
    """
    if not current_user.is_admin():
        raise AuthorizationError(message="Only admins can edit campaigns")
    
    return campaign


async def check_campaign_delete_permission(
    request: Request,
    campaign: DonationCampaign = Depends(get_campaign_by_id),
    current_user: User = Depends(get_current_user),
) -> DonationCampaign:
    """
    Check if user can delete a campaign.
    
    - Only admins can delete campaigns
    - Cannot delete campaigns with completed donations
    """
    if not current_user.is_admin():
        raise AuthorizationError(message="Only admins can delete campaigns")
    
    # Check if campaign has completed donations
    if campaign.donations:
        completed_donations = [d for d in campaign.donations 
                              if d.payment_status == PaymentStatus.COMPLETED.value]
        if completed_donations:
            raise BusinessError(message="Cannot delete campaign with completed donations")
    
    return campaign


# =============================================================================
# Donation Creation Dependencies
# =============================================================================

async def get_current_member_id(
    current_user: User = Depends(get_current_user),
) -> Optional[UUID]:
    """
    Get the current user's member ID.
    
    Returns None if user is not a member.
    """
    if hasattr(current_user, 'member_profile') and current_user.member_profile:
        return current_user.member_profile.id
    return None


# =============================================================================
# Admin Check Dependency
# =============================================================================

async def require_donation_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Require donation admin role.
    
    Raises:
        AuthorizationError: If user is not an admin
    """
    if not current_user.is_admin():
        raise AuthorizationError(message="Admin access required")
    return current_user


# =============================================================================
# Payment Verification Dependencies
# =============================================================================

async def verify_payment_signature(
    request: Request,
    payment_id: str,
    signature: str,
    order_id: str,
    db: AsyncSession = Depends(get_db),
) -> bool:
    """
    Verify payment gateway signature.
    
    This is a placeholder for signature verification.
    In production, implement proper signature verification.
    """
    # TODO: Implement actual signature verification
    # For now, just return True
    return True
