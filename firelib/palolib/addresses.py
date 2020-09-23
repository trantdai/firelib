"A module to represent address and address group objects. In the future, SSH classes like SSHAdress making use of panssh.PANSSHSession will be created"

import ipaddress
import xml.etree.ElementTree as ET
from typing import List, Union

from ..common import firelogging, util
from ..common.objects import IPObject, FWObject
from . import constants, responses
from .objectbase import ConfigBase
from .panapi import PANAPISession

# START LOGGING TO FILE
logger = firelogging.FireLogger(name=__name__).firelogger
logger.debug('*** Start of palolib objects ***')


class _AddressBase(ConfigBase):
    """Base class for Address and AddressGroup classes
    """

    def __init__(self, name, apisession: PANAPISession, location='Shared', description='') -> None:
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
        ConfigBase.__init__(self, name, apisession)

        self._location = location
        self._tags = None
        self._desc = description

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


class Address(_AddressBase):
    def __init__(self, name, apisession: PANAPISession, location='Shared', description='') -> None:
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
        _AddressBase.__init__(self, name, apisession, location, description)
        
        if self._session.panos == "8.1.6":
            pass
        elif self._session.panos == "8.0.10":
            pass
        else:  # self._session.panos == "default":
            if self._session.hosttype == 'manager':
                if self._location == "Shared":
                    self._xpath_head += constants.XPATH_SHARED + \
                        constants.XPATH_ADDRESS + constants.XPATH_ENTRY.format(self.name)
                else:  # self.location == '<device group name>'
                    self._xpath_head += constants.XPATH_DEVICES + constants.XPATH_ENTRY.format(
                        constants.XPATH_ENTRY_LOCALHOST_LOCALDOMAIN) + constants.XPATH_DEVICE_GROUP + constants.XPATH_ENTRY.format(self._location) + constants.XPATH_ADDRESS + constants.XPATH_ENTRY.format(self.name)
            else:  # self._session.hosttype == 'firewall'
                pass

    def build_xml_object(self, ipobject: IPObject, description='fwauto') -> None:
        """
        ipobject = common.IPObject
        """
        xmlobject = ET.Element(constants.TAG_ENTRY)
        # <entry name="H-1.1.1.1" />
        xmlobject.set(constants.TAG_ATTRIBUTE_NAME, ipobject.name)
        """
        ipnode = ET.Element(ipobject.get_element_name())
        # <ip-netmask>1.1.1.1</ip-netmask>
        ipnode.text = str(ipobject)
        # <entry name="H-1.1.1.1"><ip-netmask>1.1.1.1</ip-netmask></entry>
        xmlobject.append(ipnode)
        """
        # Add IP node <ip-netmask>1.1.1.1</ip-netmask>
        ipnode = ET.SubElement(xmlobject, ipobject.get_element_name())
        ipnode.text = str(ipobject)

        # Add description node
        description_node = ET.SubElement(xmlobject, 'description')
        description_node.text = description
        # return xmlobject
        self._xmlobject = xmlobject

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

    @staticmethod
    def is_address_range_in_class_c_network(address_range) -> bool:
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
        return bool(ipaddress.ip_address(bytearray(fhost)) in ipaddress.ip_network(bytearray(addrnet)) and ipaddress.ip_address(bytearray(lhost)) in ipaddress.ip_network(bytearray(addrnet)))

    @staticmethod
    def unpack_address_input_to_single_addresses(address) -> List[str]:
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
        if '/' in address:
            netmask = int(address.split('/')[1])
            two_first_octets = address.split(
                '.')[0] + '.' + address.split('.')[1]
            three_first_octets = address[:address.rfind('.')]
            third_octet = int(address.split('.')[2])

            if netmask == 32:
                return [address.split('/')[0]]
            if 22 <= netmask <= 24:
                class_c_network_num = pow(24 - netmask, 2)
                # If class C network
                if class_c_network_num == 0:
                    return [three_first_octets + '.50']
                all_third_octets = list(range(
                    third_octet, third_octet + class_c_network_num))
                return [two_first_octets + '.' + str(x) + '.50' for x in
                        all_third_octets]
            # If netmask > 24 and < 32
            netobj = ipaddress.ip_network(bytearray(address))
            # return list of 2nd last IP in that network
            return [str(netobj[-2])]
        # elif FQDN
        # If single fixed IP without netmask
        return [address]

    def contain_value(self, input_value) -> bool:
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
                if self_fhost <= input_value <= self_lhost:
                    return True
            else:  # If self_value is a single IP
                if input_value == self_value:
                    return True
        return False

    def print_object(self) -> None:
        print(('*** PAN Address: {0} ***\n'.format(self.name)))
        if self.xmlobject is None:
            print(('Address {0} is NEW and not defined yet!\n'.format(
                self.name)))
        else:
            print(('Value: {0}'.format(self.value)))
            print(('Type: {0}'.format(self.type)))
            print(('Location: {0}'.format(self.location)))
            print(('Description: {0}\n'.format(self.desc)))


