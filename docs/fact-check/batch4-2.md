# Факт-чек: партия 4, список 2 (тиранны, титира, хищные, совы, голуби, трогон, манакин, олуша, змеешейка)

32 карточки написаны 27.09.2026 по data/species, data/texts (Wikipedia en/es/ru), data/site_species.json и полевым знаниям агента. Ниже то, что стоит проверить по открытым источникам. Формат: `slug — что проверить`.

## Общее

- Голоса почти везде даны по памяти или по выдержкам Wikipedia в пересказе. В выдержках голос описан у: contopus-sordidulus, myiodynastes-chrysocephalus (для южных популяций), glaucidium-brasilianum, herpetotheres-cachinnans (ru), morphnarchus-princeps (ru), patagioenas-subvinacea, patagioenas-speciosa, claravis-pretiosa, leptotila-verreauxi, tapera-naevia, columbina-passerina, trogon-collaris, sula-variegata. Остальные голоса (особенно lophotriccus-pileatus, tityra-inquisitor, piprites-chloris, myiarchus-tuberculifer, buteo-platypterus, strix-albitarsis, circus-cinereus, falco-sparverius, falco-peregrinus, elanoides-forficatus, megascops-choliba, daptrius-ater, ibycter-americanus, accipiter-striatus, rostrhamus-sociabilis, leptotila-rufaxilla, cryptopipo-holochlora, anhinga-anhinga) проверить.
- Размерные классы на границе: lophotriccus-pileatus (8–10 см) поставлен в `hummingbird` по правилу «крошки до 10 см»; myiarchus-tuberculifer (16–18,5 см) — `sparrow`; tapera-naevia (27 см, но 40–50 г и стройная) — `thrush`; trogon-collaris (25–29 см) — `pigeon`, как trogon-comptus; accipiter-striatus (самцы 23–30, самки 29–37 см) — `pigeon`; elanoides-forficatus (50–68 см с хвостом) — `larger`.

## По видам

