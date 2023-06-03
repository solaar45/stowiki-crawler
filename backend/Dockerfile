# Verwende ein Python-Basisimage
FROM python:3.9

# Setze das Arbeitsverzeichnis im Container
WORKDIR /app

# Kopiere die Anwendungsdateien in das Arbeitsverzeichnis
COPY . /app

# Installiere die Python-Abhängigkeiten
RUN pip install --no-cache-dir -r requirements.txt

# Setze den Befehl, der beim Start des Containers ausgeführt werden soll
CMD ["python", "server.py"]
