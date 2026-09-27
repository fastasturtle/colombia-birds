# Факт-чек: партия 2, список B (муравьеловки, антпитты, печники, тиранновые, прочие воробьиные, голуби, попугаи)

Карточки написаны 27.09.2026 (23 вида). Ниже — что проверить, формат «slug — что проверить».

## Данные (Data issues)

- metopothrix-aurantiaca — русское имя «Коронадо» в data/species_index.json похоже на кальку испанского «coronado» и не выглядит устоявшимся; в тексте карточки не используется (только английское). Проверить источник `name_ru_source`.
- metopothrix-aurantiaca — в site_species вид «maybe» на Финке Дискосура (800–1 000 м, 471 запись), хотя по Wikipedia в Колумбии он не выше 500 м; вероятно, радиус 7 км захватывает низины. Проверить.
- chamaeza-turdina — в data высоты 900–2 600 м, а en-Wikipedia для Колумбии даёт 1 600–2 800 м; Эль-Энканто (1 350 м) ниже этого пояса. В тексте указаны высоты по Wikipedia; проверить, не смешаны ли записи с Short-tailed Antthrush.
- cichlopsis-leucogenys — высоты в data 750–850 м (min_extreme 100) выглядят слишком узкими; вид отмечен в Авес-и-Флорес (1 100–1 300 м) и Рио-Ньямби (1 100–1 900 м). В тексте высоты не названы. Статус: ACO «EN», Wikidata «vulnerable» — в тексте нейтрально «угрожаемый».
- columbina-buckleyi — en-Wikipedia пишет «Ecuador and Peru», без Колумбии; вид есть в ACO и в GBIF у Тумако/Км 42. Проверить, подтверждено ли присутствие в Нариньо (не перепутаны ли записи с C. talpacoti / C. cruziana).
- attila-torridus — en-Wikipedia: в Колумбии ниже 200 м, es-Wikipedia: «одна старая находка в Нариньо»; GBIF даёт 190 записей у Финки Марагрикола. Проверить, что это действительно регулярный вид района Тумако.
- frederickena-fulva — вид равнинный (до ~700 м), Исла-Эскондида 650–1 600 м; в тексте совет искать «в нижней части участка» — проверить у гида/по eBird, где его отмечают.
- campylorhamphus-pusillus — «maybe» на Км 42 (50–150 м): возможно, это Red-billed Scythebill (C. trochilirostris); Км 42 в тексте не упомянут.
- grallaria-rufocinerea — content/families/grallariidae.md пишет «в Сибундое ищем Bicolored», а site_species даёт только Трамплин птиц (maybe), Сибундой — unlikely. Одно из двух поправить.
- amazona-farinosa — content/groups/parrots.md называет Орито, а в site_species Орито «unlikely» (4 записи); вид «maybe» только в Исла-Эскондиде.
- tunchiornis-ochraceiceps (не моя карточка, используется в similar) — в индексе `ru` = «Hylophilus ochraceiceps» (латынь вместо русского имени).
- elaenia-frantzii — en-Wikipedia относит колумбийские Анды к подвиду pudica только в Западных и Центральных хребтах, но GBIF даёт тысячи записей у Боготы (Восточные Анды). Проверить распространение подвидов.

## Внешность и отличия

