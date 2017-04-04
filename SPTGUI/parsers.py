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
def read_file(fn):
    """A wrapper for all the parsers. To be run sequencially. 
    To be effective, the parser should raise an exception if it 
    cannot deal with the file"""

    ## Sanity checks
    if not os.path.isfile(fn):
        raise IOError("File not found: {}".format(fn))

    da = read_anders(fn)

    return da
    

## ==== Anders' file format
def read_anders(fn):
    """The file format sent by Anders. I don't really know where it 
    comes from"""
    
    ## Sanity checks
    if not os.path.isfile(fn):
        raise IOError("File not found: {}".format(fn))

    try:
        mat = scipy.io.loadmat(fn)
        m=np.asarray(mat['trackedPar'])
    except:
        raise IOError("The file does not seem to be a .mat file ({})".format(fn))

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
            
    
    ## And create the format.
    
