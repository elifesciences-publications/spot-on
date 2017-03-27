fastSPT (provisional title)
--------------------------

# Installation
Requirements include `celery`, `django`, `python`.

# Usage
## Start the service

```{bash}
cd thesis/9_SPT/fastSPT/
python manage.py runserver
celery -A SPTGUI worker -l info # In a different terminal
```
