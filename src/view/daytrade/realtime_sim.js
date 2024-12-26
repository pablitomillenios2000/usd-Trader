function plotData() {
    // Arrays for data (raw timestamps as integers)
    const timestampsRealtime = [];
    const valuesRealtime = [];

    // ---------------------------
    //  Fetch and parse the realtime.txt file (from the same folder)
    // ---------------------------
    fetch('./realtime.txt?' + Math.random())  // Adjusted path to be in the same folder
        .then(response => response.text())
        .then(data => {
            // Split the file into lines and process each line
            const lines = data.split('\n');
            lines.forEach(line => {
                const row = line.split(',');
                if (row.length < 2) return;
                const timestamp = parseInt(row[0].trim(), 10);
                const value = parseFloat(row[1].trim());
                if (!isNaN(timestamp) && !isNaN(value)) {
                    timestampsRealtime.push(timestamp);
                    valuesRealtime.push(value);
                }
            });

            // Create the chart after data is processed
            createChart();
        })
        .catch(err => console.error('Error fetching or parsing realtime.txt:', err));

    function createChart() {
        const lineStyle = {
            shape: 'spline',  // smooth lines
            smoothing: 1.3,   // adjust smoothing factor as needed
            width: 2          // thicker line for clarity on 4K
        };

        const traces = [];

        // Realtime trace
        traces.push({
            x: timestampsRealtime.map(ts => new Date(ts * 1000)),
            y: valuesRealtime,
            mode: 'lines',
            type: 'scatter',
            name: 'Realtime Data',
            yaxis: 'y1',
            line: lineStyle,
        });

        const layout = {
            title: 'PRODUCTION Data Chart', // Static title
            xaxis: { title: 'Time' },
            yaxis: {
                title: 'Realtime Value',
                side: 'left',
                showgrid: true,
                type: 'linear'
            },
            legend: {
                x: 0,
                y: 1,
                xanchor: 'left',
                yanchor: 'top',
            },
        };

        // Higher pixel ratio for sharper lines on 4K
        const config = {
            plotGlPixelRatio: 5  // try 2 or 3 depending on your performance needs
        };

        Plotly.newPlot('chart', traces, layout, config);
    }
}

// Add a div for the chart in the DOM
document.body.innerHTML += '<div id="chart" style="width: 100%; height: 98vh;"></div>';

// Call the plotData function
plotData();
