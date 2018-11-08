#!/usr/bin/env python
import os
import argparse
import sys
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.storage.models import StorageAccountCreateParameters
from azure.cosmosdb.table import TableService, Entity
from azservices import _get_storage_account_key

SUB_ID = os.environ['ACCOUNT_ID']
APP_ID = os.environ['APP_ID']
TENANT_ID = os.environ['TENANT_ID']
APP_SECRET = os.environ['APP_SECRET']
RG_NAME = os.environ['GROUP_NAME']
SA_NAME = os.environ['SWARM_INFO_STORAGE_ACCOUNT']

def get_storage_key():
    global SUB_ID, TENANT_ID, APP_ID, APP_SECRET, RG_NAME, SA_NAME
    cred = ServicePrincipalCredentials(
        client_id=APP_ID,
        secret=APP_SECRET,
        tenant=TENANT_ID
    )

    storage_client = StorageManagementClient(cred, SUB_ID)

    return _get_storage_account_key(storage_client, RG_NAME, SA_NAME)

def main():
    key = get_storage_key()
    print(u'{}'.format(key))

if __name__ == "__main__":
    main()
