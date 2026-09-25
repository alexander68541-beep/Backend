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
