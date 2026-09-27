# Факт-чек: партия 5, список 3 (муравьеловки, печниковые, древолазы)

Карточки написаны 27.09.2026 по data/species, data/texts (Wikipedia en) и полевым знаниям агента.
Ниже то, что стоит проверить по открытым источникам перед публикацией. Формат: `slug — что проверить`.

## Общее

- Голоса пересказаны по разделу Vocalization Wikipedia (en); транскрипции кириллицей условные.
- Размерные классы на границе: Western Fire-eye (16–18 см) — `thrush`, Rufous Spinetail (16–18, длинный хвост) и Rufous-tailed Foliage-gleaner (16–17) — `sparrow`; White-flanked Antwren (9–10,5) — `hummingbird`, как Pacific Antwren в партии 4; Ochre-breasted Antpitta (~10 см) — `sparrow`, как Slate-crowned Antpitta; Cinnamon-throated Woodcreeper (22,5–27) — `thrush`. Проверить единообразие.
- `feeder` не ставился никому. Undulated и Yellow-breasted Antpitta ходят на кормушки с червями в других заповедниках (по Wikipedia); есть ли кормушки для них на Ла-Планаде или в Обсерватории колибри — не проверялось.

## Карточки

- anabacerthia-ruficaudata — какой подвид в Путумайо (flavipectus или subflavescens) не указан; «на тех же высотах на Исла-Эскондиде встречается Montane Foliage-gleaner» — по data/site_species.json (оба «возможно»), реальное перекрытие высот не проверено; отличие от Montane («спина бурая, без жёлтого тона») по памяти и по карточке anabacerthia-striaticollis.
- thamnophilus-unicolor — высоты 1 200–2 200 м по Wikipedia (ACO 1 000–2 300); голос по Wikipedia.
- pyriglena-maura — подвид castanoptera в Хуиле и Путумайо по Wikipedia (восточный склон Центральных и оба склона Восточных Анд); высоты 500–2 500 м по Wikipedia (ACO 300–2 200). Размерный класс — см. Общее.
- xiphorhynchus-triangularis — «горло в тёмной чешуе» против «в точках» у Spotted Woodcreeper взято из карточки xiphorhynchus-erythropygius; различимость в поле проверить.
- thamnophilus-tenuepunctatus — отличие от Bar-crested (шапка и хохол самца в полосах; самки почти одинаковы) по карточке thamnophilus-multistriatus; «живёт в долине Магдалены» — по точкам маршрута (Чикаке, Эль-Энканто, Ла-Дримофила), а не по ареалу. Cymbilaimus: «держится выше, в лианах» — по памяти.
- xiphorhynchus-ocellatus — подвид napensis «нижние склоны Анд южной Колумбии» по Wikipedia; высота Исла-Эскондиды (650–1 600 м) выше обычных 500 м, Wikipedia даёт до 1 800 м в Андах.
- dendrexetastes-rufigula — отличие от Plain-brown по памяти (клюв тёмный и тоньше).
- synallaxis-albescens — «в районе Чикаке» по GBIF; Чикаке 2 000–2 700 м, вид в Колумбии до 1 800 м (Wikipedia), ACO до 1 500. Сформулировано осторожно.
- hypocnemis-peruviana — отличия согласованы с карточками myrmoborus-myotherinus и hylophylax-naevius.
- dysithamnus-mentalis — подвиды semicinereus (Хуила, Восточные Анды до Какеты) и napensis (крайний юг Колумбии, восточный склон) по Wikipedia; к какому относятся птицы Исла-Эскондиды — не проверено.
- cercomacroides-serva — **нет data/texts**: карточка написана по data/species, сравнениям в карточках cercomacroides-nigrescens, -fuscicauda, akletos-melanoceps и памяти. Проверить: окраску самки (оливково-бурый верх, рыже-охристый низ), белые точки/каймы на кроющих самца, голос (песня и дуэт описаны расплывчато), отличие от Blackish Antbird («держится внутри леса на склонах, а не в прибрежных зарослях»).
- gymnopithys-leucaspis — ок, по Wikipedia (подвид castaneus в Путумайо). Русское имя см. Data issues.
- thamnomanes-ardesiacus — Wikipedia: в Колумбии только до 400 м; Исла-Эскондида 650–1 600 м, ACO до 1 050. «У верхней границы высот» — осторожная формулировка; «часто первой подаёт тревогу, и стая идёт за ней» — полевое знание о роде Thamnomanes, проверить для этого вида. Отличие самки от Cinereous Antshrike по Wikipedia, различимость в поле сомнительна.
- synallaxis-unirufa — голос номинативного подвида по Wikipedia; отличие от Sharpe's (Sepia-brown) Wren по Wikipedia.
- grallaria-squamigera — в программе тура данных нет (только Чингаса и Обсерватория колибри, обе optional). Отличие от Giant Antpitta по Wikipedia; упоминание «очень редка» — по памяти.
- hafferia-fortis — Wikipedia: в Колумбии до 300 м, ACO до 900 (крайн. 1 200); Исла-Эскондида 650–1 600 м — в тексте «до нескольких сотен метров», проверить реальность встречи на Исла-Эскондиде.
- thripadectes-ignobilis — высоты: Wikipedia 500–2 500 в Колумбии, ACO 700–1 700; в тексте 700–1 700. «Самый тёмный из лесовиков, клюв короче» — по Wikipedia.
- dendrocincla-fuliginosa — подвиды в Путумайо (neglecta или phaeochroa) не названы; ridgwayi на тихоокеанской стороне по Wikipedia. Отличие от White-chinned («почти только у колонн муравьёв») по памяти.
- formicarius-nigricapillus — русского имени нет; в тексте указано ACO-имя Black-headed Antthrush. Отличие от Black-faced Antthrush («живёт восточнее Анд и в долинах севера») — по памяти, проверить ареал F. analis в Колумбии.
- myrmotherula-ignota — «горло жёлтое» у Moustached против белого у Pygmy — вывод из Wikipedia (у ignota низ жёлтый, у brachyura горло белое), для подвида obscura проверить. Платформы в кронах на Исла-Эскондиде — из data/sites.json.
- myrmeciza-longipes — см. Data issues про Чикаке; подвид boucardi по Wikipedia.
- thripadectes-virgaticeps — подвид sclateri на Ла-Планаде по Wikipedia (Западные Анды от Валье до Нариньо); отличие от Flammulated Treehunter («живёт выше») по Wikipedia (2 200–3 500 м, локально до 700 м на западе Колумбии).
- sclateria-naevia — ок, по Wikipedia; «ноги розоватые» — по памяти.
- scytalopus-atratus — какой подвид в Хуиле (atratus или confusus) не указан; голос описан обобщённо («быстрая серия одинаковых звонких нот») — проверить по xeno-canto для Хуилы. Отличие от Blackish Tapaculo «живёт выше» — по карточке scytalopus-latrans.
- grallaria-nuchalis — какой подвид на Трамплине птиц (Путумайо) и у Ла-Кочи — Wikipedia не говорит (номинативный «может заходить до Нариньо»); проверить, есть ли вид вообще на восточном склоне в Путумайо.
- pseudocolaptes-johnsoni — «окончательно признан видом в 2022» по Wikipedia (AOS/Clements).
- grallaria-flavotincta — «на некоторых кормушках с червями в Эквадоре стала ручной»: Wikipedia говорит о кормушках без указания страны, страна — по памяти (Пас-де-лас-Авес и др.), проверить.
- myrmotherula-axillaris — отличие от Long-winged Antwren и Gray Antwren по Wikipedia; оба не на маршруте.
- grallaricula-flavirostris — подвид mindoensis на западном склоне Нариньо по Wikipedia; голос почти не описан.
- pithys-albifrons — ок, по Wikipedia.
- dendroma-rufa — подвид riveti по Wikipedia; высоты см. Data issues.

