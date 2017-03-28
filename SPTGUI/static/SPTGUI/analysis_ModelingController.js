angular.module('app')
    .controller('ModelingController', ['analysisService', 'getterService', '$scope', '$interval', function(analysisService, getterService, $scope, $interval) {
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
	    // Send the POST command to the server
	    // Show a progress bar (synced from messages from the broker)
	    // Display a graph
	    $scope.modelingParameters.include = $scope.datasets.map(function(l){return true;})
	    $scope.jlhist = [{'x': 1,'y': 5}, 
			     {'x': 20,'y': 20}, 
			     {'x': 40,'y': 10}, 
			     {'x': 60,'y': 40}, 
			     {'x': 80,'y': 5},
			     {'x': 100,'y': parameters.random}];
	    $scope.$applyAsync();
	    analysisService.runAnalysis(parameters).then(
		function(dataResponse) {alert(dataResponse['data'])});	    
	    $scope.analysisState='done'; // 'running' for progress bar
	}

	// Debug function to check the analysis
	$scope.checkAnalysis = function(params) {
	    analysisService.checkAnalysis(params).then(
		function(dataResponse) {alert(dataResponse['data'])});
	}
    }]);
