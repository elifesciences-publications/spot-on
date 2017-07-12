## File implements the check for the test stuff
from django.apps import AppConfig
from django.core.checks import Error, register
import fastSPT.custom_settings as custom_settings
import logging
##
## ==== Startup checks
## (should ultimately be moved to another module)

class MyAppConfig(AppConfig):
    name = 'SPTGUI'
    verbose_name = "My Application"
    def ready(self):
        from SPTGUI.models import Analysis

        @register()
        def check_the_app(app_configs, **kwargs):
            errors = []
            errors = check_demo(errors)
            errors = check_captcha(errors)
            return errors

        def check_demo(errors):
            """Checks if the demo analysis has been provided. So far, it
            is not bound to anything, so this should be fixed 
            /!\ TODO MW: when use_demo==False, do not display the 'start with
            a demo dataset' option."""
            
            print "checking for demo Analysis"
            try:
                Analysis.objects.filter(editable=False) # Should be the demo entries
                check_failed = False
            except:
                if custom_settings.use_demo:
                    check_failed = True
                else:
                    check_failed = False
                    
            if check_failed:
                errors.append(
                    Error(
                        'Could not find any demo dataset',
                        hint='Make sure that you initialized Spot-On (demofiles.py)',
                        obj="",
                        id='SPTGUI.E001',
                    )
                )
            return errors

        def check_captcha(errors):
            """Display a warning message if the CAPTCHA validating string is not
            provided"""
            if not custom_settings.RECAPTCHA_USE:
                logging.warning("RECAPTCHA_USE is False in custome_settings.py, the reCAPTCHA will be ignored. Anyone can create an analysis and upload files to your server")
            return errors

