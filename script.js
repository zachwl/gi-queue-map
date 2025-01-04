// Global variable for county-level data
let cachedGeoJSON;

// Create the leaflet map
// Centered on a point in Kansas
const map = L.map('map').setView([38, -95], 5);

// Use the Esri light gray basemap
// This provides a subtle background that works well with the data
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
	attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
	maxZoom: 16,
}).addTo(map);


// Function to load data from a GeoJSON and add it to the map
// Accepts a GeoJSON object and a symbology function
// Includes functionality to create a pie chart in the pop-up
function loadMap(data, symbology) {
    L.geoJSON(data, {
        style: symbology,
        onEachFeature: function (feature, layer) {
            // Extract data for the pop-up panel with pie chart
            const countyName = feature.properties.join_key;
            const totalMW = feature.properties.total_capacity;
            const solarMW = feature.properties.total_solar;
            const ssMW = feature.properties.total_hybrid;
            const windMW = feature.properties.total_wind;
            const storageMW = feature.properties.total_storage;
            const gasMW = feature.properties.total_natural_gas;
            const otherMW = feature.properties.total_other;
            const rtoCount = feature.properties.rto_count;

            // Only counties with at least 1 project will have a pop-up
            if (totalMW > 0 && totalMW !== null) {
                // Pie chart gets id from join_key
                const canvasId = `county-pie-chart-${feature.properties.join_key.replace(/\s+/g, '-')}`;

                // Create the pop-up content
                const popupContent = `
                    <h3>${countyName}</h3>
                    <p>Total queued energy: ${totalMW.toFixed(1)} MW</p>
                    <canvas id="${canvasId}" width="250" height="250"></canvas>
                `;

                layer.bindPopup(popupContent);

                // Event listener for popupopen
                layer.on('popupopen', function() {
                    const pieData = {
                        labels: [],
                        datasets: [{
                            data: [],
                            backgroundColor: []
                        }]
                    };

                    // Create data labels for pie chart
                    // Assign values taken from geoJSON file and give colors
                    const energySources = [
                        { label: `Solar: ${solarMW.toFixed(1)} MW`, value: solarMW, color: '#FFD700' },
                        { label: `Hybrid: ${ssMW.toFixed(1)} MW`, value: ssMW, color: '#FFAA00' },
                        { label: `Wind: ${windMW.toFixed(1)} MW`, value: windMW, color: '#00BFFF' },
                        { label: `Storage: ${storageMW.toFixed(1)} MW`, value: storageMW, color: '#32CD32' },
                        { label: `Gas: ${gasMW.toFixed(1)} MW`, value: gasMW, color: '#FF6347' },
                        { label: `Other: ${otherMW.toFixed(1)} MW`, value: otherMW, color: '#B0C4DE' }
                    ];
                    
                    // Ensure that labels are only added when that fuel type is present in the county
                    // Otherwise, it crowds up the panel and makes everything less readable
                    energySources.forEach(source => {
                        if (source.value > 0) {
                            pieData.labels.push(source.label);
                            pieData.datasets[0].data.push(source.value);
                            pieData.datasets[0].backgroundColor.push(source.color);
                        }
                    });

                    // Create pie chart
                    const ctx = document.getElementById(canvasId).getContext('2d');
                    new Chart(ctx, {
                        type: 'pie',
                        data: pieData,
                        options: {
                            responsive: true,
                            plugins: {
                                legend: {
                                    position: 'top',
                                },
                                tooltip: {
                                    callbacks: {
                                        label: function(tooltipItem) {
                                            // Calculate percentage of that fuel type is to total queued generation
                                            return ' ' + (tooltipItem.raw / totalMW * 100).toFixed(1) + '%';
                                        }
                                    }
                                }
                            }
                        }
                    });
                });
            }
        }
    }).addTo(map);
}

// Function to clear all loaded layers from the map 
// Designed to be called when the user clicks on a button to change the symbology
function clearMap(map) {
    map.eachLayer(function(layer) {
        if (layer instanceof L.GeoJSON) {
            map.removeLayer(layer);
        }
    });
}

// This function acts as a "holding container" for the other symbology functions
// Otherwise, it would be be possible to pass arguments to the symbology functions
// Therefore each of the symbology functions can call this one to set the arugments
function setStyleFuelTotal(feature, fuelType, thresholds, colors) {
    const MW_val = feature.properties[fuelType];

    // This style object contains the default symbology that will be changed by the below code
    const style = {
        color: 'gray',
        weight: 1,
        fillColor: 'gray',
        fillOpacity: 0.6
    };

    // If there is no queued generation, make the feature transparent
    // Makes it easier to focus on counties that do have data
    if (MW_val === 0 || MW_val === null) {
        style.fillOpacity = 0;
        return style;
    }

    // Each defined symbology will have color values and MW thresholds
    // These form a graduated symbology
    for (let i = 0; i < thresholds.length; i++) {
        if (MW_val > thresholds[i]) {
            style.fillColor = colors[i];
            break;
        }
    }

    return style;
}

// The below functions are used to set the symbology in different circumstances
// By calling the setStyleFuelTotal function with the appropriate arguments, these functions can be inserted into the loadMap function

