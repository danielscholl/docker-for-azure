



#### Tips

* Post Deployment, one can ssh to the manager using the id_rsa.pub as mentioned during swarm creation: 
 <code>ssh docker@sshlbrip -p 50000</code>


* Transfer the keys to the swarm manager to use it as a jumpbox to workers: 
<code>scp -P 50000 ~/.ssh/id_rsa ~/.ssh/id_rsa.pub docker@sshlbrip:/home/docker/.ssh</code>

* For Deploying a stack in v3 docker-compose file: 
<code>docker stack deploy -c --path to docker-compose.yml file-- --stackname-- </code>

* To update stack: 
<code>docker stack up deploy -c --path to docker-compose.yml file-- --stackname--</code>


#### Some Samples
<code> wget  https://raw.githubusercontent.com/Azure/azure-docker4azureoms/master/docker-compose-ekv3.yml && docker stack deploy -c docker-compose-ekv3.yml elasticsearchkibana </code>

*  ElasticSearch Service: http://Docker4AzureRGExternalLoadBalance:9200/ 
*  Kibana Service: http://Docker4AzureRGExternalLoadBalance:5601/

<code>wget https://raw.githubusercontent.com/Azure/azure-docker4azureoms/master/docker-compose-votingappv3.yml && docker stack deploy -c docker-compose-votingappv3.yml votingapp</code>

*  Vote: http://Docker4AzureRGExternalLoadBalance:5002/ 
*  Voting Results: http://Docker4AzureRGExternalLoadBalance:5003
*  @manomarks Swarm Visualizer: http://Docker4AzureRGExternalLoadBalance:8080 - 
  * <code>docker service create  --name=viz  --publish=8087:8080/tcp  --constraint=node.role==manager --mount=type=bind,src=/var/run/docker.sock,dst=/var/run/docker.sock  manomarks/visualizer</code>

<code>wget https://raw.githubusercontent.com/robinong79/docker-swarm-monitoring/master/composefiles/docker-compose-monitoring.yml &&  wget https://raw.githubusercontent.com/robinong79/docker-swarm-monitoring/master/composefiles/docker-compose-logging.yml && docker network create --driver overlay monitoring && docker network create --driver overlay logging && docker stack deploy -c docker-compose-logging.yml elk &&  docker stack deploy -c docker-compose-monitoring.yml prommon</code>

#### Spring Cloud Netflix Samples
Forked from https://github.com/sqshq/PiggyMetrics, this example demonstrates the use of Netlix OSS API with Spring. The docker-compose file has been updated to make use of the latest features of Compose 3.0; it's still a work in progress. The service container logs are drained into OMS.

<code> wget https://raw.githubusercontent.com/danielscholl/docker-for-azure/master/apps/docker-compose-piggymetricsv3.yml && docker stack deploy -c docker-compose-piggymetricsv3.yml piggymetrics </code>

*  Rabbit MQ Service: http://Docker4AzureRGExternalLoadBalancer:15672/ (guest/guest)
*  Eureka Service: http://Docker4AzureRGExternalLoadBalance:8761/ 
*  Echo Test Service: http://Docker4AzureRGExternalLoadBalance:8989/ 
*  PiggyMetrics Sprint Boot Service: http://Docker4AzureRGExternalLoadBalance:8081/ 
*  Hystrix: http://Docker4AzureRGExternalLoadBalance:9000/hystrix
  * Turbine Stream for Hystrix Dashboard: http://Docker4AzureRGExternalLoadBalance:8989/turbine/turbine.stream

