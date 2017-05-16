# Index of views for the fastSPT-GUI app (sockets side)
# A graphical user interface to the fastSPT tool by Anders S. Hansen, 2016
# By MW, GPLv3+, Feb.-Apr. 2017
#
# Here we store views that are routes for the second tab (corresponding to the
# ModelingController in Angular.

# === Imports
import fitted_zcor

# ==== Initialization
path = "./SPTGUI/fit_zcorr/"
tree_init = fitted_zcor.init(path=path)

# ==== Functions (called from socket)
def get_fitted_zcor(message, data, url_basename):
    """Wrapper function to collect the object containing the filename of
    the nearest pair of (a,b) coefficients required to estimate the z correction
    to fit the jump length distribution"""
    return fitted_zcor.query_nearest(data['dT'], data['dZ'], tree_init)
