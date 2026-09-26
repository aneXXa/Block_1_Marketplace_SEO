from pydantic import BaseModel, Field, field_validator


class SeoPackage(BaseModel):
    """Готовый текстовый пакет для карточки маркетплейса."""

    title: str
    description: str
    tags: list[str] = Field(default_factory=list)
    attributes: list[str] = Field(default_factory=list)

    @field_validator("title", "description", mode="before")
    @classmethod
    def _strip_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("tags", "attributes", mode="before")
    @classmethod
    def _clean_list(cls, value: object) -> object:
        if value is None:
            return []
        if isinstance(value, str):
            value = [part.strip() for part in value.split(",")]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return value


class ProductBrief(BaseModel):
    """Вводные селлера: факты + опциональное фото из Telegram."""

    facts: str = ""
    photo_file_id: str | None = None

    def has_signal(self) -> bool:
        return bool(self.facts.strip()) or bool(self.photo_file_id)
