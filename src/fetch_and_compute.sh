clear
cd "./python/binance/data/"
python3 "keep-fetching.py" --once
cd ../../../../
cd ./src/dist
pwd
python3 "recompute.py" 
cd ..
echo " "
echo "Data fetched and computed. Please refresh localhost:8000 now"