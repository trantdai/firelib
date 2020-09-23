"REPLACED BY addressess.py, services.py and urlcategory.py"

import ipaddress
import xml.etree.ElementTree as ET
from typing import List, Optional, Union

from ..common import constants as common_constants
from ..common import firelogging, util
from ..common.objects import URLObject
from . import constants
from .panfwapi import PanFWAPISession
from .panoapi import PanoramaAPISession

# START LOGGING TO FILE LIKE
logger = firelogging.FireLogger(name=__name__).firelogger
logger.debug('*** Start of palolib objects ***')


class BadActionError(RuntimeError):
    pass


class Address:
    def __init__(self, name, apisession, location='Shared'):
        """
        - Input:
          + name: string - name of address object
          + location: location of address group. If Panorama address group, location can be 'Shared'
          or '<device group name>'. If Firewall address group, location can be 'Panorama', 'Shared', or '<vsys name>'.
          The Firewall 'Shared' is for multi-vsys. The single vsys firewall, the location is 'vsys1'
        - Output:
          + self._xmlobject: Output of show/get request,
          i.e. type=config&action=get&xpath=/config/shared/address/entry[@name='H-1.1.1.1'].
          Example: <entry name="H-1.1.1.1"><ip-netmask>1.1.1.1</ip-netmask><description>...</description><tag>...<tag>
          </entry>
        """
        self._name = name
        self._session = apisession

        if apisession.get_session_host_role() == 'panorama':
            self._host_type = 'panorama'
        else:
            self._host_type = 'firewall'

        self._location = location
        self.xmlobject = None
        self._xmlobject = None

    def build_xml_object(self, ipobject, description='firewallauto'):
        """
        ipobject = common.IPObject
        """
        xmlobject = ET.Element(constants.TAG_ENTRY)
        # <entry name="H-1.1.1.1" />
        xmlobject.set(constants.TAG_ATTRIBUTE_NAME, ipobject.name)
        ipnode = ET.Element(ipobject.get_element_name())
        # <ip-netmask>1.1.1.1</ip-netmask>
        ipnode.text = str(ipobject)
        # <entry name="H-1.1.1.1"><ip-netmask>1.1.1.1</ip-netmask></entry>
        xmlobject.append(ipnode)
        # Add description node
        description_node = ET.SubElement(xmlobject, 'description')
        description_node.text = description
        # return xmlobject
        self._xmlobject = xmlobject

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, n):
        self._name = n

    @property
    def type(self):
        if constants.ADDRESS_TYPE_FQDN in ET.tostring(self.xmlobject, encoding='unicode'):
            self._type = constants.ADDRESS_TYPE_FQDN
        elif constants.ADDRESS_TYPE_IP_NETMASK in ET.tostring(self.xmlobject, encoding='unicode'):
            self._type = constants.ADDRESS_TYPE_IP_NETMASK
        else:
            self._type = constants.ADDRESS_TYPE_IP_RANGE
        return self._type

    @type.setter
    def type(self, t):
        self._type = t

    @property
    def value(self):
        self._value = self.xmlobject[0].text
        return self._value

    @value.setter
    def value(self, v):
        self._value = v
        self.xmlobject[0].text = v

    @property
    def host_type(self):
        return self._host_type

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, l):
        self._location = l

    @property
    def xmlobject(self):
        return self._xmlobject

    @xmlobject.setter
    def xmlobject(self, xml_object):
        self._xmlobject = xml_object

    @property
    def desc(self):
        # If description field is not empty/undefined
        if self.xmlobject.find(constants.TAG_DESCRIPTION) is not None:
            self._desc = self.xmlobject.find(constants.TAG_DESCRIPTION).text
        else:
            self._desc = ''
        return self._desc

    @desc.setter
    def desc(self, desc):
        self._desc = desc
        # If description field is defined
        if self.xmlobject.find(constants.TAG_DESCRIPTION) is not None:
            self.xmlobject.find(constants.TAG_DESCRIPTION).text = desc
        # If there is no node like <description>...</description>
        else:
            desc_node = ET.Element(constants.TAG_DESCRIPTION)
            desc_node.text = desc
            self.xmlobject.append(desc_node)

    @staticmethod
    def is_address_range_in_class_c_network(address_range):
        """
        Parameters
        ----------
        address_range: str
                Expected address in format of 10.10.10.10-10.10.10.20

        Return
        ---------
                True if so, else False
        """
        fhost = address_range.split('-')[0]
        lhost = address_range.split('-')[1]
        addrnet = fhost[:fhost.rfind('.')] + '.0/24'
        if ipaddress.ip_address(bytearray(fhost)) in \
                ipaddress.ip_network(bytearray(addrnet)) and \
                ipaddress.ip_address(bytearray(lhost)) in \
                ipaddress.ip_network(bytearray(addrnet)):
            return True
        else:
            return False

    @staticmethod
    def unpack_address_input_to_single_addresses(address):
        """
        Parameters
        ----------
        address: str
                Expected address in format of single IP, network/mask, or IP range

        Algorithm
        ---------
                If single IP, return list of that IP
                If class C network, return list of representative IP network.50
                If netmask < 22, return too big network and exit => checked by caller
                If 24 >= netmask <= 22, return list of rep IPs in class C networks
                If netmask > 25, return list of 2nd last IP in that network
                If IP range is not in class C, return too big range and exit =>
                checked by caller
                If IP range is in class C, return list of IPs in the range
        """
        if '-' in address:
            fhost = address.split('-')[0]
            lhost = address.split('-')[1]
            fhost_last_digit = int(fhost.split('.')[-1])
            lhost_last_digit = int(lhost.split('.')[-1])
            return list(range(fhost_last_digit, lhost_last_digit + 1))
        elif '/' in address:

            netmask = int(address.split('/')[1])
            two_first_octets = address.split(
                '.')[0] + '.' + address.split('.')[1]
            three_first_octets = address[:address.rfind('.')]
            third_octet = int(address.split('.')[2])

            if netmask == 32:
                return [address.split('/')[0]]
            elif netmask >= 22 and netmask <= 24:
                class_c_network_num = pow(24 - netmask, 2)
                # If class C network
                if class_c_network_num == 0:
                    return [three_first_octets + '.50']
                else:
                    all_third_octets = list(range(
                        third_octet, third_octet + class_c_network_num))
                    return [two_first_octets + '.' + str(x) + '.50' for x in
                            all_third_octets]
            # If netmask > 24 and < 32
            else:
                netobj = ipaddress.ip_network(bytearray(address))
                # return list of 2nd last IP in that network
                return [str(netobj[-2])]
        # elif FQDN
        # If single fixed IP without netmask
        else:
            return [address]

    def is_object_defined(self):
        """
        Parameters
        ----------
        objectname: str
                name of object to be checked for its existence in FW management sytem
        Return: True if defined, else False
        """
        # Retrieve xmlobject
        if self.xmlobject is None:
            self.get_address_object()

        # If object does not exist in FW system
        if self.xmlobject is None:
            return False
        return True

    def get_address_object(self):
        """
        When ipobject is not provided in __init__()
        The address is retrieved using the address group and apisession
        """
        if self.host_type == 'panorama':
            if self.location == 'Shared':
                self.xmlobject = self._session.get_shared_address_object(
                    self.name)
            else:  # self.location == '<device group name>'
                self.xmlobject = self._session.get_device_group_address_object(
                    self.name, self.location)
        else:  # self.host_type == 'firewall'
            if self.location == 'Panorama':
                self.xmlobject = self._session.get_panorama_address_object(
                    self.name)
            elif self.location == 'Shared':
                self.xmlobject = self._session.get_shared_address_object(
                    self.name)
            else:  # self.location = '<vsys no>'
                self.xmlobject = self._session.get_vsys_address_object(
                    self.name, self.location)

    def contain_value(self, input_value):
        """
        - Input:
          + input_value: Bare string value. It can be fqdn, single ip, ip-range
          or ip network
        - Output: True or False
        - Algorithm:
          - Check if input_value is a single IP and provided in format of 1.1.1.1/32. If so, remove /32. Do the same for self.value
          - Check for exact match
          - Check if input_value is fqdn using util.is_valid_hostname()
          - Check if input_value is 'ip-netmask'
          - Check if input_value is 'ip-range'
        """
        self_value = self.value
        # If input_value is a single IP that has /32 posfix, remove postfix
        if ('/' in input_value) and (input_value.split('/')[1] == '32'):
            input_value = input_value.split('/')[0]
        # If input_value is a single IP that has /32 posfix, remove postfix
        if ('/' in self.value) and self.value.split('/')[1] == '32':
            self_value = self.value.split('/')[0]

        # If input_value is a network
        if '/' in input_value:
            # If self_value is network
            if '/' in self_value:
                if ipaddress.ip_network(
                    bytearray(input_value)).subnet_of(
                    ipaddress.ip_network(
                        bytearray(self_value))):
                    return True

            # If self_value is range
            elif self.type == constants.ADDRESS_TYPE_IP_RANGE:
                ipaddr = ipaddress.ip_network(bytearray(input_value))
                # ipaddress.ip_address((u'1.2.3.0')
                fhost, lhost = ipaddr[0], ipaddr[-1]
                self_fhost = ipaddress.ip_address(
                    bytearray(self_value.split('-')[0]))
                self_lhost = ipaddress.ip_address(
                    bytearray(self_value.split('-')[1]))
                if self_fhost <= fhost and lhost <= self_lhost:
                    return True
            # else: #If self_value is single IP, return False at bottom
        elif '-' in input_value:  # If input_value is a range
            # If self_value is network
            if '/' in self_value:
                fhost = ipaddress.ip_address(
                    bytearray(input_value.split('-')[0]))
                lhost = ipaddress.ip_address(
                    bytearray(input_value.split('-')[1]))
                ipaddr = ipaddress.ip_network(bytearray(self_value))
                self_fhost, self_lhost = ipaddr[0], ipaddr[-1]
                if self_fhost <= fhost and lhost <= self_lhost:
                    return True
            elif self.type == constants.ADDRESS_TYPE_IP_RANGE:  # If self_value is range
                fhost = ipaddress.ip_address(
                    bytearray(input_value.split('-')[0]))
                lhost = ipaddress.ip_address(
                    bytearray(input_value.split('-')[1]))
                self_fhost = ipaddress.ip_address(
                    bytearray(self_value.split('-')[0]))
                self_lhost = ipaddress.ip_address(
                    bytearray(self_value.split('-')[1]))
                if self_fhost <= fhost and lhost <= self_lhost:
                    return True
            # else: #If self_value is single IP, return False at bottom
        # If input_value is a fqdn
        elif util.IP.is_valid_hostname(input_value):
            if (self.type == constants.ADDRESS_TYPE_FQDN) and (
                    input_value == self_value):
                return True
        else:  # If input_value is a single IP
            # If self_value is network
            if '/' in self_value:
                if ipaddress.ip_address(bytearray(input_value)) in \
                        ipaddress.ip_network(bytearray(self_value)):
                    return True
            elif self.type == constants.ADDRESS_TYPE_IP_RANGE:  # If self_value is range
                self_fhost = ipaddress.ip_address(
                    bytearray(self_value.split('-')[0]))
                self_lhost = ipaddress.ip_address(
                    bytearray(self_value.split('-')[1]))
                if self_fhost <= input_value and input_value <= self_lhost:
                    return True
            else:  # If self_value is a single IP
                if input_value == self_value:
                    return True
        return False

    def add_address_object(self):
        """
        Method called to add self.name to firewall system using
        self._xmlobject initiated via build_xml_object with ipobject
        """
        xpath_entry = constants.XPATH_ENTRY.format(
            self.xmlobject.attrib[constants.TAG_ATTRIBUTE_NAME])
        # <ip-netmask>1.1.1.1</ip-netmask>
        # element_node = self.xmlobject[0]
        # element_tail='<ip-netmask>1.1.1.1</ip-netmask><description>99999999</description>'
        element_tail = ''.join([ET.tostring(x, encoding='unicode') for x in self.xmlobject])
        # xpath_element: &element=<ip-netmask>1.1.1.1</ip-netmask><description>99999999</description>
        # xpath_element = '&' + constants.XPATH_ELEMENT + '=' + ET.tostring(element_node)
        xpath_element = '&' + constants.XPATH_ELEMENT + '=' + element_tail
        xpath_tail = xpath_entry + xpath_element

        logger.debug('add_address_object - xpath_tail: {0}'.format(xpath_tail))

        if self.host_type == 'panorama':
            if self.location == 'Shared':
                self._session.add_shared_address_object(xpath_tail)
            else:  # self.location == '<device group name>'
                self._session.add_device_group_address_object(
                    xpath_tail, self.location)
        else:  # self.host_type == 'firewall'
            if self.location == 'Panorama':
                raise BadActionError(
                    "Address {0} is read-only as it is managed by Panorama".format(self.name))
            elif self.location == 'Shared':
                self._session.add_shared_address_object(xpath_tail)
            else:  # self.location = '<vsys no>'
                self._session.add_vsys_address_object(
                    xpath_tail, self.location)

    def append_description(self, desc):
        """
        PAN only support max desc length of 1023
        If len of new description is greater than 1023,
        remove the first record number in current description,
        and then append new record number to it
        - Algorithm:
          + If self.desc is not set from xmlobject, set it
          + Check if len(self._desc) + len(' ') + len(desc) > 1023, remove first record number and space from self._desc
          + Append desc to self.desc
        """
        """
        if len(self.desc) == 0:
            self.desc = desc
        if len(self.desc) + len(' ') + len(desc) > 1023:
            # Find index of the first space character
            idx = self.desc.index(' ')
            # Slice current desc removing first record number and space
            self.desc = self.desc[idx + 1:]
        self.desc += ' ' + desc
        """
        new_description = ''
        if len(self.desc) == 0:
            new_description = desc
        # If new description is already in the description field, do nothing
        elif desc in self.desc:
            return
        elif len(self.desc) + len(' ') + len(desc) > 1023:
            # Find index of the first space character
            idx = self.desc.index(' ')
            # Slice current desc removing first record number and space
            # then append new desc
            new_description = self.desc[idx + 1:] + ' ' + desc
        else:
            new_description = self.desc + ' ' + desc
        self.desc = new_description

        member_node = ET.Element(constants.TAG_DESCRIPTION)
        member_node.text = self.desc
        # &element=<description>11224488</description>
        xpath_tail = '&' + constants.XPATH_ELEMENT + \
            '=' + ET.tostring(member_node, encoding='unicode')

        if self.host_type == 'panorama':
            if self.location == 'Shared':
                self._session.set_shared_address_object_description(
                    xpath_tail, self.name)
            else:  # self.location == '<device group name>'
                self._session.set_device_group_address_object_description(
                    xpath_tail, self.name, self.location)
        else:  # self.host_type == 'firewall'
            if self.location == 'Panorama':
                raise BadActionError(
                    "Address group {0} is read-only as it is managed by Panorama".format(self.name))
            elif self.location == 'Shared':
                self.xmlobject = self._session.set_shared_address_object_description(
                    xpath_tail, self.name)
            else:  # self.location = '<vsys no>'
                self._session.set_vsys_address_object_description(
                    xpath_tail, self.name, self.location)

    def print_address_object(self):
        print(('*** PAN Address: {0} ***\n'.format(self.name)))
        if self.xmlobject is None:
            print(('Address {0} is NEW and not defined yet!\n'.format(
                self.name)))
        else:
            print(('Value: {0}'.format(self.value)))
            print(('Type: {0}'.format(self.type)))
            print(('Location: {0}'.format(self.location)))
            print(('Description: {0}\n'.format(self.desc)))


