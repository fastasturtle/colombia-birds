# TODO

Статус на 2026-09-27. Закрытые пункты помечаем `[x]`, не удаляем.

## База данных
- [x] Список видов ACO 2022, статусы, биотопы, IUCN (`pipeline/steps/fetch_aco.py`)
- [x] Имена ru/en/es и коды eBird, сопоставление ACO ↔ Clements (4 ручных маппинга)
- [x] Признаки BIRDBASE: высоты, биотопы, масса, диета, миграция
- [x] Wikidata: QID, внешние ID, категории Commons, ссылки на статьи Wikipedia
- [x] Сборка `data/species/*.json`, индекса и семейств
- [x] Выдержки Wikipedia en/es/ru для всех видов (27.09: en 1901, es 1898, ru 980)
- [x] Ранжирование фото: чистка авторов, дубликаты, гравюры последними и не больше одной, зоопарки/музеи ниже диких
- [x] Фото: шаги `photos` (кандидаты Commons + iNat) и `upload` (ресайз, R2, credits) написаны; Commons проверен только на моках
- [x] Первый запуск фото в GitHub Actions (27.09): 1926 видов с фото, 2667 файлов (231 вид с 4 фото); Commons отвечает из CI
- [x] Таксономия/маппинги по итогам факт-чека 125 карточек (27.09), проверить против Clements/eBird 2025 и перемапить: Whimbrel → *Numenius hudsonicus* (Hudsonian, сплит 2025); Choco Warbler *Myiothlypis chlorophrys* слит в chrysogaster (gbif_to_species.json); Longuemare's Sunangel *Heliangelus clarisse* (eBird amtsun2, в данных amtsun3, без ru); Yellow-tufted Dacnis *D. egregia* нет в индексе, записи Км 42/Марагрикола идут в lineata; Ecuadorian Rail *Rallus aequatorialis* (IOC сплит; проверить eBird virrai1); Cabot's Tern *Thalasseus acuflavidus*; Boyacá Antpitta *Grallaria alticola* (IOC 2023, Сумапас/Чингаса); ACO-имена перепутаны у grallaria-saturata («Perijá Antpitta») и grallaria-saltuensis — сделано 27.09 (DECISIONS 19): ремапы в `aco_to_ebird.json` (hudsonicus, clarisse, chlorophrys, crassus, aequatorialis), новые виды `source: clements2025` в `pipeline/mappings/clements2025.json` (dacnis-egregia, grallaria-alticola), GBIF-сплиты по регионам (`gbif_region_splits.json`), имена ACO saturata/saltuensis (`aco_fixes.json`); Cabot's Tern в Clements 2025 не выделен, данные не менялись
- [x] Русские имена в данных: опечатки «Коричневохвотсая которра» (pyrrhura-melanura), «Коричневогруая которра» (pyrrhura-calliptera); строчная «масковый дакнис»; null у atlapetes-schistaceus, grallaria-saturata/saltuensis/quitensis/alvarezi, dubusia-taeniata, tephrophilus-wetmorei; ru-статья Wikipedia у phaethornis-yaruqui не про него — сделано 27.09: `pipeline/mappings/names_ru_overrides.json` + нормализация в build (заглавная буква, латиница → null); у перечисленных видов статей ru.wikipedia с русским заголовком нет, остались null (phaethornis-yaruqui не смотрели)
- [ ] После таксономических ремапов 27.09 перезапустить в CI: `ebird wikidata build` (все), `gbif_sites sites study` (light), `wikipedia photos upload` для numenius-hudsonicus heliangelus-clarisse myiothlypis-chlorophrys atlapetes-crassus rallus-aequatorialis dacnis-egregia grallaria-alticola; затем убрать `renamed` из `clements2025.json` и осиротевшие data/{photos,texts,credits}/<старый слаг>.json
- [ ] Карточки content/species для новых видов dacnis-egregia (Км 42, Марагрикола) и grallaria-alticola (Чингаса, Сумапас)
- [ ] Аудит других ACO-видов, у которых eBird 2025 после сплита оставил имя за внеколумбийской половиной (en eBird с «Northern/Southern/Western/Atlantic/Mangrove…»): troglodytes-aedon (в Колумбии T. musculus), tyto-alba (T. furcata), xenops-minutus (X. genibarbis/mexicanus), formicivora-grisea (F. intermedia), setophaga-petechia, oxyura-jamaicensis (O. ferruginea), mionectes-olivaceus (M. galbinus), chlorothraupis-carmioli (C. frenata), lophornis-chalybeus (L. verreauxii), zimmerius-chrysops, cyphorhinus-thoracicus, trogon-rufus/ramonianus, contopus-cinereus, rhynchocyclus-olivaceus, automolus-subulatus, gygis-alba, ardea-ibis; часть уже видна в gbif_to_species.json и lynx_names.json
- [ ] Высоты BIRDBASE, неверные для Колумбии (в карточках уже поправлено словами): turdus-ignobilis низ 900 м (низинная форма debilis), oxyura-jamaicensis верх 2200 м (андские формы 2500–3000+), vanellus-chilensis верх 1200 м («точно» на 2600–2800), geospizopsis-unicolor низ 800 м, oxypogon-guerinii верх 5200 м
- [ ] Статус: ACO 2022 vs текущий IUCN расходятся (doliornis-remseni VU/NT, vireo-masteri EN/NT, leptotila-conoveri EN/NT/VU) — решить, что показывать; geranoaetus-polyosoma «Migratorio Austral», а нариньские птицы оседлые
- [ ] Нет data/texts для ardea-ibis (статья теперь «Western cattle egret»), saucerottia-saucerottei, dubusia-taeniata, tephrophilus-wetmorei — проверить шаг wikipedia
- [ ] В `similar` есть виды не с маршрута (pardirallus-nigricans ×2, Gray-chested Dove у leptotila-pallida, Mourning Warbler у pseudocolopteryx) — заменить на маршрутные; согласовать цвет хвоста Bronze-tailed Thornbill между oxypogon-guerinii и chalcostigma-heteropogon; `feeder` у видов Обсерватории/El Encanto не подтверждён
- [ ] Проверить маппинги ACO↔eBird/GBIF, найденные при написании карточек (batch 1): «Whimbrel» → Numenius phaeopus, а в Колумбии зимует N. hudsonicus; Choco Warbler (Myiothlypis chlorophrys) сведён в myiothlypis-chrysogaster (Cuzco Warbler); Dacnis на Км 42 скорее D. egregia, а не lineata; grallaria-saturata в ACO как «Perijá Antpitta»; опечатка ru «Коричневохвотсая которра» у Pyrrhura melanura/calliptera; ru-статья Wikipedia у phaethornis-yaruqui не про него; верх высот oxypogon-guerinii 5200 м (Wikipedia 4200); низ turdus-ignobilis 900 м при «точно» в низинах; статус CR у pseudocolopteryx-acutipennis
- [ ] В data/species нет длины тела (только масса) — добавить длину (AVONET/Wikipedia) для разметки `size` в карточках
- [x] Русские названия семейств из Wikidata (QLever), шаг `family_names` → `data/families.json` (85 из 94; без ru 9: Oceanitidae, Semnornithidae, Sapayoidae, Oxyruncidae, Onychorhynchidae, Donacobiidae, Rhodinocichlidae, Passerellidae, Mitrospingidae — показываем английское)
- [x] `build` больше не стирает `photos`/`texts`/`sounds` в `data/species/*.json` и `photo` в индексе
- [ ] Данные по итогам факт-чека партии 2 (27.09): tunchiornis-ochraceiceps — амазонские записи (Isla Escondida) это Rufous-fronted Greenlet *T. ferrugineifrons*, нет в индексе (следующая таксономическая волна); `elevation_m.min` строка «L» у cephalopterus-ornatus, tangara-schrankii, selenidera-reinwardtii, galbalcyrhynchus-leucotis, monasa-flavirostris, galbula-tombacea (починить парсер BIRDBASE); масса pulsatrix-melanota 82 г (реально 590–1250); поле `iucn` в индексе берёт статус ACO 2022 и показывается как IUCN (phlogophilus-hemileucurus VU vs IUCN LC; grallaricula-cucullata VU/NT) — развести «ACO/Libro Rojo» и «IUCN»; ru-опечатка «Золотошейний туканчик» (selenidera-reinwardtii); `names.en_aco` с битой кодировкой «NariÒo Tapaculo» (scytalopus-vicinior); names.en «Amazonian Violaceous Trogon» vs «Amazonian Trogon» (trogon-ramonianus); сомнительные ru: «Перуанская неясыть» (pulsatrix), «Каштановоухая танагра» (chlorochrysa-calliparaea, ru-wiki «Оранжевоухая»), «Коронадо» (metopothrix); null ru: tangara-xanthocephala, coeligena-bonapartei (ещё и эндемик по Wikipedia, а в данных почти-эндемик)
- [ ] GBIF-радиус 7 км захватывает низины у предгорных точек: Finca Discosura (celeus-flavus, metopothrix, picumnus-squamulatus), Isla Escondida (mitu-salvini, cotinga-cayana, pharomachrus-pavoninus, trogon-ramonianus) — подумать про фильтр по высоте вида при расчёте состояний
- [ ] Портреты семейств/групп противоречат site_species: grallariidae (Bicolored Antpitta в Сибундое — «вряд ли»), parrots (Mealy Amazon в Орито), trogonidae (Amazonian Trogon в Playa Rica), thamnophilidae (sipia-berlepschi в Bangsias) — прогнать /fact-check content/families content/groups с проверкой точек
- [ ] Данные по флагам волны 3 карточек (27.09): маппинг Pacific Hornero *Furnarius cinnamomeus* (Тумако) vs furnarius-leucopus; Giant Hummingbird сплит — колумбийские птицы *Patagona peruviana*, в данных старый код giahum1 и нет записей site_species; Tropical Pewee ACO → contopus-cinereus (Southern), для Колумбии скорее другой сплит; polioptila-plumbea на побережье — группа bilineata (проверить сплит); ru-опечатки «Уккрашенная курэта» (myiotriccus-ornatus), «Рыжспинный» (patagioenas-cayennensis); ru «Желтоклювая пиайя» у coccyzus-americanus (имя другого рода); null ru у piaya-cayana, ochthoeca-cinnamomeiventris, furnarius-leucopus, cnemoscopus-rubrirostris, butorides-striata, dacnis-egregia, grallaria-alticola; нет data/texts у sporathraupis-cyanocephala (смена рода), vireo-olivaceus, cercomacroides-fuscicauda, grallaria-rufula, ochthoeca-cinnamomeiventris, chrysuronia-goudoti, cnemoscopus-rubrirostris, butorides-striata; фото grallaria-rufula — эквадорская форма комплекса; near_endemic=true сомнителен у cinnycerthia-unirufa, pionus-chalcopterus; habitat «Marine» у jacana-jacana и eurypyga-helias, «Coastal» у psophia-crepitans; dacnis-berlepschi VU → LC (2025); coragyps-atratus/fulica-americana/elanus-leucurus/plegadis-falcinellus: max высоты BIRDBASE ниже боготских точек
- [ ] `data/sites.json` target_species_raw расходятся с GBIF: Torrent Duck как цель Ла-Кочи (река, не озеро; sci null), Large-headed Flatbill в El Encanto, Silvery Grebe, Buff-throated Tody-Tyrant, Sapphire Quail-Dove/Gray-winged Trumpeter/Black Tinamou (Isla Escondida, Trampolín), Ladder-tailed Nightjar (Playa Rica), thorntails и Coppery-chested Jacamar, touit-huetii (El Escondite), odontorchilus-branickii (Trampolín), zimmerius-albigularis (Bangsias, нет записей после сплита) — решить, показывать ли цели без записей отдельно («по отчётам гидов»)
- [ ] Перелётные виды в определителе: piranga-olivacea и другие северные мигранты осенью в неброском наряде — правило для `colors` (осенний наряд, а не брачный) записать в README после ревизии словаря
- [ ] Русские имена для 63 видов без имени в eBird/Wikidata (IOC Multilingual как fallback)
- [ ] Эндемики и почти-эндемики из Chaparro-Herrera 2024 (CC BY-NC) → поле `near_endemic`
- [ ] AVONET: длина клюва/крыла/хвоста для сравнения похожих видов
- [ ] GBIF: присутствие вида по департаментам маршрута → «вероятность встречи» по регионам
- [ ] xeno-canto: список записей на вид (нужен ключ в Secrets, уже есть)
- [ ] Тексты из PD-источников (Chapman 1917, Todd & Carriker 1922) как «исторические заметки»
- [ ] SiB Colombia fichas (CC BY-NC) для испанских описаний

