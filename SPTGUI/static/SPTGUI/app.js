/*global angular */
'use strict';

/**
 * The main app module
 * @name app
 * @type {angular.Module}
 */
var app = angular.module('app', ['flow', 'ngCookies'])
    .config(['flowFactoryProvider', function (flowFactoryProvider) {
	flowFactoryProvider.defaults = {
	    target: '/SPTGUI/upload/',
	    permanentErrors: [404, 500, 501],
	    maxChunkRetries: 1,
	    chunkRetryInterval: 5000,
	    simultaneousUploads: 4
	};
	flowFactoryProvider.on('catchAll', function (event) {
	    console.log('catchAll', arguments);
	});
	// Can be used with different implementations of Flow.js
	// flowFactoryProvider.factory = fustyFlowFactory;
    }])
    .config(function($httpProvider) {
	$httpProvider.defaults.xsrfCookieName = 'csrftoken';
	$httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    })
    .run(run);

run.$inject = ['$http'];

/**
* @name run
* @desc Update xsrf $http headers to align with Django's defaults
*/
function run($http) {
  $http.defaults.xsrfHeaderName = 'X-CSRFToken';
  $http.defaults.xsrfCookieName = 'csrftoken';
}
