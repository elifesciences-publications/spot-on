angular.module('app')
    .directive('jumpLengthHistogram', function() {
	function link(scope, el, attr){
	    var lineData = scope.data;

	    var vis = d3.select(el[0]).append('svg');

	    WIDTH = 300
	    HEIGHT = 300
	    MARGINS = {top: 20, right: 20, bottom: 20, left: 50}
	    vis.attr({width: WIDTH, height: HEIGHT});

	    xRange = d3.scale.linear()
		.range([MARGINS.left, WIDTH - MARGINS.right])
		.domain([d3.min(lineData, function (d) {return d.x;}),
			 d3.max(lineData, function (d) {return d.x;})]);

	    yRange = d3.scale.linear()
		.range([HEIGHT - MARGINS.top, MARGINS.bottom])
		.domain([d3.min(lineData, function (d) {return d.y;}),
			 d3.max(lineData, function (d) {return d.y;})]);
	    xAxis =  d3.svg.axis().scale(xRange)
		.tickSize(5).tickSubdivide(true);
	    yAxis = d3.svg.axis().scale(yRange)
		.tickSize(5).orient("left").tickSubdivide(true);

	    vis.append("svg:g")
		.attr("class", "x axis")
		.attr("transform", "translate(0,"+(HEIGHT-MARGINS.bottom)+")")
		.call(xAxis);

	    vis.append("svg:g")
		.attr("class", "y axis")
		.attr("transform", "translate(" + (MARGINS.left) + ",0)")
		.call(yAxis);

	    var lineFunc = d3.svg.line()
		.x(function (d) {return xRange(d.x);})
		.y(function (d) {return yRange(d.y);})
		.interpolate('basis');
	    
	    vis.append("svg:path")
		.attr("d", lineFunc(lineData))
		.attr("stroke", "blue").attr("stroke-width", 2)
		.attr("fill", "none");
	    
	    scope.$watch('data', function(lineData){ // Angular connexion
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
	    scope: {data: '='}
	};
    })
