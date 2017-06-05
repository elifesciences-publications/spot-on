// A module to display a few visualizations in the docs.
;(function(window) {
    // From https://thinkster.io/angular-tabs-directive
    angular.module('app', ['rzModule'])
})(window);

angular.module('app')
    .directive('jumpLengthDistribution', function() {
	function distrib(x, D, sigma, dt) {
	    return x.map(function(xx) {return xx/(2*(dt*D+sigma*sigma))*Math.exp(-1*xx*xx/(4*(dt*D+sigma*sigma)))
				      })
	}
	function link(scope, el, attr) {
	    // Prepare the SVG canvas
	    var svg = d3.select(el[0]).append('svg')
	    margin = {top: 20, right: 20, bottom: 50, left: 30},
 	    width = 600;
 	    height = 300;	    
 	    svg.attr("width", width).attr("height", height);
	    width = width - margin.left - margin.right;
	    height = height - margin.top - margin.bottom;

	    var g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");
	    
	    scope.$watch('data', function(dat){
		console.log("hi");
		// Compute stuff
		D1 = dat.D1 // 5
		D2 = dat.D2 // .1
		P = dat.P // 0.5
		dt = dat.dt/1000 // 0.01
		sigma = dat.S/1000 //35/1000.0

		x_range = [0, 3] // µm
		X = d3.range(x_range[0], x_range[1], x_range[1]/300)
		Y1 = distrib(X, D1, sigma, dt)
		XY1 = X.map(function(xx, i) {return {x: xx, y:P*Y1[i]}})
		Y2 = distrib(X, D2, sigma, dt)
		XY2 = X.map(function(xx, i) {return {x: xx, y:(1-P)*Y2[i]}})
		XY12 = X.map(function(xx, i) {return {x: xx, y:P*Y1[i]+(1-P)*Y2[i]}})

		// Clean plot
		g.selectAll("g").remove()
		
		// Prepare plot
		var x = d3.scaleLinear().rangeRound([0, width]);
		var y = d3.scaleLinear().rangeRound([height, 0]);
 		x.domain(x_range);
 		y.domain([0, d3.max(XY12.map(function(xy, i){
		    return Math.max(XY1[i].y, XY2[i].y, XY12[i].y)}))]);
		var lines = g.append("g");
		var Aaxis = g.append("g")
		var line = d3.line()
 	    	    .curve(d3.curveBasis)
 		    .x(function(d) { return x(d.x); })
 		    .y(function(d) { return y(d.y); });
		
		// DRAW!!!
		lines.append("path")
	    	    .datum(XY12)
 	    	    .attr("fill", "none")
 	    	    .attr("stroke", "orange")
 	    	    .attr("stroke-width", 4)
 	    	    .attr("d", line)
		lines.append("path")
		    .datum(XY1)
 		    .attr("fill", "none")
 		    .attr("stroke", "red")
 		    .attr("stroke-width", 2.5)
 		    .attr("d", line)
		lines.append("path")
	    	    .datum(XY2)
 	    	    .attr("fill", "none")
 	    	    .attr("stroke", "blue")
 	    	    .attr("stroke-width", 2.5)
 	    	    .attr("d", line)

		// Some legends
		Aaxis.append("g")
		    .attr("transform", "translate(0," + height + ")")
		    .call(d3.axisBottom(x))
		    .append("text")
		    .attr("fill", "#000")
		.attr("transform", "translate("+width/2+","+ "30" +")")
		    .attr("text-anchor", "middle")
		    .text("jump distance (µm)")	    

		Aaxis.append("g")
	    	    .call(d3.axisLeft(y))
	    	    .append("text")
	    	    .attr("fill", "#000")
	    	//.attr("transform", "rotate(-90)")
	    	//.attr("y", 6)
	    	    .attr("dy", "-1em")
	    	    .attr("text-anchor", "end")
	    	    .text("P(r)");
	    
		p1 = [18, 36, 36+18]
		co = ['red', 'blue', 'orange']
		na = ["D1="+D1+" µm²/s", "D2="+D2+" µm²/s", "Two components"]
		for (var i=0;i<p1.length;i++) {
		    Aaxis.append("rect")
			.attr("x", width - 18)
			.attr("y", p1[i])
			.attr("width", 14)
		    .attr("height", 14)
			.style("fill", co[i]);
		    Aaxis.append("text")
			.attr("x", width - 24)
			.attr("y", p1[i])
			.attr("dy", ".75em")
			.style("text-anchor", "end")
			.text(na[i]);
		}
	    }, true)
	}
	return {
	    link: link,
	    restrict: 'E',
	    scope: {data: '='}
	};
    })
