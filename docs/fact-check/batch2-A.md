# Факт-чек: партия 2, список A (колибри, трогоны, момоты, пуховки, якамары)

Карточки написаны 27.09.2026 по data/species, data/texts (Wikipedia en) и полевым знаниям агента.
Ниже то, что стоит проверить по открытым источникам перед публикацией. Формат: `slug — что проверить`.

## Общее

- Кормушки (`feeder` в `layer`) поставлены только saucerottia-cyanifrons (кормушки Эль-Энканто/Чикаке — по общему знанию, что вид обычен на кормушках Колумбии) и coeligena-bonapartei (Чикаке, по content/groups/swifts-hummingbirds.md). Проверить. Не поставлены, но возможны: heliangelus-amethysticollis и lafresnaya-lafresnayi (кормушки Обсерватории колибри — точка вне программы), heliodoxa-leadbeateri, anthocephala-berlepschi, chaetocercus-heliodor (кормушки/сады Эль-Энканто), chrysuronia-oenone, thalurania-furcata (Дискосура, Исла-Эскондида), doryfera-ludovicae (Авес-и-Флорес).
- Голоса heliodoxa-aurescens, doryfera-ludovicae, eutoxeres-condamini и pharomachrus-antisianus в выдержках Wikipedia не описаны; в карточках дана обобщённая формулировка, проверить.

## По видам

