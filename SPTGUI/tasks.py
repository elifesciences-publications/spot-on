# Index of the asynchronous tasks to be performed for the fastSPT-GUI
# By MW, GPLv3+, Feb.-Apr. 2017

##
## ==== A bunch of imports
##

## General imports
from __future__ import absolute_import, unicode_literals
import os, sys, tempfile, json, pickle, fasteners, subprocess, shutil
import numpy as np
import pandas as pd

## Celery imports
from celery import shared_task
from celery.utils.log import get_task_logger

## Initialize django stuff
import django
django.setup()

from django.core.files import File
from SPTGUI.models import Dataset, Download
import SPTGUI.parsers as parsers

## Import analysis backend
import fastspt
import SPTGUI.statistics as stats

##
## ==== Initialize stuff
##
logger = get_task_logger(__name__)

##
## ==== Here go the tasks to be performed asynchronously
##    

@shared_task
def compute_jld(dataset_id, pooled=False, include=None,
                path=None, hash_prefix=None, url_basename=None,
                compute_params=None, default=False):
    """
    This function computes the histogram of jump length of an uploaded 
    dataset and save it in the corresponding dataset slot. It does not 
    compute the fit of the dataset.

    The `compute_jld` function accepts both single and multi cells computations 
    of the jump lengths distribution (jld) through two configurations of
    arguments:

    1. Single cell/dataset computation: if `dataset_id` is provided AND
    `pooled=False`. In that case, the computed histogram is saved in the database
    2. Multiple cell/dataset computation: if `pooled=True`, `include` is a list
    of datasets (represented by their id in the database) and `fname` is a 
    string that will be used as a prefix for saving. Saving is performed as a 
    pickle object.

    Finally, if `compute_params` is provided as a dictionary (and not None), the
    jld is computed with custom parameters instead of the default ones, and the
    result is saved in at a custom location (similarly as the pooled values).

    Arguments:
    ---------
    - dataset_id (int): the id of the dataset in the Dataset database (single cell only)
    - pooled (bool): whether we should compute a single (False) or a multi-dataset (True) jld
    - include (list of int): if `pooled==True`, the list of dataset ids in the Dataset database.
    - path (str): if `pooled==True`, the folder where to save the results
    - hash_prefix (str): if `pooled==True`, the prefix to be used for saving
    - url_basename (str): if `pooled==True`, the folder where to save the results
    - compute_params (dict): a dictionary of parameters to be passed to the
    compute_jump_length_distribution of the fastspt backend.
    """
    compute_jld.update_state(state='PROGRESS', meta={'progress': 'loading file'})
    ## ==== Load datasets
    savefile = False
    if compute_params != None:
        prog_p = os.path.join(path,url_basename, "jld_{}_{}.pkl".format(hash_prefix, dataset_id))
        savefile = True
    else:
        compute_params = {}
    if not pooled:
        include = [dataset_id]
    else: ## Return if it has already been computed
        prog_p = os.path.join(path,url_basename, "{}_pooled.pkl".format(hash_prefix))
        savefile = True
    if savefile:
        if os.path.exists(prog_p):
            with open(prog_p, 'r') as f:
                save_params = pickle.load(f)
                if save_params['status'] == 'done':
                    if save_params['include']==include:
                        return (path, url_basename, hash_prefix, include)
                    else:
                        print "Includes do not match, recomputing"
                else:
                    save_params['status'] = 'computing'
            with open(prog_p, 'w') as f:
                pickle.dump(save_params, f)
                        
    cell_l = []
    for da_id in include:
        da = Dataset.objects.get(id=da_id)
        with open(da.parsed.path, 'r') as f:  ## Open dataset
            cell_l.append(parsers.to_fastSPT(f)) ##Format the dataset for analysis
    cell = np.hstack(cell_l)
            
    ## ==== Compute the JLD
    compute_jld.update_state(state='PROGRESS', meta={'progress': 'computing JLD'})

    an = fastspt.compute_jump_length_distribution(cell, CDF=True, **compute_params) ## Perform the analysis
    logger.info("DONE: Computed JLD for dataset(s) {}".format(include))

    
    compute_jld.update_state(state='PROGRESS', meta={'progress': 'saving result'})
    ## ==== Save results
    if not savefile or default:
        with tempfile.NamedTemporaryFile(dir="static/upload/", delete=False) as f:
            fil = File(f)
            pickle.dump(an, fil)
            da.jld = fil
            da.jld.name = da.data.name + '.jld'
            da.save()
    if savefile:
        with fasteners.InterProcessLock(prog_p+'.lock'):
            if pooled:
                with open(prog_p, 'w') as f:
                    pickle.dump({'jld': an,
                                 'include': include,
                                 'status': 'done',
                                 'fit': None,
                                 'fitparams': None,
                                 'params' : None}, f)
            else:
                with open(prog_p, 'r') as f:
                    save_params = pickle.load(f)
                save_params['jld'] = an
                save_params['status'] = 'done'
                with open(prog_p, 'w') as f:
                    pickle.dump(save_params, f)
    return (path, url_basename, hash_prefix, include)