class AddressGroup:
    """
    - Create class object for new address group
    - Set xmlobject via build_xml_object
    - Call add_address_group_object to add address group to FW system
    """

    def __init__(self, name, apisession, location='Shared'):
        """
        location: location of address group. If Panorama address group, location can be 'Shared' or '<device group name>'. If Firewall address group, location can be 'Panorama', 'Shared', or '<vsys name>'. The Firewall 'Shared' is for multi-vsys. The single vsys firewall, the location is 'vsys1'
        self._xmlobject: Output of show/get request, i.e. \        type=config&action=get&xpath=/config/shared/address-group/entry[@name='group_name']
        Example: <entry name="group_name"><static><member>...</member><description>...</description><tag>...<tag></entry>
        """
        self._name = name
        self._session = apisession

        if apisession.get_session_host_role() == 'panorama':
            self._host_type = 'panorama'
        else:
            self._host_type = 'firewall'

        self._location = location
        self._desc = None
        self._tags = None
        self._xmlobject = None

    def build_xml_object(self, **kwargs):
        """
        **kwargs:
        + name = self._name
        + type = static or dynamic
        + members = list of address/group names
        + ...
        + description: str
        + tags = list of tags
        Return something similar to: <entry name="firegroupobject"><static><member>...</member></static>
        <description>...</description><tag><member>...</member><tag></entry>
        """
        xmlobject = ET.Element(constants.TAG_ENTRY)
        # <entry name="firegroupobject" />
        xmlobject.set(constants.TAG_ATTRIBUTE_NAME, self._name)

        if kwargs['type'] == 'static':
            static_node = ET.Element(constants.TAG_STATIC)

            for member in kwargs['members']:
                member_node = ET.Element(constants.TAG_MEMBER)
                member_node.text = member
                static_node.append(member_node)
            xmlobject.append(static_node)

            if 'description' in kwargs:
                desc_node = ET.Element(constants.TAG_DESCRIPTION)
                desc_node.text = kwargs['description']
                xmlobject.append(desc_node)

            if 'tags' in kwargs:
                tag_node = ET.Element(constants.TAG_TAG)
                for tag in kwargs['tags']:
                    tag_member_node = ET.Element(constants.TAG_MEMBER)
                    tag_member_node.text = tag
                    tag_node.append(tag_member_node)
                xmlobject.append(tag_node)

            self._xmlobject = xmlobject
            logger.debug(
                'build_xml_object of {0}: {1}'.format(
                    self._name, ET.tostring(xmlobject, encoding='unicode')))
        # dynamic
        else:
            pass

    def extract_content_as_string_from_xmlobject(self):
        """
        Input: <entry name="firegroupobject">
        <static><member>...</member></static>    <description>...</description>
        <tag><member>...</member></tag></entry>
        Out: xml string: <static><member>...</member></static>    <description>...</description>
        <tag><member>...</member></tag>
        """
        return ''.join(ET.tostring(x, encoding='unicode') for x in self._xmlobject)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, n):
        self._name = n

    @property
    def host_type(self):
        return self._host_type

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, l):
        self._location = l

    @property
    def xmlobject(self):
        return self._xmlobject

    @xmlobject.setter
    def xmlobject(self, xml_object):
        self._xmlobject = xml_object

    @property
    def desc(self):
        # If description field is not empty/undefined
        if self.xmlobject.find(constants.TAG_DESCRIPTION) is not None:
            self._desc = self.xmlobject.find(constants.TAG_DESCRIPTION).text
        else:
            self._desc = ''
        return self._desc

    @desc.setter
    def desc(self, desc):
        self._desc = desc
        # If description field is defined
        if self.xmlobject.find(constants.TAG_DESCRIPTION) is not None:
            self.xmlobject.find(constants.TAG_DESCRIPTION).text = desc
        # If there is no node like <description>...</description>
        else:
            desc_node = ET.Element(constants.TAG_DESCRIPTION)
            desc_node.text = desc
            self.xmlobject.append(desc_node)

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, t):
        self._tags = t

    def is_object_defined(self):
        """
        Parameters
        ----------
        objectname: str
                name of object to be checked for its existence in FW management sytem
        Return: True if defined, else False
        """
        # Retrieve xmlobject
        if self.xmlobject is None:
            self.get_address_group_object()

        # If object does not exist in FW system
        if self.xmlobject is None:
            return False
        return True

    def get_address_group_object(self):
        """
        When kwargs is not provided in __init__(self, name, apisession, **kwargs)
        The address group is retrieved using the address group name and apisession
        """
        if self.host_type == 'panorama':
            if self.location == 'Shared':
                self.xmlobject = self._session.get_shared_address_group_object(
                    self.name)
            else:  # self.location == '<device group name>'
                self.xmlobject = self._session.get_device_group_address_group_object(
                    self.name, self.location)
        else:  # self.host_type == 'firewall'
            if self.location == 'Panorama':
                self.xmlobject = self._session.get_panorama_address_group_object(
                    self.name)
            elif self.location == 'Shared':
                self.xmlobject = self._session.get_shared_address_group_object(
                    self.name)
            else:  # self.location = '<vsys no>'
                self.xmlobject = self._session.get_vsys_address_group_object(
                    self.name, self.location)
        # print('xmlobject of {0}: {1}'.format(self.name, ET.tostring(self.xmlobjectt)))

    def add_address_group_object(self):
        """
        Method called to add self.name to firewall system using
        self._xmlobject initiated via build_xml_object
        """
        xpath_entry = constants.XPATH_ENTRY.format(
            self.xmlobject.attrib[constants.TAG_ATTRIBUTE_NAME])
        xpath_element = '&' + constants.XPATH_ELEMENT + '=' + \
                        self.extract_content_as_string_from_xmlobject()
        xpath_tail = xpath_entry + xpath_element

        if self.host_type == 'panorama':
            if self.location == 'Shared':
                self._session.add_shared_address_group_object(xpath_tail)
            else:  # self.location == '<device group name>'
                self.xmlobject = self._session.add_device_group_address_group_object(
                    xpath_tail, self.location)
        else:  # self.host_type == 'firewall'
            if self.location == 'Panorama':
                raise BadActionError(
                    "Address group {0} is read-only as it is managed by Panorama".format(self.name))
            elif self.location == 'Shared':
                self._session.add_shared_address_group_object(xpath_tail)
            else:  # self.location = '<vsys no>'
                self._session.add_vsys_address_group_object(
                    xpath_tail, self.location)

    def add_address_to_static_group(self, ipobject):
        """
        Obsolete replaced by add_member_from_static_group()
        - Input:
          + ipobject: util.IP object string formated by util.IP.get_name() like H-1.1.1.1, R-1.1.1.1-1.1.1.2, N-1.1.1.0/24
        - Algorithm:
          + Check if ipobject.get_name() exists on host. If not create it
          + Build address_element_xpath
          + Call panoapi.add_address_to_static_group(), if successful then
          + Add <member>H-1.1.1.1</member> to self._xmlobject to update self._xmlobject
        """
        member_node = ET.Element(constants.TAG_MEMBER)
        # ipobject.get_name() returns something formatted like H-1.1.1.1
        member_node.text = ipobject.get_name()
        new_static_node = ET.Element(constants.TAG_STATIC)
        new_static_node.append(member_node)
        # &element=<static><member>H-1.1.1.1</member></static>
        address_element_xpath = '&' + constants.XPATH_ELEMENT + \
            '=' + ET.tostring(new_static_node, encoding='unicode')

        # Create new address object
        addrobj = Address(ipobject.get_name(), self._session, self.location)
        # Retrieve xmlobject
        addrobj.get_address_object()
        # If address does not exist in FW system
        if addrobj.xmlobject is None:
            # Set xmlobject
            addrobj.build_xml_object(ipobject)
            # Create address in FW system
            addrobj.add_address_object()
        # If ipobject is a member of self, do nothing
        elif self.have_static_member(ipobject.get_name()):
            return
        if self.host_type == 'panorama':
            if self.location == 'Shared':
                self._session.add_address_to_shared_static_group(
                    address_element_xpath, self.name)
            else:  # self.location == '<device group name>'
                self._session.add_address_to_device_group_static_group(
                    address_element_xpath, self.name, self.location)
        else:  # self.host_type == 'firewall'
            if self.location == 'Panorama':
                raise BadActionError(
                    "Address group {0} is read-only as it is managed by Panorama".format(self.name))
            elif self.location == 'Shared':
                self.xmlobject = self._session.add_address_to_shared_static_group(
                    address_element_xpath, self.name)
            else:  # self.location = '<vsys no>'
                self._session.add_address_to_vsys_static_group(
                    address_element_xpath, self.name, self.location)

        static_node = self.xmlobject.find(constants.TAG_STATIC)
        static_node.append(member_node)

    def add_member_to_static_group(self, ipobject):
        """Add a common.objects.py to self group. The caller of this method will check:
+               - If ipobject is a FW object, is it defined?
+               - If ipobject is a new address, create it in FW system first
+               See fireobjectupdater.update_pan_address_group_object() for usage example

        Parameters
        ----------
        ipobject: firelib\common\objects.py FWObject
        - Algorithm:
          + Check if ipobject is object or group object via ipobject.get_type()
          + Check if ipobject.name exists on host. If not do nothing.
          + Build member_element_xpath
          + Call panoapi.add_address_to_static_group(), if successful then
          + Add <member>H-1.1.1.1</member> to self._xmlobject to update self._xmlobject
        """
        # If ipobject is already a member of self group, do nothing
        if self.have_static_member(ipobject.name):
            return

        member_node = ET.Element(constants.TAG_MEMBER)
        # ipobject.get_name() returns something formatted like H-1.1.1.1
        # member_node.text = ipobject.get_name()
        member_node.text = ipobject.name
        new_static_node = ET.Element(constants.TAG_STATIC)
        new_static_node.append(member_node)
        # &element=<static><member>H-1.1.1.1</member></static>
        member_element_xpath = '&' + constants.XPATH_ELEMENT + \
            '=' + ET.tostring(new_static_node, encoding='unicode')

        if self.host_type == 'panorama':
            if self.location == 'Shared':
                self._session.add_address_to_shared_static_group(
                    member_element_xpath, self.name)
            else:  # self.location == '<device group name>'
                self._session.add_address_to_device_group_static_group(
                    member_element_xpath, self.name, self.location)
        else:  # self.host_type == 'firewall'
            if self.location == 'Panorama':
                raise BadActionError(
                    "Address group {0} is read-only as it is managed by Panorama".format(self.name))
            elif self.location == 'Shared':
                self.xmlobject = self._session.add_address_to_shared_static_group(
                    member_element_xpath, self.name)
            else:  # self.location = '<vsys no>'
                self._session.add_address_to_vsys_static_group(
                    member_element_xpath, self.name, self.location)

        static_node = self.xmlobject.find(constants.TAG_STATIC)
        static_node.append(member_node)

    def remove_address_from_static_group(self, ipobject):
        """
        Obsolete replaced by remove_member_from_static_group()
        - Input:
          + ipobject: util.IP object => real/raw value is str(ipobject)
        - Algorithm:
          + Check if ipobject.name or str(ipobject) is in the xmlobject
          + Does not check in children, grandchildren of xmlobject. Only check at xmlobject level.
          + Build xpath_tail: /static/member[text()='{0}'.format(ipobject.name)] or /static/member[text()='{0}.format(str(ipobject))']
          + Call panoapi.remove_address_from_shared_static_group(), if successful then
          + Remove <member>1.1.1.1(or H-1.1.1.1)</member> from self._xmlobject to update self._xmlobject
        """
        member_text = ''
        if self.have_static_member(ipobject.get_name()):
            member_text = ipobject.get_name()
        elif self.have_static_member(str(ipobject)):
            member_text = str(ipobject)
        else:
            return
        xpath_tail = constants.XPATH_STATIC + constants.XPATH_MEMBER_TEXT.format(member_text)

        # Remove from firewall system
        if self.host_type == 'panorama':
            if self.location == 'Shared':
                self._session.remove_address_from_shared_static_group(
                    xpath_tail, self.name)
            else:  # self.location == '<device group name>'
                self._session.remove_address_from_device_group_static_group(
                    xpath_tail, self.name, self.location)
        else:  # self.host_type == 'firewall'
            if self.location == 'Panorama':
                raise BadActionError(
                    "Address group {0} is read-only as it is managed by Panorama".format(self.name))
            elif self.location == 'Shared':
                self._session.remove_address_from_shared_static_group(
                    xpath_tail, self.name)
            else:  # self.location = '<vsys no>'
                self._session.remove_address_from_vsys_static_group(
                    xpath_tail, self.name, self.location)

        # Remove from xmlobject
        xml_member_path = constants.TAG_STATIC + constants.FORWARD_SLASH + \
            constants.TAG_MEMBER
        for m in self.xmlobject.findall(xml_member_path):
            if m.text == member_text:
                static_node = self.xmlobject.find(constants.TAG_STATIC)
                static_node.remove(m)
                break

    def remove_member_from_static_group(self, ipobject):
        """
        - Input:
          + ipobject: firelib\common\objects.py FWObject
        - Algorithm:
          + Check if ipobject.name or str(ipobject) is in the xmlobject
          + Does not check in children, grandchildren of xmlobject. Only check at xmlobject level.
          + Build xpath_tail: /static/member[text()='{0}'.format(ipobject.name)] or /static/member[text()='{0}.format(str(ipobject))']
          + Call panoapi.remove_address_from_shared_static_group(), if successful then
          + Remove <member>1.1.1.1(or H-1.1.1.1)</member> from self._xmlobject to update self._xmlobject
        """
        member_text = ''
        if self.have_static_member(ipobject.name):
            member_text = ipobject.name
        elif self.have_static_member(str(ipobject)):
            member_text = str(ipobject)
        else:
            return
        xpath_tail = constants.XPATH_STATIC + constants.XPATH_MEMBER_TEXT.format(member_text)

        # Remove from firewall system
        if self.host_type == 'panorama':
            if self.location == 'Shared':
                self._session.remove_address_from_shared_static_group(
                    xpath_tail, self.name)
            else:  # self.location == '<device group name>'
                self._session.remove_address_from_device_group_static_group(
                    xpath_tail, self.name, self.location)
        else:  # self.host_type == 'firewall'
            if self.location == 'Panorama':
                raise BadActionError(
                    "Address group {0} is read-only as it is managed by Panorama".format(self.name))
            elif self.location == 'Shared':
                self._session.remove_address_from_shared_static_group(
                    xpath_tail, self.name)
            else:  # self.location = '<vsys no>'
                self._session.remove_address_from_vsys_static_group(
                    xpath_tail, self.name, self.location)

        # Remove from xmlobject
        xml_member_path = constants.TAG_STATIC + constants.FORWARD_SLASH + \
            constants.TAG_MEMBER
        for m in self.xmlobject.findall(xml_member_path):
            if m.text == member_text:
                static_node = self.xmlobject.find(constants.TAG_STATIC)
                static_node.remove(m)
                break

    def have_static_member(self, object_name):
        """
        - Input:
          + object_name: Name of the address/group object
        - Algorithm:
          + Check if object_name is in the xmlobject
          + Does not check in children, grandchildren of xmlobject. Only check at xmlobject level.
        """
        member_node = ET.Element(constants.TAG_MEMBER)
        member_node.text = object_name

        # If <member>H-1.1.1.1</member> in self.xmlobject
        # If the is uncommitted change - candidate config
        if 'dirtyId=' in ET.tostring(self.xmlobject, encoding='unicode'):
            if '>' + object_name + '<' in ET.tostring(self.xmlobject, encoding='unicode'):
                return True
        elif ET.tostring(member_node, encoding='unicode') in ET.tostring(self.xmlobject, encoding='unicode'):
            return True
        else:
            return False

    def contain_static_value(self, object_value):
        """
        - Input:
          + object_value: IP address, IP range, IP network or FQDN in string format
         - Output: True if the self.name or its member has object_value
         - Algorithm:
           + Retrieve values of direct children of self.name
           + Check exact match with above values
           + If no match, identify children that are address group objects
           + Repeat the algorithm for each of them
        """
        member_names = self.get_static_member_names()
        children_group_names = []
        for member_name in member_names:
            # Assume they are all addresses
            address_object = Address(
                member_name, self._session, self.location)
            address_object.get_address_object()
            if address_object.xmlobject is None:
                # address_object is child address group
                children_group_names.append(address_object.name)
            else:  # address_object is child address
                # if object_value == address_object.value:
                if address_object.contain_value(object_value):
                    return True
        # Recursive call to check child groups
        if len(children_group_names) > 0:
            for group_name in children_group_names:
                group_object = AddressGroup(
                    group_name, self._session, self.location)
                group_object.get_address_group_object()
                if group_object.contain_static_value(object_value):
                    return True
        return False

    def append_description(self, desc):
        """
        PAN only support max desc length of 1023
        If len of new description is greater than 1023,
        remove the first record number in current description,
        and then append new record number to it
        - Algorithm:
          + If self.desc is not set from xmlobject, set it
          + Check if len(self._desc) + len(' ') + len(desc) > 1023, remove first record number and space from self._desc
          + Append desc to self.desc
        """
        new_description = ''
        if len(self.desc) == 0:
            new_description = desc
        # If new description is already in the description field, do nothing
        elif desc in self.desc:
            return
        elif len(self.desc) + len(' ') + len(desc) > 1023:
            # Find index of the first space character
            idx = self.desc.index(' ')
            # Slice current desc removing first record number and space
            # then append new desc
            new_description = self.desc[idx + 1:] + ' ' + desc
        else:
            new_description = self.desc + ' ' + desc
        self.desc = new_description

        member_node = ET.Element(constants.TAG_DESCRIPTION)
        member_node.text = self.desc
        # &element=<description>11224488</description>
        xpath_tail = '&' + constants.XPATH_ELEMENT + \
            '=' + ET.tostring(member_node, encoding='unicode')

        if self.host_type == 'panorama':
            if self.location == 'Shared':
                self._session.set_shared_address_group_description(
                    xpath_tail, self.name)
            else:  # self.location == '<device group name>'
                self._session.set_device_group_address_group_description(
                    xpath_tail, self.name, self.location)
        else:  # self.host_type == 'firewall'
            if self.location == 'Panorama':
                raise BadActionError(
                    "Address group {0} is read-only as it is managed by Panorama".format(self.name))
            elif self.location == 'Shared':
                self.xmlobject = self._session.set_shared_address_group_description(
                    xpath_tail, self.name)
            else:  # self.location = '<vsys no>'
                self._session.set_vsys_address_group_description(
                    xpath_tail, self.name, self.location)

    def get_static_member_names(self):
        """
        Read xmlobject and return a list of member names of the static group
        """
        xml_member_path = constants.TAG_STATIC + constants.FORWARD_SLASH + \
            constants.TAG_MEMBER
        return [x.text for x in self.xmlobject.findall(xml_member_path)]

    def print_address_group(self):
        print(('*** PAN Address Group: {0} ***\n'.format(self.name)))
        # print('')
        if self.xmlobject is None:
            print(('Address group {0} is NEW and not defined yet!\n'.format(
                self.name)))
        else:
            members = self.get_static_member_names()
            print(('{0} members:'.format(len(members))))
            print((', '.join(members) + '\n'))
            # print('')
            print(('Description: {0}\n'.format(self.desc)))
        # print('')


