# Факт-чек: партия 4, список 8 (стрижи, колибри, цапли, ибисы, пастушки, котинга, манакины)

Карточки написаны 27.09.2026 по data/species, data/texts (Wikipedia en/es/ru) и полевым знаниям агента.
Ниже то, что стоит проверить по открытым источникам перед публикацией. Формат: `slug — что проверить`.

## Общее

- Голоса по памяти или обобщённо (в выдержках Wikipedia голос не описан или обрезан): chalybura-buffonii, ocreatus-underwoodii, coeligena-coeligena, polyerata-amabilis, polyerata-rosenbergi, threnetes-leucurus, heliodoxa-schreibersii, glaucis-hirsutus (позыв «сип»), phaethornis-griseogularis, doryfera-johannae, egretta-tricolor, egretta-caerulea, eudocimus-ruber, eudocimus-albus, porphyrio-martinica, aramus-guarauna («кррр-а-оу»), aramides-axillaris, aramides-cajaneus (дуэт), mustelirallus-erythrops, pipreola-riefferii, masius-chrysopterus («нурт»), machaeropterus-striolatus.
- `feeder` поставлен по общему знанию о поведении вида на кормушках лоджей Анд, без проверки конкретных лоджей маршрута: florisuga-mellivora, chalybura-buffonii, ocreatus-underwoodii, coeligena-coeligena, boissonneaua-flavescens. Не поставлен, но возможен: phaethornis-syrmatophorus, campylopterus-largipennis, polyerata-amabilis, heliodoxa-schreibersii, doryfera-johannae.
- Длина тела для `size` взята из Wikipedia; у aramides-cajaneus (≈36–40 см по памяти, в выдержке длины нет) поставлен `crow`, у A. wolfi (33–36) и A. axillaris (29–33) — `pigeon`. У eudocimus-ruber (55–63 см) и chaetura-brachyura (10,5 см) пограничные классы: `larger` и `sparrow`.

## По видам

