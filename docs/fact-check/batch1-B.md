# Факт-чек: партия 1, список B (танагры, овсянки, певуны, трупиалы)

Карточки написаны 27.09.2026. Ниже — что проверить, формат «slug — что проверить».

## Таксономия и данные (важно)

- myiothlypis-chrysogaster — сопоставление вида: на маршруте (склон Чоко) живёт Myiothlypis chlorophrys (Choco Warbler), а eBird-имя Cuzco Warbler относится к перуанско-боливийскому виду; в `pipeline/mappings/gbif_to_species.json` chlorophrys сведён в chrysogaster. Проверить маппинг ACO→eBird и английское имя на сайте; в карточке это сказано в тексте. Приметы (полосатое темя, короткая бровь перед глазом) взяты из сравнения в es-Wikipedia — сверить.
- dacnis-lineata — записи на Км 42 (тихоокеанская сторона), скорее всего, относятся к Yellow-tufted Dacnis (D. egregia), которого нет в data/species_index.json. Проверить, выделен ли egregia в Clements 2025 и нужен ли отдельный вид в индексе; тогда убрать Км 42 из site_species для lineata.
- dubusia-taeniata — нет русского имени и текстов Wikipedia; в ACO «Buff-breasted Mountain-Tanager», в Clements «Buff-banded». Сверить границы вида после раздела рода и описание оперения (голубая пестрая бровь, охристая полоса на груди).
- anisognathus-igniventris — колумбийские птицы относятся к группе lunulatus (иногда отдельный вид); проверить, что приметы (алое пятно за глазом, голубые плечо и поясница) верны для колумбийской формы.
- tephrophilus-wetmorei — нет текстов Wikipedia; описание оперения (чёрная маска в жёлтой рамке, оливковая спина, голубовато-серое плечо) по памяти; голос в карточке не описан.
- geospizopsis-unicolor — в data минимальная высота 800 м выглядит ошибкой источника (вид парамо, в основном 3 000–4 600 м); в тексте указано «в основном выше 3 000 м».

## Внешность

- iridosornis-rufivertex — рыже-каштановое подхвостье «у большинства популяций»: проверить, у какого подвида на юго-западе Колумбии (Бордонсильо) подхвостье синее или шапочка оранжевее.
- chlorochrysa-phoenicotis — крошечное оранжево-красное пятнышко за ухом у самца (Wikipedia его не упоминает, только серые пятна).
- chlorothraupis-stolzmanni — цвет глаза и наличие жёлтого кольца: en-Wikipedia пишет «бледно-серо-голубая радужка, без кольца», es-Wikipedia упоминает жёлтое кольцо.
- ixothraupis-rufigula — золотисто-зеленоватая поясница и зелёная чешуйка на спине.
- sporophila-telasco — белое пятно у основания маховых, светлая поясница и пестрины на спине самца; цвет клюва.
- tangara-chilensis — цвет поясницы у колумбийской (путумайской) формы: только красная или красная с жёлтым.
- psarocolius-angustifrons — цвет клюва и лба у популяций Путумайо (предгорная форма alfredi с желтоватым клювом и жёлтым лбом против низинной с тёмным клювом).
- diglossa-lafresnayii — отличие от Black Flowerpiercer (D. humeralis): у восточноандского подвида humeralis тоже есть серое плечо; проверить формулировку «мельче, матовый, плечо мелкое или его нет».
- diglossa-indigotica — отличие от Deep-blue Flowerpiercer (D. glauca): цвет глаза у glauca (жёлто-оранжевый).
- dacnis-lineata — отличия от Blue Dacnis (цвет глаза) и Yellow-bellied Dacnis (красный глаз).
- bangsia-edwardsi — подтвердить, ходит ли вид на фруктовые кормушки в Авес-и-Флорес / Бангсиас-лодже (feeder в traits не поставлен).
- chrysothlypis-salmoni — окраска самки (es-Wikipedia обрывается на «алое заменено на…»).

## Голос

- diglossa-lafresnayii, anisognathus-igniventris, atlapetes-schistaceus, dubusia-taeniata («простой двусложный свист»), myiothlypis-chrysogaster, spinus-spinescens, sporophila-telasco, chrysomus-icterocephalus — голос описан по общим знаниям, без источника в data/texts.
- bangsia-edwardsi, ixothraupis-rufigula, chlorochrysa-phoenicotis, chrysothlypis-salmoni, diglossa-indigotica, dacnis-lineata — голос дан осторожно («тонкие высокие звуки»), уточнить.

## Маршрут

- geospizopsis-unicolor, conirostrum-rufum, chrysomus-icterocephalus, spinus-spinescens, dubusia-taeniata — основные точки (Чингаса, Сумапас, Ла-Флорида, Ботанический сад) не входят в itinerary.json; в тексте предложены свободные дни в Боготе 2 и 25 октября. Уточнить у владельца, планируются ли выезды.
