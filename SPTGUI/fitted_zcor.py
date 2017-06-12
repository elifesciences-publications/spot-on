# Getter to load precomputed fits.
# To do that in a nice way, we implement a KD-tree so that the
# algorithm returns the nearest neighbour in the (dZ, dT)
#
# By MW, GPLv3+, May 2017

## ==== Imports
import os
import numpy as np
from scipy.spatial import cKDTree as KDTree
import pandas as pd

## ==== Main functions
def init(paths, scale_t=1000.0):
    """Function that instanciates the KD-tree.
    Inspired from: http://stackoverflow.com/questions/28177114/merge-join-2-dataframes-by-complex-criteria/28186940#28186940

    Inputs:
    - paths (dict): keys are (int) corresponding to the number of gaps
                    values are (str) with the corresponding path
    - scale_t (float): the space-time ratio

    Returns:
    - a dict: kd_init, 
    """
    ret = {}
    # Parse the input directory
    for ngaps in paths:
        path = paths[ngaps]
        li = os.listdir(path)
        xy_raw = [(i, float(i.split('_')[2][2:])*scale_t, float(i.split('_')[3][2:-4])) for i in li]
        xy = pd.DataFrame([{"dT": i[1], "dZ": i[2], "fn": i[0]} for i in xy_raw])
        print "Found {} files of fits in folder {}".format(len(xy_raw), path)
    
        join_cols = ['dT', "dZ"]
        tree = KDTree(xy[join_cols])
        ret[ngaps] = {"tree": tree, "df": xy, "path": path, "scale_t": scale_t}
    return ret

def query_nearest(dT, dZ, ngaps, tree_init):
    """This function returns the nearest (dT,dZ) pair from the input dT, dZ. These
    parameters are to be used for the fitting of the jump length distribution. This
    allow to then load the (a,b) coefficients required for the z-depth correction.
    This method allows to always find the nearest value in a context where (a,b)
    coefficients have not be estimated on a regular grid."""
    # Deparse
    tree_init = tree_init[ngaps]
    tree = tree_init["tree"]
    df1 = tree_init["df"]
    path = tree_init["path"]
    df2 = pd.DataFrame([{"dT":dT*tree_init["scale_t"], "dZ":dZ}])
    join_cols = ["dT", "dZ"]
    
    # Query and merge
    distance, indices = tree.query(df2[join_cols])
    df1_near_2 = df1.take(indices).reset_index(drop=True)
    left = df1_near_2
    right = df2.rename(columns=lambda l: l + "_query")
    merged = pd.concat([left, right], axis=1)
    
    # Open dict
    fn = merged.fn[0]
    data = np.load(os.path.join(path, fn))
    params = [i for i in data["params"]]
    
    ret = {"dT_query": float(dT), "dZ_query": float(dZ), 
           "dT": merged["dT"][0]/tree_init["scale_t"], "dZ": merged["dZ"][0],
           "fn": fn, "ssq2": data["ssq2"], "params": params, "path": path}
    return ret
