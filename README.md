# find-free-huts

**find-free-huts** hilft dir, freie DAV/SAC/ÖAV Hütten für eine oder mehrere Nächte zu finden und passende Hüttengruppen für deine Tour zu bilden. Das Skript `find_neighboured_free_huts.py` ist fertig, während das Skript `find_available-hut.py` mehr ein "Proof of Concept" ist.

---

## Features

- Suche nach freien Hütten an mehreren Tagen
- Filter nach Land und geografischen Grenzen
- Gruppierung benachbarter Hütten für Mehrtagestouren
- CSV-Export der Ergebnisse

---

## Voraussetzungen

- Python 3.7 oder neuer
- Benötigte Python-Bibliotheken:
  - `requests`
  - `csv`
  - `math`
  - `time`
  - `datetime`
Installiere fehlende Bibliotheken mit:
```bash
pip install requests
```

---

## Vorbereitung

1. **Login:**  
   Melde dich auf [hut-reservation.org](https://www.hut-reservation.org) an.

2. **Cookies kopieren:**  
   - Öffne die Entwicklerwerkzeuge deines Browsers (Rechtsklick → Untersuchen/Inspect).
   - Gehe zum Tab „Storage“/„Speicher“ und suche die Cookies `SESSION` und `XSRF-TOKEN`.
   - Trage diese Werte in die Datei `HEADERS_COOKIES.py` ein.

---

## Konfiguration

Passe zu Beginn von `find_neighboured_free_huts.py` folgende Variablen an:

```python
DATE_TO_CHECK = ["2025-07-09", "2025-07-10", "2025-07-11", "2025-07-12"]  # Deine Wunschdaten (letztes Datum = Abreisetag)
NUMBER_OF_PEOPLE = 5  # Mindestanzahl freier Plätze (0 = egal)
BORDERS = {
    "west": 9.635,
    "east": 12.401,
    "north": 47.769,
    "south": 46.851
}  # Optional: Geografische Grenzen (Längengrad/Breitengrad)
COUNTRY = "AT"  # Land: "AT" (Österreich), "CH" (Schweiz), "DE" (Deutschland)
ALLOW_DOUBLE_HUT = False  # True: Hütte kann mehrfach in einer Gruppe sein
ALLOW_STATIONARY_HUTS = False  # True: Gruppen mit nur einer Hütte möglich
MAX_DISTANCE = 10  # Maximale Luftliniendistanz (km) zwischen Hütten
```

**Hinweise:**
- Die Liste `DATE_TO_CHECK` muss nicht sortiert oder vollständig sein. Fehlende Tage werden automatisch ergänzt (`sort_and_fill_Datelist()`).
- Mit `BORDERS` und `COUNTRY` kannst du die Suche geografisch einschränken.
- `NUMBER_OF_PEOPLE` stellt sicher, dass nur Hütten berücksichtigt werden mit einer Mindestanzahl von freien Plätzen. Diese können sich jedoch in unterschiedlichen Zimmerkategorien befinden. 
- Setze `ALLOW_STATIONARY_HUTS` auf `True`, wenn du auch angezeigt haben möchtest, welche Hütte die gesamte Zeit verfügbar ist.
---

## Nutzung

Starte das Skript im Terminal:

```bash
python find_neighboured_free_huts.py
```

Die Ergebnisse werden als CSV-Dateien gespeichert (`hut_infos.csv`, `huettengruppen_at.csv`). Sie erhalten die Hütten-IDs, Namen und Koordinaten für jeden Tag.

---

## Erweiterungen & Hinweise

- Die Optionen `ALLOW_DOUBLE_HUT` und `ALLOW_STATIONARY_HUTS` beeinflussen die Gruppensuche (z.B. für stationäre Aufenthalte).
- Um nur Hütten anzuzeigen, die genug freie Plätze einer Zimmerkategorie haben, könnte `check_availability(hut_id, arrival, departure=None)` angepasst werden. Hier ist der Wert `availabilityPerDayDTOs[idx]["bedCategoriesData"][idx_1]["totalFreePlaces"]` ebenfalls in der Serverantwort verfügbar.
- Das Skript kann um weitere Filter und Optionen erweitert werden.
- Eine grafische Oberfläche (GUI) ist nicht enthalten, weder für die Suche noch für die Darstellung der Ergebnisse.
- Statt einer Luftliniendistanz (`MAX_DISTANCE`) kann mit zusätzlichen Libraries auch eine reale Wegdistanz berechnet werden.

---

## Beispiel

```python
DATE_TO_CHECK = ["2025-07-09", "2025-07-10", "2025-07-11"]
NUMBER_OF_PEOPLE = 4
COUNTRY = "DE"
MAX_DISTANCE = 8
```
Sucht nach freien Hütten in Deutschland für 4 Personen an den angegebenen Tagen, wobei benachbarte Hütten maximal 8 km auseinanderliegen dürfen.

---

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz.


