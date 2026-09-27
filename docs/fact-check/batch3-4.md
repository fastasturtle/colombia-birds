# Факт-чек: партия 3, список 4 (муравьеловки, антпитты, тапакуло, печниковые, морские птицы)

Карточки написаны 27.09.2026 по data/species, data/texts (Wikipedia en/es/ru) и полевым знаниям агента.
Ниже то, что стоит проверить по открытым источникам перед публикацией. Формат: `slug — что проверить`.

## Общее

- Для grallaria-alticola, grallaria-rufula и cercomacroides-fuscicauda в data/texts нет выдержек Wikipedia: карточки написаны по data/species и памяти, формулировки осторожные; проверить целиком (окраска, голос, высоты).
- Голоса описаны по выдержкам Wikipedia (перефразом), кроме: grallaria-alticola, grallaria-rufula, scytalopus-opacus, cercomacroides-fuscicauda, cinclodes-albidiventris, glyphorynchus-spirurus (позыв «чиф»), phaethon-aethereus — там по памяти и обобщённо.
- size на границах классов: cinclodes-albidiventris (16–17 см, поставлен thrush), dichrozona-cincta (9–10 см, поставлен sparrow, а не hummingbird), myrmothera-fulviventris (14–15 см, sparrow), hydrobates-tethys (около 15 см, sparrow), phaethon-aethereus (тело 48 см, с лентами 90–105 см, поставлен crow).

## По видам

- grallaria-alticola — окраска перенесена с Tawny Antpitta (G. quitensis, карточка партии 1); проверить, отличается ли alticola внешне (colors [brown, olive] против [brown, rufous] у quitensis). Голос «несколько свистовых нот с открытой присады» — по памяти. «Недавно выделен из Tawny Antpitta» — проверить год и систему (Clements 2024/2025?).
- grallaria-rufula — высоты в тексте по data (1 850–3 800 м); реальный пояс Muisca Antpitta, вероятно, уже (≈2 500–3 500 м). Описание окраски («почти сплошь рыжая, низ светлее») и голос обобщённые; отличие от G. saturata «по ареалу и песне» согласовано с её карточкой.
- cinclodes-albidiventris — «подёргивает хвостом», токование с поднятыми крыльями и трелью — по памяти; similar cinclodes-excelsior: «у Боготы не встречается» — проверить распространение Stout-billed Cinclodes в Колумбии.
- leptasthenura-andicola — подвид exterior у Боготы по Wikipedia; поведение «как синица, вниз головой» по памяти (в выдержке кормление обрезано).
- glyphorynchus-spirurus — подвид subrufescens на тихоокеанском склоне по Wikipedia; similar xenops-rutilans — проверить, встречается ли Streaked Xenops на тихоокеанском склоне Нариньо на высотах Авес-и-Флорес (и нет ли в индексе Plain Xenops тихоокеанской формы: в индексе только xenops-minutus «Atlantic Plain-Xenops»).
- dysithamnus-puncticeps — similar dysithamnus-mentalis «живёт выше по склону» — по памяти; bill [short, thick] — проверить.
- hafferia-zeledoni — tail «длинный» (long_tail) по памяти; «иногда у кочевых муравьёв» по памяти (выдержка о кормлении обрезана).
- epinecrophylla-fulviventris — similar myrmotherula-schisticolor по памяти.
- scytalopus-opacus — голос («ритмичная серия коротких нот») обобщённый, проверить по xeno-canto. marks barred поставлен за полоски на боках.
- synallaxis-azarae — подвид на юге Колумбии (media) по Wikipedia; отличие от S. brachyura по памяти.
- cercomacra-nigricans — similar cercomacroides-tyrannina и thamnophilus-atrinucha по памяти; белые концы хвоста по Wikipedia (у самца).
- furnarius-leucopus — см. «Data issues»: птицы Тумако — Pacific Hornero (F. cinnamomeus). Описание окраски (рыжий верх, белое горло и бровь) дано по номинативному leucopus из Wikipedia и должно подходить к cinnamomeus, но проверить (цвет ног и клюва, оттенок низа). Similar cantorchilus-nigricapillus — натяжка: похожих видов на побережье почти нет.
- liosceles-thoracicus — «хвост часто приподнят» по памяти.
- grallaricula-nana — какой подвид на Трамплине птиц (occidentalis?); отличия от G. cucullata и G. flavirostris по памяти, сверить с их карточками/фото.
- xiphocolaptes-promeropirhynchus — similar lepidocolaptes-lacrymiger и campylorhamphus-pusillus; «долбит бромелии» по памяти.
- myornis-senilis — content/families/rhinocryptidae.md пишет «Ash-colored в Чикаке», а data/site_species.json даёт там unlikely (freq 0.0005); в карточке Чикаке не упомянута — согласовать семейный текст.
- myrmothera-fulviventris — Исла-Эскондида (650–1 600 м) выше пояса вида (до 400 м в Колумбии по Wikipedia, до 600 м по data), а data даёт там maybe; similar myrmothera-campanisona — отличие по памяти.
- dichrozona-cincta — то же: Исла-Эскондида выше пояса (до 500 м в Колумбии). tone=bright за резкий чёрно-белый рисунок — пограничный.
- rhegmatorhina-melanosticta — similar gymnopithys-leucaspis, phlegopsis-nigromaculata по памяти.
- thripadectes-holostictus — подвид striatidorsus на западном склоне юга Колумбии (с Кауки на юг) по Wikipedia; отличия от T. flammulatus и T. virgaticeps по памяти.
- siptornis-striaticollis — «клюв прямой» и отличия от xenops/premnoplex по памяти; голос почти не известен.
- berlepschia-rikeri — Эль-Эскондите упомянута по study_lists (день 13–14 октября), site_species для неё данных нет.
- dysithamnus-occidentalis — высоты: data 900–2 200 м, Wikipedia 1 600–2 400 м в Колумбии; в тексте дано по Wikipedia. Статус: libro_rojo VU, IUCN ACO VU, BIRDBASE NT, Wikipedia NT. Отличия от thamnophilus-unicolor и sipia-nigricauda по памяти.
- sipia-berlepschi — Бангсиас-лодж (900–1 200 м) выше пояса вида (до 650 м).
- cercomacroides-fuscicauda — вся карточка по памяти: окраска самца/самки, дуэт, отличие от C. nigrescens по голосу и биотопу. Высоты по data (100–600 м).
- nannopterum-brasilianum — similar anhinga-anhinga; брачный наряд по Wikipedia.
- sula-granti — «гнездится на Мальпело» (Wikipedia пишет лишь «occurs»); клюв Masked Booby «зеленовато-жёлтый» по памяти; libro_rojo VU по data.
- hydrobates-tethys — ru-Wikipedia пишет «нижняя часть тела светлее, с беловатым оттенком», что противоречит полевому облику (сплошь тёмная с белой поясницей); в карточку не взято. «Светлая полоса на крыле сверху» и отличия от H. microsoma, H. castro, Oceanites gracilis — по памяти.
- procellaria-parkinsoni — «клюв светлый с тёмным кончиком» (Wikipedia: «pale sections on the bill»), «кормится у дельфинов и тунца» — по памяти; отличия от Ardenna grisea / pacifica по памяти.
- phaethon-aethereus — Wikipedia противоречит себе: «streamers about two times their body length» и «48 см тело, ленты 46–56 см»; в тексте дано 48 см и 90–105 см общей длины. «Гнездится на островах тихоокеанского побережья Колумбии» — взято из content/families/phaethontidae.md, проверить. similar phaethon-lepturus в Колумбии hypothetical.

