"""
##############################################
*Author:   Dai Tran
*Email:    trantdaiau@gmail.com
*Project:  Firewall Automation
*Script:   Common library
*Release:  Version 1.1
##############################################
"""

import ipaddress
import re
from . import firelogging

# START LOGGING TO FILE
logger = firelogging.FireLogger(name=__name__).firelogger


class InvalidIPError(ValueError):
    """
    Exceptions thrown on parsing invalid IP strings
    """
    pass


class InvalidServiceError(ValueError):
    """
    Exceptions thrown on parsing invalid service strings
    """
    pass


class _ObjectBase:
    def __init__(self, value, name=None):
        """
        Base class to represent the input of address/group and service/group

        Parameters
        ----------
        value: input str
                In format of 1.1.1.1, 1.1.1.1-1.1.1.5, 1.1.1.0/24, fqdn, tcp/443,
                tcp/1-65535/7005.
                value = name if self is firewall object.
        name: str
                Optional, if not provided, standard name is used. Used for situation
                to add object where the name is different from standard name.


        Make sure value is <type 'str'>, not <type 'unicode'>. Otherwise,
        <type 'unicode'> would cause exception in connectors.convert_dict_to_object
        """
        self._value = str(value)
        self._name = name
        """
        self._parse()
        self._check()
        """

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self._value = v

    @property
    def name(self):
        if self._name is not None:
            return self._name
        else:
            return self._value

    @name.setter
    def name(self, n):
        self._name = n

    def __str__(self):
        return self._value

    def _parse(self):
        pass

    def _check(self):
        pass

    def get_type(self):
        """
        ip host
        ip range
        ip netmask
        ip fqdn
        ip object
        ip group object
        service
        service range
        service complex
        service object
        service group object
        url
        """
        # return 'ip host'
        pass

    def get_pan_type(self):
        pass

    def get_element_name(self):
        """
        For backward compatibility with palolib\objects.Address.build_xml_object
        """
        return self.get_pan_type()


class _IPBase(_ObjectBase):
    """
    To replace InputObject that is to be obsolete
    """

    def __init__(self, value, name=None):
        _ObjectBase.__init__(self, value, name)
        self._parse()
        self._check()

    """
    getter and setter of properties name and value are inherited from _ObjectBase
    """

    def get_type(self):
        return 'ip host'

    def get_pan_type(self):
        return 'ip-netmask'


class IPHost(_IPBase):
    def _check(self):
        try:
            # ipaddress.ip_address(bytearray(self._value))
            ipaddress.ip_address(self._value)
        except ValueError:
            raise InvalidIPError(
                '\n\n*** Error: ' +
                self._value +
                ' is not a valid IP address! ***\n')

    @property
    def name(self):
        # return _IPBase.name.fget(self)
        if self._name is not None:
            return self._name
        else:
            return 'H-' + self._value
    """
    As @property of name is override, setter of name needs to be defined/override
    as well. Otherwise, IPHost.name = new_name raises AttributeError: can't set attribute.
    https://stackoverflow.com/questions/21844240/python-extending-properties-like-youd-extend-a-function?noredirect=1&lq=1 => "A.prop.fset(self, value)"
    #37663266 => "Unless your property doesn't have a setter, you have to define both the setter and the getter in B even if you only change the behaviour of one of them."
    https://stackoverflow.com/questions/1021464/how-to-call-a-property-of-the-base-class-if-this-property-is-being-overwritten-i/37663266

    """
    @name.setter
    def name(self, n):
        # pylint: disable=no-member
        _IPBase.name.fset(self, n)


