
// Create a new date from a string, return as a timestamp.
function timestamp(str){
    return new Date(str).getTime();
}

var dateSlider = document.getElementById('date-slider');

noUiSlider.create(dateSlider, {
// Create two timestamps to define a range.
    range: {
        min: timestamp('1990'),
        max: timestamp('2016')
    },

// Steps of one week
    step: 365 * 24 * 60 * 60 * 1000,

// Two more timestamps indicate the handle starting positions.
    start: [ timestamp('2011'), timestamp('2015') ],

// No decimals
    format: wNumb({
        decimals: 0
    }),
    connect: true
});

// Create a list of day and monthnames.
var
    weekdays = [
        "Sunday", "Monday", "Tuesday",
        "Wednesday", "Thursday", "Friday",
        "Saturday"
    ],
    months = [
        "January", "February", "March",
        "April", "May", "June", "July",
        "August", "September", "October",
        "November", "December"
    ];

// Append a suffix to dates.
// Example: 23 => 23rd, 1 => 1st.
function nth (d) {
    if(d>3 && d<21) return 'th';
    switch (d % 10) {
        case 1:  return "st";
        case 2:  return "nd";
        case 3:  return "rd";
        default: return "th";
    }
}

// Create a string representation of the date.
function formatDate ( date ) {
    return weekdays[date.getDay()] + ", " +
        date.getDate() + nth(date.getDate()) + " " +
        months[date.getMonth()] + " " +
        date.getFullYear();
}

var dateValues = [
    document.getElementById('event-start'),
    document.getElementById('event-end')
];

dateSlider.noUiSlider.on('update', function( values, handle ) {
    dateValues[handle].innerHTML = (new Date(+values[handle])).getUTCFullYear();
});

var slider = document.getElementById('magnitude_slider');

noUiSlider.create(slider, {
    start: [ 3, 8 ], // Handle start position
    step: 0.1, // Slider moves in increments of '10'
    margin: 0.3, // Handles must be more than '20' apart
    connect: true, // Display a colored bar between the handles
    direction: 'rtl', // Put '0' at the bottom of the slider
    behaviour: 'tap-drag', // Move handle on tap, bar is draggable
    range: { // Slider can select '0' to '100'
        'min': 1,
        'max': 10
    },
    tooltips: [  wNumb({ decimals: 1 }), wNumb({ decimals: 1 }) ],
    pips: { // Show a scale with the slider
        mode: 'count',
        values: 10,
        density: 1
    }
});

$('#update').click(function(){
    scale_low = slider.noUiSlider.get()[0];
    scale_high = slider.noUiSlider.get()[1];
    date_start = new Date(dateSlider.noUiSlider.get()[0] * 1);
    date_end = new Date(dateSlider.noUiSlider.get()[1] * 1);

    lat_low = parseFloat($("#result .swlat").val());
    lat_high = parseFloat($("#result .nelat").val());
    long_low = parseFloat($("#result .swlng").val());
    long_high = parseFloat($("#result .nelng").val());

    var _lat_low, _lat_high, _long_low, _long_high;
    if (lat_low < 0 )
        _lat_low = "\\" + lat_low;
    else
        _lat_low =  lat_low;
    if (lat_high < 0 )
        _lat_high = "\\" + lat_high;
    else
        _lat_high =  lat_high;
    if (long_low < 0 )
        _long_low = "\\" + long_low;
    else
        _long_low =  long_low;
    if (long_high < 0 )
        _long_high = "\\" + long_high;
    else
        _long_high =  long_high;


    url = EVENT_SERVER + 'cube/quake_events/facts?cut=scale:'+ scale_low + '-' + scale_high + '|year:' + date_start.getUTCFullYear() +"-" + date_end.getUTCFullYear()  +'|lat:'+ _lat_low + '-' + _lat_high +'|long:'+ _long_low + '-'+ _long_high ;
    //alert(url);
    refresh(url);
});



$('#contour').click(function(){
    //alert ( SPARK_SERVER + "get_image/" + $("#event_list").val() );
    imageURL=SPARK_SERVER + "get_image/"$("#event_list").val();
    window.open(imageURL,"_blank");
});