## Data issues

- furnarius-leucopus — маппинг: в Clements/IOC птицы тихоокеанского побережья Колумбии (Тумако) — отдельный вид Pacific Hornero (Furnarius cinnamomeus), а F. leucopus в узком смысле в Колумбии не встречается (Wikipedia: Боливия, Бразилия, Гайана, Перу). В data/species_index.json нет furnarius-cinnamomeus; ACO 2022 держит широкий F. leucopus. Проверить pipeline/mappings/aco_to_ebird.json; у вида и нет русского имени (ru: None).
- cinclodes-albidiventris — data: near_endemic=true, хотя вид распространён от Венесуэлы до Перу; проверить источник (Chaparro-Herrera et al. 2024?).
- grallaria-alticola — en_aco = None, ru = None; libro_rojo и habitat_aco пустые (вид новый, после сплита Tawny Antpitta). IUCN aco_2022 = None.
- grallaria-rufula — links.wikipedia все null, нет data/texts; фото в data — «Rufous Antpitta, Tapichalaca, Ecuador», то есть другая форма комплекса (не Muisca); проверить фото.
- cercomacroides-fuscicauda — нет записей в data/site_species.json ни на одной точке, но вид есть в study_lists на 11–13 октября; нет data/texts.
- phaethon-aethereus, procellaria-parkinsoni — нет записей в site_species (только study_lists 22–23 октября); procellaria-parkinsoni в data habitats включает «forest» (гнездовой биотоп в Новой Зеландии), для Колумбии неактуально.
- myrmothera-fulviventris, dichrozona-cincta, sipia-berlepschi — «maybe/unlikely» на точках выше их высотного пояса (Исла-Эскондида 650–1 600 м, Бангсиас 900–1 200 м): вероятно, радиус GBIF захватывает низины.
- dysithamnus-occidentalis — высоты data (900–2 200) расходятся с Wikipedia (1 600–2 400 в Колумбии).
- hydrobates-tethys — data primary_diet = Fish; Wikipedia ru — планктон и мелкая рыба (не ошибка, но уточнить).
