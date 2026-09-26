from typing import Any

import pytest

from marketplace_poster.llm.parse import SeoParseError
from marketplace_poster.models.seo_package import ProductBrief
from marketplace_poster.platforms import WILDBERRIES
from marketplace_poster.services.generation import GenerationError, GenerationService


class FakeLlm:
    def __init__(self, answers: list[str]) -> None:
        self.answers = answers
        self.calls: list[list[dict[str, Any]]] = []

    async def complete(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.6,
    ) -> str:
        del temperature
        self.calls.append(messages)
        if len(self.answers) == 1:
            return self.answers[0]
        return self.answers.pop(0)


_LONG_DESC = (
    "Мужское худи оверсайз из хлопка для повседневной носки, дороги и офиса в casual. "
    "Свободный крой, капюшон, карман-кенгуру. Ткань мягкая, после стирки держит форму. "
    "Чёрный цвет не маркий, сочетается с джинсами и чиносами. "
    "Подойдёт как подарок коллеге: нейтральный фасон без принта на груди. "
    "Слой весной и осенью, дома и в машине. Капюшон без декора, карман глубокий. "
    "Состав и размеры не выдумываю — только то, что есть во вводе селлера. "
    "Уход: стирка 30 градусов наизнанку, без отбеливателя, сушка на горизонтали. "
    "Не тереть капюшон и не сушить на батарее, чтобы крой не сел по длине рукава. "
    "Носить с джинсами, спортивными брюками и чиносами. В прохладный день — один слой, "
    "в помещении — поверх футболки. Рост модели и таблицу размеров не указываю, "
    "если селлер их не прислал. Плотность ткани тоже только из фактов."
)


def _ok_json(title: str = "Худи мужское оверсайз хлопок") -> str:
    return (
        '{"title": "'
        + title
        + '", "description": "'
        + _LONG_DESC
        + '", '
        + '"tags": ["худи", "оверсайз", "хлопок", "капюшон", '
        + '"повседневное", "подарок коллеге", "чёрный", "капюшон мужской"], '
        + '"attributes": ["мужской"]}'
    )


@pytest.mark.asyncio
async def test_generate_parses_and_validates() -> None:
    llm = FakeLlm([_ok_json()])
    service = GenerationService(llm)
    package, result = await service.generate(
        WILDBERRIES,
        ProductBrief(facts="Худи мужское хлопок"),
    )
    assert "Худи" in package.title
    assert len(package.title) <= WILDBERRIES.max_title
    assert result.needs_llm_repair is False
    assert len(llm.calls) == 1
    system = llm.calls[0][0]["content"]
    assert "Wildberries" in system


@pytest.mark.asyncio
async def test_generate_repairs_when_title_overshoots() -> None:
    long_title = "Худи " * 30
    llm = FakeLlm([_ok_json(long_title), _ok_json("Худи мужское оверсайз хлопок")])
    service = GenerationService(llm)
    package, _result = await service.generate(
        WILDBERRIES,
        ProductBrief(facts="Худи"),
    )
    assert len(llm.calls) == 2
    assert len(package.title) <= 60


@pytest.mark.asyncio
async def test_generate_raises_on_garbage() -> None:
    llm = FakeLlm(["¯\\_(ツ)_/¯"])
    service = GenerationService(llm)
    with pytest.raises(GenerationError):
        await service.generate(WILDBERRIES, ProductBrief(facts="Худи"))


@pytest.mark.asyncio
async def test_photo_is_attached_as_data_url() -> None:
    llm = FakeLlm([_ok_json()])
    service = GenerationService(llm)
    await service.generate(
        WILDBERRIES,
        ProductBrief(facts="Худи", photo_file_id="file-1"),
        photo_bytes=b"jpeg-bytes",
    )
    user_content = llm.calls[0][1]["content"]
    assert isinstance(user_content, list)
    assert user_content[1]["type"] == "image_url"
    assert user_content[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")


def test_parse_error_message_is_human() -> None:
    with pytest.raises(SeoParseError, match="не JSON"):
        raise SeoParseError("ответ не JSON: boom")


def test_humanize_location_is_generic() -> None:
    from marketplace_poster.services.generation import humanize_llm_error

    text = humanize_llm_error(
        RuntimeError("Error code: 400 User location is not supported for the API use.")
    )
    assert "VPN" not in text
    assert "TUN" not in text
    assert "Не удалось обратиться к модели" in text
