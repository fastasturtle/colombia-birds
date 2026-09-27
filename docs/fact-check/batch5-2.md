# Факт-чек: партия 5, список 2 (тиранны, цапли, пастушок, куриные, трогоны, пуховки, зимородок, якамара)

Карточки написаны 27.09.2026 по data/species, data/texts (Wikipedia en/es/ru) и полевым знаниям агента.
Ниже то, что стоит проверить по открытым источникам перед публикацией. Формат: `slug — что проверить`.

## Общее

- Нет текста Wikipedia в data/texts, карточка написана по данным проекта и памяти: pogonotriccus-ophthalmicus, pipile-cumanensis. Проверить все признаки, голос и поведение.
- Голоса по памяти или обобщённо (в выдержке голоса нет или он обрезан): myiotheretes-fumigatus, elaenia-albiceps, myiopagis-viridicata («чиий-ир»), poecilotriccus-sylvia, pogonotriccus-ophthalmicus, ardea-cocoi, ardea-herodias, theristicus-caudatus, pilherodius-pileatus («обычно молчит»), trogon-massena (выдержка обрезана на Vocalization), monasa-morphoeus, chloroceryle-inda, odontophorus-gujanensis, penelope-jacquacu (и токовое хлопанье крыльями), pipile-cumanensis, aburria-aburri (связь названия «абурриа» с голосом, крики ночью).
- Длина тела для `size` — из Wikipedia. Пограничные классы: pilherodius-pileatus 51–59 см → `crow`; galbula-ruficauda ≈25 см → `thrush`; monasa-morphoeus 21–29 см → `pigeon` (как у M. nigrifrons); porzana-carolina 19–30 см → `thrush`.
- Нет русского имени в data/species_index.json (в тексте только английское): poecilotriccus-sylvia, pipile-cumanensis.

## По видам