class IPRange(_IPBase):

    @property
    def name(self):
        if self._name is not None:
            return self._name
        else:
            return 'R-' + self._value

    @name.setter
    def name(self, n):
        # pylint: disable=no-member
        _IPBase.name.fset(self, n)

    def _parse(self):
        beg_str = self._value[:self._value.find('-')]
        end_str = self._value[self._value.find('-') + 1:]
        self._beg = IPHost(beg_str)
        self._end = IPHost(end_str)

    def _check(self):
        try:
            # Python2 code
            # begip = ipaddress.ip_address(bytearray(self._beg.value))
            # endip = ipaddress.ip_address(bytearray(self._end.value))
            begip = ipaddress.ip_address(self._beg.value)
            endip = ipaddress.ip_address(self._end.value)
        except ValueError:
            raise InvalidIPError(
                '\n\n*** Error: ' +
                self._value +
                ' is not a valid IP address range! ***\n')
        if begip and endip and begip >= endip:
            raise InvalidIPError(
                '\n\n*** Error: ' +
                self._value +
                ' is not a valid IP address range! ***\n')

    def get_type(self):
        return 'ip range'

    def get_pan_type(self):
        return 'ip-range'


class IPNetwork(_IPBase):

    @property
    def name(self):
        if self._name is not None:
            return self._name
        else:
            return 'N-{0}-{1}'.format(self._base, self._prefixlen)

    @name.setter
    def name(self, n):
        # pylint: disable=no-member
        _IPBase.name.fset(self, n)

    def _parse(self):
        self._base = self._value[:self._value.find('/')]
        # _prefixlen like /24
        self._prefixlen = int(self._value[self._value.find('/') + 1:])

    def _check(self):
        try:
            # Python2 code
            # ipaddress.ip_network(bytearray(self._value))
            ipaddress.ip_network(self._value)
        except ValueError:
            raise InvalidIPError(
                '\n\n*** Error: ' +
                self._value +
                ' is not a valid IP address network! ***\n')

    def get_type(self):
        return 'ip netmask'


class IPFQDN(_IPBase):

    def _parse(self):
        if self._value[-1] == ".":
            # strip exactly one dot from the right, if present
            self._value = self._value[:-1]

    def _check(self):
        """
        Ensures that each segment:
        + contains at least one character and a maximum of 63 characters
        + consists only of allowed characters
        + doesn't begin or end with a hyphen.
        """
        if not self.is_hostname_valid(self._value):
            raise InvalidIPError(
                '\n\n*** Error: ' +
                self._value +
                ' is not a valid IP FQDN! ***\n')

    def get_type(self):
        return 'ip fqdn'

    def get_pan_type(self):
        return 'fqdn'

    @staticmethod
    def is_hostname_valid(hostname):
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
        # Haven't tested this regex https://www.regextester.com/98986
        return all(allowed.match(x) for x in hostname.split("."))


class FWObject(_ObjectBase):
    """
    Public class for representing named firewall object
    """

    def __init__(self, value, name, objtype):
        """
        Parameters
        ----------
        value: str
                In the format of object name
        name: str
                Optional, name of the the object that is different from standard name
        type: str
                Object type: ip object, ip group object, service object, service group object
        """
        _ObjectBase.__init__(self, value, name)
        self._type = objtype

    def get_type(self):
        return self._type

    def get_pan_type(self):
        return None


class IPObject:
    """
    Public class for interacting with IP addresses.
    When instantiating the class with an IP string, the format will be
    checked and can throw an InvalidIPError if not valid.
    """

    def __init__(self, addr_str, name=None):
        """
        Parameters
        ----------
        addr_str: str
                In the format of 1.1.1.1, 1.1.1.0/24, 1.1.1.1-1.1.1.5, fqdn
        name: str
                Optional, name of the object that is different from standard name
        """
        """
        Make sure addr_str is <type 'str'>, not <type 'unicode'>. Otherwise,
        <type 'unicode'> would cause exception in connectors.convert_dict_to_object()
        """
        self._parse(str(addr_str), name)

    def _parse(self, addr_str, name=None):
        """
        Perform the parsing of the ip string and setup the private
        implementation.
        """
        if IPFQDN.is_hostname_valid(addr_str):
            self._instance = IPFQDN(addr_str, name)
        elif '-' in addr_str:
            self._instance = IPRange(addr_str, name)
        elif '/' in addr_str:
            self._instance = IPNetwork(addr_str, name)
        else:
            self._instance = IPHost(addr_str, name)

    @property
    def name(self):
        return self._instance.name

    @name.setter
    def name(self, n):
        self._instance.name = n

    @property
    def value(self):
        return self._instance.value

    @value.setter
    def value(self, v):
        self._instance.value = v

    def __str__(self):
        return self._instance._value

    def get_type(self):
        return self._instance.get_type()

    def get_pan_type(self):
        return self._instance.get_pan_type()
    """
    def get_standard_name(self):
        return self._instance.get_standard_name()
    """

    def get_element_name(self):
        return self._instance.get_element_name()


