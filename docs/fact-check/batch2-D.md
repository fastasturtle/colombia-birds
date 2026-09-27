# Факт-чек: партия 2, список D (танагры, атлапеты, древесницы, трупиалы, хищные, совы, ибис, кваква, пастушок)

Карточки написаны 27.09.2026 по data/species, data/texts (Wikipedia en/es/ru), data/site_species.json, data/sites.json и полевым знаниям.
Ниже то, что стоит проверить. Формат: `slug` — что проверить.

## Данные и таксономия (важно)

- `atlapetes-tricolor` — **таксономия и тексты**: ACO «Atlapetes tricolor» сопоставлен с eBird tribrf2 (en «Golden-crowned Brushfinch», ru «трёхцветная атлапета» со строчной буквы). В Колумбии живёт форма crassus (у IOC отдельный вид Choco Brushfinch, A. crassus), а тексты Wikipedia (en/es/ru) и высоты в данных (1 525–3 050 м) относятся к перуанскому A. tricolor. Проверить, какой вид eBird/Clements 2025 имеет в виду под tribrf2, поправить маппинг/тексты. В карточке окраска описана для crassus по памяти (золотисто-охристое темя, чёрное лицо, жёлтый низ), высоты «примерно 1 000–1 900 м» взяты по высотам точек маршрута, а не из источника.
- `pulsatrix-melanota` — в data/species масса 82 г, по Wikipedia 590–1 250 г (в среднем 873 г). Ошибка BIRDBASE/маппинга.
- `pulsatrix-melanota` — русское имя «Перуанская неясыть» (eBird) при роде Pulsatrix; оставлено как в индексе.
- `ramphocelus-nigrogularis` — русское имя «Масковый сереброклюв» (eBird); оставлено как в индексе.
- `atlapetes-tricolor` — ru-имя в индексе со строчной буквы («трёхцветная атлапета»), похоже на опечатку источника.
- `cnemathraupis-eximia` — единственная «возможная» точка — Чингаса (optional); по маршруту вид маловероятен. Высоты в данных 2 700–3 400 м, в ru-Wikipedia 2 000–3 800 м.
- `megascops-roraimae` — BIRDBASE без данных по МСОП (birdbase_2024: null), range_restricted null.

## Голос (формулировки по памяти, сверить с xeno-canto)

- `tangara-parzudakii`, `tangara-chrysotis`, `chlorochrysa-calliparaea` — голоса описаны обобщённо («цит», «ци»).
- `diglossa-glauca` — «цип» и щебечущая трель: по памяти.
- `cnemathraupis-eximia` — голос почти не знаю, описан обобщённо.
- `kleinothraupis-atropileus` — «трескучее щебетание, дуэты».
- `chlorophonia-flavirostris` — «мягкие жалобные посвисты».
- `atlapetes-fuscoolivaceus`, `atlapetes-tricolor`, `atlapetes-albofrenatus` — голоса описаны обобщённо.
- `leistes-bellicosus` — песня «хрипловатая трель с жужжащим окончанием», позыв «чек».
- `ictinia-plumbea` — свист из 2–3 слогов с понижением (ru-Wikipedia).
- `glaucidium-nubicola` — «ровная серия глухих ху»: у вида, возможно, ноты сдвоены — проверить.
- `glaucidium-jardinii` — «быстрые пу-пу-пу, иногда с трелью в начале».
- `megascops-roraimae` — «долгая ровная трель, чуть поднимается и резко обрывается»; отличие песни от Tropical Screech-Owl («короткая трель с 1–2 ударными нотами в конце»).
- `micrastur-gilvicollis` — «короткие двусложные лающие крики на рассвете».
- `mesembrinibis-cayennensis` — «раскатистое ко-ко-ко».
- `nyctanassa-violacea` — «хриплое квок».
- `laterallus-exilis` — «звонкие кик-кик-кик, иногда сухая трель».

