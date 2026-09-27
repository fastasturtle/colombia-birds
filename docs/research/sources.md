# Источники данных: обзор и лицензии

Дата разведки: 2026-09-27. Все утверждения о лицензиях проверены агентами по указанным
ссылкам; перед использованием нового источника лицензию перепроверять.

Принцип: в базу попадает только то, что можно **скопировать и хранить** под лицензией
CC0 / CC BY / CC BY-SA / Public Domain (для текстов также CC BY-NC с пометкой).
Всё остальное — только ссылки.

## 1. Список видов и статусы

| Источник | Что даёт | Лицензия | Как забирать | Роль |
|---|---|---|---|---|
| **ACO «Lista de referencia de especies de aves de Colombia 2022»** (SiB Colombia / GBIF `6c9c4b08-4cec-4160-a708-7f16060d7db0`) | 1 966 таксонов, порядок/семейство, англ. имя, статус (Residente / Endémica / Migratorio Boreal / Austral / Errática / Hipotética), биотоп, IUCN, Libro Rojo | **CC BY 4.0** | Darwin Core Archive (zip из TSV): `https://ipt.biodiversidad.co/sib/archive.do?r=aco_listaavescolombia2017` — файлы `taxon.txt`, `distribution.txt`, `speciesprofile.txt`, `description.txt` | **Канонический список Колумбии** |
| **eBird API v2 taxonomy** | Таксономия Clements 2025, коды видов, имена на языках (`locale=ru` — 10 366 / 11 167 видов с кириллицей; `es_CO`) | Условия eBird (некоммерч., ссылка на Cornell); ключ **не нужен** для `ref/taxonomy` | `https://api.ebird.org/v2/ref/taxonomy/ebird?fmt=json&cat=species&locale=ru` | Коды видов, русские и английские имена, ссылки на eBird |
| **Clements/eBird v2025 CSV** | То же в CSV | Cornell; сайт закрыт Cloudflare для скриптов | скачать вручную, положить в `pipeline/vendor/` | Резерв |
| **IOC World Bird List 15.2, Multilingual** | Имена на 42 языках, включая русский и испанский | Свободно для некоммерч. с цитированием | `https://worldbirdnames.org/Multiling%20IOC%2015.2.xlsx` | Fallback русских имён |
| **AviList v2025b** | Мировая таксономия (объединение IOC/Clements/BirdLife) | CC BY 4.0 | XLSX с `https://www.avilist.org/checklist/v2025b/` | Сверка таксономий |
| **Chaparro-Herrera et al. 2024** (Ornitología Colombiana 25, doi 10.59517/oc.e580) | 87 эндемиков, 202 почти-эндемика (CE 197 + CEa 5, морские/островные), 17 «of interest» (EI), 17 «información insuficiente» (II) | CC BY-NC 4.0 | XLSX-приложения на сайте журнала, скрипт качает напрямую (`view` редиректит на `https://revistas.ornitologiacolombiana.com/index.php/roc/article/download/580/<n>`): виды с категориями — только **Anexo 3** (`/496`); `/493` (Anexo 1) — высотные пояса и регионы, `/494` (Anexo 2) — коды стран. Шаг `endemics` | Эндемики и почти-эндемики (`colombia.near_endemic`) |
| Wikipedia «List of birds of Colombia», «Endemic birds of Colombia» | 2 040 записей с флагами (V)(E)(I)(U) | CC BY-SA 4.0 | MediaWiki API `action=parse` | Сверка |
| SACC country lists (`SACCListByCountry.xlsx`) | Коды X / X(e) / NB / V | Без лицензии, академическое цитирование | не редистрибутировать файл | Сверка |
| Avibase Colombia, BirdLife DataZone, ProAves | Списки, ареалы, статусы | Все права защищены | — | **Только ссылки** |
| **Hilty, S.L. (2021) «Birds of Colombia»**, Lynx Edicions (бумажная книга группы) | Номера страниц видов и семейств из указателя книги; список литературы | Все права защищены; берём только служебные разделы (указатели, литература) с фото владельца, транскрипция в `pipeline/sources/lynx/` | Шаг `lynx` (`pipeline/README.md`) | `lynx_page` на карточках вида и семейства |

## 2. Признаки, высоты, биотопы

