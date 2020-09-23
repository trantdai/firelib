import re

from ..common import constants as common_constants
from . import constants, panfwapi


def get_firewall_interface_address_map(active_firewalls, ignored=True):
    """
    Input:
    - active_firewalls: A list of FQDN lowercase active PAN firewalls which can be retrieved from
    pano.show_active_devices()
    - ignored: If True, script skips all firewalls in constants.FIREWALL_PATH_IGNORED_FIREWALLS
    Output: Build and return a dictionary of keys and values: FQDN PAN firewalls and their interface addresses.
    """
    paipmap = dict()
    #print("Building the map of firewalls and their interface addresses via API... Please be PATIENT...\n")
    for pa in active_firewalls:
        if ignored:
            # If the firewall is in the ignored list, skip to next loop
            if pa.split('.')[0] in constants.FIREWALL_PATH_IGNORED_FIREWALLS:
                continue

        palosess = panfwapi.PanFWAPISession(pa)
        # palosess.get_palo_api_key()
        try:
            addresses = palosess.get_firewall_interface_addresses()
        except Exception:
            # Connection to some firewalls like frafwp300 and tusfwo fails
            print((
                "Connection to {} FAILED! Please check access to firewall manually.\n".format(pa)))
            #print("Error message: {}".format(e))
            print("Moving onto next step...\n")
            continue
        # Remove netmask and "N/A" from the FW addresses
        paipmap[pa] = [address[:address.index(
            "/")] for address in addresses if address != "N/A"]
        # Check if any unknown IPs in srclist is a firewall ip address

    return paipmap


def replace_addresses_with_pan_names(nodelist, paipmap):
    """
    Inputs: List of network nodes derived from parsing traceroute and dictionary of PAN firewall to IP address map
    Output: New list where PAN interface addresses are replaced by PAN names
    """
    #ipregex = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    ipregex = common_constants.REGEX_IPV4_SIMPLE
    # Search for IPs in the nodelist
    unknowns = [e for e in nodelist if re.search(ipregex, e)]
    if unknowns:
        for ip in unknowns:
            # Check if unknown IP is PAN firewall address
            palos = [
                palo for palo,
                addresses in list(paipmap.items()) if ip in addresses]
            """
            print("ip: {}".format(ip))
            for palo, addresses in paipmap.items():
                print("address: {}".format(addresses))
                print(str(ip) in addresses)
            """
            #print("palos: {}".format(palos))
            # If yes, replace IP with firewall name
            if palos:
                index = nodelist.index(ip)
                #print("index: {}".format(index))
                nodelist[index] = palos[0]
    #print("nodelist: {}".format(nodelist))
    return nodelist
