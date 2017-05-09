#!/bin/bash

# forces ssh to use password
export SSH_AUTH_SOCK=""
SSH_AUTH_SOCK=""

# allows promiscuous mode
sudo chmod a+rw /dev/vmnet*

ansible-playbook -vvvv -i 'localhost,' deploy_esx.yml

rm -rf *.retry
