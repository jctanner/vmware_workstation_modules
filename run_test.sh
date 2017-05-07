#!/bin/bash

ansible-playbook -vvvv -i 'localhost,' integration_test.yml

rm -rf *.retry
