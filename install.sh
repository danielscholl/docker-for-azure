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
function CreateResourceGroup() {
  # Required Argument $1 = RESOURCE_GROUP
  # Required Argument $2 = LOCATION

  if [ -z $1 ]; then
    tput setaf 1; echo 'ERROR: Argument $1 (RESOURCE_GROUP) not received'; tput sgr0
    exit 1;
  fi
  if [ -z $2 ]; then
    tput setaf 1; echo 'ERROR: Argument $2 (LOCATION) not received'; tput sgr0
    exit 1;
  fi

  local _result=$(az group show --name $1)
  if [ "$_result"  == "" ]
    then
      OUTPUT=$(az group create --name $1 \
        --location $2 \
        -ojsonc)
    else
      tput setaf 3;  echo "Resource Group $1 already exists."; tput sgr0
    fi
}
function CreateServicePrincipal() {
    # Required Argument $1 = PRINCIPAL_NAME
    # Required Argument $2 = RESOURCE_GROUP

    if [ -z $1 ]; then
        tput setaf 1; echo 'ERROR: Argument $1 (PRINCIPAL_NAME) not received'; tput sgr0
        exit 1;
    fi
    if [ -z $2 ]; then
        tput setaf 1; echo 'ERROR: Argument $2 (RESOURCE_GROUP) not received'; tput sgr0
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

      SCOPE=$(az group show --name $2 --query id -otsv)
      
      az role assignment create --assignee $CLIENT_ID --scope $SCOPE --role Contributor

      echo "" >> .envrc
      echo "export CLIENT_ID=${CLIENT_ID}" >> .envrc
      echo "export CLIENT_SECRET=${CLIENT_SECRET}" >> .envrc
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
    fi
}
function CreateSSHKeys() {
  # Required Argument $1 = SSH_USER

  if [ -f ~/.ssh/id_rsa.pub ]
  then
    tput setaf 3;  echo "SSH Keys for User $1: "; tput sgr0
    _result=`cat ~/.ssh/id_rsa.pub`

  else
    if [ -d ./.ssh ]
    then 
      tput setaf 3;  echo "SSH Keys for User $1: "; tput sgr0
    else 
      mkdir .ssh && cd .ssh
      ssh-keygen -t rsa -b 2048 -C $1 -f id_rsa && cd ..
      _result=`cat ./.ssh/id_rsa.pub`
    fi 
  fi

   echo $_result
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

tput setaf 2; echo 'Creating Resource Group...' ; tput sgr0
RESOURCE_GROUP="$INITIALS-swarm"
CreateResourceGroup $RESOURCE_GROUP $AZURE_LOCATION


# tput setaf 2; echo 'Creating Service Principal and Role Assignment...' ; tput sgr0
PRINCIPAL_NAME="$INITIALS-swarm-principal"
CreateServicePrincipal $PRINCIPAL_NAME $RESOURCE_GROUP


tput setaf 2; echo 'Creating SSH Keys...' ; tput sgr0
AZURE_USER=$(az account show --query user.name -otsv) 
LINUX_USER=(${AZURE_USER//@/ })
CreateSSHKeys $AZURE_USER


tput setaf 2; echo 'Accepting Marketplace Terms and Conditions...' ; tput sgr0
AcceptTC "docker-ce-edge"


tput setaf 2; echo 'Deploying ARM Template...' ; tput sgr0
az group deployment create --template-file azuredeploy.json  \
    --resource-group $RESOURCE_GROUP \
    --parameters azuredeploy.parameters.json \
    --parameters servicePrincipalAppId=$CLIENT_ID --parameters servicePrincipalAppSecret=$CLIENT_SECRET