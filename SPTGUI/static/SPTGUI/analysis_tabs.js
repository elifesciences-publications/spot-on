angular.module('app')
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
    });
