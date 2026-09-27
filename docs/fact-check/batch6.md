# Факт-чек: партия 6 (виды, переименованные или выделенные при переходе на eBird/Clements 2025)

Карточки написаны 27.09.2026 по data/species, pipeline/mappings/clements2025.json, выдержкам Wikipedia о родительских
или соседних видах (у 13 из 15 видов своей выдержки в data/texts нет), карточкам похожих видов и полевым знаниям агента.
Разметка `traits` — по ревизии словаря 27.09.2026. Формат: `slug — что проверить`.

## Общее

- Нет data/texts (писалось по данным проекта, соседним статьям Wikipedia и памяти): все, кроме setophaga-petechia и
  zimmerius-chrysops. После CI-прогона `wikipedia` для новых слагов стоит сверить окраску, длину и голос с их собственными статьями.
- Голоса у всех 15 видов по памяти или обобщённо (формулировки намеренно общие).
- Годы разделений указаны только там, где есть источник: Formicivora (Clements 2023, Wikipedia: Southern white-fringed antwren),
  Setophaga aestiva и Tunchiornis ferrugineifrons (2025, заметки clements2025.json). В остальных карточках — «до разделения в eBird/Clements» без года.
- `feeder` не поставлен никому: ни один вид не отмечен «точно» на точке с кормушками подходящего корма.

## По видам

- chlorothraupis-frenata — длина ≈17 см (по C. carmioli), size `thrush` на границе; жёлтая уздечка у обоих полов или ярче у самки — по памяти; голос по памяти.
- contopus-bogotensis — светлая уздечка, тонкое кольцо у глаза, подрагивание хвостом после посадки — по описанию Southern Tropical Pewee и памяти; голос («тонкая трель», «чистый свист») по памяти. Отличия согласованы с карточкой contopus-virens.
- formicivora-intermedia — окраска самки (беловато-охристый низ, белая бровь, тёмная щека) по памяти; голос («двусложные посвисты») по памяти; tone `bright` за чёрно-белый контраст самца.
- furnarius-cinnamomeus — длина не найдена (масса 54 г по BIRDBASE, крупнее F. leucopus 15–18 см), size `thrush`; признаки (серое темя, беловатый глаз) — из карточки furnarius-leucopus; голос-дуэт по памяти.
- lophornis-verreauxii — окраска самца (зелёный хохолок, удлинённые перья шеи, рыжевато-бронзовый хвост) и самки (светлая полоса на щеке) по памяти, проверить обязательно; `crest` в marks под вопросом.
- mionectes-galbinus — розоватое основание подклювья и голос («высокий писк сериями») по памяти/по описанию M. olivaceus.
- ocreatus-peruanus — охристые (не белые) «штанишки» как главное отличие от O. underwoodii — по памяти, проверить обязательно; остальная окраска по описанию O. underwoodii.
- polioptila-bilineata — описание группы bilineata по Wikipedia (Tropical gnatcatcher); `wing_patch` и `cap` по новым правилам; голос по описанию P. plumbea.
- setophaga-aestiva — `marks: [plain]` при том, что у части взрослых самцов осенью есть слабые рыжие штрихи на груди; проверить, не лучше ли `streaked_breast`. Голос по памяти.
- setophaga-petechia — объём рыжего на голове у подвида peruviana (шапочка или вся голова) — в карточке обе версии; голос по памяти.
- tolmomyias-viridiceps — окраска (оливковое лицо без охристого, светлое подклювье) по описанию T. flaviventris и памяти; голос по памяти.
- troglodytes-musculus — `colors: [brown, white]` (низ беловато-охристый, можно спорить о `rufous`); голос по памяти.
- tunchiornis-ferrugineifrons — светлый глаз, сероватое лицо, охристая грудь — по описанию T. ochraceiceps и памяти; голос по памяти.
- tyto-furcata — длина ≈33–40 см по памяти, size `[pigeon, crow]` по диапазону через границу 36 см; «в среднем крупнее Western Barn Owl» по памяти; `spotted_breast` за мелкие точки на низе.
- zimmerius-chrysops — голос по памяти; «через глаз тёмная черта» по Wikipedia en.

## Data issues

- zimmerius-chrysops — «точно»/«возможно» на тихоокеанском склоне Нариньо (Ла-Планада 374 осенних записи, Ла-Нутрия, Рио-Ньямби, Авес-и-Флорес, Бангсиас-лодж), хотя по Wikipedia вида нет на юго-западе Нариньо: вероятно, GBIF сводит Z. albigularis (Choco Tyrannulet) в Z. chrysops. Нужна запись в pipeline/mappings/gbif_region_splits.json (narino_pacific → zimmerius-albigularis); карточка zimmerius-albigularis сейчас пишет, что записей вида нет.
- formicivora-intermedia — «возможно» в Чикаке (2 000–2 700 м, 116 осенних записей) при высотах вида 0–1 000 м (экстремум 2 000): радиус GBIF захватывает нижние склоны; в карточке так и сказано.
- Старые карточки описывают птиц маршрута под родительскими видами и теперь устарели: furnarius-leucopus (птицы Тумако — теперь furnarius-cinnamomeus), polioptila-plumbea (Км 42 и побережье — теперь polioptila-bilineata), tolmomyias-flaviventris (Путумайо — теперь tolmomyias-viridiceps), ocreatus-underwoodii (абзац про Сибундой). Стоит переписать route-абзацы и similar.
- leiothlypis-peregrina — в similar стоит setophaga-petechia с текстом про перелётную птицу; после разделения это setophaga-aestiva.
- data/species/setophaga-petechia.json — traits.elevation_m.max_extreme = "F" (мусор из BIRDBASE).
- data/species/furnarius-cinnamomeus.json — elevation max_extreme 2 700 м для вида тихоокеанских низин (до 800 м) — вероятно, унаследовано от широкого F. leucopus.
- data/species/mionectes-galbinus.json — max_extreme 3 000 м, похоже на унаследованное от Olive-streaked (Панама).
- Русских имён нет у 11 из 15 видов; у setophaga-petechia `ru` «Жёлтая древесница» — это имя широкого вида Yellow Warbler (ru.wikipedia), для Mangrove Yellow Warbler оно неточное.
