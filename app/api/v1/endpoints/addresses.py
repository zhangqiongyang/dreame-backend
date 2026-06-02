from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.core.response import ApiResponse, success
from app.schemas.address import AddressCreateIn, AddressOut, AddressUpdateIn
from app.services import address_service

router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.get("", response_model=ApiResponse[list[AddressOut]])
async def list_addresses(db: DbSession, user: CurrentUser) -> ApiResponse[list[AddressOut]]:
    return success(await address_service.list_addresses(db, user))


@router.get("/{address_id}", response_model=ApiResponse[AddressOut])
async def get_address(
    address_id: str, db: DbSession, user: CurrentUser
) -> ApiResponse[AddressOut]:
    return success(await address_service.get_address(db, user, address_id))


@router.post("", response_model=ApiResponse[AddressOut])
async def create_address(
    body: AddressCreateIn, db: DbSession, user: CurrentUser
) -> ApiResponse[AddressOut]:
    return success(await address_service.create_address(db, user, body))


@router.put("/{address_id}", response_model=ApiResponse[AddressOut])
async def update_address(
    address_id: str, body: AddressUpdateIn, db: DbSession, user: CurrentUser
) -> ApiResponse[AddressOut]:
    return success(await address_service.update_address(db, user, address_id, body))


@router.delete("/{address_id}", response_model=ApiResponse)
async def delete_address(
    address_id: str, db: DbSession, user: CurrentUser
) -> ApiResponse:
    await address_service.delete_address(db, user, address_id)
    return success()


@router.post("/{address_id}/default", response_model=ApiResponse[AddressOut])
async def set_default_address(
    address_id: str, db: DbSession, user: CurrentUser
) -> ApiResponse[AddressOut]:
    return success(await address_service.set_default_address(db, user, address_id))
