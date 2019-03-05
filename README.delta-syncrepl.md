Delta replication
-----------------

Delta-syncrepl works by maintaining a changelog of a selectable depth in a separate database on the provider.
The replication consumer checks the changelog for the changes it needs and, as long as the changelog contains
the needed changes, the consumer fetches the changes from the changelog and applies them to its database.
If, however, a replica is too far out of sync (or completely empty), conventional syncrepl is used to bring
it up to date and replication then switches back to the delta-syncrepl mode.


This guide illustrates how to add a delta-syncrepl slave to this slapd configuration.
You already know that:

- In your ACL there's a rule for ou=repl, every children (user) in it will access to all (*) the content of the server, this means data and configuration DIT;
- replication is based on the Change Sequence Number (CSN) of the context (the highest entryCSN used in the context or synchronization search scope).
CSNs (both entryCSN and contextCSN) are extensively used in OpenLDAP syncrepl style replication operations;
- Setting up delta-syncrepl requires configuration changes on both the master and replica servers;


Things to know about SyncRepl
-----------------------------

In syncrepl style replication the consumer always initiates the update process.
The consumer may be configured to periodically pull the updates
from the provider (refreshOnly) or it may request the provider to push updates (refreshAndPersist).


In all replication cases, in order to unambiguously refer to an entry the server must
maintain a universally unique number (entryUUID) for each entry in a DIT.


In refreshAndPersist type of replication the consumer initiates a connection with the provider,
synchronization of DITs takes places immediately and at the end of this process the connection is maintained (it persists).
Subsequent changes to the provider are immediately propagated to the consumer.


olcSyncProvConfig options
-------------------------

`olcSpCheckpoint: ops minutes`: The attribute/directive may be used to force the provider to write the contextCSN to the underlying database
after a successful write operation after either every ops write operations or more than minutes time have passed since the last contextCSN
database update (or checkpoint). This directive is designed to minimise the amount of consumer synchronization activity required in the event
that the master (provider) DIT server crashes.
`olcSpSessionlog: ops`: *ops* specifies the number of operations that are recorded in the log of write operations made by the provider.
The session log is memory based and contains all operations performed (except add operations).
Depending on the time period covered by the session log it may allow the provider to skip the
optional present phase - thus significantly speeding up the synchronization process.
If the session log does not contain enough information the provider executes a full re-synchronization sequence from the last known point.
`olcSpNoPresent: TRUE | FALSE`: Set it to TRUE for a syncprov instance used with a log database such as accesslog overlay. The default is FALSE.
`olcSpReloadHint: TRUE | FALSE`: It must be set TRUE when using the accesslog overlay for delta-synchonization. The default is FALSE.

Provider slapd configuration
----------------------------
Run the playbook with `accesslog_enabled` and `syncrepl_enabled`, remember to
rename playbook.yml to playbook.production-consumer for safety.
````
ansible-playbook -i "localhost," -c local playbook.production-consumer
````

Then add the consumer user this way:

````
# these are the same on both provider and consumer
export D1=it
export D2=testunical
export USERUID=ldap1
export USERPWD=thatpassword
````

Create the user used for delta repl from consumers
````
ldapadd -Y EXTERNAL -H ldapi:/// <<EOF
dn: uid=$USERUID,ou=repl,dc=$D2,dc=$D1
objectClass: inetOrgPerson
cn: $USERUID
sn: $USERUID consumer
uid: $USERUID consumer
userPassword: $USERPWD
EOF
````

Create the user used for repl-chain, this will enable
PPolicy forward updates from consumer to provider.
````
ldapadd -Y EXTERNAL -H ldapi:/// <<EOF
dn: uid=$USERUID,ou=repl-chain,dc=$D2,dc=$D1
objectClass: inetOrgPerson
cn: $USERUID
sn: $USERUID consumer
uid: $USERUID consumer
userPassword: $USERPWD
EOF
````

Consumer slapd configuration
----------------------------

Test the ACL before all
````
# generic search on ou
ldapsearch -H ldap://ldap.testunical.it -D "uid=$USERUID,ou=repl,dc=$D2,dc=$D1" -w $USERPWD -b 'ou=people,dc=testunical,dc=it' -LLL

# access to accelog (required for delta repl)
ldapsearch -H ldap://ldap.testunical.it -D "uid=$USERUID,ou=repl,dc=$D2,dc=$D1" -w $USERPWD -b 'cn=accesslog' -LLL

````
Execute the following statement to make this server a consumer of a provider,
remember that `olcDbIndex: entryUUID` was already configured by playbook,
so we don't need to configure it again.

*Here* would be inserted the chain overlay. See _Chain overlay ISSUES_.

_Remember:_ To add `starttls=critical tls_reqcert=demand` to the previous ldapmodify command
to ensure data security and integrity in production context.
````
ldapmodify -Y EXTERNAL -H ldapi:/// <<EOF
dn: cn=module{0},cn=config
changetype: modify
add: olcModuleLoad
olcModuleLoad: syncprov