class AddressGroup(_AddressBase):
    def __init__(self, name, apisession: PANAPISession, location='Shared', description='') -> None:
        """
        location: location of address group. If Panorama address group, location can be 'Shared' or '<device group name>'. If Firewall address group, location can be 'Panorama', 'Shared', or '<vsys name>'. The Firewall 'Shared' is for multi-vsys. The single vsys firewall, the location is 'vsys1'
        self._xmlobject: Output of show/get request, i.e. \        type=config&action=get&xpath=/config/shared/address-group/entry[@name='object_group_name']
        Example: <entry name="object_group_name"><static><member>...</member><description>...</description><tag>...<tag></entry>
        """
        _AddressBase.__init__(self, name, apisession, location, description)
        
        if self._session.panos == "8.1.6":
            pass
        elif self._session.panos == "8.0.10":
            pass
        else:  # self._session.panos == "default":
            if self._session.hosttype == 'manager':
                if self._location == "Shared":
                    self._xpath_head += constants.XPATH_SHARED + \
                        constants.XPATH_ADDRESS_GROUP + constants.XPATH_ENTRY.format(self.name)
                else:  # self.location == '<device group name>'
                    self._xpath_head += constants.XPATH_DEVICES + constants.XPATH_ENTRY.format(
                        constants.XPATH_ENTRY_LOCALHOST_LOCALDOMAIN) + constants.XPATH_DEVICE_GROUP + constants.XPATH_ENTRY.format(self._location) + constants.XPATH_ADDRESS_GROUP + constants.XPATH_ENTRY.format(self.name)
            else:  # self._session.hosttype == 'firewall'
                pass

    def build_xml_object(self, **kwargs) -> None:
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

    def add_member_to_static_group(self, ipobject: Union[IPObject, FWObject]) -> None:
        """Add a common.objects.py to self group. The caller of this method will check:
            - If ipobject is a FW object, is it defined?
            - If ipobject is a new address, create it in FW system first
            - See fireobjectupdater.update_pan_address_group_object() for usage example

        Parameters
        ----------
        ipobject: firelib\common\objects.py FWObject
        - Algorithm:
          + Check if ipobject is object or group object via ipobject.get_type()
          + Check if ipobject.name exists on host. If not do nothing.
          + Build member_element_xpath
          + Call API to add object to group on FW management, if successful then
          + Add <member>H-1.1.1.1</member> to self._xmlobject to update self._xmlobject
        """
        # If ipobject is already a member of self group, do nothing
        if self.have_static_member(ipobject.name):
            return

        member_node = ET.Element(constants.TAG_MEMBER)
        # ipobject.get_name() returns something formatted like H-1.1.1.1
        member_node.text = ipobject.name
        new_static_node = ET.Element(constants.TAG_STATIC)
        new_static_node.append(member_node)
        member_element_xpath = '&' + constants.XPATH_ELEMENT + \
            '=' + ET.tostring(new_static_node, encoding='unicode')

        xpath = self._xpath_head + member_element_xpath
        response_text = self._session.config_command(action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise RuntimeError(
                "Failed to add a member to address group: {0}".format(
                    result.get_error()))

        static_node = self.xmlobject.find(constants.TAG_STATIC)
        static_node.append(member_node)

    def have_static_member(self, object_name) -> bool:
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
        return False

    def get_static_member_names(self) -> List[str]:
        """
        Read xmlobject and return a list of member names of the static group
        """
        xml_member_path = constants.TAG_STATIC + constants.FORWARD_SLASH + \
            constants.TAG_MEMBER
        return [x.text for x in self.xmlobject.findall(xml_member_path)]

    def add_members_to_static_group(self, add_list: List[Union[IPObject, FWObject]], description: str) -> None:
        """Add multiple objects to address group self

        :param add_list: List of objects to be added
        :type add_list: List[Union[IPObject, FWObject]]
        :param description: New description usually Win@ record to be appended to self's description
        :type description: str
        """
        # Remove existing members in self group from add_list
        filtered_members = [x.name for x in add_list if not self.have_static_member(x.name)]

        # Remove duplicates like tcp-80 and tcp/80 have the same name
        seen = set()
        seen_add = seen.add
        add_members = [x for x in filtered_members if not (x in seen or seen_add(x))]

        if len(add_members) > 0:
            # Prepare member object list
            member_element_xpath = '<static>'
            for member_name in add_members:
                member_element_xpath += constants.NODE_MEMBER.format(member_name)
            member_element_xpath += '</static>'

            element_xpath = '&' + \
                constants.XPATH_ELEMENT + '=' + member_element_xpath

            xpath = self._xpath_head + element_xpath
            #response_text = self._session.config_command(action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
            response_text = self._session.config_command(
                method=constants.URL_REQUEST_METHOD_POST, action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
            result = responses.Response(response_text)
            if not result.ok():
                raise RuntimeError(
                    "Failed to add members to address group: {0}".format(
                        result.get_error()))

            # Update xmlobject
            memlist = self.xmlobject.find('static')
            for member_name in add_members:
                member = ET.SubElement(memlist, 'member')
                member.text = member_name

            self.append_description(description)

    def remove_members_from_static_group(self, delete_list: List[Union[IPObject, FWObject]], description: str) -> None:
        """Remove multiple address objects from the address group object self

        :param delete_list: List of objects to be deleted
        :type delete_list: List[Union[IPObject, FWObject]]
        :param description: New description usually Win@ record to be appended to self's description
        :type description: str
        """
        # Calculate remaining members after deletion
        # commonset = set(self.get_static_member_names()) & set([addrobj.name for addrobj in delete_list])
        commonset = set(self.get_static_member_names()) & {addrobj.name for addrobj in delete_list}
        remainder = []
        if len(commonset) > 0:
            remainder = [x for x in self.get_static_member_names() if x not in commonset]

        # Only edit/remove if there is actual change
        if len(remainder) > 0:
            # Prepare member element xpath
            static_xpath = '<static>'
            for objname in remainder:
                static_xpath += constants.NODE_MEMBER.format(objname)
            static_xpath += '</static>'
            element_xpath = '&' + \
                constants.XPATH_ELEMENT + '=' + static_xpath

            xpath = self._xpath_head + constants.XPATH_STATIC + element_xpath
            #response_text = self._session.config_command(action=constants.URL_REQUEST_ACTION_EDIT, xpath=xpath)
            response_text = self._session.config_command(
                method=constants.URL_REQUEST_METHOD_POST, action=constants.URL_REQUEST_ACTION_EDIT, xpath=xpath)
            result = responses.Response(response_text)
            if not result.ok():
                raise RuntimeError(
                    "Failed to delete members from address group: {0}".format(
                        result.get_error()))

            # Populate xmlobject with remainder
            memlist = self.xmlobject.find('static')
            self.xmlobject.remove(memlist)
            newlist = ET.fromstring(static_xpath)
            self.xmlobject.append(newlist)

            self.append_description(description)

    def contain_static_value(self, object_value) -> bool:
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
            address_object.get_object()
            if address_object.xmlobject is None:
                # address_object is child address group
                children_group_names.append(address_object.name)
            else:  # address_object is child address
                if address_object.contain_value(object_value):
                    return True
        # Recursive call to check child groups
        if len(children_group_names) > 0:
            for group_name in children_group_names:
                group_object = AddressGroup(
                    group_name, self._session, self.location)
                group_object.get_object()
                if group_object.contain_static_value(object_value):
                    return True
        return False

    def print_object(self) -> None:
        print(('*** PAN Address Group: {0} ***\n'.format(self.name)))
        # print('')
        if self.xmlobject is None:
            print(('Address group {0} is NEW and not defined yet!\n'.format(
                self.name)))
        else:
            members = self.get_static_member_names()
            print(('{0} members:'.format(len(members))))
            print((', '.join(members) + '\n'))

            print(('Description: {0}\n'.format(self.desc)))
