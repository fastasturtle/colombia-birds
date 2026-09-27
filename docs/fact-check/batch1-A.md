# Факт-чек: партия 1, список A (колибри, трогоны/зимородки, туканы/бородатки)

Карточки написаны 27.09.2026 по data/species, data/texts (Wikipedia en) и полевым знаниям агента.
Ниже то, что стоит проверить по открытым источникам перед публикацией. Формат: `slug — что проверить`.

## Общее

- chalcostigma-heteropogon, coeligena-helianthea, eriocnemis-cupreoventris, oxypogon-guerinii — вид есть только в необязательных точках у Боготы (Обсерватория колибри, Чингаса, Сумапас), в тексте сказано «шанс только при поездке туда 1–2 октября». Когда решится TODO про дни 1–2 октября, поправить формулировку (и, если поедут 25 октября, добавить дату).
- lesbia-victoriae, lesbia-nuna, metallura-tyrianthina, eriocnemis-vestita, chaetocercus-mulsant — упоминают Обсерваторию колибри «если в свободные дни туда выбраться»; та же зависимость от TODO.
- Все колибри — `feeder` в `layer` поставлен только coeligena-wilsoni, heliangelus-exortis, heliodoxa-imperatrix, boissonneaua-jardini, urosticte-benjamini. Проверить, реально ли эти виды ходят на кормушки именно лоджей маршрута (Авес-и-Флорес, Рио-Ньямби, Ла-Нутрия, Чикаке), и не стоит ли добавить `feeder` видам Обсерватории колибри (lesbia-*, metallura-tyrianthina, eriocnemis-*, coeligena-helianthea, chaetocercus-mulsant) и phaethornis-yaruqui, chionomesa-fimbriata (Финка Дискосура).

## По видам

- lesbia-victoriae — голос: «тонкие сухие позывки» написаны обобщённо; щелчок хвостом на токовом пикировании взят из Wikipedia. Длина клюва (`bill: short`) и изгиб «чуть загнут вниз» — сверить с фото; Wikipedia сравнивает только относительно L. nuna.
- oxypogon-guerinii — высоты: в data 3 000–5 200 м (BIRDBASE, вероятно, по старому объёму вида вместе с O. lindenii/stuebelii), в тексте 3 000–4 200 м по Wikipedia; уточнить. Голос не описан, в карточке «тихий, в поиске почти не помогает» — проверить. tone=bright выбран за контраст головы при тусклом теле — пограничный случай.
- chaetocercus-mulsant — отличия от C. heliodor («брюхо тёмное, горжетка с удлинёнными уголками») даны по памяти, сверить. Регулярно ли ходит на кормушки (Обсерватория, Чикаке)?
- metallura-tyrianthina — цвет хвоста номинативного подвида: Wikipedia пишет «glistening bronze», в карточке «медно-бронзовый с красноватым отливом»; уточнить. Отличия от M. williami (цвет хвоста, горло самки, высоты) — по памяти, проверить. Голос обобщённый.
- eriocnemis-vestita — фраза, что в Нариньо (ssp. smaragdinipectus) фиолетовое пятно у самцов крупнее, чем у птиц из-под Боготы, опирается на Wikipedia; перепроверить, какой подвид на Бордонсильо.
- coeligena-helianthea — выбор colors [black, green, purple] при розовом брюхе (в словаре нет pink); tone=dull спорно. Голос «одиночные резкие чит» по Wikipedia.
- chalcostigma-herrani — голос почти неизвестен; в карточке об этом прямо сказано. Отличие от M. williami по памяти.
- lesbia-nuna — голос по Wikipedia («дррт», «бзззт») относится к виду в целом; проверить для ssp. gouldii в Колумбии.
- chalcostigma-heteropogon — статус «почти-эндемик Колумбии» из data (near_endemic=true); tone=dull, colors [green, olive] — пограничные.
- phaethornis-yaruqui — ru-статья Wikipedia в data/texts названа «Синехвостый солнечный колибри», что не похоже на этот вид (вероятно, ошибка в Wikidata/ruwiki); в sources ru не использовалась. Ходит ли вид на кормушки Авес-и-Флорес — не указано, проверить. Подбор цветков («геликонии, имбирные») — общее для отшельников, не видовое.
- coeligena-wilsoni — «регулярно приходит на кормушки лоджей и держится спокойнее многих соседей» — по полевому опыту Эквадора, проверить для Нариньо. Отличие от C. coeligena (горло беловатое в пестринах) по памяти.
- heliangelus-exortis — отличие от H. amethysticollis (охристая полоса под горлом) по памяти; в Колумбии у Боготы подвид/вид amethysticollis может называться иначе (Longuemare's Sunangel, H. clarisse) — сверить таксономию с eBird 2025. Голос по Wikipedia.
- eriocnemis-mosquera — отличие от E. derbyi («штанишки» чёрные) по памяти; присутствие E. derbyi на Бордонсильо в data не подтверждено. Голос обобщённый.
- chionomesa-fimbriata — отличия от Chlorostilbon mellisugus и Chrysuronia oenone по памяти. Бирюзовый оттенок горла у ssp. fluviatilis — из Wikipedia.
- heliodoxa-imperatrix — отличие от H. jacula («хвост короче и почти не вырезан, брюхо без золотистого») по памяти, проверить. Посещение кормушек лоджей Нариньо — проверить.
- boissonneaua-jardini — отличие от B. flavescens по памяти (охристый хвост, рыжие подкрылья). Голос обобщённый.
- eriocnemis-cupreoventris — всё по Wikipedia; colors [green, orange, white] (медь → orange) — пограничный выбор.
- urosticte-benjamini — посещение кормушек (в т. ч. на Ла-Нутрии) не проверено; отличия от H. jacula и Heliothryx barroti по памяти.
- megaceryle-torquata — длина около 40 см дана по общим знаниям и семейному тексту (в выдержке Wikipedia длины нет). Отличие от M. alcyon (северный мигрант, в data на маршруте нет) — проверить, нужен ли он вообще в similar.
- trogon-comptus — отличие от T. massena (оранжевое кольцо, оранжево-красный клюв, зелёный хвост сверху) по памяти; проверить. Размер 28 см → `pigeon`.
- capito-squamatus — отличие от C. quinticolor (красное темя самца, жёлтые полосы на спине) по памяти; C. quinticolor в data на маршруте нет. Статус VU — из data (libro_rojo ACO).
- capito-auratus — голос «низкое гулкое ху-ту-ту» дан по памяти, проверить обязательно. Colors/marks (eyebrow, wing_bars, streaked_breast) — сверить с фото колумбийского подвида.
- ramphastos-brevis — «низ клюва каштановый» у R. ambiguus (ssp. swainsonii) и транскрипция его крика «кьё-ке-ке» — по памяти; проверить. difficulty=hard из-за необходимости голоса.
- eubucco-bourcierii — голос («тихая трель») по памяти; размер ~16 см отнесён к `sparrow` (граница с `thrush`). Описание самки («голубые щёки, оранжево-жёлтое горло, зелёная шапочка») согласовано с content/families/capitonidae.md, но у подвидов оно разное.
