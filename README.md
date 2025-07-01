# find-free-huts
Finde freie DAV/SAC/ÖAV Hütten an einem oder mehrern Daten.

Logge dich bei https://www.hut-reservation.org ein. öfnne über den Rechtsklick und dann Inspect(Q)/Untersuchen(Q) die Entwickleroptionen. Wähle im oberen Menü "Storage"/"Speicher" aus und navigiere zu den Cookies. Dort findest du einen Wert für SESSION und XSRF-TOKEN. Diese beiden Werte kopierst du an die entsprechende Stelle in HEADERS_COOKIES.py.

Zu Beginn der Datei find_neighboured_free_huts.py findest du weitere Variablen, die du setzen kannst, aber nicht musst. 

```python
DATE_TO_CHECK = ["2025-07-09","2025-07-10", "2025-07-11","2025-07-12"] # <-- Hier dein Wunschdatum eintragen

NUMBER_OF_PEOPLE = 5  # Anzahl der Personen für die Reservierung, 0 für gibt an, dass es egal ist

BORDERS = {
    "west": 9.635,  # Längengrad Westgrenze
    "east": 12.401,  # Längengrad Ostgrenze
    "north": 47.769,  # Breitengrad Nordgrenze
    "south": 46.851   # Breitengrad Südgrenze
}

COUNTRY = "AT"  # Land, für das die Hütten aufgelistet werden sollen, z.B. "AT" für Österreich, "CH" für Schweiz, "DE" für Deutschland

ALLOW_DOUBLE_HUT = False  # Wenn True, kann eine Hütte mehrmals in einer Gruppe sein, sonst nur einmal
ALLOW_STATIONARY_HUTS = False  # Wenn True, werden auch Gruppen gebildet mit nur einer Hütte, die an allen Tagen verfügbar ist
MAX_DISTANCE = 10  # Maximale Distanz in km, um benachbarte Hütten zu finden (Luftlinie)
``` 

In <code>DATE_TO_CHECK</code> gibst du die Tage an, für die du deine Tour planst. Dabei ist das letzte Datum dein Abreisetag und das erste Datum dein Anreisetag. Die Daten müssen nicht sortiert sein und auch nicht vollständig. Alle Daten zwischen dem frühsten und spätesten Datum werden aufgefüllt (sort_and_fill_Datelist()).

<code>NUMBER_OF_PEOPLE</code> stellt sicher, dass nur Hütten berücksichtigt werden mit einer Mindestanzahl von freien Plätzen. Diese können sich jedoch in unterschiedlichen Zimmerkategorien befinden. Dies könnte in <code>check_availability(hut_id, arrival, departure=None)</code> ergänzt werden, da der Wert <code>availabilityPerDayDTOs[idx]["bedCategoriesData"][idx_1]["totalFreePlaces"]</code> ebenfalls in der Serverantwort verfügbar ist.

Als weiter Optionen kann via <code>COUNTRY</code> nach einen Land gefilter werden oder/und via <code>BORDERS</code> nach einem Gebiet.

Die Optionen <code>ALLOW_DOUBLE_HUT</code> und <code>ALLOW_STATIONARY_HUTS</code> sind Paramter für die Bildung der Hüttengruppen und können auf <code>True</code> gestellt werden, wenn sonst keine Ergebnisse verfügbar sind oder eine Hütte gesucht wird, die an allen Tagen verfügbar ist für einen stationären Aufenthalt

Gerne kann das Skript um weiter Optionen erweitert werden. Ebenso fehlt noch eine GUI sowohl für die Suche als auch die Darstellung der Ergebnisse. Diese werden aktuell in einer csv-Datei gespeichert.

Statt einer Luftliniendistanz (<code>MAX_DISTANCE = 10</code>) könnte auch unter Einbindung weiterer Libraries eine reelle Wegdistanz verwendet werden.