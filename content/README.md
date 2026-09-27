# Рукописный контент

Пишется агентами, сливается с `data/` при сборке сайта. Формат:

## `content/species/<slug>.md` — карточка вида

Слаг = `id` из `data/species_index.json`. Сайт читает и проверяет карточки при сборке (`site/src/lib/content.ts`,
`site/src/lib/traits.ts`): ошибка схемы или признак вне словаря роняет `npm run build` с именем файла.
Пример: `content/species/grallaria-hypoleuca.md`.

```markdown
---
id: grallaria-hypoleuca            # обязательно, = имя файла и id в data/species_index.json
difficulty: medium                 # easy | medium | hard — насколько легко узнать в поле
lynx_page: null                    # ручное переопределение страницы в Lynx «Birds of Colombia» (Hilty 2021); по умолчанию null — сайт берёт lynx_page из data/species_index.json
checked: 2026-09-27                # необязательно: дата последнего факт-чека (YYYY-MM-DD), на сайте не показывается; сводка — scripts/card_index.py → docs/fact-check/INDEX.md
key_features:                      # 3–5 признаков, каждый начинается с признака, ≤ 20 слов
  - "Горло и брюхо чисто белые, без пестрин"
similar:                           # похожие виды: id из индекса (лучше с маршрута) и отличие одной фразой
  - id: grallaria-ruficapilla
    how: "грудь в крупных тёмных пестринах, голова ярче каштановая"
behavior: "1–2 предложения: где держится и что делает"
voice: "1 предложение: голос словами"
traits:                            # словарь определителя, см. ниже
  size: thrush
  colors: [rufous, white, gray]
  tone: dull
  marks: [short_tail, plain]
  bill: medium
  layer: [ground, understory, feeder]
sources:                           # что использовано; тексты Wikipedia — с лицензией
  - "Wikipedia: White-bellied antpitta (en, CC BY-SA 4.0)"
  - "Данные проекта: data/species/grallaria-hypoleuca.json (ACO 2022, BIRDBASE 2025)"
en:                                # английское зеркало, те же id в similar и в том же порядке
  key_features: ["..."]
  similar: [{ id: grallaria-ruficapilla, how: "..." }]
  behavior: "..."
  voice: "..."
---
Текст по-русски, 60–120 слов: где и на каких высотах живёт, чем выделяется, где искать на маршруте
(локации и даты из data/site_species.json / study_lists.json).

## English

The same text in English.
```

Отдельной врезки «для новичка» нет (поле `beginner_note` удалено 27.09, сборка падает, если оно есть в карточке): подсказки для начинающего пишутся прямо в тексте, голосом полевого определителя, без снисходительного тона и без повтора `key_features` (образ вроде «в тени кажется просто чёрным, первыми видны белые пятна на груди» — в абзац).

Факты — из `data/species/<slug>.json`, `data/texts/<slug>.json` (Wikipedia, CC BY-SA, указать в `sources`) и общих
знаний; из защищённых определителей (Lynx, Birds of the World, eBird) не копировать. Стиль и термины — скилл `polish`.

### `traits` — закрытый словарь определителя

Словарь с русскими подписями — `content/traits.yaml` (его читает страница `/identify/`). Значение вне словаря или
неверное число значений в группе — ошибка сборки. Одно значение можно писать строкой, несколько — списком.

| Группа | Сколько | Значения |
|---|---|---|
| `size` | ровно 1 | `hummingbird` (любой колибри и крошки до 10 см), `sparrow` 10–16 см, `thrush` 17–25, `pigeon` 26–35, `crow` 36–55, `larger` > 55 |
| `colors` | 1–3 | `black gray brown rufous olive yellow orange red blue green white purple` — главные цвета, заметные в поле, по убыванию площади |
| `tone` | ровно 1 | `bright` (насыщенные цвета или резкий контраст) · `dull` (приглушённая, однотонная, в т. ч. белые цапли) |
| `marks` | 0 и больше | `crest eye_ring eyebrow mask wing_bars streaked_breast spotted_breast barred long_tail short_tail forked_tail white_tail_tips rump_patch throat_patch bare_face wattle plain` |
| `bill` | 1–2 | `short medium long curved hooked thick thin flat hummingbird_long` |
| `layer` | 1 и больше | `ground understory midstory canopy water air feeder night` |

Правила разметки:
- Размер — по длине тела из справочников; все колибри — `hummingbird`, даже длиннохвостые и с длинным клювом.
  Пограничные виды — в класс, в который их поставит человек в поле (Great Thrush ≈ 30 см — `pigeon`).
- `colors` описывают взрослого самца в типичном наряде; если самка резко отличается, её цвет можно добавить третьим.
- `plain` — оперение тела без пятен, пестрин и полос; сочетается со структурными приметами (`short_tail`, `crest`)
  и мелкими метками на голове (`eye_ring`).
- `bill`: длина относительно головы; у колибри вместо `long` — `hummingbird_long` (клюв заметно длиннее головы),
  `hooked` — крючок на конце надклювья (цветоколы, хищники), `thick` — массивный (бородатки, туканы, вьюрки).
- `layer`: где птицу обычно видят; `feeder` — если регулярно ходит на кормушки маршрута; `night` — активна ночью.
- Словарь закрытый и меняется редко и осознанно. Новое значение добавляется только когда без него целая группа птиц
  неразличима в определителе, одним решением после ревизии (см. docs/TODO.md), не по ходу написания карточек.
  При добавлении: правь `content/traits.yaml` и эту таблицу вместе, запиши в traits.yaml дату и причину, прогони
  сборку и обязательно сделай проход переразметки по всем существующим карточкам (один агент на ~200 карточек, только
  по тексту карточек, без веба): иначе в определителе старые виды исчезнут при выборе нового чипа. Удаление или
  переименование значения сборка проверит сама — покажет карточки, где оно осталось.

## `content/similar/<slug-a>--<slug-b>.md`

Сравнение двух (или группы) похожих видов: таблица признаков, на что смотреть первым делом.