@shared_task
def fit_jld(arg, hash_prefix):
    (path, url_basename, hash_jld, dataset_id) = arg
    """This function fits the histogram of jump lengths of a given 
    dataset for a specific set of parameters to a BOUND-UNBOUND kinetic 
    model.
    
    Inputs:
    - path: the folder where the analyses are stored
    - url_basename: the name of the analysis page
    - hash_prefix: the prefix filename
    - dataset_id: the id of the dataset in the database.

    Returns: None
    - Update the Dataset entry with the appropriately parsed information
    """
    prog_p = os.path.join(path,url_basename, "{}_progress.pkl".format(hash_prefix+hash_jld))
    prog_jld = os.path.join(path,url_basename, "jld_{}_{}.pkl".format(hash_jld, dataset_id))
    
    if type(dataset_id)==list:
        pooled=True
    elif type(dataset_id)==int:
        pooled=False
    else:
        raise TypeError("dataset_id should be either an int or a list")

    
    ## ==== Load JLD
    if not pooled:
        da =  Dataset.objects.get(id=dataset_id)
        with open(prog_jld, 'r') as f: ## Open the pickle file
            jld = pickle.load(f)['jld']
        prog_da = os.path.join(path,url_basename,
                               "{}_{}.pkl".format(hash_prefix+hash_jld,
                                                  dataset_id))
        out_pars = {}
    else:
        prog_jld = os.path.join(path,url_basename, "{}_pooled.pkl".format(hash_jld))
        prog_da = os.path.join(path,url_basename, "{}_pooled.pkl".format(hash_prefix+hash_jld))
        with open(prog_jld, 'r') as f:
            out_pars = pickle.load(f)
            jld = out_pars['jld']
            
    HistVecJumps = jld[2] ## Extract from the pickled file
    JumpProb = jld[3]
    HistVecJumpsCDF = jld[0]
    JumpProbCDF = jld[1]
    
    ## ==== Initialize
    with fasteners.InterProcessLock(prog_p+'.lock'):
        with open(prog_p, 'r') as f:
            save_pars = pickle.load(f)
            if not pooled:
                save_pars['queue'][dataset_id]['status'] = 'processing'
            else:
                save_pars['queue']['pooled']['status'] = 'processing'
        with open(prog_p, 'w') as f:
            pickle.dump(save_pars, f)

    ## ==== Sanity format the dictionary of parameters
    params = save_pars['pars'].copy()
    fit2states = params["fit2states"]
    params.pop("include")
    params.pop("hashvalue")
    
    if fit2states:
        params["LB"] = np.array([params["D_free"][0],
                                 params["D_bound"][0],
                                 params["F_bound"][0],
                                 params["sigma"][0]])
        params["UB"] = np.array([params["D_free"][1],
                                 params["D_bound"][1],
                                 params["F_bound"][1],
                                 params["sigma"][1]])
        params.pop("D_bound")
        params.pop("D_free")
        params.pop("F_bound")
        params.pop("sigma")
    else:
        params["LB"] = np.array([params["D_fast"][0],
                                 params["D_med"][0],
                                 params["D_bound"][0],
                                 params["F_fast"][0],
                                 params["F_bound"][0],
                                 params["sigma"][0]])
        params["UB"] = np.array([params["D_fast"][1],
                                 params["D_med"][1],
                                 params["D_bound"][1],
                                 params["F_fast"][1],
                                 params["F_bound"][1],
                                 params["sigma"][1]])
        params.pop("D_fast")
        params.pop("D_med")
        params.pop("D_bound")
        params.pop("F_fast")
        params.pop("sigma")
                                
    
    ## ==== Perform the fit and compute the distribution
    fit = fastspt.fit_jump_length_distribution(JumpProb, JumpProbCDF,
                                               HistVecJumps, HistVecJumpsCDF,
                                               **params)
    ## Generate the PDF corresponding to the fitted parameters
    y = fastspt.generate_jump_length_distribution(
        fit.params,  
        JumpProb = JumpProb,
        r = HistVecJumpsCDF,
        LocError = fit.params['sigma'].value,
        #LocError = params['LocError'],
        dT = params['dT'],
        dZ = params['dZ'],
        a = params["a"],
        b = params["b"],
        fit2states = fit2states)
        
    ## Normalize it
    norm_y = np.zeros_like(y)
    for i in range(y.shape[0]): # Normalize y as a PDF
        norm_y[i,:] = y[i,:]/y[i,:].sum()
        scaled_y = (float(len(HistVecJumpsCDF))/len(HistVecJumps))*norm_y
    
    # ==== Save results
    ## Save the histogram (save params AND the hist)
    with fasteners.InterProcessLock(prog_da+'.lock'):
        with open(prog_da, 'w') as f:
            out_pars['fit'] = {'x': HistVecJumpsCDF, 'y':scaled_y}
            out_pars['fitparams'] = fit.params
            out_pars['fit_ssq2'] = fit.params.ssq2
            out_pars['fit_aic'] = fit.aic
            out_pars['fit_bic'] = fit.bic
            out_pars['params'] = save_pars['pars']
            pickle.dump(out_pars, f)
    
    ## Open the pickle file and change the pickle file to 'done'
    with fasteners.InterProcessLock(prog_p+'.lock'):
        with open(prog_p, 'r') as f:
            save_pars = pickle.load(f)
        if pooled:
            save_pars['queue']['pooled']['status'] = 'done'            
        else:
            save_pars['queue'][dataset_id]['status'] = 'done'            
        with open(prog_p, 'w') as f:
            pickle.dump(save_pars, f)
    