## Маршрут
- [x] Разведка 20 локаций + Chicaque: координаты, высоты, хотспоты, целевые виды
- [x] `data/sites.json` (27 локаций), `data/itinerary.json` (25 дней), `data/regions.json`, шаг `sites` → 274 фокусных вида
- [ ] Red-winged Wood-Rail (Isla Escondida) нет в списке ACO — проверить, добавить как «вне списка»
- [ ] Дни 1–2 октября (Богота) без локаций: решить, куда едем (Chingaza? La Florida? Observatorio de Colibríes?)
- [x] Проверить все ID хотспотов eBird через API: шаг `hotspots`, отчёт `docs/research/hotspots-check.md`; исправлены Sumapaz, El Escondite, Orito, Km 42, La Nutria (ID удалён, рядом только Río Ñambí), добавлены ID для El Encanto, Discosura, Puerto Asís, Maragrícola, Tumaco
- [ ] La Nutria: найти настоящий хотспот (записанный L5632537 в 230 км); El Escondite: уточнить координаты (хотспот в 15 км)
- [ ] Найти хотспоты El Encanto, Finca Discosura, Km 42, Finca Maragrícola
- [ ] Manakin Nature Tours PDF «Macizo, Amazon & Pacific Foothills 2026» — вытащить список видов

