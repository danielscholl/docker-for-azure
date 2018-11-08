FROM docker4x/guide-azure:18.03.0-ce-azure1

RUN apk add --update py-pip
RUN pip install --upgrade pip
RUN pip install --force-reinstall -U cryptography adal requests docker[tls] docker-py docker-compose pytz azure
RUN pip install --force-reinstall -U azure.common azure-keyvault azure.mgmt

COPY ./entry.sh /
COPY ./python/*.py /usr/bin/


ENTRYPOINT ["/entry.sh"]
