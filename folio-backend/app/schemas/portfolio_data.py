import uuid

from pydantic import BaseModel, ConfigDict, Field


class _Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    position: int


# ---------- Projects ----------
class ProjectIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    role: str | None = Field(default=None, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    url: str | None = Field(default=None, max_length=2048)
    image_url: str | None = Field(default=None, max_length=2048)
    tags: list[str] = Field(default_factory=list, max_length=20)
    start_date: str | None = Field(default=None, max_length=40)
    end_date: str | None = Field(default=None, max_length=40)
    is_featured: bool = False


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    role: str | None = Field(default=None, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    url: str | None = Field(default=None, max_length=2048)
    image_url: str | None = Field(default=None, max_length=2048)
    tags: list[str] | None = Field(default=None, max_length=20)
    start_date: str | None = Field(default=None, max_length=40)
    end_date: str | None = Field(default=None, max_length=40)
    is_featured: bool | None = None


class ProjectOut(_Out):
    title: str
    role: str | None = None
    description: str | None = None
    url: str | None = None
    image_url: str | None = None
    tags: list[str] = []
    start_date: str | None = None
    end_date: str | None = None
    is_featured: bool = False


# ---------- Skills ----------
class SkillIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: str | None = Field(default=None, max_length=80)
    level: int | None = Field(default=None, ge=1, le=5)


class SkillUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    category: str | None = Field(default=None, max_length=80)
    level: int | None = Field(default=None, ge=1, le=5)


class SkillOut(_Out):
    name: str
    category: str | None = None
    level: int | None = None


# ---------- Experience ----------
class ExperienceIn(BaseModel):
    company: str = Field(min_length=1, max_length=200)
    title: str | None = Field(default=None, max_length=160)
    location: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=4000)
    start_date: str | None = Field(default=None, max_length=40)
    end_date: str | None = Field(default=None, max_length=40)
    is_current: bool = False


class ExperienceUpdate(BaseModel):
    company: str | None = Field(default=None, min_length=1, max_length=200)
    title: str | None = Field(default=None, max_length=160)
    location: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=4000)
    start_date: str | None = Field(default=None, max_length=40)
    end_date: str | None = Field(default=None, max_length=40)
    is_current: bool | None = None


class ExperienceOut(_Out):
    company: str
    title: str | None = None
    location: str | None = None
    description: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool = False


# ---------- Education ----------
class EducationIn(BaseModel):
    school: str = Field(min_length=1, max_length=200)
    degree: str | None = Field(default=None, max_length=160)
    field: str | None = Field(default=None, max_length=160)
    start_date: str | None = Field(default=None, max_length=40)
    end_date: str | None = Field(default=None, max_length=40)
    description: str | None = Field(default=None, max_length=4000)


class EducationUpdate(BaseModel):
    school: str | None = Field(default=None, min_length=1, max_length=200)
    degree: str | None = Field(default=None, max_length=160)
    field: str | None = Field(default=None, max_length=160)
    start_date: str | None = Field(default=None, max_length=40)
    end_date: str | None = Field(default=None, max_length=40)
    description: str | None = Field(default=None, max_length=4000)


class EducationOut(_Out):
    school: str
    degree: str | None = None
    field: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None


# ---------- Social links ----------
class SocialLinkIn(BaseModel):
    platform: str = Field(min_length=1, max_length=60)
    url: str = Field(min_length=1, max_length=2048)
    label: str | None = Field(default=None, max_length=80)


class SocialLinkUpdate(BaseModel):
    platform: str | None = Field(default=None, min_length=1, max_length=60)
    url: str | None = Field(default=None, min_length=1, max_length=2048)
    label: str | None = Field(default=None, max_length=80)


class SocialLinkOut(_Out):
    platform: str
    url: str
    label: str | None = None


class ReorderIn(BaseModel):
    ids: list[uuid.UUID]


# ---------- Services ----------
class ServiceIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    price: str | None = Field(default=None, max_length=80)


class ServiceUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    price: str | None = Field(default=None, max_length=80)


class ServiceOut(_Out):
    title: str
    description: str | None = None
    price: str | None = None


# ---------- Certifications ----------
class CertificationIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    issuer: str | None = Field(default=None, max_length=200)
    issue_date: str | None = Field(default=None, max_length=40)
    credential_id: str | None = Field(default=None, max_length=200)
    url: str | None = Field(default=None, max_length=2048)


class CertificationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    issuer: str | None = Field(default=None, max_length=200)
    issue_date: str | None = Field(default=None, max_length=40)
    credential_id: str | None = Field(default=None, max_length=200)
    url: str | None = Field(default=None, max_length=2048)


class CertificationOut(_Out):
    name: str
    issuer: str | None = None
    issue_date: str | None = None
    credential_id: str | None = None
    url: str | None = None


# ---------- Achievements ----------
class AchievementIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    date: str | None = Field(default=None, max_length=40)


class AchievementUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    date: str | None = Field(default=None, max_length=40)


class AchievementOut(_Out):
    title: str
    description: str | None = None
    date: str | None = None


# ---------- Testimonials ----------
class TestimonialIn(BaseModel):
    author: str = Field(min_length=1, max_length=200)
    role: str | None = Field(default=None, max_length=200)
    quote: str = Field(min_length=1, max_length=4000)
    avatar_url: str | None = Field(default=None, max_length=2048)


class TestimonialUpdate(BaseModel):
    author: str | None = Field(default=None, min_length=1, max_length=200)
    role: str | None = Field(default=None, max_length=200)
    quote: str | None = Field(default=None, min_length=1, max_length=4000)
    avatar_url: str | None = Field(default=None, max_length=2048)


class TestimonialOut(_Out):
    author: str
    role: str | None = None
    quote: str
    avatar_url: str | None = None


# ---------- Publications ----------
class PublicationIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    publisher: str | None = Field(default=None, max_length=200)
    date: str | None = Field(default=None, max_length=40)
    url: str | None = Field(default=None, max_length=2048)
    description: str | None = Field(default=None, max_length=4000)


class PublicationUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    publisher: str | None = Field(default=None, max_length=200)
    date: str | None = Field(default=None, max_length=40)
    url: str | None = Field(default=None, max_length=2048)
    description: str | None = Field(default=None, max_length=4000)


class PublicationOut(_Out):
    title: str
    publisher: str | None = None
    date: str | None = None
    url: str | None = None
    description: str | None = None


# ---------- Gallery ----------
class GalleryIn(BaseModel):
    image_url: str = Field(min_length=1, max_length=2048)
    caption: str | None = Field(default=None, max_length=300)


class GalleryUpdate(BaseModel):
    image_url: str | None = Field(default=None, min_length=1, max_length=2048)
    caption: str | None = Field(default=None, max_length=300)


class GalleryOut(_Out):
    image_url: str
    caption: str | None = None


# ---------- Videos ----------
class VideoIn(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    url: str = Field(min_length=1, max_length=2048)


class VideoUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    url: str | None = Field(default=None, min_length=1, max_length=2048)


class VideoOut(_Out):
    title: str | None = None
    url: str