## Контент
- [x] Портреты семейств: 57 семейств с видами маршрута (ru + en)
- [x] Портреты 18 групп
- [ ] `/fact-check content/families content/groups`: агенты сами пометили факты из памяти — размеры клюва Hook-billed Kite, появление Glossy Ibis в Америках в XIX в., «два вида» у Semnornithidae, аукцион имени Chocó Vireo, эпоним Пола Шварца, перелёт Blackpoll Warbler 2 500 км
- [ ] Русские названия семейств без метки в Wikidata: Semnornithidae, Donacobiidae, Passerellidae и ещё 6 — принять варианты агентов или подобрать
- [x] Карточки видов, партия 1 (27.09): 100 видов «точно» на маршруте, 88 фокусных, 4 агента (docs/fact-check/batch1-*.md — 110 флагов)
- [x] `/fact-check content/species` партия 1: все 125 карточек проверены 27.09 (8 агентов, логи docs/fact-check/log-2026-09-27-*.md, ~2–3 мин/карточка)
- [ ] `/fact-check content/species` партия 2 после написания; старые флаги: в первую очередь голоса (Gilded Barbet, Yellow-throated Toucan, колибри), отличия похожих видов из памяти, андские подвиды пастушков и уток
  - [x] Пилот 27.09: 10 карточек (docs/fact-check-log.md). Учёт — поле `checked:` в карточке, указатель `docs/fact-check/INDEX.md` (`python3 scripts/card_index.py`, перезапускать после каждой партии)
