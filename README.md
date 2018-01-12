Ansible slapd
-------------
This playbook will install a slapd server with:

 - mdb storage
 - eduperson2016 schema
 - schac-2015 schema
 - memberOf overlay
 - ppolicy overlay
 - SASL TLS (ldaps://)

You can even import users from a CSV file, globals parameters can also be edited in playbook.yml.
All about overlays configuration can be found in:
````
roles/slapd/templates/*
````

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

In order to use SASL/TLS  you must have certificates, for testing purposes 
a self-signed certificate will suffice. To learn more about certificates, see OpenSSL.
Remeber that OpenLDAP cannot use a certificate that has a password associated to it.

First of all create your certificates and put them in roles/files/certs/ then 
configure their names in playbook variables. A script named make_CA.sh can do this automatically, 
this create your own self signed keys with easy-rsa. Here it is:

````
#!/bin/bash
export SLAPKEYNAME="slapd"
export PEM_PATH="keys/pem"
export CERT_PATH=`pwd`"/roles/slapd/files/certs"
export SERVER_FQDN="ldap.testunical.it"

apt install easy-rsa
rm -f easy-rsa
cp -Rp /usr/share/easy-rsa/ .
cd easy-rsa

# link easy-rsa ssl config defaults
# You can also edit it to change some informations about issuer and remove EASY-Rsa messages
ln -s openssl-1.0.0.cnf openssl.cnf # won't works with CommonName

# using original openssl file (needs more customizations)
# cp /etc/ssl/openssl.cnf openssl.cnf
# sed -i '1s/^/# For use with easy-rsa version 2.0 and OpenSSL 1.0.0*\n/' openssl.cnf

# customize informations in vars file (or override them later with env VAR)
# remember to configure "Common Name (your server's hostname)" in your certs 
# to let your client avoids "does not match common name in certificate"
nano vars

# then source it
. ./vars

# override for speedup
export KEY_ALTNAMES=$SERVER_FQDN
export KEY_OU=$SERVER_FQDN
export KEY_NAME=$SERVER_FQDN

export KEY_COUNTRY="IT"
export KEY_PROVINCE="CS"
export KEY_CITY="Cosenza"
export KEY_ORG="testunical.it"
export KEY_EMAIL="me@testunical.it"

./clean-all

./build-ca
./build-dh
./build-key $SERVER_FQDN

mkdir -p $PEM_PATH

openssl x509 -inform PEM -in keys/ca.crt > $PEM_PATH/slapd-cacert.pem

openssl x509 -inform PEM -in keys/$SERVER_FQDN.crt > $PEM_PATH/$SLAPKEYNAME-cert.pem
openssl rsa -in keys/$SERVER_FQDN.key -text > $PEM_PATH/$SLAPKEYNAME-key.pem

mkdir -p $CERT_PATH

cp $PEM_PATH/slapd-cacert.pem $CERT_PATH/
cp $PEM_PATH/$SLAPKEYNAME-cert.pem $CERT_PATH/
cp $PEM_PATH/$SLAPKEYNAME-key.pem $CERT_PATH/
````

Create fake users using CSV file
--------------------------------
It would be also possible to create your own custom fake users using a CSV file
![Alt text](images/csv.png)

You can create and Map oid to one or more csv columns in the csv2ldif.py file.
Csv2ldif.py works this way: if a value contains ('name', 'surname') in ATTRIBUTES_MAP the corrisponding  csv columns
will be merged into one oid value, named with the relative ATTRIBUTES_MAP key. 
If csv column value is composed by many values separated by commas instead,
it will create many ldif rows how the splitted csv values are.
````
# csv2ldif.py
ATTRIBUTES_MAP=OrderedDict([('dn', 'dn'),
                            ('objectClass', 'objectClass'),
                            ('uid','dn'),
                            ('sn', 'surname'),
                            ('givenName', 'name'),
                            ('cn', ('name', 'surname')),
                            ('mail', 'mail'),
                            ('userPassword', 'password'),
                            ('edupersonAffiliation', 'groups')])
````

Edit the users in the csv file and then export them in ldif format using csv2ldif:
````
cd roles/slapd/templates/entries/
# edit csv file
nano entries-people.csv
python csv2ldif.py entries-people.csv > entries-people.ldif
python csv2ldif.py entries-people.csv
````

It simply print the exported ldif format in stdout:
````
dn: uid=mario,dc=testunical,dc=it
objectClass: inetOrgPerson
objectClass: eduPerson
uid: mario
sn: Rossi
givenName: mario
cn: mario Rossi
mail: mario.rossi@testunical.it
userPassword: cimpa12
edupersonAffiliation: staff
edupersonAffiliation: member

dn: uid=peppe,dc=testunical,dc=it
objectClass: inetOrgPerson
objectClass: eduPerson
uid: peppe
sn: Grossi
givenName: peppe
cn: peppe Grossi
mail: pgrossi@testunical.it
mail: pgrossi@edu.testunical.it
userPassword: roll983
edupersonAffiliation: faculty

[...]
````

Play this book
--------------
Running it locally
````
ansible-playbook -i "localhost," -c local playbook.yml [-vvv]

# purge all the configuration and the databases as well
ansible-playbook -i "localhost," -c local playbook.yml -e '{ cleanup: true }'
````

Play with LDAP administrative's tasks
-------------------------------------
Commands related to OpenLDAP that begin with ldap (like ldapsearch) are 
client-side utilities, while commands that begin with slap (like slapcat) are server-side.

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

# Check Password Policy schema on openLDAP
ldapsearch -QLLLY EXTERNAL -H ldapi:/// -b cn=schema,cn=config cn=*ppolicy dn

# available backends
ldapsearch -H ldapi:// -Y EXTERNAL -b "cn=config" -LLL -Q "objectClass=olcBackendConfig"

# databases configured in
ldapsearch -H ldapi:// -Y EXTERNAL -b "cn=config" -LLL -Q "olcDatabase=*" dn

# view configuration of a database, {number} may vary
ldapsearch -H ldapi:// -Y EXTERNAL -b "olcDatabase={1}mdb,cn=config" -LLL -Q -s base

# view SASL supporthem mechanisms
ldapsearch -x -H ldapi:/// -b "" -LLL -s base supportedSASLMechanisms
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

# change a normal ldap user password with admin privileges
ldappasswd -H ldaps://ldap.testunical.it -D 'cn=admin,dc=testunical,dc=it' -w slapdsecret  -S -x "uid=gino,ou=people,dc=testunical,dc=it"
````

Remote connections
------------------
````
# bind to ldaps:// on local
ldapsearch -H ldaps:/// -b "dc=testunical,dc=it" -LLL -D "cn=admin,dc=testunical,dc=it" -w slapdsecret

# remote client authentication test (ldap_ca_cert must be copied to clients, hostname must be resolvend at least in /etc/hosts by them)
ldapsearch -H ldaps://ldap.testunical.it:636 -b "dc=testunical,dc=it" -LLL -D "cn=admin,dc=testunical,dc=it" -w slapdsecret -d 1

# test remote client connection
ldapwhoami -x -H ldaps://ldap.testunical.it -D "uid=gino,ou=people,dc=testunical,dc=it" -w geu45 -d 1

# ldap user change his password by himself
ldappasswd -H ldaps://ldap.testunical.it -D 'uid=gino,ou=people,dc=testunical,dc=it' -w ginopassword  -S -x "uid=gino,ou=people,dc=testunical,dc=it"
````

PPolicy management
------------------
````
# get all locket out accounts
ldapsearch -H ldaps://ldap.testunical.it -D "cn=admin,dc=testunical,dc=it" -b "ou=people,dc=testunical,dc=it"  -w slapdsecret "pwdAccountLockedTime=*" pwdAccountLockedTime

# unkock
dn: cn=gino,ou=people,dc=testunical,dc=it
changetype: modify
delete: pwdAccountLockedTime

# or pwdReset. It must be then resetted using ldappasswd

dn: cn=gino,ou=people,dc=testunical,dc=it
changetype: modify
add: pwdReset
pwdReset: TRUE

````

Backup and restore
------------------
It will extract the entire database contents into the "backup_slapd.ldif" file 
and then restore "backup_slapd.ldif", importing it back into the LDAP after 
a system rebuild.
````
# entire backup
slapcat -vl /etc/openldap/backup_slapd.ldif

# restore
slapadd -vl /etc/openldap/backup_slapd.ldif

# backup config
slapcat -F /etc/openldap/slapd.d -n 0 -l "$(hostname)-ldap-mdb-config-$(date '+%F').ldif"
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


Hints
-----
- ldap:// is disabled, only ldapi:/// and ldaps:/// will be available;
- Be aware that ldapmodify is sensitive to (trailing) spaces;
- https://www.openldap.org/doc/admin24/appendix-common-errors.html
- Error 80 (implementation specific error) raises when tls certs doesn't have read permissions or if the ldif used with ldapadd/ldapmodify have some trailing spaces or too many blank lines or some syntax error;
- ldapadd, ldapsearch, ldapmodify: set debug level with -d 1 or more. It's the only way to get ldap be more eloquent;
- every client must have slapd-cacert.pem configured in /etc/ldap.conf (pem file could be copied with scp);
- Passwords in the CSV example file will be stored by LDAP in cleartex format, don't do this in production environment, {SSHA} is a good choice;

License
-------
BSD


Author Information
------------------
Giuseppe De Marco <giuseppe.demarco@unical.it>


Special thanks to
-----------------
- Marco Malavolti

  For his awesome repository: https://github.com/malavolti/ansible-shibboleth
  
- IDEM:GARR guys

  For Digital Identity Management general knowledge :)

- Unical guys

  For everyday brain crushing
