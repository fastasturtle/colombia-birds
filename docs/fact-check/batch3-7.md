# Факт-чек: партия 3, список 7 (ласточки, крапивники, дрозды, виреоны, сойки, попугаи, козодой)

Карточки написаны 27.09.2026 по data/species, data/texts (Wikipedia en/es/ru), data/site_species.json и полевым знаниям агента.
Ниже то, что стоит проверить перед публикацией. Формат: `slug — что проверить`.

## Общее

- Голоса попугаев pionus-chalcopterus, pyrrhura-calliptera, aratinga-weddellii, forpus-conspicillatus и ласточки progne-chalybea (кроме «чю-чю»), polioptila-plumbea — в выдержках Wikipedia описаны скупо или не описаны; в карточках обобщённые формулировки («резкие скрипучие крики»), проверить.
- Размерные классы на границе: cyanocorax-violaceus (33–37 см) поставлен `crow`; aratinga-weddellii (25–28 см) — `pigeon`; progne-chalybea (16–18 см) — `thrush`; hirundo-rustica (17–19 см с косицами) — `sparrow`; cistothorus-platensis (10–10,5 см) — `sparrow`.
- Сойки и попугаи с кормушками: `feeder` не ставился никому.

## По видам

- vireo-olivaceus — нет data/texts; карточка целиком по data и памяти. Проверить: отличие от V. chivi (кайма брови, желтизна боков), голос на зимовке («мяй», «чит»), сроки пролёта (сентябрь–октябрь), цвет глаза у молодых.
- orochelidon-murina — отличие от O. flavipes («горло рыжевато-охристое, брюхо белое с тёмными боками, над кронами облачного леса») по памяти.
- cyanocorax-violaceus — отличие от C. yncas («бело-голубая шапка, чёрная грудь», высоты Уилы) по памяти; размер группы «4–10 птиц» по памяти.
- pygochelidon-cyanoleuca — отличие от tachycineta-albiventer по памяти.
- mimus-gilvus — similar tyrannus-dominicensis выбран за неимением лучшего (на маршруте не отмечен); подвид в Сибундое/Уиле предположен как tolimensis (Wikipedia: «western and central Colombia south to extreme northern Ecuador»).
- henicorhina-leucophrys — отличие от troglodytes-solstitialis («широкая охристая бровь, щёки без штрихов, кормится во мху») по памяти.
- atticora-fasciata — Wikipedia упоминает «white bars on the edges of its wings»; в карточку не вынесено, проверить по фото. Отличия от A. tibialis и P. melanoleuca по памяти (кроме «white underparts and throat» у melanoleuca).
- catharus-ustulatus — голос на зимовке («уит», «пуик») по памяти; отличия от C. minimus и C. fuscescens по памяти.
- cinnycerthia-unirufa — «группы по 3–8 птиц» по памяти (Wikipedia: «groups of a few individuals»).
- cistothorus-platensis — «шапочка тоже в штрихах» согласовано с карточкой cistothorus-apolinari (там: «шапочка тоже в пестринах»); отличие apolinari («крупнее, голова сероватая, шапочка без штрихов, тростники») по памяти — сверить с её карточкой и фото.
- vireo-leucophrys — голос («короткая быстрая переливчатая фраза») по памяти; отличие от V. masteri («две белые полосы на крыле, бровь желтоватая») взято из карточки vireo-masteri.
- progne-chalybea — отличия от P. tapera и P. subis (самка со светлым лбом и серым воротником) по памяти.
- microcerculus-marginatus — «ходит, покачивая задней частью тела» по памяти (для рода известно, но проверить для этого вида); подвид на склоне Чоко (occidentalis) по Wikipedia.
- microbates-cinereiventris — подвид в Путумайо (hormotus: «southern Colombia, eastern Ecuador») по Wikipedia; «часто со смешанными стаями подлеска» по памяти.
- hirundo-rustica — сроки пребывания «примерно с сентября по апрель» по памяти.
- polioptila-plumbea — таксономия: птицы тихоокеанского побережья относятся к группе bilineata (White-browed Gnatcatcher); проверить, выделен ли P. bilineata в Clements 2025, и если да, то куда отнести наблюдения на Км 42/Тумако. Отличие от P. schistaceigula по памяти.
- stelgidopteryx-ruficollis — подвиды (uropygialis на западе, номинативный на юго-востоке) по Wikipedia; similar progne-tapera по памяти.
- henicorhina-leucosticta — «полоса, где высоты перекрываются» — формулировка без чисел; в sources указана ru-статья Wikipedia «Белогрудый лесной крапивник» (есть в data/texts).
- cyanolyca-pulchra — отличие от C. turcosa по Wikipedia (turcosa: светлый лоб, узкий ошейник) и памяти; статус: ACO libro_rojo VU, МСОП NT (data).
- cyanolyca-turcosa — отличие от C. armillata («темнее, глубоко-синяя, горло синее») по памяти; проверить, какой вид реально живёт в лесах Сибундоя/Бордонсильо (см. Data issues).
- odontorchilus-branickii — голос не описан в Wikipedia, в карточке обобщённо; отличие от troglodytes-solstitialis по памяти.
- pionus-chalcopterus — «глубокие взмахи, как у всех амазонетов» — по content/families/psittacidae.md; в content/groups/parrots.md сказано обратное («амазоны и пионы … неглубокими взмахами»): согласовать групповой портрет.
- pionus-menstruus — подвид rubrigularis на тихоокеанском склоне по Wikipedia («southern Central America and the Chocó»); проверить, относится ли к нему популяция у Тумако/Км 42.
- pyrrhura-calliptera — голос не описан; ru-название в Wikipedia «Роскошный краснохвостый попугай», в индексе «Коричневогрудая которра».
- aratinga-weddellii — отличия от brotogeris-cyanoptera и psittacara-leucophthalmus по памяти.
- pyrilia-pulchra — «почти-эндемик Колумбии» по data (near_endemic=true); ареал: Колумбия и запад Эквадора.
- forpus-conspicillatus — Wikipedia-выдержка без описания; окраска (синее кольцо у самца, изумрудное у самки, синие поясница и крыло), местообитания и размер по памяти. Вид «точно» на Плайя-дель-Морро и «возможно» у Тумако — проверить, не перепутаны ли в GBIF наблюдения с F. coelestis (см. Data issues).
- touit-huetii — «кочуют стайками» по Wikipedia («Movement» не прочитан до конца) и памяти.
- touit-stictopterus — wing_bars поставлены за ряды светлых пятен на кроющих самца; пограничный выбор.
- nyctiphrynus-rosenbergi — отличия от Nyctidromus albicollis и Lurocalis semitorquatus по памяти; белых кончиков хвоста в карточке нет (не уверен, есть ли они у вида).

