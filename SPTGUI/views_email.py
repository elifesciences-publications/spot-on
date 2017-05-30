
def email(request, token=None):
    """This function either add one email to the Email database (when called with
    "POST"), or confirm one address email (if called with a "GET" and if `token`
    is provided"""
    if request.method == "POST":
        # Check email address
        # Check for duplicate -> if already present but not acivated, resend email
        print "Adding email address"
        # Send confirmation email
    elif request.method == "POST" and token != None:
        print "Confirming email (in that case return a confirmation page)"
        # Send confirmation email
        

def email_unsubscribe(request, token):
    """This function removes one address email from the database, based on the 
    token"""
    return "You have been removed from the database"
