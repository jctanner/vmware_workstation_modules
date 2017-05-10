#!/bin/bash

# forces ssh to use password
export SSH_AUTH_SOCK=""
SSH_AUTH_SOCK=""

ansible-playbook -vvvv -i 'localhost,' rehome_esx.yml

rm -rf *.retry