- chaetura-brachyura — отличия от C. cinereiventris и C. spinicaudus: по Wikipedia en (нет контраста поясницы и хвоста); узкая полоса на пояснице у spinicaudus — по памяти.
- florisuga-mellivora — отличие самки от самки thalurania-colombica и от heliothryx-barroti по памяти.
- campylopterus-largipennis — подвид aequatorialis «с серыми концами крайних рулевых» по Wikipedia en (сказано про obscurus «с aequatorialis», формулировка двусмысленна). Розовое подклювье — у номинативного подвида; проверить для aequatorialis.
- chalybura-buffonii — подвид в Уиле (micans или buffonii?) и в Чикаке: по Wikipedia micans «в дальней верхней Магдалене», buffonii — «верхняя и средняя Магдалена». В карточке «вероятно, micans». Цвет подхвостья и груди самца по номинативному описанию.
- phaethornis-syrmatophorus — на Трамплине птиц (восточный склон, Путумайо) предположен columbianus. Отличие от P. guy по памяти.
- ocreatus-underwoodii — самки melanantherus (Нариньо) «без крапин» по Wikipedia; на Ла-Планаде именно этот подвид? Отличие от chaetocercus-mulsant по памяти; голос по памяти.
- chlorostilbon-gibsoni — отличие от C. poortmani («хвост короткий, зелёный, клюв тёмный») по памяти. Как gibsoni попадает в Чикаке (облачный лес 2 000–2 700 м) — вероятно, записи из долины в радиусе 7 км.
- coeligena-coeligena — какой подвид на Трамплине птиц (obscura или columbiana) — предположение. Отличие от doryfera-ludovicae по карточке ludovicae.
- polyerata-amabilis / polyerata-rosenbergi — отличия самцов (блестящее темя у amabilis, размер и положение синего пятна) по памяти и es-Wikipedia; es-описание rosenbergi: «хвост… белый снизу» — в карточке «подхвостье светлое», проверить. Подклювье rosenbergi не упомянуто.
- threnetes-leucurus — «бледно-охристые крайние рулевые» у cervinicauda выведены из названия подвида и общего знания; Wikipedia говорит лишь о «разных оттенках» хвоста. Отличие от phaethornis-hispidus по памяти.
- phaethornis-griseogularis — отличие от P. ruber («горло рыжее, без серого») по памяти; ruber не на маршруте по данным.
- heliodoxa-schreibersii — голос не описан.
- doryfera-johannae — голос: выдержка Wikipedia обрезана («While foraging it makes …»).
- boissonneaua-flavescens — `colors: [green, yellow]` за «охристый» хвост: пограничный выбор (buff нет в словаре). Отличие от coeligena-lutetiae по её карточке.
- egretta-tricolor — отличие от egretta-rufescens (тёмная морфа: рыжие голова и шея, розовый клюв с чёрным концом) по памяти. `tone: bright` из-за контраста белого брюха — пограничный выбор.
- eudocimus-ruber — ареал в Колумбии («в основном льяносы Ориноко и карибское побережье») по памяти; встречи в Путумайо (Пуэрто-Асис, Плайя-Рика, Эль-Эскондите) названы «по-видимому, необычными» — проверить по eBird, не ошибка ли GBIF.
- eudocimus-albus — «в центральной Венесуэле скрещивается с алым» по Wikipedia en; отметки в Эль-Эскондите (Путумайо) проверить так же, как у алого.
- egretta-caerulea — «в Колумбии есть и оседлые птицы, и зимующие мигранты» по статусу ACO «Migratorio Boreal - Residente».
- porphyrio-martinica — голос по памяти.
- aramides-wolfi — отличие от A. cajaneus (цвет ног, серая шея) по Wikipedia; живёт ли cajaneus на тихоокеанской низменности Нариньо — не проверено.
- aramus-guarauna — «кррр-а-оу» и активность ночью по Wikipedia en (частично) и памяти.
- aramides-axillaris — голос по памяти.
- mustelirallus-erythrops — отличие от pardirallus-nigricans по памяти; окраска клюва («красный у основания, жёлто-зелёный к концу») — Wikipedia говорит лишь «red and yellow bill».
- aramides-cajaneus — длина тела и голос по памяти.
- pipreola-riefferii — какой подвид в Уиле и на Трамплине (riefferii или confusa?); голос («очень высокий писк») по памяти.
- masius-chrysopterus — описание тока у бревна по памяти; подвид в Уиле (pax или chrysopterus) не указан.
- lepidothrix-coronata — «самки со светлым желтоватым брюхом» по памяти; отличие самки Pseudopipra pipra («серая голова») по памяти.
- machaeropterus-striolatus — голос и поведение на току по памяти.

## Data issues

- porphyrio-martinica — в data/species верхняя граница высот 4 080 м (ACO); для малой султанки это выглядит как залётная запись. Не упоминалось как норма в тексте.
- mustelirallus-erythrops — русское имя «Желтоклювый туру» (eBird) не отражает двухцветный красно-жёлтый клюв; оставлено как есть, стоит сверить с IOC-ru.
- lepidothrix-coronata — нет русского имени в data/species_index.json (`ru: null`); в тексте только английское.
- chlorostilbon-gibsoni — habitat_aco «Forest», хотя вид сухих кустарников и садов (habitats BIRDBASE: woodland, savanna, agricultural).
- eudocimus-ruber, eudocimus-albus — «maybe» в Пуэрто-Асисе / Плайя-Рике / Эль-Эскондите (Путумайо) по GBIF; для этих видов в амазонском предгорье подозрительно, проверить исходные записи.
- boissonneaua-flavescens — «maybe» в Эль-Энканто (1 350 м) при высотах вида 2 000–3 500 м: вероятно, записи из радиуса 7 км выше по склону.
- chlorostilbon-mellisugus (не из партии, замечено попутно) — в индексе высоты [750, 2600], для равнинного Blue-tailed Emerald странно; возможна путаница с раньше включавшимися в него горными формами.
