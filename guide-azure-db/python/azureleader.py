#!/usr/bin/env python
import os
import argparse
import sys
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.storage.models import StorageAccountCreateParameters
from azure.cosmosdb.table import TableService, Entity
from azservices import create_table_service

PARTITION_NAME = 'tokens'
ROW_ID = '1'
TBL_NAME = 'swarminfo'

SUB_ID = os.environ['ACCOUNT_ID']
TENANT_ID = os.environ['TENANT_ID']
APP_ID = os.environ['APP_ID']
APP_SECRET = os.environ['APP_SECRET']
RG_NAME = os.environ['GROUP_NAME']
SA_NAME = os.environ['SWARM_INFO_STORAGE_ACCOUNT']

def print_ip(storage_client):
    global PARTITION_NAME, ROW_ID, SA_NAME, TBL_NAME
    tbl_svc = create_table_service(storage_client, RG_NAME, SA_NAME)
    if not tbl_svc.exists(TBL_NAME):
        return False
    try:
        token = tbl_svc.get_entity(TBL_NAME, PARTITION_NAME, ROW_ID)
        print('{}'.format(token.manager_ip))
        return True
    except:
        return False


def insert_ip(storage_client, manager_ip):
    global PARTITION_NAME, ROW_ID, TBL_NAME, SA_NAME
    tbl_svc = create_table_service(storage_client, RG_NAME, SA_NAME)
    token = {'PartitionKey': PARTITION_NAME, 'RowKey': ROW_ID, 'manager_ip': manager_ip}
    try:
        # this upsert operation should always succeed
        tbl_svc.insert_or_replace_entity(TBL_NAME, token)
        print "successfully inserted/replaced tokens"
        return True
    except:
        print "exception while inserting tokens"
        return False


def create_table(storage_client):
    global TBL_NAME, SA_NAME
    tbl_svc = create_table_service(storage_client, RG_NAME, SA_NAME)
    try:
        # this will succeed only once for a given table name on a storage account
        tbl_svc.create_table(TBL_NAME, fail_on_exist=True)
        print "successfully created table"
        return True
    except:
        print "exception while creating table"
        return False

def main():

    parser = argparse.ArgumentParser(description='Tool to store Docker Swarm info in Azure Tables')
    subparsers = parser.add_subparsers(help='commands', dest='action')
    create_table_parser = subparsers.add_parser('create-table', help='Create table specified in env var AZURE_TBL_NAME')
    get_tokens_parser = subparsers.add_parser('get-ip', help='Get swarm info from table specified in env var AZURE_TBL_NAME')
    insert_tokens_parser = subparsers.add_parser('insert-ip', help='Insert swarm info to table specified in env var AZURE_TBL_NAME')
    insert_tokens_parser.add_argument('ip', help='IP address of the primary swarm manager')

    args = parser.parse_args()

    cred = ServicePrincipalCredentials(
        client_id=APP_ID,
        secret=APP_SECRET,
        tenant=TENANT_ID
    )

    storage_client = StorageManagementClient(cred, SUB_ID)

    if args.action == 'create-table':
        if not create_table(storage_client):
            sys.exit(1)
    elif args.action == 'get-ip':
        print_ip(storage_client)
    elif args.action == 'insert-ip':
        insert_ip(storage_client, args.ip)
    else:
        parser.print_usage()

if __name__ == "__main__":
    main()
