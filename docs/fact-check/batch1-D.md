# Факт-чек: партия 1, список D (кулики, голуби/кукушки, пастушки, утки, морские птицы)

Карточки написаны 27.09.2026 по data/species, data/texts (Wikipedia en), data/site_species.json и полевым знаниям.
Ниже то, что стоит проверить. Формат: `slug` — что проверить.

## Данные и таксономия (важно)

- `numenius-phaeopus` — **маппинг ACO → eBird**: ACO «Whimbrel» сопоставлен с Eurasian Whimbrel (N. phaeopus), но в Колумбии зимует Hudsonian Whimbrel (N. hudsonicus, отдельный вид в Clements с 2023). `numenius-hudsonicus` в индексе нет. Вероятно, нужно исправить `pipeline/mappings/aco_to_ebird.json`, переименовать карточку и русское имя. В тексте карточки уже сказано, что у наших птиц поясница бурая, без белого клина.
- `rallus-limicola` — в Колумбии оседлая андская форма (aequatorialis; у IOC отдельный вид Ecuadorian Rail). Проверить описание окраски именно этой формы (рыжая грудь, серые щёки), «мельче и темнее северных» и голос «кидик» для неё. Высоты в данных до 2 370 м, а Ла-Коча на 2 800 м.
- `oxyura-jamaicensis` — рисунок головы андских самцов: у формы andina (Богота) щёки с белыми пятнами разной величины, у ferruginea (Нариньо, Ла-Коча) голова целиком чёрная? Сохраняется ли голубой клюв у андских самцов в октябре? В данных максимальная высота 2 200 м, но вид «точно» на Ла-Коче и в Сумапасе.
- `fulica-ardesiaca` — действительно ли на Ла-Коче встречается и American Coot (в site_species «точно»), или это ошибки определения или смешение в GBIF. Проверить отличие «клюв белый с тёмным кольцом у конца» для колумбийской формы American Coot (columbiana) и тёмное подхвостье у F. a. atrura.
- `leptotila-conoveri` — статус расходится: ACO 2022 EN, Libro Rojo VU, BirdLife NT. В тексте осторожно: «от почти угрожаемого до под угрозой».

## Голос (формулировки по памяти)

- `gallinago-nobilis` — позыв при взлёте «кэч» и токование.
- `leptotila-conoveri` — голос описан обобщённо, как у рода.
- `fulica-ardesiaca` — «кук», «пит».
- `rallus-semiplumbeus` — «хрюканье и визг, серии писклявых нот».
- `porphyriops-melanops` — щелчки, квохтанье, нисходящая серия: по памяти, проверить по xeno-canto.
- `anas-andium`, `anas-bahamensis` — голоса самца и самки описаны обобщённо.
- `sula-nebouxii` — у самца свист, у самки гоготание (общеизвестно, но свериться).

## Признаки и отличия

- `chroicocephalus-serranus` — в каком наряде птицы на Ла-Коче в октябре (с капюшоном или без).
- `gallinago-nobilis` — отличие от Jameson's Snipe (низ сплошь в полосах, широкие округлые крылья) взято из Wikipedia; проверить, нет ли на Бордонсильо и Ла-Коче также Wilson's или Pantanal Snipe.
- `thalasseus-maximus` — Sandwich Tern на Тихом океане: какой таксон (Cabot's, чёрный клюв с жёлтым кончиком), встречаются ли там Elegant Terns, с которыми тоже можно спутать.
- `vanellus-chilensis` — утверждение «кричит и ночью».
- `actitis-macularius` — отличие от Solitary Sandpiper («кивает, а не качается»).
- `columbina-cruziana` — отличия от Ecuadorian Ground Dove (чёрные подкрылья) и Plain-breasted Ground Dove.
- `crotophaga-major` — отличие от Great-tailed Grackle: «глаз жёлтый» у гракла (у самки тоже светлый?).
- `leptotila-conoveri` — отличие от White-tipped Dove (граница груди, контраст горла) и от White-throated Quail-Dove; ходит ли вид на кормушки с кукурузой в Эль-Энканто (layer feeder не ставил).
- `leptotila-pallida` — цвет кожи вокруг глаза у White-tipped Dove в Нариньо (синяя или красная), чтобы не путать; в how это не использовано.
- `zenaida-auriculata` — «вместе с Rufous-collared Sparrow заселяет горные города»: образ, не факт из источника.
- `porphyriops-melanops` — высоты колумбийской популяции (около 2 500–3 000 м) и статус EN в национальной Красной книге (есть в data: libro_rojo EN).
- `anas-georgica` — «местная популяция считается исчезнувшей с 1950-х» (Niceforo's pintail, по Wikipedia последняя запись 1952).
- `anas-andium` — цвет клюва (тёмный сизый) и зеркальце (зелёное с охристой каймой).
- `anas-bahamensis` — «с Blue-winged Teal на прудах Марагриколы»: образ по site_species (оба вида на Марагриколе), не наблюдение.
- `fregata-magnificens` — отличия самки Great Frigatebird (горло серовато-белое, красное кольцо у глаза).
- `sula-nebouxii` — где в Колумбии обычна («особенно на юге, у Нариньо»); отличие от Peruvian Booby («белые чешуйки на спине»).
- `rallus-semiplumbeus`, `porphyriops-melanops` — Ла-Флорида только как вариант свободного дня 2 или 25 октября (itinerary); подтвердить с владельцем, стоит ли её упоминать.
