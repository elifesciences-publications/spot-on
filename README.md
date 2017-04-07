fastSPT (provisional title)
--------------------------

# Installation
This software has been written for Python 2, but minimum work should be required to port it to Python 3. We recommend to install the dependencies of the software in a *virtual environment* (using the `virtualenv` and `virtualenvwrapper` tools).

This section assumes that the user has access to the [`pip`](https://pip.pypa.io/en/stable/installing/) utility.

## Setup the virtual environment
We first install a tool to manage Python's [virtual environements](https://virtualenvwrapper.readthedocs.io/en/latest/): [`virtualenvwrapper`](https://virtualenvwrapper.readthedocs.io/en/latest/) and create a virtualenv called **fastSPT**.

```{shell}
pip install virtualenvwrapper
export WORKON_HOME=~/.envs
mkdir -p $WORKON_HOME
source /usr/local/bin/virtualenvwrapper.sh ## or: source ~/.local/bin/virtualenvwrapper.sh
mkvirtualenv fastSPT
```

## Install dependencies
Some of the dependencies might already be installed on your system, or might be directly available through your operating system's package manager. It is possible to use those provided that they are recent enough. In particular, `numpy` and `scipy` are fairly standard librairies and come often preinstalled with your system.

You will also need the [`git` tool](https://git-scm.com/) to download the files.

```{shell}
sudo apt-get install rabbitmq-server
pip install Django
pip install numpy # Useless if already installed on your system, compilation might be long
pip install scipy # Useless if already installed on your system, compilation might be long
pip install lmfit celery fasteners
pip install django-angular
```

## Install the `fastspt` backend
```{shell}
wget http://www.eleves.ens.fr/home/woringer/fastspt-6.1.tar.gz
pip install fastspt-6.1.tar.gz
```

## Download and install the fastSPT repository

```{shell}
git clone https://padouppadoup@gitlab.com/padouppadoup/fastSPT.git
cd fastSPT
```

# Usage
## Start the service

```{bash}
export WORKON_HOME=~/.envs
source /usr/local/bin/virtualenvwrapper.sh ## or: source ~/.local/bin/virtualenvwrapper.sh
cd fastSPT/
tmux
workon fastSPT
python manage.py runserver
celery -A SPTGUI worker -l info # In a different terminal
```
