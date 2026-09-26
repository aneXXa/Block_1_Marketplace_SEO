"""Сборка инструкции пользователя (Участник 3) в .docx."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "screenshots"
OUT = ROOT / "Инструкция_пользователя_SEO_Seller.docx"

BG = (14, 22, 33)
PANEL = (23, 33, 43)
BOT = (36, 47, 61)
USER = (46, 125, 184)
BTN = (32, 48, 68)
BTN_LINE = (70, 130, 180)
WHITE = (255, 255, 255)
MUTED = (154, 170, 186)
GREEN = (82, 196, 26)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    return ImageFont.truetype(f"C:/Windows/Fonts/{name}", size)


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines: list[str] = []
    for raw in text.split("\n"):
        if raw == "":
            lines.append("")
            continue
        words = raw.split(" ")
        current = ""
        for word in words:
            trial = word if not current else f"{current} {word}"
            if draw.textlength(trial, font=fnt) <= width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
    return lines


def bubble(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    text: str,
    *,
    max_w: int,
    fill: tuple[int, int, int],
    align_right: bool = False,
    canvas_w: int,
) -> int:
    fnt = font(22)
    lines = wrap(draw, text, fnt, max_w - 36)
    line_h = 30
    h = 28 + line_h * max(1, len(lines))
    w = min(max_w, int(max(draw.textlength(line, font=fnt) for line in lines or [""]) + 40))
    left = canvas_w - 28 - w if align_right else x
    draw.rounded_rectangle((left, y, left + w, y + h), 16, fill=fill)
    ty = y + 12
    for line in lines:
        draw.text((left + 18, ty), line, font=fnt, fill=WHITE)
        ty += line_h
    return y + h + 12


def buttons(draw: ImageDraw.ImageDraw, y: int, labels: list[str], canvas_w: int) -> int:
    fnt = font(20, bold=True)
    x0, x1 = 24, canvas_w - 24
    for label in labels:
        draw.rounded_rectangle((x0, y, x1, y + 46), 12, fill=BTN, outline=BTN_LINE, width=2)
        tw = draw.textlength(label, font=fnt)
        draw.text(((canvas_w - tw) / 2, y + 10), label, font=fnt, fill=(140, 200, 255))
        y += 56
    return y + 4


def chat(path: Path, title: str, events: list[tuple[str, object]]) -> None:
    w, h = 720, 1280
    img = Image.new("RGB", (w, h), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, w, 88), fill=PANEL)
    draw.text((28, 22), title, font=font(26, bold=True), fill=WHITE)
    draw.text((28, 56), "@CardSEO_bot", font=font(16), fill=MUTED)
    y = 108
    for kind, payload in events:
        if kind == "bot":
            y = bubble(draw, 24, y, str(payload), max_w=560, fill=BOT, canvas_w=w)
        elif kind == "user":
            y = bubble(draw, 24, y, str(payload), max_w=500, fill=USER, align_right=True, canvas_w=w)
        elif kind == "btns":
            y = buttons(draw, y, list(payload), w)
        elif kind == "status":
            fnt = font(18)
            tw = draw.textlength(str(payload), font=fnt)
            draw.text(((w - tw) / 2, y), str(payload), font=fnt, fill=GREEN)
            y += 36
    img.crop((0, 0, w, min(h, y + 40))).save(path)


def set_run(run, *, size: int = 12, bold: bool = False, color: RGBColor | None = None) -> None:
    run.font.name = "Calibri"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = color


def add_p(doc: Document, text: str, *, bold: bool = False, size: int = 12) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.space_before = Pt(0)
    run = p.add_run(text)
    set_run(run, size=size, bold=bold)


def add_h(doc: Document, text: str) -> None:
    p = doc.add_heading(text, level=1)
    for run in p.runs:
        set_run(run, size=16, bold=True, color=RGBColor(0x1F, 0x3A, 0x5F))


def add_label(doc: Document, label: str, body: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(8)
    r1 = p.add_run(label)
    set_run(r1, bold=True)
    r2 = p.add_run(body)
    set_run(r2)


def add_shot(doc: Document, path: Path, caption: str) -> None:
    pic = doc.add_paragraph()
    pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pic.paragraph_format.space_after = Pt(4)
    pic.add_run().add_picture(str(path), width=Cm(11.5))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(14)
    run = cap.add_run(caption)
    set_run(run, size=10)
    run.italic = True


def build_shots() -> dict[str, Path]:
    SHOTS.mkdir(parents=True, exist_ok=True)
    files = {
        "landing": SHOTS / "01_vhod_v_bota.png",
        "start": SHOTS / "02_start.png",
        "facts": SHOTS / "03_vybor_ploshchadki.png",
        "wait": SHOTS / "04_ozhidanie.png",
        "result": SHOTS / "05_seo_paket.png",
        "switch": SHOTS / "06_drugaya_ploshchadka.png",
        "copy": SHOTS / "07_kopirovanie.png",
    }
    chat(
        files["start"],
        "SEO Seller",
        [
            (
                "bot",
                "Готовый SEO-пакет для Wildberries, Ozon и Авито за пару минут: "
                "заголовок, описание и теги под лимиты площадки.\n\nВыберите площадку.",
            ),
            ("btns", ["Wildberries", "Ozon", "Авито"]),
        ],
    )
    chat(
        files["facts"],
        "SEO Seller",
        [
            ("user", "Выбрана площадка: Wildberries"),
            (
                "bot",
                "Wildberries. Пришлите фото товара или сразу факты списком: "
                "тип, бренд, материал, цвет, для кого, повод.",
            ),
            ("btns", ["Без фото", "Сменить площадку"]),
            (
                "user",
                "Худи мужское\nБренд: Nordveil\nМатериал: хлопок 80%, полиэстер 20%\n"
                "Цвет: чёрный\nКрой: оверсайз\nДля кого: мужчины 25-40\n"
                "Повод: повседневная носка, подарок коллеге\nДетали: капюшон, карман кенгуру",
            ),
        ],
    )
    chat(
        files["wait"],
        "SEO Seller",
        [("status", "Собираю SEO-пакет…")],
    )
    chat(
        files["result"],
        "SEO Seller",
        [
            (
                "bot",
                "Wildberries · SEO-пакет\n\n"
                "Заголовок (47/60)\n"
                "Худи мужское оверсайз хлопок капюшон чёрное\n\n"
                "Описание (примерно 900/2000)\n"
                "Мужское худи оверсайз из хлопка с полиэстером для повседневной носки…\n\n"
                "Теги\nхуди мужское, оверсайз, хлопок, с капюшоном, карман кенгуру, "
                "повседневное, подарок коллеге, подарок мужчине\n\n"
                "Характеристики\nмужской, оверсайз, хлопок, чёрный, капюшон, подарок коллеге",
            ),
            (
                "btns",
                [
                    "Копировать заголовок",
                    "Копировать описание",
                    "Копировать теги",
                    "Копировать всё",
                    "Перегенерировать    Другая площадка",
                    "Новый товар",
                ],
            ),
        ],
    )
    chat(
        files["switch"],
        "SEO Seller",
        [
            ("user", "Другая площадка"),
            ("bot", "Куда пересобрать пакет?"),
            ("btns", ["Ozon", "Авито"]),
            (
                "bot",
                "Ozon · SEO-пакет\n\n"
                "Заголовок\nХуди мужское оверсайз хлопок капюшон карман кенгуру чёрное Nordveil\n\n"
                "Тот же товар, но название и теги уже под правила Ozon: "
                "бренд в заголовке, описание не для поиска.",
            ),
        ],
    )
    chat(
        files["copy"],
        "SEO Seller",
        [
            ("user", "Перегенерировать"),
            (
                "bot",
                "Другой угол формулировок того же товара: акцент на сценарий носки "
                "и подарок коллеге, без выдуманного состава.",
            ),
            ("btns", ["Копировать заголовок", "Копировать описание", "Копировать теги"]),
        ],
    )
    return files


def build_doc(shots: dict[str, Path]) -> None:
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.2)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = title.add_run("ИНСТРУКЦИЯ ПОЛЬЗОВАТЕЛЯ")
    set_run(r, size=20, bold=True, color=RGBColor(0x1F, 0x3A, 0x5F))
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sr = sub.add_run("Пошаговое руководство · Участник 3")
    set_run(sr, size=12, color=RGBColor(0x5A, 0x6A, 0x7A))
    note = doc.add_paragraph()
    nr = note.add_run(
        "Цель документа: любой человек, не знакомый с проектом, должен суметь пройти "
        "весь путь от первого входа до получения результата, используя только эту инструкцию."
    )
    set_run(nr, size=11)
    nr.italic = True

    add_h(doc, "0. Введение")
    add_label(doc, "Название проекта: ", "SEO Seller")
    add_label(doc, "Ссылка на работающий MVP: ", "https://t.me/CardSEO_bot")
    add_label(
        doc,
        "Для кого этот продукт: ",
        "Селлеры и контент-менеджеры, которые заполняют карточки на Wildberries, Ozon и Авито "
        "и не хотят каждый раз заново подгонять текст под лимиты площадки.",
    )
    add_label(
        doc,
        "Что он делает: ",
        "По фактам о товаре собирает готовый SEO-пакет: заголовок, описание, теги и характеристики под выбранную витрину.",
    )
    add_label(
        doc,
        "Сколько времени займёт знакомство: ",
        "3–5 минут до первого результата, если факты о товаре уже под рукой. Генерация обычно занимает от нескольких секунд до минуты.",
    )

    add_h(doc, "1. Первый вход в продукт")
    add_p(doc, "Как попасть в продукт")
    add_p(
        doc,
        "Откройте Telegram и перейдите по ссылке https://t.me/CardSEO_bot либо найдите бота по имени SEO Seller (@CardSEO_bot). "
        "Нажмите «Start Bot» / «Запустить» — откроется чат с ботом.",
    )
    add_p(doc, "Что нужно сделать на старте")
    add_p(
        doc,
        "Регистрация в продукте не нужна. Отдельный логин, почта и карта не запрашиваются. "
        "Достаточно аккаунта Telegram. Сразу после входа ничего заполнять не требуется: отправьте команду /start.",
    )
    add_p(doc, "Что пользователь увидит первым")
    add_p(
        doc,
        "Бот приветствует коротко: «Готовый SEO-пакет для Wildberries, Ozon и Авито за пару минут: "
        "заголовок, описание и теги под лимиты площадки.» Ниже — три кнопки площадок: Wildberries, Ozon, Авито. "
        "Это и есть главный экран. Кабинета, корзины и ленты заказов нет: весь сценарий живёт в одном чате.",
    )
    add_shot(doc, shots["landing"], "Рисунок 1. Страница входа в SEO Seller: имя бота и кнопка запуска.")
    add_shot(doc, shots["start"], "Рисунок 2. Стартовый экран после /start: приветствие и выбор площадки.")

    add_h(doc, "2. Основная функция №1. Собрать SEO-пакет под площадку")
    add_label(doc, "Название функции: ", "Генерация SEO-пакета под выбранную площадку")
    add_label(
        doc,
        "Зачем она нужна пользователю: ",
        "Закрывает самую частую боль селлера — написать карточку с нуля и не вылезти за лимиты. "
        "Wildberries режет название на 60 символах, у Ozon описание почти не участвует в поиске, "
        "на Авито в ленте видны первые строки. Бот держит эти правила и отдаёт черновик, который можно сразу вставить в карточку. "
        "В кабинеты маркетплейсов он ничего не публикует.",
    )
    add_p(doc, "Пошаговая инструкция")
    add_p(doc, "1. Пользователь открывает бота и отправляет /start.")
    add_p(doc, "2. Затем нажимает кнопку площадки — например, Wildberries.")
    add_p(
        doc,
        "3. Присылает факты о товаре списком (тип, бренд, материал, цвет, для кого, повод). "
        "Фото можно приложить или пропустить кнопкой «Без фото».",
    )
    add_p(
        doc,
        "4. Система обрабатывает запрос: на экране появляется статус «Собираю SEO-пакет…». "
        "Обычно это 5–40 секунд, иногда до минуты.",
    )
    add_p(
        doc,
        "5. Пользователь получает пакет: заголовок со счётчиком символов, описание, теги и характеристики — "
        "плюс кнопки копирования.",
    )
    add_label(
        doc,
        "Пример входных данных: ",
        "текст фактов. Фото необязательно. Файл и ссылка на кабинет не нужны.",
    )
    add_p(
        doc,
        "Худи мужское\n"
        "Бренд: Nordveil\n"
        "Материал: хлопок 80%, полиэстер 20%\n"
        "Цвет: чёрный\n"
        "Крой: оверсайз\n"
        "Для кого: мужчины 25-40\n"
        "Повод: повседневная носка, подарок коллеге\n"
        "Детали: капюшон, карман кенгуру",
    )
    add_label(doc, "Пример результата: ", "готовый пакет для Wildberries.")
    add_p(doc, "Заголовок: «Худи мужское оверсайз хлопок капюшон чёрное» (47 из 60 символов).")
    add_p(
        doc,
        "Описание: живой текст для покупателя — что это, кому подойдёт, как носить, как ухаживать. "
        "Состав только из ввода, без выдуманных сертификатов.",
    )
    add_p(
        doc,
        "Теги: худи мужское; оверсайз; хлопок; с капюшоном; карман кенгуру; повседневное; подарок коллеге; подарок мужчине.",
    )
    add_p(doc, "Характеристики: мужской, оверсайз, хлопок, чёрный, капюшон, подарок коллеге.")
    add_shot(doc, shots["facts"], "Рисунок 3. Выбор Wildberries и ввод фактов о товаре.")
    add_shot(doc, shots["wait"], "Рисунок 4. Ожидание: бот собирает SEO-пакет.")
    add_shot(doc, shots["result"], "Рисунок 5. Результат core-функции: пакет с кнопками копирования.")

    add_h(doc, "3. Основная функция №2. Пересобрать тот же товар под другую площадку")
    add_label(doc, "Название функции: ", "Пересборка пакета под другую витрину без повторного ввода")
    add_label(
        doc,
        "Зачем она нужна: ",
        "Один товар часто продают сразу на нескольких площадках. "
        "Не нужно заново набирать факты: бот берёт тот же ввод и переписывает текст под другие лимиты и правила поиска.",
    )
    add_p(doc, "Пошаговая инструкция")
    add_p(doc, "1. После готового пакета нажмите «Другая площадка».")
    add_p(doc, "2. Выберите витрину, которой ещё не было — например, Ozon. Текущая кнопка скрывается.")
    add_p(doc, "3. Дождитесь нового пакета. Факты и фото подставляются автоматически.")
    add_label(
        doc,
        "Пример входных данных: ",
        "те же факты худи Nordveil, без повторного набора.",
    )
    add_label(
        doc,
        "Пример выходных данных: ",
        "для Ozon заголовок длиннее и содержит бренд: "
        "«Худи мужское оверсайз хлопок капюшон карман кенгуру чёрное Nordveil». "
        "Теги и характеристики становятся опорой для поиска, потому что описание Ozon почти не индексирует.",
    )
    add_shot(doc, shots["switch"], "Рисунок 6. Пересборка того же товара под Ozon.")

    add_h(doc, "4. Основная функция №3. Скопировать поля и получить другой вариант текста")
    add_label(doc, "Название функции: ", "Копирование полей и перегенерация формулировок")
    add_label(
        doc,
        "Зачем она нужна: ",
        "Это завершение цикла: текст не остаётся в чате «для чтения», его можно сразу унести в карточку. "
        "Если тон не зашёл — другой угол без смены товара. Так селлер закрывает задачу: получил, выбрал, вставил.",
    )
    add_p(doc, "Пошаговая инструкция")
    add_p(
        doc,
        "1. Нажмите «Копировать заголовок», «Копировать описание», «Копировать теги» или «Копировать всё». "
        "Короткое поле сразу попадает в буфер. Если текст длиннее лимита кнопки Telegram (256 символов), "
        "бот пришлёт его отдельным сообщением — скопируйте из чата.",
    )
    add_p(
        doc,
        "2. Если формулировка не подошла, нажмите «Перегенерировать». "
        "Бот напишет тот же товар иначе: другой акцент, без дословного повтора.",
    )
    add_p(doc, "3. Для следующего SKU нажмите «Новый товар» — диалог начнётся с выбора площадки.")
    add_label(
        doc,
        "Пример результата: ",
        "заголовок в буфере обмена; либо новый вариант описания того же худи с акцентом на подарок коллеге. "
        "Состав и бренд по-прежнему только из исходных фактов.",
    )
    add_shot(doc, shots["copy"], "Рисунок 7. Копирование полей и перегенерация формулировок.")

    add_h(doc, "5. Что делать, если что-то пошло не так")
    add_label(
        doc,
        "Ошибка №1: бот не отвечает, чат «молчит» после /start. ",
        "→ MVP работает, только пока запущен процесс бота. Подождите минуту и отправьте /start ещё раз. "
        "Если ответа нет, напишите тому, кто показывает демо: инстанс могли остановить.",
    )
    add_label(
        doc,
        "Ошибка №2: вместо пакета пришло «Не удалось обратиться к модели» или кнопка «Повторить». ",
        "→ Демо ходит в бесплатный шлюз, он иногда отвечает пусто или с задержкой. Подождите полминуты и нажмите «Повторить». "
        "Не открывайте несколько копий бота сразу.",
    )
    add_label(
        doc,
        "Ошибка №3: бот пишет «Нужны фото или хотя бы несколько фактов о товаре». ",
        "→ Пришлите текст: что это за товар, материал, цвет, для кого. Одной фразы «вещь» мало. "
        "Фото само по себе допустимо, но факты делают текст заметно точнее.",
    )
    add_label(
        doc,
        "Ошибка №4: генерация идёт дольше минуты. ",
        "→ Не нажимайте кнопки пачкой. Дождитесь статуса или сообщения об ошибке. "
        "Если ответа нет — «Повторить» или /start.",
    )

    add_h(doc, "6. Частые вопросы (FAQ)")
    add_label(
        doc,
        "Бот сам опубликует карточку на Wildberries, Ozon или Авито? ",
        "Нет. Он готовит черновик. Публикацию в кабинете селлер делает сам.",
    )
    add_label(
        doc,
        "Нужно ли платить или вводить ключ нейросети? ",
        "Для демо — нет. Сейчас стоит бесплатный шлюз, чтобы показать систему. "
        "В рабочем контуре планируется более сильная модель.",
    )
    add_label(
        doc,
        "Обязательно ли фото? ",
        "Нет. Достаточно фактов списком. Кнопка «Без фото» как раз для этого. "
        "Фото помогает сверить цвет и детали, которые вы не успели написать.",
    )
    add_label(
        doc,
        "Бот не допишет состав и размер, если я их не указал? ",
        "Да, так и задумано. Неизвестное он пропускает, а не выдумывает.",
    )
    add_label(
        doc,
        "Можно ли сделать текст сразу на три площадки? ",
        "Да. Сначала соберите пакет на одной, затем «Другая площадка» — факты вводить заново не нужно.",
    )

    footer = doc.add_paragraph()
    footer.paragraph_format.space_before = Pt(18)
    fr = footer.add_run(
        "Рисунки 2–7 воспроизводят реальные тексты и кнопки диалога SEO Seller. "
        "Рисунок 1 — живая страница https://t.me/CardSEO_bot."
    )
    set_run(fr, size=10, color=RGBColor(0x5A, 0x6A, 0x7A))
    fr.italic = True

    doc.save(OUT)


if __name__ == "__main__":
    build_doc(build_shots())
    print(OUT)
