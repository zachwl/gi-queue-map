// Create the map and set the view to a specific location and zoom level
const map = L.map('map').setView([40, -87], 6); // Centered on the USA

// Add OpenStreetMap tiles as the basemap
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

function setStyleTotalCapacity(feature) {
    const totalMW = feature.properties.total_capacity;
    const rto_count = feature.properties.rto_count;
    // Example: Set color based on total queued energy
    let fillColor;
    let opacity = 0.7;
    let lineColor = 'gray';
    let lineWeight = 1;
    if (totalMW > 2000) {
        fillColor = '#000080';  // Dark Blue for very high capacity
    } else if (totalMW > 1500) {
        fillColor = '#0000CD';  // Medium Dark Blue for high capacity
    } else if (totalMW > 1000) {
        fillColor = '#1E90FF';  // Dodger Blue for medium-high capacity
    } else if (totalMW > 500) {
        fillColor = '#00BFFF';  // Deep Sky Blue for medium capacity
    } else if (totalMW > 100) {
        fillColor = '#87CEFA';  // Light Sky Blue for low-medium capacity
    } else if (totalMW > 0) {
        fillColor = '#B0E0E6';  // Powder Blue for low capacity
    } else {
        fillColor = '#D3D3D3';  // Gray for no capacity
        opacity = 0;
    }
    if (rto_count >= 2) {
        lineColor = '#000000';  // Gold for multiple RTOs
        lineWeight = 3.5;
    }
    return {
        color: lineColor,  // Border color
        weight: lineWeight,  // Border thickness
        fillColor: fillColor,  // Fill color based on totalMW
        fillOpacity: opacity  // Transparency of the fill
    };
}

function setStyleLeadingFuel(feature){
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
        let opacity = 0.8;
        let lineColor = 'gray';
        let lineWeight = 1;

        const leading_fuel = Math.max(solarMW, ssMW, windMW, storageMW, gasMW, otherMW);
        const percent_leading_fuel = leading_fuel / totalMW * 100;

        let hue;
        const saturation = percent_leading_fuel;
        console.log(saturation);
        const value = 100;
        if (solarMW === leading_fuel){
            hue = 54;  // Yellow for solar
        } else if (ssMW === leading_fuel){
            hue = 35;  // Orange for solar-storage
        } else if (windMW === leading_fuel){
            hue = 173;  // Blue for wind
        } else if (storageMW === leading_fuel){
            hue = 133;  // Green for storage
        } else if (gasMW === leading_fuel){
            hue = 5;  // Red for gas
        } else {
            hue = 285;  // Purple for other
        }

        function hsvToRgb(h, s) {
            // Ensure h and s are in the range of 0-360 (for h) and 0-100 (for s)
            h = h % 360; // Wrap around hue if needed
            s = s / 100;
        
            let c = s; // Chroma (since v is always 100%)
            let x = c * (1 - Math.abs((h / 60) % 2 - 1)); // Intermediate value
            let m = 1 - c; // Match factor for brightness adjustment
        
            let r = 0, g = 0, b = 0;
        
            if (h >= 0 && h < 60) {
                r = c; g = x; b = 0;
            } else if (h >= 60 && h < 120) {
                r = x; g = c; b = 0;
            } else if (h >= 120 && h < 180) {
                r = 0; g = c; b = x;
            } else if (h >= 180 && h < 240) {
                r = 0; g = x; b = c;
            } else if (h >= 240 && h < 300) {
                r = x; g = 0; b = c;
            } else if (h >= 300 && h < 360) {
                r = c; g = 0; b = x;
            }
        
            // Convert to 0-255 range
            r = Math.round((r + m) * 255);
            g = Math.round((g + m) * 255);
            b = Math.round((b + m) * 255);
            color_string = `rgb(${r}, ${g}, ${b})`;
            return color_string;
        }
        fillColor = hsvToRgb(hue, saturation)
        








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

// Load the GeoJSON data
fetch('data.geojson')
    .then(response => response.json())
    .then(data => {
        L.geoJSON(data, {
            style: setStyleLeadingFuel,
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
    })
    .catch(error => console.error('Error loading GeoJSON data:', error));
