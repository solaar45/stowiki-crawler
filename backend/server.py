from flask import Flask, jsonify, send_file
import subprocess
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)  # Fügt die CORS-Konfiguration zum Flask-Server hinzu


@app.route("/run-scripts", methods=["GET"])
def run_scripts():
    try:
        # Erstes Skript ausführen und Ergebnis in output.json speichern
        subprocess.call(["python", "scrape3.py"])

        # Zweites Skript ausführen und Ergebnis in ergebnis.json speichern
        subprocess.call(["python", "test3.py"])

        # JSON-Ergebnis aus ergebnis.json lesen und als JSON-Response senden
        with open("ergebnis.json", "r") as file:
            result = json.load(file)

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/download-result", methods=["GET"])
def download_result():
    try:
        # Datei mit dem Ergebnis des zweiten Skripts als Download bereitstellen
        return send_file("ergebnis.json", as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run()
