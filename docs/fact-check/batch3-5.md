# Факт-чек: партия 3, список 5 (колибри, стрижи, трогоны, момоты, пуховки, якамары)

Карточки написаны 27.09.2026 по data/species, data/texts (Wikipedia en/ru), data/site_species.json, data/sites.json
(списки целей) и полевым знаниям агента. Ниже то, что стоит проверить по открытым источникам перед публикацией.
Формат: `slug — что проверить`.

## Общее

- Кормушки (`feeder` в `layer`) поставлены: aglaiocercus-coelestis, thalurania-colombica, heliodoxa-jacula (Авес-и-Флорес),
  colibri-delphinae, uranomitra-franciae (Эль-Энканто), coeligena-torquata (Чикаке) — по общему знанию, что виды обычны
  на кормушках; проверить. Не поставлены, хотя вид ходит на кормушки вне маршрута: pterophanes-cyanopterus (Обсерватория
  колибри, вне программы), coeligena-lutetiae, taphrospilus-hypostictus, boissonneaua-matthewsii, androdon-aequatorialis.
- Голоса, которых нет в выдержках Wikipedia и которые даны обобщённо по памяти: pterophanes-cyanopterus, thalurania-colombica,
  heliodoxa-jacula, anthracothorax-nigricollis, adelomyia-melanogenys, tachornis-squamata, streptoprocne-zonaris,
  uranomitra-franciae, chrysuronia-goudoti, discosura-langsdorffi, klais-guimeti (песня — по описанию токов), patagona-gigas,
  pharomachrus-auriceps.
- Для видов со статусом «маловероятно» по GBIF, но в списке целей точки (data/sites.json target_species_raw), текст говорит
  «в списке целей, но наблюдений мало»: urochroa-leucura, discosura-popelairii, taphrospilus-hypostictus,
  discosura-langsdorffi, klais-guimeti, patagona-gigas, chaetocercus-bombus, boissonneaua-matthewsii, galbula-pastazae,
  malacoptila-fulvogularis, cypseloides-cherriei, schistes-albogularis.

## По видам

