angular.module('app')
    .service('analysisService', ['$http', '$rootScope', function($http, $rootScope) {
	// This service handles $http requests to perform the analysis of a dataset
	function encodeQueryData(data) { // From http://stackoverflow.com/questions/111529/how-to-create-query-parameters-in-javascript
	    let ret = [];
	    for (let d in data)
		ret.push(encodeURIComponent(d) + '=' + encodeURIComponent(data[d]));
	    return ret.join('&');}

	this.runAnalysis = function(paramsJLD, paramsFit) {
	    // Start the analysis for the specified datasets and
	    // specified parameters
	    paramsJLD.hashvalueJLD = 'null';	    
	    paramsJLD.hashvalueJLD = encodeQueryData(paramsJLD);
	    paramsFit.hashvalue = 'null';
	    paramsFit.hashvalue = encodeQueryData(paramsFit);
	    return $http.post('./api/analyze/', [paramsJLD, paramsFit]);
	}

	this.checkAnalysis = function(paramsJLD, paramsFit) {
	    //This either contains the progress report or the result
	    paramsJLD.hashvalueJLD = 'null';	    
	    paramsJLD.hashvalueJLD = encodeQueryData(paramsJLD);
	    paramsFit.hashvalue = 'null';
	    paramsFit.hashvalue = encodeQueryData(paramsFit);
	    return $http.get('./api/analyze/?' + encodeQueryData(Object.assign({}, paramsJLD, paramsFit)));
	}

	this.getFitted = function(data_id, paramsJLD, paramsFit) {
	    //This either contains the progress report or the result
	    paramsJLD.hashvalueJLD = 'null';	    
	    paramsJLD.hashvalueJLD = encodeQueryData(paramsJLD);
	    paramsFit.hashvalue = 'null';
	    paramsFit.hashvalue = encodeQueryData(paramsFit);
	    return $http.get('./api/analyze/'+data_id+'?'+encodeQueryData( Object.assign({}, paramsJLD, paramsFit)));
	}

	this.getPooledFitted = function(paramsJLD, paramsFit) {
	    //This either contains the progress report or the result
	    paramsJLD = angular.copy(paramsJLD)
	    paramsJLD.hashvalueJLD = 'null';	    
	    paramsJLD.hashvalueJLD = encodeQueryData(paramsJLD);
	    paramsFit = angular.copy(paramsFit)
	    paramsFit.hashvalue = 'null';
	    paramsFit.hashvalue = encodeQueryData(paramsFit);
	    //console.log('./api/analyze/pooled?'+encodeQueryData( Object.assign({}, paramsJLD, paramsFit)))
	    return $http.get('./api/analyze/pooled?'+encodeQueryData( Object.assign({}, paramsJLD, paramsFit)));
	}
	
	// Function to query the pooled histogram
	this.getPooledJLD = function(paramsJLD, include) {
	    //This either contains the progress report or the result
	    params = angular.copy(paramsJLD)
	    params.hashvalueJLD ='null'
	    params.include = include
	    params.hashvalueJLD = encodeQueryData(params)
	    return $http.get('./api/jld/pooled?'+encodeQueryData(params));
	}

	// Functions to compute a custom JLD (with custom modeling parameters)
	this.setNonDefaultJLD = function(params) {
	    params = angular.copy(params)
	    params.hashvalueJLD ='null'
	    params.hashvalueJLD = encodeQueryData(params)	    
	    return $http.post('./api/jld/', params);
	}
	this.getNonDefaultJLD = function(params) {
	    params = angular.copy(params)
	    params.hashvalueJLD ='null'
	    params.hashvalueJLD = encodeQueryData(params)	    
	    return $http.get('./api/jld/?'+encodeQueryData(params));
	}
	
	// Get some statistics on the uploaded and preprocessed datasets
	this.getDefaultJLD = function(dataset_id) {
	    return $http.get('./api/jld_default/'+dataset_id);
	};

    }]);
