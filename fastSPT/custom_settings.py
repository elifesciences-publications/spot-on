## ==== Custom settings for Spot-On ====
## By MW, AGPLv3+, Jul. 2017
##
## Here go all the custom parameters to run Spot-On
## This file includes passwords (for emails for instance)
## and thus SHOULD NOT BE SHARED
## See the documentation for a thorough description of
## of each option.


## (1) ==== Whether to use the demonstration files. ====
##     To use demonstration files, you need to have an analysis
##     uploaded in the database that is marked with the
##     editable=False flag. Spot-On will always use the latest uploaded
##     demo analysis. The previously uploaded demo analysis will not be
##     deleted, but will not loaded by default anymore.
use_demo = False

## (2) ==== Protect Spot-On by reCAPTCHA ====
##     /!\ Note that reCAPTCHA is a Google service, by activating it, you
##     - Allow Google to monitor your traffic (who accesses your website)
##     - Help Google to improve its artificial intelligence program, by
##       forcing users to provide free labor to Google, which is a form of
##       modern slavery
##     If you don't care about that and/or just want to activate it, see below.
RECAPTCHA_USE = False ## Set to True to check for CAPTCHA.
RECAPTCHA_PUBLIC = "" ## Provided by Google reCAPTCAH interface
RECAPTCHA_SECRET = "" ## Provided by Google reCAPTCAH interface
## https://www.google.com/recaptcha/admin (to administrate them)

## (3) ==== Email settings ====
##     These email settings are required for the email functionalities
##     to work, namely the contact form and the newsletter subscription.
##     Apart from that, they are not required and you can leave them blank
##     in the first place.
##     -> See the documentation for more explanation.
URL_BASENAME = '' # URL here
ADMIN_NAME = 'the Spot-On team' # Name to be displayed when sending emails.
ADMIN_EMAIL = '' # Admin email (cc'ed in contacts)
EMAIL_USE = True
EMAIL_USE_TLS = True
EMAIL_HOST = '' # The host where the SMTP server lies
EMAIL_PORT = 587
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_CC_LIST = [] # emails to CC when an email is sent from the contact form.

## (4) ==== Default parameters to compute the jump length distribution
##     See the documentation for the signification of those.
##     Note that if you misform those parameters, Spot-On may crash without
##     being very verbos. Be careful!
compute_params = {'BinWidth' : 0.01,
                  'GapsAllowed' : None,
                  'TimePoints' : 8,
                  'JumpsToConsider' : 4,
                  'MaxJump' : 3}

## (5) ==== Whether to activate the direct upload API ====
##     This setting allows a third-party program to directly upload datasets
##     to Spot-On, without going through the web page. This is useful to directly
##     transfer files from a detection/tracking software to perform analysis,
##     thus streamlining the global analysis pipeline.
##     On the other hand, this allows a potential malicious user to upload
##     arbitrary files to your website. Nonetheless, these files will be
##     automatically deleted if they are not tracking files.
UPLOADAPI_ENABLE = False
UPLOADAPI_ENABLE_NEWANALYSIS = False
UPLOADAPI_ENABLE_EXISTINGANALYSIS = False
