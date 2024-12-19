// Create the map and set the view to a specific location and zoom level
const map = L.map('map').setView([39.8283, -98.5795], 4); // Centered on the USA

// Add OpenStreetMap tiles as the basemap
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Load the GeoJSON file
fetch('data.geojson')
    .then(response => {
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
    })
    .then(geojsonData => {
    // Add GeoJSON layer to the map
    L.geoJSON(geojsonData, {
    style: {
        color: "blue",
        weight: 2,
        opacity: 0.8
    },
        onEachFeature: function (feature, layer) {
        if (feature.properties && feature.properties.name) {
            layer.bindPopup(feature.properties.name);
        }
        }
    }).addTo(map);
    })
    .catch(error => {
    console.error('Error loading GeoJSON:', error);
    });
