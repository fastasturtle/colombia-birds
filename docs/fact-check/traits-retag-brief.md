# Переразметка `traits` после ревизии словаря (27.09.2026)

Ревизия словаря определителя по 467 карточкам. Решения записаны в `content/traits.yaml` (журнал изменений в
начале файла) и в правилах `content/README.md` → «`traits` — закрытый словарь определителя». Здесь: на чём основаны
решения и что сделать с каждой карточкой. Сами карточки при ревизии не менялись: сборка проходит, новые значения
необязательны.

## Что изменилось

| Что | Было | Стало |
|---|---|---|
| `size` | ровно 1 класс | 1–2 **соседних** класса: диапазон длины через границу или хвост ≥ половины длины |
| `size.hummingbird` | «с колибри», «крошки до 10 см» | «колибри и крошки»: любой колибри; прочие короче 10 см (ровно 10 см — `sparrow`) |
| `marks` | 17 значений | + `cap` (шапочка/капюшон), `wing_patch` (пятно на крыле), `bright_bill` (яркий клюв); `plain` не сочетается с `cap`/`wing_patch` |
| `colors`/`tone` | «взрослый самец в типичном наряде» | наряд, который виден на маршруте в октябре: у северных мигрантов осенний/зимний/первогодний; оттенки вне словаря сводятся к ближайшему |
| `layer.feeder` | «регулярно ходит на кормушки маршрута» | только с подтверждением для маршрута (источник или «точно» на точке с кормушкой нужного корма) |

## Основания (коротко)

- **Размер.** Из 406 карточек не-колибри у 327 длина есть в Wikipedia (`data/texts/<slug>.json`); у 72 из них
  опубликованный диапазон переходит границу класса, ещё 7 разобраны ошибочно (размах крыльев, масса). Логи факт-чека
  отмечают ~20 пограничных решений (`batch1-C`, `batch2-B`, `batch3-*`, `log-*-b3-*`), и они приняты по-разному
  (Club-winged Manakin 9,5–10 см — `sparrow`, Rufous-crowned Tody-Flycatcher 9–10 см — `hummingbird`; Columbina
  buckleyi `thrush`, C. talpacoti `sparrow`). В определителе чипы одной группы работают как «или», поэтому два
  соседних класса у пограничного вида — это «найдётся при любой догадке», а не шум. Длиннохвостые (Asthenes fuliginosa
  18–20 см, половина — хвост) получают и класс «по телу».
- **Колибри-класс.** В нём 65 карточек: 61 колибри и 4 не-колибри (picumnus-lafresnayi, platyrinchus-flavigularis,
  poecilotriccus-ruficeps, todirostrum-cinereum). Подпись «с колибри» читалась как «только колибри».
- **Приметы.** `marks: []` у 87 карточек из 467 (19 %): Thraupidae 22, Trochilidae 17, Columbidae 5, Fringillidae 4 и др.
  Их `key_features` описывают как раз то, чего в словаре не было: контрастную шапочку или капюшон (≈35 из 87), цвет
  клюва (≈12), пятно на крыле (≈7). По `key_features` всех карточек кандидатов: `cap` ≈135 (с запасом, regex),
  `bright_bill` ≈69, `wing_patch` ≈31 — у каждого больше 10. Отклонены: светлый/яркий глаз (≈55 карточек, но виден
  только вблизи, остаётся в `key_features`), новые цвета pink/ochre (жалобы в batch1-A, batch2-B, batch3-6 решаются
  правилом сведения оттенков).
- **Распределение значений** (467 карточек): все значения используются; самые редкие — `wattle` 7, `night` 8,
  `hummingbird_long` 11, `curved` 12. Доминируют `bill: short` (55 %) и `layer: midstory` (50 %) — это свойство
  птиц, не словаря; `tone` делится 219/248. `colors`: 1 цвет у 28 карточек, 2 — у 198, 3 — у 241.
- **Мигранты.** 31 карточка со статусом `boreal_migrant`/`austral_migrant` (28 северных); TODO просил правило
  «осенний наряд» (piranga-olivacea уже размечена так). Сезонный наряд есть и у местных видов (Andean Gull —
  вопрос batch1-D не решён источниками).
- **Кормушки.** `feeder` у 37 карточек; по логам факт-чека у 12 из них основание — «общее знание» или портрет семейства
  без точки маршрута. Сверка с `data/site_species.json` («точно» на точке с кормушкой) и с источниками дала списки ниже.

## Как делить работу

Три агента по алфавитным диапазонам слагов (`ls content/species`). Карточки, появившиеся после этой записки, агент
берёт в своём диапазоне так же.

| Агент | Диапазон слагов | Карточек на 27.09 |
|---|---|---|
| 1 | `actitis-macularius` … `elaenia-pallatangae` | 156 |
| 2 | `elanus-leucurus` … `pharomachrus-antisianus` | 156 |
| 3 | `pharomachrus-auriceps` … `zonotrichia-capensis` | 155 |

