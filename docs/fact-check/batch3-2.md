# Факт-чек: партия 3, список 2 (танагры, цапли и ибисы, пастушки, хищники, сычик, уратао)

Карточки написаны 27.09.2026 по data/species, data/texts (Wikipedia en/es/ru), data/site_species.json, data/study_lists.json
и полевым знаниям агента. Ниже то, что стоит проверить по открытым источникам перед публикацией. Формат: `slug — что проверить`.

## Общее

- dacnis-egregia, cnemoscopus-rubrirostris, butorides-striata — в data/texts нет текстов Wikipedia; карточки написаны по data/species и памяти, все признаки и голос сверить целиком.
- tangara-cyanotis, dacnis-berlepschi, rufirallus-fasciatus, eurypyga-helias, micrastur-plumbeus, glaucidium-parkeri, nyctibius-grandis — на точках маршрута только «маловероятно» (или совсем нет данных); в тексте так и сказано. Если лидер хочет не писать карточки для таких видов, это они.
- Голоса почти везде обобщённые; проверять в первую очередь у танагр (sphenopsis, bangsia, iridosornis, anisognathus, cnemoscopus, catamenia, dacnis-egregia) и у пастушков (mustelirallus, laterallus).

## По видам

- stilpnia-nigrocincta — «чёрная маска у основания клюва и вокруг глаза» и «сиренево-голубая голова» по памяти; сверить с фото. Отличие от Tangara mexicana («брюхо бледно-жёлтое») по памяти.
- stilpnia-cyanicollis — «плечо золотисто-зелёное» по es-Wikipedia; у колумбийских подвидов оттенок может отличаться. Отличие от T. vassorii по памяти.
- tersina-viridis — «местами в Колумбии кочует по сезонам» — по памяти, сверить.
- dacnis-egregia — вся окраска (жёлтое брюхо и пучки, жёлтый глаз, самка) по памяти и по аналогии с картой dacnis-lineata; сверить. Отличие от D. venusta («низ чёрный, глаз красный») по памяти. Питание нектаром — «по-видимому».
- catamenia-homochroa — цвет клюва («розовато-желтоватый»), кочёвки за плодоносящим бамбуком, песня — по памяти. Нижняя граница 1 600 м в data против 2 400–3 600 в es-Wikipedia; в тексте дано по data с оговоркой «обычно у верхней границы леса».
- sphenopsis-frontalis — голос («быстрая щебечущая фраза») по памяти; отличия от T. superciliaris и C. flavopectus по памяти.
- bangsia-flavovirens — окраска дана только по Wikipedia (ru/en); ru-статья называется «Чернолобая…», что намекает на тёмный лоб — не отражено в карточке, проверить. Голос не описан, в карточке так и сказано. Отличия от двух Chlorospingus по памяти.
- tangara-cyanotis — «горло и грудь голубые, брюхо светлое, охристое» у ssp. lutleyi — по памяти, сверить. Отличие от T. labradorides по памяти.
- cnemoscopus-rubrirostris — английское имя в индексе «Pink-billed Cnemoscopus» (в ACO Gray-hooded Bush Tanager): проверить, что это действительно имя eBird/Clements 2025. Подёргивание хвостом, серый «капюшон» до груди, голос — по памяти.
- iridosornis-porphyrocephalus — «середина брюха охристая, подхвостье рыжеватое» по памяти; сверить.
- anisognathus-notabilis — жёлтая полоса по темени до затылка, чёрный подбородок, отсутствие синего в крыле, отличие от A. somptuosus («горло жёлтое») и A. lacrymosus — по памяти; сверить с фото. Голос по памяти. Русское имя «Эквадорская танагра» из индекса (eBird ru) не похоже на перевод; оставлено как есть.
- dacnis-berlepschi — статус: в data VU (ACO/BIRDBASE), Красная книга Колумбии EN, en-Wikipedia пишет о понижении до LC в 2025; в тексте даны EN и LC-2025 — проверить по IUCN.
- phimosus-infuscatus — «на пастбищах у дороги, а не в лесу» (Чикаке) — предположение; «не боится людей» — полевой опыт.
- fulica-americana — окраска щитка у ssp. columbiana («белый или желтоватый») по памяти; сверить. «Изредка северные мигранты» — по статусу data (boreal_migrant + resident).
- gallinula-galeata — «ноги жёлто-зелёные» по памяти; отличие от Porphyrio martinica по памяти.
- nycticorax-nycticorax — «ноги желтоватые» и описание молодых по памяти.
- butorides-striata — вся карточка по памяти (текстов нет): окраска горла, цвет ног, голос; размер `crow` (≈ 40–44 см) — пограничный.
- mustelirallus-albicollis — голос («громкие хриплые ритмичные серии») по памяти, сверить с xeno-canto. «Лучшее место — болота Пуэрто-Асиса» взято из content/groups/herons-rails.md, а по data там «маловероятно».
- laterallus-melanophaius — голос («нисходящая трескучая трель») по памяти; размер sparrow при длине 14–18 см — пограничный.
- plegadis-falcinellus — «изредка появляется на болотах Саваны Боготы» — вывод из site_species (Ла-Флорида «возможно»); проверить по eBird, насколько регулярно.
- eurypyga-helias — сходство с Tigrisoma fasciatum условное (единственный похожий силуэт на каменистых ручьях); голос по памяти.
- rufirallus-fasciatus — отличие от Rufirallus viridis («брюхо рыжее без полос, лицо серое») по памяти. Указание на Пуэрто-Асис — из study_lists (все дни «маловероятно»).
- coragyps-atratus — «лапы почти достают до края хвоста» по памяти.
- elanus-leucurus — голос по памяти; «на ночь собирается группами» — общее знание о виде.
- cathartes-aura — «у колумбийских оседлых птиц» не упомянута светлая полоса на затылке (ssp. ruficollis) — возможно, стоит добавить. Сроки осеннего пролёта мигрантов через Колумбию (октябрь) — проверить.
- pandion-haliaetus — «к октябрю мигранты уже на месте» и верхняя граница «до 1 000 м, изредка выше» — проверить.
- micrastur-plumbeus — отличие от Cryptoleucopteryx plumbea (тоже серый с одной белой полосой на хвосте и оранжевыми ногами) по памяти; число полос на хвосте у M. ruficollis («три-четыре») по памяти.
- glaucidium-parkeri — отличие от G. jardinii («темя в густых мелких точках», «песня — длинная серия») по памяти и по карте glaucidium-jardinii; год описания «1990-е» (1995?) — проверить. Записи в Эль-Энканто / на Ла-Дримофиле (Уила, верхняя Магдалена) странны для вида восточного склона — возможно, ошибки определения в GBIF.
- nyctibius-grandis — «отблеск глаз в луче фонаря» по en-Wikipedia; отличия от N. griseus и N. aethereus по памяти.

