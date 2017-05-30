;(function(window) {
    // From https://thinkster.io/angular-tabs-directive
    app = angular.module('app', ['ngCookies'])
	.config(['$httpProvider', function($httpProvider) {
	    // Play nicely with the CSRF cookie. Here we set the CSRF cookie
	    // to the cookie sent by Django
	    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
	    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
	}]) 
	.run(['$http', '$cookies', function($http, $cookies) {
	    // CSRF cookie initialization
	    // And here we properly populate it (cannot be done before)
	    $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;
	}])   
})(window);

angular.module('app')
    .controller('EmailController', ['$scope', '$http', function($scope, $http) {
	console.log("hehe")
	// This is the controller for the "Subscribe to the newsletter part
	$scope.email = ""
	$scope.message = null;
	$scope.subscribe = function(email) {
	    // The function that does the POST
	    console.log('submitting')
	    $scope.message =  null;
	    $http.post('./email/subscribe/',{'email': email}).then(function(resp) {
		alert("Got response")
	    })
	    
	}
    }]);


validateCAPTCHA = function() {
    var googleResponse = jQuery('#g-recaptcha-response').val();
    if (!googleResponse) {
	$('<p style="color:red !important" class=error-captcha"><span class="glyphicon glyphicon-remove " ></span> Please fill up the captcha.</p>" ').insertAfter("#recaptcha-response");
	return false;
    } else {            
	return true;
    }
}
