# Факт-чек: партия 3, список 1 (танагры, цветоколы, семеноеды, манакин, котинга)

Карточки написаны 27.09.2026 по data/species, data/texts (Wikipedia en/es/ru) и полевым знаниям агента.
Ниже то, что стоит проверить по открытым источникам перед публикацией. Формат: `slug — что проверить`.

## Общее

- Кормушки (`feeder` в `layer`) поставлены по общему знанию, что вид регулярно ходит на фруктовые (или, у кареба, на нектарные) кормушки в лоджах северных Анд, без проверки конкретных лоджей маршрута: ramphocelus-flammigerus, ramphocelus-carbo, ramphocelus-dimidiatus, tangara-icterocephala, saltator-maximus, saltator-atripennis, coereba-flaveola, stilpnia-larvata, tangara-gyrola, sporathraupis-cyanocephala. Проверить, есть ли фруктовые кормушки в Ла-Планаде, на Авес-и-Флорес, в Эль-Энканто, Финке Дискосура, на Трамплине птиц. Не поставлены, но возможны: diglossa-humeralis/albilatera (нектарные кормушки), cyanerpes-caeruleus, tachyphonus-rufus, tangara-mexicana, sicalis-flaveola (рис/зерно).
- Голоса почти везде даны обобщённо по памяти (в выдержках Wikipedia голос описан только у humeralis, icterocephala, gyrola, mexicana, tachyphonus-rufus, sporophila-corvina, piranga-rubra, manacus-manacus). Особенно проверить: anisognathus-lacrymosus, ramphocelus-carbo, ramphocelus-dimidiatus, ramphocelus-flammigerus, saltator-maximus, saltator-atripennis, diglossa-albilatera, diglossa-caerulescens, diglossa-sittoides, sporophila-luctuosa, sicalis-luteola, catamenia-inornata, conirostrum-sitticolor, sporathraupis-cyanocephala, ampelioides-tschudii («нарастающий свист»), piranga-olivacea («чип-бурр»), volatinia-jacarina («и-дзип»).

## По видам

