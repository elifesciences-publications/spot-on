// NOTE: $cookies might not be required everywhere...

;(function(window) {

    // From https://thinkster.io/angular-tabs-directive
    angular.module('app', ['flow', 'ngCookies', 'toggle-switch', 'ui.bootstrap', 'rzModule'])
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

