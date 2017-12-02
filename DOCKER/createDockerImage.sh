#!/bin/bash

rm -rf BibiImageCreator/

git clone https://github.com/awalende/BibiImageCreator.git

if [ ! -f packer ]; then
	echo 'Downloading packer 1.1.2'
	wget https://releases.hashicorp.com/packer/1.1.2/packer_1.1.2_linux_amd64.zip?_ga=2.180224551.2048116518.1512220632-1111468850.1512076026
	mv packer_1.1.2_linux_amd64.zip?_ga=2.180224551.2048116518.1512220632-1111468850.1512076026 packer.zip
	unzip packer.zip
	rm packer.zip
fi

docker build -t bibicreator .
