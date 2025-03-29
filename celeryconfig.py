from celery.schedules import crontab

beat_schedule = {
    'scrape-gims-every-hour': {
        'task': 'app.scrape_youtube_task',
        'schedule': crontab(minute=0, hour='*'),  # À H:00
        'args': ('GIMS',),
    },
    'scrape-soprano-every-hour': {
        'task': 'app.scrape_youtube_task',
        'schedule': crontab(minute=10, hour='*'),  # À H:10
        'args': ('Soprano',),
    },
    'scrape-jul-every-hour': {
        'task': 'app.scrape_youtube_task',
        'schedule': crontab(minute=20, hour='*'),  # À H:20
        'args': ('Jul',),
    },
}