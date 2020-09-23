"A module to represent service and service group objects"

import xml.etree.ElementTree as ET
from typing import List, Set, Union

from ..common import constants as common_constants
from ..common import firelogging
from ..common.objects import ServiceObject, FWObject
from . import constants, responses
from .objectbase import ConfigBase
from .panapi import PANAPISession

# START LOGGING TO FILE
logger = firelogging.FireLogger(name=__name__).firelogger
logger.debug('*** Start of palolib objects ***')


class _ServiceBase(ConfigBase):
    """Base class for Service and ServiceGroup classes
    """

    def __init__(self, name, apisession: PANAPISession, location='Shared') -> None:
        """
        - Input:
          + name: string - name of service object
          + location: location of service object. If Panorama service object, location can be 'Shared'
          or '<device group name>'. If Firewall service object, location can be 'Panorama', 'Shared', or '<vsys name>'.
          The Firewall 'Shared' is for multi-vsys. The single vsys firewall, the location is 'vsys1'
        - Output:
          + self._xmlobject: Output of show/get request, i.e.
          type=config&action=get&xpath=/config/shared/service/entry[@name='tcp_complex']. Example:
                                        <entry name="tcp_complex">
                                        <protocol><tcp>
                                        <port>10959,10960,10961,40959,40960,40961,10977,21271,40977,51271</port>
                                        </tcp></protocol>
                                        <tag><member>complex</member></tag>
                                        <description>complex</description>
                                        </entry>
        """
        ConfigBase.__init__(self, name, apisession)

        self._location = location
        self._tags = None

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


class Service(_ServiceBase):
    def __init__(self, name, apisession, location='Shared', description='') -> None:
        """
        - Input:
          + name: string - name of service object
          + location: location of service object. If Panorama service object, location can be 'Shared'
          or '<device group name>'. If Firewall service object, location can be 'Panorama', 'Shared', or '<vsys name>'.
          The Firewall 'Shared' is for multi-vsys. The single vsys firewall, the location is 'vsys1'
        - Output:
          + self._xmlobject: Output of show/get request, i.e.
          type=config&action=get&xpath=/config/shared/service/entry[@name='tcp_complex']. Example:
                                        <entry name="tcp_complex">
                                        <protocol><tcp>
                                        <port>10959,10960,10961,40959,40960,40961,10977,21271,40977,51271</port>
                                        </tcp></protocol>
                                        <tag><member>complex</member></tag>
                                        <description>complex</description>
                                        </entry>
        """
        _ServiceBase.__init__(self, name, apisession, location)
        self._desc = description
        if self._session.panos == "8.1.0":
            pass
        elif self._session.panos == "8.0.0":
            pass
        else:  # self._session.panos == "default":
            if self._session.hosttype == 'manager':
                if self._location == "Shared":
                    self._xpath_head += constants.XPATH_SHARED + \
                        constants.XPATH_SERVICE + constants.XPATH_ENTRY.format(self.name)
                else:  # self.location == '<device group name>'
                    self._xpath_head += constants.XPATH_DEVICES + constants.XPATH_ENTRY.format(
                        constants.XPATH_ENTRY_LOCALHOST_LOCALDOMAIN) + constants.XPATH_DEVICE_GROUP + constants.XPATH_ENTRY.format(self._location) + constants.XPATH_SERVICE + constants.XPATH_ENTRY.format(self.name)
            else:  # self._session.hosttype == 'firewall'
                pass

    def build_xml_object(self, serviceobject: ServiceObject, description='fireauto') -> None:
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
    def value(self):
        v = self.protocol + '/'
        if self.sport is not None:
            v += self.sport + '/'
        v += self.port
        return v

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

    @staticmethod
    def is_service_forbidden(fullservice) -> Set[Union[bool, str]]:
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
    def is_port_range_valid(port) -> bool:
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
    def is_service_range_valid(service) -> bool:
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
    def unpack_service_to_protocol_ports(service) -> Set[str]:
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

    def print_service_object(self) -> None:
        print(('*** PAN Service: {0} ***\n'.format(self.name)))
        if self.xmlobject is None:
            print(('Service {0} is NEW and not defined yet!\n'.format(
                self.name)))
        else:
            print(('Value: {0}'.format(self.value)))
            print(('Location: {0}'.format(self.location)))
            print(('Description: {0}\n'.format(self.desc)))


