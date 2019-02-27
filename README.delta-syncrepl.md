Delta replication
-----------------

This guide illustrates how to add a delta-syncrepl slave to this slapd configuration.
You already know that:

- In your ACL there's a rule for ou=repl, every children (user) in it will access to all (*) the content of the server, this means data and configuration.
- replication is based on the Change Sequence Number (CSN) of the context (the highest entryCSN used in the context or synchronization search scope).
CSNs (both entryCSN and contextCSN) are extensively used in OpenLDAP syncrepl style replication operations.


References
----------

- http://www.openldap.org/doc/admin24/guide.html#delta-syncrepl%20replication
- http://www.zytrax.com/books/ldap/ch6/syncprov.html
- http://www.zytrax.com/books/ldap/ch7/#access-log
- https://people.phys.ethz.ch/~rda/openldap/delta-syncrepl/questions_issues.html
