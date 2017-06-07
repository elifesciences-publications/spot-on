# Index of views for the fastSPT-GUI app (sockets side)
# A graphical user interface to the fastSPT tool by Anders S. Hansen, 2016
# By MW, GPLv3+, Feb.-Apr. 2017
#
# Here we store views that are routes for the first tab (corresponding to the
# uploadController in Angular.
#
# We also store the logic to have several queues running in parallel with
#+different rules. The current queues are:
# - preprocessing: for the preprocessing of a just uploaded file
# - jld: to compute the jump length distribution
# - fit: to fit a computed jld
# - download: to compute the files to be downloaded (in the download tab)


## ==== Imports
import logging, os
from django.shortcuts import get_object_or_404
from .models import Analysis, Dataset
import SPTGUI.statistics as stats
import tasks

## ==== Views
def poll_queue(message, data, url_basename):
    """A function that takes a list of ids (contained in data) and check the 
    state of the preprocessing
    """
    res = []
    for (idd, queue_type) in zip(data['celery_ids'], data['queue_type']):
        if queue_type == 'preprocessing':
            res.append(poll_preprocessing_queue(idd))
        elif queue_type == 'jld':
            res.append(poll_jld_queue(idd))
        elif queue_type == 'fit':
            res.append(poll_fit_queue(idd))
        elif queue_type == 'download':
            res.append(poll_download_queue(idd))
        else:
            logging.error("Unknown queue: {}".format(queue_type))

    return res

def poll_download_queue(idd):
    """Relates to the `download` queue"""
    r = tasks.convert_svg_to.AsyncResult(idd)
    #print idd, r.status
    if r.status == 'SUCCESS':
        return 'OK'
    else:
        return r.status

def poll_fit_queue(idd):
    """Relates to the `fit` queue"""
    r = tasks.compute_jld.AsyncResult(idd)
    #print idd, r.status
    if r.status == 'SUCCESS':
        return 'OK'
    else:
        return r.status
    
def poll_jld_queue(idd):
    """Relates to the `jld` queue"""
    r = tasks.compute_jld.AsyncResult(idd)
    #print idd, r.status
    if r.status == 'SUCCESS':
        return 'OK'
    else:
        return r.status

def poll_preprocessing_queue(idd_str) :
    """Relates to the `preprocessing` queue"""
    idd = idd_str.split('@')
    r_chk = tasks.check_input_file.AsyncResult(idd[0])
    r_jld = tasks.check_input_file.AsyncResult(idd[1])
    #print idd, r_chk.status,  r_jld.status
    if r_chk.status == 'PENDING':
        res = 'PENDING'
    elif r_chk.status == 'PROGRESS':
        res = 'CHECKINGFILE'
    elif r_chk.status == 'SUCCESS' and r_jld.status == 'PENDING':
        res = 'CHECKFILEDONE'
    elif r_chk.status == 'SUCCESS' and r_jld.status == 'PROGRESS':
        res = 'COMPUTINGJLD'
    elif r_chk.status == 'SUCCESS' and r_jld.status == 'SUCCESS':
        res = 'OK'
    else:
        res.append("Unhandled message: {}, {}".format(r_chk.status, r_jld.status))
    return res

def list_datasets(message, data, url_basename):
    """
    Function that exposes the list of available datasets for a given analysis 
    (that is, a given url, specified by the `url_basename` (str) parameter, it is
    a view on the Datasets library
    """
    try:
        ana = get_object_or_404(Analysis, url_basename=url_basename)
    except:
        logging.warning("in 'list_datasets', analysis '{}' not found in the database")
        return {'status': 'error',
                'message': 'analysis does not exist'}
    
    ret = [{'id': d.id, ## the id of the Dataset in the database
            'unique_id': d.unique_id,
            'filename' : d.data.name,
            'name' :    d.name,
            'description' : d.description,
            'upload_status' : d.upload_status,
            'preanalysis_status' : d.preanalysis_status,

            ## Preanalysis statistics
            'pre_ntraces' : d.pre_ntraces,
            'pre_npoints' : d.pre_npoints,
            'pre_ntraces3' : d.pre_ntraces3,
            'pre_nframes' : d.pre_nframes,
            'pre_njumps' : d.pre_njumps,
            'pre_median_length_of_trajectories' : d.pre_median_length_of_trajectories,
            'pre_mean_length_of_trajectories' : d.pre_mean_length_of_trajectories,
            'pre_median_particles_per_frame' : d.pre_median_particles_per_frame,
            'pre_mean_particles_per_frame' : d.pre_mean_particles_per_frame,
            'pre_median_jump_length' : d.pre_median_jump_length,
            'pre_mean_jump_length' : d.pre_mean_jump_length,
            
            'jld_available': check_jld(d),
        } for d in Dataset.objects.filter(analysis=ana)]
    
    return ret


def global_statistics(message, data, url_basename):
    """Function returns some global statistics about all the datasets"""
    def mean(m,e):
        """Compute a weighted mean, given a list of individual means (m)
        and a list of 'effectifs'"""
        return sum([i*j for (i,j) in zip(m,e)])/sum(e)

    try:
        ana = get_object_or_404(Analysis, url_basename=url_basename)
    except:
        return {'status': 'error',
                'message': 'analysis does not exist'}
    try:
        da = Dataset.objects.filter(analysis=ana, preanalysis_status='ok')
    except:
        return {'status': 'error',
                'message': 'dataset not found'}
    if len(da)==0:
        return {'status': 'empty',
                'message': 'no properly uploaded dataset'}

    comp_ltraj = stats.global_mean_median(da, stats.length_of_trajectories)
    comp_ppf = stats.global_mean_median(da, stats.particles_per_frame, reindex_frames=True)
    comp_jlength = stats.global_mean_median(da, stats.jump_length)
    
    res = {'status' : 'ok',
           'ok_traces' : len(da),
           'pre_ntraces' : sum([i.pre_ntraces for i in da]),
           'pre_npoints' : sum([i.pre_npoints for i in da]),
           'pre_ntraces3': sum([i.pre_ntraces3 for i in da]),
           'pre_nframes' : sum([i.pre_nframes for i in da]),
           'pre_njumps'  : sum([i.pre_njumps for i in da]),
           'pre_median_length_of_trajectories' : comp_ltraj['median'],
           'pre_mean_length_of_trajectories' : comp_ltraj['mean'],
           'pre_median_particles_per_frame' : comp_ppf['median'],
           'pre_mean_particles_per_frame' : comp_ppf['mean'],
           'pre_median_jump_length' : comp_jlength['median'],
           'pre_mean_jump_length' : comp_jlength['mean'],
       }
                            
    return res


def edit_api(message, data, url_basename): #request, url_basename):
    """Function to edit a dataset
    So far the following fields of the database are handled:
    - name
    - description
    """

    ana = get_object_or_404(Analysis, url_basename=url_basename)
    d = get_object_or_404(Dataset, id=data['dataset_id'])

    ## Make the update
    d.name = data['dataset']['name']
    d.description = data['dataset']['description']
    d.save()

    ## Return something
    ret = {'id': d.id, ## the id of the Dataset in the database
            'unique_id': d.unique_id,
            'filename' : d.data.name,
            'name' :    d.name,
            'description' : d.description,
            'upload_status' : d.upload_status,
            'preanalysis_status' : d.preanalysis_status}
    
    return ret


## ==== Helper functions
def check_jld(d):
    """Small helper function to check if we have a JLD stored"""
    try:
        return os.path.exists(d.jld.path)
    except:
        return False
