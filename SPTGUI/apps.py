## File implements the check for the test stuff
from django.apps import AppConfig
from django.core.checks import Error, register
import fastSPT.custom_settings as custom_settings
##
## ==== Startup checks
## (should ultimately be moved to another module)

class MyAppConfig(AppConfig):
    name = 'SPTGUI'
    verbose_name = "My Application"
    def ready(self):
        from SPTGUI.models import Analysis

        @register()
        def example_check(app_configs, **kwargs):
            errors = []
            print "checking for demo Analysis"
            try:
                Analysis.objects.get(id=custom_settings.demo_id)
                check_failed = False
            except:
                check_failed = True
            if check_failed:
                errors.append(
                    Error(
                        'Could not find the demo dataset, id={}'.format(custom_settings.demo_id),
                        hint='Make sure that this value points to an existing analysis',
                        obj="",
                        id='myapp.E001',
                    )
                )
            return errors
