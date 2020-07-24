import sys
import os
import logging
import uuid
import json
import argparse
from datetime import datetime
from tempfile import mkstemp
from io import StringIO
from base64 import b64encode
from sh import az, ssh_keygen, watch

TEMPLATE_FILE_PATH = "template_vm.json"
RESOURCE_GROUP_PREFIX = "vm_test_"
VM_USERNAME = "vmuser"

VM_INIT_SCRIPT = """
#!/bin/bash
echo "Set script to fail if command in script returns non zero return code"
set -exu pipefall
echo "Updating packages ..."
apt-get -y update
echo "Updated packages."
echo "cat /etc/apt/sources.list"
cat /etc/apt/sources.list
echo "ls -la /etc/apt/sources.list.d/"
ls -la /etc/apt/sources.list.d/
"""

def generate_random_sshkey():
    _, tmp_file = mkstemp()
    os.remove(tmp_file)
    ssh_keygen(f"-t rsa -b 4096 -f {tmp_file} -q -N none".split())
    buf = StringIO()
    ssh_keygen(f"-f {tmp_file} -P none -y".split(), _out=buf)
    return buf.getvalue()


if __name__ == "__main__":
    # set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # parse args
    parser = argparse.ArgumentParser(description='VM Creation Script.')
    parser.add_argument('--subscription', type=str,
                        help='The Azure Subscription Id to be used to create the VMs')
    parser.add_argument('--vm-count', type=int, default='20',
                        help='The number of VMs to create (default: 20)')
    parser.add_argument('--location', type=str, default='westus2',
                        help='The Azure region to create VMs in (default: westus2)')
    parser.add_argument('--vm-size', type=str, default='Standard_F2s_v2',
                    help='The VM size to use. (default: Standard_F2s_v2)')
    args = parser.parse_args()
    subscription = args.subscription or input("Please enter a subscription id: ")
    location = args.location
    vm_count = args.vm_count
    vm_size = args.vm_size
    logging.info(f"SUBSCRIPTION={subscription}")
    logging.info(f"LOCATION={location}")
    logging.info(f"VM COUNT={vm_count}")
    logging.info(f"VM SIZE={vm_size}")

    # azure login
    logging.info("Please log in to Azure...")
    resource_group = f"{RESOURCE_GROUP_PREFIX}{datetime.now().strftime('%d_%m_%Y_%H')}"
    az('login --use-device-code --output none'.split(), _out=sys.stdout, _err=sys.stderr)
    az(f'account set --subscription {subscription} --output none'.split(), _out=sys.stdout, _err=sys.stderr)

    # create resource group
    az(f'group create -l {location} --name {resource_group}'.split(), _out=sys.stdout, _err=sys.stderr)

    # create the vms
    for i in range(0, vm_count):
        vm_name = str(uuid.uuid4())
        deployment_name = f"Create-LinuxVm-{vm_name}"
        template_params = dict()
        template_params['adminUsername'] = {"value": VM_USERNAME}
        template_params['adminPublicKeyPath'] = {"value": f"/home/{VM_USERNAME}/.ssh/authorized_keys"}
        template_params['adminPublicKey'] = {"value": generate_random_sshkey()}
        template_params['location'] = {"value": location}
        template_params['virtualMachineName'] = {"value": vm_name}
        template_params['osDiskName'] = {"value": f"{vm_name}-disk"}
        template_params['networkInterfaceName'] = {"value": f"{vm_name}-nic"}
        template_params['virtualMachineSize'] = {"value": vm_size}
        template_params['vmSetupScript'] = {"value": b64encode(VM_INIT_SCRIPT.encode('utf-8')).decode('utf-8')}
        template_params_as_json = json.dumps(template_params)
        az(['deployment', 'group', 'create', '--resource-group', resource_group, '--mode', 'Incremental', '--name', deployment_name, '--no-wait', '--template-file', TEMPLATE_FILE_PATH, '--parameters', template_params_as_json], _out=sys.stdout, _err=sys.stderr)
        logging.info(f"Deployed {i+1}/{vm_count}")

    # watch deployment status
    logging.info("Watching the status of the deployments (press ctrl + C to end)...")
    watch(f"-n 15 az deployment group list --resource-group {resource_group} -otable".split(), _out=sys.stdout, _err=sys.stderr)
