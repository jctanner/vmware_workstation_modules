#!/bin/bash

# forces ssh to use password
export SSH_AUTH_SOCK=""
SSH_AUTH_SOCK=""

ansible-playbook -vvvv -i 'localhost,' deploy_esx.yml

rm -rf *.retry
