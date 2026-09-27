# Рукописный контент

Пишется агентами, сливается с `data/` при сборке сайта. Формат:

## `content/species/<slug>.md`

```markdown
---
id: grallaria-milleri            # обязательно, = id в data/species_index.json
difficulty: medium               # easy | medium | hard — насколько легко узнать в поле
lynx_page: 412                   # страница в Lynx «Birds of Colombia» (Ayerbe-Quiñones), если известна
key_features:                    # 3–5 признаков, по которым узнаём
  - "Рыжевато-бурая грудь с узкой тёмной полосой"
similar:                         # похожие виды и чем отличаются
  - id: grallaria-rufula
    how: "мельче, без полосы на груди, выше по высоте"
voice: "Серия из 3–5 нисходящих свистов"
sources:                         # если текст опирается на CC-источники
  - "Wikipedia: Brown-banded antpitta (CC BY-SA 4.0)"
---
Свободный текст по-русски: где искать, поведение, интересные факты.
```

## `content/similar/<slug-a>--<slug-b>.md`

Сравнение двух (или группы) похожих видов: таблица признаков, на что смотреть первым делом.