Источники — только локальные: текст карточки, `data/species/<slug>.json`, `data/texts/<slug>.json` (Wikipedia),
`data/site_species.json`, `data/sites.json`, `content/families/`, `content/groups/`, `docs/fact-check/`. Веба нет.
Правится только `traits` (и, для мигрантов, одна фраза в `key_features` + её `en`-зеркало). `checked:` не трогать.
В конце: `cd site && npm ci && npm run verify`, лог `docs/fact-check/retag-2026-09-27-<N>.md` (слаг → что изменено и
почему, одна строка на карточку; карточки без изменений — одной строкой-списком).

## Порядок проверки каждой карточки (все 467)

1. **`size`** — таблица ниже даёт готовое предложение для 87 карточек; для остальных оставить как есть. Перед
   записью сверить число с `data/texts/<slug>.json` → `wikipedia.en.sections.Description` (скрипт брал первое
   «N cm» в тексте и мог схватить не длину). Не-колибри короче 10 см по всему диапазону — `hummingbird`;
   колибри — всегда один `hummingbird`. Два значения пишутся списком в порядке словаря: `size: [sparrow, thrush]`.
2. **`colors`/`tone`** — у мигрантов и сезонных видов (список ниже) — наряд октября; у всех — сведение оттенков
   (охристый/коричный/каштановый → `rufous`, розовый → `red`, сиренево-розовый → `purple`, медный → `orange`,
   серебристый/сизый → `gray`). Цвета не менять без причины из этих двух правил.
3. **`marks`** — у каждой карточки проверить три новых значения по `key_features` и тексту: `cap` (темя или вся
   голова резко другого цвета, чем спина и грудь; не маска через глаз и не только горло), `wing_patch` (пятно,
   зеркальце, цветное плечо, пятно у основания маховых; не две полосы), `bright_bill` (яркий клюв, его заметная
   половина или лобный щиток). Затем убрать `plain`, если появились `cap` или `wing_patch`. Карточки с пустым
   `marks` (87, список ниже) проверить первыми; если птица однотонная — поставить `plain`.
4. **`layer.feeder`** — по спискам ниже: оставить, снять, добавить.
5. `bill` не меняется (цвет клюва — только в `marks`).

Списки кандидатов на `cap`/`wing_patch`/`bright_bill` ниже собраны regex по `key_features` — это подсказка, а не
решение: часть ложных (например, «шапочка темнее» — не резкий контраст), часть видов не найдена (атлапеты с полосой
на темени, розовый клюв catamenia-inornata).

## 1. Размер: 87 карточек с предложением

«Wikipedia, см» — первое число «N cm» из `data/texts`; «—» — длины нет, предложение только по правилу хвоста.
Хвостовое правило применено к 19 видам, у которых хвост около половины длины или есть косицы: Piaya, Crotophaga,
Hirundo, Synallaxis, Asthenes, Leptasthenura, Drymophila, мотмоты, Phaethon, Pyrrhura, Aratinga, Orthopsittaca,
Quiscalus (самец), Cissopis, Hydropsalis. Остальные 43 карточки не-колибри с `long_tail`/`forked_tail` (трогоны,
якамары, арасари, гуаны и чачалаки, фрегат, ласточки без косиц) не понижаются; если агент по тексту видит хвост ≥ половины
длины — применить правило и записать в лог.

Не разобраны автоматически (ошибочное число в Wikipedia-выдержке): `nyctibius-grandis`, `oxyura-jamaicensis`,
`pelecanus-occidentalis`, `thalasseus-maximus` — оставить как есть, если текст карточки не даёт диапазона через
границу.

#### Агент 1