#@shared_task(ignore_result=True)
@shared_task(ignore_result=False)
def check_input_file(filepath, file_id, fmt, fmtParams):
    """This function checks that the uploaded file has the right format and
    can be analyzed. It is further saved in the database
    
    Inputs:
    - filepath: the path to the file to be checked
    - file_id: the id of the file in the database.
    - fmt (str): the file format, coming from the user
    - fmtParams (dict): a dictionary of format-specific parameters for the parser

    Returns: None
    - Update the Dataset entry with the appropriately parsed information
    """

    check_input_file.update_state(state='PROGRESS', meta={'progress': 'checking file format'})
    ## ==== Sanity checks
    da = Dataset.objects.get(id=file_id)
    
    ## ==== Check file format
    fi = parsers.read_file(da.data.path, fmt, fmtParams) ## DEBUG, should be in the try
    try: # try to parse the file
        fi = parsers.read_file(da.data.path, fmt, fmtParams)
    except: # exit
        da.preanalysis_token = ''
        da.preanalysis_status = 'error'
        toremove = da.data.path
        da.data.delete()
        da.save()
        if os.path.isfile(toremove):
            os.remove(toremove)
        return

    ## ==== Save the parsed result!
    with tempfile.NamedTemporaryFile(dir="static/upload/", delete=False) as f:
        fil = File(f)
        fil.write(json.dumps(fi))

        da.parsed = fil
        da.parsed.name = da.data.name + '.parsed'
        da.save()

    check_input_file.update_state(state='PROGRESS', meta={'progress': 'computing statistics'})

    ## ==== Extract the relevant information
    da.pre_ntraces = stats.number_of_trajectories(fi) # number of traces
    da.pre_ntraces3= stats.number_of_trajectories3(fi)
    da.pre_npoints = stats.number_of_detections(fi)   # number of points
    da.pre_njumps  = stats.number_of_jumps(fi)
    da.pre_nframes = stats.number_of_frames(fi) # Number of frames
    le = stats.length_of_trajectories(fi)
    da.pre_median_length_of_trajectories = le["median"]
    da.pre_mean_length_of_trajectories   = le["mean"]
    le = stats.particles_per_frame(fi)
    da.pre_median_particles_per_frame    = le["median"]
    da.pre_mean_particles_per_frame      = le["mean"]
    le = stats.jump_length(fi)
    da.pre_median_jump_length            = le["median"]
    da.pre_mean_jump_length              = le["mean"]
    
    ## ==== Update the state
    da.preanalysis_token = ''
    da.preanalysis_status = 'ok'
    da.save()
    check_input_file.update_state(state='PROGRESS', meta={'progress': 'file checked'})

    return file_id

