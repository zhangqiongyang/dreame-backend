from __future__ import annotations

from fastapi import APIRouter, Depends, File, Request, UploadFile

from app.api.deps import verify_admin
from app.core.response import ApiResponse, success
from app.schemas.upload import UploadImageOut
from app.services import upload_service

router = APIRouter(prefix="/admin", tags=["admin-upload"], dependencies=[Depends(verify_admin)])


@router.post("/upload/image", response_model=ApiResponse[UploadImageOut])
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
) -> ApiResponse[UploadImageOut]:
    url = await upload_service.save_product_image(file, request)
    return success(UploadImageOut(url=url))
