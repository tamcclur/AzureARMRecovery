# AzureARMRecovery

## Description

This is a python based script that will automate the recovery of an unreachable ARM Linux VM in Azure. This script aims to automate the following:

1. Outputting metadata information of your VM for later recreation
2. Deleting the VM to free the disks leased to it
3. Creating a temporary VM
4. Attaching the OS disk to the temporary VM for troubleshooting

## Prerequisites

* This only works with ARM (Azure Resource Manager | V2) Linux VMs
* This is tested with Python 2.7.x
* You will need adminstrator privileges for the subscription
* MFA authentication <strong>is not supported</strong>
* A C compiler is needed for some python modules

## Disclaimer

<strong>This will start a Standard_DS1_v2 VM in a resource group. Please be aware this will incur minor charges.</strong>
Please also note this build is <strong>extremely</strong> experimental and has only been tested with a limited range of environments. I also do not have local error checking/validation, only Azure SDK errors.

## Usage

Clone the project to your own workspace

`git clone https://github.com/tamcclur/AzureARMRecovery.git`

Install the required packages in your virtualenv or site

`pip install -r requirements.txt`

Run the script as follows

`python main.py <subscription_id> <resource_group_name> <vm_name>`

The script will then ask you to authenticate with your AD username and password. After authenticating the script will go to work and output the SSH details of the new rescue VM.

SSH to the rescue VM and `lsblk` to see your OS disk attached at `/dev/sdc`

Mount the OS partition

`/dev/sdc[0-9]`

## FAQ

Q: When doing `pip install -r requirements.txt` I get a variation of the following error:

```
Command "/usr/bin/python -u -c "import setuptools, tokenize;__file__='/tmp/pip-build-4rKyp4/cryptography/setup.py';exec(compile(getattr(tokenize, 'open', open)(__file__).read().replace('\r\n', '\n'), __file__, 'exec'))" install --record /tmp/pip-Tbbp6S-record/install-record.txt --single-version-externally-managed --compile" failed with error code 1 in /tmp/pip-build-4rKyp4/cryptography/
```

A: This most likely due to a missing package, specifically `libssl-dev` on Debian and `openssl-devel` for RedHat based distros. Install this package with your package manager and re-run `pip install -r requirements.txt`.