| Источник | Что даёт | Лицензия | Как забирать |
|---|---|---|---|
| **BIRDBASE v2025.1** (Şekercioğlu et al. 2025, Sci Data) | 78 признаков на 11 589 видов: мин/макс высота, биотоп, диета, реалм, IUCN, ключи к Clements/IOC/BirdLife/AviList | **CC BY 4.0** | figshare `https://doi.org/10.6084/m9.figshare.27051040` (XLSX 6.7 МБ) |
| **AVONET** (Tobias et al. 2022) | Морфометрия (масса, длина клюва/крыла/хвоста), биотоп, трофическая ниша, миграция | CC BY 4.0 | figshare `16586228` |
| IAvH список эндемиков 2016 | Высотные пояса и регионы Колумбии текстом (испанский) | CC BY-NC 4.0 | DwC-A `http://ipt.biodiversidad.co/iavh/archive.do?r=biota_v14_n2_09` |
| Quintero & Jetz 2018 | Высотные диапазоны | Не указана, регистрация на mol.org | проверить перед использованием |

## 3. Распространение по регионам и ареалы

| Источник | Что даёт | Лицензия | Как забирать |
|---|---|---|---|
| **GBIF occurrence API** | Подсчёт находок вида по департаменту / полигону / GADM; фасеты по видам на регион | CC0 / CC BY / CC BY-NC по датасету (в основном CC BY); цитировать GBIF | `https://api.gbif.org/v1/occurrence/search?taxonKey=…&country=CO&gadmGid=COL.8_2&limit=0`; `facet=speciesKey&facetLimit=2000` |
| **GBIF Maps API v2** | Тайлы плотности находок (PNG/MVT) для карты ареала | Атрибуция GBIF | `https://api.gbif.org/v2/map/occurrence/density/{z}/{x}/{y}@1x.png?taxonKey=…&bin=hex` |
| Vélez et al. 2021 «Distribution of birds in Colombia» (BDJ 9:e59202) | Экспертные шейпфайлы ареалов 1 889 видов | CC BY 4.0 | Zenodo 4533435 (там только PDF); шейпфайлы искать в дополнениях статьи |
| eBird Status & Trends, BirdLife ареалы, Map of Life | Полигоны ареалов | Запрос/ограничения на редистрибуцию | **не использовать** |
| eBird hotspots / targets | Списки видов по хотспоту | Хранить и перепубликовать нельзя | **только ссылки** `https://ebird.org/hotspot/{locId}` |

## 4. Идентификаторы и имена (Wikidata, CC0)

Wikidata — «позвоночник» базы: QID, `P225` латынь, `P3444` eBird, `P2026` Avibase,
`P627`/`P5257` IUCN, `P141` статус IUCN, `P830` EOL, `P18` фото, `P373` категория Commons,
метки ru/en/es (ru-метки есть у 99 % видов). SPARQL endpoint `https://query.wikidata.org/sparql`,
обязателен User-Agent, батчи `VALUES` по ~200. Пример запроса — в отчёте агента, перенести в `pipeline/wikidata.py`.

## 5. Тексты

| Источник | Покрытие | Лицензия | Как забирать |
|---|---|---|---|
| **Wikipedia en / es / ru** | Статьи: en 93 %, es 91 %, ru 49 % видов; с полезным разделом «Описание»: en ~75–85 %, es ~40–55 %, ru ~20–30 % | **CC BY-SA 4.0**, атрибуция со ссылкой на статью, изменённый текст остаётся CC BY-SA | `action=parse&prop=sections|wikitext` (взять Description), или `prop=extracts`; заголовки через sitelinks Wikidata. Лимит 200 req/min с User-Agent; при 429 — Wikimedia Enterprise On-demand (50k/мес бесплатно) |
| **EOL API** | Тексты с пер-объектной лицензией (часто зеркала Wikipedia) | по объекту | `https://eol.org/api/pages/1.0/{id}.json?texts_per_page=5&details=true` |
| **SiB Colombia Catálogo de la Biodiversidad** | Испанские fichas (история, биотоп, имена), сотни видов | CC BY-NC 4.0 | `https://api.catalogo.biodiversidad.co/record_search/search?q=…` |
| **Chapman 1917** «Distribution of Bird-Life in Colombia» | Распространение и описания, устаревшая таксономия | Public Domain | OCR `https://archive.org/download/distributionbir00chapgoog/distributionbir00chapgoog_djvu.txt` |
| **Todd & Carriker 1922** «Birds of the Santa Marta region» | То же для Санта-Марты | Public Domain | IA `cu31924022518686` |
| Ridgway «Birds of North and Middle America» | Виды карибского склона | Public Domain | BHL `10.5962/bhl.title.54021` |
| xeno-canto `rmk` | Полевые заметки рекордистов | как запись (обычно BY-NC-SA) | вместе с записями |
| Wikispecies | Синонимы, авторы | CC BY-SA | — |
| Birds of the World, Avibase, IUCN текст, BirdLife, ICESI WikiAves, ProAves, Animal Diversity Web | | Защищены / NC-SA | **только ссылки** |

