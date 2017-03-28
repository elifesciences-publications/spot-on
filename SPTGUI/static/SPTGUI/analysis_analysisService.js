angular.module('app')
    .service('getterService', ['$http', '$rootScope', function($http, $rootScope) {
	// This service handles $http requests to perform the analysis of a dataset

	this.runAnalysis = function(params) {
	    // Start the analysis for the specified datasets and
	    // specified parameters
	    return $http.post('./api/analyze/', params);
	}

	this.checkAnalysis = function(callback) {
	    // make a get here on './analyze/'. Return the result.
	    //This either contains the progress report or the result
	    return $http.get('./api/analyze/');
	}

	// Get empirical jump length distribution
	// ./analyze/1/jld
	// ./analyze/c/jld
	// ./analyze/1/fit <-- focus on this one

	// call runAnalysis
	// start periodical timer (not inside this service)
	// this timer updates the progress bar
	// update the graph when we have everything
