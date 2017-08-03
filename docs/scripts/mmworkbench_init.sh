#!/usr/bin/env bash

# needed for pyenv install fix
xcode-select --install

set -e

NEEDS_DEP_INSTALL=0

function check_macos() {
	platform=$(uname)
	if [[ ! $platform == "Darwin" ]]; then
		echo This Installer is for MacOS only. Quitting.
		exit 1
	fi
}

function check_dependency {
	local command=$1
	echo -n "   " $command "... "

	# output yes or no
	if [[ `which $command` ]]; then
		if [[ $command == "java" ]]; then
			version=$(java -version 2>&1 | head -1 | awk '{print $3}' | sed "s/\"//g")
			if [[ $version == 1.8* ]]; then
				echo yes
			else
				echo older version $version found. 1.8+ needed.
				NEEDS_DEP_INSTALL=1
			fi
		else
			echo yes
		fi
	else
		echo no
		NEEDS_DEP_INSTALL=1
	fi
}

function install_dependency {
	local command=$1

	if [[ ! `which $command` ]]; then
		echo "   " $command
		if [[ $command == "brew" ]]; then
			/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
		elif [[ $command == "python" ]]; then
			brew install python
		elif [[ $command == "pip" ]]; then
			brew install python # this installs pip as well
		elif [[ $command == "java" ]]; then
			brew tap caskroom/cask
			brew cask install java
	    elif [[ $command == "elasticsearch" ]]; then
	    	brew install elasticsearch
			brew services start elasticsearch 
	    else
			brew install $command
		fi
	elif [[ $command == "java" ]]; then
		version=$(java -version 2>&1 | head -1 | awk '{print $3}' | sed "s/\"//g")
		if [[ ! $version == 1.8* ]]; then
			echo "   " $command ... 
			brew tap caskroom/cask
			brew cask install java
		fi
	fi
}

function check_virtualenv {
	echo -n "   " pyenv-virtualenv "... "
	if [[ `brew list pyenv-virtualenv 2> /dev/null` ]]; then
		echo yes
	else
		echo no - will be installed at the very end since a shell restart is required
	fi
}

function install_virtualenv {
	if [[ ! `brew list pyenv-virtualenv 2> /dev/null` ]]; then
		echo "   " Installing pyenv-virtualenv - MAKE SURE to follow the instructions at the end to add the provided lines to your profile and reload your shell
		brew install pyenv-virtualenv
	fi
}

# Gather Info
echo
echo The MindMeld Workbench Installer checks dependencies and installs them.
echo

check_macos

echo Checking dependencies already installed

check_dependency brew
check_dependency python
check_dependency pip
check_dependency pyenv

# pyenv-virtualenv
check_virtualenv

check_dependency java
check_dependency elasticsearch
echo done

if [[ ${NEEDS_DEP_INSTALL} == 1 ]]; then
	echo
	read -p "Do you want to install the missing dependencies (Y/n): " RESPONSE
	# lowercase
	RESPONSE=$(echo "$RESPONSE" | tr '[:upper:]' '[:lower:]')
	if [[ (! $RESPONSE == "") && (! $RESPONSE == "y") && (! $RESPONSE == "yes") ]]; then
		echo exiting
		exit 1
	fi

	# Install stuff
	echo
	echo Installing missing dependencies

	install_dependency brew
	install_dependency python
	install_dependency pip
	install_dependency pyenv
	install_dependency java
	install_dependency elasticsearch

	echo done
fi


echo
echo Setting up configuration files
read -p "   Enter mindmeld.com username: " USERNAME
echo -n "   Enter mindmeld.com password: "
read -s PASSWORD
echo

###
# .mmworkbench/config
###

mkdir -p ~/.mmworkbench
cat >~/.mmworkbench/config <<EOL
[mmworkbench]
mindmeld_url = https://mindmeld.com
username = $USERNAME
password = $PASSWORD
EOL

echo ~/.mmworkbench/config created.

####
# pip.conf
###

# create folder if not exists
mkdir -p ~/.pip

# if file already exists, make a backup
if test -f ~/.pip/pip.conf; then
	cp ~/.pip/pip.conf ~/.pip/pip.conf.backup
fi

# create file if not exists
touch ~/.pip/pip.conf

# this will wipe out your existing pip.conf
cat >~/.pip/pip.conf <<EOL
[global]
extra-index-url = https://$USERNAME:$PASSWORD@mindmeld.com/pypi
trusted-host = mindmeld.com
EOL

echo ~/.pip/pip.conf created.

echo
install_virtualenv