# Setting up the ssh based vpn for remote clients
sshuttle -v -r jtanner@fedmac 192.168.49.0/24

# Govc
https://github.com/vmware/govmomi/tree/master/govc

# Get logs with govc
GOVC_INSECURE=1 GOVC_USERNAME=administrator@vsphere.local GOVC_PASSWORD=VMware1! GOVC_URL=https://192.168.49.132/sdk ./govc_linux_amd64 logs

# Add host to cluster with govc
GOVC_INSECURE=1 GOVC_USERNAME=administrator@vsphere.local GOVC_PASSWORD=VMware1! GOVC_URL=https://192.168.49.132/sdk ./govc_linux_amd64 host.add -dc=cluster1 -hostname=192.168.49.133 -username=root --password=vmware1234 -noverify
[09-05-17 21:53:52] adding 192.168.49.133 to folder /cluster1/host... OK

