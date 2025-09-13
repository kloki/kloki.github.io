#!/usr/bin/env sh

set -eu
echo "getting dot files"
sudo apt install -y git
git clone git@github.com:kloki/dotfiles.git
cp -r dotfiles/. ~/
rm dotfiles/ -rf
cd ~
./setup.sh