| slug | сейчас | Wikipedia, см | предлагается | почему |
|---|---|---|---|---|
| `aratinga-weddellii` | pigeon | 25–28 | **thrush, pigeon** | хвост (диапазон уже даёт два класса) |
| `asthenes-flammulata` | sparrow | 16–17 | **sparrow, thrush** | диапазон через границу |
| `asthenes-fuliginosa` | thrush | 18–20 | **sparrow, thrush** | хвост |
| `baryphthengus-martii` | crow | 42–47 | **pigeon, crow** | хвост |
| `cacicus-cela` | pigeon | 30–45 | **pigeon, crow** | диапазон через границу |
| `cacicus-chrysonotus` | pigeon | 25–30 | **thrush, pigeon** | диапазон через границу |
| `camptostoma-obsoletum` | sparrow | 9.5–10.5 | **hummingbird, sparrow** | диапазон через границу |
| `capito-squamatus` | thrush | 16–18 | **sparrow, thrush** | диапазон через границу |
| `catharus-ustulatus` | thrush | 16–20 | **sparrow, thrush** | диапазон через границу |
| `celeus-flavus` | pigeon | 24–27 | **thrush, pigeon** | диапазон через границу |
| `chamaepetes-goudotii` | larger | 50–65 | **crow, larger** | диапазон через границу |
| `cissopis-leverianus` | pigeon | 25–30 | **thrush, pigeon** | хвост (диапазон уже даёт два класса) |
| `columbina-talpacoti` | sparrow | 12–18 | **sparrow, thrush** | диапазон через границу |
| `contopus-fumigatus` | thrush | 16–17 | **sparrow, thrush** | диапазон через границу |
| `crotophaga-ani` | pigeon | 35–35 | **thrush, pigeon** | хвост |
| `crotophaga-major` | crow | 46–46 | **pigeon, crow** | хвост |
| `cyanerpes-caeruleus` | sparrow | 9.3–11.4 | **hummingbird, sparrow** | диапазон через границу |
| `cyanocorax-violaceus` | crow | 33–37 | **pigeon, crow** | диапазон через границу |
| `dichrozona-cincta` | sparrow | 9–10 | **hummingbird, sparrow** | диапазон через границу |
| `dryocopus-lineatus` | pigeon | 31.5–36 | **pigeon, crow** | диапазон через границу |
| `elaenia-flavogaster` | sparrow | 15–17 | **sparrow, thrush** | диапазон через границу |

#### Агент 2

| slug | сейчас | Wikipedia, см | предлагается | почему |
|---|---|---|---|---|
| `elanus-leucurus` | crow | 35–43 | **pigeon, crow** | диапазон через границу |
| `electron-platyrhynchum` | pigeon | — | **thrush, pigeon** | хвост |
| `euphonia-concinna` | sparrow | 9–10 | **hummingbird, sparrow** | диапазон через границу |
| `euphonia-xanthogaster` | sparrow | 9–11 | **hummingbird, sparrow** | диапазон через границу |
| `fulica-americana` | crow | 34–43 | **pigeon, crow** | диапазон через границу |
| `furnarius-leucopus` | thrush | 15–18 | **sparrow, thrush** | диапазон через границу |
| `geotrygon-saphirina` | thrush | 22–26 | **thrush, pigeon** | диапазон через границу |
| `grallaria-hypoleuca` | thrush | 16–18 | **sparrow, thrush** | диапазон через границу |
| `grallaria-rufocinerea` | thrush | 15–18 | **sparrow, thrush** | диапазон через границу |
| `gymnoderus-foetidus` | crow | 34–39 | **pigeon, crow** | диапазон через границу |
| `himantopus-mexicanus` | crow | 35–39 | **pigeon, crow** | диапазон через границу |
| `hirundo-rustica` | sparrow | 17–19 | **sparrow, thrush** | хвост |
| `hydropsalis-climacocerca` | thrush | — | **sparrow, thrush** | хвост |
| `ictinia-plumbea` | crow | 34–37.5 | **pigeon, crow** | диапазон через границу |
| `laterallus-melanophaius` | sparrow | 14–18 | **sparrow, thrush** | диапазон через границу |
| `legatus-leucophaius` | sparrow | 14.5–17 | **sparrow, thrush** | диапазон через границу |
| `leptasthenura-andicola` | sparrow | 15–17 | **sparrow, thrush** | хвост (диапазон уже даёт два класса) |
| `leptotila-pallida` | thrush | 23–26 | **thrush, pigeon** | диапазон через границу |
| `machaeropterus-deliciosus` | sparrow | 9.5–10 | **hummingbird, sparrow** | диапазон через границу |
| `mesembrinibis-cayennensis` | crow | 45–60 | **crow, larger** | диапазон через границу |
| `micrastur-gilvicollis` | pigeon | 33–38 | **pigeon, crow** | диапазон через границу |
| `microbates-cinereiventris` | sparrow | 9–11 | **hummingbird, sparrow** | диапазон через границу |
| `myiozetetes-cayanensis` | thrush | 16.5–18 | **sparrow, thrush** | диапазон через границу |
| `myiozetetes-similis` | thrush | 16–18.5 | **sparrow, thrush** | диапазон через границу |
| `nothocrax-urumutum` | larger | 50–57.5 | **crow, larger** | диапазон через границу |
| `nyctanassa-violacea` | larger | 55–70 | **crow, larger** | диапазон через границу |
| `odontophorus-hyperythrus` | pigeon | 25–29 | **thrush, pigeon** | диапазон через границу |
| `odontophorus-melanonotus` | pigeon | 23–28 | **thrush, pigeon** | диапазон через границу |
| `ortalis-cinereiceps` | crow | 48–58 | **crow, larger** | диапазон через границу |
| `ortalis-columbiana` | crow | 50–60 | **crow, larger** | диапазон через границу |
| `orthopsittaca-manilatus` | crow | 46–46 | **pigeon, crow** | хвост |
| `pandion-haliaetus` | larger | 50–66 | **crow, larger** | диапазон через границу |
| `patagioenas-fasciata` | pigeon | 33–40 | **pigeon, crow** | диапазон через границу |
| `phaethon-aethereus` | crow | 90–105 | **crow, larger** | хвост |