- chaetocercus-heliodor — difficulty=hard (эльфы, самки). Карточка chaetocercus-mulsant (партия 1) пишет про heliodor «брюхо тёмное, без белого», а Wikipedia — «white spots on the flanks»; в новой карточке упомянуты белые пятна на боках, согласовать формулировку в mulsant.
- saucerottia-cyanifrons — `marks: [plain]` при синей шапочке (README допускает мелкие метки на голове); отличие от S. saucerottei («темя зелёное») по памяти.
- heliangelus-amethysticollis — таксономия: en-статья Wikipedia описывает вид в узком объёме IOC (Боливия, Эквадор, Перу), колумбийские птицы — форма clarisse (Longuemare's Sunangel), в Clements входящая в H. amethysticollis. Проверить окраску clarisse: «светлая полоса под горлом» (охристая или беловатая?), «самка с рыжеватым горлом в крапинах» взято у номинативного подвида. Посещение кормушек Обсерватории колибри — проверить.
- ramphomicron-microrhynchum — «в сезон дождей поднимается выше» по Wikipedia. Отличие от chalcostigma-herrani добавлено по карточке herrani.
- heliodoxa-leadbeateri — подвид в Уиле (parvula?): Wikipedia даёт parvula для «most of the Eastern Andes»; Эль-Энканто на склоне верхней Магдалены — уточнить. Сравнение с thalurania-colombica (самец с фиолетовой шапочкой в долине Магдалены) по памяти; проверить подвид Thalurania в Уиле.
- anthocephala-berlepschi — colors [green, gray, rufous] пограничны (низ серовато-охристый). Wikipedia пишет «northern Huila», а data даёт «возможно» у Питалито (юг Уилы) — проверить, реально ли вид в Эль-Энканто.
- chrysuronia-oenone — colors с orange за медно-золотой хвост; пограничный выбор.
- coeligena-bonapartei — высоты: data 2 150–3 000 м, Wikipedia 1 400–3 200 м; в тексте «в основном около 2 000–3 000 м». Статус: data near_endemic=true, Wikipedia — эндемик Колумбии (вероятно, из-за ssp. consita в Перихе на границе с Венесуэлой); проверить. Отличие от coeligena-helianthea согласовано с её карточкой.
- aglaeactis-cupripennis — similar pterophanes-cyanopterus (самка с рыжим низом) по памяти; вид есть только в Сумапасе (вне программы).
- thalurania-furcata — подвид viridipectus и «узкая тёмная полоса» между горлом и брюхом по Wikipedia; высоты «до 1 700–2 000 м» — сводка data (1 700) и Wikipedia (2 000).
- phlogophilus-hemileucurus — статус: IUCN в data VU, libro_rojo ACO — NT; в тексте указано VU по МСОП. «Нектар обычно пьёт, присев у цветка» — по Wikipedia («perches to take nectar»).
- haplophaedia-lugens — отличие от H. aureliae и Urosticte benjamini по памяти.
- doryfera-ludovicae — отличие от D. johannae («мельче, темнее, лоб самца фиолетово-синий») по памяти. Голос не описан в Wikipedia.
- heliodoxa-aurescens — отличие от H. schreibersii («горло и грудь чёрные с фиолетовым пятном») по памяти. Голос не описан.
- lafresnaya-lafresnayi — подвиды: под Боготой номинативный (охристый хвост), в Нариньо saul (белый) — по Wikipedia. Отличие от boissonneaua-flavescens («поднимает крылья, садясь») по памяти. tone=bright пограничный. bill только [curved] (без hummingbird_long) — сверить с фото.
- eutoxeres-condamini — «цепляется лапками у цветка» и голос «цип» по памяти. Отличие от phaethornis-malaris по памяти.
- trogon-viridis — size=pigeon по 28–30 см из Wikipedia.
- trogon-ramonianus — жёлтое кольцо вокруг глаза самца взято из статьи Green-backed trogon («violaceous trogon has a yellow eye-ring»); узкая белая полоса на груди (Wikipedia) в карточку не вынесена — проверить. Кольцо самки не указано. Вид «возможен» в Исла-Эскондиде (650–1 600 м) при поясе до 500–1 000 м; family trogonidae.md называет Плайя-Рику — по data там его нет.
- pharomachrus-pavoninus — высоты: Wikipedia даёт две версии (250–1 200 м и 0–700 м), data 0–700; Исла-Эскондида 650–1 600 м — на краю пояса. Отличие от trogon-collaris по памяти.
- pharomachrus-antisianus — «хвост снизу у самца белый» — по полевым знаниям (Wikipedia пишет только «vent is white»); проверить обязательно, это главный признак в карточке. Голос обобщённый.
- baryphthengus-martii — size=crow по 42–47 см (с хвостом). Отличие от Electron platyrhynchum по памяти.
- notharchus-hyperrhynchus — size=thrush при ~25 см (граница с pigeon). Отличие от N. tectus по памяти.
- galbalcyrhynchus-leucotis — розово-красный цвет клюва и «короче хвостом» по памяти (Wikipedia: «more robust bill», цвет не назван). tone=bright за контраст белой щеки.
- monasa-flavirostris — tone=dull при жёлтом клюве и белом пятне — пограничный. Только 3 key_features.
- galbula-tombacea — similar только galbalcyrhynchus-leucotis; других Galbula на маршруте по data нет.

## Data issues

- heliangelus-amethysticollis — data/texts берёт en-статью Wikipedia «Amethyst-throated sunangel» в объёме IOC, где вид в Колумбии не встречается (колумбийская форма там — H. clarisse, Longuemare's Sunangel). Для карточки лучше тянуть текст статьи Longuemare's sunangel. Русского имени нет (names.ru = null).
- coeligena-bonapartei — names.ru = null; высоты в data (2 150–3 000 м) уже, чем в Wikipedia (1 400–3 200 м).
- galbalcyrhynchus-leucotis, monasa-flavirostris, galbula-tombacea — elevation min = "L" (строка вместо числа) в data/species и species_index.
- pharomachrus-pavoninus — «возможно» в Исла-Эскондиде (650–1 600 м) при поясе вида 0–700 м в data; trogon-ramonianus — то же (0–500 м, экстремум 1 000 м).
- content/families/galbulidae.md называет Galbalcyrhynchus «бурыми, без блеска»; по Wikipedia G. leucotis красновато-каштановая с бронзовым блеском на темени, крыльях и хвосте. content/families/trogonidae.md помещает Green-backed и Amazonian Violaceous Trogon на Плайя-Рику (день 10), а data/site_species.json даёт trogon-viridis «возможно» в Плайя-Рике, но trogon-ramonianus — только в Исла-Эскондиде.
- trogon-viridis — ru «Зеленохвостый трогон» при английском Green-backed (зеленоспинный); проверить eBird ru.
- eutoxeres-condamini — ru «Краснохвостый орлиноклюв» при buff-tailed (охристый хвост); имя из eBird, оставлено как есть.
