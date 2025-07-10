# app/api/v1/contact.py

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID as PyUUID

from app.dependencies import get_current_active_admin, get_current_user
from app.database import get_async_db
from app.dependencies import get_current_active_moderator_or_admin
from app.models.user import User
from app.models.contact_submission import ContactStatus
from app.schemas.contact_submission import (
    ContactSubmissionCreate, 
    ContactSubmissionResponse, 
    ContactSubmissionUpdateAdmin
)
from app.schemas.pagination import PaginatedResponse
from app.crud.contact_submission import contact_submission_crud

router = APIRouter()


# --- Public Endpoint ---

@router.post(
    "", 
    response_model=ContactSubmissionResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new contact form inquiry"
)
async def submit_contact_form(
    submission_in: ContactSubmissionCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Public endpoint for any user to submit a contact form.
    No authentication is required.
    """
    # Optional: Add rate limiting here if needed
    new_submission = await contact_submission_crud.create_submission(db=db, obj_in=submission_in)
    return new_submission


# --- Admin Endpoints ---

@router.get(
    "",
    response_model=PaginatedResponse[ContactSubmissionResponse],
    summary="List all contact submissions (Admin/Moderator)"
)
async def list_all_contact_submissions(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status_filter: Optional[ContactStatus] = Query(None, description="Filter by submission status"),
    search: Optional[str] = Query(None, description="Search by name, email, or subject")
):
    """
    Retrieve all contact form submissions.
    Requires Moderator or Admin role.
    """
    submissions, total_count = await contact_submission_crud.get_submissions_paginated(
        db=db, skip=skip, limit=limit, status_filter=status_filter, search_query=search
    )
    
    # ... (pagination next/prev page logic from your other endpoints) ...
    next_page, prev_page = None, None
    if (skip + limit) < total_count:
        # Build URL for next page
        pass
    if skip > 0:
        # Build URL for prev page
        pass
        
    return PaginatedResponse[ContactSubmissionResponse](
        total_count=total_count,
        limit=limit,
        skip=skip,
        next_page=next_page,
        prev_page=prev_page,
        items=submissions
    )


@router.get(
    "/{submission_id}",
    response_model=ContactSubmissionResponse,
    summary="Get a single submission by ID (Admin/Moderator)"
)
async def get_single_submission(
    submission_id: PyUUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_admin)
):
    submission = await contact_submission_crud.get(db=db, id=submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    return submission


@router.put(
    "/{submission_id}",
    response_model=ContactSubmissionResponse,
    summary="Update a submission's status or notes (Admin/Moderator)"
)
async def update_submission(
    submission_id: PyUUID,
    submission_in: ContactSubmissionUpdateAdmin,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_admin)
):
    db_submission = await contact_submission_crud.get(db=db, id=submission_id)
    if not db_submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    
    updated_submission = await contact_submission_crud.update_submission_status(
        db=db,
        db_obj=db_submission,
        obj_in=submission_in,
        #resolver_id=current_user.id
    )
    return updated_submission

@router.delete(
    "/{submission_id}",
    response_model=ContactSubmissionResponse,
    summary="Delete a submission (Admin/Moderator)"
)
async def delete_submission(
    submission_id: PyUUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_admin)
):
    deleted_submission = await contact_submission_crud.delete_submission(db=db, submission_id=submission_id)
    if not deleted_submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    return deleted_submission