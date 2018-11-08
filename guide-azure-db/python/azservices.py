import os
import sys
from azure.common import AzureHttpError
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.storage import StorageManagementClient
from azure.cosmosdb.table import TableService
from azure.storage.queue import QueueService
from azendpt import AZURE_PLATFORMS, AZURE_DEFAULT_ENV

RESOURCE_MANAGER_ENDPOINT = AZURE_PLATFORMS[AZURE_DEFAULT_ENV]['RESOURCE_MANAGER_ENDPOINT']
ACTIVE_DIRECTORY_ENDPOINT = AZURE_PLATFORMS[AZURE_DEFAULT_ENV]['ACTIVE_DIRECTORY_ENDPOINT']
STORAGE_ENDPOINT = AZURE_PLATFORMS[AZURE_DEFAULT_ENV]['STORAGE_ENDPOINT']

KEY_FILE_PATH="/tmp/"

def _lookup_key(storage_client, resource_group, account_name):
    storage_keys = storage_client.storage_accounts.list_keys(resource_group, account_name)
    storage_keys = {v.key_name: v.value for v in storage_keys.keys}
    return storage_keys['key1']

def _get_storage_account_key(storage_client, resource_group, account_name):
    key_file = KEY_FILE_PATH+account_name
    if os.path.isfile(key_file):
        with open(key_file, 'r') as f:
            return f.read()
    key = _lookup_key(storage_client, resource_group, account_name)
    with open(key_file, 'w') as f:
        f.write(key)
    return key

def _get_service(storage_client, resource_group, account_name, endpoint_suffix, create_service, validate_service):
    account_key = _get_storage_account_key(storage_client, resource_group, account_name)
    service = create_service(account_name=account_name, account_key=account_key, endpoint_suffix=endpoint_suffix)
    try:
        validate_service(service)
        return service
    except AzureHttpError:
        key_file = KEY_FILE_PATH+account_name
        os.remove(key_file)
        account_key = _get_storage_account_key(storage_client, resource_group, account_name)
    return create_service(account_name=account_name, account_key=account_key, endpoint_suffix=endpoint_suffix)

def _create_table_service(account_name, account_key, endpoint_suffix):
    return TableService(account_name=account_name, account_key=account_key, endpoint_suffix=endpoint_suffix)

def _validate_table_service(table_service):
    props = table_service.get_table_service_properties()

def _create_queue_service(account_name, account_key, endpoint_suffix):
    return QueueService(account_name=account_name, account_key=account_key, endpoint_suffix=endpoint_suffix)

def _validate_queue_service(queue_service):
    props = queue_service.get_queue_service_properties()

def create_table_service(storage_client, resource_group, storage_account):
    return _get_service(storage_client, resource_group, storage_account, STORAGE_ENDPOINT, _create_table_service, _validate_table_service)

def create_queue_service(storage_client, resource_group, storage_account):
    return _get_service(storage_client, resource_group, storage_account, STORAGE_ENDPOINT, _create_queue_service, _validate_queue_service)

def main():

    SUB_ID = os.environ['ACCOUNT_ID']
    TENANT_ID = os.environ['TENANT_ID']
    APP_ID = os.environ['APP_ID']
    APP_SECRET = os.environ['APP_SECRET']
    RG_NAME = os.environ['GROUP_NAME']
    SA_NAME = os.environ['SWARM_INFO_STORAGE_ACCOUNT']

    # init various Azure API clients using credentials
    cred = ServicePrincipalCredentials(
        client_id=APP_ID,
        secret=APP_SECRET,
        tenant=TENANT_ID,
        resource=RESOURCE_MANAGER_ENDPOINT,
        auth_uri=ACTIVE_DIRECTORY_ENDPOINT
    )
    storage_client = StorageManagementClient(cred, SUB_ID, base_url=RESOURCE_MANAGER_ENDPOINT)

    table_service = create_table_service(storage_client, RG_NAME, SA_NAME)
    props = table_service.get_table_service_properties()
    print(props.cors)

    queue_service = create_queue_service(storage_client, RG_NAME, SA_NAME)
    props = queue_service.get_queue_service_properties()
    print(props.cors)

if __name__ == "__main__":
    main() 
