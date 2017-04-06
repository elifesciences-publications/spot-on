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
	function fmt_fit(x,y) {
	    data = [];
	    for (i=0; i<x.length; i++) {
		data.push({x: x[i], y: y[i]});
	    }
	    return data;	    
	};
	function link(scope, el, attr){
	    // Get input and parse it
	    dt = scope.data[2];
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
	    
	    var line = d3.line()
		.x(function(d) { return x(d.x); })
		.y(function(d) { return y(d.y); });

	    x.domain([0, d3.max(data, function(d) { return d.date; })]);
	    y.domain([0, 1.1*d3.max(data, function(d) { return d.close; })]);

	    bars = g.append("g");
	    fitline = g.append("g");
	    fitline.append("path");
	    bars.append("path")
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

	    scope.$watch('data', function(dat){ // Angular connexion
		if(!dat){ return; }
		dt = dat[2];
		if (!dt) {return;}
		if (dt<dat[0][1].length && dt>0) {
		    data = fmt_data([dat[0][0], dat[0][1][dt]]);
		    bars.selectAll("path")
			.datum(data)
			.attr("fill", "steelblue")
			.attr("d", area);
		    
		}
		else {
		    bars.selectAll("path").attr("fill", "transparent");
		}
		if (dat[1]) { // Add the line graph of the fit
		    fit = dat[1].fit;
		    fitline.selectAll("path")
		    	.datum(fmt_fit(fit.x, fit.y[dt]))
			.attr("fill", "none")
			.attr("stroke", "red")
			.attr("stroke-width", 1.5)
			.attr("d", line);
		} else { // Erase the line
		    fitline.selectAll("path")
		    .attr("stroke", "transparent")
		}
	    }); 
	}
	return {
	    link: link,
	    restrict: 'E',
	    scope: {data: '='}
	};
	})
	    

