Docker Swarm Apps
===

Tips
---

```bash
# SSH to the Manager Node
ResourceGroup="demo-swarm"
IPName="$ResourceGroup-nat-ip"

NatLB="$(az network public-ip show --resource-group $ResourceGroup --name $IPName --query ipAddress -otsv)"

ssh docker@$NatLB -p 50000
```

```bash
# Transfer Keys to the Manager to enable SSH to workers
scp -P 50000 ~/.ssh/id_rsa ~/.ssh/id_rsa.pub docker@$NatLB:/home/docker/.ssh
```

```bash
# Deploying and Updating Docker Stacks

docker stack deploy -c <path_to_your_compose> <stackname>
docker stack up deploy -c <path_to_your_compose> <stackname>
```


Swarm Visualizer
---

```bash
# Startup the Visualizer Service
docker service create \
  --name=viz \
  --publish=8080:8080/tcp \
  --constraint=node.role==manager \
  --mount=type=bind,src=/var/run/docker.sock,dst=/var/run/docker.sock \
  dockersamples/visualizer
```

```bash
# Startup Voting App
wget https://raw.githubusercontent.com/danielscholl/docker-for-azure/master/apps/docker-compose-votingapp.yml && \
  docker stack deploy \
    -c docker-compose-votingapp.yml \
    votingapp
```

#### Voting App

```bash
# Startup Voting App
URL="https://raw.githubusercontent.com/danielscholl/docker-for-azure/master/apps/docker-compose-votingapp.yml"
wget $URL && \
  docker stack deploy \
    -c docker-compose-votingapp.yml \
    votingapp
```
*  Vote: http://swarmLB:5002/
*  Voting Results: http://swarmLB:5003


#### Spring Cloud Netflix Samples
Forked from https://github.com/sqshq/PiggyMetrics, this example demonstrates the use of Netlix OSS API with Spring. The docker-compose file has been updated to make use of the latest features of Compose 3.0; it's still a work in progress. The service container logs are drained into OMS.

```bash
URL="https://raw.githubusercontent.com/danielscholl/docker-for-azure/master/apps/docker-comopose-piggymetrics.yml"

wget $URL && \
  docker stack deploy \
  -c docker-comopose-piggymetrics.yml \
  piggymetrics
```
*  Rabbit MQ Service: http://swarmLB:15672/ (guest/guest)
*  Eureka Service: http://swarmLB:8761/
*  Echo Test Service: http://swarmLB:8989/
*  PiggyMetrics Sprint Boot Service: http://swarmLB:8081/
*  Hystrix: http://swarmLB:9000/hystrix
*  Turbine Stream for Hystrix Dashboard: http://swarmLB:8989/turbine/turbine.stream



#### Some Samples
<code> wget  https://raw.githubusercontent.com/Azure/azure-docker4azureoms/master/docker-compose-ekv3.yml && docker stack deploy -c docker-compose-ekv3.yml elasticsearchkibana </code>

*  ElasticSearch Service: http://Docker4AzureRGExternalLoadBalance:9200/
*  Kibana Service: http://Docker4AzureRGExternalLoadBalance:5601/


