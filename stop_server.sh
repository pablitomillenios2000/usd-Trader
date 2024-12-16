clear
echo ""
echo "Stopping the server background processes"
echo ""
echo "Leaving the webserver running"
echo ""

pkill -f "python3 ./bucle.py"
pkill -f "python3 ./keep-fetching.py"

