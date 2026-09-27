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
   Русские имена из eBird (`locale=ru`), fallback Wikidata/IOC, источник в `name_ru_source`.
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
- Скриншоты сайта на телефоне: `cd site && npm run build && npm run shots -- / /species/<slug>/ /route/`
  (флаги `--dark`, `--full`, `--out DIR`). Файлы попадают в `.screenshots/` (в .gitignore), смотреть через Read.
  Playwright — devDependency сайта; в облачной сессии Chromium уже стоит (`PLAYWRIGHT_BROWSERS_PATH`),
  локально один раз `npx playwright install chromium`. Карта маршрута — статичный SVG без онлайн-тайлов:
  подложка `site/src/generated/basemap.json` (Natural Earth, шаг пайплайна `basemap`).
- Сборка сайта: `cd site && npm run build` (~10 с, 2 000+ страниц). Проверять перед каждым коммитом в `site/`.

## Частые задачи

- Добавить/исправить сопоставление вида между ACO и eBird: `pipeline/mappings/aco_to_ebird.json`,
  затем `uv run python run.py ebird birdbase wikidata build`.
- Добавить локацию или день маршрута: `data/sites.json` / `data/itinerary.json`, затем
  `uv run python run.py sites` (пересчитывает целевые виды и `data/focus_species.json`).
- Написать русское описание вида: `content/species/<slug>.md`, опираясь на `data/texts/<slug>.json`
  (Wikipedia, обязательна атрибуция при заимствовании) и `data/species/<slug>.json`.
- Добавить пару «похожие виды»: `content/similar/<slug-a>--<slug-b>.md`.
- Загрузить фото для набора видов: Actions → pipeline → steps `photos upload`, `only` = слаги.
