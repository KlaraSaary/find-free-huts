import time
import requests
import csv
import math

from datetime import datetime, timedelta

from HEADERS_COOKIES import COOKIES, HEADERS

BASE_URL = "https://www.hut-reservation.org/api/v1"
DATE_TO_CHECK = ["2025-07-09","2025-07-12"] # <-- Hier deine Wunschdaten eintragen

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
MAX_DISTANCE = 8  # Maximale Distanz in km, um benachbarte Hütten zu finden (Luftlinie)

OUTPUT_FILE = "huettengruppen.csv"  # Dateiname für die Ausgabe der Gruppen

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Erdradius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def get_huts():
    url = f"{BASE_URL}/manage/hutsList"
    resp = requests.get(url, headers=HEADERS, cookies=COOKIES)
    resp.raise_for_status()
    return resp.json()

def get_hut_details(hut_id, return_category="all", retries=3, delay=1):
    # Beispiel Response:
    # {"hutWebsite":"https://www.sac-pilatus.ch/aarbiwak.html","hutId":603,"tenantCode":"SAC","hutUnlocked":true,"maxNumberOfNights":20,"hutName":"Aarbiwak SAC","hutWarden":"Markus Brefin","phone":"+41 33 744 36 11","coordinates":"46.5555,  8.1522","altitude":"2731 m","totalBedsInfo":"17","tenantCountry":"CH","picture":{"fileType":"HUT_PICTURE","blobPath":"https://www.hut-reservation.org/data/files/hut_picture_603.jpeg","fileName":"picture_603.jpeg","fileData":null},"hutLanguages":["DE_CH","EN"],"hutBedCategories":[{"index":1,"categoryID":1771,"rooms":[],"isVisible":true,"totalSleepingPlaces":14,"reservationMode":"ROOM","hutBedCategoryLanguageData":[{"language":"DE_CH","label":"Massenlager","shortLabel":"ML","description":"Bitte immer einen Hüttenschlafsack mitnehmen"},{"language":"EN","label":"Dormitory","shortLabel":"Dorm","description":"Please always take a hut sleeping bag with you"}],"isLinkedToReservation":false,"tenantBedCategoryId":1},{"index":11,"categoryID":1772,"rooms":[],"isVisible":true,"totalSleepingPlaces":14,"reservationMode":"UNSERVICED","hutBedCategoryLanguageData":[{"language":"DE_CH","label":"Schutzraum/Winterraum","shortLabel":"SrWr","description":"Bitte immer einen Hüttenschlafsack mitnehmen"},{"language":"EN","label":"Emergency Room","shortLabel":"Emer","description":"Please always take a hut sleeping bag with you"}],"isLinkedToReservation":false,"tenantBedCategoryId":43}],"providerName":"NO_EPAYMENT","hutGeneralDescriptions":[{"description":"Das Aarbiwak ist eine unbewartete Selbsversorgerhütte. Stornierungen einer Reservation können bis um 18:00 Uhr des Vorabends getätigt werden. Falls nicht rechtzeitig storniert wird, behalten wir uns vor, eine No-Show-Gebühr von CHF 25.- zu verrechnen.","language":"DE_CH"},{"description":"L'Aarbiwak est une cabane indépendante sans surveillance. Les annulations de réservation peuvent être faites jusqu'à 18h la veille. Si vous n'annulez pas à temps, nous nous réservons le droit de facturer des frais de non-présentation de CHF 25.","language":"FR"},{"description":"L'Aarbiwak è una capanna self-catering incustodita. Le cancellazioni di una prenotazione possono essere effettuate fino alle 18:00 della sera precedente. Se non si annulla in tempo, ci riserviamo il diritto di addebitare una penale per mancata presentazione di CHF 25.","language":"IT"},{"description":"The Aarbiwak is an unattended self-catering hut. Cancellations of a reservation can be made up to 6 p.m. the evening before. If you do not cancel in time, we reserve the right to charge a no-show fee of CHF 25.","language":"EN"}],"supportLink":"","waitingListEnabled":false}
    url = f"{BASE_URL}/reservation/hutInfo/{hut_id}"
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, cookies=COOKIES, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if return_category == "all":
                return data
            elif isinstance(return_category, list):
                return {cat: data.get(cat, {}) for cat in return_category}
            else:        
                return data.get(return_category, {})
        except requests.exceptions.RequestException as e:
            print(f"Fehler beim Abrufen von Hütte {hut_id} (Versuch {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                return None
    
def get_hut_hutBedCategories(hut_id):
    hutBedCategories = get_hut_details(hut_id, return_category="hutBedCategories")
    hutBedCategories_Ids=[]
    for category in hutBedCategories:
        hutBedCategories_Ids.append(category["categoryID"])
    return hutBedCategories_Ids

def check_availability(hut_id, arrival, departure=None):
    # Request Headers:
    # {"arrivalDate":"12.07.2025","departureDate":"13.07.2025","numberOfPeople":0,"nextPossibleReservations":false,"peoplePerCategory":[{"categoryId":1771,"people":0}],"isWaitingListAccepted":false,"reservationPublicId":""}
    url = f"{BASE_URL}/reservation/checkAvailability/{hut_id}"

    # Abreise = nächster Tag
    arrival_dt = datetime.strptime(arrival, "%Y-%m-%d")
    if departure:
        departure_dt = datetime.strptime(departure, "%Y-%m-%d")
    else:
        # Wenn kein Abreisedatum angegeben ist, setze es auf den nächsten Tag
        departure_dt = arrival_dt + timedelta(days=1)

    # Erstelle peoplePerCategory for request
    peoplePerCategory = []
    hutBedCategories = get_hut_hutBedCategories(hut_id)
    # print(f"Hut {hut_id} hat folgende Bettkategorien: {hutBedCategories}")
    for category_id in hutBedCategories:
        peoplePerCategory.append({
            "categoryId": category_id,
            "people": NUMBER_OF_PEOPLE
        })
    # print(f"peoplePerCategory: {peoplePerCategory}")

    payload = {
        "arrivalDate": arrival_dt.strftime("%d.%m.%Y"),
        "departureDate": departure_dt.strftime("%d.%m.%Y"),
        "numberOfPeople": NUMBER_OF_PEOPLE,
        "nextPossibleReservations": False,
        "peoplePerCategory": peoplePerCategory,
        "isWaitingListAccepted": False,
        "reservationPublicId": ""
    }
    # print(f"Payload: {payload}")
    resp = requests.post(url, headers=HEADERS, cookies=COOKIES, json=payload)
    resp.raise_for_status()
    data = resp.json()
    free_beds = []

    for day_info in data.get("availabilityPerDayDTOs", []):
        free_beds.append({
            "CheckedDate": day_info.get("day"),
            "FreeBeds": day_info.get("freePlaces", 0)
        })    

    return free_beds

def find_groups(hut_infos, available_per_day, allow_double_hut=False, allow_stationary_huts=False):
    # allow_double_hut: Wenn True, kann eine Hütte mehrmals in einer Gruppe sein, sonst nur einmal
    #allow_stationary_huts: Wenn True, werden nur Hütten berücksichtigt, die an allen Tagen verfügbar sind

    # hut_infos ist ein Dictionary mit Hut-IDs als Schlüsseln und Informationen über die Hütten (Name, Koordinaten) als Werten für Hütten, die mindestens an einem der angegebenen Tage verfügbar sind
    # available_per_day ist ein Dictionary mit Datum als Schlüssel und einer Liste von Hut-IDs, die an diesem Tag verfügbar sind
    all_groups = []
    
    # Wenn available_per_day für einen Tag keine Hütten hat, ist keine Gruppe möglich
    for date, hut_ids in available_per_day.items():
        if not hut_ids:
            print(f"Keine Hütten verfügbar am {date}. Keine Gruppen möglich.")
            return all_groups  # Keine Gruppen möglich, wenn an einem Tag keine Hütten verfügbar sind
    
    # Erstelle Baumstruktur für benachbarte Hütten mit Koordinaten
    hut_tree = {}
    for hut_id, info in hut_infos.items():
        lat = info["lat"]
        lon = info["lon"]
        hut_tree[hut_id] = {
            "lat": lat,
            "lon": lon,
            "neighbours": find_neighbours(hut_id, lat, lon, hut_infos, max_distance=MAX_DISTANCE)  # max_distance in km, hier 10 km
        }
    # Finde den Tag mit den wenigsten verfügbaren Hütten
    min_day = min(available_per_day, key=lambda d: len(available_per_day[d]))
    start_huts = set(available_per_day[min_day])

    print(f"Start Hütten am {min_day}: {start_huts}")
    if not start_huts:
        print("Keine Start-Hütten gefunden, die an den angegebenen Tagen verfügbar sind.")
        return all_groups
    
    #Prüfe welche der Start-Hütten auch an den anderen Tagen verfügbar sind, um eine Wanderung nur mit Tagesrouten zu ermöglichen
    if allow_stationary_huts:
        stationary_huts = start_huts.copy()  # Kopie der Start-Hütten, um sie zu filtern
        for date in available_per_day:
            # Filtere alle Hütten aus start_huts, die an diesem Tag verfügbar sind
            available_today = set(available_per_day[date])
            # Behalte nur die Hütten, die an diesem Tag verfügbar sind
            stationary_huts = stationary_huts.intersection(available_today)
        if not stationary_huts:
            print("Keine Hütten gefunden, die an allen angegebenen Tagen verfügbar sind.")
        else:
            all_groups = [[hid] for hid in stationary_huts]  # Jede Hütte als eigene Gruppe

    steps = len(DATE_TO_CHECK) - 1 # Anzahl der Schritte, die wir gehen können, basierend auf den verfügbaren Tagen
    relevant_huts = reachable_huts(hut_tree, start_huts, steps)
    if not relevant_huts:
        print("Keine erreichbaren Hütten gefunden, die an den angegebenen Tagen verfügbar sind.")
        return all_groups

    # Filter hut_infos
    print(f"Relevante Hütten: {len(relevant_huts)} von {len(hut_infos)} Hütten")
    hut_infos = {hid: info for hid, info in hut_infos.items() if hid in relevant_huts}
    # Prüfe, dass len(hut_infos) == len(relevant_huts)
    if len(hut_infos) != len(relevant_huts):
        print(f"Warnung: Anzahl der Hütten in hut_infos ({len(hut_infos)}) stimmt nicht mit der Anzahl der relevanten Hütten ({len(relevant_huts)}) überein.")

    # Filter available_per_day
    for day in available_per_day:
        available_per_day[day] = [hid for hid in available_per_day[day] if hid in relevant_huts]
    print(f"Verfügbare Hütten pro Tag nach Filterung: {available_per_day}")

    # Suche Gruppen von Hütten, die an allen Tagen verfügbar sind und benachbart sind
    def search_group(current_group, remaining_days):
        if not remaining_days:
            # Wenn keine verbleibenden Tage mehr, füge die aktuelle Gruppe zu den Gruppen hinzu
            print(f"Gefundene Gruppe: {current_group}")
            all_groups.append(current_group)
            return
        
        current_date = remaining_days[0]
        available_huts_today = available_per_day.get(current_date, [])
        
        for hut_id in available_huts_today:
            # Überprüfe, ob die Hütte bereits in der aktuellen Gruppe ist, wenn jede Hütte nur einmal in der Gruppe sein soll
            if not allow_double_hut and hut_id in current_group:
               continue

            # Überprüfe, ob die Hütte benachbart zu einer der bereits in der Gruppe befindlichen Hütten ist
            is_neighbour = any(
                hut_id in hut_tree[existing_hut]["neighbours"] for existing_hut in current_group
            )
            if is_neighbour or not current_group:  # Wenn es noch keine Hütten in der Gruppe gibt, füge die Hütte hinzu
                new_group = current_group + [hut_id]
                search_group(new_group, remaining_days[1:])
    

    # Starte die Suche mit einer leeren Gruppe und allen verfügbaren Tagen
    search_group([], list(available_per_day.keys()))

    return all_groups

def find_neighbours(hut_id, lat, lon, hut_infos, max_distance=10):
    neighbours = []
    for other_id, info in hut_infos.items():
        if other_id == hut_id:
            continue  # Selbstreferenz ausschließen
        other_lat = info["lat"]
        other_lon = info["lon"]
        distance = haversine(lat, lon, other_lat, other_lon)
        if distance <= max_distance:
            neighbours.append(other_id)
    return neighbours

def reachable_huts(hut_tree, start_huts, steps):
    reachable = set(start_huts)
    frontier = set(start_huts)
    for _ in range(steps):
        next_frontier = set()
        for hut in frontier:
            next_frontier.update(hut_tree[hut]["neighbours"])
        next_frontier -= reachable
        reachable.update(next_frontier)
        frontier = next_frontier
    return reachable

def sort_and_fill_Datelist():
    #Sortier DATE_TO_CHECK 
    global DATE_TO_CHECK
    if isinstance(DATE_TO_CHECK, str):
        DATE_TO_CHECK = [DATE_TO_CHECK]
    DATE_TO_CHECK = sorted(DATE_TO_CHECK, key=lambda x: datetime.strptime(x, "%Y-%m-%d"))

    # Stelle sicher, dass DATE_TO_CHECK kontinuierlich ist und ergänze fehlende Tage
    start_date = datetime.strptime(DATE_TO_CHECK[0], "%Y-%m-%d")
    end_date = datetime.strptime(DATE_TO_CHECK[-1], "%Y-%m-%d")
    all_dates = []
    current_date = start_date
    while current_date <= end_date:
        all_dates.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)
    DATE_TO_CHECK = all_dates
    return DATE_TO_CHECK

