#!/usr/bin/env python

# https://www.vmware.com/support/developer/vix-api/vix112_vmrun_command.pdf

import ast
import json
import os
import subprocess
from pprint import pprint


def run_command(cmd):
    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )
    (so, se) = p.communicate()
    return (p.returncode, so, se)


def clean_ini_data(data):

    rdata = {}

    # cleanup
    data = data.replace('"', '')
    data = data.replace('TRUE', 'True')
    data = data.replace('true', 'True')
    data = data.replace('FALSE', 'False')
    data = data.replace('false', 'False')

    entries = data.split('\n')
    entries = [x.strip() for x in entries]
    entries = [x for x in entries if not x.startswith('#')]
    for entry in entries:
        parts = entry.split('=', 1)
        parts = [x.strip() for x in parts if x.strip()]
        if len(parts) > 1:

            key = parts[0]
            val = parts[1]

            # make ints/floats/bools
            try:
                val = ast.literal_eval(val)
            except:
                pass

            rdata[key] = val

    return rdata


def guestinfo(vmxpath):
    '''Use the vmx and vmrun to get metadata about the guest'''

    rdata = {
        'vmxfile': vmxpath,
        'ipaddress': None,
        'tools_state': None
    }

    if not os.path.isfile(vmxpath):
        return rdata

    with open(vmxpath, 'rb') as f:
        vmxdata = f.read()

    entries = clean_ini_data(vmxdata)
    for k,v in entries.items():
        rdata[k] = v

    # vmrun checkToolsState
    cmd = 'vmrun checkToolsState %s' % vmxpath
    (rc, so, se) = run_command(cmd)
    if rc == 0:
        rdata['toolsstate'] = so.strip()

    # vmrun getGuestIPAddress
    cmd = 'vmrun getGuestIPAddress %s' % vmxpath
    (rc, so, se) = run_command(cmd)

    if rc != 0 or 'tools are not running' in so.lower():
        if rdata['tools_state'] is None:
            rdata['tools_state'] = 'not running'
    else:
        rdata['ipaddress'] = so.strip()
        if rdata['tools_state'] is None:
            rdata['tools_state'] = 'running'

    return rdata


def parse_inventory_file():

    _vms = {}

    # cat ~/.vmware/inventory.vmls
    inventory_file = '~/.vmware/inventory.vmls'
    inventory_file = os.path.expanduser(inventory_file)

    with open(inventory_file, 'rb') as f:
        data = f.read()
    entries = clean_ini_data(data)

    for k, v in entries.items():
        if k.startswith('vmlist'):
            key = k.replace('vmlist', '')
            key_parts = key.split('.')
            number = key_parts[0]
            section = key_parts[1]

            if number not in _vms:
                _vms[number] = {}

            _vms[number][section] = v

    vms = {}
    for k, v in _vms.items():
        vms[v['config']] = v.copy()

    return vms


def listvms():

    vms = parse_inventory_file()

    cmd = 'vmrun list'
    (rc, so, se) = run_command(cmd)
    vmxpaths = so.split('\n')
    vmxpaths = [x.strip() for x in vmxpaths if x.strip()]
    vmxpaths = [x for x in vmxpaths if not x.startswith('Total running')]
    for vmxpath in vmxpaths:
        if vmxpath not in vms:
            vms[vmxpath] = {}

    for k, v in vms.items():

        # fetch data from the vmx
        guest_info = guestinfo(k)
        for k2, v2 in guest_info.items():
            vms[k][k2] = v2

    return vms


def main():

    vms = listvms()
    print(json.dumps(vms, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
