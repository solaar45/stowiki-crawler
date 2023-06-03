import requests
from bs4 import BeautifulSoup
import json

# URLs der Seiten
urls = [
    "https://sto.fandom.com/wiki/Dominion_playable_starship",
]

# Ergebnis als Liste initialisieren
result = []

# Schleife über alle URLs
for url in urls:
    # Anforderung an die Seite senden
    response = requests.get(url)

    # BeautifulSoup initialisieren
    soup = BeautifulSoup(response.text, "html.parser")

    # Alle Tabellen mit der Klasse "wikitable" finden
    tables = soup.find_all("table", class_="sortable")

    # Schleife über alle gefundenen Tabellen
    for table in tables:
        # Die Zeilen (table rows) in der Tabelle finden
        rows = table.find_all("tr")

        # Schleife über alle Zeilen (überspringe die erste Zeile mit den Spaltenüberschriften)
        for row in rows[1:]:
            # Die zweite Spalte der aktuellen Zeile finden
            second_column = row.find_all("td")[1]

            # Den Link extrahieren
            link = second_column.find("a")["href"]

            # Den Link mit dem Basis-URL ergänzen
            complete_link = "https://sto.fandom.com" + link

            # Anforderung an die ergänzte URL senden
            response_complete = requests.get(complete_link)

            # BeautifulSoup für die ergänzte URL initialisieren
            soup_complete = BeautifulSoup(response_complete.text, "html.parser")

            # Das gewünschte div-Tag mit der Klasse "missionname" finden
            mission_name_div = soup_complete.find("div", class_="missionname")

            # Ein neues Ergebnisobjekt für die aktuelle Zeile erstellen
            result_row = {}

            if mission_name_div:
                # Inhalt aus dem div-Tag mit der Klasse "missionname" extrahieren
                mission_name = mission_name_div.get_text().strip()
                result_row["Ship"] = mission_name

                # Füge den Link zur Ergebniszeile hinzu
                result_row["Link"] = complete_link

                # Extrahiere den Inhalt aus den <div class="entry">
                entry_divs = soup_complete.find_all("div", class_="entry")
                entries = []
                for entry_div in entry_divs:
                    content = []
                    for element in entry_div.descendants:
                        if element.name == "img":
                            if "alt" in element.attrs:
                                content.append(element["alt"])
                            else:
                                content.append(element["src"])
                        elif (
                            element.name not in ["small", "span", "i", "a", "td"]
                            and element.string
                        ):
                            content.append(element.string.strip())
                    entries.append(" ".join(content))  # Concatenate the content

                # Extrahiere den Inhalt aus den <div class="label">
                label_divs = soup_complete.find_all("div", class_="label")
                results = {}
                for i, label_div in enumerate(label_divs):
                    label = label_div.text.strip() if label_div.text else ""
                    if label in results:
                        results[label] += " " + entries[i] if i < len(entries) else ""
                    else:
                        results[label] = entries[i] if i < len(entries) else ""

                # Die Ergebniszeile zur Ergebnisliste hinzufügen
                result_row.update(results)
                result.append(result_row)

# Ergebnis als JSON speichern
with open("output.json", "w") as f:
    json.dump(result, f)

print("Ergebnis wurde als JSON in output.json gespeichert.")
