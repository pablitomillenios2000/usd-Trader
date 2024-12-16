clear

echo "Diagnosing the following processes to be up:"
echo ""
ps aux | grep "python3 -m http.server" | grep -v grep
ps aux | grep "python3 ./keep-fetching.py" | grep -v grep
ps aux | grep "python3 ./bucle.py" | grep -v grep
echo ""
