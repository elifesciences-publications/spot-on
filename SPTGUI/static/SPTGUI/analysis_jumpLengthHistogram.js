angular.module('app')
    .directive('jumpLengthHistogram', function() {
	function fmt_data(dat) {
	    data = [];
	    data.push({date: 0, close: 0});
	    for (i=1; i<dat[0].length; i++) {
		data.push({date: dat[0][i-1], close: dat[1][i]});
		data.push({date: dat[0][i], close: dat[1][i]});
	    }
	    return data;
	};
	function link(scope, el, attr){
	    // Get input and parse it
	    dt = scope.data[1];
	    data = fmt_data([scope.data[0][0], scope.data[0][1][dt]]);
	    
	    var svg = d3.select(el[0]).append('svg')
	    margin = {top: 20, right: 20, bottom: 30, left: 50},
	    width = 600;
	    height = 400;
	    
	    svg.attr("width", width).attr("height", height);
	    width = width - margin.left - margin.right; //+svg.attr("width")
	    height = height - margin.top - margin.bottom; // +svg.attr("height")
	    g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	    var x = d3.scaleLinear().rangeRound([0, width]);
	    var y = d3.scaleLinear().rangeRound([height, 0]);

	    var area = d3.area()
		.x(function(d) { return x(d.date); })
		.y1(function(d) { return y(d.close); })
		.y0(function(d) {return y(0);});

	    x.domain([0, d3.max(data, function(d) { return d.date; })]);
	    y.domain([0, 1.1*d3.max(data, function(d) { return d.close; })]);

	    g.append("path")
		.datum(data)
		.attr("fill", "steelblue")
		.attr("d", area);

	    g.append("g")
		.attr("transform", "translate(0," + height + ")")
		.call(d3.axisBottom(x));

	    g.append("g")
		.call(d3.axisLeft(y))
		.append("text")
		.attr("fill", "#000")
		.attr("transform", "rotate(-90)")
		.attr("y", 6)
		.attr("dy", "0.71em")
		.attr("text-anchor", "end")
		.text("P(r)");

	    scope.$watch('data', function(data){ // Angular connexion
		if(!data){ return; }
		dt = data[1];
		if (!dt) {return;}
		if (dt<data[0][1].length && dt>0) {
		    data = fmt_data([data[0][0], data[0][1][dt]]);
		    g.selectAll("path")
			.datum(data)
			.attr("fill", "steelblue")
			.attr("d", area);
		    
		}
		else {
		    g.selectAll("path").attr("fill", "transparent");
		}
	    });
	    
	    
	}
	return {
	    link: link,
	    restrict: 'E',
	    scope: {data: '='}
	};
    })
	    
    .directive('jumpLengthHistogram2', function() {
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