class _ServiceBase(_ObjectBase):
    """
    Base object for services provided as arguments from input
    """

    def __init__(self, value, name=None):
        _ObjectBase.__init__(self, value, name)
        self._parse()
        self._check()

    def _parse(self):
        sport = None
        # If there is source port
        if len(self._value.split('/')) == 3:
            prot, sport, port = self._value.split('/')
        else:
            prot, port = self._value.split('/')

        # Protocol
        self._prot = prot
        # Source port/range
        self._sport = sport
        # Destination port/range
        self._port = port

        logger.debug(
            'Input service string: {0}, protocol: {1}, source port: {2}, port: {3}'.format(
                self._value,
                self._prot,
                self._sport,
                self._port))

        # For naming service with source ports using postfix
        # src.<firstport>.<lastport>
        self._postfix = ''
        if self._sport is not None:
            firstport = self._sport.split(',')[0].split('-')[0]
            if '-' in self._sport.split(',')[-1]:
                lastport = self._sport.split(',')[-1].split('-')[1]
            else:
                lastport = self._sport.split(',')[-1]
            if firstport != lastport:
                self._postfix = '.src.' + firstport + '.' + lastport
            else:
                self._postfix = '.src.' + firstport

    def _check(self):
        if self._prot not in ['tcp', 'udp', 'sctp']:
            raise InvalidServiceError(
                '\n\n*** Error: ' +
                self._value +
                ' is not a valid TCP/IP service! ***\n')
        # Check source port
        if self._sport is not None:
            # If port values are comma separated
            sport_list = self._sport.split(',')
            for sport in sport_list:
                if '-' in sport:
                    beg = sport.split('-')[0]
                    end = sport.split('-')[1]
                    if (not beg.isdigit() or
                            not end.isdigit()):
                        raise InvalidServiceError(
                            '\n\n*** Error: ' + self._value + ' is not a valid TCP/IP service! ***\n')
                    if not (int(beg) >= 1 and int(end) <= 65535):
                        raise InvalidServiceError(
                            '\n\n*** Error: ' + self._value + ' is not a valid TCP/IP service! ***\n')
                    if int(beg) >= int(end):
                        raise InvalidServiceError(
                            '\n\n*** Error: ' + self._value + ' is not a valid TCP/IP service! ***\n')
                else:
                    if not sport.isdigit():
                        raise InvalidServiceError(
                            '\n\n*** Error: ' + self._value + ' is not a valid TCP/IP service! ***\n')
                    if not (int(sport) >= 1 and int(sport) <= 65535):
                        raise InvalidServiceError(
                            '\n\n*** Error: ' + self._value + ' is not a valid TCP/IP service! ***\n')

    @property
    def protocol(self):
        return self._prot

    @property
    def source_port(self):
        return self._sport

    @property
    def port(self):
        return self._port

    def get_type(self):
        return 'service'


class Service(_ServiceBase):
    """
    Class represents single service string
    """
    # def _parse(self):

    def _check(self):
        if not self._port.isdigit():
            raise InvalidServiceError(
                '\n\n*** Error: ' +
                self._value +
                ' is not a valid TCP/IP service! ***\n')
        if not (int(self._port) >= 1 and int(self._port) <= 65535):
            raise InvalidServiceError(
                '\n\n*** Error: ' +
                self._value +
                ' is not a valid TCP/IP service! ***\n')

    @property
    def name(self):
        if self._name is not None:
            return self._name
        else:
            return self._prot + '-' + self._port + self._postfix

    @name.setter
    def name(self, n):
        # pylint: disable=no-member
        _ServiceBase.name.fset(self, n)