@shared_task
def convert_svg_to(fmt, download_id):
    """Converts the SVG file indexed by `download_id` to a given format `fmt`.
    Uses Inkscape in the background."""

    do = Download.objects.get(id=download_id)
    
    options = {'pdf' : ['-A'],
               'png' : ['-e', '-d', '300'],
               'eps' : ['-E']}
    
    tmpdirname = tempfile.mkdtemp()
    out_file = 'export.{}'.format(fmt)
    path = os.path.join(tmpdirname,out_file)
    subprocess.call(["inkscape", "-f",
                     do.export_svg.path,
                     options[fmt][0],
                     path]+options[fmt][1:])
    with tempfile.NamedTemporaryFile(dir="SPTGUI/static/SPTGUI/downloads/",
                                     prefix="{}_".format(do.name),
                                     suffix=".{}".format(fmt),
                                     delete=False) as f:
        F = File(f)
        with open(path, 'r') as ff:
            F.write(ff.read())
        if fmt=='png':
            do.export_png = F
            do.status_png = 'done'
        if fmt=='pdf':
            do.export_pdf = F
            do.status_pdf = 'done'
        if fmt=='eps':
            do.export_eps = F
            do.status_eps = 'done'
        do.save()

@shared_task
def get_zip(download_id):
    """Function that zips the results of an analysis and generate all the
    required reports to be sent for download. This function is to be called
    from the celery backend directly."""

    ## ==== Initialize the exports
    convert_svg_to('png', download_id) ## Get the png
    convert_svg_to('pdf', download_id) ## Get the pdf
    convert_svg_to('eps', download_id) ## Get the eps

    ## ==== Initialize objects
    do = Download.objects.get(id=download_id)
    ana = do.analysis
    da = Dataset.objects.filter(analysis=ana)
    
    ## ==== Save everything to the tmp folder
    tmpdirname = tempfile.mkdtemp() ## Create the temp dir
    collect_download_for_zip(tmpdirname, do, ana, da) ## Create the folder architecture

    ## zip and move it at the right place
    fname = ''
    with tempfile.NamedTemporaryFile(dir="SPTGUI/static/SPTGUI/downloads/",
                                     prefix="{}_".format(do.name),
                                     suffix="_{}".format(ana.url_basename),
                                     delete=False) as f:
        fname = f.name
    os.remove(fname)
    shutil.make_archive(fname, 'zip', tmpdirname)
    with open(fname+".zip", 'r') as f2:
        fi = File(f2)
        do.export_zip = fi
        do.save()
    
    ## Get a table formatting for the analysis parameters    
    shutil.rmtree(tmpdirname) ## Delete the temporary dir

    ## say that we are done
    do.status_zip = 'done'
    do.save()
    