- [ ] Карточки видов, партии 2+: всего кандидатов 973 (точно 291 + возможно 635 + фокус); решить объём («точно + фокус» ≈ 340 или все) после ревью партии 1
- [ ] В карточках видов точек под Боготой (Chingaza, Sumapaz, La Florida, Observatorio de Colibríes) написано «свободные дни 1–2 / 25 октября» — поправить, когда решим, куда едем
- [ ] Ревизия словаря признаков после партии 2 (~225 карточек): собрать все пожелания агентов и пограничные случаи, добавить значения разом, затем проход переразметки по всем карточкам (правило в content/README.md)
- [ ] Пограничные размеры в `size`: правило для длиннохвостых (Asthenes fuliginosa 18–20 см, половина хвост) и крошек (Club-winged Manakin 9,5–10 см) — зафиксировать в README
- [ ] Портреты остальных 37 семейств без видов маршрута (низкий приоритет)

## Сайт
- [x] Кнопка «сообщить об ошибке»: `worker/` + `.github/workflows/worker.yml` + `site/src/components/ReportButton.svelte` (скилл `.claude/skills/error-reports`)
  - [x] Интеграция с книгой Lynx «Birds of Colombia» (Hilty 2021): указатель, литература и индекс семейств транскрибированы в `pipeline/sources/lynx/`, шаг `lynx` → `data/lynx_pages.json`, страница показана на карточке вида и семейства
  - [ ] Lynx: 20 видов без страницы (`data/sources/lynx_report.md`, раздел Unmatched) — по фото указателя их в книге нет (залётные, интродуценты, Thinocoridae, свежие сплиты: Great-billed / Black-billed Seed-Finch, Stripe-cheeked Woodpecker и др.); *Myiopagis caniceps* — книга делит на Amazonian (386) и Choco Grey Elaenia (387), выбрать. Проверить `aco_to_ebird` для *Contopus cinereus* и *Myiopagis caniceps*
  - [ ] Lynx: 3 конфликта страниц — так напечатано в книге (Masked Trogon 202/203, Amazonian Antshrike 275/276, Black-collared Jay 423/422), берём латинскую
  - [ ] Lynx: при случае досфотографировать с. 592–604 (испанский указатель, указатель групп) и с. 558
