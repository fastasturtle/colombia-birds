# Инструкции для агентов

Проект: справочник птиц Колумбии для тура (см. README.md). Владелец работает через Claude Code,
руками файлы не правит: всё, что здесь описано, делают агенты.

## Правила

1. **`data/` не редактировать руками.** Это выход пайплайна `pipeline/`. Нужно поменять данные —
   меняй шаг пайплайна или маппинг в `pipeline/mappings/` и перезапускай. Исключения (авторские файлы):
   `data/sites.json`, `data/itinerary.json`, `data/regions.json`.
2. **Рукописный контент только в `content/`.** Один markdown на вид: `content/species/<slug>.md`
   с frontmatter (см. `content/README.md`). Слаг = `id` из `data/species_index.json`.
3. **Лицензии.** В базу и на сайт попадает только CC0 / CC BY / CC BY-SA / Public Domain
   (тексты дополнительно CC BY-NC с пометкой). NC/ND, eBird/Macaulay медиа, Birds of the World,
   Avibase, BirdLife, ICESI WikiAves, ProAves — только ссылки. У каждого фото и текста хранить автора,
   лицензию с версией, URL источника, дату. Подробности: `docs/research/sources.md`.
4. **Таксономия.** Канон — eBird/Clements 2025 (совпадает с Merlin). Список видов и статусы — ACO 2022.
   Русские имена из eBird (`locale=ru`), fallback метка Wikidata, затем заголовок статьи ru.wikipedia (только кириллица), затем
   IOC World Bird List Multilingual (шаг `ioc_names`, только точное совпадение бинома), затем ручные
   `pipeline/mappings/names_ru_overrides.json`; источник в `name_ru_source` (`ebird` / `wikidata` / `ruwiki` / `ioc` / из overrides).
5. **Секреты** только в `.env` и GitHub Secrets (`XENO_CANTO_API_KEY`, `R2_ACCESS_KEY_ID`,
   `R2_SECRET_ACCESS_KEY`, `R2_CLOUDFLARE_TOKEN`). Никогда не коммитить и не печатать в чат.
6. **Сеть из облачной сессии Claude Code**: Wikimedia (Wikipedia, Commons, WDQS) режет общий IP
   (403/429). Массовые шаги `wikipedia`, `photos`, `upload` запускать через GitHub Actions
   (`.github/workflows/pipeline.yml`), локально только проверять на 1–3 видах. Wikidata брать через
   QLever (`https://qlever.dev/api/wikidata`). iNaturalist, GBIF, eBird API работают.
7. **Сайт**: Astro 7 + Svelte 5, `site/`. Данные читаются из `../data` через `site/src/lib/data.ts`
   только на этапе сборки. Мобильный экран — приоритет. Все тексты интерфейса по-русски, названия
   видов: английское + латынь + русское. Перед коммитом `cd site && npm run build` должен проходить.
8. **Деплой** на GitHub Pages из `main` (`.github/workflows/deploy.yml`). Рабочие ветки не деплоятся.
9. **Долгие операции** (разведка в интернете, массовые загрузки, большие рефакторинги) выносить в
   фоновых сабагентов, чтобы основной диалог оставался отзывчивым (см. CLAUDE.md).
10. **Массовые операции только ступенями.** Любая генерация контента, разметка или загрузка на сотни видов
    начинается с пробной партии в 20–30 видов, доведённой до продакшена (в `main`, на сайте). Владелец и
    ведущий агент смотрят результат, и только после одобрения запускается всё остальное.
11. **TODO** ведём в `docs/TODO.md`: закрыл пункт — отметь, нашёл новое — добавь.

## Окружение и проверка глазами

- Первый запуск в свежей сессии: `scripts/setup.sh` (uv sync + npm install).
- Скриншоты сайта на телефоне: `cd site && npm run build && npm run shots -- / /days/<date>/ /sites/<id>/ /species/<slug>/`
  (флаги `--dark`, `--full`, `--out DIR`). Файлы попадают в `.screenshots/` (в .gitignore), смотреть через Read.
  Playwright — devDependency сайта; в облачной сессии Chromium уже стоит (`PLAYWRIGHT_BROWSERS_PATH`),
  локально один раз `npx playwright install chromium`. Карта маршрута — статичный SVG без онлайн-тайлов:
  подложка `site/src/generated/basemap.json` (Natural Earth, шаг пайплайна `basemap`).
- Офлайн (service worker, пакет `/offline/`): после сборки `cd site && npm run test:offline` — Playwright-смоук на маленьком тестовом манифесте (скачать → отключить сеть → страница и фото из кэша, нескачанная страница → «Офлайн»); гоняется и в CI перед деплоем.
- Сборка сайта: `cd site && npm run build` (~10 с, 2 000+ страниц). Проверять перед каждым коммитом в `site/`.
- Проверка перед коммитом в `site/`: `cd site && npm run verify` (`astro check` — 0 ошибок/предупреждений, затем сборка).
  Тот же `astro check` гоняется в CI перед деплоем и роняет его при ошибках типов.

## Частые задачи

- Добавить/исправить сопоставление вида между ACO и eBird: `pipeline/mappings/aco_to_ebird.json`,
  затем `uv run python run.py ebird birdbase wikidata build`.
