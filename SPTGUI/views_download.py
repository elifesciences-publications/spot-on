# Index of views for the fastSPT-GUI app
# A graphical user interface to the fastSPT tool by Anders S. Hansen, 2016
# By MW, GPLv3+, Feb.-Apr. 2017
#
# Here we store views that relate to the download of the results

## ==== Imports
import pickle, json, tempfile, os
import tasks
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from .models import Analysis, Dataset, Download
from django.core.files import File

## ==== Actual functions
def check_filefield(d):
    """Function to avoid an exception when checking whether a file exists 
    in the database"""
    try:
        return os.path.exists(d.path)
    except:
        return False
    
def set_download(request, url_basename) :
    """Function that receives a set of instructions and a graph and that
    generate the corresponding stuff. To do so, it stores the results in the 
    Download database and the downloads are computed asynchronously. 
    
    Returns the id of the database, that will be used by the getter"""

    ana = get_object_or_404(Analysis, url_basename=url_basename)
    
    if request.method == 'POST':
        body = json.loads(request.body)
        da = get_object_or_404(Dataset, analysis=ana, id=body['cell'])
        do = Download(dataset=da)
        
        # Save params and export_svg here, defer what should be deferred to a task
        with tempfile.NamedTemporaryFile(dir="static/upload/", delete=False) as f1:
            fil1 = File(f1)
            pickle.dump({'fit': body['fitParams'], 'jld': body['jldParams']}, f1)
            do.params = fil1
            do.save()
        with tempfile.NamedTemporaryFile(dir="static/upload/", delete=False) as f2:
            fil2 = File(f2)
            pickle.dump({'jld': body['jld'],
                         'fit': body['fit'],
                         'jldp': body['jldp'],
                         'fitp': body['fitp']}, f2)
            do.data = fil2
            do.save()
        with tempfile.NamedTemporaryFile(dir="static/upload/", delete=False) as f3:
            fil3 = File(f3)
            f3.write(body['svg'])
            do.export_svg = fil3
            do.export_svg.name = "{}_{}.svg".format(url_basename, "addStuffHere")
            do.status_svg = 'done'
            do.save()

        if body['format'] not in ('svg', 'zip'):
            tasks.convert_svg_to.delay(body['format'], do.id)
            
        return HttpResponse(json.dumps({'id': do.id, 'status': 'success'}), content_type='application/json')

    else :
        return HttpResponse(json.dumps({'status': 'error'}), content_type='application/json', status=400)



def get_download(request, url_basename, download_id, format):
    """Function that either returns the link to the zip archive or a 
    wait message"""

    do = Download.objects.get(id=download_id)

    fil = {'svg': do.export_svg,
           'eps': do.export_eps,
           'pdf': do.export_pdf,
           'png': do.export_png}
    sta = {'svg': do.status_svg,
           'eps': do.status_eps,
           'pdf': do.status_pdf,
           'png': do.status_png}

    if sta[format] != 'done':
        return HttpResponse(json.dumps({'status': sta[format]}), content_type='application/json')
    else:
        return HttpResponse(json.dumps({'status': 'success', 'url':  os.path.basename(fil[format].name)}), content_type='application/json')
