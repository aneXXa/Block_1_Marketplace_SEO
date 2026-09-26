from marketplace_poster.platforms.base import PlatformId, PlatformRulePack

AVITO = PlatformRulePack(
    id=PlatformId.AVITO,
    display_name="Авито",
    max_title=50,
    target_title_min=28,
    target_title_max=50,
    max_description=7500,
    target_description_min=800,
    target_description_max=1500,
    min_tags=5,
    max_tags=10,
    title_formula="главный запрос + одно уточнение (тип + свойство)",
    extra_instructions=(
        "Первые 200 символов описания видны в выдаче — туда УТП и выгоду, без приветствий. "
        "Объём 800–1500 символов, короткие абзацы и буллеты. "
        "Теги — 5–10 точных фраз, без решёток и облака ключей внизу текста. "
        "Без кликбейта («акция», «шок-цена», «дёшево») и без контактов."
    ),
    banned_substrings=("акция", "шок", "шок-цена", "дёшево", "дешево"),
    strip_hashtags=True,
    search_indexes_description=True,
)