class Service:
    def __init__(self, name, apisession, location='Shared'):
        """
        - Input:
          + name: string - name of service object
          + location: location of service object. If Panorama service object, location can be 'Shared'
          or '<device group name>'. If Firewall service object, location can be 'Panorama', 'Shared', or '<vsys name>'.
          The Firewall 'Shared' is for multi-vsys. The single vsys firewall, the location is 'vsys1'
        - Output:
          + self._xmlobject: Output of show/get request
        """
        self._name = name
        self._session = apisession

        if apisession.get_session_host_role() == 'panorama':
            self._host_type = 'panorama'
        else:
            self._host_type = 'firewall'

        self._location = location
        self._xmlobject = None

    def build_xml_object(self, serviceobject, description='firewallauto'):
        xmlobject = ET.Element(constants.TAG_ENTRY, {'name': self._name})
        protocol = ET.SubElement(xmlobject, 'protocol')
        prot_value = ET.SubElement(protocol, serviceobject.protocol)
        port = ET.SubElement(prot_value, 'port')
        port.text = serviceobject.port

        if serviceobject.source_port is not None:
            sport = ET.SubElement(prot_value, 'source-port')
            sport.text = serviceobject.source_port

        description_node = ET.SubElement(xmlobject, 'description')
        description_node.text = description
        self._xmlobject = xmlobject

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, n):
        self._name = n

    @property
    def protocol(self):
        if constants.SERVICE_PROTOCOL_TCP in ET.tostring(self.xmlobject, encoding='unicode'):
            self._protocol = constants.SERVICE_PROTOCOL_TCP
        elif constants.SERVICE_PROTOCOL_UDP in ET.tostring(self.xmlobject, encoding='unicode'):
            self._protocol = constants.SERVICE_PROTOCOL_UDP
        else:  # SCTP
            self._protocol = constants.SERVICE_PROTOCOL_SCTP
        return self._protocol

    @protocol.setter
    def protocol(self, p):
        self._protocol = p

    @property
    def port(self):
        self._port = self.xmlobject[0][0][0].text
        return self._port

    @port.setter
    def port(self, p):
        self._port = p
        self.xmlobject[0][0][0].text = p

    # source-port
    @property
    def sport(self):
        if len(self.xmlobject[0][0]) == 2:
            self._sport = self.xmlobject[0][0][1].text
        else:
            self._sport = None
        return self._sport

    @sport.setter
    def sport(self, sp):
        self._sport = sp
        self.xmlobject[0][0][1].text = sp

    @property
    def host_type(self):
        return self._host_type

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, l):
        self._location = l

    @property
    def xmlobject(self):
        return self._xmlobject

    @xmlobject.setter
    def xmlobject(self, xml_object):
        self._xmlobject = xml_object

    @property
    def desc(self):
        # If description field is not empty/undefined
        if self.xmlobject.find(constants.TAG_DESCRIPTION) is not None:
            self._desc = self.xmlobject.find(constants.TAG_DESCRIPTION).text
        else:
            self._desc = ''
        return self._desc

    @desc.setter
    def desc(self, desc):
        self._desc = desc
        # If description field is defined
        if self.xmlobject.find(constants.TAG_DESCRIPTION) is not None:
            self.xmlobject.find(constants.TAG_DESCRIPTION).text = desc
        # If there is no node like <description>...</description>
        else:
            desc_node = ET.Element(constants.TAG_DESCRIPTION)
            desc_node.text = desc
            self.xmlobject.append(desc_node)

    @property
    def value(self):
        v = self.protocol + '/'
        if self.sport is not None:
            v += self.sport + '/'
        v += self.port
        return v

    def is_object_defined(self):
        """Check if self exists in FW system

        Return: True if defined, else False
        """
        # Retrieve xmlobject
        self.get_service_object()

        # If object does not exist in FW system
        if self.xmlobject is None:
            return False
        return True

    def get_service_object(self):
        """
        - Read service object config from the host (Panorama or Firewall)
        - Extract the content at the entry level and assign it to xmlobject
        """
        if self.host_type == 'panorama':
            if self.location == 'Shared':
                self.xmlobject = self._session.get_shared_service_object(
                    self.name)
            else:  # self.location == '<device group name>'
                self.xmlobject = self._session.get_device_group_service_object(
                    self.name, self.location)
        else:  # self.host_type == 'firewall'
            if self.location == 'Panorama':
                self.xmlobject = self._session.get_panorama_service_object(
                    self.name)
            elif self.location == 'Shared':
                self.xmlobject = self._session.get_shared_service_object(
                    self.name)
            else:  # self.location = '<vsys no>'
                self.xmlobject = self._session.get_vsys_service_object(
                    self.name, self.location)

    def contain_value(self, input_value):
        """
        - Input:
          + input_value: Bare string value. It can be fqdn, single ip, ip-range
          or ip network
        - Output: True or False
        - Algorithm:
          - Check if input_value is a single IP and provided in format of 1.1.1.1/32. If so, remove /32. Do the same for self.value
          - Check for exact match
          - Check if input_value is fqdn using util.is_valid_hostname()
          - Check if input_value is 'ip-netmask'
          - Check if input_value is 'ip-range'
        """
        pass

    def extract_object_content_as_xml_string(self):
        """
        Input: self._xmlobject = <entry name="rule1" loc="device_group_name"><protocol>...</protocol>
        <description>...</description><tag>...</tag></entry>
        Output: xml string <protocol>...</protocol><description>...</description><tag>...</tag>
        """
        return ''.join(ET.tostring(x, encoding='unicode') for x in self._xmlobject)

    def add_service_object(self):
        """
        Method called to add self.name to firewall system using
        self._xmlobject initiated via build_xml_object
        """
        xpath_entry = constants.XPATH_ENTRY.format(
            self.xmlobject.attrib[constants.TAG_ATTRIBUTE_NAME])
        # element_node = self.xmlobject[0]
        # xpath_element = '&' + constants.XPATH_ELEMENT + '=' + ET.tostring(element_node)
        # &element=<protocol><tcp><port>443</port></tcp></protocol>
        element_string = self.extract_object_content_as_xml_string()
        xpath_element = '&' + constants.XPATH_ELEMENT + '=' + element_string
        xpath_tail = xpath_entry + xpath_element

        if self.host_type == 'panorama':
            if self.location == 'Shared':
                self._session.add_shared_service_object(xpath_tail)
            else:  # self.location == '<device group name>'
                self._session.add_device_group_address_object(
                    xpath_tail, self.location)
        else:  # self.host_type == 'firewall'
            if self.location == 'Panorama':
                raise BadActionError(
                    "Service {0} is read-only as it is managed by Panorama".format(self.name))
            elif self.location == 'Shared':
                self._session.add_shared_address_object(xpath_tail)
            else:  # self.location = '<vsys no>'
                self._session.add_vsys_address_object(
                    xpath_tail, self.location)

    @staticmethod
    def is_service_forbidden(fullservice):
        """
        fullservice: string i.e. tcp/443, tcp/20-22
        Check if fullservice has any service forbidden by SO
        If yes return tuple of <True, reason>
        """
        prot = fullservice.split('/')[0]
        port = fullservice.split('/')[1]

        if '-' in port:
            start = int(port.split('-')[0])
            end = int(port.split('-')[1]) + 1
        else:
            start = int(port)
            end = start + 1
        for p in range(start, end):
            service = prot + '/' + str(p)
            if service in common_constants.FORBIDDEN_SERVICES_VULNERABLE:
                return True, 'vulnerable'
            if service in common_constants.FORBIDDEN_SERVICES_CLEAR_TEXT:
                return True, 'cleartext'
        return False, ''

    @staticmethod
    def is_port_range_valid(port):
        """
        port: string expected to be any or from 0-65535 can be single or range
        Check if port is any or in 0-65535
        If yes, return True
        """
        if port == 'any':
            return True
        if '-' in port:
            start = int(port.split('-')[0])
            end = int(port.split('-')[1])
        else:
            start = int(port)
            end = start
        if start < 0 or end > 65535:
            return False
        return True

    @staticmethod
    def is_service_range_valid(service):
        """
        Parameters
        ----------
        service: str
                Expected service in format of protocol/port-(range) or any
        like tcp/80, tcp/443-444, and udp/53

        Returns
        -------
        bool
                Return True if format and value are expected/valid.
                Else return False.
        """
        if '/' not in service:
            return False
        if service.split(
                '/')[0].lower() not in constants.PAN_SERVICE_PROTOCOLS:
            return False
        if Service.is_port_range_valid(service.split('/')[1]) is False:
            return False
        return True

    @staticmethod
    def unpack_service_to_protocol_ports(service):
        """
        Parameters
        ----------
        service: str
                Expected service in format of protocol/port-(range) or any
        like tcp/80, tcp/443-444, and udp/53

        Returns
        -------
                tuple of protocol number as string and list of string ports
        """
        service = service.lower()
        prot = service.split('/')[0]
        prot_num = None
        if prot == 'tcp':
            prot_num = '6'
        elif prot == 'udp':
            prot_num = '17'

        port = service.split('/')[1]
        ports = None
        if '-' in port:
            ports = list(range(int(port.split('-')[0]), int(port.split('-')[1]) + 1))
        else:
            ports = [port]

        return prot_num, ports

    def print_service_object(self):
        print(('*** PAN Service: {0} ***\n'.format(self.name)))
        if self.xmlobject is None:
            print(('Service {0} is NEW and not defined yet!\n'.format(
                self.name)))
        else:
            print(('Value: {0}'.format(self.value)))
            print(('Location: {0}'.format(self.location)))
            print(('Description: {0}\n'.format(self.desc)))


