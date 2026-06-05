from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi import Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.deps import get_current_user
from app.modules.library.constants import ResourceType
from app.modules.library.schemas import (
    LibraryResourceListResponse,
    LibraryResourcePatch,
    LibraryResourceResponse,
)
from app.modules.library.service import LibraryService
from app.modules.users.models import User

router = APIRouter(prefix="/library", tags=["library"])

library_service = LibraryService()


@router.get("/resources", response_model=LibraryResourceListResponse)
async def list_resources(
    type: ResourceType | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LibraryResourceListResponse:
    return await library_service.list_resources(
        db,
        user=current_user,
        type=type,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/resources",
    response_model=LibraryResourceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_resource(
    type: ResourceType = Form(...),
    name: str = Form(..., min_length=1, max_length=255),
    image: UploadFile | None = File(default=None),
    audio: UploadFile | None = File(default=None),
    tags: list[str] = Form(default=[]),
    comment: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LibraryResourceResponse:
    resource = await library_service.create_resource(
        db,
        user=current_user,
        type=type,
        name=name,
        image=image,
        audio=audio,
        tags=tags if tags else None,
        comment=comment if comment else None,
    )
    return LibraryResourceResponse.model_validate(resource)


@router.get("/resources/{resource_id}", response_model=LibraryResourceResponse)
async def get_resource(
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LibraryResourceResponse:
    resource = await library_service.get_resource(db, resource_id=resource_id, user=current_user)
    return LibraryResourceResponse.model_validate(resource)


@router.patch("/resources/{resource_id}", response_model=LibraryResourceResponse)
async def update_resource(
    resource_id: int,
    payload: LibraryResourcePatch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LibraryResourceResponse:
    resource = await library_service.update_resource(
        db,
        resource_id=resource_id,
        user=current_user,
        name=payload.name,
        tags=payload.tags,
        comment=payload.comment,
    )
    return LibraryResourceResponse.model_validate(resource)


@router.delete("/resources/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    await library_service.delete_resource(db, resource_id=resource_id, user=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