## Data issues

- cyanolyca-turcosa — в data/site_species.json нет ни одной точки маршрута, даже со статусом unlikely, хотя вид живёт в Нариньо и Путумайо на 1 850–3 000 м; зато cyanolyca-armillata «возможно» в Сибундое и на Трамплине птиц. Возможна путаница видов или пробел GBIF. content/groups/songbirds.md называет Turquoise Jay в Ла-Нутрии (1 000–1 400 м) — ниже высот вида, по data там её тоже нет; исправить групповой портрет.
- cyanolyca-turcosa — статья en Wikipedia даёт высоты «2000–3000 feet» и «2600–3000 feet» — явная ошибка единиц (должны быть метры).
- odontorchilus-branickii — цель Трамплина птиц в data/sites.json (target_species_raw), но в site_species.json там unlikely (freq 0). data/species: habitat_aco «Shrubland» при кронах горного леса.
- touit-huetii — цель Эль-Эскондите в data/sites.json, но в site_species.json Эль-Эскондите нет вовсе. content/groups/parrots.md и families/psittacidae.md называют вид в Эль-Эскондите и «в низинах у Пуэрто-Асиса» — по data там unlikely.
- touit-stictopterus — цель Эль-Энканто в data/sites.json, в site_species.json там unlikely (freq 0,0002).
- nyctiphrynus-rosenbergi — content/families/caprimulgidae.md называет Рио-Ньямби основным местом (день 17), но по data там unlikely, а Рио-Ньямби (1 100–1 900 м) выше пояса вида (до 900 м).
- cinnycerthia-unirufa, pionus-chalcopterus — near_endemic=true в data, хотя оба вида широко живут за пределами Колумбии (Венесуэла–Перу; Венесуэла–Перу); проверить источник флага.
- pyrrhura-calliptera — en Wikipedia озаглавлена «Flame-winged parakeet», ACO/eBird — Brown-breasted Parakeet; в карточке указаны оба.
- microbates-cinereiventris — en_aco «Half-collared Gnatwren», в индексе (eBird) «Tawny-faced Gnatwren»; в карточке указаны оба.
- forpus-conspicillatus — «sure» на Плайя-дель-Морро и «maybe» у Тумако при соседстве F. coelestis (карточка forpus-coelestis: единственное место в Колумбии — юго-запад Нариньо); возможно, часть наблюдений — ошибочные определения.
- polioptila-plumbea — в индексе нет P. bilineata; если Clements 2025 его выделяет, маппинг ACO → eBird для тихоокеанских птиц надо пересмотреть.
- vireo-olivaceus — нет data/texts (Wikipedia en не загружена); wikidata iucn = null.
