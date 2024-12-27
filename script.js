// Create the map and set the view to a specific location and zoom level
const map = L.map('map').setView([39.8283, -98.5795], 4); // Centered on the USA

// Add OpenStreetMap tiles as the basemap
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

function createPieChart(data, colors, size) {
    const canvas = document.createElement('canvas');
    canvas.width = size; // Adjust size as needed
    canvas.height = size;

    const ctx = canvas.getContext('2d');
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: data.map((_, i) => `Segment ${i + 1}`), // Optional labels
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderColor: 'black',
                borderWidth: 1
            }]
        },
        options: {
            responsive: false,
            plugins: {
                legend: { display: false } // Hide legend for compact size
            }
        }
    });

    //console.log('Pie chart created:', canvas); // Debugging statement

    return canvas;
}

function addPieChartToMap(map, lat, lng, data, colors, size) {
    const pieChartCanvas = createPieChart(data, colors, size);

    const pieChartIcon = L.divIcon({
        html: pieChartCanvas, // Convert canvas to HTML
        className: '', // Remove default styles
        iconSize: [size, size], // Match canvas size
        iconAnchor: [size/2, size/2], // Center the icon
        //zIndexOffset: 1000 // Ensure the pie chart is on top
    });

    L.marker([lat, lng], { icon: pieChartIcon }).addTo(map);
    //console.log('Pie chart added to map at:', lat, lng); // Debugging statement
}

function chartSize(capacity) {
    if (capacity < 100) {
        return 10;
    } else if (capacity < 500) {
        return 15;
    } else if (capacity < 1000) {
        return 25;
    } else {
        return 30;
    }
}

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
                color: "gray",
                weight: 1.5,
                opacity: 1,
                fillColor: 'transparent',
            },
            onEachFeature: function (feature, layer) {
                if (feature.geometry.type === "Polygon") {
                    const centroid = turf.centroid(feature).geometry.coordinates;

                    const total = feature.properties.total_capacity;
                    const solar = feature.properties.total_solar;
                    const hybrid = feature.properties.total_hybrid;
                    const storage = feature.properties.total_storage;
                    const natural_gas = feature.properties.total_natural_gas;
                    const wind = feature.properties.total_wind;
                    const other = feature.properties.total_other;

                    const pieData = [
                        (solar / total) * 100,
                        (hybrid / total) * 100,
                        (storage / total) * 100,
                        (natural_gas / total) * 100,
                        (wind / total) * 100,
                        (other / total) * 100
                    ];
                    const pieColors = ['rgb(255, 212, 19)', 'rgb(255, 137, 2)', 'rgb(229, 53, 9)', 'rgb(28, 232, 45)', 'rgb(9, 223, 243)', 'rgb(179, 179, 179)'];
                    
                    const size = chartSize(total);
                    // Add the pie chart to the map
                    addPieChartToMap(map, centroid[1], centroid[0], pieData, pieColors, size);
                }
            }
        }).addTo(map);
    })
    .catch(error => {
        console.error('Error loading GeoJSON:', error);
    });