- myiotheretes-fumigatus — высоты «примерно 2 000–3 600 м» по Wikipedia en (в data 1 800–3 000, экстремум 3 600). Отличие от O. fumicolor и M. striaticollis сверено с их карточками. Голос не описан.
- elaenia-brachyptera — отличие от E. flavogaster и E. frantzii по памяти; есть ли E. frantzii на склоне Чоко в Нариньо, где живёт brachyptera. Транскрипция голоса — перевод цитат Wikipedia (из eBird/BoW через Wikipedia), проверить, что это не дословное копирование.
- elaenia-albiceps — зимуют ли птицы подвида chilensis в Колумбии (статус ACO «Migratorio Austral - Residente»; в карточке «возможно, доходят до юга Колумбии»). Подвид в Нариньо — griseigularis (по Wikipedia). Голос по памяти.
- attila-spadiceus — какой подвид в Путумайо (восточный склон; в карточке подвид не назван). «Обычно до 1 500 м, местами выше» — по data и Wikipedia (до 2 100 м).
- todirostrum-nigriceps — распространение в Колумбии («тихоокеанская сторона, север, долины между кордильерами») обобщено по Wikipedia; проверить, есть ли вид в Нариньо у Тумако (Финка Марагрикола).
- mecocerculus-poecilocercus — Z. chrysops как похожий вид выбран агентом; отсутствие чётких полос на крыле у Zimmerius — по памяти.
- myiopagis-viridicata — голос по памяти; подвид у Чикаке (pallens?) не назван. Отличие от Z. chrysops и E. frantzii по памяти.
- poecilotriccus-sylvia — голос («сухая квакающая трель», «тик») по памяти.
- pogonotriccus-ophthalmicus — вся карточка: окраска (мраморное лицо, чёрный полумесяц за щекой, серая шапочка, желтоватые полосы на крыле), поведение (сидит горизонтально, в смешанных стаях), голос. Высоты 800–2 400 м только по data.
- poecilotriccus-calopterus — «ниже на крыле ярко-жёлтые полосы»: по Wikipedia средние кроющие жёлтые и «видны как две полосы»; проверить формулировку.
- ardea-cocoi — «чёрный хохол с затылка» и «чёрная шапка до уровня глаза» по Wikipedia en; голос «низкое хриплое карканье» — Wikipedia говорит «deep croak».
- theristicus-caudatus — предположение, что птицы у Эль-Энканто и Ла-Дримофилы — с пастбищ долины Питалито. Голос по памяти. Высоты «до 2 000 м» — по data (max_extreme 2 000).
- tigrisoma-fasciatum — высоты противоречат: data 300–2 200 м (экстремум 3 300), Wikipedia en «от уровня моря до 730 м». В карточке «по данным проекта примерно от 300 до 2 200 м»; проверить для Колумбии.
- ardea-herodias — «в Колумбии держится в основном на побережьях и в низинах», «в октябре мигранты только прилетают» — по памяти.
- porzana-carolina — сроки пребывания в Колумбии («в основном в северную зиму», первые мигранты в начале октября) по памяти; максимальная высота 4 080 м из data.
- pilherodius-pileatus — голос («обычно молчит») по памяти.
- butorides-virescens — промежуточные особи virescens × striata в Панаме и Колумбии — по памяти; «прилетают осенью, в основном на побережья и в мангры» — по памяти.
- egretta-rufescens — статус на тихоокеанском побережье Колумбии («по-видимому, редка») по памяти; ACO даёт «Residente», высоты 0–50 м. Wikipedia en не упоминает Южную Америку вовсе.
- trogon-curucui — «в Путумайо его отмечают и в предгорьях» — вывод из site_species (Исла-Эскондида 650–1 600 м, Финка Дискосура 800–1 000 м) и data (до 1 750 м); Wikipedia: на севере ареала редко выше 500 м.
- trogon-chionurus — рисунок хвоста самки («неясные чёрно-белые полоски») по Wikipedia en; отличие от T. massena по памяти.
- trogon-massena — «в Колумбии до 1 100 м» по Wikipedia; data даёт до 1 400 м.
- monasa-morphoeus — «местами выше 1 000 м»: Wikipedia даёт до 1 050 м в Перу и 1 350 м в Эквадоре; data max 300, max_extreme 1 350. Исла-Эскондида лежит на 650–1 600 м — проверить, реальны ли записи.
- nystalus-obamai — год и обстоятельства описания вида не указаны (по памяти описан в HBW Special Volume 2013); проверить формулировку «выделена в отдельный вид недавно».
- chloroceryle-inda — голос по памяти; «хохол лохматый» по Wikipedia («somewhat shaggy crest»).
- galbula-ruficauda — как вид с потолком ~1 300 м попадает в Чикаке (2 000–2 700 м): предположены записи с тёплых склонов ниже в радиусе 7 км. Подвид у Чикаке не указан. Отличие от G. pastazae и G. tombacea — по их карточкам (виды не пересекаются с ruficauda на маршруте).
- odontophorus-gujanensis — голос обобщён («дуэт звучных фраз»), по памяти.
- penelope-jacquacu — «белые каёмки и пестрины на шее и груди», сизая кожа у глаза, красноватые ноги — по памяти (Wikipedia описывает только общий цвет). Какой подвид в Путумайо.
- pipile-cumanensis — вся карточка по памяти: белый хохол, голубая серёжка, белое пятно на крыле, красные ноги, свисты-«дудочки», треск крыльев; высоты по data (до 1 000–1 100 м).
- aburria-aburri — цвет серёжки («красная и жёлтая», какая часть какого цвета) и клюва («голубой с тёмным концом») — по Wikipedia en кратко; цвет ног «телесный» по Wikipedia. Голос по памяти.
- odontophorus-erythrops — «в некоторых лоджах приходят к зерну» по Wikipedia (без указания лоджей); на лоджах маршрута кормушек с зерном для перепелов не подтверждено, поэтому `feeder` не поставлен.

## Data issues

- nystalus-obamai — в data/species/nystalus-obamai.json `elevation_m.min` = "L" (строка вместо числа).
- butorides-virescens — в data/species/butorides-virescens.json `elevation_m.max` = "M" (строка вместо числа).
- myiotheretes-fumigatus — `habitat_aco` = "Riverine", хотя это вид горного леса; вероятно, ошибка маппинга ACO.
- poecilotriccus-sylvia, myiopagis-viridicata, galbula-ruficauda — «maybe» в Чикаке (2 000–2 700 м) при потолке вида 1 100–1 800 м; вероятно, записи из долины в радиусе 7 км. Стоит проверить радиус/высотный фильтр для Чикаке.
- mecocerculus-poecilocercus — «maybe» в Чингасе (3 000–3 500 м) выше обычного потолка вида (2 800 м, экстремум 3 050).
- monasa-morphoeus — «maybe» на Исла-Эскондиде (650–1 600 м) при max 300 м (экстремум 1 350) в data.
- aburria-aburri — IUCN: ACO 2022 «NT», BIRDBASE 2024 «LC»; в карточке указан статус ACO.
- tigrisoma-fasciatum — высоты в data (300–2 200 м, экстремум 3 300) сильно расходятся с Wikipedia en (0–730 м).
- pilherodius-pileatus — ru-заголовок Wikipedia «Южноамериканская кваква», а в species_index «Капюшоновая цапля» (eBird); в тексте использовано имя из индекса.
