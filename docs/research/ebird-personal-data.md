# Личные данные eBird для «Увидели»: как получить виды и места Ани

Все проверки выполнены 2026-09-30, если не указано иное. Цель: на сайте отмечать виды, которые Аня
(своя учётная запись eBird) уже видела в поездке 1–25.10.2026, и показывать, где. Пункт «Увидели» в
`docs/TODO.md` (решение владельца от 27.09: CSV в браузер, localStorage) здесь пересматривается с учётом
того, что нашлось.

Главное в трёх строках:
- Официальный eBird API v2 **не имеет** ни одного «личного» эндпоинта: нет «мои чеклисты», «мой life list».
  Чеклист отдаётся только по известному `subId` (`product/checklist/view/{subId}`, нужен ключ).
- **eBird Trip Report** с видимостью Link-Only/Public отдаётся без входа и без ключа через внутренний JSON
  `https://ebird.org/tripreport-internal/v1/...`: список чеклистов (с `locId`, координатами, датой) и список
  видов, с фильтром по участнику. Проверено вживую. Минус: интерфейс недокументированный, а `robots.txt` у
  ebird.org закрывает всё (`User-agent: * Disallow: /`).
- «Download My Data» даёт полный CSV (23 колонки, есть `Location ID`, координаты), но только по письму и руками.

## 1. «Download My Data» (MyEBirdData.csv)