class ServiceGroup:
    def __init__(self, name, apisession, location='Shared'):
        """
        - Input:
          + name: string - name of service group object
          + location: location of service object. If Panorama service object, location can be 'Shared' or
          '<device group name>'. If Firewall service object, location can be 'Panorama', 'Shared', or '<vsys name>'.
          The Firewall 'Shared' is for multi-vsys. The single vsys firewall, the location is 'vsys1'
        - Output:
          + self._xmlobject: Output of show/get request,
          i.e. type=config&action=get&xpath=/config/shared/service-group/entry[@name='http-https']. Example:
                                   <entry name="http-https">
                                   <members>
                                   <member>tcp-80</member>
                                   <member>tcp-443</member>
                                   </members>
                                   <tag>
                                       <member>...</member>
                                   </tag>
                                   </entry>
        """
        self._name = name
        self._session = apisession

        if apisession.get_session_host_role() == 'panorama':
            self._host_type = 'panorama'
        else:
            self._host_type = 'firewall'

        self._location = location
        self._tags = None
        self._xmlobject = None

    def build_xml_object(self, **kwargs):
        """
        **kwargs:
        + name = self._name - not needed
        + members = list of service/group names
        + tags = list of tags
        Return something similar to: <entry name="http-https">
        <members><member>tcp-80</member><member>tcp-443</member></members>
        <tag><member>fireauto</member></tag>
        </entry>
        """
        # Create entry node <entry name="gs-web" />
        xmlobject = ET.Element(constants.TAG_ENTRY, {'name': self._name})
        members = ET.SubElement(xmlobject, 'members')

        for member in kwargs['members']:
            member_node = ET.SubElement(members, 'member')
            member_node.text = member

        if 'tags' in kwargs:
            tag_node = ET.SubElement(xmlobject, "tag")
            for tag in kwargs['tags']:
                member = ET.SubElement(tag_node, "member")
                member.text = tag

        self._xmlobject = xmlobject
        # print('Service group xmlobject: {0}'.format(ET.tostring(xmlobject)))

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, n):
        self._name = n

    @property
    def host_type(self):
        return self._host_type

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, l):
        self._location = l

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, t):
        self._tags = t

    @property
    def xmlobject(self):
        return self._xmlobject

    @xmlobject.setter
    def xmlobject(self, xml_object):
        self._xmlobject = xml_object

    def extract_content_as_string_from_xmlobject(self):
        """
        Input: <entry name="http-https">
        <members><member>tcp-80</member><member>tcp-443</member></members>
        <tag><member>fireauto</member></tag>
        </entry>

        Output: xml string - <members><member>tcp-80</member><member>tcp-443</member></members>
        <tag><member>fireauto</member></tag>
        """
        return ''.join(ET.tostring(x, encoding='unicode') for x in self._xmlobject)

    def is_object_defined(self):
        """Check if self exists in FW system

        Return: True if defined, else False
        """
        # Retrieve xmlobject
        self.get_service_group_object()

        # If object does not exist in FW system
        if self.xmlobject is None:
            return False
        return True

    def get_service_group_object(self):
        """
        - Read service group object config from the host (Panorama or Firewall)
        - Extract the content at the entry level and assign it to xmlobject
        """
        if self.host_type == 'panorama':
            if self.location == 'Shared':
                self.xmlobject = self._session.get_shared_service_group_object(
                    self.name)
            else:  # self.location == '<device group name>'
                self.xmlobject = self._session.get_device_group_service_group_object(
                    self.name, self.location)
        else:  # self.host_type == 'firewall'
            if self.location == 'Panorama':
                self.xmlobject = self._session.get_panorama_service_group_object(
                    self.name)
            elif self.location == 'Shared':
                self.xmlobject = self._session.get_shared_service_group_object(
                    self.name)
            else:  # self.location = '<vsys no>'
                self.xmlobject = self._session.get_vsys_service_group_object(
                    self.name, self.location)

    def add_service_group_object(self):
        """
        Method called to add self.name to firewall system using
        self._xmlobject initiated via build_xml_object
        """
        xpath_entry = constants.XPATH_ENTRY.format(
            self.xmlobject.attrib[constants.TAG_ATTRIBUTE_NAME])
        xpath_element = '&' + constants.XPATH_ELEMENT + '=' + \
                        self.extract_content_as_string_from_xmlobject()
        xpath_tail = xpath_entry + xpath_element

        if self.host_type == 'panorama':
            if self.location == 'Shared':
                self._session.add_shared_service_group_object(xpath_tail)
            else:  # self.location == '<device group name>'
                self.xmlobject = self._session.add_device_group_service_group_object(
                    xpath_tail, self.location)
        else:  # self.host_type == 'firewall'
            if self.location == 'Panorama':
                raise BadActionError(
                    "Service group {0} is read-only as it is managed by Panorama".format(self.name))
            elif self.location == 'Shared':
                self._session.add_shared_service_group_object(xpath_tail)
            else:  # self.location = '<vsys no>'
                self._session.add_vsys_service_group_object(
                    xpath_tail, self.location)

    def add_member_to_service_group(self, serviceobject):
        """The caller needs to do:
        - If serviceobject is name of FW object, check if it is defined
        - If serviceobject is a new service, create it in FW system first
        See fireobjectupdater.update_pan_service_group_object() for usage example

        Parameters
        ----------
        serviceobject: custom object
                firelib\common\objects.py FWObject or ServiceObject
        - Algorithm:
          + Check if serviceobject is object or group object via serviceobject.get_type()
          # + Check if serviceobject.name is defined in FW systems. If not, raise ValueError.
          + Check if serviceobject.name is a member self of group. If not do nothing.
          + Build member_element_xpath
          + Call panoapi.add_member_to_service_group(), if successful then
          + Add <member>tcp-443</member> to self._xmlobject to update self._xmlobject
        """
        # If serviceobject is already a member of self group, do nothing
        if self.have_member(serviceobject.name):
            return
        # member_node = ET.Element(constants.TAG_MEMBER)
        # member_node.text = serviceobject.name

        members = ET.Element('members')
        member = ET.SubElement(members, 'member')
        member.text = serviceobject.name
        # &element=<members><member>tcp-80</member></members>
        member_element_xpath = '&' + \
                               constants.XPATH_ELEMENT + '=' + ET.tostring(members, encoding='unicode')

        if self.host_type == 'panorama':
            if self.location == 'Shared':
                self._session.add_member_to_shared_service_group(
                    member_element_xpath, self.name)
            else:  # self.location == '<device group name>'
                self._session.add_member_to_device_group_service_group(
                    member_element_xpath, self.name, self.location)
        else:  # self.host_type == 'firewall'
            if self.location == 'Panorama':
                raise BadActionError(
                    "Service group {0} is read-only as it is managed by Panorama".format(self.name))
            elif self.location == 'Shared':
                self.xmlobject = self._session.add_member_to_shared_service_group(
                    member_element_xpath, self.name)
            else:  # self.location = '<vsys no>'
                self._session.add_member_to_vsys_service_group(
                    member_element_xpath, self.name, self.location)

        members = self.xmlobject.find('members')
        members.append(member)

    def remove_member_from_service_group(self, serviceobject):
        """The caller needs to check if serviceobject is a member
        See fireobjectupdater.update_pan_service_group_object for usage example
        - Input:
          + serviceobject: firelib\common\objects.py FWObject
        - Algorithm:
          + Check if serviceobject.name or str(serviceobject) is in the xmlobject
          + Does not check in children, grandchildren of xmlobject. Only check at xmlobject level.
          + Build xpath_tail: /members/member[text()='{0}'.format(serviceobject.name)] or /members/member[text()='{0}.format(str(serviceobject))']
          + Call panoapi.remove_member_from_shared_service_group(), if successful then
          + Remove <member>tcp-80</member> from self._xmlobject to update self._xmlobject
        """
        member_text = serviceobject.name
        # xpath_tail = "/members/member[text()='tcp-443']"
        xpath_tail = '/members' + \
                     constants.XPATH_MEMBER_TEXT.format(member_text)

        # Remove from firewall system
        if self.host_type == 'panorama':
            if self.location == 'Shared':
                self._session.remove_member_from_shared_service_group(
                    xpath_tail, self.name)
            else:  # self.location == '<device group name>'
                self._session.remove_member_from_device_group_service_group(
                    xpath_tail, self.name, self.location)
        else:  # self.host_type == 'firewall'
            if self.location == 'Panorama':
                raise BadActionError(
                    "Service group {0} is read-only as it is managed by Panorama".format(self.name))
            elif self.location == 'Shared':
                self._session.remove_service_from_shared_service_group(
                    xpath_tail, self.name)
            else:  # self.location = '<vsys no>'
                self._session.remove_service_from_vsys_service_group(
                    xpath_tail, self.name, self.location)

        # Remove from xmlobject
        xml_member_path = 'members/member'
        for m in self.xmlobject.findall(xml_member_path):
            if m.text == member_text:
                members = self.xmlobject.find('members')
                members.remove(m)
                break

    def have_member(self, object_name):
        """
        - Input:
          + object_name: Name of the object to be checked against membership
        - Algorithm:
          + Check if object_name is in the xmlobject
          + Does not check in children, grandchildren of xmlobject. Only check at xmlobject level.
        """
        member_node = ET.Element(constants.TAG_MEMBER)
        member_node.text = object_name
        # If <member>tcp-80</member> in self.xmlobject
        # If the is uncommitted change - candidate config
        if 'dirtyId=' in ET.tostring(self.xmlobject, encoding='unicode'):
            if '>' + object_name + '<' in ET.tostring(self.xmlobject, encoding='unicode'):
                return True
        elif ET.tostring(member_node, encoding='unicode') in ET.tostring(self.xmlobject, encoding='unicode'):
            return True
        else:
            return False

    def contain_static_value(self, object_value):
        """
        - Input:
          + object_value: service, service range, service complex in string format
         - Output: True if the self.name or its member has object_value
         - Algorithm:
           + Retrieve values of direct children of self.name
           + Check exact match with above values
           + If no match, identify children that are service group objects
           + Repeat the algorithm for each of them
        """
        pass

    def get_member_names(self):
        """
        Read xmlobject and return a list of member names of the service group
        """
        xml_member_path = 'members/member'
        return [x.text for x in self.xmlobject.findall(xml_member_path)]

    def print_service_group(self):
        print(('*** PAN Service Group: {0} ***\n'.format(self.name)))
        if self.xmlobject is None:
            print(('Service group {0} is NEW and not defined yet!\n'.format(
                self.name)))
        else:
            members = self.get_member_names()
            print(('{0} members:'.format(len(members))))
            print((', '.join(members) + '\n'))


