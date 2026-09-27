"""Generic ownership-scoped CRUD for a portfolio's child entities.

All items belong to the user's primary portfolio. Every mutation is scoped to that
portfolio_id, so a user can never read or change another user's rows.
"""
from __future__ import annotations

import uuid
from typing import TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.base import Base

T = TypeVar("T", bound=Base)


async def list_items(db: AsyncSession, model: type[T], portfolio_id: uuid.UUID) -> list[T]:
    stmt = (
        select(model)
        .where(model.portfolio_id == portfolio_id)  # type: ignore[attr-defined]
        .order_by(model.position.asc(), model.created_at.asc())  # type: ignore[attr-defined]
    )
    return list((await db.execute(stmt)).scalars().all())


async def create_item(
    db: AsyncSession, model: type[T], portfolio_id: uuid.UUID, data: dict
) -> T:
    next_pos = (
        await db.execute(
            select(func.coalesce(func.max(model.position), -1) + 1).where(  # type: ignore[attr-defined]
                model.portfolio_id == portfolio_id  # type: ignore[attr-defined]
            )
        )
    ).scalar_one()
    item = model(portfolio_id=portfolio_id, position=next_pos, **data)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def get_owned_item(
    db: AsyncSession, model: type[T], portfolio_id: uuid.UUID, item_id: uuid.UUID
) -> T:
    item = await db.get(model, item_id)
    if item is None or item.portfolio_id != portfolio_id:  # type: ignore[attr-defined]
        raise AppError("Item not found", code="not_found", status_code=404)
    return item


async def update_item(db: AsyncSession, item: T, data: dict) -> T:
    for key, value in data.items():
        setattr(item, key, value)
    await db.commit()
    await db.refresh(item)
    return item


async def delete_item(db: AsyncSession, item: T) -> None:
    await db.delete(item)
    await db.commit()


async def reorder(
    db: AsyncSession, model: type[T], portfolio_id: uuid.UUID, ids: list[uuid.UUID]
) -> list[T]:
    items = await list_items(db, model, portfolio_id)
    order = {id_: i for i, id_ in enumerate(ids)}
    for it in items:
        if it.id in order:  # type: ignore[attr-defined]
            it.position = order[it.id]  # type: ignore[attr-defined]
    await db.commit()
    return await list_items(db, model, portfolio_id)
