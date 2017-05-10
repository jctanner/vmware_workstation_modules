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
module: vmware_ws_guest_facts
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
   name:
        description:
            - Name of the VM to work with
        required: True
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

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, type='str'),
        ),
        supports_check_mode=True,
    )

    vmwh = VMwareWorkstationHelper(module)
    vm = vmwh.get_workstation_vm_by_name(
        module.params['name'],
        filter_unknown=False
    )

    if vm:
        module.exit_json(**vm)
    else:
        module.fail_json(**{})


if __name__ == '__main__':
    main()
