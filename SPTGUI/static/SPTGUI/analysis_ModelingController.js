angular.module('app')
    .controller('ModelingController', ['analysisService', 'getterService', '$scope', '$interval', '$q', function(analysisService, getterService, $scope, $interval, $q) {
	// This is the controller for the modeling tab

	// Scope variables
	$scope.analysisState = 'notrun';

	// Initiate the window with what we have
	getterService.getDatasets().then(function(dataResponse) {
	    $scope.datasets = dataResponse['data'];
	}); // Populate the scope with the already uploaded datasets
	getterService.getStatistics().then(function(dataResponse) {
	    $scope.statistics = dataResponse['data'];
	}); // Populate the scope with the already computed statistics
	$scope.$on('datasets:updated', function(event,data) {
	    $scope.datasets = data
	}); // Look for updated datasets
	
	//
	// ==== CRUD modeling parameters
	//

	// Should also contain the datasets to include
	$scope.modelingParameters = {bin_size : 10,
				     random : 3,
				     include : null // Populated later
				    };
	//
	// ==== Analysis computation logic
	//

	// Function that runs the analysis
	$scope.runAnalysis = function(parameters) {
	    // Show a progress bar (synced from messages from the broker)
	    $scope.modelingParameters.include = $scope.datasets.map(function(l){return l.id;})
	    $scope.jlhist = [{'x': 1,'y': 5}, 
			     {'x': 20,'y': 20}, 
			     {'x': 40,'y': 10}, 
			     {'x': 60,'y': 40}, 
			     {'x': 80,'y': 5},
			     {'x': 100,'y': parameters.random}];
	    $scope.$applyAsync();
	    analysisService.runAnalysis(parameters)   
	    $scope.analysisState='running'; // 'running' for progress bar
	}

	// A watcher that periodically checks the state of the computation
	processingWaiter = $interval(function() {
	    // This loops forever, but might become inactive
	    if ($scope.analysisState=='running') {
		pars = $scope.modelingParameters;
		analysisService.checkAnalysis(pars)
		    .then(function(dataResponse) {
			if (dataResponse['data'].allgood) {
			    //alert('getting fitted values');// Download the fitted values
			    $q.all(pars.include.map(function(data_id) {
				return analysisService.getFitted(data_id, pars);
			    })).then(function(l) {
				alert('all done!');
				$scope.analysisState = 'done'; // Hide progress bar
			    });
			}
		    });
	    }
	    return(true)
	}, 2000);

	// Debug function to check the analysis
	$scope.checkAnalysis = function(params) {
	    analysisService.checkAnalysis(params).then(
		function(dataResponse) {alert(dataResponse['data'])});
	}
    }]);