#### Агент 3

| slug | сейчас | Wikipedia, см | предлагается | почему |
|---|---|---|---|---|
| `pharomachrus-auriceps` | pigeon | 30–36 | **pigeon, crow** | диапазон через границу |
| `piaya-cayana` | crow | 40.5–50 | **pigeon, crow** | хвост |
| `picumnus-lafresnayi` | hummingbird | 9–10 | **hummingbird, sparrow** | диапазон через границу |
| `piranga-olivacea` | thrush | 16–19 | **sparrow, thrush** | диапазон через границу |
| `pitangus-sulphuratus` | thrush | 25–28 | **thrush, pigeon** | диапазон через границу |
| `platyrinchus-flavigularis` | hummingbird | 9.5–10.2 | **hummingbird, sparrow** | диапазон через границу |
| `plegadis-falcinellus` | larger | 48–66 | **crow, larger** | диапазон через границу |
| `podilymbus-podiceps` | pigeon | 31–38 | **pigeon, crow** | диапазон через границу |
| `poecilotriccus-ruficeps` | hummingbird | 9–10 | **hummingbird, sparrow** | диапазон через границу |
| `progne-chalybea` | thrush | 16–18 | **sparrow, thrush** | диапазон через границу |
| `pyrrhura-calliptera` | thrush | 22–23 | **sparrow, thrush** | хвост |
| `pyrrhura-melanura` | thrush | 23–25 | **sparrow, thrush** | хвост |
| `querula-purpurata` | pigeon | 25–30 | **thrush, pigeon** | диапазон через границу |
| `quiscalus-mexicanus` | crow | 38–46 | **pigeon, crow** | хвост |
| `rallus-semiplumbeus` | pigeon | 25–30 | **thrush, pigeon** | диапазон через границу |
| `ramphastos-ambiguus` | crow | 47–61 | **crow, larger** | диапазон через границу |
| `ramphastos-tucanus` | crow | 50–61 | **crow, larger** | диапазон через границу |
| `ramphocelus-carbo` | sparrow | 16–17 | **sparrow, thrush** | диапазон через границу |
| `rupornis-magnirostris` | pigeon | 31–41 | **pigeon, crow** | диапазон через границу |
| `serpophaga-cinerea` | sparrow | 9.5–12 | **hummingbird, sparrow** | диапазон через границу |
| `spinus-psaltria` | sparrow | 9–12 | **hummingbird, sparrow** | диапазон через границу |
| `spinus-spinescens` | sparrow | 9.5–11 | **hummingbird, sparrow** | диапазон через границу |
| `sturnella-magna` | thrush | 19–28 | **thrush, pigeon** | диапазон через границу |
| `synallaxis-azarae` | sparrow | 15–18 | **sparrow, thrush** | хвост (диапазон уже даёт два класса) |
| `synallaxis-subpudica` | thrush | 17–19 | **sparrow, thrush** | хвост |
| `thraupis-episcopus` | sparrow | 16–18 | **sparrow, thrush** | диапазон через границу |
| `thraupis-palmarum` | sparrow | 19–19 | **thrush** | диапазон через границу |
| `todirostrum-cinereum` | hummingbird | 8.8–10.2 | **hummingbird, sparrow** | диапазон через границу |
| `tringa-melanoleuca` | pigeon | 29–40 | **pigeon, crow** | диапазон через границу |
| `tringa-semipalmata` | crow | 31–41 | **pigeon, crow** | диапазон через границу |
| `vanellus-chilensis` | pigeon | 32–38 | **pigeon, crow** | диапазон через границу |
| `volatinia-jacarina` | sparrow | 8.7–10.9 | **hummingbird, sparrow** | диапазон через границу |

## 2. `feeder`: оставить 28, снять 9, проверить на добавление 22

Точки с кормушками (`data/sites.json`, `route_note` портретов): нектар — observatorio-colibries, chicaque,
finca-discosura, aves-y-florez, la-nutria, el-encanto; фрукты — aves-y-florez, el-encanto (бананы и кукуруза,
источник в логе факт-чека), la-nutria; черви — la-drymophila.