class _BaseObject:
    """
    Private class as base class for all other object class
    Going to be REMOVED
    """

    def __init__(self, name: str, apisession: Union[PanoramaAPISession, PanFWAPISession], location: str = 'Shared') -> None:
        """Initialize _BaseObject object

        :param name: Name of custom URL category object
        :type name: str
        :param apisession: Either firewall or Panorama API session
        :type apisession: Union[PanoramaAPISession, PanFWAPISession]
        :param location: Location of URL category object, defaults to 'Shared'. If Panorama service object, location can be 'Shared' or '<device group name>'. If Firewall service object, location can be 'Panorama', 'Shared', or '<vsys name>'. The Firewall 'Shared' is for multi-vsys. The single vsys firewall, the location is 'vsys1'
        :type location: str, optional
        """
        self._name = name
        self._session = apisession

        if apisession.get_session_host_role() == 'panorama':
            self._host_type = 'panorama'
        else:
            self._host_type = 'firewall'

        self._location = location
        self._tags = None
        self._xmlobject = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, n):
        self._name = n

    @property
    def host_type(self):
        return self._host_type

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, l):
        self._location = l

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, t):
        self._tags = t

    @property
    def desc(self):
        return None

    @desc.setter
    def desc(self, desc):
        pass

    @property
    def xmlobject(self):
        return self._xmlobject

    @xmlobject.setter
    def xmlobject(self, xml_object):
        self._xmlobject = xml_object

    def extract_string_content_from_xmlobject(self) -> Optional[str]:
        """
        Example input: <entry name="http-https">
        <members><member>tcp-80</member><member>tcp-443</member></members>
        <tag><member>auto</member></tag>
        </entry>

        Example output: xml string - <members><member>tcp-80</member><member>tcp-443</member></members>
        <tag><member>auto</member></tag>
        """
        if self._xmlobject is not None:
            return ''.join(ET.tostring(x, encoding='unicode') for x in self._xmlobject)
        else:
            return None

    def is_object_defined(self) -> bool:
        """
        Check if self exists in FW system. Return: True if defined, else False
        """
        pass

    def get_objet(self) -> None:
        """
        - Read service group object config from the host (Panorama or Firewall)
        - Extract the content at the entry level and assign it to xmlobject
        """
        pass

    def create_object(self) -> None:
        """
        Create new object in FW system using self._xmlobject
        """
        pass

    def append_description(self, desc) -> None:  # pylint: disable=unused-argument
        """
        PAN only support max desc length of 1023. If len of new description is greater than 1023, remove the first record number in current description, and then append new record number to it.
        - Algorithm:
        + If self.desc is not set from xmlobject, set it
        + Check if len(self._desc) + len(' ') + len(desc) > 1023, remove first record number and space from self._desc
        + Append desc to self.desc
        """
        """
        if len(self.desc) == 0:
			self.desc = desc
		if len(self.desc) + len(' ') + len(desc) > 1023:
			# Find index of the first space character
			idx = self.desc.index(' ')
			# Slice current desc removing first record number and space
			self.desc = self.desc[idx + 1:]
		self.desc += ' ' + desc
		"""
        """
		if self.desc is None:
			return

		new_description = ''
		if len(self.desc) == 0:
			new_description = desc
		# If new description is already in the description field, do nothing
		elif desc in self.desc:
			return
		elif len(self.desc) + len(' ') + len(desc) > 1023:
			# Find index of the first space character
			idx = self.desc.index(' ')
			# Slice current desc removing first record number and space
			# then append new desc
			new_description = self.desc[idx + 1:] + ' ' + desc
		else:
			new_description = self.desc + ' ' + desc
		self.desc = new_description

		member_node = ET.Element(constants.TAG_DESCRIPTION)
		member_node.text = self.desc
		# &element=<description>11224488</description>
		xpath_tail = '&' + constants.XPATH_ELEMENT + \
			'=' + ET.tostring(member_node, encoding='unicode')

		if self.host_type == 'panorama':
			if self.location == 'Shared':
				self._session.set_shared_address_object_description(
					xpath_tail, self.name)
			else:  # self.location == '<device group name>'
				self._session.set_device_group_address_object_description(
					xpath_tail, self.name, self.location)
		else:  # self.host_type == 'firewall'
			if self.location == 'Panorama':
				raise BadActionError(
					"Address group {0} is read-only as it is managed by
					Panorama".format(self.name))
			elif self.location == 'Shared':
				self.xmlobject = self._session.set_shared_address_object_description(
					xpath_tail, self.name)
			else:  # self.location = '<vsys no>'
				self._session.set_vsys_address_object_description(
					xpath_tail, self.name, self.location)
		"""