- Добавить локацию или день маршрута: `data/sites.json` / `data/itinerary.json`, затем
  `uv run python run.py sites` (пересчитывает целевые виды и `data/focus_species.json`).
- Поле `"optional": true` в `data/sites.json` — локация не входит в программу группового тура (кандидат на
  самостоятельный выезд из Боготы в свободные дни, дней в `data/itinerary.json` у неё нет). Сайт показывает такие
  локации отдельной группой «Возможные выезды из Боготы» с пометкой «не в программе тура» (`isOptionalSite()` в
  `site/src/lib/data.ts`); в GBIF-подсчётах они участвуют как обычно. В карточках видов не придумывать для них даты.
- Написать русское описание вида: `content/species/<slug>.md`, опираясь на `data/texts/<slug>.json`
  (Wikipedia, обязательна атрибуция при заимствовании) и `data/species/<slug>.json`.
- Добавить пару «похожие виды»: `content/similar/<slug-a>--<slug-b>.md`.
- Факт-чек карточек: скилл `fact-check` ставит `checked: <дата>` во frontmatter; `python3 scripts/card_index.py` пересобирает `docs/fact-check/INDEX.md` (сколько проверено, какие нет).
- Загрузить фото для набора видов: Actions → pipeline → steps `photos upload`, `only` = слаги.
- Погода: `data/weather.json` (прогноз Open-Meteo утро/день/вечер по дням и локациям) обновляет без ИИ ежедневный
  workflow `.github/workflows/weather.yml` (05:13 Боготы, шаг `weather`, коммит + деплой). Вручную: `uv run python run.py weather`
  или Actions → weather → Run workflow. Ночёвка вне `data/sites.json` (отель в городе): поле дня
  `overnight_loc` `{id, name_ru, lat, lon}` в `data/itinerary.json` (высота из `elev_sleep`), без него — Богота. На сайте: `WeatherDay.astro` на странице дня и строка в `DayCard.astro`.
- Наблюдения в туре (что уже увидели) обновляются сами: workflow `.github/workflows/observations.yml` каждые 2 часа
  (до конца поездки плюс день: последняя дата `data/itinerary.json`; ручной запуск работает всегда) запускает `run.py ebird_trip observations` — шаг `ebird_trip` берёт новые чеклисты Ани из публичного отчёта поездки
  eBird (`pipeline/sources/ebird/trip_reports.json` → `trip_report.csv`), `observations` сливает их с выгрузкой
  (выгрузка главнее по `Submission ID`), коммит и деплой только при изменениях. Вручную:
  `uv run python run.py ebird_trip observations` или Actions → observations → Run workflow. Тот же workflow затем
  запускает шаг `igor500` (`continue-on-error`): из того же отчёта он пересчитывает `data/igor500.json` для скрытой
  страницы `/igor-500/` (кандидаты по локациям, счёт, `as_of`); в репозиторий попадают только производные данные,
  без списков видов Игоря и группы, чеклистов и локаций (решение владельца). Без секрета
  `EBIRD_API_KEY` из отчёта приходят только виды и численность, поэтому ручная выгрузка остаётся нужна: комментарии,
  коды гнездования, протокол и длительность, а также чеклисты 1–2 октября (до начала отчёта, только в выгрузке).
  Выгрузка: Аня присылает новую выгрузку eBird («Download my data», `MyEBirdData.csv`).
  Положить её вне репозитория (это личная история локаций по всему миру, **не коммитить**) и выполнить
  `cd pipeline && uv run python run.py observations --import <путь к MyEBirdData.csv>`: шаг перепишет
  `pipeline/sources/ebird/colombia_2026.csv` (только строки CO-* с начала тура) и `life_list_before_trip.json`
  (виды до тура, для «новых для Ани»), затем `data/observations.json` и отчёт `data/sources/observations_report.md`
  (проверить «Не сопоставлено» и «Чеклисты без локации»). Без `--import` шаг пересобирает только из закоммиченных
  источников. Коммитить эти четыре файла, сайт пересобрать. На сайте: `/seen/`, фильтр «Видели» на списках, ✓ у видов. Блок «Группа» на `/seen/` — счёт eBird по каждому участнику
  отчёта поездки (только имена и числа: виды, чеклисты; без чеклистов, локаций и списков видов — решение владельца),
  его тоже обновляет `ebird_trip`.
  Подробная процедура (проверка отчёта, несопоставленные виды, чеклисты без локации, деплой): скилл `ebird`.
- Расписания `observations` (каждые 2 часа) и `weather` (10:13 UTC): GitHub под нагрузкой запускает cron с опозданием
  на часы, поэтому оба workflow вовремя запускает cron Cloudflare Worker (`worker/`, `[triggers]` в `wrangler.toml`,
  `observations` в :47 с input `scheduled=true`, чтобы после поездки он останавливался, как cron GitHub). Cron GitHub
  в workflow оставлены запасными. Токену `REPORTS_TOKEN` для этого нужно право Actions: Read and write (`worker/README.md`).
- Прогресс пайплайна в CI: `curl -s https://pub-5e58909dbd0e457c85e4e36ef2cdc583.r2.dev/status/pipeline.json` (обновляется раз в минуту; локально `pipeline/cache/status.json`, см. `pipeline/README.md`).
