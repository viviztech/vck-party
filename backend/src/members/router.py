"""
Member Router
API routes for member management.
"""

from datetime import datetime, timezone
from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import (
    NotFoundError,
    AlreadyExistsError,
    ValidationError,
    AuthorizationError,
)
from src.core.security import get_current_user
from src.auth.models import User

from src.members.schemas import (
    MemberCreate,
    MemberUpdate,
    MemberResponse,
    MemberDetailResponse,
    MemberListResponse,
    MemberSearchFilters,
    MemberProfileCreate,
    MemberProfileUpdate,
    MemberProfileResponse,
    MemberFamilyCreate,
    MemberFamilyUpdate,
    MemberFamilyResponse,
    MemberDocumentCreate,
    MemberDocumentResponse,
    MemberTagAdd,
    MemberTagResponse,
    MemberNoteCreate,
    MemberNoteUpdate,
    MemberNoteResponse,
    MembershipHistoryResponse,
    MemberStats,
    MemberStatsResponse,
    MemberBulkImport,
    MemberBulkImportResult,
    MemberExportRequest,
    FamilyTreeNode,
)
from src.members.deps import (
    get_member_by_id,
    get_active_member_by_id,
    check_member_view_permission,
    check_member_edit_permission,
    getPaginationParams,
)
from src.members.crud import (
    MemberCRUD,
    MemberProfileCRUD,
    MemberFamilyCRUD,
    MemberDocumentCRUD,
    MemberNoteCRUD,
    MemberTagCRUD,
    MemberStatsCRUD,
    MemberBulkCRUD,
)
from src.members.models import MembershipStatus


router = APIRouter(prefix="/members", tags=["Members"])


# =============================================================================
# Health Check
# =============================================================================

@router.get("/health")
async def members_health_check():
    """Health check endpoint for members service."""
    return {"status": "healthy", "service": "members"}


# =============================================================================
# Member CRUD
# =============================================================================

@router.get("", response_model=MemberListResponse)
async def list_members(
    request: Request,
    search: Optional[str] = None,
    status_filter: Optional[List[str]] = Query(None),
    district: Optional[str] = None,
    constituency: Optional[str] = None,
    ward: Optional[str] = None,
    gender: Optional[str] = None,
    occupation: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List/search members with filters.
    
    Supports pagination and filtering by various criteria.
    """
    page, limit = getPaginationParams(page, limit)
    
    filters = MemberSearchFilters(
        search=search,
        status=status_filter,
        district=district,
        constituency=constituency,
        ward=ward,
        gender=gender,
        occupation=occupation,
    )
    
    members, total = await MemberCRUD.search(db, filters, page, limit)
    
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    
    return MemberListResponse(
        members=[MemberResponse.model_validate(m) for m in members],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.post("", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def create_member(
    member_data: MemberCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new member.
    
    Creates a new member with pending status.
    """
    try:
        member = await MemberCRUD.create(db, member_data)
        return MemberResponse.model_validate(member)
    except AlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=e.to_dict())


