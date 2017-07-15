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
#
# IMPORTANT: to add a file format, you need to edit the 'inits' list at the end
#+of this file.

## ==== Imports
import scipy.io, os, json, xmltodict
import numpy as np
import pandas as pd

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

    return da

## ==== evalSPT file format
def init_evalspt():
    pars = [{'name': 'framerate (ms)', 'info': '', 'type': 'number',
             'value': 'framerate', 'model': 'framerate'}]
    return {'name': 'evalSPT', 'info': "", 'anchor': 'evalspt',
            'active': True, 'params': pars}
def read_evalspt(fn, framerate):
    return read_arbitrary_csv(fn, col_traj=3, col_x=0, col_y=1, col_frame=2,
                              framerate=framerate/1000., sep="\t", header=None)

## ==== MOSAIC suite file format
def init_mosaic():
    pars = [{'name': 'framerate (ms)', 'info': '', 'type': 'number',
             'value': 'framerate', 'model': 'framerate'},
            {'name': 'pixel size (nm/px)', 'type': 'number',
             'value': 'pixelsize', 'model': 'pixelsize'}]
    return {'name': 'MOSAIC suite', 'info': "A ImageJ/Fiji plugin", 'anchor': 'mosaic',
            'active': True, 'params': pars}
def read_mosaic(fn, framerate, pixelsize):
    return read_arbitrary_csv(fn, col_traj="Trajectory", col_x="x", col_y="y", col_frame="Frame", framerate=framerate/1000., pixelsize=pixelsize/1000.)

    
## ==== UTrack file format
def init_utrack():
    pars = [{'name': 'framerate (ms)', 'info': '', 'type': 'number',
             'value': 'framerate', 'model': 'framerate'}]
    return {'name': 'UTrack', 'info': "UTrack file format", 'anchor': 'utrack',
            'active': True, 'params': pars}
def read_utrack(fn, framerate):
    traces = []
    m=scipy.io.loadmat(fn)
    for (idx, tr) in enumerate(m['tracksFinal']):
        out = []
        fp = tr[0][2][0,0]
        pts = tr[0][1].reshape(-1,8)
        for i in range(tr[0][1].size/8):
            out.append([pts[i,0], pts[i,1], (fp+i)*framerate, int(fp+i)])
        traces.append(out)
    return traces    
    
## ==== TrackMate file format
def init_trackmate():
    pars = [{'name': 'XML', 'type': 'radio', 'info': '',
             'value': 'xml', 'model': 'format'},
            {'name': 'CSV', 'type': 'radio', 'info': '',
             'value': 'csv', 'model': 'format'},
            {'name': 'framerate (ms)', 'type': 'number', 'info': 'placeholder',
             'value': 'framerate', 'model': 'framerate'}]
    return {'name': 'TrackMate', 'info': "TrackMate file format (an ImageJ/Fiji plugin)", 'anchor': 'trackmate',
            'active': True, 'params': pars}

def read_trackmate_csv(fn, framerate):
    """Do not call directly, wrapped into `read_trackmate`"""    
    def cb(da):
        return da[da.TRACK_ID!="None"]
    return read_arbitrary_csv(fn, col_traj="TRACK_ID", col_x="POSITION_X", col_y="POSITION_Y", col_frame="FRAME", framerate=framerate/1000., cb=cb)

def read_trackmate_xml(fn):
    """Do not call directly, wrapped into `read_trackmate`"""
    x=xmltodict.parse(open(fn, 'r').read())
    # Checks
    if x['Tracks']['@spaceUnits'] != 'micron':
        raise IOError("Spatial unit not recognized")
        
    # parameters
    framerate = float(x['Tracks']['@frameInterval'])
    traces = []
    
    for particle in x['Tracks']['particle']:  
        traces.append([(float(d['@x']), float(d['@y']), float(d['@t'])*framerate, float(d['@t'])) for d in particle['detection']])
    return traces

def read_trackmate(fn, format, framerate):
    if format == 'xml':
        return read_trackmate_xml(fn)
    elif format == 'csv':
        return read_trackmate_csv(fn, framerate)
    else:
        raise IOError("It doesn't work, dammit")
    
## ==== CSV file format
def init_csv():
    return {'name': 'CSV', 'info': "Comma-separated values text file", 'anchor': 'csv',
            'active': True, 'params': []}
def read_csv(fn):
    return read_arbitrary_csv(fn, col_traj="trajectory", col_x="x", col_y="y", col_frame="frame", col_t="t")
    
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

##
## ==== This are some helper functions
##

def traces_to_csv(traces):
    """Returns a CSV file with the format 
    trajectory,x,y,t,frame
    """
    csv = "trajectory,x,y,t,frame\n"
    for (tr_n, tr) in enumerate(traces):
        for pt in tr:
            csv +="{},{},{},{},{}\n".format(tr_n, pt[0],pt[1],pt[2],pt[3])
    return csv

def read_arbitrary_csv(fn, col_x="", col_y="", col_frame="", col_t="t",
                       col_traj="", framerate=None, pixelsize=None, cb=None,
                       sep=",", header='infer'):
    """This function takes the file name of a CSV file as input and parses it to
    the list of list format required by Spot-On. This function is called by various
    CSV importers and it is advised not to call it directly."""
    
    da = pd.read_csv(fn, sep=sep, header=header) # Read file
    
    # Check that all the columns are present:
    cols = da.columns
    if (not (col_traj in cols and col_x in cols and col_y in cols and col_frame in cols)) or (not (col_t in cols) and framerate==None):
        raise IOError("Missing columns in the file, or wrong header")
        
    # Correct units if needed
    if framerate != None:
        da[col_t]=da[col_frame]*framerate
    if pixelsize != None:
        da[col_x]*=pixelsize
        da[col_y]*=pixelsize
        
    # Apply potential callback
    if cb != None:
        da = cb(da)
        
    # Split by traj
    out = []
    for (idx,t) in da.sort_values(col_traj).groupby(col_traj):
        tr = [(tt[1][col_x], tt[1][col_y], tt[1][col_t], int(tt[1][col_frame])) for tt in t.sort_values(col_frame).iterrows()] # Order by trace, then by frame
        out.append(tr)
    
    return out

##
## ==== Inits
##
inits = [{'name': 'csv',       'init': init_csv, 'parser': read_csv},
         {'name': 'trackmate', 'init': init_trackmate, 'parser': read_trackmate},
         {'name': 'utrack',    'init': init_utrack, 'parser': read_utrack},
         {'name': 'mosaic',    'init': init_mosaic, 'parser': read_mosaic},
         {'name': 'evalspt',   'init': init_evalspt, 'parser': read_evalspt},
         {'name': 'anders',    'init': init_anders, 'parser': read_anders}]
initsDict = {i['name']: i for i in inits}
