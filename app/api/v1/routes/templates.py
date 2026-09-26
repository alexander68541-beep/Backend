from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models import CustomTemplate
from app.schemas.extras import CustomTemplateOut

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=list[CustomTemplateOut])
async def list_templates(_=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(CustomTemplate)
            .where(CustomTemplate.is_published == True)  # noqa: E712
            .order_by(CustomTemplate.position.asc(), CustomTemplate.created_at.asc())
        )
    ).scalars().all()
    return [CustomTemplateOut.model_validate(r) for r in rows]
