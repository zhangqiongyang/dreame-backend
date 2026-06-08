from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessError
from app.models.user import User
from app.models.user_address import UserAddress
from app.schemas.address import AddressCreateIn, AddressOut, AddressUpdateIn
from app.schemas.common import ReceiverIn
from app.utils.phone import validate_cn_mobile
from app.utils.ids import IdPrefix, generate_unique_id

MAX_ADDRESSES_PER_USER = 20


def _full_address(addr: UserAddress) -> str:
    parts = [addr.province, addr.city, addr.district, addr.detail]
    return "".join(p for p in parts if p)


def address_to_out(addr: UserAddress) -> AddressOut:
    return AddressOut(
        id=addr.address_no,
        name=addr.name,
        phone=addr.phone,
        province=addr.province,
        city=addr.city,
        district=addr.district,
        detail=addr.detail,
        isDefault=addr.is_default,
        fullAddress=_full_address(addr),
    )


async def generate_address_no(session: AsyncSession) -> str:
    async def exists(no: str) -> bool:
        r = await session.execute(
            select(UserAddress.id).where(UserAddress.address_no == no).limit(1)
        )
        return r.scalar_one_or_none() is not None

    return await generate_unique_id(session, IdPrefix.ADDRESS, exists_query=exists)


async def _get_address_owned(
    session: AsyncSession, user: User, address_no: str
) -> UserAddress:
    result = await session.execute(
        select(UserAddress).where(
            UserAddress.address_no == address_no, UserAddress.user_id == user.user_no
        )
    )
    addr = result.scalar_one_or_none()
    if addr is None:
        raise BusinessError("收货地址不存在")
    return addr


async def _count_addresses(session: AsyncSession, user_no: str) -> int:
    result = await session.execute(
        select(UserAddress.id).where(UserAddress.user_id == user_no)
    )
    return len(result.all())


async def _clear_default(session: AsyncSession, user_no: str) -> None:
    await session.execute(
        update(UserAddress)
        .where(UserAddress.user_id == user_no, UserAddress.is_default.is_(True))
        .values(is_default=False)
    )


async def list_addresses(session: AsyncSession, user: User) -> List[AddressOut]:
    result = await session.execute(
        select(UserAddress)
        .where(UserAddress.user_id == user.user_no)
        .order_by(UserAddress.is_default.desc(), UserAddress.updated_at.desc())
    )
    return [address_to_out(a) for a in result.scalars().all()]


async def get_address(session: AsyncSession, user: User, address_no: str) -> AddressOut:
    addr = await _get_address_owned(session, user, address_no)
    return address_to_out(addr)


async def create_address(
    session: AsyncSession, user: User, body: AddressCreateIn
) -> AddressOut:
    count = await _count_addresses(session, user.user_no)
    if count >= MAX_ADDRESSES_PER_USER:
        raise BusinessError(f"最多保存 {MAX_ADDRESSES_PER_USER} 条收货地址")

    is_default = body.isDefault or count == 0
    if is_default:
        await _clear_default(session, user.user_no)

    addr = UserAddress(
        address_no=await generate_address_no(session),
        user_id=user.user_no,
        name=body.name.strip(),
        phone=body.phone.strip(),
        province=body.province.strip(),
        city=body.city.strip(),
        district=body.district.strip(),
        detail=body.detail.strip(),
        is_default=is_default,
    )
    session.add(addr)
    await session.commit()
    await session.refresh(addr)
    return address_to_out(addr)


async def update_address(
    session: AsyncSession, user: User, address_no: str, body: AddressUpdateIn
) -> AddressOut:
    addr = await _get_address_owned(session, user, address_no)

    if body.name is not None:
        addr.name = body.name.strip()
    if body.phone is not None:
        addr.phone = body.phone.strip()
    if body.province is not None:
        addr.province = body.province.strip()
    if body.city is not None:
        addr.city = body.city.strip()
    if body.district is not None:
        addr.district = body.district.strip()
    if body.detail is not None:
        addr.detail = body.detail.strip()

    if body.isDefault is True:
        await _clear_default(session, user.user_no)
        addr.is_default = True
    elif body.isDefault is False and addr.is_default:
        addr.is_default = False

    await session.commit()
    await session.refresh(addr)

    if not addr.is_default:
        result = await session.execute(
            select(UserAddress).where(UserAddress.user_id == user.user_no)
        )
        rows = list(result.scalars().all())
        if rows and not any(a.is_default for a in rows):
            rows[0].is_default = True
            await session.commit()
            await session.refresh(addr)

    return address_to_out(addr)


async def delete_address(session: AsyncSession, user: User, address_no: str) -> None:
    addr = await _get_address_owned(session, user, address_no)
    was_default = addr.is_default
    await session.delete(addr)
    await session.flush()

    if was_default:
        result = await session.execute(
            select(UserAddress)
            .where(UserAddress.user_id == user.user_no)
            .order_by(UserAddress.updated_at.desc())
            .limit(1)
        )
        next_addr = result.scalar_one_or_none()
        if next_addr is not None:
            next_addr.is_default = True

    await session.commit()


async def set_default_address(
    session: AsyncSession, user: User, address_no: str
) -> AddressOut:
    addr = await _get_address_owned(session, user, address_no)
    await _clear_default(session, user.user_no)
    addr.is_default = True
    await session.commit()
    await session.refresh(addr)
    return address_to_out(addr)


async def resolve_receiver(
    session: AsyncSession, user: User, *, address_id: Optional[str], receiver: Optional[ReceiverIn]
) -> ReceiverIn:
    if address_id:
        addr = await _get_address_owned(session, user, address_id)
        return ReceiverIn(
            name=addr.name,
            phone=validate_cn_mobile(addr.phone),
            province=addr.province,
            city=addr.city,
            district=addr.district,
            detail=addr.detail,
        )
    if receiver is not None:
        return receiver
    raise BusinessError("请选择或填写收货地址")
