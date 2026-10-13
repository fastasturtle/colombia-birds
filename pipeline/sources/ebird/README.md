# eBird: наблюдения Ани в туре

Входы шага `observations` (`pipeline/steps/build_observations.py`), пишутся командой
`uv run python run.py observations --import <MyEBirdData.csv>` из личной выгрузки eBird Ани («Download my data»).

| Файл | Что |
|---|---|
| `colombia_2026.csv` | строки выгрузки с `State/Province` `CO-*` и датой не раньше начала тура (первая дата `data/itinerary.json`), все столбцы, тот же заголовок |
| `life_list_before_trip.json` | `{before, exported, species}`: научные названия видов, отмеченных где угодно до начала тура (для «новый вид для Ани»), без координат и дат |

Полная выгрузка (вся история наблюдений по миру с местами и датами) — личные данные: в репозиторий не попадает,
держать вне его. Руками эти файлы не править: новая выгрузка → повторить `--import`.