**Оставить** — вид «точно» на точке с подходящей кормушкой и высота совпадает (22):
- агент 1 (8): `aglaiocercus-coelestis` (aves-y-florez, la-nutria), `amazilia-tzacatl` (la-nutria), `boissonneaua-jardini` (aves-y-florez), `coeligena-wilsoni` (aves-y-florez, la-nutria), `coereba-flaveola` (chicaque, la-nutria, el-encanto), `colibri-coruscans` (observatorio-colibries, el-encanto), `colibri-cyanotus` (observatorio-colibries, chicaque), `colibri-delphinae` (el-encanto)
- агент 2 (4): `ensifera-ensifera` (observatorio-colibries), `heliodoxa-imperatrix` (la-nutria), `heliodoxa-jacula` (aves-y-florez), `ortalis-columbiana` (el-encanto)
- агент 3 (10): `ramphocelus-dimidiatus` (el-encanto), `ramphocelus-flammigerus` (aves-y-florez, la-nutria), `stilpnia-vitriolina` (el-encanto), `tangara-gyrola` (el-encanto), `tangara-icterocephala` (la-nutria), `thalurania-colombica` (aves-y-florez), `thraupis-episcopus` (el-encanto, la-nutria), `thraupis-palmarum` (el-encanto), `uranomitra-franciae` (el-encanto), `urosticte-benjamini` (la-nutria)

**Оставить по прямому источнику** (в `site_species` вид не «точно», но точка и кормушка названы) (6):
- агент 1: `coeligena-bonapartei` — Чикаке: content/groups/swifts-hummingbirds.md route_note, факт-чек (thebirdersshow.com)
- агент 1: `coeligena-prunellei` — Чикаке: route_note swifts-hummingbirds (Black Inca у кормушек)
- агент 2: `heliangelus-exortis` — Чикаке: route_note swifts-hummingbirds (Tourmaline Sunangel)
- агент 2: `grallaria-hypoleuca` — Ла-Дримофила: route_note grallariidae и antbirds-ovenbirds
- агент 2: `grallaricula-cucullata` — Ла-Дримофила: route_note grallariidae, факт-чек (elencantonaturereserve.com)
- агент 3: `semnornis-ramphastinus` — Авес-и-Флорес: route_note toucans-woodpeckers

**Снять** — основание только «общее знание» (логи batch2-A, batch2-D, log-b2-*), на точках с кормушками вид не
«точно» (9). Естественные ярусы у всех остаются:
- агент 1 (2): `aglaiocercus-kingii` (точно: sibundoy), `coeligena-torquata` (точно: trampolin-aves)
- агент 2 (0): —
- агент 3 (7): `ramphocelus-carbo` (точно: el-escondite, finca-discosura, orito, playa-rica, puerto-asis), `saltator-atripennis` (точно: la-planada), `saltator-maximus` (точно: km-42), `saucerottia-cyanifrons` (точно: нигде), `sporathraupis-cyanocephala` (точно: trampolin-aves), `stilpnia-heinei` (точно: sibundoy), `stilpnia-larvata` (точно: km-42, la-planada)

**Добавить, если текст карточки не противоречит** (вид «точно» на точке с кормушкой нужного корма, высота
совпадает; чаще всего это колибри Обсерватории и фруктоеды Эль-Энканто/Авес-и-Флорес) (22):
- агент 1 (10): `anthracothorax-nigricollis` (finca-discosura), `bangsia-edwardsi` (aves-y-florez), `cacicus-uropygialis` (aves-y-florez), `chaetocercus-mulsant` (observatorio-colibries), `chionomesa-fimbriata` (finca-discosura), `chlorochrysa-phoenicotis` (aves-y-florez, la-nutria), `chrysuronia-goudoti` (el-encanto), `coeligena-helianthea` (observatorio-colibries), `diglossa-humeralis` (observatorio-colibries), `diglossa-indigotica` (aves-y-florez, la-nutria)
- агент 2 (9): `eriocnemis-cupreoventris` (observatorio-colibries), `eriocnemis-vestita` (observatorio-colibries), `eubucco-bourcierii` (el-encanto), `euphonia-laniirostris` (el-encanto), `euphonia-xanthogaster` (aves-y-florez, la-nutria), `ixothraupis-rufigula` (aves-y-florez, la-nutria), `lesbia-nuna` (observatorio-colibries), `lesbia-victoriae` (observatorio-colibries), `metallura-tyrianthina` (observatorio-colibries)
- агент 3 (3): `pterophanes-cyanopterus` (observatorio-colibries), `stilpnia-cyanicollis` (el-encanto), `tangara-arthus` (la-nutria)

Отшельники `androdon-aequatorialis` и `phaethornis-yaruqui` формально проходят, но по правилу берутся только по
прямому источнику — не добавлять. Если лид решит держать `feeder` строже (только по прямому источнику), блок
«Добавить» пропускается целиком.

## 3. Наряд октября: 31 мигрант и 7 местных видов с сезонным нарядом

Проверить `colors`, `tone`, `marks` на соответствие октябрьскому наряду и что одна из `key_features` его называет
(«осенью…», «зимой…», «молодые первой осени…»; `en` — тем же пунктом). Брачные приметы, которых в октябре нет,
из `marks` убрать (пример: пятна на груди у Spotted Sandpiper; чёрный капюшон у Laughing Gull). `piranga-olivacea`
уже размечена по осеннему наряду — образец.

