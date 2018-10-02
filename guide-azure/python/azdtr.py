#!/usr/bin/env python

##################################################################
# Library to handle tracking of DTR replicas using Azure tables. #
##################################################################

import os
import sys
import urllib2
import ssl
import logging
import logging.config
from datetime import datetime
from time import sleep
from docker import Client
from azure.common.credentials import ServicePrincipalCredentials
from azure.storage.table import TableService, Entity

UCP_HTTPS_PORTS = {443, 8443, 12390}
DTR_TBL_NAME = 'dtrtable'
DTR_PARTITION_NAME = 'dtrreplicas'
DTR_VERSION_PARTITION_NAME = 'dtrversion'
DTR_VERSION_ROW_ID = 1

# get storage account used for DTR metadata
def get_dtr_storage_account(storage_client, rg_name, storage_endpoint, logger):
    storage_accs = storage_client.storage_accounts.list_by_resource_group(rg_name)
    for storage_acc in storage_accs:
        sa_name = storage_acc.name
        if sa_name.endswith("dtr"):
            storage_keys = storage_client.storage_accounts.list_keys(rg_name, sa_name)
            storage_keys = {v.key_name: v.value for v in storage_keys.keys}
            tbl_svc = TableService(account_name=sa_name, account_key=storage_keys['key1'], endpoint_suffix=storage_endpoint)
            if tbl_svc.exists(DTR_TBL_NAME):
                logger.info("DTR table found in Storage Account {}".format(sa_name))
                return sa_name
    raise LookupError("Storage Account with DTR table not found")

# create the Azure table to store DTR info
def create_dtr_table(tbl_svc, logger):
    try:
        # this will succeed only once for a given table name on a storage account
        tbl_svc.create_table(DTR_TBL_NAME, fail_on_exist=True)
        logger.info("successfully created table")
        return True
    except:
        logger.error("exception while creating table")
        return False

# check if UCP is up and running on each node and populate the port on which UCP responded
def populate_ucp_ports(docker_client, ucp_ports, logger):
    logger.info("Checking to see if UCP is up and healthy")
    n = 0
    while n < 20:
        logger.info("Checking managers. Try #{}".format(n))
        nodes = docker_client.nodes(filters={'role': 'manager'})
        # Find first node that's not myself
        ucp_up_on_all_nodes = True
        for node in nodes:
            ucp_on_current_node = False
            manager_ip = node['Status']['Addr']
            logger.info("Manager IP: {}".format(manager_ip))
            # Checking if UCP is up and running.
            # UCP port changes across different releases - so try all
            for ucp_port in UCP_HTTPS_PORTS:
                ucp_url = 'https://%s:%s/_ping' % (manager_ip, ucp_port)
                logger.info("Try to reach UCP at {}".format(ucp_url))
                ssl._create_default_https_context = ssl._create_unverified_context
                try:
                    resp = urllib2.urlopen(ucp_url)
                    logger.info("UCP on %s is healthy" % manager_ip)
                    ucp_on_current_node = True
                    ucp_ports[manager_ip] = ucp_port
                    break
                except urllib2.URLError, e:
                    logger.info("URLError {}".format(str(e.reason)))
                except urllib2.HTTPError, e:
                    logger.info("HTTPError {}".format(str(e.code)))
        if not ucp_on_current_node:
            # fail right away if one node is down
            ucp_up_on_all_nodes = False
            break

        if ucp_up_on_all_nodes:
            logger.info("UCP is all healthy, good to move on!")
            break
        else:
            logger.info("Not all healthy, rest and try again..")
            if n == 20:
                # this will cause the Autoscale group to timeout, and leave this node in the swarm
                # it will eventually be killed once the timeout it hits. TODO: Do something about this.
                logger.error("UCP failed status check after $n tries. Aborting...")
                exit(0)
            sleep(30)
            n = n + 1

# get all replica ids from DTR Table
def get_ids(tbl_svc, logger):
    try:
        replicaids = tbl_svc.query_entities(DTR_TBL_NAME, filter="PartitionKey eq 'dtrreplicas'")
        ids = []
        for replicaid in replicaids:
            ids.append(replicaid.replica_id)
        return ids
    except:
        return None

# get all descriptions from DTR Table
def get_descriptions(tbl_svc, logger):
    try:
        replicaids = tbl_svc.query_entities(DTR_TBL_NAME, filter="PartitionKey eq 'dtrreplicas'", select='description')
        descriptions = []
        for replicaid in replicaids:
            descriptions.append(replicaid.description)
        return descriptions
    except:
        logger.error("exception getting description")
        return None

# get swarm node name that matches replica ID from DTR table
def get_nodename(tbl_svc, replica_id, logger):
    try:
        replicaids = tbl_svc.query_entities(DTR_TBL_NAME, filter="PartitionKey eq 'dtrreplicas'")
        for replicaid in replicaids:
            if replicaid.replica_id == replica_id:
                return replicaid.node_name
        return None
    except:
        logger.error("exception getting node name")
        return None