## Data issues

- thamnophilus-tenuepunctatus — data/species: `iucn.aco_2022 = VU`; по IUCN вид, насколько известно, LC. Возможно, ошибка маппинга статуса ACO или национальный статус. В карточку не вынесено.
- pyriglena-maura — `names.en_aco = "East Amazonian Fire-eye"` (это P. leuconota), тогда как вид в Колумбии — Western Fire-eye (P. maura castanoptera). Маппинг ACO → eBird, видимо, верный, но английское ACO-имя вводит в заблуждение.
- myrmeciza-longipes — «возможно» в Чикаке (2 000–2 700 м) при высотах вида 0–700 (ACO, крайн. 1 750) и до 1 800 по Wikipedia. Вероятно, в 7-км радиус GBIF попадают записи из долины ниже парка. Аналогично synallaxis-albescens в Чикаке.
- hafferia-fortis, thamnomanes-ardesiacus — «возможно» на Исла-Эскондиде (650–1 600 м) при максимуме по Wikipedia 300 и 400 м в Колумбии; вероятно, записи из низин в радиусе локации.
- dendroma-rufa — ACO/BIRDBASE: elevation min 0 м; для андских популяций Wikipedia даёт 600–2 000 м (0 м — только для юго-восточной Бразилии).
- gymnopithys-leucaspis — русское имя «Белобрюхая гологлазка» для White-cheeked Antbird (скорее соответствует старому объединённому Bicolored Antbird); проверить источник eBird ru.
- formicarius-nigricapillus, pseudocolaptes-johnsoni — `names.ru = null`.
- cercomacroides-serva — нет data/texts (Wikipedia не скачана).
