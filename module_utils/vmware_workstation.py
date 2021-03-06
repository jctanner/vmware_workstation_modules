#!/usr/bin/env python

# https://www.vmware.com/support/developer/vix-api/vix112_vmrun_command.pdf

import ast
import os
import shutil
import subprocess


def initchildproc():
    # http://stackoverflow.com/a/36187216
    os.setpgrp()
    os.umask(022)


def run_command(cmd, use_unsafe_shell=False, umask=False):

    kwargs = {
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE,
        'shell': use_unsafe_shell
    }

    if umask:
        kwargs['preexec_fn'] = initchildproc

    p = subprocess.Popen(cmd, **kwargs)
    (so, se) = p.communicate()
    return (p.returncode, so, se)


class VMwareWorkstationHelper(object):

    def __init__(self, module):
        self.module = module
        self.vmware_dir = os.path.expanduser('~/vmware')
        self.log = []
        self.result = {
            'failed': False,
            'changed': False,
            'log': []
        }

    def run_command_with_log(self, cmd):
        self.result['log'].append(cmd)
        (rc, so, se) = run_command(cmd, use_unsafe_shell=True, umask=True)
        self.result['log'].append(rc)
        self.result['log'].append(so)
        self.result['log'].append(se)
        return (rc, so, se)

    def fail(self, msg=None):
        self.module.fail_json(msg=msg, meta=self.log)

    @staticmethod
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

    @staticmethod
    def guestinfo(vmxpath):
        '''Use the vmx and vmrun to get metadata about the guest'''

        rdata = {
            'vmxfile': vmxpath,
            'ipaddress': None,
            'tools_state': None,
            'config': vmxpath
        }

        if not os.path.isfile(vmxpath):
            return rdata

        with open(vmxpath, 'rb') as f:
            vmxdata = f.read()

        entries = VMwareWorkstationHelper.clean_ini_data(vmxdata)
        for k,v in entries.items():
            rdata[k] = v

        # vmrun checkToolsState
        cmd = 'vmrun checkToolsState %s' % vmxpath
        (rc, so, se) = run_command(cmd, use_unsafe_shell=True)
        if rc == 0:
            rdata['toolsstate'] = so.strip()

        # vmrun getGuestIPAddress
        cmd = 'vmrun getGuestIPAddress %s' % vmxpath
        (rc, so, se) = run_command(cmd, use_unsafe_shell=True)

        if rc != 0 or 'tools are not running' in so.lower():
            if rdata['tools_state'] is None:
                rdata['tools_state'] = 'not running'
        else:
            rdata['ipaddress'] = so.strip()
            if rdata['tools_state'] is None:
                rdata['tools_state'] = 'running'

        return rdata

    @staticmethod
    def parse_inventory_file():

        _vms = {}

        # cat ~/.vmware/inventory.vmls
        inventory_file = '~/.vmware/inventory.vmls'
        inventory_file = os.path.expanduser(inventory_file)

        with open(inventory_file, 'rb') as f:
            data = f.read()
        entries = VMwareWorkstationHelper.clean_ini_data(data)

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

    @staticmethod
    def listvms(filter_unknown=True):

        vms = VMwareWorkstationHelper.parse_inventory_file()

        cmd = 'vmrun list'
        (rc, so, se) = run_command(cmd, use_unsafe_shell=True)
        vmxpaths = so.split('\n')
        vmxpaths = [x.strip() for x in vmxpaths if x.strip()]
        vmxpaths = [x for x in vmxpaths if not x.startswith('Total running')]
        for vmxpath in vmxpaths:
            if vmxpath not in vms:
                vms[vmxpath] = {}

        # make a list of basedirs for known VMs
        vmxparents = []
        for k, v in vms.items():
            config = v.get('config')
            if config:
                parent = os.path.dirname(config)
                parent = os.path.dirname(parent)
                if parent not in vmxparents:
                    vmxparents.append(parent)

        # find any vms not listed by the commands
        for vmxp in vmxparents:
            for root, dirs, files in os.walk(vmxp):
                vmxfiles = [x for x in files if x.endswith('.vmx')]
                if vmxfiles:
                    vmxpath = os.path.join(root, vmxfiles[0])
                    if vmxpath not in vms:
                        vms[vmxpath] = {}

        for k, v in vms.items():
            # fetch data from the vmx
            guest_info = VMwareWorkstationHelper.guestinfo(k)
            for k2, v2 in guest_info.items():
                vms[k][k2] = v2
            if not vms[k].get('config'):
                vms[k]['config'] = k

        # get rid of anything that is in a bad state
        if filter_unknown:
            to_remove = []
            for k, v in vms.items():
                config = v.get('config')
                if not config or not os.path.isfile(config):
                    to_remove.append(k)
            if to_remove:
                for tr in to_remove:
                    vms.pop(tr, None)

        return vms

    @staticmethod
    def get_workstation_vm_by_name(name, filter_unknown=True):

        vms = VMwareWorkstationHelper.listvms(filter_unknown=filter_unknown)
        for k, v in vms.items():
            if v.get('DisplayName') == name or v.get('displayname') == name:
                return v
            else:
                pass

        vmxpath = os.path.expanduser('~/vmware')
        vmxpath = os.path.join(vmxpath, name, '%s.vmx' % name)
        if os.path.isfile(vmxpath):
            guest_info = VMwareWorkstationHelper.guestinfo(vmxpath)
            if guest_info:
                guest_info['config'] = vmxpath
                return guest_info

        return None

    @staticmethod
    def get_ova_display_name(ovafile):
        name = None
        cmd = 'ovftool %s' % ovafile
        (rc, so, se) = run_command(cmd, use_unsafe_shell=True)
        lines = so.split('\n')
        for line in lines:
            if line.startswith('Name: '):
                name = line.split(None, 1)[-1].strip()
        return name

    def clone_vm(self, name, template):

        vmxdir = os.path.expanduser('~/vmware')
        vmxdir = os.path.join(vmxdir, name)
        self.result['vmxdir'] = vmxdir
        vmxpath = os.path.join(vmxdir, '%s.vmx' % name)
        self.result['vmxpath'] = vmxdir

        template_vm = VMwareWorkstationHelper.get_workstation_vm_by_name(
            template,
            filter_unknown=False
        )

        if not template_vm:
            self.fail(msg='%s template not found' % template)

        template_vmxpath = template_vm['config']

        if not os.path.isdir(vmxdir):
            os.makedirs(vmxdir)

        cmd = 'vmrun -T ws clone %s %s full -cloneName="%s"' % \
            (template_vmxpath, vmxpath, name)
        (rc, so, se) = self.run_command_with_log(cmd)

        if rc == 0:
            return True
        else:
            self.fail(msg='Cloning %s to %s failed' % (template_vmxpath, vmxpath))

    def import_ova(self, ovafile, accept_eula=False):

        ovafile = os.path.expanduser(ovafile)

        cmd = ['ovftool']
        if accept_eula:
            cmd.append('--acceptAllEulas')
        cmd.append('--lax')
        cmd.append(ovafile)
        cmd.append(self.vmware_dir)
        cmd = ' '.join(cmd)
        self.log.append(cmd)
        (rc, so, se) = run_command(cmd, use_unsafe_shell=True)
        self.log.append(rc)
        self.log.append(so)
        self.log.append(se)

        if rc == 0:
            return True
        else:
            self.fail(msg='Importing %s failed' % (ovafile))


    def delete_vm(self, vmxpath):

        self.result['changed'] = True

        vmxdir = os.path.dirname(vmxpath)
        cmd = 'vmrun deleteVm %s' % vmxpath
        (rc, so, se) = self.run_command_with_log(cmd)

        if rc == 0 and os.path.isdir(vmxdir):
            shutil.rmtree(vmxdir)
            return True
        else:
            self.fail(msg='Destroying %s failed' % vmxpath)

    def stop_vm(self, vmxpath):

        self.result['changed'] = True

        cmd = 'vmrun stop %s' % vmxpath
        (rc, so, se) = self.run_command_with_log(cmd)

        if rc == 0:
            return True
        else:
            return False

    def start_vm(self, vmxpath):

        # need to set umask 022 to make this work
        # https://groups.google.com/forum/#!topic/vagrant-up/S3mpns57OAk

        self.result['changed'] = True

        cmd = 'vmrun start %s nogui' % vmxpath
        (rc, so, se) = self.run_command_with_log(cmd)

        if rc == 0:
            return True
        else:
            self.fail(msg='Stopping %s failed' % vmxpath)