dn: olcDatabase={1}mdb,cn=config
changetype: modify
add: olcSyncRepl
olcSyncRepl: rid=0
    provider=ldap://ldap.$D2.$D1
    bindmethod=simple
    binddn="uid=$USERUID,ou=repl,dc=$D2,dc=$D1"
    credentials=$USERPWD
    searchbase="dc=$D2,dc=$D1"
    logbase="cn=accesslog"
    logfilter="(&(objectClass=auditWriteObject)(reqResult=0))"
    schemachecking=on
    type=refreshAndPersist
    retry="60 +"
    syncdata=accesslog
-
add: olcUpdateRef
olcUpdateRef: ldap://ldap.$D2.$D1
EOF
````

_olcUpdateRef_ demand to the master the updates of value.
Even if you omit this option the consumer cannot update their local
values, it will get: _ldap_modify: Server is unwilling to perform (53) additional info: shadow context; no update referral_


About `retry` option:
1.  "retry" accepts a comma separated list of number pairs
    (+ may be used in the second value of a pair).
2.  The first value of the pair is the "retry interval" in seconds
3.  The second value of the pair is the "number of retries"
   "+" or "-1" may be used for an infinite number of retriess


Debug
-----

check replica index on provider
````
ldapsearch -Y EXTERNAL -H ldapi:/// -LLL -s base -b dc=$D2,dc=$D1 contextCSN
````

check replica index on provider from consumers
````
ldapsearch -H ldap://ldap.testunical.it -LLL -w $USERPWD -D uid=$USERUID,ou=repl,dc=$D2,dc=$D1 -s base -b dc=$D2,dc=$D1 contextCSN
````

then check on the slave, if these two numbers match then we have replication
TODO: do a unitest script for replication here!
````
ldapsearch -Y EXTERNAL -H ldapi:/// -LLL -s base -b dc=$D2,dc=$D1 contextCSN
````

Notes
-----

Remove UpdateRef
````
ldapmodify -Y EXTERNAL -H ldapi:/// <<EOF
dn: olcDatabase={1}mdb,cn=config
changetype: modify
delete: olcUpdateRef
EOF


TODO
----

- [ppolicy_forward_updates `olcPPolicyForwardUpdates: TRUE`](https://www.systutorials.com/docs/linux/man/5-slapo-ppolicy/), userlockout should be updated from consumer to provider with a good [updateref](http://www.zytrax.com/books/ldap/ch6/index.html#updateref) and [chain overlay](https://linux.die.net/man/5/slapo-chain);
 Additional resources:
  - https://www.openldap.org/lists/openldap-technical/201005/msg00028.html
  - https://www.linuxtopia.org/online_books//network_administration_guides/ldap_administration/overlays_Chaining.html#Chaining
  - http://www.informatik.uni-bremen.de/~manal/ldap/slaves.conf

Chain overlay ISSUES
--------------------

The process for converting a slapd configuration to cn=config making use of
slapo-chain at a global level seems to be  seriously broken.

- http://www.openldap.org/its/index.cgi/Incoming?id=8799;page=116;statetype=-1

These are the further steps that still waiting to be imported.

Remeber to add back_ldap if you're using a Debian.
````
ldapadd -Y EXTERNAL -H ldapi:/// <<EOF
dn: cn=module,cn=config
objectclass: olcModuleList
cn: module
olcModuleLoad: back_ldap
EOF
````

Remember to add `olcDbStartTLS` for security.
````
ldapadd -Y EXTERNAL -H ldapi:/// <<EOF
dn: olcOverlay=chain,olcDatabase={-1}frontend,cn=config
objectClass: olcOverlayConfig
objectClass: olcChainConfig
olcOverlay: chain
olcChainCacheURI: FALSE
olcChainMaxReferralDepth: 1
olcChainReturnError: TRUE

dn: olcDatabase=ldap,olcOverlay=chain,olcDatabase={-1}frontend,cn=config
objectClass: olcLDAPConfig
objectClass: olcChainDatabase
olcDBURI: ldap://ldap.$D2.$D1
olcDbIDAssertBind: bindmethod=simple
  binddn="uid=$USERUID,ou=repl-chain,dc=$D2,dc=$D1"
  credentials=$USERPWD
  mode=self
EOF
````

Add chain overlay for enable olcPPolicyForwardUpdates in consumer.
````
ldapmodify -Y EXTERNAL -H ldapi:/// <<EOF
dn: cn=default,ou=policies,{{ ldap_basedc }}
objectClass: pwdPolicy
olcPPolicyForwardUpdates=TRUE
EOF
````

References
----------

- https://icicimov.github.io/blog/devops/LDAP-replication-for-Directory-HA/
- http://www.openldap.org/doc/admin24/guide.html#delta-syncrepl%20replication
- http://www.zytrax.com/books/ldap/ch6/syncprov.html
- http://www.zytrax.com/books/ldap/ch7/#access-log
- https://people.phys.ethz.ch/~rda/openldap/delta-syncrepl/questions_issues.html
- [RFC4533](http://www.zytrax.com/books/ldap/apc/rfc4533.txt)
