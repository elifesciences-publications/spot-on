## Simple script to extract the (a,b) z-correction coefficients from
## the format saved by the fitting procedure

import os
import numpy as np

## Variables
path = "./SPTGUI/fit_zcorr/{}gaps/"
out = "170611_fitted_zcor.csv"

## List folder
xy_raw = []
for g in [0,1,2]:
    li = os.listdir(path.format(g))
    xy_raw += [(i, float(i.split('_')[2][2:]), float(i.split('_')[3][2:-4]), g) for i in li]
    print "Found {} files of fits in folder {}".format(len(li), path.format(g))
xy = [{"dT": i[1], "dZ": i[2], "fn": i[0], "gaps": i[3]} for i in xy_raw]


##
with open(out, "w") as f:
    f.write("dT,dZ,gaps,a,b\n")
    for l in xy:
        data = np.load(os.path.join(path.format(l['gaps']), l['fn']))
        f.write("{},{},{},{},{}\n".format(l['dT'], l['dZ'], l['gaps'],
                                       data['params'][0], data['params'][1]))
    print "Done!"