def main():
    DATE_TO_CHECK = sort_and_fill_Datelist()  # Sortiere und fülle die Datums-Liste auf
    print(f"Liste alle Hütten im System auf...")
    huts = get_huts() # Struktur: [{'hutName': 'Hütte A', 'hutId': 603, 'hutCountry': 'CH'}, , {"hutId": 456, "hutName": "Hütte B", "hutCountry": AT}, ...]
    
    #Filter huts for hutCountry = COUNTRY
    if COUNTRY:
        huts = [hut for hut in huts if hut.get("hutCountry") == COUNTRY]

    #FOR DEBUGGING: Kürze huts auf die ersten 10 Einträge
    #huts = huts[:10]  # Nur die ersten 10 Hütten für Debugging

    # print(f"Gefundene Hütten: {huts}")
    hut_infos = {}        
    available_huts = []

    available_per_day = {}
    for date in DATE_TO_CHECK[0:-1]:  # Letztes Datum nicht einbeziehen, da es kein Folgedatum gibt
        available_per_day[date] = []
    
    print(f"Iteriere über alle {len(huts)} Hütten und prüfe Verfügbarkeit an den Daten {DATE_TO_CHECK} für {NUMBER_OF_PEOPLE} Personen...")
    for hut in huts:
        available_at_all = False
        hut_id = hut["hutId"]
        name = hut.get("hutName", "")
        coords_str = get_hut_details(hut["hutId"], return_category="coordinates") # Struktur: "46.5555, 8.1522" oder auch '46.953985/12.781181'
        if coords_str:
                coords_str = coords_str.replace("/", ",")
                lat_str, lon_str = coords_str.split(",")
                coords = {"latitude": float(lat_str.strip()), "longitude": float(lon_str.strip())}
        else:
            coords = {"latitude": None, "longitude": None}

        # Wenn BORDERS gesetzt ist, prüfe, ob die Koordinaten innerhalb der Grenzen liegen
        if BORDERS:
            if coords["longitude"] < BORDERS["west"] or coords["longitude"] > BORDERS["east"] or coords["latitude"] < BORDERS["south"] or coords["latitude"] > BORDERS["north"]:
                continue  # Nur Hütten innerhalb der Grenzen BORDERS berücksichtigen
        try:
            free_beds = check_availability(hut_id, DATE_TO_CHECK[0], DATE_TO_CHECK[-1])
            for day in free_beds:
                date = day.get("CheckedDate")
                iso_date = datetime.strptime(date, "%d.%m.%Y").strftime("%Y-%m-%d")
                if iso_date in DATE_TO_CHECK and day.get("FreeBeds", 0) >= NUMBER_OF_PEOPLE:
                    available_at_all = True
                    # print(f"Hütte {hut_id} ({name}) hat am {date} freie Betten: {day.get('FreeBeds', 0)}")
                    available = {
                        "id": hut_id,
                        "name": name,
                        "checkedDate": date,
                        "free_beds": day.get("FreeBeds", 0)
                    }
                    available_huts.append(available)
                    available_per_day[iso_date].append(hut_id)
        except Exception:
            continue
    
        # Wenn die Hütte an mindestens einem der angegebenen Tage verfügbar ist, füge sie zu hut_infos hinzu
        if available_at_all:
            hut_infos[hut_id] = {
                "name": name,
                "lat": coords.get("latitude"),
                "lon": coords.get("longitude")
            }

    print(f"Versuche aus den {len(hut_infos)} verfügbaren Hütten Gruppen zu bilden...")
    all_groups = find_groups(hut_infos, available_per_day, allow_double_hut=ALLOW_DOUBLE_HUT, allow_stationary_huts=ALLOW_STATIONARY_HUTS)
    print(f"Gefundene Gruppen: {all_groups}")
    
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Interleave lat/lon headers
        coords_headers = []
        for i in range(len(DATE_TO_CHECK)-1):
            coords_headers.append(f"Coords_lat_Tag{i+1}")
            coords_headers.append(f"Coords_lon_Tag{i+1}")
        header = (
            [f"Tag{i+1}_id" for i in range(len(DATE_TO_CHECK)-1)] +
            [f"Tag{i+1}_name" for i in range(len(DATE_TO_CHECK)-1)] +
            coords_headers
        )
        writer.writerow(header)
        for group in all_groups:
            ids = group
            names = [hut_infos[hid]["name"] for hid in group]
            coords = []
            for hid in group:
                coords.append(hut_infos[hid]['lat'])
                coords.append(hut_infos[hid]['lon'])
            writer.writerow(ids + names + coords)

    print(f"{len(all_groups)} Hütten mit freien Betten am {DATE_TO_CHECK} gefunden.")

if __name__ == "__main__":
    main()