@shared_task
def get_zip_all(download_ids):
    """Function that collects all downloads in `download_ids` in a single zip
    file and returns the path when done"""
    # ==== Create the output folder
    tmpdirname = tempfile.mkdtemp() ## Create the temp dir

    # ==== Populate it
    #if type(download_ids)==int:
    #    download_ids=list(download_ids)
    for (i,download_id) in enumerate(download_ids):
        convert_svg_to('png', download_id) ## Get the png
        convert_svg_to('pdf', download_id) ## Get the pdf
        convert_svg_to('eps', download_id) ## Get the eps

        ## ==== Initialize objects
        do = Download.objects.get(id=download_id)
        ana = do.analysis
        da = Dataset.objects.filter(analysis=ana)
    
        ## ==== Save everything to the tmp folder
        subpath=os.path.join(tmpdirname, str(i+1))
        os.mkdir(subpath)
        collect_download_for_zip(subpath, do, ana, da) ## Create the folder architecture

    ## zip and move it at the right place
    fname = ''
    with tempfile.NamedTemporaryFile(dir="SPTGUI/static/SPTGUI/downloads/", prefix="{}_".format(ana.url_basename), delete=False) as f:
        fname = f.name
    os.remove(fname)
    shutil.make_archive(fname, 'zip', tmpdirname)
    #with open(fname+".zip", 'r') as f2:
    #    fi = File(f2)
    #    ana.export_zip_all = fi
    #    ana.save()
    
    ## Get a table formatting for the analysis parameters    
    shutil.rmtree(tmpdirname) ## Delete the temporary dir

    return fname + ".zip"
    


## ==== Helper functions
def collect_download_for_zip(tmpdirname, do, ana, da):
    """Function that create the folder structure to be zipped. It takes one
    download as input and create the folder structure at the `path` location."""
    basename = os.path.basename
    ## Create the folder architecture
    os.mkdir(os.path.join(tmpdirname, 'raw'))
    os.mkdir(os.path.join(tmpdirname, 'fit'))
    os.mkdir(os.path.join(tmpdirname, 'jld'))
    os.mkdir(os.path.join(tmpdirname, 'graphs'))

    ## Get the raw files
    raw = os.path.join(tmpdirname, 'raw')
    for d in da:
        shutil.copyfile(d.data.path, "{}/{}_{}".format(raw, d.id, basename(d.data.name)))
        shutil.copyfile(d.parsed.path, "{}/{}_{}".format(raw,d.id, basename(d.parsed.name)))

    ## Get graphs
    gra = os.path.join(tmpdirname, 'graphs')
    shutil.copyfile(do.export_png.path, "{}/{}".format(gra, basename(do.export_png.name)))
    shutil.copyfile(do.export_pdf.path, "{}/{}".format(gra, basename(do.export_pdf.name)))
    shutil.copyfile(do.export_eps.path, "{}/{}".format(gra, basename(do.export_eps.name)))
    shutil.copyfile(do.export_svg.path, "{}/{}".format(gra, basename(do.export_svg.name)))
    
    ## Get the raw fitted coefficients & fit parameters
    bn = tmpdirname
    shutil.copyfile(do.data.path, "{}/fit_{}".format(bn, basename(d.data.name)))
    shutil.copyfile(do.params.path, "{}/params_{}".format(bn, basename(do.params.name)))
    with open(os.path.join(bn, "fit_parameters.txt"), "w") as f:
        with open(do.params.name, 'r') as ff:
            params = pickle.load(ff)
            f.write("\n\n".join(get_export_fit(params)))
    with open(os.path.join(bn, "fit_coefficients.txt"), "w") as f:
        with open(do.data.name, 'r') as ff:
            coefs = pickle.load(ff)
            print "Coefs: ", coefs.keys()
            if "fit" in coefs and coefs["fit"]!=None and "fitparams" in coefs["fit"]:
                f.write("---- Individual fit")
                f.write(get_export_coefficients(coefs['fit']['fitparams']))
            elif "fitp" in coefs and coefs["fitp"]!=None and "fitparams" in coefs["fitp"]:
                f.write("---- Global fit")
                f.write(get_export_coefficients(coefs['fitp']['fitparams']))
            else:
                f.write("No fit performed")
                
    ## Export raw tables
    with open(do.data.name, 'r') as f:
        curves = pickle.load(f)
        table_raw = get_export_tableJLD(curves)
        table_raw.to_csv(os.path.join(bn, "raw_tables.csv"))
        table_fit = get_export_tableFIT(curves)
        table_fit.to_csv(os.path.join(bn, "fit_tables.csv"))
        
    ## Get statistics    
    with open(os.path.join(bn, "statistics.txt"), "w") as f: 
        f.write("\n\n".join(get_export_statistics(da)))
    
