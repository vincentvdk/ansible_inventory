#!/usr/bin/python
#
## ansible ldap inventory script Copyright (c) 2013 by Vincent Van der
## Kussen
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.
##

import ldap
import re
import sys
import operator

try:
    import json
except ImportError:
    import simplejson as json

# establish connection with LDAP server
try:
    l = ldap.initialize("ldap://")
    username = "cn=,dc=,dc="
    password = ""
    l.bind_s(username, password, ldap.AUTH_SIMPLE)

except ldap.LDAPError, e:
    print e

# LDAP variables
baseDN = 'ou=, dc=, dc='
searchScope = ldap.SCOPE_SUBTREE
attrs = None

# We only want the groups and not groups + computer CNs
groupsearchFilter = '(&(objectClass=groupOfNames)(cn=*))'

# ------------------------------------------------------------------
# get a list of groups with their hosts
def getlist():
    try:
        grp = {}
        result = l.search_s(baseDN, searchScope, groupsearchFilter)
        for item in result:
            #print item
            res = item[1]
            groups = res['cn'][0]
            grp[groups] = []
            res = dict(item[1])
            for key, value in res.iteritems():
                hosts = []
                if key == "member":
                    for item in value:
                        host = re.match(r'cn=([^,]*)', item)
                        host = host.group(1)
                        grp[groups].append(host)
        print grp
        print json.dumps(grp, sort_keys=True, indent=2)

    except ldap.LDAPError, e:
        print e

    l.unbind_s()

# --------------------------------------------------------------------
# get all attributes from a host
def getdetails(host):
    hostsearchFilter = "cn=%s" % host
    details = {}
    result = l.search_s(baseDN, searchScope, hostsearchFilter)
    for item in result:
        res = dict(item[1])
        for key, value in res.iteritems():
            if key != "objectClass":
                details[key] = value[0]
        print json.dumps(details, sort_keys=True, indent=2)
    l.unbind_s()

# ----------------------------------------------------------------------
# get list of machines from RHN
if len(sys.argv) == 2 and (sys.argv[1] == '--list'):
    getlist()

#get details from a host
elif len(sys.argv) == 3 and (sys.argv[1] == '--host'):
    host = sys.argv[2]
    getdetails(host)

else:
    print "usage --list or --host <hostname>"
    sys.exit(1)
