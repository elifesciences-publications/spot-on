# Index of views for the fastSPT-GUI app
# A graphical user interface to the fastSPT tool by Anders S. Hansen, 2016
# By MW, GPLv3+, Feb.-Apr. 2017
#
# Here we store views that perform actions related to the import of datasets
# such as returning the importation report of the file in various formats.

## ==== Imports
import json, os

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from wsgiref.util import FileWrapper

from .models import Analysis, Dataset

## ==== Views
def dataset_original(request, url_basename, dataset_id):
    """Function that return a pointer to the original file"""

    ## Sanity checks
    ana = get_object_or_404(Analysis, url_basename=url_basename)
    da = get_object_or_404(Dataset, analysis=ana, id=dataset_id)
 
    ## Return data
    response = HttpResponse(FileWrapper(da.data.file),
                            content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename={}'.format(os.path.basename(da.data.path))
    return response
        

def dataset_parsed(request, url_basename, dataset_id):
    """Function that return a pointer to the parsed file"""
    ## Sanity checks
    ana = get_object_or_404(Analysis, url_basename=url_basename)
    da = get_object_or_404(Dataset, analysis=ana, id=dataset_id)    

    ## Return data
    response = HttpResponse(FileWrapper(da.parsed.file),
                            content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename={}'.format(os.path.basename(da.parsed.path))
    return response

def dataset_report(request, url_basename, dataset_id):
    """Function that return a pointer to the importation report"""
    ## Sanity checks
    ana = get_object_or_404(Analysis, url_basename=url_basename)
    da = get_object_or_404(Dataset, analysis=ana, id=dataset_id)    
    
    ## Return data
    try:
        ret = da.import_report.replace("\n", "\n<br/>")
    except:
        ret = "Import report not available, maybe the file is still processing"
    response = HttpResponse(ret)
    return response