- pterophanes-cyanopterus — подвид на Бордонсильо (peruvianus или caeruleus?) не указан в карточке; «махи как у ласточки» по памяти. Размер крупнее «топазов» — по Wikipedia.
- aglaiocercus-coelestis — смена с A. kingii по сезонам (Wikipedia: в юго-западной Колумбии coelestis доминирует в январе–апреле, в сезон дождей его вытесняет kingii): в карточке смягчено до «соотношение меняется по сезонам»; проверить, не будет ли в октябре на Нариньо больше kingii. «Поясница синеватая» — по Wikipedia (violet-blue rump).
- thalurania-colombica — ключевое: окраска подвида verticeps (Нариньо, тихоокеанский склон). В карточке: темя зелёное, спина целиком зелёная, брюхо фиолетовое (вывод из Wikipedia, где verticeps описан после fannyae с зелёным теменем). Проверить; также какой подвид в Уиле (колумбийский номинативный «до верховьев Магдалены» — по Wikipedia).
- androdon-aequatorialis — высота в Колумбии до ~1 050–1 100 м, а Авес-и-Флорес 1 100–1 300 м; в карточке «верхний край пояса». difficulty=medium.
- adelomyia-melanogenys — охристые кончики хвоста и сходство с anthocephala-berlepschi (темя самца белое и каштановое) — по памяти и по формулировкам карточки berlepschi; отличие от самки urosticte-ruficrissa по памяти. marks [spotted_breast, eyebrow] — чёрная щека словарём не покрыта.
- heliodoxa-jacula — «белые штанишки» и «белое пятнышко за глазом» по Wikipedia; у подвида jamersoni голова и грудь тусклее. Утверждение, что вид «один из хозяев кормушек» Авес-и-Флорес, — по общему знанию о кормушках Чоко.
- colibri-delphinae — «на кормушках больше гоняет, чем пьёт» по Wikipedia; отличия от C. cyanotus и C. coruscans согласованы с их карточками.
- anthracothorax-nigricollis — отличие от florisuga-mellivora (синяя голова, белый полумесяц на затылке, почти белый хвост у самца) по памяти.
- coeligena-torquata — отличие от C. prunellei и C. wilsoni согласовано с их карточками; отличие от lafresnaya-lafresnayi («брюхо чёрное») по памяти — у самца Lafresnaya брюхо чёрное, у самки белое в пятнах.
- tachornis-squamata — голос по памяти; отличие от panyptila-cayennensis (белые горло, воротник, пятна по бокам поясницы) по памяти.
- streptoprocne-zonaris — size=thrush по длине тела 20–21,5 см, хотя в поле он выглядит крупнее (размах 45–55 см); пограничный выбор. Голос «скрии» по памяти. Ночёвка за водопадами — по content/groups и полевым знаниям.
- coeligena-lutetiae — высоты «от 2 600 м и выше» (Wikipedia и data дают до 4 800 м — подозрительно высоко, в тексте верхняя граница не названа).
- uranomitra-franciae — подвид в Уиле: Wikipedia даёт номинативный для «Andes of northwestern and central Colombia»; принадлежность птиц верхней Магдалены (Эль-Энканто) не проверена. В Нариньо viridiceps «с зелёной головой» (Wikipedia: green crown). Отличие от chalybura-buffonii по памяти.
- chrysuronia-goudoti — ТЕКСТА WIKIPEDIA НЕТ. Вся карточка по памяти: окраска (весь зелёный, подклювье красное, хвост тёмный), распространение (почти-эндемик Колумбии и Венесуэлы — data near_endemic=true), биотопы, голос, отличия от Chlorostilbon gibsoni и Saucerottia saucerottei. difficulty=hard. Высоты: data 0–1 000 м, а вид «точно» в Эль-Энканто (1 350 м) — проверить.
- cypseloides-cherriei — «хвост почти квадратный» и отличие от C. cryptus по памяти; size=sparrow по 14 см.
- schistes-albogularis — отличие от urosticte-benjamini и adelomyia по памяти/по карточкам. Рио-Ньямби в списке целей как «Chocó Daggerbill».
- urochroa-leucura — «рыжая усиковая полоса» у U. bougueri — по названию Rufous-gaped и русскому «безусый»; проверить. Wikipedia (en) даёт распространение «east slope from southern Colombia»; в Сибундое цель записана как «White-tailed Hillstar».
- discosura-popelairii — NT в data (iucn.aco_2022) при LC в Wikipedia; в тексте сказано так. «Кормится медленно, приподняв хвост, как насекомое» и «в садах опускается к цветникам» по памяти.
- taphrospilus-hypostictus — Колумбия «по немногим находкам на юге» по Wikipedia (documented in southern Colombia).
- discosura-langsdorffi — «зависает медленно, как шмель» по памяти; голос по памяти.
- klais-guimeti — colors [green, purple, gray]; marks пусто (белое пятно за глазом словарём не покрыто).
- patagona-gigas — см. Data issues (таксономия). Все приметы по памяти: размер ~20 см, беловатая поясница, окраска северного вида (P. peruviana; Wikipedia: yellowish brown, white on chin and throat — в карточку не вынесено), голос «цвиик», биотопы в Нариньо. Распространение в Колумбии «только крайний юг, Нариньо» — проверить. colors [brown, olive, rufous] пограничны.
- chaetocercus-bombus — статус в Колумбии: ACO 2022 «Hipotética», Wikipedia — «extreme southwestern Colombia»; в тексте сказано о гипотетическом статусе. Отличие от C. heliodor («горжетка шире на бока шеи, охристой полосы нет») по памяти; согласовать с карточкой heliodor. IUCN в data VU, Wikipedia — NT (2021); в тексте статус МСОП не назван.
- boissonneaua-matthewsii — высоты даны эквадорские (Wikipedia), колумбийских нет. Отличие от B. flavescens и aglaeactis по памяти.
- monasa-nigrifrons — size=pigeon (26–29 см). Клюв «слегка изогнутый» по памяти.
- electron-platyrhynchum — расхождение с карточкой baryphthengus-martii: там про Electron «рыжие только голова и шея, грудь зелёная», а Wikipedia пишет «head, neck and chest cinnamon-rufous»; в новой карточке «голова, шея и верх груди рыжие». Согласовать. Длина «около 30 см» (Wikipedia: about 12 inches); size=pigeon.
- pharomachrus-auriceps — голос (двусложные свисты, кудахтающий позыв) по памяти. Высоты 1 200–3 100 м по data.
- hapaloptila-castanea — «не находится под угрозой» по Wikipedia (LC, stable); tone=bright пограничный; marks [plain] при белом «лице».
- galbula-pastazae — ключевое: оранжево-жёлтое голое кольцо вокруг глаза (по памяти, в Wikipedia нет) и название «coppery-chested» при том, что Wikipedia описывает грудь как блестящую зелёную (content/families/galbulidae.md пишет «медно-рыжая грудь»). Проверить окраску груди. Высоты «около 750–1 600 м» (Эквадор 750–1 500, находка в Колумбии на 1 600 м).
- malacoptila-fulvogularis — подвиды huilae и substriata по Wikipedia (Clements); какой подвид на Финке Дискосура — не указано.

## Data issues

- patagona-gigas — таксономия: Clements/eBird (ebird_code в data — giahum1) и Wikipedia разделили Giant Hummingbird на Southern (P. gigas) и Northern (P. peruviana). data/texts содержит статью о южном виде (Southern giant hummingbird), к колумбийским птицам неприменимую; ACO 2022 даёт P. gigas. Нужен маппинг на северный вид и перезагрузка текстов. Также data elevation 0–4 800 м (от южного вида).
- patagona-gigas — в data/site_species.json вида нет ни на одной точке, хотя Лагуна Ла-Коча держит его в списке целей.
- chaetocercus-bombus — colombia.status_raw «Hipotética», при этом data/species_index.json показывает вид как обычный и сайт, вероятно, не помечает его гипотетичность.
- discosura-langsdorffi — data elevation 100–300 м, а цель поставлена на Исла-Эскондиду (650–1 600 м); вероятно, цель списка сайта ошибочна или относится к нижней части маршрута к лоджу.
- cypseloides-cherriei — «возможно» на Км 42 (50–150 м) при поясе вида 1 100–2 200 м; стоит проверить записи GBIF (возможно, неверная привязка/путаница с другими стрижами).
- chrysuronia-goudoti — нет data/texts (Wikipedia-статья, вероятно, под названием Shining-green hummingbird или Amazilia/Lepidopyga goudoti, не сопоставилась).
- aglaiocercus-coelestis — habitat_aco «Grassland» выглядит неверным для лесного колибри.
- taphrospilus-hypostictus — habitat_aco «Shrubland», по Wikipedia — внутри и на опушках леса.
- urochroa-leucura — русское имя «Безусый диамант» выглядит странно для рода Urochroa (hillstar), но взято как есть из data.
- heliodoxa-jacula — русское имя «Синегрудый бриллиант» не соответствует окраске (у вида зелёная грудь); взято как есть из data.
- hapaloptila-castanea — русское имя «Белолицая ленивка» (в content/families/bucconidae.md то же), оставлено как в data.
