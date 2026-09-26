from marketplace_poster.platforms.base import PlatformId, PlatformRulePack

WILDBERRIES = PlatformRulePack(
    id=PlatformId.WILDBERRIES,
    display_name="Wildberries",
    max_title=60,
    target_title_min=40,
    target_title_max=55,
    max_description=2000,
    target_description_min=800,
    target_description_max=1500,
    min_tags=8,
    max_tags=20,
    title_formula="тип товара + ключевое свойство + назначение или модель",
    extra_instructions=(
        "Главный ключ — в первых 40 символах названия. Бренд в название не дублируй. "
        "Без синонимов подряд («кроссовки кеды»), без капслока, эмодзи, ссылок и восклицаний. "
        "Описание — живой текст консультанта: первый абзац что это и для кого, "
        "затем факты, сценарии, уход. Не перечисляй ключи списком. "
        "Теги — характеристики и поводы для фильтров (крой, материал, цвет, подарок маме)."
    ),
    banned_substrings=("лучший", "уникальный", "единственный"),
    search_indexes_description=True,
)
