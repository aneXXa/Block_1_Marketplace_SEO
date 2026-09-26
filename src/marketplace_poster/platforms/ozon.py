from marketplace_poster.platforms.base import PlatformId, PlatformRulePack

OZON = PlatformRulePack(
    id=PlatformId.OZON,
    display_name="Ozon",
    max_title=200,
    target_title_min=40,
    target_title_max=80,
    max_description=6000,
    target_description_min=1200,
    target_description_max=2500,
    min_tags=10,
    max_tags=25,
    title_formula="тип + бренд + модель + важные характеристики",
    extra_instructions=(
        "Поиск Ozon индексирует название и характеристики, НЕ описание. "
        "Поэтому теги и attributes — точные фильтруемые факты, не «вода». "
        "В названии одно слово не больше двух раз, длина слова не больше 27 символов. "
        "Описание (аннотация) работает на конверсию: факты, сценарии, уход. "
        "Без HTML, без цены, доставки, контактов и формулировок «аналог/копия/реплика»."
    ),
    max_word_length=27,
    max_word_repeats=2,
    banned_substrings=("аналог", "копия", "реплика", "подделка"),
    search_indexes_description=False,
)
