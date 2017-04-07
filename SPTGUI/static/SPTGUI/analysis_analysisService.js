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
	    //This either contains the progress report or the result
	    params.hashvalue='null'
	    params.hashvalue = encodeQueryData(params)
	    return $http.get('./api/analyze/?' + encodeQueryData(params));
	}

	this.getFitted = function(data_id, params) {
	    //This either contains the progress report or the result
	    params.hashvalue='null'
	    params.hashvalue = encodeQueryData(params)
	    return $http.get('./api/analyze/'+data_id+'?'+encodeQueryData(params));
	}

	this.getPooledFitted = function(params) {
	    //This either contains the progress report or the result
	    params.hashvalue='null'
	    params.hashvalue = encodeQueryData(params)
	    return $http.get('./api/analyze/pooled?'+encodeQueryData(params));
	}
	

	// Function to query the pooled histogram
	this.getPooledJLD = function(params) {
	    //This either contains the progress report or the result
	    params.hashvalue='null'
	    params.hashvalue = encodeQueryData(params)
	    return $http.get('./api/jld/pooled?'+encodeQueryData(params));
	}

    }]);
