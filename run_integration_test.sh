#!/bin/bash

# forces ssh to use password
export SSH_AUTH_SOCK=""
SSH_AUTH_SOCK=""

ansible-playbook -vvvv -i 'localhost,' integration_test.yml

rm -rf *.retry

find ~/vmware

vmrun getGuestIPAddress /home/jtanner/vmware/testvm/testvm.vmx