# get replica id that matches swarm node from DTR Table
def get_id(tbl_svc, nodename, logger):
    try:
        replicaids = tbl_svc.query_entities(DTR_TBL_NAME, filter="PartitionKey eq 'dtrreplicas'")
        for replicaid in replicaids:
            if replicaid.node_name == nodename:
                return replicaid.replica_id
        return None
    except:
        logger.error("node name: {} not found".format(node_name))
        return None

# delete replicaid from the DTR Table
def delete_id(tbl_svc, replica_id, logger):
    try:
        # this upsert operation should always succeed
        tbl_svc.delete_entity(DTR_TBL_NAME, DTR_PARTITION_NAME, replica_id)
        logger.info("successfully deleted replica-id")
        return True
    except:
        logger.error("exception while deleting replica-id")
        return False

# add id to DTR Table
def add_id(tbl_svc, replica_id, node_name, description, logger):
    replica_id = {'PartitionKey': DTR_PARTITION_NAME, 'RowKey': replica_id, 'replica_id': replica_id, 'node_name': node_name, 'description':description}
    try:
        # this upsert operation should always succeed
        tbl_svc.insert_or_replace_entity(DTR_TBL_NAME, replica_id)
        logger.info("successfully inserted/replaced replica-id {}".format(replica_id))
        return True
    except:
        logger.error("exception while inserting replica-id")
        return False

# remove DTR from node and perform table cleanup
def remove_dtr(docker_client, tbl_svc_dtr, dtr_image, node_name, node_ip, ucp_user, ucp_password, logger):
    logger.info("Remove DTR from node: {}".format(node_name))
    ucp_ports = {}
    populate_ucp_ports(docker_client, ucp_ports, logger)
    local_dtr_id = get_id(tbl_svc_dtr, node_name, logger)
    if local_dtr_id is None or local_dtr_id == False:
        logger.info("DTR not installed on this node")
        return
    logger.info("Remove DTR ID: {} from Azure DTR Table".format(local_dtr_id))
    delete_id(tbl_svc_dtr, local_dtr_id, logger)
    num_replicas = 0
    replica_ids = get_ids(tbl_svc_dtr, logger)
    for replica_id in replica_ids:
        num_replicas = num_replicas + 1
        existing_replica_id = replica_id
    # set response to 1, so we guarantee it goes into until loop at least once.
    response = 1
    count = 1
    # try to remove node, keep trying until we have a good removal status 0
    while response != 0:
        logger.info("Removing DTR node {} using ucp_port {}, existing_replica_id {} try#{}".format(local_dtr_id, ucp_ports[node_ip], existing_replica_id, count))
        cont = docker_client.create_container(image=dtr_image,
                command='remove --debug --ucp-url https://{host_ip}:{ucp_port} --ucp-username {user}'
                        ' --ucp-password {password} --ucp-insecure-tls --existing-replica-id {existing_replica}'
                        ' --replica-id {local_dtr_id}'.format(
                            host_ip=node_ip,
                            ucp_port=ucp_ports[node_ip],
                            user=ucp_user,
                            password=ucp_password,
                            existing_replica=existing_replica_id,
                            local_dtr_id=local_dtr_id))
        logger.info("{}".format(cont))
        docker_client.start(cont)
        response = docker_client.wait(cont)
        logger.info("DTR Remove Command Response:{}".format(response))
        if response != 0:
            if count == 20:
                logger.error("Tried to remove node $count times. We are over limit, aborting...")
                exit(1)
            logger.info("We failed for a reason, lets retry again after a brief delay.")
            sleep(30)
            count = count + 1
        else:
            logger.info("DTR removal complete")
    sleep(10)
    return

# get the number of replicas in DTR table
def dtr_replica_count(tbl_svc, logger):
    replicas = get_ids(tbl_svc, logger)
    num_replicas = 0
    for replica in replicas:
        num_replicas = num_replicas + 1
    return num_replicas

# store the DTR version being used
def store_dtr_version(tbl_svc, version):
    dtr_version_record = {'PartitionKey': DTR_VERSION_PARTITION_NAME, 'RowKey': DTR_VERSION_ROW_ID, 'dtr_version': version}
    tbl_svc.insert_or_replace_entity(DTR_TBL_NAME, dtr_version_record)

# get the DTR version stored
def get_dtr_version(tbl_svc):
    if not tbl_svc.exists(DTR_TBL_NAME):
        return ""
    try:
        version_info = tbl_svc.get_entity(DTR_TBL_NAME, DTR_VERSION_PARTITION_NAME, DTR_VERSION_ROW_ID)
        return version_info.dtr_version
    except:
        return ""