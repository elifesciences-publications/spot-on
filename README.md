Spot-On: model-based kinetic modeling of single-particle tracking experiments
-----------------------------------------------------------------------------

# Installation
This software has been written for Python 2, but minimum work should be required to port it to Python 3. We recommend to install the dependencies of the software in a *virtual environment* (using the `virtualenv` and `virtualenvwrapper` tools).

This section assumes that the user has access to the [`pip`](https://pip.pypa.io/en/stable/installing/) utility. Note that the pip version packaged with your distribution might be notably obsolete. In that case, pip has to be installed according to the instructions detailed in the link above.
Spot-On can be installed using `pip v.9.0` or any further version.
 
Finally, for the exports, Spot-On relies on the [Inkscape](https://inkscape.org) software to perform file conversions. 
 
## Setup the virtual environment
We first install a tool to manage Python's [virtual environements](https://virtualenvwrapper.readthedocs.io/en/latest/): [`virtualenvwrapper`](https://virtualenvwrapper.readthedocs.io/en/latest/) and create a virtualenv called **fastSPT**. This is only required if you want to work in a virtual environment (recommended).

```{shell}
pip install virtualenvwrapper
export WORKON_HOME=~/.envs
mkdir -p $WORKON_HOME
source /usr/local/bin/virtualenvwrapper.sh ## or: source ~/.local/bin/virtualenvwrapper.sh
mkvirtualenv fastSPT
```

## Install dependencies
Some of the dependencies might already be installed on your system, or might be directly available through your operating system's package manager. It is possible to use those provided that they are recent enough. In particular, `numpy` and `scipy` are fairly standard librairies and come often preinstalled with your system. Also, installing `Numpy` and `Scipy` require compilation tools (`build-essential`, `python-dev`).

You will also need the [`git` tool](https://git-scm.com/) to download the files. Under Ubuntu/Debian GNU/Linux flavours, it can be installed by typing:

```{shell}
sudo apt-get install python-dev libffi-dev libssl-dev ## Required to compile dependencies
sudo apt-get install gfortran libopenblas-dev liblapack-dev ## Required by Scipy
sudo apt-get install git inkscape 
sudo apt-get install redis-server
```

See this: http://docs.celeryproject.org/en/latest/userguide/configuration.html#conf-redis-result-backend 

## Download and install Spot-On

```{shell}
git clone https://gitlab.com/tjian-darzacq-lab/Spot-On.git
cd Spot-On
pip install pip -U # update to the last version of pip
pip install -r requirements.txt
make init ## This will download demo datasets and fitted (a,b) fitted values
```

# Usage
## Start the service

```{bash}
tmux
export WORKON_HOME=~/.envs
source /usr/local/bin/virtualenvwrapper.sh ## or: source ~/.local/bin/virtualenvwrapper.sh
cd Spot-On/
workon fastSPT
python manage.py runserver
celery -A SPTGUI worker -l INFO # In a different terminal
```

# Launching (some) tests

Open a Django shell: `python manage.py shell` and type the command: `import SPTGUI.statistics_tests as stats;stats.test_statistics()`. This should run the tests for the statistics on all the existing entries of the database.
