var center = [+37.8, -115.5];
var osmUrl = 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    osmAttrib = '&copy; <a href="http://openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    osm = L.tileLayer(osmUrl, {maxZoom: 18, attribution: osmAttrib});

hexmap = new L.Map('hexmap', {layers: [osm], center: new L.LatLng(center[0], center[1]), zoom: 6});
var options = {
    radius : 12,
    opacity: 0.6,
    duration: 200,
    lng: function(d){
        return d[0];
    },
    lat: function(d){
        return d[1];
    },
    value: function(d){
        return d.length;
    },
    valueFloor: 0,
    valueCeil: undefined
};

var hexLayer = L.hexbinLayer(options).addTo(hexmap)
hexLayer.colorScale().range(['lightblue','green', 'yellow','orange','red']);

var updateHexBin =  function (data){
    var hexData=[];
    for (var k in data){
        hexData.push([data[k].long,data[k].lat]);
    }
    if (hexData.length > 0) {
        hexLayer.data(hexData);
        hexmap.panTo(new L.LatLng((lat_high+lat_low)/2.0,(long_high+long_low)/2.0));
        //console.log(map.getZoom());
        hexmap.setZoom(map.getZoom());
    }
};