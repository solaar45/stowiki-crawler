# Verwende ein offizielles Node.js-Basisimage als Basis
FROM node:14-alpine

# Setze das Arbeitsverzeichnis innerhalb des Containers
WORKDIR /app

# Kopiere package.json und package-lock.json in das Arbeitsverzeichnis
COPY package*.json ./

# Installiere die Abhängigkeiten
RUN npm install

# Kopiere den Rest des Codes in das Arbeitsverzeichnis
COPY . .

# Baue die React-Anwendung
RUN npm run build

# Setze den Befehl, der beim Start des Containers ausgeführt werden soll
CMD ["npm", "start"]