class _BaseDeviceGroupObject(_BaseObject):
    """
    Private class as base class for all other device group object class. Ideally the Address, AddressGroup, Service, and Service Group should inherit from this class.
    """

    def __init__(self, name: str, apisession: Union[PanoramaAPISession, PanFWAPISession], location: str = 'Shared') -> None:
        """Initialize _BaseObject object

        :param name: Name of custom URL category object
        :type name: str
        :param apisession: Either firewall or Panorama API session
        :type apisession: Union[PanoramaAPISession, PanFWAPISession]
        :param location: Location of URL category object, defaults to 'Shared'. If Panorama service object, location can be 'Shared' or '<device group name>'. If Firewall service object, location can be 'Panorama', 'Shared', or '<vsys name>'. The Firewall 'Shared' is for multi-vsys. The single vsys firewall, the location is 'vsys1'
        :type location: str, optional
        """
        _BaseObject.__init__(self, name, apisession, location)


class URLCategory(_BaseDeviceGroupObject):
    """
    Public class for representing a PAN custom URL category object
    """

    def __init__(self, name: str, apisession: Union[PanoramaAPISession, PanFWAPISession], location: str = 'Shared') -> None:
        """Initialize URLCategory object

        :param name: Name of custom URL category object
        :type name: str
        :param apisession: Either firewall or Panorama API session
        :type apisession: Union[PanoramaAPISession, PanFWAPISession]
        :param location: Location of URL category object, defaults to 'Shared'. If Panorama service object, location can be 'Shared' or '<device group name>'. If Firewall service object, location can be 'Panorama', 'Shared', or '<vsys name>'. The Firewall 'Shared' is for multi-vsys. The single vsys firewall, the location is 'vsys1'
        :type location: str, optional
        """
        _BaseDeviceGroupObject.__init__(self, name, apisession, location)

    @property
    def desc(self):
        # If description field is not empty/undefined
        if self.xmlobject.find(constants.TAG_DESCRIPTION) is not None:
            self._desc = self.xmlobject.find(constants.TAG_DESCRIPTION).text
        else:
            self._desc = ''
        return self._desc

    @desc.setter
    def desc(self, desc):
        self._desc = desc
        # If description field is defined
        if self.xmlobject.find(constants.TAG_DESCRIPTION) is not None:
            self.xmlobject.find(constants.TAG_DESCRIPTION).text = desc
        # If there is no node like <description>...</description>
        else:
            desc_node = ET.Element(constants.TAG_DESCRIPTION)
            desc_node.text = desc
            self.xmlobject.append(desc_node)

    def build_xml_object(self, **kwargs):
        """Build xml object of the custom URL category object
        **kwargs:
        + name = self._name - not needed
        + loc: Only required by non-shared object
        + members: List of service/group names
        Return something similar to:
            <entry name="url_name" loc="internet">
                <list>
                <member>*.goole.com</member>
                </list>
                <description>99999999</description>
            </entry>
        or for shared object
            <entry name="url-test">
                <list>
                <member>*.google.com</member>
                </list>
                <description>99999999</description>
            </entry>
        """
        if 'loc' in kwargs:
            xmlobject = ET.Element(constants.TAG_ENTRY, {'name': self._name, 'loc': kwargs['loc']})
        else:
            xmlobject = ET.Element(constants.TAG_ENTRY, {'name': self._name})

        memlist = ET.SubElement(xmlobject, 'list')
        for member in kwargs['list']:
            member_node = ET.SubElement(memlist, 'member')
            member_node.text = member

        desc = 'firewallauto'
        if 'description' in kwargs:
            desc += ' ' + kwargs['description']
        desc_node = ET.SubElement(xmlobject, 'description')
        desc_node.text = desc

        self._xmlobject = xmlobject

    def get_object(self) -> None:
        """
        - Read service group object config from the host (Panorama or Firewall)
        - Extract the content at the entry level and assign it to xmlobject
        """
        if self.host_type == 'panorama':
            if self.location == 'Shared':
                self.xmlobject = self._session.get_shared_custom_url_category_object(
                    self.name)
            else:  # self.location == '<device group name>'
                self.xmlobject = self._session.get_device_group_custom_url_category_object(
                    self.name, self.location)
        """ Implement below in panfwapi.py
        else:  # self.host_type == 'firewall'
            if self.location == 'Panorama':
                self.xmlobject = self._session.get_panorama_custom_url_category_object(
                    self.name)
            elif self.location == 'Shared':
                self.xmlobject = self._session.get_shared_custom_url_category_object(
                    self.name)
            else:  # self.location = '<vsys no>'
                self.xmlobject = self._session.get_vsys_custom_url_category_object(
                    self.name, self.location)
        """

    def is_object_defined(self) -> bool:
        """Check if self exists in FW system. Return: True if defined, else False
        """
        # Retrieve xmlobject
        self.get_object()

        # If object does not exist in FW system
        if self.xmlobject is None:
            return False
        return True

    def create_object(self) -> bool:
        """
        Create new object in FW system using self._xmlobject
        """
        xpath_entry = constants.XPATH_ENTRY.format(
            self.xmlobject.attrib[constants.TAG_ATTRIBUTE_NAME])
        xpath_element = '&' + constants.XPATH_ELEMENT + '=' + \
                        self.extract_string_content_from_xmlobject()
        xpath_tail = xpath_entry + xpath_element

        if self.host_type == 'panorama':
            if self.location == 'Shared':
                self._session.add_shared_custom_url_category_object(xpath_tail)
            else:  # self.location == '<device group name>'
                self.xmlobject = self._session.add_device_group_custom_url_category_object(
                    xpath_tail, self.location)
        """Implement below in panfwapi.py
        else:  # self.host_type == 'firewall'
            if self.location == 'Panorama':
                raise BadActionError(
                    "Custom URL object {0} is read-only as it is managed by Panorama".format(self.name))
            elif self.location == 'Shared':
                self._session.add_shared_custom_url_category_object(xpath_tail)
            else:  # self.location = '<vsys no>'
                self._session.add_vsys_custom_url_category_object(
                    xpath_tail, self.location)
        """

    def have_member(self, url: str) -> bool:
        """Check if url is existent in the URL category object

        :param url: URL or URL expression
        :type url: str
        """
        member_node = ET.Element(constants.TAG_MEMBER)
        member_node.text = url
        # If <member>tcp-80</member> in self.xmlobject
        # If the is uncommitted change - candidate config
        if 'dirtyId=' in ET.tostring(self.xmlobject, encoding='unicode'):
            if '>' + url + '<' in ET.tostring(self.xmlobject, encoding='unicode'):
                return True
        elif ET.tostring(member_node, encoding='unicode') in ET.tostring(self.xmlobject, encoding='unicode'):
            return True
        else:
            return False

    def add_url_to_category_object(self, urlobject: URLObject) -> None:
        """Add a URL to the URL category object self

        :param urlobject: URL or URL expression
        :type urlobject: common.URLObject
        """
        # If urlobject is already a member of self group, do nothing
        if self.have_member(urlobject.name):
            return

        memlist = ET.Element('list')
        member = ET.SubElement(memlist, 'member')
        member.text = urlobject.name
        # &element=<list><member>contoso.com</member></list>
        member_element_xpath = '&' + \
                               constants.XPATH_ELEMENT + '=' + ET.tostring(memlist, encoding='unicode')

        if self.host_type == 'panorama':
            if self.location == 'Shared':
                self._session.add_member_to_shared_custom_url_category(
                    member_element_xpath, self.name)
            else:  # self.location == '<device group name>'
                self._session.add_member_to_device_group_custom_url_category(
                    member_element_xpath, self.name, self.location)
        """
        else:  # self.host_type == 'firewall'
            if self.location == 'Panorama':
                raise BadActionError(
                    "Service group {0} is read-only as it is managed by Panorama".format(self.name))
            elif self.location == 'Shared':
                self.xmlobject = self._session.add_member_to_shared_service_group(
                    member_element_xpath, self.name)
            else:  # self.location = '<vsys no>'
                self._session.add_member_to_vsys_service_group(
                    member_element_xpath, self.name, self.location)
        """

        memlist = self.xmlobject.find('list')
        memlist.append(member)

    def add_urls_to_category_object(self, add_list: List[URLObject]) -> None:
        """Add multiple URLs to the URL category object self

        :param urlobject: URL or URL expression
        :type urlobject: common.URLObject
        """
        # Remove existing URLs in URL category object from add_list
        for idx, urlobject in enumerate(add_list):
            if self.have_member(urlobject.name):
                add_list.pop(idx)

        # Prepare URL member list
        member_element_xpath = '<list>'
        for urlobject in add_list:
            member_element_xpath += constants.NODE_MEMBER.format(urlobject.name)
        member_element_xpath += '</list>'

        # &element=<list><member>contoso.com</member><member>*.contoso.com</member></list>
        member_element_xpath = '&' + \
                               constants.XPATH_ELEMENT + '=' + member_element_xpath

        if self.host_type == 'panorama':
            if self.location == 'Shared':
                self._session.add_member_to_shared_custom_url_category(
                    member_element_xpath, self.name)
            else:  # self.location == '<device group name>'
                self._session.add_member_to_device_group_custom_url_category(
                    member_element_xpath, self.name, self.location)
        """
        else:  # self.host_type == 'firewall'
            if self.location == 'Panorama':
                raise BadActionError(
                    "Service group {0} is read-only as it is managed by Panorama".format(self.name))
            elif self.location == 'Shared':
                self.xmlobject = self._session.add_member_to_shared_service_group(
                    member_element_xpath, self.name)
            else:  # self.location = '<vsys no>'
                self._session.add_member_to_vsys_service_group(
                    member_element_xpath, self.name, self.location)
        """
        # Update xmlobject
        memlist = self.xmlobject.find('list')
        for urlobject in add_list:
            member = ET.Element('member')
            member.text = urlobject.name
            memlist.append(member)

    def remove_url_from_category_object(self, urlobject: URLObject) -> None:
        """Remove a URL from the URL category object self
        The caller needs to check if urlobject is a member

        :param urlobject: URL or URL expression
        :type urlobject: common.URLObject
        """
        member_text = urlobject.name
        # xpath_tail = "/list/member[text()=''contoso.com']"
        xpath_tail = '/list' + \
                     constants.XPATH_MEMBER_TEXT.format(member_text)

        # Remove from firewall system
        if self.host_type == 'panorama':
            if self.location == 'Shared':
                self._session.remove_member_from_shared_custom_url_category(
                    xpath_tail, self.name)
            else:  # self.location == '<device group name>'
                self._session.remove_member_from_device_group_custom_url_category(
                    xpath_tail, self.name, self.location)
        """
        else:  # self.host_type == 'firewall'

            if self.location == 'Panorama':
                raise BadActionError(
                    "Service group {0} is read-only as it is managed by Panorama".format(self.name))
            elif self.location == 'Shared':
                self._session.remove_service_from_shared_service_group(
                    xpath_tail, self.name)
            else:  # self.location = '<vsys no>'
                self._session.remove_service_from_vsys_service_group(
                    xpath_tail, self.name, self.location)
        """
        # Remove from xmlobject
        xml_member_path = 'list/member'
        for m in self.xmlobject.findall(xml_member_path):
            if m.text == member_text:
                memlist = self.xmlobject.find('list')
                memlist.remove(m)
                break

    def remove_urls_from_category_object(self, delete_list: List[URLObject]) -> None:
        """Remove multiple URLs from the URL category object self
        The caller needs to check if urlobject is a member

        :param urlobject: URL or URL expression
        :type urlobject: common.URLObject
        """
        # Calculate remaining members after deletion
        remainder = list(set(self.get_member_urls()) - set([url.name for url in delete_list]))

        # Prepare URL member list
        list_xpath = '<list>'
        for url in remainder:
            list_xpath += constants.NODE_MEMBER.format(url)
        list_xpath += '</list>'
        node_xpath = '/list'
        # &element=<list><member>contoso.com</member><member>*.contoso.com</member></list>
        member_element_xpath = '&' + \
                               constants.XPATH_ELEMENT + '=' + list_xpath

        # Update custom URL object with new list
        if self.host_type == 'panorama':
            if self.location == 'Shared':
                self._session.edit_shared_custom_url_category(node_xpath, member_element_xpath, self.name)
            else:  # self.location == '<device group name>'
                self._session.edit_device_group_custom_url_category(
                    node_xpath, member_element_xpath, self.name, self.location)
        """
        else:  # self.host_type == 'firewall'

            if self.location == 'Panorama':
                raise BadActionError(
                    "Service group {0} is read-only as it is managed by Panorama".format(self.name))
            elif self.location == 'Shared':
                self._session.remove_service_from_shared_service_group(
                    xpath_tail, self.name)
            else:  # self.location = '<vsys no>'
                self._session.remove_service_from_vsys_service_group(
                    xpath_tail, self.name, self.location)
        """
        # Populate xmlobject with remainder
        memlist = self.xmlobject.find('list')
        self.xmlobject.remove(memlist)
        newlist = ET.fromstring(list_xpath)
        self.xmlobject.append(newlist)

    def get_member_urls(self) -> List[str]:
        """
        Read xmlobject and return a list of member names of the service group
        """
        xml_member_path = 'list/member'
        return [x.text for x in self.xmlobject.findall(xml_member_path)]

    def print_url_category(self) -> None:
        """Print content of URL category object
        """
        print(('*** PAN custom URL category: {0} ***\n'.format(self.name)))
        if self.xmlobject is None:
            print(('Custom URL category {0} is NEW and not defined yet!\n'.format(
                self.name)))
        else:
            members = self.get_member_urls()
            print(('{0} members:'.format(len(members))))
            print((', '.join(members) + '\n'))

    def append_description(self, desc) -> None:  # pylint: disable=unused-argument
        """
        PAN only support max desc length of 1023
        If len of new description is greater than 1023,
        remove the first record number in current description,
        and then append new record number to it
        - Algorithm:
          + If self.desc is not set from xmlobject, set it
          + Check if len(self._desc) + len(' ') + len(desc) > 1023, remove first record number and space from self._desc
          + Append desc to self.desc
        """
        """
        if len(self.desc) == 0:
            self.desc = desc
        if len(self.desc) + len(' ') + len(desc) > 1023:
            # Find index of the first space character
            idx = self.desc.index(' ')
            # Slice current desc removing first record number and space
            self.desc = self.desc[idx + 1:]
        self.desc += ' ' + desc
        """
        pass