- lophotriccus-pileatus — голос («сухие стрекочущие трели», «прит») по памяти; окраска подвида squamaecrista (зеленоватые каймы кроющих, более густые пестрины) по Wikipedia en; цвет хохла у squamaecrista (чёрный с рыжими каймами, как у номинативного?) не описан отдельно.
- tityra-inquisitor — какие подвиды на точках маршрута: тихоокеанская сторона (Км 42, Марагрикола) — albitorques? Путумайо — buckleyi или erythrogenys? Описание хвоста в тексте дано обобщённо. Цвет клюва («сизый с тёмным подклювьем») по Wikipedia en. «Самая небольшая из колумбийских титир» — проверить (16,5–20,5 см против T. cayana/semifasciata).
- piprites-chloris — подвид на Исла-Эскондиде (Путумайо): tschudii по описанию ареала «south through eastern Ecuador»; ru-название «Рыжелобая пиприта» из eBird не вяжется с окраской (лоб золотистый/оливковый), в ru Wikipedia «Серошейная пиприта». Голос по памяти.
- contopus-sordidulus — «чаще, чем восточный пиви, встречается высоко в горах» и отличие «чуть светлее и оливковее, подклювье желтее» у C. virens — по памяти; карточка contopus-virens пишет, что западный «чуть темнее и серее», это согласовано, но проверить.
- myiodynastes-chrysocephalus — таксономия: выдержка Wikipedia en описывает Golden-crowned Flycatcher только для Перу (к югу от Мараньона), Боливии и Аргентины, т. е. после разделения вида колумбийские птицы, видимо, относятся к другому виду (Golden-bellied Flycatcher, M. hemichrysus?). В карточке это сказано осторожно («может значиться под другим английским названием»). Проверить по Clements 2025 и при необходимости поправить маппинг (см. «Проблемы данных»). Голос («кии-ю», «кии-чу-ии») по памяти и по описанию южных птиц.
- myiarchus-tuberculifer — «у птиц запада Колумбии шапочка почти чёрная» (подвид nigriceps?) — проверить, какие подвиды на юго-западе и в Путумайо. Отличия от M. cephalotes (беловатые каймы хвоста) и M. ferox (позыв «пррт») по памяти.
- buteo-platypterus — высоты зимовки: ACO 0–1 000 м (крайние до 2 500 м), а по GBIF вид «возможно» в Чикаке, Сибундое и под Боготой (2 000–2 600 м). В тексте: «в основном до 1 000 м, но нередко и выше, до 2 500 м». «В октябре пролёт в разгаре» — проверить сроки. Отличие от Buteo brachyurus по памяти.
- strix-albitarsis — выдержек Wikipedia нет, карточка целиком по памяти: окраска лица (рыжий диск со светлыми бровями), рисунок брюха («крупный светлый узор»), голос («ритмичная серия глухих ху с ударной последней нотой»). Цвет глаз намеренно не указан. Отличия от M. albogularis и S. virgata проверить.
- circus-cinereus — статус в Колумбии («Residente?» по ACO) и регулярность у Ла-Кочи; «хвост один из самых длинных относительно тела» — по Wikipedia en (цифра 44,5 см хвоста выглядит сомнительно). Голос у гнезда по памяти. Отличие самца C. hudsonius по памяти.
- glaucidium-brasilianum — «темп два-три звука в секунду» по памяти.
- falco-sparverius — голос «кли-кли-кли» по памяти; окраска андского оседлого подвида не уточнялась.
- falco-peregrinus — «в Колумбии не гнездится» и «прилетает на зиму с октября» — проверить (ACO: «Migratorio Boreal – Austral?»).
- elanoides-forficatus — доля оседлых и зимующих птиц в Колумбии, голос по памяти.
- herpetotheres-cachinnans — голос «гуа-ко» (по испанскому названию guaco), дуэты — по памяти.
- megascops-choliba — «на тихоокеанском склоне редка или отсутствует» — по Wikipedia en («almost entirely east of the Andes»), для Колумбии проверить (вид есть и в Андах, и в долине Магдалены). Отличие от M. ingens (тёмные глаза) по памяти.
- cathartes-melambrotus — рисунок крыла снизу (тёмные внутренние первостепенные) согласован с карточкой cathartes-aura; отличие от C. burrovianus (светлое поле сверху на крыле) по памяти.
- morphnarchus-princeps — «одна белая полоса на хвосте» по Wikipedia en; «один из самых заметных крупных хищников тихоокеанского склона Нариньо» — оценка.
- daptrius-ater — цвет ног (жёлтые) и голой кожи (оранжево-жёлтая), голос по памяти; отличие от B. urubitinga по памяти.
- ibycter-americanus — цвет ног (красно-оранжевые) и клюва (желтоватый) по памяти.
- accipiter-striatus — окраска андской формы ventralis (изменчивый низ, тёмная морфа) по памяти; принимает ли Clements 2025 Plain-breasted Hawk отдельным видом — проверить. Отличие от Astur bicolor по памяти.
- rostrhamus-sociabilis — отличие от Helicolestes hamatus (светлый глаз, короткий хвост без белого) по памяти; голос по памяти.
- leptotila-rufaxilla — голос («глухое протяжное уууу») по памяти; «у амазонских L. verreauxi кожа у глаза синеватая» — по Wikipedia en (White-tipped dove), проверить для Путумайо.
- patagioenas-subvinacea — ритм песни («ко-КУУ-ку-ку») по Wikipedia en; отличие от P. plumbea согласовано с карточкой patagioenas-plumbea.
- claravis-pretiosa — высоты «в основном до 1 300 м» по ACO; всё остальное по Wikipedia en.
- leptotila-verreauxi — цвет кожи у глаза у колумбийских андских птиц (красный или синий) не уточнён, в карточке «красная или синеватая». В похожих заменена ушастая горлица на толимскую голубку (L. conoveri «точно» в Эль-Энканто и Ла-Дримофиле); формулировка отличия согласована с карточкой leptotila-conoveri.
- patagioenas-speciosa — голос «кро-ку-у» по Wikipedia en.
- tapera-naevia — хозяева-пищухи по Wikipedia en; отличие от Dromococcyx phasianellus по памяти (вида нет на маршруте в data).
- columbina-passerina — «на маршруте встречается нечасто» — оценка по data (только два «возможно»); Чикаке (2 000+ м) для этого вида, вероятно, из окрестностей в радиусе 7 км.
- trogon-collaris — отличие от T. personatus (более тонкая рябь хвоста снизу, маска у самки) по памяти, проверить; какой подвид на тихоокеанском склоне и отличается ли он.
- cryptopipo-holochlora — «довольно длинный для манакина хвост» и голос («гнусавые позывы») по памяти; есть ли вид на тихоокеанском склоне (подвид litae) — по Wikipedia en он только на восточном склоне.
- sula-variegata — «чаще в годы, когда у берегов Перу мало рыбы» (Эль-Ниньо) по памяти; бурые пятна на бёдрах по памяти.
- anhinga-anhinga — голос по памяти; вершина хвоста «палевая» по памяти.

## Проблемы данных

- myiodynastes-chrysocephalus — английское имя и Wikipedia-статья «Golden-crowned flycatcher» теперь описывают только южные популяции (Перу–Аргентина); колумбийские птицы после разделения, вероятно, другой вид по Clements 2025. Проверить маппинг ACO → eBird в pipeline/mappings/aco_to_ebird.json и тексты в data/texts.
- buteo-platypterus — ACO даёт 0–1 000 м, что расходится с регулярными наблюдениями в Андах (Чикаке, Сибундой, Богота, 2 000–2 600 м по GBIF).
- sula-variegata — статус «vagrant» (Errática), но в site_species «возможно» в Тумако и на Плайя-дель-Морро (freq_aut 0,006): возможно, завышено из-за единичных залётов или ошибочных определений.
- piprites-chloris — ru-имя «Рыжелобая пиприта» (name_ru_source: ebird) не соответствует окраске; в ru Wikipedia «Серошейная пиприта».
- megascops-choliba — «возможно» в Обсерватории колибри (под Боготой, ~3 000 м) при верхней границе ACO 2 800 м; скорее всего, наблюдения из более низких окрестностей.
- cryptopipo-holochlora — elevation min в data = 'L' (строка вместо числа), так же в индексе (`elev: ['L', 1200]`).
- strix-albitarsis — нет data/texts (Wikipedia не скачана).