- margarornis-squamiger — у колумбийского подвида perlatus бровь белёсая и капли белее (по Wikipedia); проверить «светлое горло» (у номинативной формы горло ярко-охристо-жёлтое).
- margarornis-squamiger — отличие от Fulvous-dotted Treerunner (M. stellatus): «горло чисто белое, капли только на верхе груди».
- scytalopus-latrans — отличие от Ash-colored Tapaculo (Myornis senilis): светлее и длиннохвостее.
- scytalopus-vicinior — длина тела в источниках не найдена (масса 23 г); размер sparrow поставлен по аналогии с родом.
- scytalopus-micropterus — отличие от White-crowned Tapaculo (S. atratus): песня «серия одинаковых нот без двойных» — по памяти, проверить.
- metopothrix-aurantiaca — отличия от Ochre-crowned Greenlet (светлый глаз, сероватый низ) и Dusky-capped Greenlet.
- grallaria-rufocinerea — формулировка «двумя популяциями в Центральных Андах»: южная популяция (romeroana) — верховья Магдалены и запад Путумайо, возможно, это уже стык хребтов.
- drymophila-caudata — отличие от Streak-headed Antbird (D. striaticeps) только по ареалу и вступлению песни; уточнить, какая Drymophila реально живёт в Эль-Энканто / Ла-Дримофиле (Уила).
- frederickena-fulva — отличия от Fasciated Antshrike (красный глаз, самка с рыжей шапочкой) и Lined Antshrike (светлый глаз, у самки рыжая шапочка, белые полоски у самца на спине).
- chamaeza-turdina — отличия от Short-tailed (охристый низ в продольных пестринах, светлая полоса на конце хвоста) и Barred Antthrush.
- epinecrophylla-spodionota — отличие от Ornate Stipplethroat (ярко-рыжая спина); на маршруте Ornate не отмечен.
- grallaricula-cucullata — бледный клюв (жёлтый/оранжево-розовый) у номинативного подвида; отличия от Slate-crowned и Ochre-breasted Antpitta.
- syndactyla-subalaris — отличия от Montane Foliage-gleaner («очки») и Streak-capped Treehunter (почти без штрихов снизу).
- elaenia-frantzii — белая полоска в шапочке: en-Wikipedia пишет о «в основном скрытом белом пятне», карточка Sierran Elaenia — что его нет. В карточке «обычно не видно»; сверить.
- fluvicola-nengeta — отличие от Pied Water-Tyrant (чёрная спина, нет маски).
- tolmomyias-traylori — «описан в 1997 году» (Schulenberg & Parker?) — проверить год; отличия от Yellow-margined (тёмный глаз, жёлтое зеркальце) и Gray-crowned Flatbill.
- attila-torridus — отличия от Cinnamon Becard и Rufous Mourner; хищный «уоиир» как у орла-хохлача (по Wikipedia «hawk-eagle-like»).
- poecilotriccus-ruficeps — размер 9–10 см поставлен как `hummingbird` («крошки до 10 см»); проверить, не лучше ли `sparrow`. Отличие от Common Tody-Flycatcher.
- donacobius-atricapilla — цвета: охристый низ не имеет точного значения в словаре, поставлены только [brown, black].
- cichlopsis-leucogenys — окраска подвида chubbi (тёмно-каштановое горло, каштановый налёт на брюхе); отличие от Pale-vented Thrush (тёмные штрихи на горле, белое подхвостье).
- columbina-buckleyi — размер 18 см поставлен как `thrush`, у Croaking Ground Dove в карточке `sparrow`; проверить единообразие. «Чёрные подкрылья» согласовано с карточкой columbina-cruziana.
- amazona-farinosa — отличия от Yellow-crowned Amazon (узкое кольцо у глаза, больше жёлтого) и Orange-winged Amazon.

## Голос

- scytalopus-latrans — «неторопливее, чем у большинства тапакуло» (по es-Wikipedia); конкретный рисунок песни не описан.
- scytalopus-micropterus — «серия двойных нот» по en-Wikipedia (couplets).
- drymophila-caudata — «хриплые жужжащие звуки» после вступления — по аналогии с родом.
- frederickena-fulva, syndactyla-subalaris, campylorhamphus-pusillus, tolmomyias-traylori, attila-torridus, poecilotriccus-ruficeps, fluvicola-nengeta, grallaria-rufocinerea, grallaricula-cucullata, chamaeza-turdina — голоса пересказаны по en-Wikipedia; сверить транскрипции с записями xeno-canto.
- elaenia-frantzii — позывки «пиу» / «брри» даны по северным подвидам; у южных (колумбийских) по Wikipedia «zrreeu» и «peuuwww».
- donacobius-atricapilla — распределение ролей в дуэте (самец свистит, самка скрежещет) по памяти.
- amazona-farinosa — «чок-чок», «киэу» — по памяти.
- cichlopsis-leucogenys — описание песни по эквадорским/венесуэльским источникам.

## Маршрут

- grallaricula-cucullata — утверждение, что её подманивают к кормушкам с червями в Ла-Дримофиле, взято из content/families/grallariidae.md; проверить у организаторов.
- grallaria-rufocinerea — «в верхней части дороги, выше 2 200 м» на Трамплине птиц: проверить, до каких высот доходит маршрут (в sites.json 1 100–2 400 м).
- tolmomyias-traylori — «целевой вид Эль-Эскондите» взят из content/families/tyrannidae.md.
