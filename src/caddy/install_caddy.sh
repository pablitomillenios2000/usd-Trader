sudo curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo apt-key add -
sudo curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy.list


sudo apt update
sudo apt install caddy -y


sudo systemctl start caddy
sudo systemctl enable caddy


echo "please edit: /etc/caddy/Caddyfile with sudo nano"
