# Факт-чек: партия 5, список 7 (хищные птицы, совы, чайковые и зуёк)

28 карточек написаны 27.09.2026 по data/species, data/texts (Wikipedia en/es/ru), data/site_species.json, data/itinerary.json, data/study_lists.json и полевым знаниям агента.
Ниже то, что стоит проверить перед публикацией. Формат: `slug — что проверить`.

## Общее

- Голоса по памяти или с пометкой «(проверить)» прямо в поле voice: leptodon-cayanensis (серии криков), geranospiza-caerulescens, buteogallus-anthracinus, asio-clamator, buteo-nitidus, buteo-brachyurus, buteo-albonotatus, harpagus-bidentatus, pseudastur-albicollis, asio-stygius, microspizias-superciliosus, buteo-albigula. Пометки «(проверить)» / «(to be verified)» убрать после факт-чека.
- Размерные классы на границе: megascops-ingens (25–28 см) — `pigeon`, хотя M. choliba — `thrush`; caracara-plancus (50–65 см) и buteogallus-urubitinga (56–64 см) — `larger`; asio-flammeus (34–43 см), gelochelidon-nilotica (33–42 см) и lophostrix-cristata (38–43 см) — `crow`; falco-columbarius (24–33 см) — `pigeon`, falco-rufigularis (23–30 см) — `thrush` (как F. sparverius); microspizias-superciliosus — `thrush`.
- Длины тела для классов взяты из Wikipedia; для buteo-nitidus en даёт 46–61 см, ru — 38–46 см (в тексте «около 40–46 см»).
- Пустой `marks: []` у megascops-ingens, leptodon-cayanensis, buteo-albonotatus: полосатый хвост в словаре не выражается.

## По видам

- megascops-ingens — голос («ровная серия, слегка ускоряется») по памяти; что на тихоокеанском склоне Нариньо именно colombianus, а на восточном склоне юга — номинативный подвид (по Wikipedia); карие глаза у обоих подвидов (Wikipedia: «honey brown» у номинативного).
- leptodon-cayanensis — «длинные серии криков» по памяти; отличие от C. uncinatus («глаз светлый») по памяти.
- geranospiza-caerulescens — какой подвид на тихоокеанском побережье (balzarensis?) не указан; «глаза красные», «белый серп на маховых снизу» по памяти; отличие от B. schistaceus («глаза светлые») проверить — возможно, жёлто-оранжевые.
- micrastur-ruficollis — голос («одиночный лающий крик») и «следует за муравьями» по памяти.
- asio-flammeus — подвид bogotensis в Андах и его присутствие в Нариньо (Ла-Коча); голос у гнезда из Wikipedia en («toot-toot»).
- spizaetus-tyrannus — длина «60–70 см» по памяти (data/texts без размеров в выдержке); голос по памяти; «хохол белый у основания».
- caracara-plancus — «расселяется в Путумайо с расчисткой леса» по памяти; «запрокидывает голову» при крике — по памяти.
- buteogallus-anthracinus — что subtilis (Mangrove Black Hawk) — форма тихоокеанского побережья Колумбии; «светлое пятнышко у основания крайних маховых»; голос.
- asio-clamator — «регулярно отмечают на Боготской саванне, 2 600 м» — по GBIF (maybe в Ботаническом саду и Ла-Флориде), при высотах в data 0–1 400 м; глаза «тёмные, коричневые» (Wikipedia en: cinnamon).
- falco-columbarius — «прилетает с октября» и высоты до 3 000 м по data.
- buteo-nitidus — голос, «глаза тёмные» по памяти.
- buteo-brachyurus — голос по памяти; «изредка выше 1 800 м» по data (max_extreme 2 500).
- buteo-albonotatus — голос по памяти; распространение до 3 000 м по data.
- harpagus-bidentatus — подвиды: номинативный к востоку от Анд, fasciatus на тихоокеанском склоне — проверить границу для Путумайо; голос по памяти.
- lophostrix-cristata — окраска лицевого диска (тёмно-бурый/каштановый) и цвет глаз по подвидам не указаны сознательно; проверить отличие от P. perspicillata.
- falco-rufigularis — подвид petoensis к западу от Анд (Wikipedia, выдержка обрезана).
- buteogallus-urubitinga — «разоряет колонии гоацинов» по Wikipedia en.
- pseudastur-albicollis — голос; какой подвид в Путумайо (номинативный по Wikipedia: «Northern Colombia and central Venezuela to Brazil» — формулировка неоднозначна для юго-востока Колумбии); отличие от L. melanops (оранжевая восковица, штрихи на темени) по памяти, проверить, есть ли L. melanops в Путумайо.
- asio-stygius — голос; «регулярно находят днём в парках Боготы» по памяти и GBIF.
- microspizias-superciliosus — длина «20–27 см» по памяти (es даёт 28–32 см, похоже на ошибку); цвет глаз; отличие от M. collaris по памяти.
- geranoaetus-albicaudatus — «слетается к пожарам» по памяти; высоты по data.
- cathartes-burrovianus — «светлое поле сверху на крыле» согласовано с карточкой cathartes-melambrotus; см. «Проблемы данных».
- buteo-albigula — голос по памяти; высоты 1 700–3 500 м по Wikipedia (data: 150–3 500).
- thalasseus-sandvicensis — что американские птицы — acuflavidus (Cabot's Tern) и что Clements 2025 держит их в составе T. sandvicensis; жёлтоклювые «Cayenne» не упомянуты.
- gelochelidon-nilotica — «зимой добавляются северные птицы» по Wikipedia en (общая фраза про миграции).
- leucophaeus-pipixcan — отличие от C. serranus по памяти; голос по памяти; «пролёт в октябре».
- sterna-hirundo — «залётные птицы в горах» — по data (elev до 4 000 м); голос по памяти.
- charadrius-vociferus — присутствие осёдлого peruvianus на юго-западе Колумбии — предположение; «кричит и ночью» по памяти.

## Проблемы данных

- cathartes-burrovianus — в data/site_species.json «maybe» на Ла-Флориде (2 540 м) при высотах вида 0–1 100 м; вероятно, ошибка определения (C. aura) или координат. В карточке Ла-Флорида не упомянута. Там же в data/species `elevation_m.max_extreme` (1 000) меньше `max` (1 100).
- asio-clamator — «maybe» в Ботаническом саду Боготы и на Ла-Флориде (2 560 м) при высотах 0–1 400 м (max_extreme 2 000); вероятно, реальное расселение, но проверить.
- geranoaetus-albicaudatus — «maybe» на Ла-Флориде (2 550 м) при max_extreme 2 400 м.
- asio-flammeus, caracara-plancus, cathartes-burrovianus, asio-stygius, buteogallus-anthracinus — `colombia.habitat_aco` выглядит странно (Forest у болотной совы и каракары, Grassland у черноватой совы и чёрного крабоеда); в карточках не использовалось.
- buteo-albonotatus — русское имя «Болотный канюк» (eBird/ru-Wikipedia) не отражает биологию вида; оставлено как в индексе.
- megascops-ingens — ru-Wikipedia называет вид «Совка Сальвина», индекс — «Бурая совка» (eBird); оставлено по индексу.