const solarSymbology = function(feature) {
    return setStyleFuelTotal(feature = feature, fuelType = 'total_solar',
        thresholds = [2000, 750, 300, 100, 0],
        colors = ['#993404', '#d95f0e', '#fe9929', '#fed98e', '#ffffd4']);
}
const windSymbology = function(feature) {
    return setStyleFuelTotal(feature = feature, fuelType = 'total_wind',
        thresholds = [750, 500, 200, 50, 0],
        colors = ['#08306b', '#2979b9', '#73b2d8', '#c8dcf0', '#f7fbff']);
}
const ngSymbology = function(feature) {
    return setStyleFuelTotal(feature = feature, fuelType = 'total_natural_gas',
        thresholds = [750, 500, 200, 50, 0],
        colors = ['#67000d', '#d32020', '#fb7050', '#fcbea5', '#fff5f0']);
}
const storageSymbology = function(feature) {
    return setStyleFuelTotal(feature = feature, fuelType = 'total_storage',
        thresholds = [750, 500, 200, 50, 0],
        colors = ['#00441b', '#1d8641', '#55b567', '#9ed798', '#d5efcf']);
}
const hybridSymbology = function(feature) {
    return setStyleFuelTotal(feature = feature, fuelType = 'total_hybrid',
        thresholds = [2000, 750, 300, 100, 0],
        colors = ['#993404', '#d95f0e', '#fe9929', '#fed98e', '#ffffd4']);
}
const otherSymbology = function(feature) {
    return setStyleFuelTotal(feature = feature, fuelType = 'total_other',
        thresholds = [200, 80, 50, 20, 0],
        colors = ['#050505', '#363636', '#676767', '#989898', '#c9c9c9']);
}
const totalGenSymbology = function(feature) {
    return setStyleFuelTotal(feature = feature, fuelType = 'total_capacity',
        thresholds = [2000, 1200, 750, 500, 200, 50, 0],
        colors = ['#810f7c', '#863e99', '#896bb1', '#8c96c6', '#a6bbd9', '#c6dbeb', '#edf8fb']);
}

// This symbology function colors the counties by the dominant fuel type
// Therefore, it does not need to call the setStyleFuelTotal function
// Instead, it uses the data from the feature it is being applied to
// It finds which fuel has highest percentage of total queued generation
function setStyleLeadingFuel(feature){
    const style = {
        color: 'gray',
        weight: 1,
        fillColor: 'gray',
        fillOpacity: 0.6
    };
    // Extract amount of total queued generation
    const totalMW = feature.properties.total_capacity;

    // If the county has no queued generation, then make it transparent
    if (totalMW === 0 || totalMW === null) {
        style.fillOpacity = 0;
        return style;
    }

    // If the feature has some queued generation, then it will grab the other feature properties
    const solarMW = feature.properties.total_solar;
    const ssMW = feature.properties.total_hybrid;
    const windMW = feature.properties.total_wind;
    const storageMW = feature.properties.total_storage;
    const gasMW = feature.properties.total_natural_gas;
    const otherMW = feature.properties.total_other;
    const rto_count = feature.properties.rto_count;

    //Calculate dominant fuel type
    const leading_fuel = Math.max(solarMW, ssMW, windMW, storageMW, gasMW, otherMW);

    //Assign color based on fuel type
    if (solarMW === leading_fuel){
        style.fillColor = '#FFD700';
    }
    if (ssMW === leading_fuel){
        style.fillColor = '#FF8C00';
    }
    if (windMW === leading_fuel){
        style.fillColor = '#1E90FF'
    }
    if (storageMW === leading_fuel){
        style.fillColor = '#006400'
    }
    if (gasMW === leading_fuel){
        style.fillColor = '#8B0000';
    } 
    if (otherMW === leading_fuel){
        style.fillColor = '#7A7A7A';
    }

    // If there's overlap between 2 or more ISOs/utilities in the county, 
    // give the feature a thick black line
    // In the main.py script, the aggregated county data is sorted by rto county before export
    // This way, when the geojson loads with the dark lines, they display prominently
    // In the future, this will be used to create its own layer to show overlap
    if (rto_count >= 2) {
        style.color = '#000000';
        style.weight = 3.5;
    }
    return style;
}

// Access the button elements in order to add event listeners
const solarButton = document.getElementById('solarButton');
const windButton = document.getElementById('windButton');
const storageButton = document.getElementById('storageButton');
const ngButton = document.getElementById('ngButton');
const hybridButton = document.getElementById('hybridButton');
const otherButton = document.getElementById('otherButton');
const totalGenButton = document.getElementById('totalGenButton');
const fuelButton = document.getElementById('fuelButton');

// Add event listeners to the buttons
// When the buttons are clicked, the script will reload the aggregated county data with a different symbology
solarButton.addEventListener('click', function() {
    clearMap(map);
    loadMap(cachedGeoJSON, solarSymbology);
});
windButton.addEventListener('click', function() {
    clearMap(map);
    loadMap(cachedGeoJSON, windSymbology);
});
ngButton.addEventListener('click', function() {
    clearMap(map);
    loadMap(cachedGeoJSON, ngSymbology);
});
storageButton.addEventListener('click', function() {
    clearMap(map);
    loadMap(cachedGeoJSON, storageSymbology);
});
hybridButton.addEventListener('click', function() {
    clearMap(map);
    loadMap(cachedGeoJSON, hybridSymbology);
});
otherButton.addEventListener('click', function() {
    clearMap(map);
    loadMap(cachedGeoJSON, otherSymbology);
});
totalGenButton.addEventListener('click', function() {
    clearMap(map);
    loadMap(cachedGeoJSON, totalGenSymbology);
});
fuelButton.addEventListener('click', function() {
    clearMap(map);
    loadMap(cachedGeoJSON, setStyleLeadingFuel);
});

// Load aggregated county data onto map
// By default, the map loads in with the total_capacity data 
// The user can then change this by clicking on the buttons
fetch('data/agg_county_data.geojson')
    .then(response => response.json())
    .then(data => {
        cachedGeoJSON = data;
        loadMap(data, totalGenSymbology);
    })
    .catch(error => console.error('Error loading GeoJSON data:', error));