Словарь Бёме–Флинта (русские имена) защищён авторским правом: не копировать; имена брать из eBird/Wikidata/IOC.

## 6. Фото и иллюстрации

Оценка покрытия ~1 950 видов хотя бы одним фото CC0/BY/BY-SA: Commons 85–90 %, плюс iNaturalist → **93–96 %**.
Остаток (50–100 редких видов) — ссылки на Macaulay/eBird.

| Источник | Как искать | Метаданные для атрибуции | Лимиты |
|---|---|---|---|
| **Wikimedia Commons** | Wikidata `P18`; `Category:<Genus species>` через `generator=categorymembers&gcmtype=file&prop=imageinfo&iiprop=url|extmetadata` | `extmetadata`: `License` (`cc-by-sa-4.0`, `cc0`, `pd`), `LicenseUrl`, `Artist` (HTML), `Credit`; отбрасывать `cc-by-nc*`, `gfdl`-only | ~200 req/min с User-Agent, серийно, `maxlag=5`; тумбы ≤1 req/s; на практике 429 быстро — троттлить |
| **Wikimedia Commons, качество** | `Category:Quality_images_of_birds`, `Category:Featured_pictures_of_birds` | | |
| **iNaturalist** | `/v1/observations?taxon_name=…&quality_grade=research&photo_license=cc0,cc-by,cc-by-sa&order_by=votes`; 1 368 видов Колумбии с CC-фото, с соседями ~80–85 % | `photos[].license_code`, `attribution` (готовая строка), URL `inaturalist-open-data.s3.amazonaws.com/photos/{id}/large.jpg` | ≤60 req/min, <10 000/день, медиа <5 ГБ/ч; для массовой выгрузки — S3 open-data (`photos.csv.gz`) |
| Flickr | `license=4,5,9,10` | нужен ключ | +2–3 %, отложено |
| Openverse | агрегатор Commons/Flickr | | удобство, не покрытие |
| **BHL Flickr** (`61021753@N02`), Commons | Иллюстрации Гулда, Кёлеманса и др. | PD | таксон-теги частичны |
| Macaulay / eBird media | | Скачивание запрещено | **только ссылки** |

Правила: NC/ND исключаем; кроп и ресайз — производное, лицензия сохраняется (BY-SA остаётся BY-SA);
для каждого файла хранить автора, название, лицензию с версией и URL, ссылку на источник, дату, признак изменения.
Показывать атрибуцию у фото (подпись/кнопка «©») и на странице credits.

## 7. Звуки

xeno-canto API v3 требует ключ (бесплатно после регистрации), v2 отключён. Записи в основном
CC BY-NC-SA / BY-NC-ND — не скачиваем, встраиваем официальный плеер
`<iframe src="https://xeno-canto.org/{XC}/embed?simple=1">` или ссылаемся. Macaulay — ссылки.

## 8. Стек сайта (проверено 2026-09)

- Astro 7 (7.3.5), деплой `withastro/action@v6` + `actions/deploy-pages@v5`, `site` + `base=/colombia-birds`.
- `@vite-pwa/astro` 1.2.0 не заявляет поддержку Astro 6/7 → service worker вручную (Workbox) или override peer deps.
- Карта: MapLibre GL + OpenFreeMap (без ключа) или Leaflet + OSM; ареалы — тайлы GBIF.
- Медиа: Cloudflare R2 (10 ГБ бесплатно, без платы за трафик), CORS для офлайн-кэша.

## 9. Рекомендованная сборка базы

1. ACO (CC BY) → канонический список 1 966 таксонов и статусы.
2. eBird API (`locale=ru`, `en`, `es_CO`) → коды и имена; Wikidata → QID и внешние ID; IOC → fallback имён.
3. BIRDBASE + AVONET (CC BY) → высоты, биотопы, размеры.
4. Chaparro-Herrera 2024 (CC BY-NC) → эндемики/почти-эндемики.
5. GBIF → присутствие по департаментам/регионам маршрута.
6. Wikipedia en/es/ru → выдержки описаний с атрибуцией; PD-тексты → исторические заметки.
7. Commons → iNaturalist → фото с `credits.json`, ресайз, загрузка в R2.
8. xeno-canto (ключ) → список записей для встраивания.
