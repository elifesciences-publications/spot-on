validateCAPTCHA = function() {
    var googleResponse = jQuery('#g-recaptcha-response').val();
    if (!googleResponse) {
	$('<p style="color:red !important" class=error-captcha"><span class="glyphicon glyphicon-remove " ></span> Please fill up the captcha.</p>" ').insertAfter("#recaptcha-response");
	return false;
    } else {            
	return true;
    }
}