Где разница наряда заметна (смотреть в первую очередь, 16):
- агент 1 (4): `calidris-alba`, `calidris-minutilla`, `actitis-macularius`, `charadrius-semipalmatus`
- агент 2 (3): `numenius-hudsonicus`, `leucophaeus-atricilla`, `hirundo-rustica`
- агент 3 (9): `piranga-rubra`, `setophaga-fusca`, `setophaga-cerulea`, `pluvialis-squatarola`, `tringa-melanoleuca`, `tringa-semipalmata`, `tringa-solitaria`, `thalasseus-maximus`, `spatula-discors`

Остальные мигранты — наряд почти не меняется, только сверить (15):
- агент 1 (5): `cardellina-canadensis`, `cathartes-aura`, `catharus-ustulatus`, `coccyzus-americanus`, `contopus-virens`
- агент 2 (5): `fulica-americana`, `gallinula-galeata`, `hydrobates-tethys`, `oxyura-jamaicensis`, `pandion-haliaetus`
- агент 3 (5): `piranga-olivacea`, `pygochelidon-cyanoleuca`, `tyrannus-melancholicus`, `tyrannus-tyrannus`, `vireo-olivaceus`

Местные виды с сезонным нарядом (в тексте есть «брачный»): если наряд в октябре не известен, цвета покрывают оба
(7):
- агент 1 (3): `ardea-ibis`, `butorides-striata`, `chroicocephalus-serranus`
- агент 2 (2): `nannopterum-brasilianum`, `pelecanus-occidentalis`
- агент 3 (2): `plegadis-falcinellus`, `podilymbus-podiceps`

Сведение оттенков — карточки, где авторы жаловались на нехватку цвета: `coeligena-helianthea` (розовое брюхо →
можно `red`), `donacobius-atricapilla` и `myiothlypis-fulvicauda` (охристый → `rufous`), `columbina-buckleyi`
(лилово-розовый → `purple`). Лимит 3 цвета сохраняется: добавлять, только если новый цвет заметнее одного из
имеющихся.

## 4. Приметы: все карточки, пустые `marks` первыми

Пустые `marks` (87):
- агент 1 (30): `amazilia-tzacatl`, `anisognathus-lacrymosus`, `anisognathus-notabilis`, `atlapetes-crassus`, `atlapetes-fuscoolivaceus`, `atlapetes-pallidinucha`, `boissonneaua-jardini`, `boissonneaua-matthewsii`, `buthraupis-montana`, `capito-squamatus`, `catamblyrhynchus-diadema`, `catamenia-inornata`, `chionomesa-fimbriata`, `chroicocephalus-serranus`, `chrysomus-icterocephalus`, `chrysothlypis-salmoni`, `chrysuronia-oenone`, `cnemathraupis-eximia`, `cnemoscopus-rubrirostris`, `coeligena-bonapartei`, `coeligena-torquata`, `colibri-coruscans`, `colibri-cyanotus`, `columbina-buckleyi`, `columbina-talpacoti`, `conirostrum-sitticolor`, `cypseloides-cherriei`, `diglossa-albilatera`, `diglossa-sittoides`, `doliornis-remseni`
- агент 2 (28): `elanus-leucurus`, `entomodestes-coracinus`, `eubucco-bourcierii`, `euphonia-concinna`, `euphonia-laniirostris`, `euphonia-xanthogaster`, `galbalcyrhynchus-leucotis`, `gallinula-galeata`, `haplophaedia-lugens`, `heliodoxa-aurescens`, `hemitriccus-rufigularis`, `himantopus-mexicanus`, `iridosornis-rufivertex`, `klais-guimeti`, `lafresnaya-lafresnayi`, `leucophaeus-atricilla`, `megascops-roraimae`, `mesembrinibis-cayennensis`, `metallura-tyrianthina`, `monasa-flavirostris`, `myioborus-ornatus`, `notharchus-hyperrhynchus`, `nyctanassa-violacea`, `nyctibius-grandis`, `nycticorax-nycticorax`, `patagioenas-cayennensis`, `patagioenas-fasciata`, `pelecanus-occidentalis`
- агент 3 (29): `pharomachrus-auriceps`, `pharomachrus-pavoninus`, `pipreola-jucunda`, `pipreola-lubomirskii`, `piranga-olivacea`, `plegadis-falcinellus`, `podiceps-occipitalis`, `porphyriops-melanops`, `psarocolius-angustifrons`, `psophia-crepitans`, `pterophanes-cyanopterus`, `ramphocelus-carbo`, `ramphocelus-dimidiatus`, `sicalis-luteola`, `spatula-discors`, `spinus-psaltria`, `sporathraupis-cyanocephala`, `sporophila-corvina`, `sporophila-luctuosa`, `stilpnia-cyanicollis`, `streptoprocne-zonaris`, `sula-nebouxii`, `tangara-arthus`, `tangara-chrysotis`, `tangara-gyrola`, `turdus-ignobilis`, `uranomitra-franciae`, `urochroa-leucura`, `zenaida-auriculata`

