# Факт-чек: партия 1, список C (муравьеловки/печники, тиранновые, прочие воробьиные, котинги/манакины, куриные/тинаму, попугаи, хищники)

Карточки написаны 27.09.2026 по data/species, data/texts (Wikipedia en/ru/es), data/site_species.json и полевым знаниям.
Формат: `slug` — что проверить.

## Данные и таксономия (важно)

- `pyrrhura-melanura` — русское имя в индексе с опечаткой («Коричневохвотсая которра»); в тексте карточки русское имя не использовано. Исправить в маппинге/источнике имён и тогда вписать. Та же опечатка у `pyrrhura-calliptera` («Коричневогруая которра»).
- `grallaria-saturata` — нет русского имени в индексе; в ACO вид значится как «Perijá Antpitta» (en_aco), а в eBird — Equatorial Antpitta. Проверить маппинг ACO→eBird: Perijá Antpitta (G. saltuensis) и Equatorial (G. saturata) — разные виды после раздела Rufous Antpitta; не смешаны ли записи.
- `pseudocolopteryx-acutipennis` — в data `libro_rojo: CR` (Красная книга Колумбии), в тексте сказано «на грани исчезновения». Для широко распространённого вида это необычно — сверить с источником ACO/Libro Rojo. Также проверить, не является ли колумбийская популяция частично мигрантом (в data «Residente»).
- `turdus-ignobilis` — в data высоты 900–2 800 м, но вид «точно» в амазонских низинах маршрута (Пуэрто-Асис, Плайя-Рика ~250 м). В тексте «от предгорий и амазонских низин… по данным проекта до 2 800 м». Проверить нижнюю границу в BIRDBASE.
- `forpus-coelestis` — Wikipedia (es) даёт ареал только Эквадор и Перу; в карточке сказано, что в Колумбию вид заходит на крайнем юго-западе Нариньо. Проверить статус в ACO 2022 (резидент или залётный) и реальность записей у Тумако.
- `cistothorus-apolinari` — в тексте: «отдельный подвид — в парамо выше 3 000 м» (hernandezi, Сумапас). Проверить, какой подвид в Сумапасе и что именно он парамный.

## Внешность и отличия

- `asthenes-fuliginosa` — размер поставлен `thrush` по длине 18–20 см (почти половина — хвост); проверить, не логичнее ли `sparrow` по правилу «как поставит человек в поле».
- `machaeropterus-deliciosus` — длина 9,5–10 см на границе классов `hummingbird`/`sparrow`; поставлен `sparrow`. Решить правило для не-колибри около 10 см.
- `grallaria-saturata` — размер `sparrow` (14,5–15 см), хотя антпитта плотная (32–47 г). Отличие от `grallaria-rufula` дано «по ареалу и песне» — проверить, что Muisca Antpitta не доходит до Нариньо.
- `scytalopus-chocoensis` — фраза «выше 1 300 м его сменяет Nariño Tapaculo»: граница высот между chocoensis и vicinior примерная.
- `sipia-nigricauda` — отличие от `sipia-berlepschi` («хвост очень короткий, живёт ниже»); family-портрет упоминает Stub-tailed в Бангсиас-лодже, а в site_species его нет — сверить.
- `pseudocolopteryx-acutipennis` — похожий вид (Mourning Warbler) выбран за неимением лучшего; поискать более уместного кандидата для тростников Ла-Кочи.
- `myadestes-ralloides` — «светлая полоса на крыле в полёте» и описание Rufous-brown Solitaire (оранжево-жёлтое подклювье, рыжее горло) — по памяти.
- `ortalis-columbiana` — отличие от Speckled Chachalaca («голова рыжеватее, кайма мельче») — по памяти.
- `pyrrhura-melanura` — «птицы склона Чоко темнее и почти без жёлтого на крыле» (подвид pacifica): текст Wikipedia обрезан, проверить, чего именно нет у pacifica.
- `uromyias-agilis` — отличие от Tufted Tit-Tyrant (белый глаз, серая спина без пестрин) — по памяти.
- `elaenia-pallatangae` — «заметно желтее соседних элений» и отличия от Mountain/White-crested Elaenia — сверить.
- `chondrohierax-uncinatus` — «парит невысоко, обычно в середине дня» — по памяти.
- `geranoaetus-melanoleucus` — отличия от Variable Hawk (уже крылья, рыжая спина у многих) — сверить.

## Голос (все описания по памяти, кроме отмеченных)

- `asthenes-flammulata` — «сухие позывки и короткая трель».
- `asthenes-fuliginosa` — «быстрая трель, поднимается и затухает».
- `scytalopus-griseicollis` — «долгая ритмичная серия одинаковых нот».
- `sipia-nigricauda` — «высокая серия свистовых нот».
- `grallaria-saturata` — «короткая свистовая песня»; описание сознательно общее, уточнить по xeno-canto.
- `uromyias-agilis`, `pseudocolopteryx-acutipennis`, `elaenia-pallatangae` — общие формулировки.
- `cistothorus-apolinari` — «громкие резкие трели, часто дуэтом».
- `turdus-ignobilis` — «неспешная песня из повторяющихся свистовых фраз».
- `ampelion-rubrocristatus` — «молчалива, изредка хриплое кваканье».
- `penelope-montagnii` — «гоготящие крики и кудахтанье».
- `chondrohierax-uncinatus`, `geranoaetus-melanoleucus` — голоса у гнезда.
- Из Wikipedia (проверено по тексту): `scytalopus-chocoensis`, `entomodestes-coracinus`, `myadestes-ralloides`, `synallaxis-subpudica`, `tyrannus-melancholicus`, `crypturellus-soui`, `orthopsittaca-manilatus`, `rupornis-magnirostris`.

## Прочее

- `entomodestes-coracinus` — «оба известных гнезда нашли в Ла-Планаде» (ru-Wikipedia); сведения могут быть устаревшими.
- `ortalis-columbiana` — `layer: feeder` поставлен по портрету семейства (кормушки с бананами); проверить, есть ли такие кормушки в Эль-Энканто.
