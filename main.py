#!/usr/env/python

from azure.common.credentials import UserPassCredentials
from azure.mgmt.resource.resources import ResourceManagementClient
from azure.mgmt.resource.resources.models import ResourceGroup
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import VirtualMachine, HardwareProfile, VirtualMachineSizeTypes, NetworkProfile, NetworkInterfaceReference, StorageProfile, OSDisk, DataDisk, CachingTypes, VirtualHardDisk, DiskCreateOptionTypes, ImageReference, OSProfile
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.network.models import VirtualNetwork, Subnet, AddressSpace, PublicIPAddress, IPAllocationMethod, NetworkInterface, NetworkInterfaceIPConfiguration
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.storage.models import StorageAccountCreateParameters, Kind, Sku, SkuName
import random
import getpass
import os
import sys
import re
import time


######Authenticating to Azure######
subscription_id = sys.argv[1]

# User defined vars
resource_group = sys.argv[2]
vm_name = sys.argv[3]

userName = raw_input('Please input your Azure AD username: ')
userPass = getpass.getpass('Please input your Azure AD password: ')

# User credentials
credentials = UserPassCredentials(
    userName,
    userPass,
)

# Defining configuration for connecting Clients
#res_config = ResourceManagementClientConfiguration(credentials, subscription_id)
#storage_config = StorageManagementClientConfiguration(credentials, subscription_id)
#compute_config = ComputeManagementClientConfiguration(credentials, subscription_id)
#network_config = NetworkManagementClientConfiguration(credentials, subscription_id)

# Defining Connecting Clients
res_client = ResourceManagementClient(credentials, subscription_id)
storage_client = StorageManagementClient(credentials, subscription_id)
compute_client = ComputeManagementClient(credentials, subscription_id)
network_client = NetworkManagementClient(credentials, subscription_id)

def vm_info():
    # Gather vm's information
    orig_vm = compute_client.virtual_machines.get(resource_group, vm_name)
    # OS Disk vhd
    os_vhd = orig_vm.storage_profile.os_disk.vhd.uri
    # VM size
    vm_size = orig_vm.hardware_profile.vm_size
    # Storage Account Name
    store_account = re.split('/|\.', orig_vm.storage_profile.os_disk.vhd.uri)[2]
    # Location
    vm_loc = orig_vm.location
    # Platform
    vm_plat = orig_vm.storage_profile.os_disk.os_type.name
    # OS Disk Image
    vm_image = 'Publisher:{0} Offer:{1} SKU:{2} Version:{3}'.format(
        orig_vm.storage_profile.image_reference.publisher,
        orig_vm.storage_profile.image_reference.offer,
        orig_vm.storage_profile.image_reference.sku,
        orig_vm.storage_profile.image_reference.version)
    # Network Interface
    network_interface = orig_vm.network_profile.network_interfaces[0].id

    # return a dictionary of values
    return {'os_vhd':os_vhd, 'vm_size':vm_size,
    'store_account':store_account, 'vm_loc':vm_loc,
    'vm_plat':vm_plat, 'vm_image':vm_image,
    'network_interface':network_interface,
    'vm_name':vm_name}

# Save all the vm_info information to global vars
orig_vm_name = vm_info()['vm_name']
orig_vm_location = vm_info()['vm_loc']
orig_vm_size = vm_info()['vm_size']
orig_vm_image = vm_info()['vm_image']
orig_vm_storage = vm_info()['store_account']
orig_vm_os_disk = vm_info()['os_vhd']
orig_vm_network_interface = vm_info()['network_interface']


def vm_output():
    f = open('{0}.txt'.format(orig_vm_name), 'wb')
    f.write('''VM Name: {0}\n
            VM Location: {1}\n
            VM Size: {2}\n
            VM Image: {3}\n
            VM Storage: {4}\n
            VM OS Disk: {5}\n
            VM Network Interface: {6}'''.format(
                        orig_vm_name,
                        orig_vm_location,
                        orig_vm_size,
                        orig_vm_image,
                        orig_vm_storage,
                        orig_vm_os_disk,
                        orig_vm_network_interface
                    )
            )
    f.close
    print('Output your original VM\'s metadata to {0}/{1}.txt'.format(
            os.path.dirname(os.path.realpath(__file__)),
            orig_vm_name)
            )

vm_output()

