;(function(window) {

    // From https://thinkster.io/angular-tabs-directive
    angular.module('app', ['flow', 'ngCookies'])
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
    
	.service('getterService', ['$http', '$cookies', function($http) {
	    // This service handles $http requests to get the list fo the datasets
	    this.getDatasets = function(callback) {
		return $http.get('./api/datasets');
	    };

	    // Delete a dataset, provided its id (filename used for validation)
	    this.deleteDataset = function(database_id, filename) {
		return $http.post('./api/delete/', {'id': database_id,
						    'filename': filename});
	    }
	}])

    
	.controller('UploadController', ['getterService', '$scope', '$cookies', function(getterService, $scope, $cookies) {
	    // This is the controller for the upload part of the app

	    //
	    // ==== Let's first define some global variables (on the $scope).
	    //
	    $scope.currentlyUploading=false;
	    $scope.successfullyUploaded=0;
	    $scope.uploadStart = function($flow){
		$flow.opts.headers =  {'X-CSRFToken' : $cookies.get("csrftoken")};
	    }; // Populate $flow with the CSRF cookie!
	    getterService.getDatasets().then(function(dataResponse) {
		$scope.datasets = dataResponse['data'];
		$scope.successfullyUploaded=dataResponse['data'].length;
	    }); // Populate the scope with the already uploaded datasets

	    
	    //
	    // ==== Handle the edition of the list of files
	    //
	    $scope.deleteDataset = function(dataset) {
		alert("deleting stuff: "+ dataset.filename + " (id: " + dataset.id + ")");
		getterService.deleteDataset(dataset.id, dataset.filename)
		    .then(function(dataResponse) {
			getterService.getDatasets().then(function(dataResponse) {
			    $scope.datasets = dataResponse['data'];
			    $scope.successfullyUploaded=dataResponse['data'].length;
			}); // Update the datasets variable when deleting sth.
		    });
	    }
	    
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