## Признаки и отличия

- `tangara-chrysotis` — рисунок темени (зеленовато-золотое с тёмной центральной полосой) и «тонкие чёрные черты у глаза и под клювом»: по памяти.
- `tangara-parzudakii` — «лицо оранжевое, без густо-красного» у lunigera (по es-Wikipedia); что на Ла-Нутрии/Ла-Планаде именно lunigera, а в Уиле и на Трамплине — номинативная форма.
- `diglossa-glauca` — «лицо темнее, но чёткой маски нет»; отличие от Bluish Flowerpiercer «обычно держится выше».
- `chlorochrysa-calliparaea` — оранжевое пятнышко на темени, оранжево-рыжая поясница, синеватое брюхо (по es-Wikipedia), чёрное горло только у самца.
- `chlorornis-riefferii` — отличие от Orange-eared Tanager («вдвое мельче»): виды пересекаются по высоте только на Трамплине.
- `bangsia-rothschildi` — «подолгу сидит неподвижно»; голос не описан.
- `cnemathraupis-eximia` — форма chloronota на юге Колумбии (по ru-Wikipedia); синие поясница и плечо.
- `catamblyrhynchus-diadema` — «за золотым лбом тёмная полоса» и серая спина.
- `kleinothraupis-atropileus` — отличие от Black-crested Warbler; что в Колумбии вид во всех трёх Кордильерах (es-Wikipedia).
- `chlorophonia-flavirostris` — изолированная популяция в Панаме; «особенно омела» — по памяти; «одна из самых маленьких не-колибри маршрута».
- `atlapetes-fuscoolivaceus` — отличие от White-naped Brushfinch (в Уиле форма с жёлтым горлом и белой полосой на темени).
- `atlapetes-albofrenatus` — жёлтое ли горло у формы Восточной Кордильеры (en-Wikipedia обрезана на описании горла; es: подбородок белый, низ жёлтый).
- `cardellina-canadensis` — высоты зимовки в Колумбии «примерно от 1 000 до 2 500 м и выше».
- `setophaga-cerulea` — сроки прилёта (конец сентября – начало октября); отличие осенней Blackpoll Warbler.
- `hypopyrrhus-pyrohypogaster` — встречается ли на Трамплине птиц (Путумайо, восточный склон) — GBIF даёт «возможно», проверить, не ошибки ли определения. Стаи «до 50 особей» (ru-Wikipedia) в карточку не взяты.
- `leistes-bellicosus` — что в Колумбии вид только в Нариньо (юго-запад); не упомянута ли более поздняя экспансия.
- `ictinia-plumbea` — часть колумбийских птиц мигрирует (es-Wikipedia): присутствуют ли они в октябре в Путумайо и на тихоокеанском побережье.
- `pulsatrix-melanota` — цвет глаз (тёмные красновато-карие по en-Wikipedia); ареал в Колумбии («от центральной Колумбии» en vs «возможно юго-восток» es).
- `glaucidium-nubicola` — «темя почти без крапин» и «спина без пятен» как отличие от Andean Pygmy-Owl; отличие Central American Pygmy-Owl «голова серая».
- `glaucidium-jardinii` — отличие Ferruginous Pygmy-Owl «темя в штрихах, а не в точках».
- `megascops-roraimae` — описание оперения обобщённое; наличие двух морф у napensis.
- `micrastur-gilvicollis` — отличия от Barred и Slaty-backed Forest-Falcon (число полос на хвосте).
- `mesembrinibis-cayennensis` — цвет голой кожи лица и клюва; встречается ли на Марагриколе (тихоокеанское побережье), в данных «возможно».
- `nyctanassa-violacea` — отличие молодых от молодой Black-crowned Night Heron; Boat-billed Heron на тихоокеанском побережье Нариньо.
- `laterallus-exilis` — цвет клюва (зеленоватый с тёмным концом, по es-Wikipedia).