def check_filefield(d):
    """Returns if a file of a FileField exists"""
    try:
        return os.path.exists(d.path)
    except:
        return False

def get_export_tableJLD(ta):
    """
    This function returns, either for the PDF or the CDF:
    - the JLD/the pooled JLD
    - the fit
    - the corresponding jump distance
    In a format that can easily be exported (easy to convert to CSV)
    For now, the format is a Pandas DataFrame.
    """
    ## Generate the dict
    di = {'time': ta['jld'][0][0]}
    for cell in range(len(ta['jld'])): ## JLD
        for i in range(len(ta['jld'][cell][1])):
            di["cell{}_jl_{}dt".format(cell+1, i+1)] = ta['jld'][cell][1][i]
    if 'jldp' in ta and ta['jldp']!=None: ## Pooled JLD
        for i in range(len(ta['jldp'][1])):
            di["pooled_jl_{}dt".format(i+1)] = ta['jldp'][1][i]
    
    return pd.DataFrame(di) ## Convert it to Pandas

def get_export_tableFIT(ta):
    """
    This function returns, either for the PDF or the CDF:
    - the JLD/the pooled JLD
    - the fit
    - the corresponding jump distance
    In a format that can easily be exported (easy to convert to CSV)
    For now, the format is a Pandas DataFrame.
    """
    di = {}
    for cell in range(len(ta["fit"])): ## Not sure this will work
        if ta['fit'][cell] != None:
            di['time'] = ta['fit'][cell][0]         
            for i in range(len(ta['fit'][cell][1])):
                di["cell{}_fit_{}dt".format(cell+1, i+1)] = ta['fit'][cell][1][i]
    if 'fitp' in ta and ta['fitp']!=None and ta['fitp']['status']=='done':
        di['time'] = ta['fitp']['fit']['x']        
        for i in range(len(ta['fitp']['fit']['y'])):
            di["pooled_fit_{}dt".format(i+1)] = ta['fitp']['fit']['y'][i]
            
    return pd.DataFrame(di) ## Convert it to Pandas

def get_export_coefficients(co):
    """Returns the fitted coefficients"""
    t = "\n"
    for k in co:
        if k not in ('fit',):
            t+="{}: {}\n".format(k, co[k])
    return t
    

def get_export_fit(fi):
    """If there is a fit, returns the fitting parameters 
    (not the fitted coefficients)."""
    out = []
    for k in fi:
        t = "---- {}\n".format(k)
        for kk in fi[k]:
            if kk not in ('hashvalue', 'hashvalueJLD'):
                t+="{}: {}\n".format(kk, fi[k][kk])
        out.append(t)
    return out

def get_export_statistics(da):
    """
    Returns statistics about the datasets
    Inputs:
    - da: a Queryset
    Output:
    - A list of strings
    """
    out = []
    for d in da:
        t = """---- {}
Description: {}
Number of traces: {}
Number of localizations: {}
Number of traces with >=3 localizations: {},
Number of frames: {}
Number of jumps: {}
Median length of trajectories: {}
Mean length of trajectories: {}
Median number of particles per frame: {}
Mean number of particles per frame: {}
Median jump length: {}
Mean jump length: {}

"""
        out.append(t.format(d.name, d.description, d.pre_ntraces, d.pre_npoints,
                 d.pre_ntraces3, d.pre_nframes, d.pre_njumps,
                 d.pre_median_length_of_trajectories,
                 d.pre_mean_length_of_trajectories,
                 d.pre_median_particles_per_frame, d.pre_mean_particles_per_frame,
                 d.pre_median_jump_length, d.pre_mean_jump_length))
    return out
