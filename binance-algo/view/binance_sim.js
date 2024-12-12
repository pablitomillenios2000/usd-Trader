function plotData() {
    // Set the slope display interval
    const slopeDisplayInterval = 5; // Change this value as needed

    // Variable to control logarithmic scale
    const logarithmic = true; // Set to true to use logarithmic scale for portfolio value

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

    let tradesLineCount = 0; // Track the number of lines in the trades file
    let skipTrades = false; // Flag to skip processing trades if line count exceeds 3000

    let datasetsLoaded = {
        asset: false,
        portfolio: false,
        untouchedPortfolio: false,
        ema: false,
        emaMicro: false,
        emaSlopes: slopeDisplayInterval === 0 ? true : false,
        trades: false,
        margin: !showMargin,
    };

    let fourBillionTimestamp = null;
    let fourBillionValue = null;

    function createChart() {
        const assetTrace = {
            x: timestampsAsset,
            y: valuesAsset,
            mode: 'lines',
            type: 'scatter',
            name: 'Asset Price',
            yaxis: 'y1',
        };

        const portfolioTrace = {
            x: timestampsPortfolio,
            y: valuesPortfolio,
            mode: 'lines',
            type: 'scatter',
            name: 'Portfolio Value',
            yaxis: 'y2',
            line: { color: 'orange' },
        };

        const untouchedPortfolioTrace = {
            x: timestampsUntouchedPortfolio,
            y: valuesUntouchedPortfolio,
            mode: 'lines',
            type: 'scatter',
            name: 'Untouched Portfolio Value',
            yaxis: 'y2',
        };

        const emaTrace = {
            x: timestampsEMA,
            y: valuesEMA,
            mode: 'lines',
            type: 'scatter',
            name: 'EMA',
            yaxis: 'y1',
            line: { color: 'black', shape: 'spline' },
        };

        const emaMicroTrace = {
            x: timestampsEMAMicro,
            y: valuesEMAMicro,
            mode: 'lines',
            type: 'scatter',
            name: 'EMA Micro',
            yaxis: 'y1',
            line: { color: 'purple', shape: 'spline' },
        };

        const marginTrace = {
            x: timestampsMargin,
            y: valuesMargin,
            mode: 'lines',
            type: 'scatter',
            name: 'Margin',
            yaxis: 'y2',
            line: { color: 'red' },
        };

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

        const traces = [assetTrace, portfolioTrace, untouchedPortfolioTrace, emaTrace, emaMicroTrace];
        if (showMargin) {
            traces.push(marginTrace);
        }

        // Hide buy/sell in log mode
        if (!logarithmic && (buyTimestamps.length > 0 || sellTimestamps.length > 0)) {
            traces.push(buyTrace, sellTrace);
        }

        const annotations = [];
        if (!logarithmic) {
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

        let shapes = [];
        if (fourBillionTimestamp && fourBillionValue) {
            // Define a large time window for horizontal line (12 hours each side)
            const halfDay = 12 * 3600 * 1000;
            const x0Time = new Date(fourBillionTimestamp.getTime() - halfDay);
            const x1Time = new Date(fourBillionTimestamp.getTime() + halfDay);

            // Define a vertical span (half to double the 4B value)
            const y0Value = fourBillionValue / 2;
            const y1Value = fourBillionValue * 2;

            shapes = [
                {
                    // Horizontal line segment crossing the 4B point
                    type: 'line',
                    layer: 'above',
                    xref: 'x',
                    yref: 'y2',
                    x0: x0Time,
                    x1: x1Time,
                    y0: fourBillionValue,
                    y1: fourBillionValue,
                    line: {
                        color: 'blue',
                        width: 8,
                        dash: 'solid',
                    }
                },
                {
                    // Vertical line segment crossing the 4B point
                    type: 'line',
                    layer: 'above',
                    xref: 'x',
                    yref: 'y2',
                    x0: fourBillionTimestamp,
                    x1: fourBillionTimestamp,
                    y0: y0Value,
                    y1: y1Value,
                    line: {
                        color: 'blue',
                        width: 8,
                        dash: 'solid',
                    }
                }
            ];

            annotations.push({
                x: fourBillionTimestamp,
                y: fourBillionValue,
                xref: 'x',
                yref: 'y2',
                text: '4B',
                showarrow: true,
                arrowhead: 2,
                arrowsize: 2,
                arrowwidth: 2,
                arrowcolor: 'blue',
                ax: 20,
                ay: -30,
                font: { size: 16, color: 'blue', family: 'Arial Black' },
                bgcolor: 'rgba(255, 255, 255, 0.7)'
            });
        }

        const layout = {
            title: 'Cryptocurrency and Portfolio Data Chart',
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
            const fourBillion = 4000000000;
            for (let i = 0; i < valuesPortfolio.length; i++) {
                if (valuesPortfolio[i] >= fourBillion) {
                    fourBillionTimestamp = timestampsPortfolio[i];
                    fourBillionValue = valuesPortfolio[i];
                    break;
                }
            }
            createChart();
        }
    }

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
            console.error('Error while parsing asset data file:', error);
        },
    });

    Papa.parse('./output/portfolio.txt', {
        download: true,
        delimiter: ',',
        dynamicTyping: true,
        step: function (row) {
            const [timestamp, value] = row.data;
            if (timestamp && value !== undefined) {
                timestampsPortfolio.push(new Date(timestamp * 1000));
                valuesPortfolio.push(value);
            }
        },
        complete: function () {
            datasetsLoaded.portfolio = true;
            checkIfReadyToCreateChart();
            parseTradesData();
        },
        error: function (error) {
            console.error('Error while parsing portfolio data file:', error);
        },
    });

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
            console.error('Error while parsing untouched portfolio data file:', error);
        },
    });

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
            console.error('Error while parsing EMA data file:', error);
        },
    });

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
            console.error('Error while parsing EMA micro data file:', error);
        },
    });

    if (slopeDisplayInterval > 0) {
        Papa.parse('./output/ema_slopes.txt', {
            download: true,
            delimiter: ',',
            dynamicTyping: true,
            step: function (row) {
                const [timestamp, slopeValue] = row.data;
                if (timestamp && slopeValue !== undefined) {
                    timestampsSlopes.push(new Date(timestamp * 1000));
                    slopes.push(slopeValue);
                }
            },
            complete: function () {
                datasetsLoaded.emaSlopes = true;
                checkIfReadyToCreateChart();
            },
            error: function (error) {
                console.error('Error while parsing EMA slopes data file:', error);
            },
        });
    }

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
                console.error('Error while parsing margin data file:', error);
            },
        });
    }

    function parseTradesData() {
        Papa.parse('./output/trades.txt', {
            download: true,
            delimiter: ',',
            dynamicTyping: true,
            step: function (row) {
                tradesLineCount += 1;
                if (tradesLineCount > 3000) {
                    skipTrades = true;
                    return; // Stop processing additional rows
                }

                const [timestamp, action, reason] = row.data;
                if (timestamp && action && reason) {
                    const date = new Date(timestamp * 1000);
                    const portfolioIndex = timestampsPortfolio.findIndex((t) => t.getTime() === date.getTime());
                    let value;
                    if (portfolioIndex !== -1) {
                        value = valuesPortfolio[portfolioIndex];
                    } else {
                        let closestIndex = -1;
                        let minDiff = Infinity;
                        timestampsPortfolio.forEach((t, idx) => {
                            const diff = Math.abs(t - date);
                            if (diff < minDiff) {
                                minDiff = diff;
                                closestIndex = idx;
                            }
                        });
                        if (closestIndex !== -1) {
                            value = valuesPortfolio[closestIndex];
                        }
                    }
                    if (value !== undefined) {
                        if (action === 'buy') {
                            buyTimestamps.push(date);
                            buyValues.push(value);
                            buyReasons.push(reason);
                        } else if (action === 'sell') {
                            sellTimestamps.push(date);
                            sellValues.push(value);
                            sellReasons.push(reason);
                        }
                    }
                }
            },
            complete: function () {
                if (skipTrades) {
                    console.warn('Trades file has more than 3000 lines. Skipping trades plotting.');
                }
                datasetsLoaded.trades = true;
                checkIfReadyToCreateChart();
            },
            error: function (error) {
                console.error('Error while parsing trades file:', error);
            },
        });
    }
}

// Add a div for the chart in the DOM
document.body.innerHTML += '<div id="chart" style="width: 100%; height: 98vh;"></div>';

// Call the function to plot the data
plotData();
