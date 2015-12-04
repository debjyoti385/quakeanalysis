(function () {
    var extent, scale,
        classes = 9, scheme_id = "Greys",
        reverse = false;
    scheme = colorbrewer[scheme_id][classes],

        container = L.DomUtil.get('map'),
        map = L.map(container).setView([-43.6, 172.3], 10);

    L.tileLayer('http://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ, TomTom, Intermap, iPC, USGS and the GIS User Community',
        maxZoom: 17
    }).addTo(map);

    var areaSelect = L.areaSelect({width:750, height:450});
    areaSelect.on("change", function() {
        var bounds = this.getBounds();
        $("#result .swlat").val(bounds.getSouthWest().lat );
        $('#result .swlng').val(bounds.getSouthWest().lng);
        $("#result .nelat").val(bounds.getNorthEast().lat );
        $('#result .nelng').val(bounds.getNorthEast().lng);
    });
    areaSelect.addTo(map);
    
    d3.json(container.dataset.source, function(collection) {
        L.pointsLayer(collection, {
            radius: get_radius,
            applyStyle: circle_style
        }).addTo(map);

        var chart = timeseries_chart(scheme)
            .x(get_time).xLabel("Earthquake origin time")
            .y(get_magnitude).yLabel("Magnitude")
            .brushmove(on_brush);
        d3.select("body").datum(collection.features).call(chart);
    });

    function get_time(d) {
        return d3.time.format.iso.parse(d.properties.origintime);
    }

    function get_magnitude(d) {
        return +d.properties.magnitude;
    }

    function on_brush(brush) {
        var s = brush.extent();
        d3.selectAll(".circle").classed("selected", function (d) {
            var time = get_time(d);
            var mag = get_magnitude(d);
            return (s[0][0] <= time && time <= s[1][0]) && (s[0][1] <= mag && mag <= s[1][1]);
        });
    }

    function get_radius(d) {
        return d.properties.magnitude * d.properties.magnitude;
    }

    function circle_style(circles) {
        if (!(extent && scale)) {
            extent = d3.extent(circles.data(), function (d) { return d.properties.depth; });
            scale = d3.scale.log()
                .domain(reverse ? extent.reverse() : extent)
                .range(d3.range(classes));
        }
        circles.attr('opacity', function(d){
                return 0.5;
            })
            .attr('stroke', scheme[classes - 1])
            .attr('stroke-width', 1)
            .attr('fill', function (d) {
                return scheme[(scale(d.properties.depth) * 20).toFixed()];
            });

        circles.on('click', function (d, i) {
            L.DomEvent.stopPropagation(d3.event);

            var t = '<h3><%- id %></h3>' +
                '<ul>' +
                '<li>Magnitude: <%- mag %></li>' +
                '<li>Depth: <%- depth %>km</li>' +
                '</ul>';

            var data = {
                id: d.id,
                mag: d.properties.magnitude,
                depth: d.properties.depth
            };

            L.popup()
                .setLatLng([d.geometry.coordinates[1], d.geometry.coordinates[0]])
                .setContent(_.template(t, data))
                .openOn(map);

        });
    }

    function timeseries_chart(color) {
        var margin = { top: 5, right: 5, bottom: 40, left: 45 },
            width = 960 ,
            height = 135;

        var x = d3.time.scale(),
            y = d3.scale.linear(),
            x_label = "X", y_label = "Y",
            brush = d3.svg.brush().x(x).y(y).on("brush", _brushmove);

        var get_x = no_op,
            get_y = no_op;

        function timeseries(selection) {
            selection.each(function (d) {
                x.range([0, width]);
                y.range([height, 0]);

                var series = d3.select(this).append("svg").attr("id", "quake-timeseries")
                    .attr("width", width + margin.left + margin.right)
                    .attr("height", height + margin.top + margin.bottom)
                    .append("g").attr("id", "date-brush")
                    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

                var x_axis = series.append("g")
                    .attr("class", "x axis")
                    .attr("transform", "translate(0," + height + ")");

                var y_axis = series.append("g")
                    .attr("class", "y axis");

                x_axis.append("text")
                    .attr("class", "label")
                    .attr("x", width)
                    .attr("y", 30)
                    .style("text-anchor", "end")
                    .text(x_label);

                y_axis.append("text")
                    .attr("class", "label")
                    .attr("transform", "rotate(-90)")
                    .attr("y", -40)
                    .attr("dy", ".71em")
                    .style("text-anchor", "end")
                    .text(y_label);

                series.append("clipPath")
                    .attr("id", "clip")
                    .append("rect")
                    .attr("width", width - 1)
                    .attr("height", height - .25)
                    .attr("transform", "translate(1,0)");

                series.append("g")
                    .attr("class", "x brush")
                    .call(brush)
                    .selectAll("rect")
                    .attr("height", height)
                    .style("stroke-width", 1)
                    .style("stroke", color[color.length - 1])
                    .style("fill", color[2])
                    .attr("opacity", 0.4);

                x.domain(d3.extent(d, get_x));
                x_axis.call(d3.svg.axis().scale(x).orient("bottom"));

                y.domain(d3.extent(d, get_y));
                y_axis.call(d3.svg.axis().scale(y).orient("left"));

                series.append("g").attr("class", "timeseries")
                    .attr("clip-path", "url(#clip)")
                    .selectAll("circle")
                    .data(d).enter()
                    .append("circle")
                    //                        .style("stroke", color[color.length - 2])
                    .style("stroke", "HoneyDew")
                    .style("stroke-width", .5)
                    //                        .style("fill", color[color.length - 1])
                    .style("fill", "White")
                    .attr("opacity", .4)
                    .attr("r", 2)
                    .attr("transform", function (d) {
                        return "translate(" + x(get_x(d)) + "," + y(get_y(d)) + ")";
                    });
            });
        }

        timeseries.x = function (accessor) {
            if (!arguments.length) return get_x;
            get_x = accessor;
            return timeseries;
        };

        timeseries.y = function (accessor) {
            if (!arguments.length) return get_y;
            get_y = accessor;
            return timeseries;
        };

        timeseries.xLabel = function (label) {
            if (!arguments.length) return x_label;
            x_label = label;
            return timeseries;
        }

        timeseries.yLabel = function (label) {
            if (!arguments.length) return y_label;
            y_label = label;
            return timeseries;
        }

        timeseries.brushmove = function (cb) {
            if (!arguments.length) return brushmove;
            brushmove = cb;
            return timeseries;
        };

        function _brushmove() {
            brushmove.call(null, brush);
        }

        function no_op() {}

        return timeseries;
    }
}());