class ServiceGroup(_ServiceBase):
    def __init__(self, name, apisession, location='Shared') -> None:
        """
        - Input:
          + name: string - name of service object
          + location: location of service object. If Panorama service object, location can be 'Shared'
          or '<device group name>'. If Firewall service object, location can be 'Panorama', 'Shared', or '<vsys name>'.
          The Firewall 'Shared' is for multi-vsys. The single vsys firewall, the location is 'vsys1'
        - Output:
          + self._xmlobject: Output of show/get request, i.e.
          type=config&action=get&xpath=/config/shared/service/entry[@name='tcp_complex']. Example:
                                        <entry name="tcp_complex">
                                        <protocol><tcp>
                                        <port>10959,10960,10961,40959,40960,40961,10977,21271,40977,51271</port>
                                        </tcp></protocol>
                                        <tag><member>complex</member></tag>
                                        <description>complex</description>
                                        </entry>
        """
        _ServiceBase.__init__(self, name, apisession, location)
        if self._session.panos == "8.1.0":
            pass
        elif self._session.panos == "8.0.0":
            pass
        else:  # self._session.panos == "default":
            if self._session.hosttype == 'manager':
                if self._location == "Shared":
                    self._xpath_head += constants.XPATH_SHARED + \
                        constants.XPATH_SERVICE_GROUP + constants.XPATH_ENTRY.format(self.name)
                else:  # self.location == '<device group name>'
                    self._xpath_head += constants.XPATH_DEVICES + constants.XPATH_ENTRY.format(
                        constants.XPATH_ENTRY_LOCALHOST_LOCALDOMAIN) + constants.XPATH_DEVICE_GROUP + constants.XPATH_ENTRY.format(self._location) + constants.XPATH_SERVICE_GROUP + constants.XPATH_ENTRY.format(self.name)
            else:  # self._session.hosttype == 'firewall'
                pass

    def build_xml_object(self, **kwargs) -> None:
        """
        **kwargs:
        + name = self._name - not needed
        + members = list of service/group names
        + tags = list of tags
        Return something similar to: <entry name="http-https">
        <members><member>http</member><member>https</member></members>
        <tag><member>FWAUTO</member></tag>
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

    def have_member(self, object_name) -> bool:
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
        """
		ET.tostring(member_node): <member>1.1.0.0/23</member>
		ET.tostring(self.xmlobject):
		<entry admin="fwauto" dirtyId="19" name="groupobj" time="2019/04/11 15:43:40">
			<static admin="fwauto" dirtyId="19" time="2019/04/11 15:43:40">
			<member admin="dtran" dirtyId="15" time="2019/04/11 10:37:09">fireobject1</member>
		"""
        if 'dirtyId=' in ET.tostring(self.xmlobject, encoding='unicode'):
            if '>' + object_name + '<' in ET.tostring(self.xmlobject, encoding='unicode'):
                return True
        if ET.tostring(member_node, encoding='unicode') in ET.tostring(self.xmlobject, encoding='unicode'):
            return True
        return False

    def get_member_names(self):
        """
        Read xmlobject and return a list of member names of the service group
        """
        xml_member_path = 'members/member'
        return [x.text for x in self.xmlobject.findall(xml_member_path)]

    def add_members_to_service_group(self, add_list: List[Union[ServiceObject, FWObject]], description: str) -> None:
        """Add multiple objects to service group self

        :param add_list: List of objects to be added
        :type add_list: List[Union[ServiceObject, FWObject]]
        :param description: New description usually support ticket to be appended to self's description
        :type description: str
        """
        # Remove existing service object in service group object from add_list
        filtered_members = [x.name for x in add_list if not self.have_member(x.name)]

        # Remove duplicates like tcp-80 and tcp/80 have the same name
        seen = set()
        seen_add = seen.add
        add_members = [x for x in filtered_members if not (x in seen or seen_add(x))]

        if len(add_members) > 0:
            # Prepare member object xpath
            member_element_xpath = '<members>'
            for member_name in add_members:
                member_element_xpath += constants.NODE_MEMBER.format(member_name)
            member_element_xpath += '</members>'
            # &element=<members><member>tcp-80</member></members>
            element_xpath = '&' + \
                constants.XPATH_ELEMENT + '=' + member_element_xpath

            xpath = self._xpath_head + element_xpath
            #response_text = self._session.config_command(action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
            response_text = self._session.config_command(
                method=constants.URL_REQUEST_METHOD_POST, action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
            result = responses.Response(response_text)
            if not result.ok():
                raise RuntimeError(
                    "Failed to add members to service group: {0}".format(
                        result.get_error()))

            # Update xmlobject
            memlist = self.xmlobject.find('members')
            for member_name in add_members:
                member = ET.SubElement(memlist, 'member')
                member.text = member_name

            self.append_description(description)

    def remove_members_from_service_group(self, delete_list: List[Union[ServiceObject, FWObject]], description: str) -> None:
        """Remove multiple objects from service group self

        :param add_list: List of objects to be removed
        :type add_list: List[Union[ServiceObject, FWObject]]
        :param description: New description usually Win@ record to be appended to self's description
        :type description: str
        """
        # Calculate remaining members after deletion
        commonset = set(self.get_member_names()) & {srvobj.name for srvobj in delete_list}
        remainder = []
        if len(commonset) > 0:
            remainder = [x for x in self.get_member_names() if x not in commonset]

        # Only edit/remove if there is actual change
        if len(remainder) > 0:
            # Prepare member object xpath
            member_element_xpath = '<members>'
            for objname in remainder:
                member_element_xpath += constants.NODE_MEMBER.format(objname)
            member_element_xpath += '</members>'
            # &element=<members><member>tcp-80</member></members>
            element_xpath = '&' + \
                constants.XPATH_ELEMENT + '=' + member_element_xpath

            xpath = self._xpath_head + constants.XPATH_MEMBERS + element_xpath
            response_text = self._session.config_command(
                method=constants.URL_REQUEST_METHOD_POST, action=constants.URL_REQUEST_ACTION_EDIT, xpath=xpath)
            result = responses.Response(response_text)
            if not result.ok():
                raise RuntimeError(
                    "Failed to delete members from service group: {0}".format(
                        result.get_error()))

            # Populate xmlobject with remainder
            memlist = self.xmlobject.find('members')
            self.xmlobject.remove(memlist)
            newlist = ET.fromstring(member_element_xpath)
            self.xmlobject.append(newlist)

            self.append_description(description)

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

    def print_object(self) -> None:
        print(('*** PAN Service Group: {0} ***\n'.format(self.name)))
        if self.xmlobject is None:
            print(('Service group {0} is NEW and not defined yet!\n'.format(
                self.name)))
        else:
            members = self.get_member_names()
            print(('{0} members:'.format(len(members))))
            print((', '.join(members) + '\n'))
