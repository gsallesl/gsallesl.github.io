#!/usr/bin/env python
# ProxyCommandResolver
# Returns a variable SSH ProxyCommand, depending on the network you are currently connected to, for a fixed SSH Host.
# GSL - 2015

import sys
import xml.etree.ElementTree as ET
import subprocess
from os.path import expanduser

HOME = expanduser("~")
CONFIG = HOME+'/.ssh/pcr.xml'

class DefaultNetworkInterfaceName:
    def __init__(self, interface=None):
        if interface is not None:
            local_interface = self.getDefaultNetworkInterfaceName()
            self.value = True if interface == local_interface else False

    def getDefaultNetworkInterfaceName(self):
        """Read the default network interface directly from /proc."""
        with open("/proc/net/route") as fh:
            for line in fh:
                fields = line.strip().split()
                if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                    continue
                return fields[0]

class DNSSearchName:
    def __init__(self, name=None):
        if name is not None:
            local_dns=None
            self.value = True if name == local_dns else False

class LocalConnectionName:
    def __init__(self, name=None):
        if name is not None:
            local_cnx = self.getLocalConnectionName()
            self.value = True if name == local_cnx else False

    def getLocalConnectionName(self):
        dnin=DefaultNetworkInterfaceName()
        ifname=dnin.getDefaultNetworkInterfaceName()
        ps = subprocess.Popen(('nmcli', 'c', 'status'), stdout=subprocess.PIPE)
        ps.wait()
        output = subprocess.check_output(('grep', ifname), stdin=ps.stdout)
        return output.split()[0]


import socket, struct
class DefaultNetworkIPAddress:
    def __init__(self, address=None):
        if address is not None:
            local_address = self.getDefaultNetworkIPAddress()
            self.value = True if address == local_address else False

    def getDefaultNetworkIPAddress(self):
        """Read the default gateway directly from /proc."""
        with open("/proc/net/route") as fh:
            for line in fh:
                fields = line.strip().split()
                if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                    continue
                return socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))

def result(host, proxy_command):
    sys.stderr.write("\033[93mConnection to %s via ProxyCommand: %s\033[0m\n" % (host, proxy_command))
    print proxy_command
    sys.exit(0)


def main(host):
    tree = ET.parse(CONFIG)
    root = tree.getroot()
    for proxyhost in root.iter('ProxyHost'):
        #print ("comparing to: %s" % proxyhost.find('Host').text)
        # we find the host:
        if proxyhost.find('Host').text.lower() == host.lower():
            # we look at the differents Proxy setup
            for proxy in proxyhost.iter('Proxy'):
                # if there is no condition, that's a fallback choice, we chose it!
                if proxy.get('fallback') == "true":
                    result(proxyhost.find('Host').text, proxy.find('ProxyCommand').text)
                else:
                    # is one of the condition set working?
                    for condition in proxy.iter('Condition'):
                        match=True
                        for requirement in condition:
                            obj=globals()[requirement.tag](requirement.text)
                            #res = getattr(obj, "__init__")
                            if not obj.value:
                                match=False
                                break
                        if match is True:
                            result(proxyhost.find('Host').text, proxy.find('ProxyCommand').text)
                        match=True
    sys.stderr.write("\033[91mHost %s not found!\033[0m\n" % host)
    sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) <> 2:
        sys.stderr.write(sys.argv[0] + ": No argument given!\n")
        sys.exit(1)
    main(sys.argv[1])



