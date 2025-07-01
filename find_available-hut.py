import requests
import csv

from datetime import datetime, timedelta

from HEADERS_COOKIES import COOKIES, HEADERS

BASE_URL = "https://www.hut-reservation.org/api/v1"
DATE_TO_CHECK = "2025-07-11"  # <-- Hier dein Wunschdatum eintragen

NUMBER_OF_PEOPLE = 0  # Anzahl der Personen für die Reservierung, 0 für gibt an, dass es egal ist

def get_huts():
    url = f"{BASE_URL}/manage/hutsList"
    resp = requests.get(url, headers=HEADERS, cookies=COOKIES)
    resp.raise_for_status()
    return resp.json()

def get_hut_details(hut_id, return_category="all"):
    url = f"{BASE_URL}/reservation/hutInfo/{hut_id}"
    resp = requests.get(url, headers=HEADERS, cookies=COOKIES)
    resp.raise_for_status()
    data = resp.json()
    # print(f"Details für Hütte {hut_id} abgerufen: {data}")
    if return_category == "all":
        return data
    else:
        return data.get(return_category, {})
    
def get_hut_hutBedCategories(hut_id):
    hutBedCategories = get_hut_details(hut_id, return_category="hutBedCategories")
    hutBedCategories_Ids=[]
    for category in hutBedCategories:
        hutBedCategories_Ids.append(category["categoryID"])
    return hutBedCategories_Ids

def check_availability(hut_id, date):
    # Request Headers:
    # {"arrivalDate":"12.07.2025","departureDate":"13.07.2025","numberOfPeople":0,"nextPossibleReservations":false,"peoplePerCategory":[{"categoryId":1771,"people":0}],"isWaitingListAccepted":false,"reservationPublicId":""}
    url = f"{BASE_URL}/reservation/checkAvailability/{hut_id}"
    # Datum im Format TT.MM.JJJJ
    arrival = date
    # Abreise = nächster Tag
    arrival_dt = datetime.strptime(arrival, "%Y-%m-%d")
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

def main():
    huts = get_huts() # Struktur: [{'hutName': 'Hütte A', 'hutId': 603, 'hutCountry': 'CH'}, , {"hutId": 456, "hutName": "Hütte B", "hutCountry": AT}, ...]
    # print(f"Gefundene Hütten: {huts}")
    available_huts = []
    for hut in huts:
        hut_id = hut["hutId"]
        name = hut.get("hutName", "")
        try:
            free_beds = check_availability(hut_id, DATE_TO_CHECK)
            for date in free_beds:
                if date.get("FreeBeds", 0) >= NUMBER_OF_PEOPLE:
                    available_huts.append({
                        "id": hut_id,
                        "name": name,
                        "checkedDate": date.get("CheckedDate"),
                        "free_beds": date.get("FreeBeds", 0)
                    })
        except Exception as e:
            print(f"Fehler bei Hütte {hut_id} ({name}): {e}")
    # free_beds = check_availability(603, "2025-07-12")  # Beispiel für eine Hütte mit ID 603 und Datum 12.07.2025")
    # available_huts.append({"id": 603, "name": "Aarbiwak SAC", "CheckedDate": "12.07.2025", "free_beds": free_beds.get("FreeBeds", 0)})
    with open("available_huts.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "name", "checkedDate", "free_beds"])
        writer.writeheader()
        writer.writerows(available_huts)

    print(f"{len(available_huts)} Hütten mit freien Betten am {DATE_TO_CHECK} gefunden.")

if __name__ == "__main__":
    main()