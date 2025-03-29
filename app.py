from flask import Flask, request, jsonify, redirect, render_template
from python import scrape_youtube, insert_data
from gestion_bd import create_tables, create_database, check_database_exists, delete_artist
from celery import Celery
from prometheus_flask_exporter import PrometheusMetrics
import os

# Flask app initialization
app = Flask(__name__)

# Add Prometheus metrics
metrics = PrometheusMetrics(app)

# Celery configuration
app.config['CELERY_BROKER_URL'] = 'redis://redis:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://redis:6379/0'
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

@celery.task
def scrape_youtube_task(artist_name):
    if not check_database_exists():
        create_database()
    create_tables()
    delete_artist(artist_name)
    data = scrape_youtube(artist_name)
    insert_data(data)
    return data

@app.route('/')
def home():
    """Render the main page"""
    return render_template('home.html')

@app.route('/youtube')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/youtube/search', methods=['POST'])
def search():
    """Handle search requests and initiate background scraping task"""
    artist_name = request.form.get('artist')
    artist_name = str(artist_name)
    print("Nom de l'artiste reçu :", artist_name)
    
    if not artist_name:
        return jsonify({'error': 'No artist name provided'}), 400
    
    try:
        task = scrape_youtube_task.delay(artist_name)
        return jsonify({'task_id': task.id, 'status': 'processing'}), 202
    except Exception as e:
        print(f"ERREUR dans /search : {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/youtube/task/<task_id>')
def check_task(task_id):
    """Check the status of a background task"""
    task = scrape_youtube_task.AsyncResult(task_id)
    
    if task.state == 'SUCCESS':
        return jsonify(task.result)
    elif task.state == 'FAILURE':
        return jsonify({'error': 'Task failed', 'details': str(task.info)}), 500
    else:
        return jsonify({'status': task.state}), 202


if __name__ == '__main__':
    try:
        create_database()
        create_tables()
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")
    
    app.run(host='0.0.0.0', port=8000)