# Портреты семейств (`content/families/`)

Вводный слой сайта: короткий портрет семейства для начинающего, который готовится к туру
(Анды, амазонские предгорья Путумайо, Чоко Нариньо, тихоокеанское побережье). Рендерится вверху
страницы `/families/<slug>/` (см. `site/src/lib/content.ts`, `site/src/pages/families/[slug].astro`).
Нет файла — на странице только список видов.

## Группы

Над семействами есть неформальный слой «групп» как в полевом определителе (`data/groups.json`,
18 групп, рукописный файл: id, названия, однофразовое описание, коды семейств; каждое семейство
ровно в одной группе). Страницы `/groups/<id>/`, каталог `/families/` сгруппирован по ним.
Портреты групп лежат в `content/groups/<id>.md` (все 18) с той же схемой frontmatter, что у семейств,
но вместо `family` — `group: <id>`, а `confusable` ссылается на другие группы (`- group: <id>` + `how`);
в `recognize` — как с первого взгляда различать семейства внутри группы. Рендер: `groupContent()` в
`site/src/lib/content.ts`, страница `site/src/pages/groups/[id].astro`. Русские названия отрядов — `data/orders_ru.json`.

## Формат: `content/families/<slug>.md`

`<slug>` и `family` (код) — из `data/families.json`.

```markdown
---
family: gralla2                 # код семейства из data/families.json (обязательно)
recognize:                      # 3–5 пунктов по-русски: как узнать семейство с первого взгляда
  - "..."                       # силуэт, размер, поведение, где сидит, как двигается
confusable:                     # 1–3 семейства, с которыми путают, и главное отличие
  - family: rhinoc1             # код семейства (станет ссылкой)
    how: "..."
route_note: "..."               # 1–3 предложения: что ждать на маршруте (виды из focus, локации, кормушки, высоты)
fact: "..."                     # одно запоминающееся предложение
en:                             # то же по-английски для гидов
  recognize: ["..."]
  route_note: "..."
  fact: "..."
---
Русский портрет: 1–2 коротких абзаца, 120–220 слов. Что это за семейство, как узнать,
как определять до вида, где и как искать на этом маршруте.

## English

Тот же портрет по-английски.
```

Правила:
- Тело — простые абзацы через пустую строку, без markdown-разметки (она не рендерится).
- Строки YAML — в двойных кавычках; внутри кавычек используй «ёлочки», не `"`.
- Английское и латинское названия семейства уже есть в заголовке страницы, не повторяй их первой фразой.
- Опирайся на `data/focus_species.json` (виды маршрута), `data/species/*.json` (высоты, биотопы,
  эндемики), `target_species` в `data/sites_resolved.json` (какие виды на какой локации) и собственные
  знания. Не копировать тексты из платных/несвободных определителей (правило 3 AGENTS.md).
- Названия видов в тексте — английские (как в заголовках карточек), при необходимости с русскими.
- Проверка: `cd site && npm run build && npm run shots -- /families/<slug>/`.

## Сделано (пробная партия)

grallariidae, trochilidae, thraupidae, rhinocryptidae, cotingidae, thamnophilidae.

## Осталось: 51 семейств

Все семейства, где есть хотя бы один вид из `data/focus_species.json`, кроме сделанных.
Последний столбец — число фокусных видов (приоритет по убыванию разумен).

