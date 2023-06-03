import json
import re
from datetime import datetime

# Pfad zur JSON-Datei
json_file_path = "output.json"

# Laden der JSON-Daten aus der Datei
with open(json_file_path, "r") as json_file:
    data = json.load(json_file)


def rename_and_reorder(json_obj):
    if isinstance(json_obj, dict):
        if "Hull:" in json_obj:
            # Umbenennen des Schlüssels "Hull:" in "Max Hull:"
            json_obj["Max Hull:"] = json_obj.pop("Hull:")

        # Erstellen einer Liste der Schlüssel-Wert-Paare im aktuellen JSON-Objekt
        items = list(json_obj.items())

        # Entfernen des aktuellen JSON-Objekts
        json_obj.clear()

        # Hinzufügen des Schlüssel-Wert-Paares "Max Hull:" an vierter Stelle
        json_obj.update(items[:3])
        json_obj["Max Hull:"] = items[3][1]
        json_obj.update(items[3:])

        # Rekursiver Aufruf für alle Werte im aktuellen JSON-Objekt
        for value in json_obj.values():
            rename_and_reorder(value)
    elif isinstance(json_obj, list):
        # Rekursiver Aufruf für alle Elemente in der Liste
        for item in json_obj:
            rename_and_reorder(item)


def remove_rank(json_data):
    if isinstance(json_data, dict):
        for key in list(json_data.keys()):
            if key == "Rank:":
                del json_data[key]
            else:
                remove_rank(json_data[key])
    elif isinstance(json_data, list):
        for item in json_data:
            remove_rank(item)


def remove_console(json_data):
    if isinstance(json_data, dict):
        for key in list(json_data.keys()):
            if key == "Console (T5-U):":
                del json_data[key]
            else:
                remove_console(json_data[key])
    elif isinstance(json_data, list):
        for item in json_data:
            remove_console(item)


# Funktion zum Durchsuchen des JSON-Objekts nach "\n" und Ersetzen durch Leerzeichen
def replace_newline(json_obj):
    if isinstance(json_obj, dict):
        for key, value in json_obj.items():
            if isinstance(value, str):
                json_obj[key] = value.replace("\n", " ")
            elif isinstance(value, (dict, list)):
                replace_newline(value)
    elif isinstance(json_obj, list):
        for item in json_obj:
            replace_newline(item)


# Funktion zum Durchsuchen des JSON-Objekts nach "\u00a0" und Ersetzen durch Leerzeichen
def replace_newline2(json_obj):
    if isinstance(json_obj, dict):
        for key, value in json_obj.items():
            if isinstance(value, str):
                json_obj[key] = value.replace("\u00a0", " ")
            elif isinstance(value, (dict, list)):
                replace_newline2(value)
    elif isinstance(json_obj, list):
        for item in json_obj:
            replace_newline2(item)


# Funktion zum Durchsuchen des JSON-Objekts nach "Requires an Upgrade Token" und Ersetzen durch "Yes"
# def replace_upgrade2(json_obj):
#    if isinstance(json_obj, dict):
#        for key, value in json_obj.items():
#            if isinstance(value, str):
#                json_obj[key] = value.replace("Requires an Upgrade Token", "Yes")
#            elif isinstance(value, (dict, list)):
#                replace_upgrade2(value)
#    elif isinstance(json_obj, list):
#        for item in json_obj:
#            replace_upgrade2(item)


# Durchsuchen des JSON-Objekts und Ersetzen
replace_newline(data)
replace_newline2(data)
remove_rank(data)
remove_console(data)
# replace_upgrade2(data)
rename_and_reorder(data)

