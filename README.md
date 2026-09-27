# Птицы Колумбии · colombia-birds

Справочник птиц для нашего тура по южной Колумбии (октябрь 2026): все 1 966 видов страны с
русскими и английскими названиями, статусами, высотами и биотопами, фото по свободным лицензиям,
маршрут тура с картой и целевыми видами локаций. Сайт: https://fastasturtle.github.io/colombia-birds/

## Как устроено

```
data/            база (генерируется пайплайном, руками не правится)
  species/       одна карточка на вид (JSON)
  species_index.json, families.json
  sources/       сырые выгрузки по источникам (ACO, eBird, BIRDBASE, Wikidata)
  texts/         выдержки Wikipedia (CC BY-SA)
  photos/        кандидаты фото, credits/ выбранные фото с атрибуцией
  sites.json, itinerary.json, regions.json   маршрут (частично авторские)
content/         рукописные тексты (пишутся агентами), сливаются на сборке сайта
pipeline/        Python-пайплайн сбора данных (uv)
site/            сайт на Astro 7 + Svelte, деплой на GitHub Pages
docs/            маршрут, разведка источников и локаций, TODO
```

Медиа лежат в Cloudflare R2 (`PUBLIC_MEDIA_BASE_URL`), в репозитории только метаданные и атрибуция.

## Запуск

```bash
# данные
cd pipeline && uv sync && uv run python run.py            # aco ebird birdbase wikidata build
uv run python run.py wikipedia photos upload              # тяжёлые шаги, лучше через GitHub Actions

# сайт
cd site && npm install && npm run dev                     # http://localhost:4321/colombia-birds/
npm run build                                             # dist/
```

Переменные окружения: см. `.env.example`. Секреты только в `.env` (в .gitignore) и GitHub Secrets.

## Источники и лицензии

Полный обзор в `docs/research/sources.md`. Коротко: список видов и статусы — ACO 2022 (CC BY 4.0);
признаки — BIRDBASE 2025 (CC BY 4.0); имена и коды — eBird/Clements 2025; идентификаторы — Wikidata (CC0);
тексты — Wikipedia (CC BY-SA 4.0); фото — Wikimedia Commons и iNaturalist, только CC0 / CC BY / CC BY-SA / PD,
с атрибуцией у каждого снимка. Звуки — ссылки на xeno-canto и eBird.
