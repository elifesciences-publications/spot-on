# -*- coding: utf-8 -*-
# Index of views for the fastSPT-GUI app
# A graphical user interface to the fastSPT tool by Anders S. Hansen, 2016
# By MW, GPLv3+, Feb.-Apr. 2017
#
# Here we store views that relate to the download of the results
# These stuff are controlled by the socket

## ==== Imports
import pickle, json, tempfile, os, logging
from django.shortcuts import get_object_or_404
from .models import Analysis, Dataset, Download
from django.core.files import File
from django.utils import timezone
import tasks

## ==== Views
def set_download(message, data, url_basename) :
    """Function that receives a set of instructions and a graph and that
    generate the corresponding stuff. To do so, it stores the results in the 
    Download database and the downloads are computed asynchronously. Note that
    this view does not start any computation, it just create the database entry.
    
    Returns the id of the database, that will be used by the getter"""

    params = data['params']

    ana = get_object_or_404(Analysis, url_basename=url_basename)
    da = get_object_or_404(Dataset, analysis=ana, id=params['cell'])
    do = Download(analysis=ana,
                  dataset=da,
                  pub_date=timezone.now(),
                  name=params['name'],
                  description=params['description'])

    # Save params and export_svg here, defer what should be deferred to a task
    with tempfile.NamedTemporaryFile(dir="static/upload/", delete=False) as f1:
        fil1 = File(f1)
        pickle.dump({'fit': params['fitParams'],
                     'jld': params['jldParams'],
                     'display': params['display']}, f1)
        do.params = fil1
        do.save()
    with tempfile.NamedTemporaryFile(dir="static/upload/", delete=False) as f2:
        fil2 = File(f2)
        pickle.dump({'jld': params['jld'],
                     'fit': params['fit'],
                     'jldp': params['jldp'],
                     'fitp': params['fitp']}, f2)
        do.data = fil2
        do.save()
    with tempfile.NamedTemporaryFile(dir="static/upload/", delete=False) as f3:
        fil3 = File(f3)
        f3.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
        f3.write(params['svg'].encode('utf-8').replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg" version="1.1"'))
        do.export_svg = fil3
        do.export_svg.name = "{}_{}.svg".format(url_basename, "addStuffHere")
        do.status_svg = 'done'
        do.save()
        
    logging.info("Created a download with id: {}".format(do.id))
    return {'id': do.id, 'status': 'success'}


def get_downloads(message, data, url_basename) :
    """This view returns the list of downloads associated with an analysis"""
    ana = Analysis.objects.get(url_basename=url_basename)
    do = Download.objects.filter(analysis=ana)
    res = []
    for d in do:
        with open(d.params.path, 'r') as f:
            params = pickle.load(f)
            res.append({'do_id': d.id,
                        'cell': d.dataset.id,
                        'jldParams': params['jld'],
                        'fitParams': params['fit'],
                        'display': params['display'],
                        'name': d.name,
                        'description': d.description,
                        'date': d.pub_date.strftime("%d-%m-%Y %H:%M")})
    return res
    
def get_download(message, data, url_basename):
    """Function that either returns the link to the zip archive or a 
    wait message"""
    fmt = data['format']
    download_id = data['download_id']

    ana = get_object_or_404(Analysis, url_basename=url_basename)
    do = Download.objects.get(id=download_id, analysis=ana)

    fil = {'svg': do.export_svg,
           'eps': do.export_eps,
           'pdf': do.export_pdf,
           'png': do.export_png,
           'zip': do.export_zip}
    sta = {'svg': do.status_svg,
           'eps': do.status_eps,
           'pdf': do.status_pdf,
           'png': do.status_png,
           'zip': do.status_zip}

    if sta[fmt] != 'done':
        if sta[fmt] == 'na':
            if fmt in ('eps', 'pdf', 'png'):
                if fmt == 'eps':
                    do.status_eps = 'queued'
                if fmt == 'pdf':
                    do.status_pdf = 'queued'
                if fmt == 'png':
                    do.status_png = 'queued'
                ta = tasks.convert_svg_to.apply_async((fmt, download_id))
            elif fmt == 'zip':
                do.status_zip = 'queued'
                ta = tasks.get_zip.apply_async((download_id,))
            do.save()
            return {'status': 'queued', 'celery_id': ta.id}
        return {'status': sta[fmt]}
        
    else:
        return {'status': 'success', 'url':  os.path.basename(fil[fmt].name)}

def del_download(message, data, url_basename) :
    """Deletes a download entry"""
    download_id = data['download_id']
    ana = get_object_or_404(Analysis, url_basename=url_basename)
    do = Download.objects.get(id=download_id, analysis=ana)

    try:
        do.delete()
        return {"status": "success"}
    except:
        return {"status": "error"}

def get_download_all(message, data, url_basename):
    """Returns a zip file that contains all the downloads"""
    if data["celery_id"] == None:
        ta = tasks.get_zip_all.apply_async((data["download_ids"],))
        return {"status": "queued", "celery_id": ta.id}
    else:
        r = tasks.get_zip_all.AsyncResult(data['celery_id'])
        if r.status == 'SUCCESS':
            return {"status": "success",
                    "url": "{}".format(r.result.split("/")[-1])}
        else:
            return {"status": "error", "message": "not ready"}