# Iteration über jeden Eintrag in der JSON-Datei
for entry in data:
    # Überprüfen, ob der Schlüssel "Max Hull:" vorhanden ist
    if "Max Hull:" in entry:
        # Extrahieren des Werts des Schlüssels "Max Hull:" aus dem aktuellen Eintrag
        hull_value = entry["Max Hull:"]

        # Überprüfen, ob der Wert "Lvl 65:", "Lvl 65 T5U:" oder "Level 50+:" enthält
        if "Lvl 65 :" in hull_value:
            hull_value = re.sub(r".*Lvl 65 :", "", hull_value)
        elif "Lvl 65 T5U :" in hull_value:
            hull_value = re.sub(r".*Lvl 65 T5U :", "", hull_value)
        elif re.search(r"Level 50\+:", hull_value):
            hull_value = re.sub(r".*Level 50\+:", "", hull_value)

        # Aktualisieren des Werts des Schlüssels "Max Hull:"
        entry["Max Hull:"] = hull_value.strip()

    # Extrahieren des Werts des Schlüssels "weapons" aus dem aktuellen Eintrag
    weapons_value = entry.get("Weapons:", "")

    # Überprüfen, ob eine Zahl und ein Buchstabe ohne Leerzeichen aufeinander folgen und ein Leerzeichen einfügen
    weapons_value = weapons_value.replace("Fore ", "").replace("Aft ", "")

    # Initialisieren der Variablen für die Werte der neuen Schlüssel
    fore_value = None
    aft_value = None
    dual_cannons_value = "no"

    # Aufteilen des Werts des Schlüssels "weapons" in Teile
    parts = weapons_value.split(" ")

    # Überprüfen der Teile und Zuweisen der Werte
    for part in parts:
        if fore_value is None:
            fore_value = str(part)
        elif aft_value is None:
            aft_value = str(part)
            break

    if "Can equip dual cannons." in weapons_value:
        dual_cannons_value = "yes"

    # Hinzufügen der neuen Schlüssel und Werte
    entry["Fore Weapons:"] = fore_value
    entry["Aft Weapons:"] = aft_value
    entry["Dual Cannons:"] = dual_cannons_value

    # Entfernen des alten Schlüssels "weapons"
    del entry["Weapons:"]

    # Überprüfen, ob der Schlüssel "Released:" vorhanden ist
    if "Released:" in entry:
        # Extrahieren des Datums im Format "Month Day, Year" aus dem aktuellen Eintrag
        date_value = entry["Released:"]

        # Konvertieren des Datums in das Format "YYYY-MM-DD"
        date_obj = datetime.strptime(date_value, "%B %d, %Y")
        formatted_date = date_obj.strftime("%Y-%m-%d")

        # Aktualisieren des Werts des Schlüssels "Released:"
        entry["Released:"] = formatted_date


def remove_colon(json_obj):
    if isinstance(json_obj, dict):
        keys_to_remove = []
        for key in json_obj.keys():
            # Überprüfen, ob der Schlüssel ":" enthält
            if ":" in key:
                keys_to_remove.append(key)

        # Entfernen der Schlüssel mit Doppelpunkt ":"
        for key in keys_to_remove:
            json_obj[key.replace(":", "")] = json_obj.pop(key)

        # Rekursiver Aufruf für alle Werte im aktuellen JSON-Objekt
        for value in json_obj.values():
            remove_colon(value)
    elif isinstance(json_obj, list):
        # Rekursiver Aufruf für alle Elemente in der Liste
        for item in json_obj:
            remove_colon(item)


# Entfernen des Doppelpunkts ":" aus den Schlüsselnamen
remove_colon(data)


def convert_to_integer(json_obj):
    if isinstance(json_obj, dict):
        if "Tier" in json_obj:
            # Konvertieren des Werts von string zu integer
            json_obj["Tier"] = int(json_obj["Tier"])

        if "Inertia rating" in json_obj:
            # Konvertieren des Werts von string zu integer
            json_obj["Inertia rating"] = int(json_obj["Inertia rating"])

        if "Device slots" in json_obj:
            # Konvertieren des Werts von string zu integer
            json_obj["Device slots"] = int(json_obj["Device slots"])

        # Rekursiver Aufruf für alle Werte im aktuellen JSON-Objekt
        for value in json_obj.values():
            convert_to_integer(value)
    elif isinstance(json_obj, list):
        # Rekursiver Aufruf für alle Elemente in der Liste
        for item in json_obj:
            convert_to_integer(item)


def convert_to_float(json_obj):
    if isinstance(json_obj, dict):
        if "Hull modifier" in json_obj:
            # Convert the value from string to float
            json_obj["Hull modifier"] = float(json_obj["Hull modifier"])

        if "Impulse modifier" in json_obj:
            # Convert the value from string to float
            json_obj["Impulse modifier"] = float(json_obj["Impulse modifier"])

        if "Shield modifier" in json_obj:
            # Convert the value from string to float
            json_obj["Shield modifier"] = float(json_obj["Shield modifier"])

        if "Turn rate" in json_obj:
            # Convert the value from string to float
            json_obj["Turn rate"] = float(json_obj["Turn rate"])

        for value in json_obj.values():
            convert_to_float(value)
    elif isinstance(json_obj, list):
        for item in json_obj:
            convert_to_float(item)


# Aufruf der Funktion zum Konvertieren des Werts von "Tier" zu integer
convert_to_integer(data)
convert_to_float(data)

# Speichern des aktualisierten JSON-Datenobjekts in einer neuen Datei
result_file_path = "ergebnis.json"
with open(result_file_path, "w") as result_file:
    json.dump(data, result_file)

print("Das Ergebnis wurde als JSON in der Datei", result_file_path, "gespeichert.")
