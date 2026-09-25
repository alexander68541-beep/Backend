import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user
from app.db.session import get_db
from app.models import (
    Achievement,
    GalleryItem,
    Video,
    Certification,
    Education,
    Experience,
    Project,
    Publication,
    Service,
    Skill,
    SocialLink,
    Testimonial,
)
from app.schemas.portfolio_data import (
    AchievementIn, AchievementOut, AchievementUpdate,
    GalleryIn, GalleryOut, GalleryUpdate,
    VideoIn, VideoOut, VideoUpdate,
    CertificationIn, CertificationOut, CertificationUpdate,
    PublicationIn, PublicationOut, PublicationUpdate,
    ServiceIn, ServiceOut, ServiceUpdate,
    TestimonialIn, TestimonialOut, TestimonialUpdate,
    EducationIn,
    EducationOut,
    EducationUpdate,
    ExperienceIn,
    ExperienceOut,
    ExperienceUpdate,
    ProjectIn,
    ProjectOut,
    ProjectUpdate,
    ReorderIn,
    SkillIn,
    SkillOut,
    SkillUpdate,
    SocialLinkIn,
    SocialLinkOut,
    SocialLinkUpdate,
)
from app.services import crud, portfolio_service


def make_crud_router(*, prefix, tag, model, create_schema, update_schema, out_schema):
    router = APIRouter(prefix=prefix, tags=[tag])

    async def _pid(user: CurrentUser, db: AsyncSession) -> uuid.UUID:
        pf = await portfolio_service.ensure_primary_portfolio(db, user.id)
        return pf.id

    @router.get("", response_model=list[out_schema])
    async def list_items(
        user: CurrentUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        return await crud.list_items(db, model, await _pid(user, db))

    @router.post("", response_model=out_schema, status_code=201)
    async def create_item(
        payload: create_schema,
        user: CurrentUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        pid = await _pid(user, db)
        return await crud.create_item(db, model, pid, payload.model_dump())

    @router.post("/reorder", response_model=list[out_schema])
    async def reorder_items(
        payload: ReorderIn,
        user: CurrentUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        pid = await _pid(user, db)
        return await crud.reorder(db, model, pid, payload.ids)

    @router.patch("/{item_id}", response_model=out_schema)
    async def update_item(
        item_id: uuid.UUID,
        payload: update_schema,
        user: CurrentUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        pid = await _pid(user, db)
        item = await crud.get_owned_item(db, model, pid, item_id)
        return await crud.update_item(db, item, payload.model_dump(exclude_unset=True))

    @router.delete("/{item_id}", status_code=204)
    async def delete_item(
        item_id: uuid.UUID,
        user: CurrentUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        pid = await _pid(user, db)
        item = await crud.get_owned_item(db, model, pid, item_id)
        await crud.delete_item(db, item)

    return router


projects_router = make_crud_router(
    prefix="/portfolio/projects", tag="projects", model=Project,
    create_schema=ProjectIn, update_schema=ProjectUpdate, out_schema=ProjectOut,
)
skills_router = make_crud_router(
    prefix="/portfolio/skills", tag="skills", model=Skill,
    create_schema=SkillIn, update_schema=SkillUpdate, out_schema=SkillOut,
)
experience_router = make_crud_router(
    prefix="/portfolio/experience", tag="experience", model=Experience,
    create_schema=ExperienceIn, update_schema=ExperienceUpdate, out_schema=ExperienceOut,
)
education_router = make_crud_router(
    prefix="/portfolio/education", tag="education", model=Education,
    create_schema=EducationIn, update_schema=EducationUpdate, out_schema=EducationOut,
)
links_router = make_crud_router(
    prefix="/portfolio/links", tag="links", model=SocialLink,
    create_schema=SocialLinkIn, update_schema=SocialLinkUpdate, out_schema=SocialLinkOut,
)

services_router = make_crud_router(
    prefix="/portfolio/services", tag="services", model=Service,
    create_schema=ServiceIn, update_schema=ServiceUpdate, out_schema=ServiceOut,
)
certifications_router = make_crud_router(
    prefix="/portfolio/certifications", tag="certifications", model=Certification,
    create_schema=CertificationIn, update_schema=CertificationUpdate, out_schema=CertificationOut,
)
achievements_router = make_crud_router(
    prefix="/portfolio/achievements", tag="achievements", model=Achievement,
    create_schema=AchievementIn, update_schema=AchievementUpdate, out_schema=AchievementOut,
)
testimonials_router = make_crud_router(
    prefix="/portfolio/testimonials", tag="testimonials", model=Testimonial,
    create_schema=TestimonialIn, update_schema=TestimonialUpdate, out_schema=TestimonialOut,
)
publications_router = make_crud_router(
    prefix="/portfolio/publications", tag="publications", model=Publication,
    create_schema=PublicationIn, update_schema=PublicationUpdate, out_schema=PublicationOut,
)

gallery_router = make_crud_router(
    prefix="/portfolio/gallery", tag="gallery", model=GalleryItem,
    create_schema=GalleryIn, update_schema=GalleryUpdate, out_schema=GalleryOut,
)
videos_router = make_crud_router(
    prefix="/portfolio/videos", tag="videos", model=Video,
    create_schema=VideoIn, update_schema=VideoUpdate, out_schema=VideoOut,
)

all_routers = [
    projects_router,
    skills_router,
    experience_router,
    education_router,
    links_router,
    services_router,
    certifications_router,
    achievements_router,
    testimonials_router,
    publications_router,
    gallery_router,
    videos_router,
]
