## Simple script to extract the (a,b) z-correction coefficients from
## the format saved by the fitting procedure

import os
import numpy as np

## Variables
path = "./SPTGUI/fit_zcorr/"
out = "170530_fitted_zcor.csv"

## List folder
li = os.listdir(path)
xy_raw = [(i, float(i.split('_')[2][2:]), float(i.split('_')[3][2:-4])) for i in li]
xy = [{"dT": i[1], "dZ": i[2], "fn": i[0]} for i in xy_raw]
print "Found {} files of fits in folder {}".format(len(xy_raw), path)

##
with open(out, "w") as f:
    f.write("dT, dZ, a, b\n")
    for l in xy:
        data = np.load(os.path.join(path, l['fn']))
        f.write("{},{},{},{}\n".format(l['dT'], l['dZ'],
                                       data['params'][0], data['params'][1]))
    print "Done!"
    