@router.get("/{member_id}", response_model=MemberDetailResponse)
async def get_member(
    request: Request,
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get member by ID with full details.
    """
    member = await MemberCRUD.get_detailed(db, member_id)
    if not member:
        raise NotFoundError(resource="Member", resource_id=str(member_id))
    
    return MemberDetailResponse.model_validate(member)


@router.put("/{member_id}", response_model=MemberResponse)
async def update_member(
    request: Request,
    member_id: UUID,
    member_data: MemberUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update member information.
    """
    try:
        member = await MemberCRUD.update(db, member_id, member_data)
        if not member:
            raise NotFoundError(resource="Member", resource_id=str(member_id))
        return MemberResponse.model_validate(member)
    except AlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=e.to_dict())


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(
    request: Request,
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Soft delete a member.
    """
    success = await MemberCRUD.soft_delete(db, member_id)
    if not success:
        raise NotFoundError(resource="Member", resource_id=str(member_id))


# =============================================================================
# Member Profile
# =============================================================================

@router.get("/{member_id}/profile", response_model=MemberProfileResponse)
async def get_member_profile(
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get member profile.
    """
    profile = await MemberProfileCRUD.get_by_member_id(db, member_id)
    if not profile:
        raise NotFoundError(resource="MemberProfile", resource_id=str(member_id))
    return MemberProfileResponse.model_validate(profile)


@router.post("/{member_id}/profile", response_model=MemberProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_member_profile(
    member_id: UUID,
    profile_data: MemberProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create member profile.
    """
    # Check if profile already exists
    existing = await MemberProfileCRUD.get_by_member_id(db, member_id)
    if existing:
        raise AlreadyExistsError(resource="MemberProfile", field="member_id", value=str(member_id))
    
    profile = await MemberProfileCRUD.create(db, member_id, profile_data)
    return MemberProfileResponse.model_validate(profile)


@router.put("/{member_id}/profile", response_model=MemberProfileResponse)
async def update_member_profile(
    member_id: UUID,
    profile_data: MemberProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update member profile.
    """
    profile = await MemberProfileCRUD.update(db, member_id, profile_data)
    if not profile:
        raise NotFoundError(resource="MemberProfile", resource_id=str(member_id))
    return MemberProfileResponse.model_validate(profile)


# =============================================================================
# Member Family
# =============================================================================

@router.get("/{member_id}/family", response_model=List[MemberFamilyResponse])
async def get_member_family(
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get member's family relationships.
    """
    family = await MemberFamilyCRUD.get_family_tree(db, member_id)
    return [MemberFamilyResponse.model_validate(f) for f in family]


@router.post("/{member_id}/family", response_model=MemberFamilyResponse, status_code=status.HTTP_201_CREATED)
async def add_family_member(
    member_id: UUID,
    family_data: MemberFamilyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Add a family relationship.
    """
    try:
        family = await MemberFamilyCRUD.add_relationship(db, member_id, family_data)
        return MemberFamilyResponse.model_validate(family)
    except AlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=e.to_dict())


@router.put("/{member_id}/family/{family_id}", response_model=MemberFamilyResponse)
async def update_family_relationship(
    member_id: UUID,
    family_id: UUID,
    family_data: MemberFamilyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a family relationship.
    """
    family = await MemberFamilyCRUD.update_relationship(db, family_id, family_data)
    if not family:
        raise NotFoundError(resource="MemberFamily", resource_id=str(family_id))
    return MemberFamilyResponse.model_validate(family)


@router.delete("/{member_id}/family/{family_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_family_member(
    member_id: UUID,
    family_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Remove a family relationship.
    """
    success = await MemberFamilyCRUD.remove_relationship(db, family_id)
    if not success:
        raise NotFoundError(resource="MemberFamily", resource_id=str(family_id))


@router.get("/{member_id}/family-tree", response_model=FamilyTreeNode)
async def get_family_tree(
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get member's family tree (hierarchical).
    """
    # TODO: Implement hierarchical family tree using ltree
    family = await MemberFamilyCRUD.get_family_tree(db, member_id)
    
    # Build tree structure (simplified)
    tree = FamilyTreeNode(
        member_id=member_id,
        name="Member",
        relationship_type="self",
        children=[]
    )
    
    return tree


# =============================================================================
# Member Documents
# =============================================================================

@router.get("/{member_id}/documents", response_model=List[MemberDocumentResponse])
async def get_member_documents(
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get member's documents.
    """
    documents = await MemberDocumentCRUD.get_by_member_id(db, member_id)
    return [MemberDocumentResponse.model_validate(d) for d in documents]


@router.post("/{member_id}/documents", response_model=MemberDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    member_id: UUID,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a document for a member.
    """
    # TODO: Implement file upload to storage
    # For now, just create the document record
    document_data = MemberDocumentCreate(
        document_type=document_type,
        file_name=file.filename,
        file_path=f"/uploads/{member_id}/{file.filename}",
        mime_type=file.content_type,
    )
    
    document = await MemberDocumentCRUD.create(db, member_id, document_data)
    return MemberDocumentResponse.model_validate(document)


@router.delete("/{member_id}/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    member_id: UUID,
    doc_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a document.
    """
    success = await MemberDocumentCRUD.delete(db, doc_id)
    if not success:
        raise NotFoundError(resource="MemberDocument", resource_id=str(doc_id))


# =============================================================================
# Member Tags
# =============================================================================

@router.get("/{member_id}/tags", response_model=List[MemberTagResponse])
async def get_member_tags(
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get member's tags.
    """
    member = await MemberCRUD.get_by_id(db, Member, member_id)
    if not member:
        raise NotFoundError(resource="Member", resource_id=str(member_id))
    
    return [MemberTagResponse.model_validate(t) for t in member.tags]


@router.post("/{member_id}/tags", response_model=MemberResponse)
async def add_member_tags(
    member_id: UUID,
    tag_data: MemberTagAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Add tags to a member.
    """
    member = await MemberTagCRUD.add_tags(db, member_id, tag_data.tag_ids)
    return MemberResponse.model_validate(member)


@router.delete("/{member_id}/tags/{tag_id}", response_model=MemberResponse)
async def remove_member_tag(
    member_id: UUID,
    tag_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Remove a tag from a member.
    """
    success = await MemberTagCRUD.remove_tag(db, member_id, tag_id)
    if not success:
        raise NotFoundError(resource="Tag", resource_id=str(tag_id))
    
    member = await MemberCRUD.get_by_id(db, Member, member_id)
    return MemberResponse.model_validate(member)


# =============================================================================
# Member Notes
# =============================================================================

@router.get("/{member_id}/notes", response_model=List[MemberNoteResponse])
async def get_member_notes(
    member_id: UUID,
    include_private: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get member's notes.
    """
    notes = await MemberNoteCRUD.get_by_member_id(db, member_id, include_private)
    return [MemberNoteResponse.model_validate(n) for n in notes]


@router.post("/{member_id}/notes", response_model=MemberNoteResponse, status_code=status.HTTP_201_CREATED)
async def add_member_note(
    member_id: UUID,
    note_data: MemberNoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a note to a member.
    """
    # Get member ID from current user
    member_user = await MemberCRUD.get_by_id(db, Member, member_id)
    if not member_user:
        raise NotFoundError(resource="Member", resource_id=str(member_id))
    
    note = await MemberNoteCRUD.create(db, member_id, current_user.id, note_data)
    return MemberNoteResponse.model_validate(note)


@router.put("/{member_id}/notes/{note_id}", response_model=MemberNoteResponse)
async def update_member_note(
    member_id: UUID,
    note_id: UUID,
    note_data: MemberNoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a note.
    """
    note = await MemberNoteCRUD.update(db, note_id, note_data)
    if not note:
        raise NotFoundError(resource="MemberNote", resource_id=str(note_id))
    return MemberNoteResponse.model_validate(note)


@router.delete("/{member_id}/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_member_note(
    member_id: UUID,
    note_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a note.
    """
    success = await MemberNoteCRUD.delete(db, note_id)
    if not success:
        raise NotFoundError(resource="MemberNote", resource_id=str(note_id))


# =============================================================================
# Membership History
# =============================================================================

@router.get("/{member_id}/history", response_model=List[MembershipHistoryResponse])
async def get_membership_history(
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get member's membership history.
    """
    member = await MemberCRUD.get_by_id(db, Member, member_id)
    if not member:
        raise NotFoundError(resource="Member", resource_id=str(member_id))
    
    return [MembershipHistoryResponse.model_validate(h) for h in member.history]


# =============================================================================
# Member Status
# =============================================================================

@router.post("/{member_id}/activate", response_model=MemberResponse)
async def activate_member(
    member_id: UUID,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Activate a member (change status to active).
    """
    member = await MemberCRUD.update_status(
        db,
        member_id,
        MembershipStatus.ACTIVE.value,
        reason=reason,
        performed_by=current_user.id,
    )
    if not member:
        raise NotFoundError(resource="Member", resource_id=str(member_id))
    return MemberResponse.model_validate(member)


@router.post("/{member_id}/suspend", response_model=MemberResponse)
async def suspend_member(
    member_id: UUID,
    reason: str = Query(..., description="Reason for suspension"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Suspend a member.
    """
    member = await MemberCRUD.update_status(
        db,
        member_id,
        MembershipStatus.SUSPENDED.value,
        reason=reason,
        performed_by=current_user.id,
    )
    if not member:
        raise NotFoundError(resource="Member", resource_id=str(member_id))
    return MemberResponse.model_validate(member)


# =============================================================================
# Bulk Operations
# =============================================================================

@router.post("/bulk/import", response_model=MemberBulkImportResult)
async def import_members(
    import_data: MemberBulkImport,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Import members in bulk (from list of member data).
    """
    members_dicts = [m.model_dump() for m in import_data.members]
    result = await MemberBulkCRUD.import_members(
        db,
        members_dicts,
        notify=import_data.notify_new_members,
    )
    return MemberBulkImportResult(**result)


@router.get("/export")
async def export_members(
    format: str = "csv",
    status_filter: Optional[List[str]] = Query(None),
    district: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export members to CSV/Excel/JSON format.
    """
    filters = MemberSearchFilters(
        status=status_filter,
        district=district,
    )
    
    csv_data = await MemberStatsCRUD.export_members(db, filters)
    
    return {
        "content": csv_data,
        "filename": f"members_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv",
        "content_type": "text/csv",
    }


# =============================================================================
# Member Statistics
# =============================================================================

@router.get("/stats", response_model=MemberStatsResponse)
async def get_member_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get member statistics.
    """
    stats_data = await MemberStatsCRUD.get_stats(db)
    return MemberStatsResponse(
        stats=MemberStats(**stats_data),
        generated_at=datetime.now(timezone.utc),
    )


@router.get("/stats/by-status")
async def get_stats_by_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get member count by status.
    """
    stats = await MemberStatsCRUD.get_stats(db)
    return {
        "by_status": stats["by_status"],
        "total": stats["total_members"],
        "active": stats["active_members"],
    }


@router.get("/stats/by-district")
async def get_stats_by_district(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get member count by district.
    """
    stats = await MemberStatsCRUD.get_stats(db)
    return {
        "by_district": stats["by_district"],
        "total": stats["total_members"],
    }


# =============================================================================
# Tag Definitions
# =============================================================================

@router.get("/tags/definitions", response_model=List[MemberTagResponse])
async def get_tag_definitions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all tag definitions.
    """
    tags = await MemberTagCRUD.get_all_definitions(db)
    return [MemberTagResponse.model_validate(t) for t in tags]


# =============================================================================
# Search
# =============================================================================

@router.get("/search")
async def search_members(
    q: str = Query(..., min_length=2),
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Quick search for members by name, phone, or email.
    """
    filters = MemberSearchFilters(search=q)
    members, total = await MemberCRUD.search(db, filters, page=1, limit=limit)
    
    return {
        "query": q,
        "results": [MemberResponse.model_validate(m) for m in members],
        "total": total,
    }


@router.get("/by-phone/{phone}", response_model=MemberResponse)
async def get_member_by_phone(
    phone: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get member by phone number.
    """
    member = await MemberCRUD.get_by_phone(db, phone)
    if not member:
        raise NotFoundError(resource="Member", resource_id=f"phone:{phone}")
    return MemberResponse.model_validate(member)


@router.get("/by-membership-number/{membership_number}", response_model=MemberResponse)
async def get_member_by_membership_number(
    membership_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get member by membership number.
    """
    member = await MemberCRUD.get_by_membership_number(db, membership_number)
    if not member:
        raise NotFoundError(resource="Member", resource_id=f"membership_number:{membership_number}")
    return MemberResponse.model_validate(member)
