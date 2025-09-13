#!/usr/bin/env sh

set -eu
echo "getting dot files"
sudo apt install -y git
git clone https://github.com/kloki/dotfiles.git
cp -r dotfiles/* ~/
rm dotfiles/ -r
cd ~
./setup.sh
