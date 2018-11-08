#!/usr/bin/env python

import os
import sys
from time import sleep
from docker import Client
from azure.cosmosdb.table import TableService, Entity

SWARM_TABLE = 'swarminfo'
LEADER_PARTITION = 'tokens'
LEADER_ROW = '1'

MGR_VMSS_NAME = "swarm-manager-vmss"
WRK_VMSS_NAME = "swarm-worker-vmss"

MGR_ROLE = "MANAGER"
WRK_ROLE = "WORKER"

UPGRADE_MSG_QUEUE = 'upgradeq'
REJOIN_MSG_QUEUE = 'rejoinq'

WRK_TOKEN_ENDPOINT = "http://{}:9024/token/worker/"
SWARM_LISTEN_PORT = 2377
SWARM_LISTEN_ADDR = "0.0.0.0"

def get_swarm_leader_ip(docker_client):
    # find the leader in the swarm and return it's IP address from above mappings
    vms = docker_client.nodes(filters={'role': 'manager'})
    for vm in vms:
        try:
            if vm['ManagerStatus']['Leader'] == True:
                leader_ip = vm['Status']['Addr']
                print("Current leader IP: {}".format(leader_ip))
                return leader_ip
        except KeyError:
            pass
    print "ERROR: No Leader found!"
    return ""


def update_leader_tbl(tbl_svc, tbl_name, tbl_partition, tbl_row, leader_ip):
    ldr_row = {'PartitionKey': tbl_partition, \
                'RowKey': tbl_row, \
                'manager_ip': leader_ip}
    try:
        # this upsert operation should always succeed
        tbl_svc.insert_or_replace_entity(tbl_name, ldr_row)
        print "successfully inserted/replaced tokens"
    except:
        print "exception while inserting tokens"


def wait_with_status(poller, msg):
    while True:
        if poller.done():
            break
        sleep(10)
        print msg