#!/bin/bash

ansible-playbook -vvvv -i 'localhost,' integration_test.yml

rm -rf *.retry

find ~/vmware

vmrun getGuestIPAddress /home/jtanner/vmware/testvm/testvm.vmx