## Data issues

- elanus-leucurus — в data высоты 0–1 500 м, habitat_aco «Forest»; вид обычен на Саване Боготы (2 600 м) и «точно» в Ла-Флориде. Высотная граница и тип местообитания, похоже, неверны.
- coragyps-atratus — max 2 000 м в data, но «точно» в Чингасе (3 000–3 500 м), Обсерватории колибри и у Сибундоя.
- fulica-americana — max 2 500 м в data, но «точно» на Ла-Коче (2 800 м) и в Сумапасе (3 600–3 800 м).
- plegadis-falcinellus — max 500 м в data, но есть в данных по Ла-Флориде (2 540 м).
- eurypyga-helias — habitat_aco «Marine» — явно неверно (лесные реки и ручьи).
- pandion-haliaetus — habitat_aco «Forest» — странно для скопы.
- nyctibius-grandis — elevation_m.min = «L» (строка вместо числа) в data/species и species_index.
- dacnis-berlepschi — IUCN в data VU, en-Wikipedia (и wikidata в data) — LC с 2025 г.; mass_g = null.
- cnemoscopus-rubrirostris, dacnis-egregia, butorides-striata — нет русского имени в индексе (names.ru = null); в карточках использовано английское.
- glaucidium-parkeri — точки в Уиле (Эль-Энканто, Ла-Дримофила) для вида восточного склона — проверить GBIF-записи на ошибки определения.
