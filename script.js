// Create the map and set the view to a specific location and zoom level
const map = L.map('map').setView([38, -95], 5); // Centered on the USA

/*
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
}).addTo(map);
*/
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
	attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
	maxZoom: 16,
}).addTo(map);

function setStyleLeadingFuel2(feature){
    const style = {
        color: 'gray',
        weight: 1,
        fillColor: 'gray',
        fillOpacity: 0.6
    };
    const totalMW = feature.properties.total_capacity;

    if (totalMW === 0 || totalMW === null) {
        style.fillOpacity = 0;
        return style;
    }

    const solarMW = feature.properties.total_solar;
    const ssMW = feature.properties.total_hybrid;
    const windMW = feature.properties.total_wind;
    const storageMW = feature.properties.total_storage;
    const gasMW = feature.properties.total_natural_gas;
    const otherMW = feature.properties.total_other;
    const rto_count = feature.properties.rto_count;

    const leading_fuel = Math.max(solarMW, ssMW, windMW, storageMW, gasMW, otherMW);

    if (solarMW === leading_fuel){
        style.fillColor = '#FFD700';  // Dark Yellow for high percentage
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
        style.fillColor = '#7A7A7A';  // Dark Gray for high percentage
    }
    if (rto_count >= 2) {
        style.color = '#000000';
        style.weight = 3.5;
    }
    return style;
}

/*
function setStyleLeadingFuel2(feature){
    const totalMW = feature.properties.total_capacity;
    const solarMW = feature.properties.total_solar;
    const ssMW = feature.properties.total_hybrid;
    const windMW = feature.properties.total_wind;
    const storageMW = feature.properties.total_storage;
    const gasMW = feature.properties.total_natural_gas;
    const otherMW = feature.properties.total_other;
    const rto_count = feature.properties.rto_count;

    if (totalMW > 0 && totalMW !== null) {

        let fillColor;
        let opacity = 0.6;
        let lineColor = 'gray';
        let lineWeight = 1;

        const leading_fuel = Math.max(solarMW, ssMW, windMW, storageMW, gasMW, otherMW);
        const percent_leading_fuel = leading_fuel / totalMW * 100;

        if (solarMW === leading_fuel){
            if (percent_leading_fuel > 75 ){
                fillColor = '#FFD700';  // Dark Yellow for high percentage
            } else if (percent_leading_fuel > 50){
                fillColor = '#FFEA00';  // Medium Yellow for medium percentage
            } else {
                fillColor = '#fcfa68';  // Light Yellow for low percentage
            }
        }
        if (ssMW === leading_fuel){
            if (percent_leading_fuel > 75 ){
                fillColor = '#FF8C00';  // Dark Orange for high percentage
            } else if (percent_leading_fuel > 50){
                fillColor = '#FFA500';  // Medium Orange for medium percentage
            } else {
                fillColor = '#FFDAB9';  // Light Orange for low percentage
            }
        }
        if (windMW === leading_fuel){
            if (percent_leading_fuel > 75 ){
                fillColor = '#0000CD';  // Dark Blue for high percentage
            } else if (percent_leading_fuel > 50){
                fillColor = '#1E90FF';  // Medium Blue for medium percentage
            } else {
                fillColor = '#ADD8E6';  // Light Blue for low percentage
            }
        }
        if (storageMW === leading_fuel){
            if (percent_leading_fuel > 75 ){
                fillColor = '#006400';  // Dark Green for high percentage
            } else if (percent_leading_fuel > 50){
                fillColor = '#32CD32';  // Medium Green for medium percentage
            } else {
                fillColor = '#98FB98';  // Light Green for low percentage
            }
        }
        if (gasMW === leading_fuel){
            if (percent_leading_fuel > 75 ){
                fillColor = '#8B0000';  // Dark Red for high percentage
            } else if (percent_leading_fuel > 50){
                fillColor = '#FF6347';  // Medium Red for medium percentage
            } else {
                fillColor = '#FFA07A';  // Light Red for low percentage
            }
        } 
        if (otherMW === leading_fuel){
            if (percent_leading_fuel > 75 ){
                fillColor = '#7A7A7A';  // Dark Gray for high percentage
            } else if (percent_leading_fuel > 50){
                fillColor = '#A9A9A9';  // Medium Gray for medium percentage
            } else {
                fillColor = '#D3D3D3';  // Light Gray for low percentage
            }
        }


        if (rto_count >= 2) {
            lineColor = '#000000';
            lineWeight = 3.5;
        }
        return {
            color: lineColor,
            weight: lineWeight,
            fillColor: fillColor,
            fillOpacity: opacity
        };
    } else {
        return {
            color: 'gray',
            weight: 1,
            fillColor: 'gray',
            fillOpacity: 0
        };
    }
}
*/
function setStyleFuelTotal(feature, fuelType, thresholds, colors) {
    const MW_val = feature.properties[fuelType];

    const style = {
        color: 'gray',
        weight: 1,
        fillColor: 'gray',
        fillOpacity: 0.6
    };

    // Return gray style for non-positive capacity
    if (MW_val === 0 || MW_val === null) {
        style.fillOpacity = 0;
        return style;
    }

    // Loop through thresholds and assign colors
    for (let i = 0; i < thresholds.length; i++) {
        if (MW_val > thresholds[i]) {
            style.fillColor = colors[i];
            break;  // Exit loop once the correct color is applied
        }
    }

    return style;
}


