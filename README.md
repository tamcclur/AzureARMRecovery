# AzureARMRecovery

## Description

This is a python based script that will automate the recovery of an unreachable ARM Linux VM in Azure. This script aims to automate the following:

1. Shutting down your VM
2. Deleting the VM to free the disks leased to it
3. Creating a temporary VM
4. Attaching the OS disk to the temporary VM for troubleshooting

## Prerequisites

* This only works with ARM (Azure Resource Manager | V2) Linux VMs
* This is tested with Python 2.7.x
* You will need adminstrator privileges for the subscription
* MFA authentication <strong>is not supported</support>

## Disclaimer

<strong>This will start a Standard_DS1_v2 VM in a resource group. Please be aware this will incur minor charges.</strong>

## Usage

Clone the project to your own workspace

`git clone https://github.com/tamcclur/AzureARMRecovery.git`

Install the required packages in your virtualenv or site

`pip install -r requirements.txt`

Run the script as follows

`python main.py <subscription_id> <resource_group_name> <vm_name>`

The script will then as you to authenticate with your AD username and password. After authenticating the script will go to work and output the SSH details of the new rescue VM.

SSH to the rescue VM and `lsblk` to see your OS disk attached at `/dev/sdc`

Mount the OS partition

`/dev/sdc[0-9]`
