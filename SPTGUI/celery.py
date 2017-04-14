from __future__ import absolute_import, unicode_literals
import os
import celery
from celery import Celery



#from django.conf import settings
#settings.configure()

#from django.apps import AppConfig

import time

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fastSPT.settings')


app = Celery('fastSPT')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


## Some debug stuff...
# @app.task(bind=True)
# def debug_task(self):
#     print('Request: {0!r}'.format(self.request))

# @app.task()
# def loong():
#     """ Get some rest, asynchronously, and update the state all the time """
#     for i in range(1000):
#         time.sleep(0.1)
#         print i
#         app.current_task.update_state(state='PROGRESS',
#             meta={'current': i, 'total': 100})
