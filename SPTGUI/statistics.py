# Statistics computed from a dataset or a pool of datasets, a submodule of
# A graphical user interface to the fastSPT tool by Anders S. Hansen, 2016
# By MW, GPLv3+, Feb.-Apr. 2017

import numpy as np
import logging, json

def number_of_trajectories(fi):
    """Returns the number of trajectories in a dataset"""
    return len(fi)

def number_of_trajectories3(fi):
    """Returns the number of trajectories of length >3"""
    return len([i for i in fi if len(i)>=3])

def number_of_jumps(fi):
    """Returns the total number of jumps"""
    return sum([len(i)-1 for i in fi if len(i)>1])

def number_of_frames(fi):
    """Returns the number of recorded frames as the maximum of the frame index"""
    l = 0
    for traj in fi:
        m = max([i[3] for i in traj])
        if m>l:
            l=m
    return l

def number_of_detections(fi):
    """Returns the number of detections in a dataset"""
    return sum([len(i) for i in fi])

def length_of_trajectories(fi):
    """Returns the mean and median length of trajectories in the units of
    number of translocations. This is not related to time."""
    l = np.array([len(i) for i in fi])
    return {"median": np.median(l), "mean": l.mean()}

def particles_per_frame(fi):
    """Returns the mean and median number of particles per frame"""
    ld = {}
    for traj in fi:
        for p in traj:
            if not p[3] in ld:
                ld[p[3]] = 1
            else:
                ld[p[3]] += 1
    l = np.zeros((max(ld.keys())))
    for i in ld.keys():
        l[i-1] = ld[i]
    return {"median": np.median(l), "mean": l.mean()}

def jump_length(fi):
    """Computes mean and median jump length"""
    logging.warning("This is poorly optimized (jump length function in statistics.py")
    def dist(x0, y0, x1, y1):
        return ((x0-x1)**2+(y0-y1)**2)**0.5
    l = []
    for traj in [i for i in fi if len(i)>1]:
        for i in range(1,len(traj)):
            l.append(dist(traj[i-1][0], traj[i-1][1], traj[i][0], traj[i][1]))
    l = np.asarray(l)
    return {"median": np.median(l), "mean": l.mean()}

def global_mean_median(da, fu):
    """A function to compute global stuff.
    It first loads all the datasets, then send it to the corresponding function"""
    AllData = []
    for d in da:
        with open(d.parsed.path, 'r') as f:
            AllData += json.load(f)
    return fu(AllData)
            