- [x] Фото на весь экран по тапу (лайтбокс, свайп, Esc), к источнику только по явной ссылке
- [x] Каркас Astro 7 + Svelte: семейства, список видов с поиском и фильтрами, карточка вида, маршрут с картой и профилем высот
- [ ] Деплой на GitHub Pages (workflow готов, нужно: Settings → Pages → Source = GitHub Actions, слить в main)
- [ ] Показ фото из R2 (после загрузки)
- [ ] Полный офлайн (PWA): service worker с манифестом при сборке; ядро (все страницы + миниатюры, ~70 МБ) кэшируется само; кнопки «скачать день» (страницы видов дня, средние фото, портреты семейств, ~15–20 МБ/день) и «скачать весь тур»; баннер «добавить на экран Домой» для iPhone (иначе Safari чистит кэш); обновление по разнице хэшей манифеста; страница «Офлайн» со статусом: сколько файлов/МБ скачано и осталось, дата последнего обновления, кнопки «скачать весь тур» / «остановить», индикатор прогресса через сообщения от service worker. Делать после фото/текстов и переделки страниц дня. Решено: Дима на iPhone (Safari, обязательно «на экран Домой»), Аня на Android; места готовы отдать до 1 ГБ → кэшировать ядро + средние фото всех видов маршрута, «весь тур» одной кнопкой
- [ ] Ареал вида на нашей SVG-карте. Данные найдены: Vélez et al. 2021 (CC BY 4.0), шейпфайл `BIRD_Colombia.7z` (22 МБ) с GeoNetwork Института Гумбольдта, запись `5c2b19d2-6893-4955-aa65-509d1c3f2706`, URL через `/geonetwork/srv/api/records/<uuid>/attachments`; 1 889 полигонов, имена по Ayerbe-Quiñones 2019 → 1 833 наших видов совпадают, 133 нужна таблица синонимов. План: шаг `ranges` (py7zr + pyshp + shapely): клип по bbox подложки, упрощение 0.01–0.02°, проекция как в basemap, `data/ranges/<slug>.json` с path `d`, ленивая загрузка на карточке вида. Второй слой: GBIF `facet=gadmLevel1Gid` (нужны полигоны департаментов с ключами GADM в basemap)
- [ ] Страница региона: виды по высотному поясу и биотопу
- [ ] Определитель по признакам: семейство × регион × высота × биотоп × размер
- [ ] Страницы «похожие виды» из `content/similar/`
- [ ] Портреты семейств (что это за семейство, как узнать, поведение) — тексты агентами
- [ ] Русские описания видов из `content/species/` (сначала фокусные виды маршрута)
- [ ] Практическая страница: погода по дням, одежда, логистика (из чата группы)
- [ ] Страница credits со всеми авторами фото и текстов
- [ ] Тёмная тема: проверить контраст карты и чипов
- [ ] Глобальный переключатель RU/EN на весь сайт (строки интерфейса, порядок названий, en-версии контента) — после фото и текстов. В данных имена унифицированы (`names.en/ru/es` + латынь у видов, семейств, групп); разнобой только в шаблонах: виды показывают английское первым (как Merlin/гид), семейства и группы русское. Тумблер должен задавать единый порядок «основное имя / второе имя» везде
- [ ] Квиз «угадай птицу» (после фото)
- [ ] «Увидели»: без бота. Страница, куда владелец загружает CSV-экспорт из My eBird (виды + даты); список хранится в браузере (localStorage), опционально экспорт/импорт JSON между телефонами. В списках дней и локаций увиденные виды серые/свёрнутые, страница «Увидели» со счётчиком. Решено владельцем 27.09
- [ ] Словарь бёрдерского английского: выписать 100–200 частых, но нетривиальных слов (уровень A2+) из английских названий видов и описаний (chestnut, rufous, rumped, crest, mantle, wing-bars, undertail, buff, streaked…) с русским переводом и примерами видов; посчитать частоты по `data/species_index.json` (названия) и `data/texts/*.json` (описания); страница «Словарь» + режим карточек для заучивания

