#!/bin/bash

# http://www.virtuallyghetto.com/2013/12/how-to-properly-clone-nested-esxi-vm.html

# "msg": "(vim.fault.ConflictingDatastoreFound) {\n
#   dynamicType = <unset>,\n
#   dynamicProperty = (vmodl.DynamicProperty) [],\n
#   msg = \"Datastore 'datastore1' conflicts with an existing datastore in the datacenter that has the same URL (ds:///vmfs/volumes/5912145f-ed1def29-b024-000c29d8818b/), but is backed by different physical storage.\",\n
#   faultCause = <unset>,\n
#   faultMessage = (vmodl.LocalizableMessage) [],\n
#   name = 'datastore1',\n   url = 'ds:///vmfs/volumes/5912145f-ed1def29-b024-000c29d8818b/'\n}"

# http://www.virtuallyghetto.com/2013/12/how-to-properly-clone-nested-esxi-vm.html#comment-27933
# esxcli system maintenanceMode set --enable true --timeout=1
# esxcli storage filesystem unmount -l datastore
# vmkfstools -P /vmfs/volumes/datastore1 | fgrep mpx | awk '{print $1}'
# vmkfstools -C vmfs5 -b 1m -S datastorex /vmfs/devices/disks/mpx.vmhba1:C0:T0:L0:3
# esxcli system shutdown reboot
# esxcli system maintenanceMode set --enable false --timeout=1

# esxcli storage filesystem list

ESXHOST=$1
ESXUSER=$2
ESXPASS=$3

echo "HOST: $ESXHOST"
echo "USER: $ESXUSER"
echo "PASS: $ESXPASS"

export SSH_AUTH_SOCK=""
SSHBIN="sshpass -p $ESXPASS ssh $ESXUSER@$ESXHOST"

# Get the list of aliases
DSNAME=$($SSHBIN esxcli storage filesystem list | grep datastore | awk '{print $1}')
echo $DSNAME

# Unmount it if known
if [ ! -z $DSNAME ]; then
    $SSHBIN esxcli storage filesystem unmount -l $DSNAME
else
    echo "DS is not mounted, skipping unmount"
fi

# Set maintenance mode
$SSHBIN esxcli system maintenanceMode set --enable true --timeout=1

# Get the mpx deviceid
DSPATH=$($SSHBIN ls /vmfs/volumes/datastore1)
if [ ! -z $DSPATH ]; then
    MPX=$($SSHBIN vmkfstools -P $DSPATH | grep mpx | awk '{print $1 }')
else
    MPX="mpx.vmhba1:C0:T0:L0:3"
fi

# Format the device
$SSHBIN vmkfstools -C vmfs5 -b 1m -S datastore1 /vmfs/devices/disks/$MPX

# Reboot
$SSHBIN esxcli system shutdown reboot -r format

sleep 120

# Exit maintenance mode
$SSHBIN esxcli system maintenanceMode set --enable false --timeout=1
