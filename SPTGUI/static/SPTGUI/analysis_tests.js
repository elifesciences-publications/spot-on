describe("Modeling Controller", function() {
    beforeEach(module('app'));
    var $controller;
    var $scope, CreateTarget, $rootScope, getterService, MainSocket;

    beforeEach(function() {
        inject(function($injector) {
            $rootScope = $injector.get('$rootScope');
            $scope = $rootScope.$new();
            var $controller = $injector.get('$controller');
	    getterService = $injector.get('getterService');
	    MainSocket = $injector.get('MainSocket');
	    MainSocket.ws.onopen = function() {
		$rootScope.$broadcast('socket:ready');
		done()}
	    
            CreateTarget = function() {
                $controller('ModelingController', {$scope: $scope});
            }
        });
    })

    
    it("is an initialization test", function() {
	var controller = CreateTarget();
	$scope.datasets = [] // Should load something here
	$scope.initView()
	expect($scope.analysisState).toEqual('notrun');
    });
});

describe("A spec", function() {
    it("is just a function, so it can contain any code", function() {
        var foo = 0;
        foo += 1;
        expect(foo).toEqual(1);
    });
 
    it("can have more than one expectation", function () {
        var foo = 0;
        foo += 1;
 
        expect(foo).toEqual(1);
        expect(true).toEqual(true);
    });
});