class ServiceRange(_ServiceBase):
    """
    Class represents single service range string
    """

    def _parse(self):
        # Set self._port, self._prot etc
        _ServiceBase._parse(self)
        self._beg = self._port.split('-')[0]
        self._end = self._port.split('-')[1]

    def _check(self):
        if (not self._beg.isdigit() or
                not self._end.isdigit()):
            raise InvalidServiceError(
                '\n\n*** Error: ' +
                self._value +
                ' is not a valid TCP/IP service! ***\n')
        if not (int(self._beg) >= 1 and int(self._end) <= 65535):
            raise InvalidServiceError(
                '\n\n*** Error: ' +
                self._value +
                ' is not a valid TCP/IP service! ***\n')
        if int(self._beg) >= int(self._end):
            raise InvalidServiceError(
                '\n\n*** Error: ' +
                self._value +
                ' is not a valid TCP/IP service! ***\n')

    @property
    def name(self):
        if self._name is not None:
            return self._name
        else:
            return self._prot + '-range-' + self._beg + '-' + self._end + self._postfix

    @name.setter
    def name(self, n):
        # pylint: disable=no-member
        _ServiceBase.name.fset(self, n)

    def get_type(self):
        return 'service range'


class ServiceComplex(_ServiceBase):
    """
    Class represents single service complex string like 123,124-125,128
    """

    def _parse(self):
        # Set self._port, self._prot etc
        _ServiceBase._parse(self)
        # Get first port
        self._beg = self._port.split(',')[0].split('-')[0]
        # Get last port
        if '-' in self._port.split(',')[-1]:
            self._end = self._port.split(',')[-1].split('-')[1]
        else:
            self._end = self._port.split(',')[-1]

    def _check(self):
        # Check destination port
        # If port values are comma separated
        port_list = self._port.split(',')
        for port in port_list:
            if '-' in port:
                beg = port.split('-')[0]
                end = port.split('-')[1]
                if (not beg.isdigit() or
                        not end.isdigit()):
                    raise InvalidServiceError(
                        '\n\n*** Error: ' +
                        self._value +
                        ' is not a valid TCP/IP service! ***\n')
                if not (int(beg) >= 1 and int(end) <= 65535):
                    raise InvalidServiceError(
                        '\n\n*** Error: ' +
                        self._value +
                        ' is not a valid TCP/IP service! ***\n')
                if int(beg) >= int(end):
                    raise InvalidServiceError(
                        '\n\n*** Error: ' +
                        self._value +
                        ' is not a valid TCP/IP service! ***\n')
            else:
                if not port.isdigit():
                    raise InvalidServiceError(
                        '\n\n*** Error: ' +
                        self._value +
                        ' is not a valid TCP/IP service! ***\n')
                if not (int(port) >= 1 and int(port) <= 65535):
                    raise InvalidServiceError(
                        '\n\n*** Error: ' +
                        self._value +
                        ' is not a valid TCP/IP service! ***\n')

    @property
    def name(self):
        if self._name is not None:
            return self._name
        else:
            return self._prot + '-complex-' + self._beg + '.' + self._end + self._postfix

    @name.setter
    def name(self, n):
        # pylint: disable=no-member
        _ServiceBase.name.fset(self, n)

    def get_type(self):
        return 'service complex'


