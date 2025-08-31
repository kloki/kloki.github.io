#!/usr/bin/env sh

set -eu
echo "installing dependencies"
sudo apt install -y git gcc make

echo "installing keyd"
git clone https://github.com/rvaiya/keyd
cd keyd
make && sudo make install
cd ../
rm keyd -rf


echo "setting up layout"
git clone https://github.com/kloki/my-keyd.git
sudo cp ./my-keyd/default.conf /etc/keyd/
rm kmy-keyd -rf


echo "starting keyd"
sudo systemctl start keyd

echo "Run: 'sudo systemctl stop keyd' to stop"
echo "Run: 'sudo systemctl start keyd' to start"
