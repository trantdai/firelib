"""
##############################################
*Author:   Dai Tran
*Email:    trantdaiau@gmail.com
*Project:  Firewall Automation
*Script:   Common library
*Release:  Version 1.1
##############################################
"""

import argparse
import ast
import re
import sys
import time
import ipaddress
import base64
from collections import OrderedDict
from typing import List, Optional

from . import constants as common_constants

"""
Contains some utility classes to do with IP address support.
"""


class InvalidIPError(ValueError):
    """
    Exceptions thrown on parsing invalid IP strings
    """
    pass


class _IPBase:
    """
    Replaced by common/objects.py
    """

    def __init__(self, ip_str):
        self._str = ip_str
        self._parse()
        self._check()

    def _parse(self):
        """Parse the content of IP string
        """

    def _check(self):
        """Check the content of IP string
        """

    def get_element_name(self):
        return 'ip-netmask'

    def should_warn(self): return False

    def __str__(self):
        return self._str


class _IPFixed(_IPBase):
    """
    Replaced by common/objects.py
    IP implementation for a single host address.
    """

    def get_name(self):
        return 'H-' + self._str

    def digit(self, x):
        return self._digits[x]

    def _parse(self):
        try:
            address = ipaddress.ip_address(bytearray(self._str))
        except ValueError:
            raise InvalidIPError(self._str + ' is not a valid IP address!')

        self._digits = [int(x) for x in self._str.split('.')]

    def _check(self):
        def in_range(x):
            return 0 <= x <= 255

        regex = re.compile(r'(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})')
        match = regex.match(self._str)
        if not match:
            return False
        if match.group(0) != self._str:
            return False
        if not all(in_range(int(match.group(x))) for x in range(1, 5)):
            raise InvalidIPError(self._str + ' is not a valid IP address!')


class _IPRange(_IPBase):
    """
    Replaced by common/objects.py
    IP implementation for a range of hosts of the form:
    a.b.c.d-w.x.y.z
    """

    def get_element_name(self):
        return 'ip-range'

    def get_name(self):
        return 'R-' + self._str

    def _parse(self):
        beg_str = self._str[:self._str.find('-')]
        end_str = self._str[self._str.find('-') + 1:]
        self._beg = _IPFixed(beg_str)
        self._end = _IPFixed(end_str)

    def _check(self):
        if not all([self._end.digit(x) >= self._beg.digit(x)
                    for x in range(4)]):
            raise InvalidIPError(self._str + ' is not a valid IP range!')


class _IPNetwork(_IPBase):
    """
    Replaced by common/objects.py
    IP implementation for a range of hosts of the form:
    a.b.c.d/x
    """

    def get_name(self):
        return 'N-{0}-{1}'.format(self._base, self._subnet)

    def should_warn(self):
        return self._subnet <= 24

    def _parse(self):
        try:
            address = ipaddress.ip_network(bytearray(self._str))
        except ValueError:
            raise InvalidIPError(self._str + ' is not a valid IP network!')

        base_ip = self._str[:self._str.find('/')]
        self._base = _IPFixed(base_ip)
        try:
            self._subnet = int(self._str[self._str.find('/') + 1:])
        except ValueError:
            raise InvalidIPError(
                self._str + ' does not contain a valid subnet!')

    def _check(self):
        if not 1 <= self._subnet <= 32:
            raise InvalidIPError(self._str + ' is not a valid IP network!')


class _FQDN(_IPBase):
    """
    Replaced by common/objects.py
    IP implementation for a single host in the form fqdn:
    abc.com
    """

    def get_element_name(self):
        return 'fqdn'

    def get_name(self):
        return self._str

    def _parse(self):
        pass

    def _check(self):
        """
        Ensures that each segment:
        + contains at least one character and a maximum of 63 characters
        + consists only of allowed characters
        + doesn't begin or end with a hyphen.

        if len(self._str) > 255:
                raise InvalidIPError(self._str + ' is not a valid FQDN!')
        if self._str[-1] == ".":
                self._str = self._str[:-1] # strip exactly one dot from the right, if present
        allowed = re.compile(r"(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
        if not all(allowed.match(x) for x in self._str.split(".")):
                raise InvalidIPError(self._str + ' is not a valid FQDN!')
        """
        if len(self._str.split('.')) < 2:
            raise InvalidIPError(self._str + ' is not a valid FQDN!')


