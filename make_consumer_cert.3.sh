#!/bin/bash
export SLAPKEYNAME="ldap1"
export PEM_PATH="pki/pem"
export CERT_PATH=`pwd`"/certs"
export DOMAIN="testunical.it"
export SERVER_FQDN="ldap1.$DOMAIN"

# CA AUTHORITY
export EASYRSA_REQ_CN="$SERVER_FQDN"

export EASYRSA_REQ_COUNTRY="IT"
export EASYRSA_REQ_PROVINCE="Cosenza"
export EASYRSA_REQ_CITY="Cosenza"
export EASYRSA_REQ_ORG="$DOMAIN CERTIFICATE AUTHORITY"
export EASYRSA_REQ_EMAIL="info@$DOMAIN"
export EASYRSA_REQ_OU="$DOMAIN CA"

export EASYRSA_DN="cn_only"
export EASYRSA_KEY_SIZE=2048
export EASYRSA_ALGO=rsa
# 40 years before expiration ...
export EASYRSA_CA_EXPIRE=14600
export EASYRSA_CERT_EXPIRE=14600
export EASYRSA_NS_SUPPORT="no"
export EASYRSA_NS_COMMENT="$DOMAIN CERTIFICATE AUTHORITY"
export EASYRSA_DIGEST="sha256"

# otherwise the previous env vars will not be considered
export EASYRSA_BATCH=1

set -e

cd easy-rsa
cat ./vars.example > vars

set -x

./easyrsa gen-req $SERVER_FQDN nopass
# sign request
./easyrsa sign-req server $SERVER_FQDN

mkdir -p $PEM_PATH

openssl x509 -inform PEM -in pki/issued/$SERVER_FQDN.crt > $PEM_PATH/$SLAPKEYNAME-cert.pem
openssl rsa -in pki/private/$SERVER_FQDN.key -text > $PEM_PATH/$SLAPKEYNAME-key.pem

cp $PEM_PATH/$SLAPKEYNAME-cert.pem $CERT_PATH/
cp $PEM_PATH/$SLAPKEYNAME-key.pem $CERT_PATH/

openssl x509 -in $CERT_PATH/$SLAPKEYNAME-cert.pem -text -noout