function loadMap(data, symbology) {
    L.geoJSON(data, {
        style: symbology,
        onEachFeature: function (feature, layer) {
            const countyName = feature.properties.join_key;
            const totalMW = feature.properties.total_capacity;
            const solarMW = feature.properties.total_solar;
            const ssMW = feature.properties.total_hybrid;
            const windMW = feature.properties.total_wind;
            const storageMW = feature.properties.total_storage;
            const gasMW = feature.properties.total_natural_gas;
            const otherMW = feature.properties.total_other;
            const rtoCount = feature.properties.rto_count;

            if (totalMW > 0 && totalMW !== null) {
                // Generate a unique ID for the canvas element
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

                    const energySources = [
                        { label: `Solar: ${solarMW.toFixed(1)} MW`, value: solarMW, color: '#FFCC00' },
                        { label: `Hybrid: ${ssMW.toFixed(1)} MW`, value: ssMW, color: '#FFAA00' },
                        { label: `Wind: ${windMW.toFixed(1)} MW`, value: windMW, color: '#00BFFF' },
                        { label: `Storage: ${storageMW.toFixed(1)} MW`, value: storageMW, color: '#32CD32' },
                        { label: `Gas: ${gasMW.toFixed(1)} MW`, value: gasMW, color: '#FF6347' },
                        { label: `Other: ${otherMW.toFixed(1)} MW`, value: otherMW, color: '#B0C4DE' }
                    ];

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
                                            //return tooltipItem.label + ': ' + tooltipItem.raw + ' MW';
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

function clearMap(map) {
    map.eachLayer(function(layer) {
        if (layer instanceof L.GeoJSON) {
            map.removeLayer(layer);
        }
    });
}

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
        thresholds = [750, 500, 200, 50, 0],
        colors = ['#050505', '#363636', '#676767', '#989898', '#c9c9c9']);
}
const totalGenSymbology = function(feature) {
    return setStyleFuelTotal(feature = feature, fuelType = 'total_capacity',
        thresholds = [2000, 1200, 750, 500, 200, 50, 0],
        colors = ['#810f7c', '#863e99', '#896bb1', '#8c96c6', '#a6bbd9', '#c6dbeb', '#edf8fb']);
}

const fuelButton = document.getElementById('fuelButton');
const solarButton = document.getElementById('solarButton');
const windButton = document.getElementById('windButton');
const storageButton = document.getElementById('storageButton');
const ngButton = document.getElementById('ngButton');
const hybridButton = document.getElementById('hybridButton');
const otherButton = document.getElementById('otherButton');
const totalGenButton = document.getElementById('totalGenButton');

const symbologyFunc = function(feature) {
    return setStyleFuelTotal(feature);
}

fuelButton.addEventListener('click', function() {
    clearMap(map);
    loadMap(cachedGeoJSON, setStyleLeadingFuel2);
});

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

fetch('data.geojson')
    .then(response => response.json())
    .then(data => {
        cachedGeoJSON = data;
        loadMap(data, totalGenSymbology);
    })
    .catch(error => console.error('Error loading GeoJSON data:', error));