angular.module('app')
    .service('analysisService', ['$http', '$rootScope', function($http, $rootScope) {
	// This service handles $http requests to perform the analysis of a dataset
	function encodeQueryData(data) { // From http://stackoverflow.com/questions/111529/how-to-create-query-parameters-in-javascript
	    let ret = [];
	    for (let d in data)
		ret.push(encodeURIComponent(d) + '=' + encodeURIComponent(data[d]));
	    return ret.join('&');}

	this.runAnalysis = function(params) {
	    // Start the analysis for the specified datasets and
	    // specified parameters
	    params.hashvalue='null'	    
	    params.hashvalue = encodeQueryData(params)
	    return $http.post('./api/analyze/', params);
	}

	this.checkAnalysis = function(params) {
	    // make a get here on './analyze/'. Return the result.
	    //This either contains the progress report or the result
	    params.hashvalue='null'
	    params.hashvalue = encodeQueryData(params)
	    return $http.get('./api/analyze/?' + encodeQueryData(params));
	}

	// Get empirical jump length distribution
	// ./analyze/1/jld
	// ./analyze/c/jld
	// ./analyze/1/fit <-- focus on this one

	// call runAnalysis
	// start periodical timer (not inside this service)
	// this timer updates the progress bar
	// update the graph when we have everything
    }]);
