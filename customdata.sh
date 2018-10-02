export ACCOUNT_ID="subscription().subscriptionId"
export SUB_ID="subscription().subscriptionId"
export GROUP_NAME="resourceGroup().name"
export LB_NAME="variables('lbName')"
export APP_ID="parameters('servicePrincipalAppId')"
export APP_SECRET="parameters('servicePrincipalAppSecret')"
export TENANT_ID="subscription().tenantId"
export SWARM_INFO_STORAGE_ACCOUNT="variables('swarmInfoStorageAccount')"
export SWARM_LOGS_STORAGE_ACCOUNT="variables('swarmLogsStorageAccount')"
export PRIVATE_IP=$(ifconfig eth0 | grep "inet addr:" | cut -d: -f2 | cut -d " " -f1)
export AZURE_HOSTNAME=$(hostname)

docker run --label com.docker.editions.system \
    --log-driver=json-file \
    --restart=no \
    -it \
    -e LB_NAME \
    -e SUB_ID \
    -e ROLE \
    -e TENANT_ID \
    -e APP_ID \
    -e APP_SECRET \
    -e ACCOUNT_ID \
    -e GROUP_NAME \
    -e PRIVATE_IP \
    -e DOCKER_FOR_IAAS_VERSION \
    -e SWARM_INFO_STORAGE_ACCOUNT \
    -e SWARM_LOGS_STORAGE_ACCOUNT \
    -e AZURE_HOSTNAME \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v /var/lib/docker:/var/lib/docker \
    -v /var/log:/var/log \
    docker4x/init-azure:$DOCKER_FOR_IAAS_VERSION      