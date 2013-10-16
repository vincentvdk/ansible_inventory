#!/usr/bin/python
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
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program. If not, see <http://www.gnu.org/licenses/>.

import ldap
import re
import sys
import operator
import os
import shlex

try:
    import simplejson as json
except ImportError:
    import json

# establish connection with LDAP server
try:
    l = ldap.initialize(os.getenv("LDAPHOST", ""))
    username = os.getenv("LDAPBINDDN", "")
    password = os.getenv("LDAPBINDPW", "")
    l.set_option(ldap.OPT_PROTOCOL_VERSION,ldap.VERSION3)
    l.bind_s(username, password, ldap.AUTH_SIMPLE)

except ldap.LDAPError, e:
    print e

# LDAP variables
baseDN = os.getenv("LDAPBASEDN", 'ou=ansible, dc=ansible, dc=local')
searchScope = ldap.SCOPE_SUBTREE
attrs = None

# We only want the groups and not groups + computer CNs
groupsearchFilter = '(&(objectClass=groupOfNames)(cn=*))'

# ------------------------------------------------------------------
# function to split the ansibleVar (key=value) in a hashed key value.

#def generatekv(ansibleAttribute):
#    var = {}
#    attr = re.match(r'(.*)=(.*)', ansibleAttribute)
#    key = attr.group(1)
#    value = attr.group(2)
#    var[key] = value
#    return var

def generatekv(ansibleAttribute):
    attr = re.match(r'(.*)=(.*)', ansibleAttribute)
    key = attr.group(1)
    value = attr.group(2)
    bla = (key,value)
    var = (key,value)
    return var

# -------------------------------------------------------------------
# define if a groupmember is a host or a child group
#
def detect_group():
    groupsearchfilter = '(objectClass=ansibleGroup)'
    result = l.search_s(baseDN, searchScope, groupsearchfilter)
    groups = []
    for item in result:
        res = item[1]
        groupname = res['cn'][0]
        groups.append(groupname)
    return groups

# -------------------------------------------------------------------
# get a list of groups with their hosts

def getlist():
    try:
        inv = {}
        result = l.search_s(baseDN, searchScope, groupsearchFilter)
        # putting group list here otherwise it gets called for each available
        # group in ldap -> keeps growing
        groups = detect_group()
        for item in result:
            res = item[1]
            group = res['cn'][0]
            hostgroup = [ ]
            varlist = [ ]
            children = [ ]
            res = dict(item[1])
            #print res
            for key, value in res.iteritems():
                if key == "member":
                    for item in value:
                        host = re.match(r'cn=([^,]*)', item)
                        host = host.group(1)
                        if host in groups:
                            children.append(host)
                        else:
                            hostgroup.append(host)
                if key == "ansibleGroupVar":
                    for item in value:
                        ansiblevar = generatekv(item)
                        varlist.append(ansiblevar)
            inv[group] = {"hosts": hostgroup}
            inv[group]['vars'] = dict(varlist)
            inv[group]["children"]= children
        print json.dumps(inv, sort_keys=True, indent=2)

    except ldap.LDAPError, e:
        print e

    l.unbind_s()

# --------------------------------------------------------------------
# get all attributes from a host

def getdetails(host):
    hostsearchFilter = "cn=%s" % host
    details = {}
    varlist = []
    result = l.search_s(baseDN, searchScope, hostsearchFilter)
    for item in result:
        res = dict(item[1])
        for key, values in res.iteritems():
            if key == "ansibleVar":
                for val in values:
                    # Ensure we safely convert values of the form
                    # ansibleVar: key=val=x=y=z
                    for arg in shlex.split(val):
                        k, v = arg.split('=', 1)
                        valuelist = v.split(',')
                        varlist.append((k, valuelist))
        details = dict(varlist)

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
