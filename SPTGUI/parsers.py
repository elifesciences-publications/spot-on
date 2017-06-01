# parsers.py, several implementations of parsers of SPT data
# By Maxime Woringer
# GPLv3+ or AGPL, Feb. 2017
#
# ====
# The goal of the parsers is to start from a "random" file format and to end
#+up with a standardized file format that can be easily pickled and saved as a
#+file in the database.
#
#+The current file format is a list of traces. Each trace is a list of tuples:
#+ (x,y,t,f), with either t (time) or f (frame number) that can have a NA value.


## ==== Imports
import scipy.io, os, json
import numpy as np

##
## ==== This are some helper functions
##

def traces_to_csv(traces):
    """Returns a CSV file with the format 
    trace_number,x,y,t,f
    """
    csv = ""
    for (tr_n, tr) in enumerate(traces):
        for pt in tr:
            csv +="{},{},{},{},{}\n".format(tr_n, pt[0],pt[1],pt[2],pt[3])
    return csv

##
## ==== This is the real parser section
##
def list_formats():
    """Returns the list of formats for which we have parsers"""
    return [(init['name'], init['init']()) for init in inits]
        

def read_file(fn, fmt, fmtParams):
    """A wrapper for all the parsers. To be run sequencially. 
    To be effective, the parser should raise an exception if it 
    cannot deal with the file

    Inputs:
    - fn (str): the path to the file to be parsed
    - fmt (str): the format of the file, corresponding to the parser to be applied
    - fmtParams (dict): extra parameters for the parser.

    Returns: the parsed file (as a list of trajectories)
    """

    ## Sanity checks
    if not os.path.isfile(fn):
        raise IOError("File not found: {}".format(fn))

    da = initsDict[fmt]['parser'](fn, **fmtParams)
    #da = read_anders(fn)

    return da

## ==== evalSPT file format
def init_evalspt():
    return {'name': 'evalSPT', 'info': "not implemented", 'anchor': 'evalspt',
            'active': False, 'params': []}

## ==== MOSAIC suite file format
def init_mosaic():
    pars = [{'name': 'framerate (ms)', 'info': '', 'type': 'number',
             'value': 'framerate', 'model': 'framerate'},
            {'name': 'pixel size (nm/px)', 'type': 'number',
             'value': 'pixelsize', 'model': 'pixelsize'}]
    return {'name': 'MOSAIC suite', 'info': "not implemented", 'anchor': 'mosaic',
            'active': True, 'params': pars}

## ==== UTrack file format
def init_utrack():
    return {'name': 'UTrack', 'info': "not implemented", 'anchor': 'utrack',
            'active': False, 'params': []}

## ==== TrackMate file format
def init_trackmate():
    pars = [{'name': 'XML', 'type': 'radio', 'info': '',
             'value': 'xml', 'model': 'format'},
            {'name': 'CSV', 'type': 'radio', 'info': '',
             'value': 'csv', 'model': 'format'},
            {'name': 'framerate (ms)', 'type': 'number', 'info': 'placeholder',
             'value': 'framerate', 'model': 'framerate'}]
    return {'name': 'TrackMate', 'info': "not implemented", 'anchor': 'trackmate',
            'active': True, 'params': pars}

## ==== CSV file format
def init_csv():
    return {'name': 'CSV', 'info': "not implemented", 'anchor': 'csv',
            'active': True, 'params': []}

## ==== Anders' file format
def init_anders():
    """Returns a list of extra parameters to be entered by the user.
    For the case of Anders' file format, we do not need any extra parameter
    So we return an empty list."""
    return {'name': "Anders' file format",
            'info': "Anders' custom Matlab file format",
            'anchor': "matlab",
            'active': True,
            'params': []}

def read_anders(fn, new_format=True):
    """The file format sent by Anders. I don't really know where it 
    comes from.
    new_format tells whether we should perform weird column manipulations
    to get it working again..."""
    
    def new_format(cel):
        """Converts between the old and the new Matlab format. To do so, it 
        swaps columns 1 and 2 of the detections and transposes the matrices"""
        cell = cel.copy()
        for i in range(len(cell)):
            f = cell[i][2].copy()
            cell[i][2] = cell[i][1].T.copy()
            cell[i][1] = f.T
        return cell
    
    ## Sanity checks
    if not os.path.isfile(fn):
        raise IOError("File not found: {}".format(fn))

    try:
        mat = scipy.io.loadmat(fn)
        m=np.asarray(mat['trackedPar'])
    except:
        raise IOError("The file does not seem to be a .mat file ({})".format(fn))

    if new_format:
        m[0] = new_format(m[0])
    
    ## Make the conversion
    traces_header = ('x','y','t','f')
    traces = []
    for tr in m[0]:
        x = [float(i) for i in tr[0][:,0]]
        y = [float(i) for i in tr[0][:,1]]
        t = [float(i) for i in tr[1][0]]
        f = [int(i) for i in tr[2][0]]
        traces.append(zip(x,y,t,f))
    return traces

## ==== Format for fastSPT
def to_fastSPT(f):
    """Returns an object formatted to be used with fastSPT from a parsed dataset
    (in the internal representation of the GUI). f is a file descriptor (thus the
    function assumes that the file exists).

    Actually, the fastSPT code is a little bit picky about what it likes and what
    it doesn't. It cares strictly about the file format, that is a nested numpy
    object, and of the data types. I expect many bugs to arise from improper 
    converters that do not fully comply with the file format."""

    da = json.loads(f.read()) ## Load data

    ## Create the object
    dt = np.dtype([('xy', 'O'), ('TimeStamp', 'O'), ('Frame', 'O')]) # dtype
    DT = np.dtype('<f8', '<f8', 'uint16')
    trackedPar = []
    for i in da:
        xy = []
        TimeStamp = []
        Frame = []
        for p in i:
            xy.append([p[0],p[1]])
            TimeStamp.append(p[2])
            Frame.append(p[3])
        trackedPar.append((np.array(xy, dtype='<f8'),
                           np.array([TimeStamp], dtype='<f8'),
                           np.array([Frame], dtype='uint16')))
    return np.asarray(trackedPar, dtype=dt)

## ==== Inits
inits = [{'name': 'csv',       'init': init_csv, 'parser': read_anders},
         {'name': 'trackmate', 'init': init_trackmate, 'parser': read_anders},
         {'name': 'utrack',    'init': init_utrack, 'parser': read_anders},
         {'name': 'mosaic',    'init': init_mosaic, 'parser': read_anders},
         {'name': 'evalspt',   'init': init_evalspt, 'parser': read_anders},
         {'name': 'anders',    'init': init_anders, 'parser': read_anders}]
initsDict = {i['name']: i for i in inits}
