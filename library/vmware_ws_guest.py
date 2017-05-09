#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This module is also sponsored by E.T.A.I. (www.etai.fr)
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: vmware_ws_guest
short_description: Manages virtual machines in vmware workstation
description:
    - Create new virtual machines (from templates or OVAs)
    - Power on/power off/restart a virtual machine
    - Modify, rename or remove a virtual machine
version_added: 2.4
author:
    - James Tanner (@jctanner) <tanner.jc@gmail.com>
notes:
    - Tested on vmware workstation 12.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
   state:
        description:
            - What state should the virtual machine be in?
            - If C(state) is set to C(present) and VM exists, ensure the VM configuration conforms to task arguments
        required: True
        choices: ['present', 'absent', 'poweredon', 'poweredoff', 'restarted', 'suspended', 'shutdownguest', 'rebootguest']
   name:
        description:
            - Name of the VM to work with
        required: True
   template:
        description:
            - Template used to create VM.
            - If this value is not set, VM is created without using a template.
            - If the VM exists already this setting will be ignored.
   ova:
        description:
            - OVA file to import.
            - If the VM exists already this setting will be ignored.
'''

EXAMPLES = '''
'''

RETURN = """
"""

import os
import shutil
import time

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.six import iteritems
from ansible.module_utils.vmware_workstation import VMwareWorkstationHelper


def main():

    state_options = [
        'present',
        'absent'
    ]

    power_options = [
        'poweredon',
        'poweredoff',
        'restarted',
        'suspended',
        'shutdownguest',
        'rebootguest'
    ]

    create_options = [
        'poweredon',
        'poweredoff',
        'present',
        'restarted',
        'suspended'
    ]

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(
                required=False,
                choices=state_options + power_options,
                default='present'),
            template_src=dict(type='str', aliases=['template']),
            ova=dict(type='str'),
            name=dict(required=True, type='str'),
        ),
        supports_check_mode=True,
    )

    vmwh = VMwareWorkstationHelper(module)

    result = {
        'failed': False,
        'changed': False,
        'operations': []
    }

    vm = vmwh.get_workstation_vm_by_name(
        module.params['name'],
        filter_unknown=False
    )

    if vm:
        # VM already exists

        if module.params['state'] == 'absent':

            # has to be poweredoff first
            vmwh.stop_vm(vm['config'])

            # destroy it
            vmwh.delete_vm(vm['config'])
            time.sleep(5)

            vmxdir = vm['config']
            vmxdir = os.path.dirname(vmxdir)
            if os.path.isdir(vmxdir):
                shutil.rmtree(vmxdir)

        elif module.params['state'] == 'present':

            vmwh.result['instances'] = []
            vmwh.result['instances'].append(vm)

        elif module.params['state'] in power_options:

            if module.params['state'] == 'poweredon':

                if not os.path.isfile(vm['config']):
                    module.fail_json(msg="VMX(%s) does not exist, poweron will fail" % vm['config'], meta=result)

                vmwh.start_vm(vm['config'])

            new_vm = vmwh.get_workstation_vm_by_name(module.params['name'])
            vmwh.result['instances'] = []
            vmwh.result['instances'].append(new_vm)

        else:
            # This should not happen
            assert False

    else:
        # VM doesn't exist

        if module.params['state'] in create_options:

            new_vm = None

            if module.params['template_src']:

                # Clone it ...
                vmwh.clone_vm(module.params['name'], module.params['template'])
                new_vm = vmwh.get_workstation_vm_by_name(module.params['name'])

            elif module.params['ova']:

                # Import it ...
                ova_name = vmwh.get_ova_display_name(module.params['ova'])
                ova_vm = vmwh.get_workstation_vm_by_name(
                    ova_name,
                    filter_unknown=False
                )

                if not ova_vm:
                    ova_vm = vmwh.import_ova(module.params['ova'], accept_eula=True)
                    time.sleep(5)

                new_vm = ova_vm

            if module.params['state'] == 'poweredon':

                vmwh.start_vm(new_vm['config'])

                while not new_vm['ipaddress']:
                    time.sleep(10)
                    new_vm = vmwh.get_workstation_vm_by_name(module.params['name'])

            vmwh.result['instances'] = []
            vmwh.result['instances'].append(new_vm)

    if vmwh.result['failed']:
        module.fail_json(**vmwh.result)
    else:
        module.exit_json(**vmwh.result)


if __name__ == '__main__':
    main()
