# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task

from time import sleep
from celery import task, current_task, Celery

import django
django.setup()
from SPTGUI.models import Dataset


##
## ==== Here go the tasks to be performed asynchronously
##    


@shared_task
## A preprocessing task
##@app.task()
def check_input_file(filepath, file_id):
    """This function checks that the uploaded file has the right format and
    can be analyzed.
    
    Inputs:
    - filepath: the path to the file to be checked
    - file_id: the id of the file in the database.

    Returns: None
    - Update the Dataset entry with the appropriately parsed information
    """
    ## Sanity checks
    #dj = AppConfig()
    #Dataset = dj.get_model('Dataset')
    da = Dataset.objects.get(id=file_id)
    
    ## Check file format        

    ## Extract the relevant information

    ## Update the state
    da.preanalysis_token = ''
    da.preanalysis_status = 'ok'
    da.save()