| код | slug | латынь | English | фокусных видов |
|---|---|---|---|---|
| tinami1 | tinamidae | Tinamidae | Tinamous | 3 |
| anatid1 | anatidae | Anatidae | Ducks, Geese, and Waterfowl | 5 |
| cracid2 | cracidae | Cracidae | Guans, Chachalacas, and Curassows | 7 |
| odonto1 | odontophoridae | Odontophoridae | New World Quail | 2 |
| columb2 | columbidae | Columbidae | Pigeons and Doves | 6 |
| cuculi1 | cuculidae | Cuculidae | Cuckoos | 2 |
| caprim2 | caprimulgidae | Caprimulgidae | Nightjars and Allies | 2 |
| nyctib1 | nyctibiidae | Nyctibiidae | Potoos | 1 |
| apodid1 | apodidae | Apodidae | Swifts | 1 |
| rallid1 | rallidae | Rallidae | Rails, Gallinules, and Coots | 9 |
| psophi1 | psophiidae | Psophiidae | Trumpeters | 1 |
| scolop2 | scolopacidae | Scolopacidae | Sandpipers and Allies | 1 |
| larida1 | laridae | Laridae | Gulls, Terns, and Skimmers | 3 |
| podici1 | podicipedidae | Podicipedidae | Grebes | 1 |
| opisth1 | opisthocomidae | Opisthocomidae | Hoatzin | 1 |
| eurypy1 | eurypygidae | Eurypygidae | Sunbittern | 1 |
| phaeth1 | phaethontidae | Phaethontidae | Tropicbirds | 1 |
| hydrob1 | hydrobatidae | Hydrobatidae | Northern Storm-Petrels | 1 |
| procel3 | procellariidae | Procellariidae | Shearwaters and Petrels | 1 |
| fregat1 | fregatidae | Fregatidae | Frigatebirds | 1 |
| sulida1 | sulidae | Sulidae | Boobies and Gannets | 2 |
| thresk1 | threskiornithidae | Threskiornithidae | Ibises and Spoonbills | 2 |
| ardeid1 | ardeidae | Ardeidae | Herons, Egrets, and Bitterns | 1 |
| peleca1 | pelecanidae | Pelecanidae | Pelicans | 1 |
| accipi1 | accipitridae | Accipitridae | Hawks, Eagles, and Kites | 2 |
| strigi1 | strigidae | Strigidae | Owls | 5 |
| trogon1 | trogonidae | Trogonidae | Trogons | 5 |
| momoti1 | momotidae | Momotidae | Motmots | 1 |
| alcedi1 | alcedinidae | Alcedinidae | Kingfishers | 1 |
| buccon2 | bucconidae | Bucconidae | Puffbirds | 4 |
| galbul2 | galbulidae | Galbulidae | Jacamars | 3 |
| capito2 | capitonidae | Capitonidae | New World Barbets | 3 |
| semnor1 | semnornithidae | Semnornithidae | Toucan-Barbets | 1 |
| rampha1 | ramphastidae | Ramphastidae | Toucans | 7 |
| picida1 | picidae | Picidae | Woodpeckers | 5 |
| falcon1 | falconidae | Falconidae | Falcons and Caracaras | 2 |
| psitta3 | psittacidae | Psittacidae | New World and African Parrots | 6 |
| formic2 | formicariidae | Formicariidae | Antthrushes | 1 |
| furnar2 | furnariidae | Furnariidae | Ovenbirds and Woodcreepers | 11 |
| piprid1 | pipridae | Pipridae | Manakins | 1 |
| tyrann2 | tyrannidae | Tyrannidae | Tyrant Flycatchers | 12 |
| vireon1 | vireonidae | Vireonidae | Vireos, Shrike-Babblers, and Erpornis | 1 |
| corvid1 | corvidae | Corvidae | Crows, Jays, and Magpies | 2 |
| donaco1 | donacobiidae | Donacobiidae | Donacobius | 1 |
| troglo1 | troglodytidae | Troglodytidae | Wrens | 3 |
| turdid1 | turdidae | Turdidae | Thrushes and Allies | 4 |
| fringi1 | fringillidae | Fringillidae | Finches, Euphonias, and Allies | 3 |
| passer3 | passerellidae | Passerellidae | New World Sparrows | 5 |
| icteri1 | icteridae | Icteridae | Troupials and Allies | 3 |
| paruli1 | parulidae | Parulidae | New World Warblers | 4 |
| cardin1 | cardinalidae | Cardinalidae | Cardinals and Allies | 1 |
