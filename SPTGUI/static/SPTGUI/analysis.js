;(function(window) {

    // From https://thinkster.io/angular-tabs-directive
    angular.module('app', ['flow'])
    
	.service('getterService', function($http) {
	    // This service handles $http requests to get the list fo the datasets
	    this.getDatasets = function(callback) {
		return $http.get('./api/datasets');
	    }
	})

    
	.controller('UploadController', ['$scope', 'getterService', function($scope, getterService) {
	    // This is the controller for the upload part of the app

	    //
	    // ==== Let's first define some global variables (on the $scope).
	    //
	    $scope.currentlyUploading=false;
	    $scope.successfullyUploaded=0;
	    getterService.getDatasets().then(function(dataResponse) {
		$scope.datasets = dataResponse['data'];
		$scope.successfullyUploaded=dataResponse['data'].length;
	    });// Populate the scope with the already uploaded datasets
	    
	    //
	    // ==== Upload (ng-flow) events
	    //
	    // (1) Fired when a file is added to the download list
	    $scope.$on('flow::fileAdded', function (event, $flow, flowFile) {
		$scope.currentlyUploading=true;
		// Start the watcher if it has not been started before.
	    });

	    // (2) Fired when all downloads are complete
	    $scope.$on('flow::complete', function (event, $flow, flowFile) {
		$scope.currentlyUploading=false;
	    });

	    // (3) Fired when one download completes
	    $scope.$on('flow::fileSuccess', function (file, message, chunk) {
		//$scope.successfullyUploaded=$scope.successfullyUploaded+1;
		getterService.getDatasets().then(function(dataResponse) {
		    $scope.datasets = dataResponse['data'];
		    $scope.successfullyUploaded=dataResponse['data'].length;
		});
		// Call the API object
	    });

	}])
    
	.directive('tab', function() {
	    // Simple logic to create a <tab> directive in angular/bootstrap
	    return {
		restrict: 'E',
		transclude: true,
		template: '<div role="tabpanel" ng-show="active" ng-transclude></div>',
		require: '^tabset',
		scope: {
		    heading: '@'
		},
		link: function(scope, elem, attr, tabsetCtrl) {
		    scope.active = false
		    tabsetCtrl.addTab(scope)
		}
	    }
	})    
	.directive('tabset', function() {
	    // A tabset is a group of tabs.
	    return {
		restrict: 'E',
		transclude: true,
		scope: { },
		templateUrl: '/static/SPTGUI/tabset.html',
		bindToController: true,
		controllerAs: 'tabset',
		controller: function() {
		    var self = this
		    self.tabs = []
		    self.addTab = function addTab(tab) {
			self.tabs.push(tab)
			
			if(self.tabs.length === 1) {
			    tab.active = true
			}
		    }
		    self.select = function(selectedTab) {
			angular.forEach(self.tabs, function(tab) {
			    if(tab.active && tab !== selectedTab) {
				tab.active = false;
			    }
			})
			
			selectedTab.active = true;
		    }
		}
	    }
	})
    
})(window);

