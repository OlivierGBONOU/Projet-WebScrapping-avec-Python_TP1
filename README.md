# 📺 Projet de Webscraping YouTube avec Python

Ce projet est une application complète de webscraping développée en Python permettant de collecter, stocker et visualiser des données issues de **YouTube**. Il comprend une interface web, une gestion de base de données, un système de tâches asynchrones via Celery, ainsi qu’un monitoring via Prometheus et Grafana.

## 🧰 Technologies utilisées

* **Python**
* **Flask** (Framework web)
* **BeautifulSoup / requests** (Web scraping)
* **SQLite / PostgreSQL** (Gestion de base de données)
* **Celery + Redis** (Tâches asynchrones)
* **Docker / Docker Compose** (Conteneurisation)
* **Prometheus & Grafana** (Monitoring)
* **HTML / CSS (Jinja2)** (Frontend)

## 📁 Structure du projet

```bash
Projet-WebScrapping-avec-Python_TP1-main/
│
├── app.py                     # Application principale Flask
├── python.py                 # Logique de scraping
├── gestion_bd.py             # Gestion de la base de données
├── celeryconfig.py           # Configuration de Celery
├── requirements.txt          # Dépendances Python
├── docker-compose.yml        # Orchestration des services
├── Dockerfile                # Image Docker Flask
├── prometheus.yml            # Configuration de Prometheus
├── grafana.json              # Dashboard Grafana
├── _Documentation.ipynb      # Notebook explicatif
├── servers.json              # Configuration des serveurs
│
├── templates/
│   ├── index.html            # Page d'accueil
│   └── home.html             # Interface principale
│
├── static/
│   ├── images/               # Images utilisées
│   └── video/                # Vidéos statiques (ex: youtube.mp4)
```

## ⚙️ Installation et Lancement

### Prérequis

* Docker
* Docker Compose
* Accès à Internet pour installer les dépendances

### Étapes

1. **Cloner le dépôt**

```bash
git clone https://github.com/OlivierGBONOU/Projet-WebScrapping-avec-Python_TP1.git
```

2. **Lancer les services**

```bash
docker-compose up --build
```

3. Accédez à l'application :

* Interface Web : [http://localhost:5000](http://localhost:5000)
* Grafana : [http://localhost:3000](http://localhost:3000)
* Prometheus : [http://localhost:9090](http://localhost:9090)

## 🧪 Fonctionnalités

* Recherche de vidéos YouTube par mot-clé
* Extraction de données (titre, nombre de vues, durée, etc.)
* Stockage automatique en base de données
* Affichage dynamique sur interface web
* Rafraîchissement des données via Celery
* Monitoring des performances avec Prometheus et Grafana

## 📊 Monitoring

Le projet inclut une configuration prête à l’emploi de **Prometheus** et un **dashboard Grafana** (`grafana.json`) pour visualiser :

* Le temps de réponse de l'application
* La fréquence des tâches Celery
* L’utilisation mémoire et CPU

## 📌 Auteurs

* Projet réalisé par GBONOU Olivier.

## 📄 Licence

Ce projet est distribué à des fins académiques.
