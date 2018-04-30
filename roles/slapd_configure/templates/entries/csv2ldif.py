#!/usr/bin/env python3
import csv
import re
import sys

from collections import OrderedDict

_help = """csv2ldif
Converts csv files in ldif format.
You can add new oid and map them to one or more csv columns.
Mapping can be done editing ATTRIBUTES_MAP object in csv2ldiff.py file:

ATTRIBUTES_MAP=OrderedDict([('dn', 'dn'),
                            ('objectClass', 'objectClass'),
                            ('uid','dn'),
                            ('sn', 'surname'),
                            ('givenName', 'name'),
                            ('cn', ('name', 'surname')),
                            ('mail', 'mail'),
                            ('userPassword', 'password'),
                            ('edupersonAffiliation', 'groups'),
                            ('title', 'title'),
                            ('schacGender', 'schacGender'),
                            ('schacDateOfBirth', 'schacDateOfBirth'),
                            ('schacCountryOfCitizenship', 'schacCountryOfCitizenship'])



Create a csv file, eg:
echo "\
name;surname;dn;objectClass;mail;groups;password
mario;Rossi;uid=mario,ou=people,dc=testunical,dc=it;inetOrgPerson,eduPerson;mario.rossi@testunical.it;staff,member;cimpa12
peppe;Grossi;uid=peppe,ou=people,dc=testunical,dc=it;inetOrgPerson,eduPerson;pgrossi@testunical.it,pgrossi@edu.testunical.it;faculty;roll983
gino;Groe;uid=gino,ou=people,dc=testunical,dc=it;inetOrgPerson,eduPerson;ggroe@testunical.it,groe@edu.testunical.it;faculty,student;geu45" \
> file.csv

then:
    python csv2ldif.py file.csv
    python csv2ldif.py file.csv > file.ldif

"""

if len(sys.argv) < 2:
    sys.exit(_help)

ATTRIBUTES_MAP=OrderedDict([('dn', 'dn'),
                            ('objectClass', 'objectClass'),
                            ('uid','dn'),
                            ('sn', 'surname'),
                            ('givenName', 'name'),
                            ('cn', ('name', 'surname')),
                            ('mail', 'mail'),
                            ('userPassword', 'password'),
                            ('edupersonAffiliation', 'groups'),
                            ('title', 'title'),
                            ('schacGender', 'schacGender'),
                            ('schacDateOfBirth', 'schacDateOfBirth'),
                            ('schacCountryOfCitizenship', 'schacCountryOfCitizenship')])

MULTIVALUED_DELIM=','
EXCLUDED_MULTIVALUED=['dc']

DEBUG=1

def get_cleaned(value):
    return value.strip()


def get_value(oid, row):
    res = []
    col = ATTRIBUTES_MAP[oid]
    if DEBUG > 1: print(oid, col, type(col), row)
    if oid == 'uid':
        res.append(row[col].split(MULTIVALUED_DELIM)[0].split('=')[1])
    elif oid == 'dn':
        res.append(row[col])
    elif type(col) == tuple:
        ncol = []
        for c in col:
            ncol.append(row[c])
        res.append(' '.join(ncol))
    elif MULTIVALUED_DELIM in row[col]:
        for val in row[col].split(MULTIVALUED_DELIM):
            res.append(val)
    else:
        res.append(row[col])
    return res

csv_data = csv.DictReader(open(sys.argv[1]), delimiter=';')
for row in csv_data:
    nrows = []
    for oid in ATTRIBUTES_MAP:
        value = get_value(oid, row)
        # this avoids columns without values (otherwise ldapadd will fail!)
        if not value[0]: continue
        if len(value) == 1:
            nrow = '{}: {}\n'.format(oid, value[0])
        else:
            nrow = ''
            for v in value:
                nrow += '{}: {}\n'.format(oid, v)
        nrows.append(nrow)
    print(''.join(nrows))
