# TODO

Статус на 2026-09-27. Закрытые пункты помечаем `[x]`, не удаляем.

## База данных
- [x] Список видов ACO 2022, статусы, биотопы, IUCN (`pipeline/steps/fetch_aco.py`)
- [x] Имена ru/en/es и коды eBird, сопоставление ACO ↔ Clements (4 ручных маппинга)
- [x] Признаки BIRDBASE: высоты, биотопы, масса, диета, миграция
- [x] Wikidata: QID, внешние ID, категории Commons, ссылки на статьи Wikipedia
- [x] Сборка `data/species/*.json`, индекса и семейств
- [ ] Выдержки Wikipedia en/es/ru для всех видов (шаг написан, запустить в GitHub Actions)
- [x] Фото: шаги `photos` (кандидаты Commons + iNat) и `upload` (ресайз, R2, credits) написаны; Commons проверен только на моках
- [ ] Первый запуск фото в GitHub Actions: `photos upload` для всех видов; проверить, что Commons отвечает из CI
- [ ] Русские названия семейств: eBird `locale=ru` отдаёт английские, взять метки семейств из Wikidata (QLever) → `data/families.json`
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
- [ ] Проверить два ID хотспота El Escondite (L6464472 / L17054356)
- [ ] Найти хотспоты El Encanto, Finca Discosura, Km 42, Finca Maragrícola
- [ ] Manakin Nature Tours PDF «Macizo, Amazon & Pacific Foothills 2026» — вытащить список видов

## Сайт
- [x] Каркас Astro 7 + Svelte: семейства, список видов с поиском и фильтрами, карточка вида, маршрут с картой и профилем высот
- [ ] Деплой на GitHub Pages (workflow готов, нужно: Settings → Pages → Source = GitHub Actions, слить в main)
- [ ] Показ фото из R2 (после загрузки)
- [ ] PWA: service worker вручную (плагин не поддерживает Astro 7), офлайн-схема маршрута уже есть
- [ ] Страница региона: виды по высотному поясу и биотопу
- [ ] Определитель по признакам: семейство × регион × высота × биотоп × размер
- [ ] Страницы «похожие виды» из `content/similar/`
- [ ] Портреты семейств (что это за семейство, как узнать, поведение) — тексты агентами
- [ ] Русские описания видов из `content/species/` (сначала фокусные виды маршрута)
- [ ] Практическая страница: погода по дням, одежда, логистика (из чата группы)
- [ ] Страница credits со всеми авторами фото и текстов
- [ ] Тёмная тема: проверить контраст карты и чипов
- [ ] Квиз «угадай птицу» (после фото)

## Как продолжать в новой сессии
Спросить «что осталось» → этот файл. Правила → `AGENTS.md`. Решения → `docs/DECISIONS.md`. Источники → `docs/research/`.

## Инфраструктура
- [x] Секреты в GitHub, бакет R2 `colombia-birds`, публичный URL r2.dev
- [ ] CORS на бакете: origins `https://fastasturtle.github.io`, `http://localhost:4321`, методы GET/HEAD
- [ ] Свой домен для медиа вместо r2.dev (когда появится домен в Cloudflare)
- [x] Workflow `pipeline.yml` (workflow_dispatch, steps + only)
- [ ] Первый запуск `wikipedia` в Actions
- [ ] Скиллы для агентов: `/write-species-text`, `/add-similar-pair`, `/fetch-photos`