## Как продолжать в новой сессии
Спросить «что осталось» → этот файл. Правила → `AGENTS.md`. Решения → `docs/DECISIONS.md`. Источники → `docs/research/`.

## Инфраструктура
- [ ] `upload_media.py`: писать прогресс в лог (каждые 25 видов: обработано/всего, загружено файлов, МБ) и записывать `data/` инкрементально (каждые 100 видов), а workflow коммитить промежуточные результаты по ходу, чтобы фото появлялись на сайте до конца многочасового прогона; делать после окончания текущего прогона
- [x] Правило изюминок (теперь «интересные») в `build_study_lists.py`: цели из отчётов больше не выкидываются, без осенних находок GBIF они «вряд ли» + ★ (см. DECISIONS #18)
- [x] Секреты в GitHub, бакет R2 `colombia-birds`, публичный URL r2.dev
- [ ] CORS на бакете: origins `https://fastasturtle.github.io`, `http://localhost:4321`, методы GET/HEAD
- [ ] Свой домен для медиа вместо r2.dev (когда появится домен в Cloudflare)
- [x] Workflow `pipeline.yml` (workflow_dispatch, steps + only)
- [x] Первый запуск в Actions на 10 видах: тексты, фото, R2, страница на сайте проверены
- [ ] Полный прогон `wikipedia photos upload` на все виды (запущен 27.09, run 36314149564), затем повторный `photos upload` для 275 видов маршрута на исправленном ранжировании (run 36314663291)
- [x] Автодеплой после коммитов пайплайна (`actions: write` + `gh workflow run deploy.yml`); прогоны, запущенные до этого изменения, деплоим вручную
- [ ] Кэш HTTP-ответов в Actions может пропасть при таймауте прогона; тогда Commons/iNat опрашиваются заново
- [ ] `XENO_CANTO_API_KEY` приходит в job пустым: проверить имя секрета в репозитории
- [ ] У части лицензий Commons в `license_url` нет завершающего слэша
- [ ] Скиллы для агентов: `/write-species-text`, `/add-similar-pair`, `/fetch-photos`
