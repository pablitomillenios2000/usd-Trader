#!/bin/bash

clear
echo ""

# Define the port
PORT=8000

# Check if the port is already in use
if lsof -i :$PORT > /dev/null; then
    echo "Server is already running on port $PORT."
else
    echo "Starting server on port $PORT..."
    echo "starting the web server and disowning it from the terminal"
    cd src/view
    python3 -m http.server > /dev/null 2>&1 &
    ps aux | grep "pthon3 -m http.server"
    disown $(ps aux | grep "[p]ython3 -m http.server" | awk '{print $2}')
    cd ../../
    echo "Server started successfully."
fi

echo ""
echo "starting the permanent data fetcher"
rm ./src/start_protocol/keep_fetching.log
cd src/python/binance/data/
./keep-fetching.py > ../../../start_protocol/keep_fetching.log & disown $!
cd ../../../../

echo ""
echo "starting the recompute bucle"
rm ./src/start_protocol/bucle.log
cd ./src/dist
nohup ./bucle.py > ../start_protocol/bucle.log 2>&1 &

echo ""



