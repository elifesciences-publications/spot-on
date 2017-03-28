# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
import tempfile, json

## Initialize django stuff
import django
django.setup()

from django.core.files import File
from SPTGUI.models import Dataset
import SPTGUI.parsers as parsers

##
## ==== Here go the tasks to be performed asynchronously
##    

@shared_task
def empirical_jld():
    """This function computes the empirical jump length distribution of a 
    dataset"""
    import time
    time.sleep(5)
    return [1,1,7,1,2,7,0,1,4]

@shared_task
def check_input_file(filepath, file_id):
    """This function checks that the uploaded file has the right format and
    can be analyzed. It is further saved in the database
    
    Inputs:
    - filepath: the path to the file to be checked
    - file_id: the id of the file in the database.

    Returns: None
    - Update the Dataset entry with the appropriately parsed information
    """
    
    ## ==== Sanity checks
    da = Dataset.objects.get(id=file_id)
    
    ## ==== Check file format
    try: # try to parse the file
        fi = parsers.read_file(da.data.path)
    except: # exit
        da.preanalysis_token = ''
        da.preanalysis_status = 'error'
        da.save()
        return

    ## ==== Save the parsed result!
    with tempfile.NamedTemporaryFile(dir="uploads/", delete=False) as f:
        fil = File(f)
        fil.write(json.dumps(fi))

        da.parsed = fil
        da.parsed.name = da.data.name + '.parsed'
        da.save()

    ## ==== Extract the relevant information
    da.pre_ntraces = len(fi) # number of traces
    da.pre_npoints = sum([len(i) for i in fi]) # number of points

    ## ==== Update the state
    da.preanalysis_token = ''
    da.preanalysis_status = 'ok'
    da.save()
