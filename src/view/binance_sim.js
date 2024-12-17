let titleContents = '';

function setTitleWithPairName() {
    fetch('./output/pairname.txt')
        .then(response => response.text())
        .then(pairName => {
            const trimmedPairName = pairName.trim();
            if (trimmedPairName) {
                document.title = `SIMULATION - ${trimmedPairName} Data Chart`;
                titleContents = `SIMULATION - ${trimmedPairName} Data Chart`;
            }
        })
        .catch(error => console.error('Error fetching pair name:', error));
}

function plotData() {
    // Variables to skip loading certain files
    const loadEMA = true;       // Set to false to skip loading expma.txt
    const loadEMAMicro = true; // Set to false to skip loading expma_micro.txt
    const loadAsset = false;    // Set to false to skip loading asset.txt

    // Set the slope display interval
    const slopeDisplayInterval = 5; // Change this value as needed

    // Variable to control logarithmic scale for portfolio value
    const logarithmic = true; // Set to true for log scale

    // Variable to toggle display of margin data
    const showMargin = false; // Set to true to display margin data

    // Arrays for data (raw timestamps as integers)
    const timestampsAsset = [];
    const valuesAsset = [];

    const timestampsPortfolio = [];
    const valuesPortfolio = [];

    const timestampsUntouchedPortfolio = [];
    const valuesUntouchedPortfolio = [];

    const timestampsEMA = [];
    const valuesEMA = [];

    const timestampsEMAMicro = [];
    const valuesEMAMicro = [];

    const timestampsSlopes = [];
    const slopes = [];

    const timestampsMargin = [];
    const valuesMargin = [];

    // Arrays for trades (store them first, match later)
    let rawTrades = [];  // Will store {timestamp, action, reason} objects

    // Final arrays for plotting trades once matched
    const buyTimestamps = [];
    const buyValues = [];
    const buyReasons = [];

    const sellTimestamps = [];
    const sellValues = [];
    const sellReasons = [];

    let showTrades = true;  // Will be set to false if more than 10,000 trades

    let datasetsLoaded = {
        asset: !loadAsset,
        portfolio: false,
        untouchedPortfolio: false,
        ema: !loadEMA,
        emaMicro: !loadEMAMicro,
        emaSlopes: slopeDisplayInterval === 0 ? true : false,
        trades: false,
        margin: !showMargin,
    };

    // Thresholds and colors
    const thresholds = [
        { value: 100000, label: '100K', color: '#87CEFA' },
        { value: 1000000, label: '1M', color: '#6495ED' },
        { value: 100000000, label: '100M', color: '#4169E1' },
        { value: 4000000000, label: '4B', color: '#00008B' }
    ];

    let shapes = [];
    let annotations = [];
    let thresholdTraces = [];

    function createChart() {
        const traces = [];

        // Only add the asset trace if asset was loaded
        if (loadAsset && timestampsAsset.length > 0) {
            const assetTrace = {
                x: timestampsAsset.map(ts => new Date(ts * 1000)),
                y: valuesAsset,
                mode: 'lines',
                type: 'scatter',
                name: 'Asset Price',
                yaxis: 'y1',
            };
            traces.push(assetTrace);
        }

        // Portfolio trace
        const portfolioTrace = {
            x: timestampsPortfolio.map(ts => new Date(ts * 1000)),
            y: valuesPortfolio,
            mode: 'lines',
            type: 'scatter',
            name: 'Portfolio Value',
            yaxis: 'y2',
            line: { color: 'orange' },
        };
        traces.push(portfolioTrace);

        // Untouched portfolio trace
        const untouchedPortfolioTrace = {
            x: timestampsUntouchedPortfolio.map(ts => new Date(ts * 1000)),
            y: valuesUntouchedPortfolio,
            mode: 'lines',
            type: 'scatter',
            name: 'Untouched Portfolio Value',
            yaxis: 'y2',
            line: { color: 'darkblue' }
        };
        traces.push(untouchedPortfolioTrace);

        // EMA traces if loaded
        if (loadEMA && timestampsEMA.length > 0) {
            const emaTrace = {
                x: timestampsEMA.map(ts => new Date(ts * 1000)),
                y: valuesEMA,
                mode: 'lines',
                type: 'scatter',
                name: 'EMA',
                yaxis: 'y1',
                line: { color: 'black', shape: 'spline' },
            };
            traces.push(emaTrace);
        }

        if (loadEMAMicro && timestampsEMAMicro.length > 0) {
            const emaMicroTrace = {
                x: timestampsEMAMicro.map(ts => new Date(ts * 1000)),
                y: valuesEMAMicro,
                mode: 'lines',
                type: 'scatter',
                name: 'EMA Micro',
                yaxis: 'y1',
                line: { color: 'purple', shape: 'spline' },
            };
            traces.push(emaMicroTrace);
        }

        // Margin trace if enabled
        if (showMargin && timestampsMargin.length > 0) {
            const marginTrace = {
                x: timestampsMargin.map(ts => new Date(ts * 1000)),
                y: valuesMargin,
                mode: 'lines',
                type: 'scatter',
                name: 'Margin',
                yaxis: 'y2',
                line: { color: 'red' },
            };
            traces.push(marginTrace);
        }

        // Threshold markers
        if (thresholdTraces.length > 0) {
            traces.push(...thresholdTraces);
        }

        // Trades
        if (showTrades && (buyTimestamps.length > 0 || sellTimestamps.length > 0)) {
            const buyTrace = {
                x: buyTimestamps.map(ts => new Date(ts * 1000)),
                y: buyValues,
                mode: 'markers',
                type: 'scatter',
                name: 'Buy Trades',
                marker: { color: 'green', size: 10 },
                yaxis: 'y2',
            };
            const sellTrace = {
                x: sellTimestamps.map(ts => new Date(ts * 1000)),
                y: sellValues,
                mode: 'markers',
                type: 'scatter',
                name: 'Sell Trades',
                marker: { color: 'red', size: 10 },
                yaxis: 'y2',
            };
            traces.push(buyTrace, sellTrace);

            buyTimestamps.forEach((ts, index) => {
                annotations.push({
                    x: new Date(ts * 1000),
                    y: buyValues[index],
                    xref: 'x',
                    yref: 'y2',
                    text: buyReasons[index],
                    showarrow: false,
                    font: { size: 10, color: 'green' },
                    yshift: 10,
                });
            });
            sellTimestamps.forEach((ts, index) => {
                annotations.push({
                    x: new Date(ts * 1000),
                    y: sellValues[index],
                    xref: 'x',
                    yref: 'y2',
                    text: sellReasons[index],
                    showarrow: false,
                    font: { size: 10, color: 'red' },
                    yshift: -10,
                });
            });
        }

        const layout = {
            title: titleContents,
            xaxis: { title: 'Time' },
            yaxis: {
                title: 'Asset Price',
                side: 'left',
                showgrid: true,
            },
            yaxis2: {
                title: 'Portfolio Value',
                side: 'right',
                overlaying: 'y',
                showgrid: false,
                type: logarithmic ? 'log' : 'linear',
            },
            legend: {
                x: 0,
                y: 1,
                xanchor: 'left',
                yanchor: 'top',
            },
            annotations: annotations,
            shapes: shapes,
        };

        Plotly.newPlot('chart', traces, layout);
    }

    function checkIfReadyToCreateChart() {
        const allLoaded = Object.values(datasetsLoaded).every((loaded) => loaded);
        if (allLoaded) {
            // Threshold checks
            thresholds.forEach(threshold => {
                let thresholdTimestamp = null;
                let thresholdValue = threshold.value;

                for (let i = 0; i < valuesPortfolio.length; i++) {
                    if (valuesPortfolio[i] >= thresholdValue) {
                        thresholdTimestamp = timestampsPortfolio[i];
                        break;
                    }
                }

                if (thresholdTimestamp !== null) {
                    thresholdTraces.push({
                        x: [new Date(thresholdTimestamp * 1000)],
                        y: [thresholdValue],
                        mode: 'markers',
                        type: 'scatter',
                        name: threshold.label,
                        yaxis: 'y2',
                        marker: {
                            symbol: 'x',
                            size: 12,
                            color: threshold.color
                        },
                        hoverinfo: 'text',
                        hovertext: `Portfolio reached ${threshold.label} (${thresholdValue.toLocaleString()})`
                    });
                }
            });

            // Now that trades and portfolio are loaded, match trades to portfolio
            matchTradesToPortfolio();

            createChart();
        }
    }

    function matchTradesToPortfolio() {
        // For each trade, find the exact matching portfolio timestamp
        rawTrades.forEach(trade => {
            const { timestamp, action, reason } = trade;
            const idx = timestampsPortfolio.indexOf(timestamp);
            if (idx !== -1) {
                const value = valuesPortfolio[idx];
                if (action === 'buy') {
                    buyTimestamps.push(timestamp);
                    buyValues.push(value);
                    buyReasons.push(reason);
                } else if (action === 'sell') {
                    sellTimestamps.push(timestamp);
                    sellValues.push(value);
                    sellReasons.push(reason);
                }
            } else {
                console.warn(`No exact match in portfolio for trade at timestamp ${timestamp}`);
            }
        });

        const totalTrades = buyTimestamps.length + sellTimestamps.length;
        if (totalTrades > 1000) {
            showTrades = false;
        }
    }

    function parseTradesData() {
        Papa.parse('./output/trades.txt', {
            download: true,
            delimiter: ',',
            dynamicTyping: true,
            skipEmptyLines: true,
            complete: function (results) {
                const data = results.data;
                data.forEach(row => {
                    if (row.length < 3) return;
                    const [timestamp, action, reason] = row;

                    if (typeof timestamp === 'number' && action && reason) {
                        rawTrades.push({ timestamp, action, reason });
                    }
                });
                datasetsLoaded.trades = true;
                // After trades are parsed, parse the portfolio data
                parsePortfolioData();
            },
            error: function (error) {
                console.error('Error parsing trades file:', error);
            },
        });
    }

    function parsePortfolioData() {
        Papa.parse('./output/portfolio.txt', {
            download: true,
            delimiter: ',',
            dynamicTyping: true,
            skipEmptyLines: true,
            step: function (row) {
                const [timestamp, value] = row.data;
                if (typeof timestamp === 'number' && value !== undefined) {
                    timestampsPortfolio.push(timestamp);
                    valuesPortfolio.push(value);
                }
            },
            complete: function () {
                datasetsLoaded.portfolio = true;
                checkIfReadyToCreateChart();
            },
            error: function (error) {
                console.error('Error parsing portfolio data file:', error);
            },
        });
    }

    // Parse untouched portfolio
    Papa.parse('./output/untouched_portfolio.txt', {
        download: true,
        delimiter: ',',
        dynamicTyping: true,
        skipEmptyLines: true,
        step: function (row) {
            const [timestamp, value] = row.data;
            if (typeof timestamp === 'number' && value !== undefined) {
                timestampsUntouchedPortfolio.push(timestamp);
                valuesUntouchedPortfolio.push(value);
            }
        },
        complete: function () {
            datasetsLoaded.untouchedPortfolio = true;
            checkIfReadyToCreateChart();
        },
        error: function (error) {
            console.error('Error parsing untouched portfolio data file:', error);
        },
    });

    // Parse EMA if enabled
    if (loadEMA) {
        Papa.parse('./output/expma.txt', {
            download: true,
            delimiter: ',',
            dynamicTyping: true,
            skipEmptyLines: true,
            step: function (row) {
                const [timestamp, value] = row.data;
                if (typeof timestamp === 'number' && value !== undefined) {
                    timestampsEMA.push(timestamp);
                    valuesEMA.push(value);
                }
            },
            complete: function () {
                datasetsLoaded.ema = true;
                checkIfReadyToCreateChart();
            },
            error: function (error) {
                console.error('Error parsing EMA data file:', error);
            },
        });
    }

    // Parse EMA Micro if enabled
    if (loadEMAMicro) {
        Papa.parse('./output/expma_micro.txt', {
            download: true,
            delimiter: ',',
            dynamicTyping: true,
            skipEmptyLines: true,
            step: function (row) {
                const [timestamp, value] = row.data;
                if (typeof timestamp === 'number' && value !== undefined) {
                    timestampsEMAMicro.push(timestamp);
                    valuesEMAMicro.push(value);
                }
            },
            complete: function () {
                datasetsLoaded.emaMicro = true;
                checkIfReadyToCreateChart();
            },
            error: function (error) {
                console.error('Error parsing EMA micro data file:', error);
            },
        });
    }

    // Parse EMA Slopes if enabled
    if (slopeDisplayInterval > 0) {
        Papa.parse('./output/ema_slopes.txt', {
            download: true,
            delimiter: ',',
            dynamicTyping: true,
            skipEmptyLines: true,
            step: function (row) {
                const [timestamp, slopeValue] = row.data;
                if (typeof timestamp === 'number' && slopeValue !== undefined) {
                    timestampsSlopes.push(timestamp);
                    slopes.push(slopeValue);
                }
            },
            complete: function () {
                datasetsLoaded.emaSlopes = true;
                checkIfReadyToCreateChart();
            },
            error: function (error) {
                console.error('Error parsing EMA slopes data file:', error);
            },
        });
    }

    // Parse margin if enabled
    if (showMargin) {
        Papa.parse('./output/margin.txt', {
            download: true,
            delimiter: ',',
            dynamicTyping: true,
            skipEmptyLines: true,
            step: function (row) {
                const [timestamp, value] = row.data;
                if (typeof timestamp === 'number' && value !== undefined) {
                    timestampsMargin.push(timestamp);
                    valuesMargin.push(value);
                }
            },
            complete: function () {
                datasetsLoaded.margin = true;
                checkIfReadyToCreateChart();
            },
            error: function (error) {
                console.error('Error parsing margin data file:', error);
            },
        });
    }

    // Start by parsing trades first
    parseTradesData();
}

// Add a div for the chart in the DOM
document.body.innerHTML += '<div id="chart" style="width: 100%; height: 98vh;"></div>';

// Call the function to plot the data
setTitleWithPairName();
plotData();
