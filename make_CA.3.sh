#!/bin/bash
export SLAPKEYNAME="slapd"
export PEM_PATH="pki/pem"
export CERT_PATH=`pwd`"/certs"
export DOMAIN="testunical.it"
export SERVER_FQDN="ldap.$DOMAIN"

# CA AUTHORITY
export EASYRSA_REQ_CN="$SERVER_FQDN"

export EASYRSA_REQ_COUNTRY="IT"
export EASYRSA_REQ_PROVINCE="Cosenza"
export EASYRSA_REQ_CITY="Cosenza"
export EASYRSA_REQ_ORG="$DOMAIN CERTIFICATE AUTHORITY"
export EASYRSA_REQ_EMAIL="info@$DOMAIN"
export EASYRSA_REQ_OU="$DOMAIN CA"

# export EASYRSA="$PWD"
# export EASYRSA_PKI="$EASYRSA/pki"
# export EASYRSA_EXT_DIR="$EASYRSA/x509-types"
# export EASYRSA_SSL_CONF="$EASYRSA/openssl-1.0.cnf"

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

apt install easy-rsa
rm -Rf easy-rsa
mkdir -p $CERT_PATH

cp -Rp /usr/share/easy-rsa/ .
cd easy-rsa
cat ./vars.example > vars

set -x

./easyrsa init-pki
./easyrsa build-ca nopass

# it will take long time ...
# ./easyrsa gen-dh

#
./easyrsa gen-req $SERVER_FQDN nopass
# sign request
./easyrsa sign-req server $SERVER_FQDN

mkdir -p $PEM_PATH
openssl x509 -inform PEM -in pki/ca.crt > $PEM_PATH/slapd-cacert.pem

openssl x509 -inform PEM -in pki/issued/$SERVER_FQDN.crt > $PEM_PATH/$SLAPKEYNAME-cert.pem
openssl rsa -in pki/private/$SERVER_FQDN.key -text > $PEM_PATH/$SLAPKEYNAME-key.pem

cp $PEM_PATH/slapd-cacert.pem $CERT_PATH/
cp $PEM_PATH/$SLAPKEYNAME-cert.pem $CERT_PATH/
cp $PEM_PATH/$SLAPKEYNAME-key.pem $CERT_PATH/


openssl x509 -in $CERT_PATH/slapd-cacert.pem -text -noout
openssl x509 -in $CERT_PATH/$SLAPKEYNAME-cert.pem -text -noout