# Make a new VM
def temp_vm():
    # Generate random value to avoid duplicate resource group
    hash = random.getrandbits(16)

    # Defining vars
    base_name = 'rescue' + str(hash)

    storage_name = base_name
    group_name = base_name
    vm_name = base_name
    vnet_name = base_name
    subnet_name = base_name
    nic_name = base_name
    os_disk_name = base_name
    pub_ip_name = base_name
    computer_name = base_name
    admin_username='rescue'
    admin_password='P@ssWord91'
    region = orig_vm_location
    image_publisher = 'Canonical'
    image_offer = 'UbuntuServer'
    image_sku = '16.04.0-LTS'
    image_version = 'latest'

    # Helper function to create a network interface and vnet
    def create_network_interface(network_client, region, group_name, interface_name,
                                 network_name, subnet_name, ip_name):

        result = network_client.virtual_networks.create_or_update(
            group_name,
            network_name,
            VirtualNetwork(
                location=region,
                address_space=AddressSpace(
                    address_prefixes=[
                        '10.1.0.0/16',
                    ],
                ),
                subnets=[
                    Subnet(
                        name=subnet_name,
                        address_prefix='10.1.0.0/24',
                    ),
                ],
            ),
        )

        print('Creating Virtual Network...')
        result.wait() # async operation

        subnet = network_client.subnets.get(group_name, network_name, subnet_name)
        result = network_client.public_ip_addresses.create_or_update(
            group_name,
            ip_name,
            PublicIPAddress(
                location=region,
                public_ip_allocation_method=IPAllocationMethod.dynamic,
                idle_timeout_in_minutes=4,
            ),
        )

        print('Creating Subnet...')
        result.wait() # async operation

        # Creating Public IP
        public_ip_address = network_client.public_ip_addresses.get(group_name, ip_name)
        public_ip_id = public_ip_address.id

        print('Creating Public IP...')
        result.wait() # async operation

        result = network_client.network_interfaces.create_or_update(
            group_name,
            interface_name,
            NetworkInterface(
                location=region,
                ip_configurations=[
                    NetworkInterfaceIPConfiguration(
                        name='default',
                        private_ip_allocation_method=IPAllocationMethod.dynamic,
                        subnet=subnet,
                        public_ip_address=PublicIPAddress(
                            id=public_ip_id,
                        ),
                    ),
                ],
            ),
        )

        print('Creating Network Interface...')
        result.wait() # async operation

        network_interface = network_client.network_interfaces.get(
            group_name,
            interface_name,
        )

        return network_interface.id

    # 1. Create a resource group
    print('Creating resource group ' + base_name + '...')
    result = res_client.resource_groups.create_or_update(
        group_name,
        ResourceGroup(
            location=region,
        ),
    )

    # 2. Create a storage account
    print('Creating storage group ' + base_name + '...')
    result = storage_client.storage_accounts.create(
        group_name,
        storage_name,
        StorageAccountCreateParameters(
            location=region,
	    sku=Sku(SkuName.premium_lrs),
            kind=Kind.storage,
        ),
    )
    result.result()

    # 3. Create the network interface using a helper function (defined below)
    nic_id = create_network_interface(
        network_client,
        region,
        group_name,
        nic_name,
        vnet_name,
        subnet_name,
        pub_ip_name,
    )

    # 4. Create the virtual machine
    print('Creating temporary VM ' + vm_name + '...')
    result = compute_client.virtual_machines.create_or_update(
        group_name,
        vm_name,
        VirtualMachine(
            location=region,
            os_profile=OSProfile(
                admin_username=admin_username,
                admin_password=admin_password,
                computer_name=computer_name,
            ),
            hardware_profile=HardwareProfile(
                vm_size='Standard_DS1_v2'
            ),
            network_profile=NetworkProfile(
                network_interfaces=[
                    NetworkInterfaceReference(
                        id=nic_id,
                    ),
                ],
            ),
            storage_profile=StorageProfile(
                os_disk=OSDisk(
                    caching=CachingTypes.none,
                    create_option=DiskCreateOptionTypes.from_image,
                    name=os_disk_name,
                    vhd=VirtualHardDisk(
                        uri='https://{0}.blob.core.windows.net/vhds/{1}.vhd'.format(
                            storage_name,
                            os_disk_name,
                        ),
                    ),
                ),
                image_reference = ImageReference(
                    publisher=image_publisher,
                    offer=image_offer,
                    sku=image_sku,
                    version=image_version,
                ),
            ),
        ),
    )
    result.wait() # async operation

    # Display the public ip address
    # You can now connect to the machine using SSH
    public_ip_address = network_client.public_ip_addresses.get(group_name, pub_ip_name)
    print('\n' + vm_name + ' has started.')
    print('VM\'s public IP is {}'.format(public_ip_address.ip_address))
    print('SSH Username: ' + admin_username)
    print('SSH Password ' + admin_password)
    print('ssh ' + admin_username + '@' + public_ip_address.ip_address)

    # The process of shutting down the VM, deleting it, then removing/attaching OS disk to the temp
    def disk_attach():
        # Delete VM
        print('Deleting VM and freeing OS disk from ' + orig_vm_name)
        print('OS Disk Location ' + orig_vm_os_disk)
        result = compute_client.virtual_machines.delete(sys.argv[2], orig_vm_name)
        result.wait()
        # Ensures no lingering lease issues
        time.sleep(5)

        # Attach OS disk to temporary VM
        print('Attaching original OS disk to {0}'.format(vm_name))
        result = compute_client.virtual_machines.create_or_update(
            group_name,
            vm_name,
            VirtualMachine(
                location=orig_vm_location,
                storage_profile=StorageProfile(
                    data_disks=[DataDisk(
                        lun=0,
                        caching=CachingTypes.none,
                        create_option=DiskCreateOptionTypes.attach,
                        name=orig_vm_name,
                        vhd=VirtualHardDisk(
                            uri=orig_vm_os_disk
                            )
                                    )]
                                )
                            )
                        )
        result.wait()
    disk_attach()
temp_vm()