| Вопрос | Ответ | Источник |
|---|---|---|
| Как запросить | My eBird → «Download My Data» в боковой панели (на телефоне «Manage»), прямой URL `https://ebird.org/downloadMyData` (без входа 302 на логин, проверено curl). Выгружается только всё сразу. Подмножество (регион/место/даты/вид): страница Sightings Lists → кнопка «Download» (облако) | [My eBird, Help Center, обн. 28.03.2025](https://support.ebird.org/en/support/solutions/articles/48000794682-my-ebird) |
| Как приходит | Письмо от `do-not-reply@ebird.org` со ссылкой на zip, внутри `MyEBirdData.csv`; «если письма нет в течение 24 часов» — проверить адрес. На практике минуты, официального SLA нет | [eBird NZ Atlas, «Downloading your own data»](https://ebird.org/atlasnz/news/downloading-your-own-data) |
| С телефона | Да, из мобильного браузера (сайт eBird, «Manage»); в самом приложении eBird Mobile выгрузки нет | [My eBird](https://support.ebird.org/en/support/solutions/articles/48000794682-my-ebird) |
| Свежесть | Выгрузка формируется из базы на момент запроса: отправленный чеклист попадает в неё сразу; неотправленные (офлайн на телефоне) — нет | вывод из механики, официально не описано |
| Таксономия | Текущая таксономия eBird на момент выгрузки (сейчас v2025, `ref/taxonomy/versions` → `2025.0 latest`, проверено). Осенью 2026 ожидается новая версия, согласованная с AviList (v2025 вышла 31.10.2025) | [Clements update Oct 2025](https://www.birds.cornell.edu/clementschecklist/introduction/updateindex/october-2025) |
| Кодировка | Официально не указана; по разборщикам сторонних проектов — UTF-8, запятая, кавычки RFC 4180 | не подтверждено официально |

Колонки (актуальный формат, 23 шт.; подтверждается несколькими свежими парсерами, напр.
[birds-eye-app/beak `parseEbirdExport.ts`](https://github.com/birds-eye-app/beak/blob/main/src/chirped/parseEbirdExport.ts),
[jlian/wingdex fixtures](https://github.com/jlian/wingdex/tree/main/e2e/fixtures); старый формат 2010-х был без
`Location ID`, `Observation Details`, `ML Catalog Numbers`):

```
Submission ID, Common Name, Scientific Name, Taxonomic Order, Count, State/Province, County,
Location ID, Location, Latitude, Longitude, Date, Time, Protocol, Duration (Min), All Obs Reported,
Distance Traveled (km), Area Covered (ha), Number of Observers, Breeding Code, Observation Details,
Checklist Comments, ML Catalog Numbers
```

Особенности: `Count` может быть `X`; `Date` — `YYYY-MM-DD`; `Time` — `07:05 AM`; в строки попадают
`sp.`, slash, гибриды и подвидовые группы (`Scientific Name` вида `Columba livia (Feral Pigeon)`); кода вида
eBird (`speciesCode`) в CSV **нет** — только латынь и `Taxonomic Order`. `Common Name` зависит от языка
аккаунта (не проверено), поэтому сопоставлять по `Scientific Name`.

Life list отдельно: `https://ebird.org/lifelist` (только с входом) с фильтрами регион/период и ссылкой
«Download (csv)» — по одной строке на вид (первая встреча). Точный набор колонок официально не описан и не
проверен (без входа страница недоступна). Для «где видела» он хуже полного CSV: только первое место.
([описание в виньетке lifeR, CRAN](https://archive.linux.duke.edu/cran/web/packages/lifeR/vignettes/lifer-intro.html))

## 2. eBird API v2

Официальная документация (Postman, JSON коллекции `https://documenter.gw.postman.com/api/collections/664302/S1ENwy59`,
[страница](https://documenter.getpostman.com/view/664302/S1ENwy59)): группы `data/obs`, `product`, `ref/geo`,
`ref/hotspot`, `ref/taxonomy`, `ref/region`. **Эндпоинтов по пользователю нет**: ни наблюдений, ни чеклистов,
ни life list. `data/obs/{regionCode}/recent`, `product/lists/{regionCode}` — общие ленты региона, без фильтра по
автору (в `product/lists` есть `userDisplayName`, но это лента последних 200 чеклистов на регион; для
Колумбии в октябре Аню там не выловить надёжно).

`GET /v2/product/checklist/view/{subId}` — «Get the details and observations of a checklist». Поля ответа
(пример из доков): `subId`, `protocolId`, `locId`, `durationHrs`, `allObsReported`, `creationDt`,
`lastEditedDt`, `obsDt`, `numObservers`, `userDisplayName`, `obs[]` с `speciesCode`, `howManyStr`, `obsDt`,
`obsId`, `obsAux` (коды гнездования). **Координат и названия места нет** — только `locId`; координаты
отдельно через `ref/hotspot/info/{locId}` (для личных точек `L…` не хотспотов — не отдаются). Документация
предупреждает: «Do NOT use this to download large amounts of data. You will be banned if you do.» Ограничения
по чужим чеклистам в документации не описаны; сторонние обёртки (rebird, ebird-api) используют его для любого
`subId`. Скрытые (Hide from eBird output) чеклисты, вероятно, не отдаются — проверить на первом реальном.

Проверка без ключа (curl, 2026-09-30):

| Запрос | Результат |
|---|---|
| `GET https://api.ebird.org/v2/product/checklist/view/S12345678` без ключа | **403**, пустое тело |
| то же с `X-eBirdApiToken: invalid` | 403 |
| `GET /v2/data/obs/CO/recent` без ключа | 403 |
| `GET /v2/ref/hotspot/info/L1127703` без ключа | 403 |
| `GET /v2/ref/taxonomy/ebird?fmt=csv&species=barswa` без ключа | 200 (как в `fetch_ebird.py`) |

Ключ: `https://ebird.org/api/keygen` (нужна учётная запись eBird, ключ привязан к ней), передаётся заголовком
`x-ebirdapitoken` или параметром `key`. Числовые лимиты не опубликованы. Условия
([eBird API Terms of Use, ред. 19.10.2021](https://www.birds.cornell.edu/home/ebird-api-terms-of-use/)): только
некоммерческое использование; «attribute eBird.org as the source of the data … wherever it is used or
displayed»; ключ не передавать третьим лицам; не нагружать сервер. Python-обёртка
[`ebird-api` 4.1.0 на PyPI](https://pypi.org/project/ebird-api/) (14.06.2026) — тонкий клиент к тем же
эндпоинтам, личных данных не добавляет.

## 3. Шаринг чеклистов и Trip Reports

**Share checklist** ([Checklist sharing, обн. 28.03.2025](https://support.ebird.org/support/solutions/articles/48000625567-checklist-sharing-in-ebird)):
в eBird Mobile до отправки — «Number of Observers» > 1 → «Share checklist with…» → имя пользователя;
после отправки — на сайте «Checklist Tools → Share w/ others in your party». «Sharing a checklist creates
independent copies in each person's account» — у получателя появляется **своя копия со своим `subId`**, и она
становится его наблюдением. Для нас это минус: виды Ани смешаются со списком Димы.

**Публичная страница чеклиста** `https://ebird.org/checklist/S…`: вход не требуется (нет редиректа на логин),
но скрипту отдаётся заглушка Anubis «Making sure you're not a bot!» (проверено curl). То есть человек со
ссылкой видит чеклист, скрипт — нет; для скрипта остаётся API с ключом.

**Trip Reports** ([Help Center, обн. 28.03.2025](https://support.ebird.org/en/support/solutions/articles/48001201565)):
- создаются на `https://ebird.org/mytripreports`, до 31 дня подряд (наша поездка 1–25.10 влезает);
- «LIVE summaries»: все чеклисты участников за период включаются автоматически, участник может задать свои
  даты или убрать чеклист; можно создать заранее и дать ссылку друзьям;
- видимость: Limited (только приглашённые), **Link-Only** («anyone with the Trip Report link»), Public
  (индексируется Google, видна на страницах регионов);
- показывает: список видов с суммой особей, число чеклистов, карту мест, список чеклистов, фото/аудио,
  лайферы, текст; кнопка «Print / save as PDF». Кнопки выгрузки CSV нет.

Что реально отдаётся без входа (проверено на публичном отчёте WINGS, `https://ebird.org/tripreport/547642`,
2026-09-30). Страница — SPA (`trip-reports.umd.min.js`), в HTML встроен объект `tripReport = {...}` с
`tripReportId`, `privacy` (`"open"`), `people[]` (`tripReportPersonId`, `userId`, `userDisplayName`, `role`,
`personBeginDt/EndDt`). Данные SPA берёт из `tripApiBaseUrl = contextRoot + '/tripreport-internal/v1/'`,
все ответы — JSON, без входа, без ключа, без заглушки Anubis:

| Эндпоинт (`https://ebird.org/tripreport-internal/v1/…`) | Что отдаёт |
|---|---|
| `checklists/{tripId}[?tripReportPersonId=N]` | массив чеклистов: `subId`, `locId`, `numSpecies`, `obsDt`, `obsTime`, `isoObsDate`, `loc{locId, name, latitude, longitude, subnational1Code, isHotspot, hierarchicalName}` (34 шт., с фильтром по участнику 31) |
| `taxon-list/{tripId}[?tripReportPersonId=N]` | виды: `speciesCode`, `category`, `commonName`, `sciName`, `numIndividuals`, `numChecklists`, `numMedia` (352, по участнику 311) |
| `taxon-detail/{tripId}/{speciesCode}` | где и когда вид отмечен: `checklists[{subId, obsDt, locName, howMany}]`, `assetIds` |
| `locations/{tripId}` | места: `locId`, `name`, `latitude`, `longitude`, `isHotspot` |
| `num-species`, `num-checklists`, `media-stats`, `narrative`, `comments` | сводки |

Итого из trip report без ключа получается ровно то, что нужно: вид (`speciesCode`, `sciName`) → чеклисты
(`subId`) → место (`locId`, координаты) → дата. Оговорки: интерфейс внутренний и может поменяться без
предупреждения; `https://ebird.org/robots.txt` запрещает всё всем (`User-agent: *` / `Disallow: /`), хотя это
данные самой Ани с её согласия. Замечено также, что `checklists/{id}` ответил JSON для отчёта, чья HTML-страница
отдала 403 (видимо, Limited): полагаться на это нельзя, Аня должна поставить Link-Only.

## 4. Профиль (`ebird.org/profile/…`)

«If you make your profile public, it will be visible to **logged-in eBird users** anywhere your name appears»;
можно показывать последние чеклисты ([My eBird](https://support.ebird.org/en/support/solutions/articles/48000794682-my-ebird)).
Без входа `https://ebird.org/profile/<handle>` → 302 на логин CAS (проверено curl). Для сборки на GitHub
Actions без логина профиль бесполезен.

## 5. eBird Mobile

- Офлайн: полностью работает без сети, нужны заранее скачанные «Packs» (Settings → Packs → Colombia /
  департаменты); чеклисты сохраняются в «My Checklists» и отправляются, когда появится связь
  ([eBird Mobile, Help Center](https://support.ebird.org/support/solutions/articles/48000957940),
  [ebird.org/about/ebird-mobile](https://ebird.org/about/ebird-mobile/)). **Задержка на сайте = время до
  отправки**: в Чингасе, Мокоа и т. п. это может быть вечер или следующий день.
- Шаринг из приложения: «Share checklist with…» до отправки (см. §3); после отправки — через «eBird.org» в
  приложении (открывает сайт). Экспорта одного чеклиста в CSV/текст в приложении нет (официального описания
  не найдено); ссылку `ebird.org/checklist/S…` можно скопировать со страницы чеклиста.

## 6. Альтернативы

| Вариант | Итог |
|---|---|
| GBIF EOD ([датасет](https://www.gbif.org/dataset/4fa7b334-ce0d-4e88-aaae-2e0c138d049e)) | Бесполезен: обновляется раз в год, на 2026-09-30 последняя версия опубликована 08.08.2025, данные по 2024 г. включительно (проверено `api.gbif.org`). Лаг 1–2 года |
| Merlin Life List | Merlin показывает виды из eBird-чеклистов, но сохранённое **только в Merlin** «not part of public eBird displays», в trip report и API не попадает; экспорта из Merlin нет, управлять — через eBird.org ([Help Center, обн. 03.05.2024](https://support.ebird.org/en/support/solutions/articles/48001144489)). Попадают ли Merlin-сохранения в Download My Data — не проверено |
| `ebird-pages` 0.3.0 ([PyPI](https://pypi.org/project/ebird-pages/), 08.2025) | Скрейпер HTML-страниц eBird; сейчас упрётся в Anubis |
| `ebird-api` (PyPI), rebird (R) | Обёртки официального API, личных данных нет |
| Observation.org, BirdTrack, iNaturalist | Есть личные API, но Аня пишет в eBird; дублировать ввод нереально |
| Ссылки на чеклисты вручную | Аня присылает `S…`, скрипт зовёт `product/checklist/view/{subId}` с ключом Димы. Работает, но это ручной шаг на каждый чеклист, и нет координат для личных точек |

## 7. Условия и лицензии

- API: некоммерческое использование разрешено, обязательна атрибуция «eBird.org» там, где данные показаны
  ([API ToU](https://www.birds.cornell.edu/home/ebird-api-terms-of-use/)). На странице «Увидели» нужна строка
  «Данные: eBird.org, наблюдения Ани» со ссылкой на trip report.
- [Cornell Lab Terms of Use (23.10.2024)](https://www.birds.cornell.edu/home/terms-of-use/): отправляя данные,
  пользователь даёт Cornell бессрочную лицензию, но права на свои наблюдения у него не отбираются; скачивать
  можно то, что предложено для скачивания, «for personal and noncommercial use». Явного пункта про скрейпинг
  нет; технически запрет выражен `robots.txt` (всё закрыто) и Anubis.
- AGENTS.md, правило 3: медиа eBird/Macaulay и списки хотспотов — только ссылки. Собственные наблюдения Ани
  (вид, дата, место) — её данные, хранить их в `data/seen.json` можно; фото из Macaulay (`assetIds`) не
  копировать, только ссылки. Хранить только вид, дату, место и `subId`; комментарии и число особей не нужны.

## Рекомендация

Сопоставление, общее для всех вариантов:
- **Вид**: `speciesCode` → `ebird_code` в `data/species/<slug>.json` (прямое совпадение, 1 982 вида). Для CSV
  (кода нет) — `Scientific Name` → `sci_name`; подвидовые группы (`issf`, форма «Genus species (Group)») →
  родительский вид по `REPORT_AS` из `ref/taxonomy/ebird`; `spuh`, slash, гибриды — пропускать. Совпавшие ни
  с чем — список «вне нашего списка» в логе. Держать запасной путь через латынь: осенью 2026 выйдет новая
  таксономия (AviList), коды отдельных видов могут смениться прямо во время или сразу после поездки.
- **Место**: `locId` ∈ `data/sites.json → ebird_hotspots[].id` → наш `site.id` (35 хотспотов на 29 мест).
  Иначе — ближайшее место по координатам (haversine) в радиусе ~10–15 км (у части мест `coords_approx`),
  иначе показать `loc.name` как есть. Дата — `isoObsDate`/`Date`, привязка к дню маршрута по
  `data/itinerary.json`.

**A. Trip Report (Link-Only) → шаг пайплайна → `data/seen.json` → пересборка. Рекомендуется.**
- Аня: один раз создаёт trip report 01.10–25.10.2026, видимость Link-Only, присылает ссылку; дальше просто
  отправляет чеклисты в eBird Mobile (с Packs для офлайна). Дима может добавиться участником — тогда фильтр
  `tripReportPersonId` Ани (из `people[]` в HTML страницы; можно записать число в конфиг один раз).
- Владелец/агент: шаг `seen` в `pipeline/`: `checklists/{tripId}?tripReportPersonId=…` (места и даты) +
  `taxon-list/{tripId}?…` (виды) + `taxon-detail/{tripId}/{code}` на каждый вид (где/когда; ~300 запросов за
  прогон, с паузой 1 с) → `data/seen.json` `{slug: [{date, site_id|null, loc_name, lat, lon, subId}]}`;
  workflow по cron раз в 3–6 ч + ручной запуск `gh workflow run`. Вместо `taxon-detail` можно брать состав
  чеклистов официальным `product/checklist/view/{subId}` (ключ Димы в секрете `EBIRD_API_KEY`, только новые
  `subId`, ~5–10 запросов в день) — это страхует от поломки половины внутреннего интерфейса.
- Задержка: отправка чеклиста → ближайший cron (≤ 3–6 ч) → сборка и деплой (~10 мин) → плашка «Есть новая
  версия» (до 10 мин кэша `version.json`). Офлайн-участки добавляют время до появления связи.
- Трудозатраты: 1 шаг пайплайна + workflow + UI (серые виды, страница «Увидели»); ~полдня агента.
- Риски: недокументированный `tripreport-internal/v1` может смениться или закрыться Anubis/логином (тогда
  фолбэк B); `robots.txt`; отчёт максимум на 31 день.

**B. Периодический «Download My Data» → CSV в репозиторий.** Запасной путь.
- Аня: раз в 1–2 дня с телефона запрашивает выгрузку, пересылает zip Диме (или кладёт в общий диск).
- Владелец/агент: скрипт фильтрует строки `State/Province` = `CO-*` и `Date` в 2026-10-01…25, коммитит только
  нужные поля (без комментариев), шаг `seen` строит тот же `data/seen.json` по `Scientific Name`,
  `Location ID`, `Latitude/Longitude`, `Date`, `Submission ID`.
- Задержка: 1–2 дня, зависит от людей. Официальный путь, без серых зон. Риски: забудут; весь архив Ани
  проходит через почту.

**C. Загрузка CSV в браузере (как в TODO).** Минимум инфраструктуры, но хуже всего по UX.
- Аня/Дима: скачивают CSV на телефон, загружают на странице «Увидели»; разбор на клиенте, хранение в
  `localStorage` (на каждом телефоне отдельно).
- Место: по `Location ID` → хотспоты мест (их можно вшить в страницу) или по координатам. Задержка — как у B,
  плюс данные не общие и теряются с очисткой браузера. Разумно оставить как ручной резервный режим поверх A.

**Если аккаунт общий** (Аня и Дима пишут в один eBird): trip report и CSV отдадут общие наблюдения, отделить
Аню нельзя — страница станет «Увидели мы». **Если Аня пользуется только Merlin**: её сохранения в eBird-выдачу,
trip report и API не попадают, вариант A не работает, B и C под вопросом (не проверено, попадают ли они в Download My Data); нужно, чтобы она вела чеклисты в eBird Mobile
(достаточно «Incidental» — одна птица, одна отметка).
