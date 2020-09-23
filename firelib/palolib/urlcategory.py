"A module to represent service and service group objects"

import xml.etree.ElementTree as ET
from typing import List

from ..common import firelogging
from ..common.objects import URLObject
from . import constants, responses
from .objectbase import ConfigBase
from .panapi import PANAPISession

# START LOGGING TO FILE
logger = firelogging.FireLogger(name=__name__).firelogger
logger.debug('*** Start of palolib objects ***')


class URLCategory(ConfigBase):
    """
    Public class for representing a PAN custom URL category object
    """

    def __init__(self, name, apisession: PANAPISession, location='Shared', description='') -> None:
        """Initialize URLCategory object

        :param name: Name of custom URL category object
        :type name: str
        :param apisession: Either firewall or Panorama API session
        :type apisession: PANAPISession
        :param location: Location of URL category object, defaults to 'Shared'. If Panorama service object, location can be 'Shared' or '<device group name>'. If Firewall service object, location can be 'Panorama', 'Shared', or '<vsys name>'. The Firewall 'Shared' is for multi-vsys. The single vsys firewall, the location is 'vsys1'
        :type location: str, optional
        """
        ConfigBase.__init__(self, name, apisession)
        self._location = location
        self._desc = description
        if self._session.panos == "8.1.0":
            pass
        elif self._session.panos == "8.0.0":
            pass
        else:  # self._session.panos == "default":
            if self._session.hosttype == 'manager':
                if self._location == "Shared":
                    self._xpath_head += constants.XPATH_SHARED + constants.XPATH_PROFILES + \
                        constants.XPATH_CUSTOM_URL_CATEGORY + constants.XPATH_ENTRY.format(self.name)
                else:  # self.location == '<device group name>'
                    self._xpath_head += constants.XPATH_DEVICES + constants.XPATH_ENTRY.format(
                        constants.XPATH_ENTRY_LOCALHOST_LOCALDOMAIN) + constants.XPATH_DEVICE_GROUP + constants.XPATH_ENTRY.format(self._location) + constants.XPATH_PROFILES + constants.XPATH_CUSTOM_URL_CATEGORY + constants.XPATH_ENTRY.format(self.name)
            else:  # self._session.hosttype == 'firewall'
                pass

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, l):
        self._location = l

    def build_xml_object(self, **kwargs) -> None:
        """Build xml object of the custom URL category object
        **kwargs:
        + name = self._name - not needed
        + loc: Only required by non-shared object
        + members: List of service/group names
        Return something similar to:
                        <entry name="url-test-url" loc="internet">
                                        <list>
                                        <member>*.abc.com</member>
                                        </list>
                                        <description>99999999</description>
                        </entry>
        or for shared object
                        <entry name="url-test">
                                        <list>
                                        <member>*.abc.com</member>
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

    def have_member(self, url: str) -> bool:
        """Check if url is existent in the URL category object

        :param url: URL or URL expression
        :type url: str
        """
        member_node = ET.Element(constants.TAG_MEMBER)
        member_node.text = url
        # If <member>tcp-80</member> in self.xmlobject
        # If the is uncommitted change - candidate config
        """
		ET.tostring(member_node): <member>contoso.com</member>
		ET.tostring(self.xmlobject):
		<entry admin="firewallauto" dirtyId="19" name="url-test" time="2019/04/11 15:43:40">
			<static admin="admin1" dirtyId="19" time="2019/04/11 15:43:40">
			<member admin="admin2" dirtyId="15" time="2019/04/11 10:37:09">contoso.com</member>
		"""
        if 'dirtyId=' in ET.tostring(self.xmlobject, encoding='unicode'):
            if '>' + url + '<' in ET.tostring(self.xmlobject, encoding='unicode'):
                return True
        if ET.tostring(member_node, encoding='unicode') in ET.tostring(self.xmlobject, encoding='unicode'):
            return True

        return False

    def add_urls_to_category_object(self, add_list: List[URLObject], description: str) -> None:
        """Add list of URL objects to category self

        :param add_list: List of URL objects to be added to self
        :type add_list: List[URLObject]
        :param description: New description usually Win@ record to be appended to self's description
        :type description: str
        """
        # Remove existing URLs in URL category object from add_list
        add_urls = [x.name for x in add_list if not self.have_member(x.name)]

        if len(add_urls) > 0:
            # Prepare URL member list
            member_element_xpath = '<list>'
            for url in add_urls:
                member_element_xpath += constants.NODE_MEMBER.format(url)
            member_element_xpath += '</list>'

            element_xpath = '&' + \
                constants.XPATH_ELEMENT + '=' + member_element_xpath

            xpath = self._xpath_head + element_xpath
            #response_text = self._session.config_command(action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
            response_text = self._session.config_command(
                method=constants.URL_REQUEST_METHOD_POST, action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
            result = responses.Response(response_text)
            if not result.ok():
                raise RuntimeError(
                    "Failed to add members to custom URL category: {0}".format(
                        result.get_error()))

            # Update xmlobject
            memlist = self.xmlobject.find('list')
            for url in add_urls:
                member = ET.Element('member')
                member.text = url
                memlist.append(member)

            self.append_description(description, 255)

    def remove_urls_from_category_object(self, delete_list: List[URLObject], description: str) -> None:
        """Remove multiple URLs from the URL category object self

        :param delete_list: List of URL objects to be removed from self
        :type delete_list: List[URLObject]
        :param description: New description usually Win@ record to be appended to self's description
        :type description: str
        """
        # Calculate remaining members after deletion
        commonset = set(self.get_member_urls()) & {urlobj.name for urlobj in delete_list}
        remainder = []
        if len(commonset) > 0:
            remainder = [x for x in self.get_member_urls() if x not in commonset]

        # Only edit/remove if remainder is different from current category content
        if len(remainder) > 0:
            # Prepare URL member list
            member_element_xpath = '<list>'
            for objname in remainder:
                member_element_xpath += constants.NODE_MEMBER.format(objname)
            member_element_xpath += '</list>'
            element_xpath = '&' + \
                constants.XPATH_ELEMENT + '=' + member_element_xpath

            xpath = self._xpath_head + constants.XPATH_LIST + element_xpath
            response_text = self._session.config_command(
                method=constants.URL_REQUEST_METHOD_POST, action=constants.URL_REQUEST_ACTION_EDIT, xpath=xpath)
            result = responses.Response(response_text)
            if not result.ok():
                raise RuntimeError(
                    "Failed to delete members from custom URL category: {0}".format(
                        result.get_error()))

            # Populate xmlobject with remainder
            memlist = self.xmlobject.find('list')
            self.xmlobject.remove(memlist)
            newlist = ET.fromstring(member_element_xpath)
            self.xmlobject.append(newlist)

            self.append_description(description, 255)

    def edit_url_category_object(self, edit_list: List[URLObject]) -> None:
        """HAVEN'T USED YET - Remove multiple URLs from the URL category object self
        The caller needs to check if urlobject is a member

        :param urlobject: URL or URL expression
        :type urlobject: common.URLObject
        """
        # Prepare URL member list
        member_element_xpath = '<list>'
        for objname in edit_list:
            member_element_xpath += constants.NODE_MEMBER.format(objname)
        member_element_xpath += '</list>'
        element_xpath = '&' + \
            constants.XPATH_ELEMENT + '=' + member_element_xpath

        xpath = self._xpath_head + constants.XPATH_LIST + element_xpath
        response_text = self._session.config_command(action=constants.URL_REQUEST_ACTION_EDIT, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise RuntimeError(
                "Failed to delete members from custom URL category: {0}".format(
                    result.get_error()))

        # Populate xmlobject with edit_list
        memlist = self.xmlobject.find('list')
        self.xmlobject.remove(memlist)
        newlist = ET.fromstring(member_element_xpath)
        self.xmlobject.append(newlist)

    def get_member_urls(self) -> List[str]:
        """
        Read xmlobject and return a list of member names of the service group
        """
        xml_member_path = 'list/member'
        return [x.text for x in self.xmlobject.findall(xml_member_path)]

    def print_object(self) -> None:
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
