#!/usr/bin/env bash
#
#  Purpose: Initialize the template load for testing purposes
#  Usage:
#    install.sh



###############################
## ARGUMENT INPUT            ##
###############################

usage() { echo "Usage: install.sh " 1>&2; exit 1; }

if [ -f ./.envrc ]; then source ./.envrc; fi

if [ ! -z $1 ]; then INITIALS=$1; fi
if [ -z $INITIALS ]; then
  INITIALS="demo"
fi

if [ -z $AZURE_LOCATION ]; then
  AZURE_LOCATION="eastus"
fi



###############################
## FUNCTIONS                 ##
###############################

function CreateServicePrincipal() {
    # Required Argument $1 = PRINCIPAL_NAME

    if [ -z $1 ]; then
        tput setaf 1; echo 'ERROR: Argument $1 (PRINCIPAL_NAME) not received'; tput sgr0
        exit 1;
    fi

    local _result=$(az ad sp list --display-name $1 --query [].appId -otsv)
    if [ "$_result"  == "" ]
    then
      CLIENT_SECRET=$(az ad sp create-for-rbac \
        --name $1 \
        --skip-assignment \
        --query password -otsv)
      CLIENT_ID=$(az ad sp list \
        --display-name $1 \
        --query [].appId -otsv)
      OBJECT_ID=$(az ad sp list \
        --display-name $1 \
        --query [].objectId -otsv)
      UNIQUE=$(echo $RANDOM | cut -c 1-3)


      echo "" >> .envrc
      echo "export CLIENT_ID=${CLIENT_ID}" >> .envrc
      echo "export CLIENT_SECRET=${CLIENT_SECRET}" >> .envrc
      echo "export OBJECT_ID=${OBJECT_ID}" >> .envrc
      echo "export UNIQUE=${UNIQUE}" >> .envrc

    else
        tput setaf 3;  echo "Service Principal $1 already exists."; tput sgr0
        if [ -z $CLIENT_ID ]; then
          tput setaf 1; echo 'ERROR: Principal exists but CLIENT_ID not provided' ; tput sgr0
          exit 1;
        fi

        if [ -z $CLIENT_SECRET ]; then
          tput setaf 1; echo 'ERROR: Principal exists but CLIENT_SECRET not provided' ; tput sgr0
          exit 1;
        fi

        if [ -z $OBJECT_ID ]; then
          tput setaf 1; echo 'ERROR: Principal exists but OBJECT_ID not provided' ; tput sgr0
          exit 1;
        fi

        if [ -z $UNIQUE ]; then
          tput setaf 1; echo 'ERROR: UNIQUE not provided' ; tput sgr0
          exit 1;
        fi
    fi
}
function CreateSSHKeys() {
  # Required Argument $1 = SSH_USER
  if [ -d ~/.ssh ]
  then
    tput setaf 3;  echo "SSH Keys for User $1: "; tput sgr0
  else
    local _BASE_DIR = ${pwd}
    mkdir ~/.ssh && cd ~/.ssh
    ssh-keygen -t rsa -b 2048 -C $1 -f id_rsa && cd $_BASE_DIR
  fi

 _result=`cat ~/.ssh/id_rsa.pub`

}

function AcceptTC() {
  if [ -z $1 ]; then
      tput setaf 1; echo 'ERROR: Argument $1 (OFFER) not received'; tput sgr0
      exit 1;
  fi

  PUBLISHER="docker"
  URN=$(az vm image list --all --publisher $PUBLISHER --offer $1 --sku $1 --query '[0].urn' -otsv)
  az vm image accept-terms --urn $URN
}


###############################
## Azure Intialize           ##
###############################

tput setaf 2; echo 'Creating Service Principal and Role Assignment...' ; tput sgr0
PRINCIPAL_NAME="$INITIALS-swarm-principal"
CreateServicePrincipal $PRINCIPAL_NAME

tput setaf 2; echo 'Creating SSH Keys...' ; tput sgr0
AZURE_USER=$(az account show --query user.name -otsv)
LINUX_USER=(${AZURE_USER//@/ })
CreateSSHKeys $AZURE_USER


tput setaf 2; echo 'Accepting Marketplace Terms and Conditions...' ; tput sgr0
AcceptTC "docker-ce-edge"

tput setaf 2; echo 'Deploying ARM Template...' ; tput sgr0
if [ -f ./params.json ]; then PARAMS="params.json"; else PARAMS="azuredeploy.parameters.json"; fi
az deployment create --template-file azuredeploy_orig.json  \
    --name "$INITIALS-swarm" \
    --location $AZURE_LOCATION \
    --parameters $PARAMS \
    --parameters random=$UNIQUE initials=$INITIALS \
    --parameters servicePrincipalAppId=$CLIENT_ID \
    --parameters servicePrincipalAppSecret=$CLIENT_SECRET \
    --parameters servicePrincipalObjectId=$OBJECT_ID