class ServiceObject:
    """
    Public class for dealing with TCP/IP services
    """

    def __init__(self, service_str, name=None):
        """
        Parameters
        ----------
        service_str: str
                In the format of tcp/443, tcp/443-445, tcp/1-65535/7005
        name: str
                Optional, name of the object that is different from standard name
        """
        """
        Make sure service_str is <type 'str'>, not <type 'unicode'>. Otherwise,
        <type 'unicode'> would cause exception in connectors.convert_dict_to_object()
        """
        self._parse(str(service_str), name)

    def _parse(self, service_str, name=None):
        """
        Perform the parsing of the service string and setup the private implementation.
        """
        logger.debug('ServiceObject - service_str: {0}'.format(service_str))
        if ',' in service_str.split('/')[-1]:
            self._instance = ServiceComplex(service_str, name)
        # service_str.split('/')[-1] is used to avoid '-' in
        # tcp/12345-12349/10038
        elif '-' in service_str.split('/')[-1]:
            self._instance = ServiceRange(service_str, name)
        else:
            self._instance = Service(service_str, name)

    @property
    def name(self):
        return self._instance.name

    @name.setter
    def name(self, n):
        self._instance.name = n

    @property
    def value(self):
        return self._instance.value

    @value.setter
    def value(self, v):
        self._instance.value = v

    @property
    def protocol(self):
        return self._instance._prot

    @property
    def source_port(self):
        return self._instance._sport

    @property
    def port(self):
        return self._instance._port

    def __str__(self):
        return self._instance._value

    def get_type(self):
        return self._instance.get_type()


class URLObject(_ObjectBase):
    """
    Public class for representing a URL that is a member of a PAN URL category
    """

    def __init__(self, value, wildcard='*'):
        """[summary]

        :param value: Value of URL or URL expression provided by caller.
        See https://docs.paloaltonetworks.com/pan-os/8-1/pan-os-admin/url-filtering/url-filtering-concepts/block-and-allow-lists
        :type value: String. E.g: tutorialspoint.com:port/html/index.htm or 1.1.1.1/

        :param wildcard: Either asterisk (*) or caret (^)
        :type wildcard: String
        """
        _ObjectBase.__init__(self, value)
        self._type = 'url'
        self._wildcard = wildcard
        self._hostname = None
        self._port = None
        self._path = None

        self._parse()
        self._check()

    def _parse(self):
        "Parse the value of URL/expression"
        if '/' in self._value:
            idx = self._value.find('/')
            websocket = self._value[:idx]
            self._path = self._value[idx+1:]
            if ':' in websocket:
                self._hostname = websocket.split(':')[0]
                self._port = websocket.split(':')[1]
            else:
                self._hostname = websocket
        else:
            if ':' in self._value:
                self._hostname = self._value.split(':')[0]
                self._port = self._value.split(':')[1]
            else:
                self._hostname = self._value

    def _check(self):
        """Validate the value of URL/expression. It has to be specific URL, IP address, or URL wildcard

        raise ValueError if the value is invalid
        """
        # '*' and '^' are mutually exclusive
        if '*' in self._value and '^' in self._value:
            raise ValueError('\n\n*** Error: ' +
                             self._value +
                             ' is not a unaccepted URL or URL expression! ***\n')
        if self._wildcard == '*' and '^' in self._value or self._wildcard == '^' and '*' in self._value:
            raise ValueError('\n\n*** Error: ' +
                             self._value +
                             ' is not a unaccepted URL or URL expression! ***\n')

        # Check hostname: If the hostname part of value is not IP and not valid hostname, raise ValueError
        is_ipv4 = True
        try:
            ipaddress.ip_address(self._hostname)
        except ValueError:
            is_ipv4 = False
        if is_ipv4 is False:
            if self._wildcard not in self._hostname or self._hostname.startswith(self._wildcard + '.'):
                hostname = self._hostname
                if hostname.startswith(self._wildcard + '.'):
                    hostname = hostname[2:]
                if not IPFQDN.is_hostname_valid(hostname):
                    raise ValueError('\n\n*** Error: ' +
                                     self._value +
                                     ' is not a valid URL! ***\n')

        # Check port
        if self._port is not None:
            if not self._port.isdigit():
                raise ValueError(
                    '\n\n*** Error: ' +
                    self._value +
                    ' is not a valid TCP/IP port! ***\n')
            if not (int(self._port) >= 1 and int(self._port) <= 65535):
                raise InvalidServiceError(
                    '\n\n*** Error: ' +
                    self._value +
                    ' is not a valid TCP/IP port! ***\n')

        # Check URL path

    def get_type(self):
        return self._type
