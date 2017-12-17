Ansible slapd
-------------

This playbook will install a slapd server with:

 - mdb storage
 - eduperson2016 schema
 - memberOf overlay

Tested on
---------

- Debian 9

Requirements
------------

````
pip3 install ansible
````

MemberOf overlay
----------------

MemberOf overlay made a client to be able to determine which groups an entry 
is a member of, without performing an additional search. Examples of this 
are applications using the DIT for access control based on group authorization.

The memberof overlay updates an attribute (by default memberOf) whenever 
changes occur to the membership attribute (by default member) of entries of 
the objectclass (by default groupOfNames) configured to trigger updates.

Thus, it provides maintenance of the list of groups an entry is a 
member of, when usual maintenance of groups is done by modifying the 
members on the group entry.

Setup Certificates
------------------

First create your certificates and put them in roles/files/certs/.
Then configure their names in playbook variables.

A script to create your own self signed keys with easy-rsa.

````
export SLAPKEYNAME="slapd"
export PEM_PATH="keys/pem"
export CERT_PATH=`pwd`"/roles/slapd/files/certs"

apt install easy-rsa
cp -Rp /usr/share/easy-rsa/ .
cd easy-rsa

# customize informations in vars file
nano vars

# then source it
. ./vars

# link your ssl version
ln -s openssl-1.0.0.cnf openssl.cnf

./build-ca
./build-dh
./build-key $SLAPKEYNAME

mkdir -p $PEM_PATH

openssl x509 -inform PEM -in keys/ca.crt > $PEM_PATH/slapd-cacert.pem

openssl x509 -inform PEM -in keys/$SLAPKEYNAME.crt > $PEM_PATH/$SLAPKEYNAME-cert.pem
openssl rsa -in keys/$SLAPKEYNAME.key -text > $PEM_PATH/$SLAPKEYNAME-key.pem

mkdir -p $CERT_PATH

cp $PEM_PATH/slapd-cacert.pem $CERT_PATH/
cp $PEM_PATH/$SLAPKEYNAME-cert.pem $CERT_PATH/
cp $PEM_PATH/$SLAPKEYNAME-key.pem $CERT_PATH/

service slapd restart
````

Play with it
------------

Running it locally
````
ansible-playbook -i "localhost," -c local playbook.yml [-vvv]

# purge all the configuration and the databases as well
ansible-playbook -i "localhost," -c local playbook.yml -e '{ cleanup: true }'
````

Play with LDAP administrative's tasks
-------------------------------------

````
# root DSE
ldapsearch -H ldap:// -x -s base -b "" -LLL "+"

# DITs
ldapsearch -H ldap:// -x -s base -b "" -LLL "namingContexts"

# config DIT
ldapsearch -H ldap:// -x -s base -b "" -LLL "configContext"

# read config
ldapsearch -H ldapi:// -Y EXTERNAL -b "cn=config" -LLL -Q

# small config output
ldapsearch -H ldapi:// -Y EXTERNAL -b "cn=config" -LLL -Q dn

# read top level entries
ldapsearch -H ldapi:// -Y EXTERNAL -b "cn=config" -LLL -Q -s base

# find admin entry
ldapsearch -H ldapi:// -Y EXTERNAL -b "cn=config" "(olcRootDN=*)" olcSuffix olcRootDN olcRootPW -LLL -Q

# read builtin schemas
ldapsearch -H ldapi:// -Y EXTERNAL -b "cn=schema,cn=config" -s base -LLL -Q | less

# read additional schemas
# ldapsearch -H ldapi:// -Y EXTERNAL -b "cn=schema,cn=config" -LLL -Q
ldapsearch -H ldapi:// -Y EXTERNAL -b "cn=schema,cn=config" -LLL -Q dn

# get the content of an entry
ldapsearch -H ldapi:// -Y EXTERNAL -b "cn={3}inetorgperson,cn=schema,cn=config" -s base -LLL -Q

# loaded modules
ldapsearch -H ldapi:// -Y EXTERNAL -b "cn=config" -LLL -Q "objectClass=olcModuleList"

# available backends
ldapsearch -H ldapi:// -Y EXTERNAL -b "cn=config" -LLL -Q "objectClass=olcBackendConfig"

# databases configured in
ldapsearch -H ldapi:// -Y EXTERNAL -b "cn=config" -LLL -Q "olcDatabase=*" dn

# view configuration of a database, {number} may vary
ldapsearch -H ldapi:// -Y EXTERNAL -b "olcDatabase={1}mdb,cn=config" -LLL -Q -s base
````

Play with content data
----------------------

````
# query entry set
ldapsearch -H ldapi:// -Y EXTERNAL -b "dc=testunical,dc=it" -LLL

# query entry set with operational metadata
ldapsearch -H ldapi:// -Y EXTERNAL -b "dc=testunical,dc=it" -LLL "+"

# The subschema is a representation of the available classes and attributes.
ldapsearch -H ldapi:// -Y EXTERNAL -b "dc=testunical,dc=it" -LLL subschemaSubentry
````

[TODO] SQL as Database backend
------------------------------

slapd-config sql attributes:
https://github.com/openldap/openldap/blob/master/servers/slapd/back-sql/config.c#L74


- create an ldif to ldapadd, eg:
````
dn: olcDatabase=sql,cn=config
objectClass: olcDatabaseConfig
objectClass: olcSqlConfig
olcSuffix: dc=test
olcDatabase: sql
olcDbName: ldap
olcDbPass: ldap
olcDbUser: ldap
olcSqlSubtreeCond: "ldap_entries.dn LIKE CONCAT('%',?)"
olcSqlInsEntryStmt: "INSERT INTO ldap_entries (dn,oc_map_id,parent,keyval) VALUES (?,?,?,?)"
olcSqlHasLDAPinfoDnRu: no
````
- create some conditionals in slapd role to manage this feature


License
-------

BSD


Author Information
------------------

Giuseppe De Marco <giuseppe.demarco@unical.it>


Special thanks
--------------

GARR:IDEM guys
