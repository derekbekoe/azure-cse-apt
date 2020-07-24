# azure-cse-apt

## Usage

```bash
$ python app.py -h

usage: app.py [-h] [--subscription SUBSCRIPTION] [--vm-count VM_COUNT]
              [--location LOCATION] [--vm-size VM_SIZE]

VM Creation Script.

optional arguments:
  -h, --help            show this help message and exit
  --subscription SUBSCRIPTION
                        The Azure Subscription Id to be used to create the VMs
  --vm-count VM_COUNT   The number of VMs to create (default: 20)
  --location LOCATION   The Azure region to create VMs in (default: westus2)
  --vm-size VM_SIZE     The VM size to use. (default: Standard_F2s_v2)
```

The script will create a resource group with the prefix vm_test_ and deploy VMs into it.

At the end, it will poll for status so you can see the success/fail rate.

How to view deployment status and errors in Azure Portal? - https://docs.microsoft.com/en-us/azure/azure-resource-manager/templates/deployment-history?tabs=azure-portal

If you attempt to deploy too many VMs in your subscription, you may hit Azure Quota errors.

## Run in docker (recommended)

```bash
docker build -t vm-test .
docker run -it vm-test
```