Кандидаты `cap` (шапочка или капюшон) по `key_features`, 135:
- агент 1 (46): `aglaiocercus-coelestis`, `aglaiocercus-kingii`, `ampelioides-tschudii`, `anas-bahamensis`, `andigena-laminirostris`, `andigena-nigrirostris`, `anisognathus-notabilis`, `anthocephala-berlepschi`, `atlapetes-albofrenatus`, `atlapetes-crassus`, `atlapetes-leucopis`, `atlapetes-schistaceus`, `bangsia-edwardsi`, `boissonneaua-jardini`, `buthraupis-montana`, `butorides-striata`, `campephilus-gayaquilensis`, `cantorchilus-nigricapillus`, `capito-auratus`, `capito-aurovirens`, `capito-squamatus`, `celeus-spectabilis`, `chalcostigma-herrani`, `chamaeza-turdina`, `chlorospingus-flavigularis`, `chroicocephalus-serranus`, `chrysomus-icterocephalus`, `chrysuronia-oenone`, `cissopis-leverianus`, `cistothorus-apolinari`, `cistothorus-platensis`, `cnemarchus-erythropygius`, `cnemathraupis-eximia`, `cnemoscopus-rubrirostris`, `colaptes-punctigula`, `conirostrum-sitticolor`, `crypturellus-cinereus`, `cyanolyca-pulchra`, `cyanolyca-turcosa`, `doliornis-remseni`, `drymophila-caudata`, `dubusia-taeniata`, `dysithamnus-occidentalis`, `dysithamnus-puncticeps`, `elaenia-frantzii`, `elaenia-pallatangae`
- агент 2 (41): `elanus-leucurus`, `eubucco-bourcierii`, `euphonia-laniirostris`, `euphonia-xanthogaster`, `eurypyga-helias`, `fulica-americana`, `galbula-pastazae`, `glaucidium-jardinii`, `grallaria-ruficapilla`, `grallaricula-cucullata`, `grallaricula-nana`, `haematopus-palliatus`, `hemitriccus-rufigularis`, `henicorhina-leucophrys`, `henicorhina-leucosticta`, `iridosornis-rufivertex`, `klais-guimeti`, `kleinothraupis-atropileus`, `leptasthenura-andicola`, `leucophaeus-atricilla`, `liosceles-thoracicus`, `machaeropterus-deliciosus`, `malacoptila-fulvogularis`, `manacus-manacus`, `megarynchus-pitangua`, `melanerpes-pucherani`, `merganetta-armata`, `myiotriccus-ornatus`, `myiozetetes-cayanensis`, `myiozetetes-similis`, `notharchus-hyperrhynchus`, `nyctanassa-violacea`, `nycticorax-nycticorax`, `odontophorus-hyperythrus`, `odontorchilus-branickii`, `ortalis-erythroptera`, `oxypogon-guerinii`, `oxyura-jamaicensis`, `pachyramphus-cinnamomeus`, `pandion-haliaetus`, `pelecanus-occidentalis`
- агент 3 (48): `pharomachrus-auriceps`, `pharomachrus-pavoninus`, `piaya-cayana`, `picumnus-lafresnayi`, `pionus-chalcopterus`, `pipreola-jucunda`, `pitangus-sulphuratus`, `platyrinchus-flavigularis`, `podiceps-occipitalis`, `poecilotriccus-ruficeps`, `pogonotriccus-orbitalis`, `polioptila-plumbea`, `porphyriops-melanops`, `pseudocolopteryx-acutipennis`, `pteroglossus-castanotis`, `pyrilia-pulchra`, `pyrocephalus-rubinus`, `pyrrhura-melanura`, `saltator-atripennis`, `saucerottia-cyanifrons`, `semnornis-ramphastinus`, `serpophaga-cinerea`, `spatula-discors`, `spinus-spinescens`, `stilpnia-cyanicollis`, `stilpnia-heinei`, `stilpnia-larvata`, `stilpnia-vitriolina`, `sula-nebouxii`, `synallaxis-azarae`, `synallaxis-subpudica`, `tangara-chilensis`, `tangara-chrysotis`, `tangara-gyrola`, `tangara-mexicana`, `tangara-schrankii`, `tinamus-major`, `tityra-cayana`, `tolmomyias-traylori`, `trogon-ramonianus`, `trogon-viridis`, `tyrannulus-elatus`, `tyrannus-tyrannus`, `uranomitra-franciae`, `veniliornis-chocoensis`, `vireo-leucophrys`, `vireo-olivaceus`, `zimmerius-albigularis`

