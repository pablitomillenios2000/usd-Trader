let titleContents = '';

function plotData() {
    // Variables to skip loading certain files
    const loadEMA = false;       // Set to false to skip loading expma.txt
    const loadEMAMicro = false; // Set to false to skip loading expma_micro.txt
    const loadAsset = true;     // Set to false to skip loading asset.txt

    // Attempt to load direction file
    const loadDirection = false; // Set to false if you do not want to load direction data

    // Set the slope display interval
    const slopeDisplayInterval = 5; // Change this value as needed

    // Variable to control logarithmic scale
    const logarithmic = false; // Set to true to use logarithmic scale for portfolio value

    // Variable to toggle the display of the margin data
    const showMargin = false; // Set to true to display the margin data

    // Define arrays to hold the data
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

    const buyTimestamps = [];
    const buyValues = [];
    const buyReasons = []; // Reasons for buy trades

    const sellTimestamps = [];
    const sellValues = [];
    const sellReasons = []; // Reasons for sell trades

    const timestampsMargin = [];
    const valuesMargin = [];

    // New arrays for direction data
    const timestampsDirection = [];
    const valuesDirection = [];

    // New arrays for SMA data
    const timestampsSMA = [];
    const valuesSMA = [];

    let tradesLineCount = 0; // Track the number of lines in the trades file
    let skipTrades = false; // Flag to skip processing trades if line count exceeds 3000

    let datasetsLoaded = {
        asset: !loadAsset,
        portfolio: false,
        untouchedPortfolio: false,
        ema: !loadEMA,
        emaMicro: !loadEMAMicro,
        emaSlopes: slopeDisplayInterval === 0 ? true : false,
        trades: false,
        margin: !showMargin,
        direction: !loadDirection, // Initially false if we intend to load direction
        sma: false, // Will set to true when SMA file is loaded or confirmed absent
    };

    let fourBillionTimestamp = null;
    let fourBillionValue = null;
    const FOUR_BILLION = 4000000000;

    function createChart() {
        const traces = [];

        // Only add the asset trace if asset was loaded
        if (loadAsset && timestampsAsset.length > 0) {
            const assetTrace = {
                x: timestampsAsset,
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
            x: timestampsPortfolio,
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
            x: timestampsUntouchedPortfolio,
            y: valuesUntouchedPortfolio,
            mode: 'lines',
            type: 'scatter',
            name: 'Untouched Portfolio Value',
            yaxis: 'y2',
            line: { color: 'darkblue' },
        };
        traces.push(untouchedPortfolioTrace);

        // Only add EMA traces if they were loaded
        if (loadEMA && timestampsEMA.length > 0) {
            const emaTrace = {
                x: timestampsEMA,
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
                x: timestampsEMAMicro,
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
                x: timestampsMargin,
                y: valuesMargin,
                mode: 'lines',
                type: 'scatter',
                name: 'Margin',
                yaxis: 'y2',
                line: { color: 'red' },
            };
            traces.push(marginTrace);
        }

        // Direction data as scatter points if available
        if (loadDirection && timestampsDirection.length > 0) {
            const directionTrace = {
                x: timestampsDirection,
                y: valuesDirection,
                mode: 'markers',
                type: 'scatter',
                name: 'Direction Points',
                yaxis: 'y2',
                marker: { color: 'blue', size: 8 },
            };
            traces.push(directionTrace);
        }

        // Simple Moving Average (SMA) trace if available
        if (timestampsSMA.length > 0) {
            const smaTrace = {
                x: timestampsSMA,
                y: valuesSMA,
                mode: 'lines',
                type: 'scatter',
                name: 'Simple MA',
                yaxis: 'y1',
                line: { color: 'green', dash: 'dot' },
            };
            traces.push(smaTrace);
        }

        const annotations = [];
        const totalTrades = buyTimestamps.length + sellTimestamps.length;

        // Show trades in log mode only if totalTrades <= 100
        const showTrades = (totalTrades <= 100) || !logarithmic;

        if (showTrades && (buyTimestamps.length > 0 || sellTimestamps.length > 0)) {
            const buyTrace = {
                x: buyTimestamps,
                y: buyValues,
                mode: 'markers',
                type: 'scatter',
                name: 'Buy Trades',
                marker: { color: 'green', size: 10 },
                yaxis: 'y2',
            };
            const sellTrace = {
                x: sellTimestamps,
                y: sellValues,
                mode: 'markers',
                type: 'scatter',
                name: 'Sell Trades',
                marker: { color: 'red', size: 10 },
                yaxis: 'y2',
            };
            traces.push(buyTrace, sellTrace);

            // Add annotations for buy/sell trades
            buyTimestamps.forEach((timestamp, index) => {
                annotations.push({
                    x: timestamp,
                    y: buyValues[index],
                    xref: 'x',
                    yref: 'y2',
                    text: buyReasons[index],
                    showarrow: false,
                    font: { size: 10, color: 'green' },
                    yshift: 10,
                });
            });
            sellTimestamps.forEach((timestamp, index) => {
                annotations.push({
                    x: timestamp,
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

        // If in logarithmic mode and we have a recorded time/value for the 4 billion mark, add a blue cross
        if (logarithmic && fourBillionTimestamp && fourBillionValue) {
            const fourBillionTrace = {
                x: [fourBillionTimestamp],
                y: [fourBillionValue],
                mode: 'markers',
                type: 'scatter',
                name: '4 Billion Mark',
                yaxis: 'y2',
                marker: {
                    color: 'blue',
                    symbol: 'x',
                    size: 12,
                },
            };
            traces.push(fourBillionTrace);
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
        };

        Plotly.newPlot('chart', traces, layout);
    }

    function checkIfReadyToCreateChart() {
        const allLoaded = Object.values(datasetsLoaded).every((loaded) => loaded);
        if (allLoaded) {
            createChart();
        }
    }

    // Load SMA data
    fetch('./output/simple_ma.txt', { method: 'HEAD' })
        .then(response => {
            if (response.ok) {
                Papa.parse('./output/simple_ma.txt', {
                    download: true,
                    delimiter: ',',
                    dynamicTyping: true,
                    step: function (row) {
                        const [timestamp, value] = row.data;
                        if (timestamp && value !== undefined) {
                            timestampsSMA.push(new Date(timestamp * 1000));
                            valuesSMA.push(value);
                        }
                    },
                    complete: function () {
                        datasetsLoaded.sma = true;
                        checkIfReadyToCreateChart();
                    },
                    error: function (error) {
                        console.error('Error parsing SMA data file:', error);
                        datasetsLoaded.sma = true; // Proceed even if error
                        checkIfReadyToCreateChart();
                    },
                });
            } else {
                // File does not exist, mark as loaded
                datasetsLoaded.sma = true;
                checkIfReadyToCreateChart();
            }
        })
        .catch(error => {
            console.error('Error checking SMA file existence:', error);
            datasetsLoaded.sma = true; // Proceed even if error
            checkIfReadyToCreateChart();
        });

    // Asset Data
    if (loadAsset) {
        Papa.parse('./output/asset.txt', {
            download: true,
            delimiter: ',',
            dynamicTyping: true,
            step: function (row) {
                const [timestamp, value] = row.data;
                if (timestamp && value !== undefined) {
                    timestampsAsset.push(new Date(timestamp * 1000));
                    valuesAsset.push(value);
                }
            },
            complete: function () {
                datasetsLoaded.asset = true;
                checkIfReadyToCreateChart();
            },
            error: function (error) {
                console.error('Error parsing asset data file:', error);
                datasetsLoaded.asset = true;
                checkIfReadyToCreateChart();
            },
        });
    }

    // Portfolio Data
    Papa.parse('./output/portfolio.txt', {
        download: true,
        delimiter: ',',
        dynamicTyping: true,
        step: function (row) {
            const [timestamp, value] = row.data;
            if (timestamp && value !== undefined) {
                timestampsPortfolio.push(new Date(timestamp * 1000));
                valuesPortfolio.push(value);
                // Check for 4 billion mark
                if (fourBillionTimestamp === null && value >= FOUR_BILLION) {
                    fourBillionTimestamp = new Date(timestamp * 1000);
                    fourBillionValue = value;
                }
            }
        },
        complete: function () {
            datasetsLoaded.portfolio = true;
            checkIfReadyToCreateChart();
        },
        error: function (error) {
            console.error('Error parsing portfolio data file:', error);
            datasetsLoaded.portfolio = true;
            checkIfReadyToCreateChart();
        },
    });

    // Untouched Portfolio Data
    Papa.parse('./output/untouched_portfolio.txt', {
        download: true,
        delimiter: ',',
        dynamicTyping: true,
        step: function (row) {
            const [timestamp, value] = row.data;
            if (timestamp && value !== undefined) {
                timestampsUntouchedPortfolio.push(new Date(timestamp * 1000));
                valuesUntouchedPortfolio.push(value);
            }
        },
        complete: function () {
            datasetsLoaded.untouchedPortfolio = true;
            checkIfReadyToCreateChart();
        },
        error: function (error) {
            console.error('Error parsing untouched portfolio data file:', error);
            datasetsLoaded.untouchedPortfolio = true;
            checkIfReadyToCreateChart();
        },
    });

    // EMA Data
    if (loadEMA) {
        Papa.parse('./output/expma.txt', {
            download: true,
            delimiter: ',',
            dynamicTyping: true,
            step: function (row) {
                const [timestamp, value] = row.data;
                if (timestamp && value !== undefined) {
                    timestampsEMA.push(new Date(timestamp * 1000));
                    valuesEMA.push(value);
                }
            },
            complete: function () {
                datasetsLoaded.ema = true;
                checkIfReadyToCreateChart();
            },
            error: function (error) {
                console.error('Error parsing EMA data file:', error);
                datasetsLoaded.ema = true;
                checkIfReadyToCreateChart();
            },
        });
    }

    // EMAMicro Data
    if (loadEMAMicro) {
        Papa.parse('./output/expma_micro.txt', {
            download: true,
            delimiter: ',',
            dynamicTyping: true,
            step: function (row) {
                const [timestamp, value] = row.data;
                if (timestamp && value !== undefined) {
                    timestampsEMAMicro.push(new Date(timestamp * 1000));
                    valuesEMAMicro.push(value);
                }
            },
            complete: function () {
                datasetsLoaded.emaMicro = true;
                checkIfReadyToCreateChart();
            },
            error: function (error) {
                console.error('Error parsing EMAMicro data file:', error);
                datasetsLoaded.emaMicro = true;
                checkIfReadyToCreateChart();
            },
        });
    }

    // EMA Slopes (if slopeDisplayInterval != 0, load them)
    if (slopeDisplayInterval !== 0) {
        Papa.parse('./output/ema_slopes.txt', {
            download: true,
            delimiter: ',',
            dynamicTyping: true,
            step: function (row) {
                const [timestamp, slope] = row.data;
                if (timestamp && slope !== undefined) {
                    timestampsSlopes.push(new Date(timestamp * 1000));
                    slopes.push(slope);
                }
            },
            complete: function () {
                datasetsLoaded.emaSlopes = true;
                checkIfReadyToCreateChart();
            },
            error: function (error) {
                console.error('Error parsing EMA slopes data file:', error);
                datasetsLoaded.emaSlopes = true;
                checkIfReadyToCreateChart();
            },
        });
    }

    // Trades Data
    Papa.parse('./output/trades.txt', {
        download: true,
        delimiter: ',',
        dynamicTyping: true,
        step: function (row) {
            const [timestamp, price, action, reason] = row.data;
            if (timestamp && price !== undefined && action) {
                if (action.toLowerCase() === 'buy') {
                    buyTimestamps.push(new Date(timestamp * 1000));
                    buyValues.push(price);
                    buyReasons.push(reason || '');
                } else if (action.toLowerCase() === 'sell') {
                    sellTimestamps.push(new Date(timestamp * 1000));
                    sellValues.push(price);
                    sellReasons.push(reason || '');
                }
                tradesLineCount++;
                if (tradesLineCount > 3000) {
                    // Skip further processing if too many lines
                    skipTrades = true;
                }
            }
        },
        complete: function () {
            datasetsLoaded.trades = true;
            checkIfReadyToCreateChart();
        },
        error: function (error) {
            console.error('Error parsing trades data file:', error);
            datasetsLoaded.trades = true;
            checkIfReadyToCreateChart();
        },
    });

    // Margin Data
    if (showMargin) {
        Papa.parse('./output/margin.txt', {
            download: true,
            delimiter: ',',
            dynamicTyping: true,
            step: function (row) {
                const [timestamp, value] = row.data;
                if (timestamp && value !== undefined) {
                    timestampsMargin.push(new Date(timestamp * 1000));
                    valuesMargin.push(value);
                }
            },
            complete: function () {
                datasetsLoaded.margin = true;
                checkIfReadyToCreateChart();
            },
            error: function (error) {
                console.error('Error parsing margin data file:', error);
                datasetsLoaded.margin = true;
                checkIfReadyToCreateChart();
            },
        });
    }

    // Direction Data
    if (loadDirection) {
        Papa.parse('./output/direction.txt', {
            download: true,
            delimiter: ',',
            dynamicTyping: true,
            step: function (row) {
                const [timestamp, value] = row.data;
                if (timestamp && value !== undefined) {
                    timestampsDirection.push(new Date(timestamp * 1000));
                    valuesDirection.push(value);
                }
            },
            complete: function () {
                datasetsLoaded.direction = true;
                checkIfReadyToCreateChart();
            },
            error: function (error) {
                console.error('Error parsing direction data file:', error);
                datasetsLoaded.direction = true;
                checkIfReadyToCreateChart();
            },
        });
    }
}

function setTitleWithPairName() {
    fetch('./output/pairname.txt')
        .then(response => response.text())
        .then(pairName => {
            const trimmedPairName = pairName.trim();
            if (trimmedPairName) {
                // Update the browser tab title
                document.title = `SIMULATION - ${trimmedPairName} Data Chart`;
                titleContents = `SIMULATION - ${trimmedPairName} Data Chart`;
            }
        })
        .catch(error => console.error('Error fetching pair name:', error));
}

// Add a div for the chart in the DOM
document.body.innerHTML += '<div id="chart" style="width: 100%; height: 98vh;"></div>';

// Call the function to plot the data
setTitleWithPairName();
plotData();
