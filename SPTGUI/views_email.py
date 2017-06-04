# Email handling submodule, as a part of Spot-On
# By MW, GPLv3+, May 2017

## ==== Imports
import json, random
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import HttpResponse
from .models import Email
from django.utils import timezone
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, redirect

##
## ==== Views
##
def email(request, token=None):
    """This function either add one email to the Email database (when called with
    "POST"), or confirm one address email (if called with a "GET" and if `token`
    is provided"""
    if request.method == "POST":
        body = json.loads(request.body)
        email = body['email']
        print "Validating : {}".format(email)
        try:
            validate_email(email) # Check email address
        except ValidationError as e:
            return HttpResponse(json.dumps({'status': 'error',
                                            'message': 'Invalid email address'}),
                                content_type='application/json', status=400)
        else:
            em = Email.objects.filter(email=email)
            if len(em)==1: ## Email already present
                em_entry = em[0]
                validated = em_entry.validated
                if validated: ## Send a membership reminder
                    send_confirmation_email(email, em_entry.token, reminder=True)
                else: ## Resend confirmation email
                    send_confirmation_email(email, em_entry.token, reminder=False)
            else: # Send confirmation email
                token = make_token()
                em = Email(email=email, add_date=timezone.now(), token=token)
                em.save()
                send_confirmation_email(email, token, reminder=False)
            
            return HttpResponse(json.dumps({'status': 'success',
                                            'message': 'A confirmation email has been sent to you. If you had already subscribed to the newsletter, a reminder has been sent to you.'}),
                                content_type='application/json')
    elif request.method == "GET" and token != None:
        print "Confirming email (in that case return a confirmation page)"
        # Send confirmation email
        em = get_object_or_404(Email, token=token)
        em.validated = True
        em.save()
        return HttpResponse('Your address email {} has been validated. Go to the <a href="{}">Spot-On homepage</a>.'.format(em.email, reverse('SPTGUI:index'))) ## TODO: Use a template here...

def email_unsubscribe(request, token):
    """This function removes one address email from the database, based on the 
    token"""
    em = get_object_or_404(Email, token=token)
    email = em.email
    em.remove()
    return HttpResponse('Your address email {} has been removed from our database. Go to the <a href="{}">Spot-On homepage</a>.'.format(email, reverse('SPTGUI:index')))

def contactform(request):
    """Handles the logic of the contact form. A very gross system with little
    checks. In particular, note that no CAPTCHA is implemented and that a copy
    of the message is sent to the specified email address, which is potentially
    a source of spam. Be careful."""
    if request.method=="POST":
        email = request.POST['email']
        subject = request.POST['subject']
        message = request.POST['message']

        ## Validate email address
        print "Validating : {}".format(email)
        try:
            validate_email(email) # Check email address
        except ValidationError as e:
            return HttpResponse(json.dumps({'status': 'error',
                                            'message': 'Invalid email address'}),
                                content_type='application/json', status=400)

        ## Send email
        send_message(email, subject, message)

        ## Return
        # Should return a nice JSON /!\ TODO MW: Angularify this.
        return HttpResponse('Your message has been sent to the Spot-On team. We will answer you as soon as possible. Go to the <a href="{}">Spot-On homepage</a>.'.format(reverse('SPTGUI:index')))
    else:
        return redirect('SPTGUI:staticpage', 'contact') 

##
## ==== Helper functions
##
def send_confirmation_email(email, token, bp='http://127.0.0.1:8000',
                            reminder=False):
    """Sends an email confirming that the email has been added to the newsletter"""
                        
    print "sending confirmation"
    msg1 = """Hello,\n\n"""
    msg2_rem = """This is a reminder that you are registered to the Spot-On ({}) mailing
list and that your email address has been validated.

In case you might want to UNSUBSCRIBE, you can click the link below:

{}

"""

    msg2_no = """Somebody (likely you) registered this email address to the Spot-On ({})
newsletter. To confirm this registration please click on the link
below. 

{}

If you didn't subscribe to the newsletter, you can safely ignore this
message."""
    
    msg3 = """This is an automated message, but you can reply to this message.

Regards,
The Spot-On team
--

PS: You can always unsubscribe by clicking this link: {}"""

    if reminder:
        msg = msg1 + msg2_rem + msg3
        link = bp+reverse('SPTGUI:email_unsubscribe', args=[token])
    else:
        msg = msg1 + msg2_no + msg3
        link = bp+reverse('SPTGUI:email_confirm', args=[token])

    send_mail(
        'Subscription to the Spot-On newsletter',
        msg.format(bp+'/SPTGUI',
                   link,
                   bp+reverse('SPTGUI:email_unsubscribe', args=[token]),
               ),
        'the Spot-On Team <spot-on@gmx.us>',
        [email],
        fail_silently=False,
    )
    print "done"

def send_message(cc, subject, message):
    """Helper function to send a message to the Spot-On team"""
    msg = """Hi\n\nThe following message was submitted to the Spot-On contact form:\n\n============================================\n{}\n============================================\n\n -- The Spot-On team."""
    send_mail(
        '[Spot-On contact form] {}'.format(subject),
        msg.format(message),
        'the Spot-On Team <spot-on@gmx.us>',
        [cc, 'spot-on@gmx.us'],
        fail_silently=False,
    )
    print "done"    
    
def make_token(n=30):
    """Returns an hexadecimal number"""
    return '%030x' % random.randrange(16**n)