class IP:
    """
    Replaced by common/objects.py
    Public class for interacting with IP addresses.
    When instantiating the class with an IP string, the format will be
    checked and can throw an InvalidIPError if not valid.
    """

    def __init__(self, ip_str):
        self._parse(ip_str)

    def get_element_name(self):
        """
        Return the xpath name of the ip type.
        """
        return self._impl.get_element_name()

    def get_name(self):
        """
        Return the name of the address object.
        """
        return self._impl.get_name()

    @staticmethod
    def is_valid_hostname(hostname):
        """
        Ensures that each segment:
        + contains at least one character and a maximum of 63 characters
        + consists only of allowed characters
        + doesn't begin or end with a hyphen.
        """
        # Check if hostname is actually an IP
        regex = re.compile(r'(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})')
        match = regex.match(hostname)
        if match:
            return False
        # If is it not an IP, verify further
        if len(hostname) > 255:
            return False
        if hostname[-1] == ".":
            # strip exactly one dot from the right, if present
            hostname = hostname[:-1]
        allowed = re.compile(r"(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
        return all(allowed.match(x) for x in hostname.split("."))

    @staticmethod
    def is_ip_in_network_as_other(ip, other_ip, netmask):
        """
        Check if ip is same network as other_ip/netmask.
        If yes, return True. Else, return False.
        ip, other_ip: String of IP address
        netmask: String of netmask in full or short form 255.255.255.0 or /24
        """
        ipaddr = ipaddress.ip_address(str(ip))
        full_other_ip = str(other_ip + '/' + netmask)
        net = ipaddress.ip_network(full_other_ip, strict=False)
        return bool(ipaddr in net)

    def should_warn(self):
        """
        If the ip range is very broad this will return True
        """
        return self._impl.should_warn()

    def _parse(self, ip_str):
        """
        Perform the parsing of the ip string and setup the private
        implementation.
        """
        if '-' in ip_str:
            # could be ip range or abc-xyz.com
            try:
                self._impl = _IPRange(ip_str)
            except InvalidIPError:
                self._impl = _FQDN(ip_str)
        elif '/' in ip_str:
            self._impl = _IPNetwork(ip_str)
        elif IP.is_valid_hostname(ip_str):
            self._impl = _FQDN(ip_str)
        else:
            self._impl = _IPFixed(ip_str)

    def __str__(self):
        return self._impl._str


def is_address_in_range(address, iprange):
    """
    - Input:
            + address: Valid bare string value. It can be fqdn, single ip,
            ip-range or ip network
            + iprange: Valid bare string value of IP address range like 1.1.1.1-1.1.1.5
            or network or even single IP
    - Output: False if address is not in range else True
    """
    # If address is a single IP that has /32 posfix, remove postfix
    if ('/' in address) and (address.split('/')[1] == '32'):
        address = address.split('/')[0]
    # If address is a fqdn
    """
    if util.IP.is_valid_hostname(address):
        return False
    """
    # If address is a network
    if '/' in address:
        # If range is network
        if '/' in iprange:
            if ipaddress.ip_network(
                bytearray(address)).subnet_of(
                ipaddress.ip_network(
                    bytearray(iprange))):
                return True
        # If range is range
        elif '-' in iprange:
            ipaddr = ipaddress.ip_network(bytearray(address))
            # ipaddress.ip_address((u'1.2.3.0')
            fhost, lhost = ipaddr[0], ipaddr[-1]
            range_fhost = ipaddress.ip_address(
                bytearray(iprange.split('-')[0]))
            range_lhost = ipaddress.ip_address(
                bytearray(iprange.split('-')[1]))
            if range_fhost <= fhost and lhost <= range_lhost:
                return True
        # else: #If range is single IP, return False at bottom
    elif '-' in address:  # If address is a range
        # If range is network
        if '/' in iprange:
            fhost = ipaddress.ip_address(bytearray(address.split('-')[0]))
            lhost = ipaddress.ip_address(bytearray(address.split('-')[1]))
            ipaddr = ipaddress.ip_network(bytearray(iprange))
            range_fhost, range_lhost = ipaddr[0], ipaddr[-1]
            if range_fhost <= fhost and lhost <= range_lhost:
                return True
            """
            elif self.type == constants.ADDRESS_TYPE_FQDN:
                return False
            """
        elif '-' in iprange:  # If range is range
            fhost = ipaddress.ip_address(bytearray(address.split('-')[0]))
            lhost = ipaddress.ip_address(bytearray(address.split('-')[1]))
            range_fhost = ipaddress.ip_address(
                bytearray(iprange.split('-')[0]))
            range_lhost = ipaddress.ip_address(
                bytearray(iprange.split('-')[1]))
            if range_fhost <= fhost and lhost <= range_lhost:
                return True
        # else: #If range is single IP, return False at bottom
    elif IP.is_valid_hostname(address):  # If address is a fqdn
        if address == iprange:
            return True
    else:  # If address is a single IP
        # If range is network
        if '/' in iprange:
            if ipaddress.ip_address(bytearray(address)) in \
                    ipaddress.ip_network(bytearray(iprange)):
                return True
            """
            elif self.type == constants.ADDRESS_TYPE_FQDN:
                return False
            """
        elif '-' in iprange:  # If range is range
            range_fhost = ipaddress.ip_address(
                bytearray(iprange.split('-')[0]))
            range_lhost = ipaddress.ip_address(
                bytearray(iprange.split('-')[1]))
            ipaddr = ipaddress.ip_address(bytearray(address))
            if range_fhost <= ipaddr <= range_lhost:
                return True
        else:  # If range is a single IP
            if address == iprange:
                return True
    return False


def is_address_public(address, publicnet=None):
    """
    - Input:
            + address: Valid bare string value. It can be fqdn, single ip,
            ip-range or ip network.
            + publicnet: List of all public ranges
    - Output: True if address is public address else False
    """
    if publicnet is None:
        publicnet = common_constants.IPV4_ALL_PUBLIC_RANGES
    for net in publicnet:
        if is_address_in_range(address, net):
            return True
    return False


def convert_string_to_base64(text):
    """
    btext: 8-bit binary byte data such as b'text123'
    """
    return base64.b64encode(text)


def print_progress(
        iteration,
        total,
        prefix='',
        suffix='',
        decimals=1,
        length=50,
        fill='#'):
    """
    Print a progress bar to the console.
    Note that this does assume that your console is at least 50 chars wide and that it supports
    CRs properly.
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 *
                                                     (iteration / float(total)))
    filledLength = int(length * iteration // total)
    progbar = fill * filledLength + '-' * (length - filledLength)
    sys.stdout.write('\r%s |%s| %s%% %s\r' %
                     (prefix, progbar, percent, suffix))
    sys.stdout.flush()
    # Print New Line on Complete
    if iteration == total:
        print('')


def wait_for_job(session, job_id):
    """
    Wait for a commit job to complete and show the progress.
    Note: Doesn't have a timeout so if the job hangs we will still wait.
    """

    prog = 0
    while prog < 100:
        result = session.get_commit_progress(job_id)
        prog = int(result.get_progress())
        print_progress(prog, 100, 'Commit progress:', 'complete')
        time.sleep(1)
    result_str = result.get_result()
    print(('Commit finished with result: {0}'.format(result_str)))
    return result_str == 'OK'


def get_user_confirm(prompt):
    """
    Give the user a prompt and ask them whether to continue.
    The prompt should include something like [Y/N] at the end.
    Returns True if they confirm, false otherwise.
    """

    while True:
        #check = eval(input(prompt))
        check = ast.literal_eval(input(prompt))
        if check.upper() == 'N':
            return False
        if check.upper() == 'Y':
            return True


def append_prefix(strlist, prefix):
    """
    Append the prefix to the string or string list strlist
    Input:
    - strlist: a string of list of strings
    - postfix: Domain name prefix
    Output:
    - Check if strlist already contains prefix
    - If yes, just return the strlist
    - If not, return strlist with prefix
    """
    if isinstance(strlist, str):
        if prefix in strlist:
            return strlist
        return prefix + strlist
    else:
        return [
            element if element.endswith(prefix) else prefix +
            element for element in strlist]


def append_postfix(strlist, postfix):
    """
    Append the postfix to the string or string list strlist
    Input:
    - strlist: a string of list of strings
    - postfix: Domain name postfix
    Output:
    - Check if strlist already contains posfix
    - If yes, just return the strlist
    - If not, return strlist with postfix
    """
    if isinstance(strlist, str):
        if common_constants.CONTOSO_INTERNAL_POSTFIX_PROD in strlist:
            return strlist
        return strlist + postfix
    else:
        return [element if element.endswith(
            common_constants.CONTOSO_INTERNAL_POSTFIX_PROD) else
            element + postfix for element in strlist]


def is_firewall_pan(firewall):
    """
    Input
    -----
            firewall: str
    Return
    ------
            True if firewall is PAN, else False
    """
    panregex = common_constants.REGEX_PAN_FIREWALL_CLUSTER
    if re.search(panregex, firewall.lower()):
        return True
    return False


def is_ip_address(the_address):
    """
    Return True if the_address is an ip address, False if not
    """
    regex = common_constants.REGEX_IPV4_SIMPLE
    result = re.search(regex, the_address)
    if result:
        return True
    return False


def get_firewalls_from_list(nodelist):
    """
    Input: Mixture of ordered IP and firewall names
    Output: Ordered list of firewalls
    """
    fwregex = common_constants.REGEX_ALL_FIREWALL_CLUSTER
    firewall_path = [e for e in nodelist if re.search(fwregex, e)]
    return append_postfix(firewall_path, ".contoso.net")


def replace_sublist_in_a_list_with_string(mainlist, sublist, string):
    """
    - mainlist: The list to be touch
    - sublist: The sublist in the mainlist to be replaced by string
    - string: The string to replace sublist in mainlist
    Replace all occurances of sublist in mainlist with string and return new mainlist
    """
    occur = [index for index, value in enumerate(
        mainlist) if value == sublist[0]]
    for start in occur:
        if mainlist[start:start + len(sublist)] == sublist:
            mainlist[start:start + len(sublist)] = string
        # If reaching the end of occur list
        if len(occur) - 1 == occur.index(start):
            break


def replace_sublists_in_a_list_with_strings(mainlist,
                                            old_sublist_list, new_string_list):
    """
    - mainlist: The list to be touch
    - old_sublist_list: The list of sublists shown in the mainlist to be replaced by string list
    - new_string_list: The list of new strings to replace old sublist list in mainlist
    Replace all occurances of old_sublist_list in mainlist with strings of the same indexes in   and return new mainlist
    """
    for sublist_index, sublist in enumerate(old_sublist_list):
        occur = [index for index, value in enumerate(
            mainlist) if value == sublist[0]]
        for start in occur:
            if mainlist[start:start + len(sublist)] == sublist:
                # Remove sublist from the mainlist
                mainlist[start:start + len(sublist)] = []
                # Insert new string in
                mainlist.insert(start, new_string_list[sublist_index])
            # If reaching the end of occur list
            if len(occur) - 1 == occur.index(start):
                break
    return mainlist


def get_index_of_string_list_item_that_has_pattern(str_list, pattern):
    """
    - str_list: List of strings
    - pattern: Matching pattern
    - Return the index of the list item that contains the pattern
    else return None
    """
    for i, v in enumerate(str_list):
        if pattern in v:
            return i
    return None


def get_firewall_names_from_string(instr):
    """Extract a list of non-FQDN firewall cluster names from string.
    Initial design is for VPN deco.

    Args:
            instr (str)

    Returns: List of non-FQDN firewall cluster names in order

    """
    regex = re.compile(common_constants.REGEX_ALL_FIREWALL_CLUSTER_FINDALL)
    # List of clusternames
    clusternames = regex.findall(instr.lower())
    # Remove duplicate list items
    clusternames = list(OrderedDict.fromkeys(clusternames))

    return clusternames


def is_exact_match_in_string(search_str: str, target_str: str, flags: int = 0) -> bool:
    """Search 1.1.1.1 in 'abc 1.1.1.12 def' return False
    Search 1.1.1.1 in 'abc 1.1.1.1 def' return True

    :param search_str: String to look for
    :type search_str: str
    :param target_str: Target string of the exact search]
    :type target_str: str
    :param flags: re flag re.MULTILINE or combined flags like re.MULTILINE | re.IGNORECASE, defaults to 0
    :type flags: int
    :return: [description]
    :rtype: bool
    """
    regex = re.compile(r"\b{0}\b".format(search_str), flags)
    m = regex.search(target_str)
    if m:
        return True
    return False


def extract_first_match_in_string(pattern: str, target_str: str, flags: int = 0) -> str:
    """[summary]

    :param pattern: Regular expression
    :type pattern: str
    :param target_str: Target string of the search
    :type target_str: str
    :param flags: re flag re.MULTILINE or combined flags like re.MULTILINE | re.IGNORECASE, defaults to 0
    :type flags: int, optional
    :return: First string matching pattern or None
    :rtype: str
    """
    regex = re.compile(r"\b{0}\b".format(pattern), flags)
    m = regex.search(target_str)
    # To find all matches, use regex.findall(target_str)
    if m:
        return m.group(0)
    return None


def extract_all_matches_from_string(pattern: str, target_str: str, flags: int = 0) -> List:
    """[summary]

    :param pattern: Regular expression
    :type pattern: str
    :param target_str: Target string of the search
    :type target_str: str
    :param flags: re flag re.MULTILINE or combined flags like re.MULTILINE | re.IGNORECASE, defaults to 0
    :type flags: int, optional
    :return: List of strings that match the 'pattern'
    :rtype: List
    """
    regex = re.compile(r"{0}".format(pattern), flags)
    # Remove '\r' from the end of each match and return the list
    return [m.rstrip() if '\r' in m else m for m in regex.findall(target_str)]


def extract_substring_between_two_strings(start: str, end: str, target_str: str, inclusive=False) -> Optional[str]:
    """Extract substring from target_str. If inclusive, start and end are included in the substring

    :param start: Start string
    :type start: str
    :param end: End string
    :type end: str
    :param target_str: String to be extracted from
    :type target_str: str
    :param inclusive: [description], defaults to False
    :type inclusive: bool, optional
    :return: Extracted substring
    :rtype: str if found else None
    """
    pattern = r"{0}(.*){1}".format(start, end)
    regex = re.compile(pattern)
    #regex = re.compile(r"{0}(.*){1}".format(start, end))
    match = regex.search(target_str)
    if match:
        if inclusive:
            return match.group(0)
        return match.group(1)
    return None


def parse_command_line_arguments(description: str) -> List:
    """
    Define and parse command line arguments
    :return: a list of keywords passed to the command line
    """
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument("keywords", type=str, metavar='keyword', nargs='+', help="keyword to consider")

    return list(parser.parse_args().keywords)


def get_sort_key(pattern: str, target_str: str) -> str:
    """https://stackoverflow.com/questions/1082413/sort-a-list-of-strings-based-on-regular-expression-match-or-something-similar

    :param pattern: Regular expression
    :type pattern: str
    :param target_str: Target string/text of the search using pattern
    :type target_str: str
    :return: First string matching pattern or '&'
    :rtype: str
    """
    regex = re.compile(r"\b{0}\b".format(pattern))
    m = regex.search(target_str)
    return m.group(0) if m else '&'


def remove_duplicates_from_order_list(duplist: List) -> List:
    """Remove duplicates from duplist while keeping the same order
    https://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-whilst-preserving-order

    :param duplist: List with duplicates
    :type duplist: List
    :return: List without duplicates in the same order
    :rtype: List
    """
    seen = set()
    seen_add = seen.add
    return [x for x in duplist if not (x in seen or seen_add(x))]