Кандидаты `wing_patch` (пятно на крыле) по `key_features`, 31:
- агент 1 (13): `amazona-farinosa`, `anas-andium`, `anas-bahamensis`, `anisognathus-notabilis`, `cacicus-cela`, `cacicus-chrysonotus`, `capito-auratus`, `capito-squamatus`, `cnemarchus-erythropygius`, `columbina-talpacoti`, `diglossa-albilatera`, `diglossa-lafresnayii`, `donacobius-atricapilla`
- агент 2 (4): `geotrygon-saphirina`, `hafferia-zeledoni`, `monasa-flavirostris`, `nyctiphrynus-rosenbergi`
- агент 3 (14): `pipreola-arcuata`, `polioptila-plumbea`, `pyrrhura-calliptera`, `pyrrhura-melanura`, `rallus-semiplumbeus`, `spatula-discors`, `spinus-psaltria`, `sporathraupis-cyanocephala`, `sporophila-corvina`, `sporophila-luctuosa`, `sporophila-telasco`, `stilpnia-cyanicollis`, `tachyphonus-rufus`, `thraupis-episcopus`

Кандидаты `bright_bill` (яркий клюв) по `key_features`, 69:
- агент 1 (19): `amazilia-tzacatl`, `anas-bahamensis`, `anas-georgica`, `andigena-laminirostris`, `aulacorhynchus-haematopygus`, `campephilus-gayaquilensis`, `camptostoma-obsoletum`, `charadrius-semipalmatus`, `chionomesa-fimbriata`, `chlorophonia-flavirostris`, `chlorornis-riefferii`, `chrysuronia-goudoti`, `chrysuronia-oenone`, `cichlopsis-leucogenys`, `cnemoscopus-rubrirostris`, `coccyzus-americanus`, `columbina-cruziana`, `crypturellus-cinereus`, `egretta-thula`
- агент 2 (20): `entomodestes-coracinus`, `fulica-ardesiaca`, `gallinula-galeata`, `gymnoderus-foetidus`, `hapaloptila-castanea`, `heliangelus-clarisse`, `heliangelus-exortis`, `icterus-chrysater`, `jacana-jacana`, `larosterna-inca`, `merganetta-armata`, `mesembrinibis-cayennensis`, `mitu-salvini`, `monasa-flavirostris`, `monasa-nigrifrons`, `nannopterum-brasilianum`, `nothocrax-urumutum`, `oxyura-jamaicensis`, `patagioenas-fasciata`, `phaethon-aethereus`
- агент 3 (30): `pharomachrus-auriceps`, `pharomachrus-pavoninus`, `phimosus-infuscatus`, `pionus-chalcopterus`, `pipreola-arcuata`, `pipreola-chlorolepidota`, `pipreola-jucunda`, `pipreola-lubomirskii`, `platyrinchus-flavigularis`, `plegadis-falcinellus`, `podiceps-occipitalis`, `porphyriops-melanops`, `pteroglossus-castanotis`, `pteroglossus-pluricinctus`, `ramphastos-ambiguus`, `ramphastos-tucanus`, `ramphocelus-carbo`, `ramphocelus-dimidiatus`, `ramphocelus-nigrogularis`, `rufirallus-fasciatus`, `saucerottia-cyanifrons`, `selenidera-reinwardtii`, `semnornis-ramphastinus`, `sula-granti`, `tityra-cayana`, `trogon-comptus`, `trogon-viridis`, `turdus-fuscater`, `uranomitra-franciae`, `vanellus-chilensis`

`plain` вместе с кандидатом на `cap`/`wing_patch` — решить, что верно (9): `crypturellus-cinereus`, `diglossa-lafresnayii`, `fulica-americana`, `pachyramphus-cinnamomeus`, `pseudocolopteryx-acutipennis`, `saucerottia-cyanifrons`, `serpophaga-cinerea`, `tachyphonus-rufus`, `thraupis-episcopus`.

## Объём

| Правило | Карточек проверить | Агент 1 | Агент 2 | Агент 3 |
|---|---|---|---|---|
| Размер: готовые предложения | 87 | 21 | 34 | 32 |
| Наряд октября (мигранты + сезонные) | 38 | 12 | 10 | 16 |
| `feeder`: снять | 9 | 2 | 0 | 7 |
| `feeder`: добавить (кандидаты) | 22 | 10 | 9 | 3 |
| Пустые `marks` | 87 | 30 | 28 | 29 |
| Новые приметы (все карточки) | 467 | 156 | 156 | 155 |

Оценка: все карточки просматриваются из-за новых примет (~1 мин на карточку по `key_features`), изменения ожидаются
примерно в 250–300 карточках: ~87 по размеру, ~150–200 по новым приметам, ~30 по нарядам, ~30 по `feeder`.
