// NOTE: $cookies might not be required everywhere...

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
    
	.service('getterService', ['$http', '$rootScope', function($http, $rootScope) {
	    // This service handles $http requests to get the list for the datasets
	    this.getDatasets = function(callback) {
		return $http.get('./api/datasets/');
	    };

	    // Get some statistics on the uploaded and preprocessed datasets
	    this.getStatistics = function(callback) {
		return $http.get('./statistics/');
	    };	    

	    // Delete a dataset, provided its id (filename used for validation)
	    this.deleteDataset = function(database_id, filename) {
		return $http.post('./api/delete/',
				  {'id': database_id,
				   'filename': filename});
	    };

	    this.updateDataset = function(database_id, dataset) {
		return $http.post('./api/edit/',
				  {'id': database_id,
				   'dataset': dataset});
	    };

	    this.getPreprocessing = function(callback) {
		return $http.get('./api/preprocessing/');
	    };
	    
	    this.broadcastDataset = function(datasets) {
		// Broadcast a message that a dataset has been edited
		$rootScope.$broadcast('datasets:updated',datasets);
	    };
	    
	}])
	.controller('UploadController', ['getterService', '$scope', '$cookies', '$interval', function(getterService, $scope, $cookies, $interval) {
	    // This is the controller for the upload part of the app

	    //
	    // ==== Let's first define some global variables (on the $scope).
	    //
	    $scope.currentlyUploading=false;
	    $scope.successfullyUploaded=0;
	    $scope.editingDataset=false;
	    $scope.editedDataset=null;
	    $scope.poolPreprocessing=false;
	    $scope.random = 0; // DEBUG
	    //$scope.statistics = null;
	    
	    $scope.uploadStart = function($flow){
		$flow.opts.headers =  {'X-CSRFToken' : $cookies.get("csrftoken")};
	    }; // Populate $flow with the CSRF cookie!
	    getterService.getDatasets().then(function(dataResponse) {
		$scope.datasets = dataResponse['data'];
		$scope.successfullyUploaded=dataResponse['data'].length;
	    }); // Populate the scope with the already uploaded datasets
	    getterService.getStatistics().then(function(dataResponse) {
		$scope.statistics = dataResponse['data'];
	    }); // Populate the scope with the already computed statistics

	    $scope.showingStatistics=false;
	    $scope.shownStatistics=null;
	    
	    
	    //
	    // ==== Handle the edition of the list of files
	    //
	    $scope.deleteDataset = function(dataset) {
		getterService.deleteDataset(dataset.id, dataset.filename)
		    .then(function(dataResponse) {
			getterService.getDatasets().then(function(dataResponse) {
			    $scope.datasets = dataResponse['data'];
			    $scope.successfullyUploaded=dataResponse['data'].length;
			}); // Update the datasets variable when deleting sth.
			getterService.getStatistics().then(function(dataResponse) {
			    $scope.statistics = dataResponse['data'];
			}); // Populate the scope with the already computed statistics
			getterService.broadcastDataset($scope.datasets);
		    });
		if ($scope.showStatistics == dataset) {
		    $scope.shownStatistics = null;
		    $scope.showingStatistics = false;   
		}
	    }

	    $scope.editDataset = function(dataset) {
		$scope.editingDataset=true;
		$scope.editedDataset=angular.copy(dataset);
	    };

	    $scope.cancelEdit = function(dataset) {
		$scope.editedDataset = null;
		$scope.editingDataset= false;
	    };

	    $scope.saveEdit = function(dataset) {
		$scope.datasets  =_.map($scope.datasets, function(el) {
		    return (el.id===dataset.id) ? dataset : el;
		});
		// Finish by sending the updated entry to the server
		getterService.updateDataset(dataset.id, dataset)
		    .then(getterService.broadcastDataset($scope.datasets));

		$scope.cancelEdit(dataset); // End edition
	    }

	    //
	    // ==== Logic of the statistics display
	    //
	    $scope.showDataset = function(dataset) {
		$scope.shownStatistics = dataset;
		$scope.showingStatistics = true;
	    };
	    
	    //
	    // ==== Upload (ng-flow) events
	    //
	    // (1) Fired when a file is added to the download list
	    $scope.$on('flow::fileAdded', function (event, $flow, flowFile) {
		$scope.currentlyUploading=true;
	    });

	    // (2) Fired when all downloads are complete
	    $scope.$on('flow::complete', function (event, $flow, flowFile) {
		$scope.currentlyUploading=false;
	    });

	    // (3) Fired when one download completes
	    $scope.$on('flow::fileSuccess', function (file, message, chunk) {
		getterService.getDatasets().then(function(dataResponse) {
		    $scope.datasets = dataResponse['data'];
		    $scope.successfullyUploaded=dataResponse['data'].length;
		    $scope.poolPreprocessing = true; // start the watcher.
		});
		getterService.getStatistics().then(function(dataResponse) {
		    $scope.statistics = dataResponse['data'];
		}); // Populate the scope with the already computed statistics
	    });

	    //
	    // ==== Server-side processing after the upload
	    //
	    $scope.preprocessingStartStop = function() {
		// A DEBUG function
		$scope.poolPreprocessing = !$scope.poolPreprocessing;
	    }
	    preprocessingWaiter = $interval(function() {
		// This loops forever, but might become inactive
		if ($scope.poolPreprocessing) {
		    getterService.getPreprocessing().then(function(dataResponse) {
			$scope.random = dataResponse['data'];
			// Deprecated code (that works)
			// $scope.datasets = _.map($scope.datasets, function(el) {
			//     // This is just to update the preprocessing status
			//     for (i in dataResponse['data']) {
			// 	da = dataResponse['data'][i]
			// 	if (el.id == da.id) {
			// 	    el.preanalysis_status = da.state;
			// 	}
			//     }
			//     return el;
			// });
			getterService.getDatasets().then(function(dataResponse) {
			    $scope.datasets = dataResponse['data'];
			    $scope.successfullyUploaded=dataResponse['data'].length;
			}); // Populate the scope with the already uploaded datasets
			getterService.getStatistics().then(function(dataResponse) {
			    $scope.statistics = dataResponse['data'];
			}); // Populate the scope with the already computed statistics
			// Check if all the dataset is "ok", if yes, switch the flag
			if (_.every(dataResponse['data'], function(el) {return el.state==='ok'})) {
			    $scope.poolPreprocessing = false;
			}
		    });
		}
		return(true)
	    }, 2000);

	}])
    	.controller('ModelingController', ['getterService', '$scope', '$interval', function(getterService, $scope, $interval) {
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
					};
	    //$scope.saveParameters = function(modelingParameters) {
	    //$scope.modelingParameters = scope.modelingParameters
	    //};

	    //
	    // ==== Analysis computation logic
	    //

	    // Function that runs the analysis
	    $scope.runAnalysis = function(parameters) {
		// Send the POST command to the server
		// Show a progress bar (synced from messages from the broker)
		// Display a graph
		$scope.jlhist = [{'x': 1,'y': 5}, 
				 {'x': 20,'y': 20}, 
				 {'x': 40,'y': 10}, 
				 {'x': 60,'y': 40}, 
				 {'x': 80,'y': 5},
				 {'x': 100,'y': parameters.random}];
		$scope.$applyAsync();
		$scope.analysisState='done'; // 'running' for progress bar
	    }
	}])

	.directive('jumpLengthHistogram', function() {
	    function link(scope, el, attr){
		var lineData = scope.data;

		var vis = d3.select(el[0]).append('svg');

		WIDTH = 300
		HEIGHT = 300
		vis.attr({width: WIDTH, height: HEIGHT});
		
		MARGINS = {top: 20, right: 20, bottom: 20, left: 50}
		xRange = d3.scale.linear().range([MARGINS.left,
						  WIDTH - MARGINS.right]
						).domain([
						    d3.min(lineData, function (d) {return d.x;}),
						    d3.max(lineData, function (d) {return d.x;})]);

		yRange = d3.scale.linear().range([HEIGHT - MARGINS.top,
						  MARGINS.bottom]
						).domain([
						    d3.min(lineData, function (d) {return d.y;}),
						    d3.max(lineData, function (d) {return d.y;})]);
		xAxis = d3.svg.axis().scale(xRange).tickSize(5).tickSubdivide(true);
		yAxis = d3.svg.axis().scale(yRange).tickSize(5).orient("left").tickSubdivide(true);


		vis.append("svg:g")
		    .attr("class", "x axis")
		    .attr("transform", "translate(0," + (HEIGHT - MARGINS.bottom) + ")")
		    .call(xAxis);

		vis.append("svg:g")
		    .attr("class", "y axis")
		    .attr("transform", "translate(" + (MARGINS.left) + ",0)")
		    .call(yAxis);

		var lineFunc = d3.svg.line()
		    .x(function (d) {
			return xRange(d.x);
		    })
		    .y(function (d) {
			return yRange(d.y);
		    })
		    .interpolate('basis');
		
		vis.append("svg:path")
		    .attr("d", lineFunc(lineData))
		    .attr("stroke", "blue")
		    .attr("stroke-width", 2)
		    .attr("fill", "none");
	    
		scope.$watch('data', function(lineData){
		    if(!lineData){ return; }
		    vis.selectAll("path")
			.attr("d", lineFunc(lineData))
			.attr("fill", "none");
		});
		    
    // var color = d3.scale.category10();
    // var width = 200;
    // var height = 200;
    // var min = Math.min(width, height);
    // var svg = d3.select(el[0]).append('svg');
    // var pie = d3.layout.pie().sort(null);
    // var arc = d3.svg.arc()
    //   .outerRadius(min / 2 * 0.9)
    //   .innerRadius(min / 2 * 0.5);

    // svg.attr({width: width, height: height});

    // // center the donut chart
    // var g = svg.append('g')
    //   .attr('transform', 'translate(' + width / 2 + ',' + height / 2 + ')');
    
    // // add the <path>s for each arc slice
    // var arcs = g.selectAll('path');

    // scope.$watch('data', function(data){
    //   if(!data){ return; }
    //   arcs = arcs.data(pie(data));
    //   arcs.exit().remove();
    //   arcs.enter().append('path')
    //     .style('stroke', 'white')
    //     .attr('fill', function(d, i){ return color(i) });
    //   // update all the arcs (not just the ones that might have been added)
    //   arcs.attr('d', arc);
    // }, true);
  }
  return {
    link: link,
    restrict: 'E',
    scope: { data: '=' }
  };
	})

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
	.directive('tooltip', function(){
	    // To display tooltips :)
	    return {
		restrict: 'A',
		link: function(scope, element, attrs){
		    $(element).hover(function(){
			// on mouseenter
			$(element).tooltip('show');
		    }, function(){
			// on mouseleave
			$(element).tooltip('hide');
		    });
		}
	    };
	});
    
})(window);