- diglossa-humeralis — окраска подвидов по Wikipedia en: humeralis (Восточные Анды) с голубоватым плечом и серой поясницей, aterrima (юг Колумбии) целиком чёрный. Проверить, какой подвид на Ла-Коче/Бордонсильо (Нариньо) — aterrima?
- ramphocelus-flammigerus — ключевое: какой подвид на тихоокеанском склоне Нариньо. В карточке icteronotus (жёлтая поясница) и «красные птицы в долине Каука, на маршруте, скорее всего, не встретятся». Проверить ареал номинативного подвида (Wikipedia: «relatively restricted range in Colombia», текст обрезан) и зону интерградации. Окраска самки icteronotus («серовато-бурая сверху, поясница и низ жёлтые») — по обрезанной выдержке Wikipedia. Cacicus uropygialis как похожий вид: в индексе «Scarlet-rumped Cacique» с высотами 1 500–2 450 м (субтропическая форма) — проверить, что описание (светлый клюв, алая поясница) верно для этой формы.
- anisognathus-lacrymosus — подвид юга Колумбии и его окраска (синеватое плечо, «жёлтое пятнышко на боку шеи»): описание по памяти.
- piranga-rubra — «первые птицы прилетают осенью, к туру уже на месте» — сроки прилёта в Колумбию (сентябрь?) проверить. Позыв «пи-ти-тук» — по памяти.
- piranga-olivacea — «птицы прилетают в октябре» по Wikipedia (пролёт через Центральную Америку около октября). colors выбраны по осеннему наряду, который видно на маршруте ([olive, yellow, black]), а не по брачному алому; решить, как размечать мигрантов в определителе. Отличие от piranga-flava (тёмно-серый клюв, серые щёки) по памяти.
- piranga-flava — в индексе высоты null; в Южной Америке эта форма часто выделяется как Tooth-billed Tanager (P. lutea). Проверить, корректно ли сравнение.
- ramphocelus-carbo — «на тихоокеанском склоне его нет» (по Wikipedia: восточнее Анд). Размер 16–17 см поставлен в `sparrow` (граница 16/17 см), как и у ramphocelus-dimidiatus (16 см); flammigerus 18 см — `thrush`.
- sporophila-corvina — окраска самца подвида ophthalmica (юго-запад Колумбии) дана по памяти: «верх чёрный, низ белый, поперёк груди чёрная полоса, иногда разорванная; светлая поясница; белое на шее». Карточка sporophila-telasco (партия ранее) описывает ophthalmica как «чёрный сверху, снизу и на горле белый, с белой поясницей» без грудной полосы — проверить по источнику и согласовать обе карточки. Цвет самки («желтоватее снизу») по памяти.
- sporophila-luctuosa — в похожих указан S. corvina с «белым на шее» — зависит от проверки ophthalmica выше.
- diglossa-albilatera — голос («тонкая сухая трель») по памяти.
- tangara-icterocephala — посещение фруктовых кормушек на лоджах маршрута не подтверждено (см. Общее).
- saltator-maximus — голос («похожая на песню дрозда») по памяти.
- coereba-flaveola — colors [gray, yellow, white]: у колумбийских птиц верх может выглядеть почти чёрным; пограничный выбор.
- sicalis-flaveola — «точно» в Чикаке по data (облачный лес ~2 000+ м, вид в основном до 1 000 м): вероятно, наблюдения из окрестностей в радиусе 7 км. Проверить формулировку.
- ramphocelus-dimidiatus — подвид molochinus в верхней Магдалене (Wikipedia); его отличия от номинативного не описаны. Окраска самки и цвет её клюва по памяти.
- tangara-schrankii — похожий вид ixothraupis-xanthogastra (мельче, крапчатая) по памяти; голос по памяти.
- cyanerpes-caeruleus — отличие от C. nitidus («ноги розоватые, чёрное горло переходит на грудь») и от dacnis-cayana по памяти.
- saltator-atripennis — голос по памяти.
- stilpnia-larvata — «точно» в Ла-Планаде (~1 800 м) при высотах вида до 1 100 м (редко 1 800) — радиус выборки GBIF, проверить.
- sicalis-luteola — «поёт на лету» и цвет клюва по памяти.
- cissopis-leverianus — «нижний край чёрного на груди зубчатый» и «глаз ярко-жёлтый» по памяти.
- sporathraupis-cyanocephala — текста Wikipedia в data/texts нет, карточка целиком по data/species и памяти. Проверить: чёрное лицо, серый с голубым низ, жёлтые бёдра и подбой крыла, голос, посещение кормушек.
- tangara-gyrola — окраска низа у подвидов маршрута (Уила, Путумайо, Нариньо): «зелёное или бирюзово-голубое» — формулировка обтекаемая; золотистый ошейник «у части подвидов» — проверить.
- volatinia-jacarina — токовый прыжок и позыв по памяти.
- tachyphonus-rufus — «белое пятнышко на сгибе крыла» по Wikipedia («small white patch on the upperwing»).
- diglossa-sittoides — «в Боготе встречается в парках» по data (Ботанический сад — «точно»). Окраска самки по памяти.
- tangara-nigroviridis — «серебристый блеск на голове» по памяти.
- catamenia-inornata — «спина с тёмными пестринами», «клюв розоватый», отличия от C. analis (жёлтый клюв) и C. homochroa по памяти; согласовано с карточкой geospizopsis-unicolor.
- conirostrum-sitticolor — подвид Центральных/Восточных Анд и Нариньо: номинативный (чёрная голова и крылья) по Wikipedia en; ru-статья упоминает четыре подвида, en — три.
- manacus-manacus — окраска самца тихоокеанского подвида (leucochlamys?): «белое или серовато-белое» — проверить. Похожий вид machaeropterus-deliciosus: самка «без оранжевых ног» не написана, но стоит проверить цвет ног у обоих.
- ampelioides-tschudii — высоты: data 575–2 700 м, Wikipedia 1 000–3 500 м; в карточке «примерно 600–2 700 м, чаще в предгорьях». Светлый глаз, жёлтый ошейник и голос по памяти. difficulty=hard.

## Data issues

- sporathraupis-cyanocephala — нет data/texts (статья en «Blue-capped tanager» существует; вероятно, маппинг не сработал после смены рода Thraupis → Sporathraupis).
- ramphocelus-flammigerus — data: высоты 800–2 000 м, но «точно» на Плайя-дель-Морро и «возможно» в Тумако, на побережье, а icteronotus спускается до уровня моря; нижнюю границу стоит проверить. Русское имя «Красноспинный сереброклюв» не подходит птицам маршрута (у них жёлтая поясница).
- tangara-schrankii, ixothraupis-xanthogastra, ixothraupis-punctata — в data/species_index `elev` содержит строку 'L' вместо числа (нижняя граница «низменности»).
- piranga-flava — в data/species_index `elev` = [null, null].
- dubusia-taeniata — нет `ru` в data/species_index.
- coereba-flaveola — `ru` в индексе содержит два имени через запятую («Банановая кареба, сахарная цветочница»); в карточке использовано первое.
- sicalis-flaveola — «точно» в Чикаке и stilpnia-larvata — «точно» в Ла-Планаде при высотах вида ниже высоты локации: артефакт радиуса 7 км в site_species.json.
