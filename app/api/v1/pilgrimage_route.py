from fastapi import APIRouter, Depends, Request, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from app.crud import pilgrimage_route_crud, place_crud
from app.dependencies import get_current_active_admin, get_current_user
from app.schemas import (
  PilgrimageRouteCreate, PilgrimageRouteUpdate, PilgrimageRouteResponse, 
  PaginatedResponse, PilgrimageRouteResponseWithStops, PilgrimagePlace
)
from app.database import get_async_db
from app.schemas.pilgrimage_route import DifficultyType, DurationType
from app.models.user import User  # Ensure User model is imported for type hinting


router = APIRouter()


@router.post("", response_model=PilgrimageRouteResponse, status_code=status.HTTP_201_CREATED)
async def create_pilgrimage_route(
    pilgrimage_route_in: PilgrimageRouteCreate,
    current_user: User = Depends(get_current_active_admin), # Example: Only admins can create
    db: AsyncSession = Depends(get_async_db),
):
    """
    Create new content. Requires Moderator or Admin role.
    """
    # created_by will be current_user.id

    # Allowing duplicates as of now
    # existing = await pilgrimage_route_crud.get_by_name(db, name=pilgrimage_route_in.name)
    # if existing:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="A PilgrimageRoute with this name already exists.",
    #     )

    result = await pilgrimage_route_crud.create_pilgrimage_route(
        db=db,
        obj_in=pilgrimage_route_in,
        # created_by = current_user.id,
        created_by = "7e6bacf9-69f5-4807-a8e8-9b961b6c1e51"
    )
    return result


# @router.get("", response_model=List[PilgrimageRouteResponse])
@router.get("", response_model=PaginatedResponse[PilgrimageRouteResponse])
async def list_all_pilgrimage_routes(
    request: Request,  # Add this to build next/prev URLs
    search: Optional[str] = Query(None),            # changed name to search to match UI
    difficulty_level: Optional[DifficultyType] = Query(None),
    estimated_duration: Optional[DurationType] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),  # Use specific dependency
    db: AsyncSession = Depends(get_async_db),
):
    """
    Retrieve all PilgrimageRoutes if no filters are added else returns the filtered ones.
    """
    routes, total_count = await pilgrimage_route_crud.get_filtered_with_count(
        db=db,
        search=search,
        difficulty_level=difficulty_level,
        estimated_duration=estimated_duration,
        skip=skip,
        limit=limit,
    )
    response_items = [PilgrimageRouteResponse.model_validate(p) for p in routes]

    base_url = str(request.url.remove_query_params(keys=["skip", "limit"]))
    next_page = prev_page = None
    if (skip + limit) < total_count:
        next_params = request.query_params._dict.copy()
        next_params["skip"] = str(skip + limit)
        next_page = str(request.url.replace_query_params(**next_params))
    if skip > 0:
        prev_params = request.query_params._dict.copy()
        prev_params["skip"] = str(max(0, skip - limit))
        prev_page = str(request.url.replace_query_params(**prev_params))

    return PaginatedResponse[PilgrimageRouteResponse](
        total_count=total_count,
        limit=limit,
        skip=skip,
        next_page=next_page,
        prev_page=prev_page,
        items=response_items
    )


# APIs to display all durations and difficulties

@router.get("/list_all_difficulty_types", response_model=List[str])
async def list_all_difficulty_types(
    current_user: User = Depends(get_current_user),  # Use specific dependency
):
    return [key.value for key in DifficultyType]


@router.get("/list_all_duration_types", response_model=List[str])
async def list_all_duration_types(
    current_user: User = Depends(get_current_user),  # Use specific dependency
):
    return [key.value for key in DurationType]


@router.get("/{pilgrimage_route_id}", response_model=PilgrimageRouteResponseWithStops)
async def get_pilgrimage_route(
    pilgrimage_route_id: UUID, 
    current_user: User = Depends(get_current_user),  # Use specific dependency
    db: AsyncSession = Depends(get_async_db)
):
    pilgrimage_route = await pilgrimage_route_crud.get(db=db, id=pilgrimage_route_id)
    if not pilgrimage_route:
        raise HTTPException(status_code=404, detail="PilgrimageRoute not found")

    pilgrimage_route.view_count += 1

    await db.commit()       # Commit to make it permanent
    await db.refresh(pilgrimage_route)     # Refresh to re-fetch any auto-updated fields (optional)

    
    places = await place_crud.get_by_ids(db=db, ids=pilgrimage_route.route_path)
    pilgrimage_route_response = PilgrimageRouteResponseWithStops.model_validate(pilgrimage_route)
    pilgrimage_route_response.stops = [
        PilgrimagePlace.model_validate(place) for place in places
    ]
    return pilgrimage_route_response


@router.put("/{pilgrimage_route_id}", response_model=PilgrimageRouteResponse)
async def update_pilgrimage_route(
    pilgrimage_route_id: UUID,
    pilgrimage_route_in: PilgrimageRouteUpdate,
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_async_db),
):
    pilgrimage_route = await pilgrimage_route_crud.get(db=db, id=pilgrimage_route_id)
    if not pilgrimage_route:
        raise HTTPException(status_code=404, detail="PilgrimageRoute not found")

    # ... (Permission check) ...
    # is_admin_or_moderator = current_user.role in [UserRole.ADMIN.value, UserRole.MODERATOR.value]
    # is_author = pilgrimage_route.created_by == current_user.id if pilgrimage_route.created_by else False
    # if not (is_admin_or_moderator or is_author):
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    return await pilgrimage_route_crud.update(db=db, db_obj=pilgrimage_route, obj_in=pilgrimage_route_in)


@router.delete("/{pilgrimage_route_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pilgrimage_route(
    pilgrimage_route_id: UUID, 
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_async_db)
):
    pilgrimage_route = await pilgrimage_route_crud.get(db=db, id=pilgrimage_route_id)
    if not pilgrimage_route:
        raise HTTPException(status_code=404, detail="PilgrimageRoute not found")
    await pilgrimage_route_crud.remove(db=db, id=pilgrimage_route_id)
    return
