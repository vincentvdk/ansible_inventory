#!/usr/bin/python

import xmlrpclib
import operator
import sys

try:
    import json
except ImportError:
    import simplejson as json

pwd = ""
saturl = ""
user = ""

# RHN connection 
client = xmlrpclib.Server(saturl, verbose=0)
session = client.auth.login(user, pwd)

# get all groups from RHN
groups = client.systemgroup.listAllGroups(session)

# ---------------------------------------------------------------------------
# Get the name of each group and find all hosts in it and
# add it to the hashmap

#grp = { }

def getlist():
    grp = { }
    for item in groups:
        group = item.get('name')
        grp[group] = []
        machines = client.systemgroup.listSystems(session, item['name'])
        for m in machines:
            sysid = int(m['id'])
            ip = client.system.getNetwork(session, sysid)
            grp[group].append(ip['hostname'])
            #grp[group].append(m['name'])
    print json.dumps(grp)
    sys.exit(0)

# --------------------------------------------------------------------------

def getdetails(host):
    details = { }
    hosts = client.system.listUserSystems(session)
    for h in hosts:
        if h.get('name') == host:
            sysid = int(h['id'])
            ip = client.system.getNetwork(session, sysid)
            #details[host].append(ip['ip'])
            details['ipaddr'] = ip['ip']
            details['rhid'] = str(sysid)
            details['rhsysname'] = host
    #print json.dumps(details, sort_keys=True, indent=2)
    print json.dumps(details)
    sys.exit(0)

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
