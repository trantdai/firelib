"REPLACED BY panapi.py and commits.py"

import sys
import time
import xml.etree.ElementTree as ET

import requests

from ..common import constants as common_constants
from ..common import firelogging, firepass, sshsession, traceroute
from . import responses, constants

# START LOGGING TO FILE LIKE
logger = firelogging.FireLogger(name=__name__).firelogger
logger.debug('*** Start of panfwapi ***')


class NotConnectedError(AssertionError):
    pass


class BadResponseError(RuntimeError):
    pass


class BadHTTPResponseError(RuntimeError):
    pass


class PanFWAPISession:

    @staticmethod
    def extract_xml_object_from_response(response_text, xml_path):
        """
        response_text: Response from API call
        xml_path: XML path to locate and extract the interested xml portion\
        i.e 'result/entry'
        """
        root = ET.fromstring(response_text)
        xmlobj = root.find(xml_path)
        """
        if response_text = '<response status="success" code="7"><result/></response>', then xmlobj is None
        """
        return xmlobj

    def __init__(self, host=constants.FIREWALL_DEV_HOST_A):
        """
        host is the host address of the Panorama to be connected to.
        """
        self.__host = host
        if '.' not in host:
            self.__host = host + constants.PROD_HOST_POSTFIX
        self.__apikey = self.__get_palo_api_key()

    def get_session_host_role(self):
        """
        Get the role of the session host.
        Return: "panorama" or "firewall"
        """
        return 'firewall'

    def __get_palo_api_key(self):
        """
        Retrieve PAN API key from file
        """
        fp = firepass.FirePass()
        return fp.get_palo_apikey()

    # def get_palo_api_key(self):
    #    """
    #    Retrieve PAN API key from file
    #    """
    #    if self.__apikey is None:
    #        fp = firepass.FirePass()
    #        self.__apikey = fp.get_palo_apikey()

    def __check_connected(self):
        if self.__apikey is None:
            raise NotConnectedError("Need to connect() first")

    def __make_request(
            self,
            key=True,
            method=constants.URL_REQUEST_METHOD_GET,
            **kwargs):
        """
        Make the API request.
        key should be set to True if you want to add the API key to the parameters.
        method is either 'GET' or 'POST'. Default is 'GET'.
        kwargs is a easy way to set the url parameters. For instance to add a parameter action=set, you call the function with __make_request(action='set').
        RETURN: response object from request
        """
        if method == constants.URL_REQUEST_METHOD_GET:
            #url = 'https://{0}/api?'.format(self.__host)
            url = constants.URL_HTTPS + self.__host + constants.URL_API
            if key:
                self.__check_connected()
                url += 'key=' + self.__apikey + '&'
            url += '&'.join('{0}={1}'.format(k, v)
                            for k, v in kwargs.items())
            response = requests.get(url, verify=False)
        else:
            pass
        return response

    def __check_response(self, response):
        """
        Check that the request returned with a 200 status code and instantiate the
        response type with the text in the response.
        """
        if response.status_code == 200:
            return response.text
        raise BadHTTPResponseError(
            "HTTP responded with error code: {0}\nText:\n{1}".format(
                response.status_code, response.text))

    # ?type=commit&cmd=<commit></commit>
    def commit_command(self, cmd, commit_type=constants.URL_REQUEST_TYPE_COMMIT):
        r = self.__make_request(type=commit_type, cmd=cmd)
        response_text = self.__check_response(r)
        return response_text

    def config_command(self, config_type=constants.URL_REQUEST_TYPE_CONFIG,
                       action=constants.URL_REQUEST_ACTION_GET, xpath=None):
        r = self.__make_request(type=config_type, action=action, xpath=xpath)
        response_text = self.__check_response(r)
        return response_text

    def op_command(self, cmd, op_type=constants.URL_REQUEST_TYPE_OP):
        r = self.__make_request(type=op_type, cmd=cmd)
        response_text = self.__check_response(r)
        return response_text

    # HEAD XPATH BUILD
    # ADDRESS
    def build_shared_address_object_xpath_head(self):
        """
        Build xpath=config/shared/address
        """
        xpath_head = constants.XPATH_CONFIG + constants.XPATH_SHARED + constants.XPATH_ADDRESS
        return xpath_head

    def build_vsys_address_object_xpath_head(
            self, vsys=constants.VSYS_DEFAULT):
        """
        Build xpath=/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/address
        """
        xpath_head = constants.XPATH_CONFIG + constants.XPATH_DEVICES + \
            constants.XPATH_ENTRY.format(constants.XPATH_ENTRY_LOCALHOST_LOCALDOMAIN) + \
            constants.XPATH_VSYS + constants.XPATH_ENTRY.format(vsys) + constants.XPATH_ADDRESS
        return xpath_head

    def build_panorama_address_object_xpath_head(
            self, vsys=constants.VSYS_DEFAULT):
        """
        Build xpath=/config/panorama/vsys/entry[@name='vsys1']/address
        """
        xpath_head = constants.XPATH_CONFIG + constants.XPATH_PANORAMA + \
            constants.XPATH_VSYS + constants.XPATH_ENTRY.format(vsys) + \
            constants.XPATH_ADDRESS
        return xpath_head

    def build_shared_address_group_object_xpath_head(self):
        """
        Build xpath=config/shared/address-group
        """
        return constants.XPATH_CONFIG + constants.XPATH_SHARED + constants.XPATH_ADDRESS_GROUP

    def build_vsys_address_group_object_xpath_head(
            self, vsys=constants.VSYS_DEFAULT):
        """
        Build xpath=/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/address-group
        """
        xpath_head = constants.XPATH_CONFIG + constants.XPATH_DEVICES + \
            constants.XPATH_ENTRY.format(constants.XPATH_ENTRY_LOCALHOST_LOCALDOMAIN) + \
            constants.XPATH_VSYS + constants.XPATH_ENTRY.format(vsys) + constants.XPATH_ADDRESS_GROUP
        return xpath_head

    def build_panorama_address_group_object_xpath_head(
            self, vsys=constants.VSYS_DEFAULT):
        """
        Build xpath=/config/panorama/vsys/entry[@name='vsys1']/address
        """
        xpath_head = constants.XPATH_CONFIG + constants.XPATH_PANORAMA + \
            constants.XPATH_VSYS + constants.XPATH_ENTRY.format(vsys) + \
            constants.XPATH_ADDRESS_GROUP
        return xpath_head

    # SERVICE
    def build_shared_service_object_xpath_head(self):
        """
        Build xpath=config/shared/service
        """
        xpath_head = constants.XPATH_CONFIG + constants.XPATH_SHARED + \
            constants.XPATH_SERVICE
        return xpath_head

    def build_vsys_service_object_xpath_head(
            self, vsys=constants.VSYS_DEFAULT):
        """
        Build xpath=/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/service
        """
        xpath_head = constants.XPATH_CONFIG + constants.XPATH_DEVICES + \
            constants.XPATH_ENTRY.format(constants.XPATH_ENTRY_LOCALHOST_LOCALDOMAIN) + \
            constants.XPATH_VSYS + constants.XPATH_ENTRY.format(vsys) + constants.XPATH_SERVICE
        return xpath_head

    def build_panorama_service_object_xpath_head(
            self, vsys=constants.VSYS_DEFAULT):
        """
        Build xpath=/config/panorama/vsys/entry[@name='vsys1']/service
        """
        xpath_head = constants.XPATH_CONFIG + constants.XPATH_PANORAMA + \
            constants.XPATH_VSYS + constants.XPATH_ENTRY.format(vsys) + \
            constants.XPATH_SERVICE
        return xpath_head

    def build_shared_service_group_object_xpath_head(self):
        """
        Build xpath=config/shared/service-group
        """
        xpath_head = constants.XPATH_CONFIG + constants.XPATH_SHARED + \
            constants.XPATH_SERVICE_GROUP
        return xpath_head

    def build_vsys_service_group_object_xpath_head(
            self, vsys=constants.VSYS_DEFAULT):
        """
        Build xpath=/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/service-group
        """
        xpath_head = constants.XPATH_CONFIG + constants.XPATH_DEVICES + \
            constants.XPATH_ENTRY.format(constants.XPATH_ENTRY_LOCALHOST_LOCALDOMAIN) + \
            constants.XPATH_VSYS + constants.XPATH_ENTRY.format(vsys) + constants.XPATH_SERVICE_GROUP
        return xpath_head

    def build_panorama_service_group_object_xpath_head(
            self, vsys=constants.VSYS_DEFAULT):
        """
        Build xpath=/config/panorama/vsys/entry[@name='vsys1']/service-group
        """
        xpath_head = constants.XPATH_CONFIG + constants.XPATH_PANORAMA + \
            constants.XPATH_VSYS + constants.XPATH_ENTRY.format(vsys) + \
            constants.XPATH_SERVICE_GROUP
        return xpath_head

    def build_virtual_wire_xpath_head(self):
        """
        /config/devices/entry[@name='localhost.localdomain']/network/virtual-wire
        """
        xpath_head = constants.XPATH_CONFIG + constants.XPATH_DEVICES + \
            constants.XPATH_ENTRY.format(constants.XPATH_ENTRY_LOCALHOST_LOCALDOMAIN) \
            + constants.XPATH_NETWORK + constants.XPATH_VIRTUAL_WIRE
        return xpath_head

    def build_virtual_router_xpath_head(self):
        """
        /config/devices/entry[@name='localhost.localdomain']/network/virtual-router
        """
        xpath_head = constants.XPATH_CONFIG + constants.XPATH_DEVICES + \
            constants.XPATH_ENTRY.format(constants.XPATH_ENTRY_LOCALHOST_LOCALDOMAIN) \
            + constants.XPATH_NETWORK + constants.XPATH_VIRTUAL_ROUTER
        return xpath_head

    def build_panorama_security_policy_xpath_head(
            self,
            vsys=constants.VSYS_DEFAULT,
            policy_order=constants.XPATH_PRE_RULEBASE):
        """
        Build xpath head of Panorama managed security policy on firewall.
        Example: xpath=/config/panorama/vsys/entry[@name='vsys1']/pre-rulebase/security/rules
        """
        xpath_head = constants.XPATH_CONFIG + constants.XPATH_PANORAMA + \
            constants.XPATH_VSYS + constants.XPATH_ENTRY.format(vsys) + policy_order + \
            constants.XPATH_SECURITY + constants.XPATH_RULES
        return xpath_head

    def build_local_security_policy_xpath_head(
            self,
            vsys=constants.VSYS_DEFAULT,
            policy_order=constants.XPATH_RULEBASE):
        """
        Build xpath head of local security policy on firewall. Example:
        xpath=/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/rulebase/security/rules
        """
        xpath_head = constants.XPATH_CONFIG + constants.XPATH_DEVICES + \
            constants.XPATH_ENTRY.format(constants.XPATH_ENTRY_LOCALHOST_LOCALDOMAIN) + \
            constants.XPATH_VSYS + constants.XPATH_ENTRY.format(vsys) + policy_order + \
            constants.XPATH_SECURITY + constants.XPATH_RULES
        return xpath_head

    # API METHODS
    # ADDRESS
    def add_shared_address_object(self, xpath_tail):
        """
        Adding new address object using full xpath
        xpath_tail: String attribute of the Address object
        i.e. /entry[@name='H-1.1.1.1']&element=<ip-netmask>1.1.1.1</ip-netmask>
        """
        xpath_head = self.build_shared_address_object_xpath_head()
        xpath = xpath_head + xpath_tail
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to create address object: {0}".format(
                    result.get_error()))

    def add_vsys_address_object(self, xpath_tail, vsys=constants.VSYS_DEFAULT):
        """
        Adding new address object using full xpath
        xpath_tail: String attribute of the Address object
        i.e. /entry[@name='H-1.1.1.1']&element=<ip-netmask>1.1.1.1</ip-netmask>
        """
        xpath_head = self.build_vsys_address_object_xpath_head(vsys)
        xpath = xpath_head + xpath_tail
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to create address object: {0}".format(
                    result.get_error()))

    def show_shared_address_object(self, address_name):
        """
        Get active config by using action=show
        """
        xpath_head = self.build_shared_address_object_xpath_head()
        xpath_entry = constants.XPATH_ENTRY.format(address_name)
        xpath = xpath_head + xpath_entry
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_SHOW, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to show address object: {0}".format(
                    result.get_error()))
        xml_path = constants.TAG_RESULT + constants.FORWARD_SLASH + constants.TAG_ENTRY
        xml_object = self.extract_xml_object_from_response(
            response_text, xml_path)
        return xml_object

    def show_vsys_address_object(
            self,
            address_name,
            vsys=constants.VSYS_DEFAULT):
        xpath_head = self.build_vsys_address_object_xpath_head(vsys)
        xpath_entry = constants.XPATH_ENTRY.format(address_name)
        xpath = xpath_head + xpath_entry
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_SHOW, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to show address object: {0}".format(
                    result.get_error()))
        xml_path = constants.TAG_RESULT + constants.FORWARD_SLASH + constants.TAG_ENTRY
        xml_object = self.extract_xml_object_from_response(
            response_text, xml_path)
        return xml_object

    def get_shared_address_object(self, address_name):
        """
        Get candidate config by using action=get
        """
        xpath_head = self.build_shared_address_object_xpath_head()
        xpath_entry = constants.XPATH_ENTRY.format(address_name)
        xpath = xpath_head + xpath_entry
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_GET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get address object: {0}".format(
                    result.get_error()))
        xml_path = constants.TAG_RESULT + constants.FORWARD_SLASH + constants.TAG_ENTRY
        xml_object = self.extract_xml_object_from_response(
            response_text, xml_path)
        return xml_object

    def get_vsys_address_object(
            self,
            address_name,
            vsys=constants.VSYS_DEFAULT):
        xpath_head = self.build_vsys_address_object_xpath_head(vsys)
        xpath_entry = constants.XPATH_ENTRY.format(address_name)
        xpath = xpath_head + xpath_entry
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_GET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get address object: {0}".format(
                    result.get_error()))
        xml_path = constants.TAG_RESULT + constants.FORWARD_SLASH + constants.TAG_ENTRY
        xml_object = self.extract_xml_object_from_response(
            response_text, xml_path)
        return xml_object

    def get_panorama_address_object(
            self,
            address_name,
            vsys=constants.VSYS_DEFAULT):
        xpath_head = self.build_panorama_address_object_xpath_head(vsys)
        xpath_entry = constants.XPATH_ENTRY.format(address_name)
        xpath = xpath_head + xpath_entry
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_GET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get address object: {0}".format(
                    result.get_error()))
        xml_path = constants.TAG_RESULT + constants.FORWARD_SLASH + constants.TAG_ENTRY
        xml_object = self.extract_xml_object_from_response(
            response_text, xml_path)
        return xml_object

    def add_shared_address_group_object(self, xpath_tail):
        xpath_head = self.build_shared_address_group_object_xpath_head()
        xpath = xpath_head + xpath_tail
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to create address object: {0}".format(
                    result.get_error()))

    def add_vsys_address_group_object(
            self, xpath_tail, vsys=constants.VSYS_DEFAULT):
        xpath_head = self.build_vsys_address_group_object_xpath_head(vsys)
        xpath = xpath_head + xpath_tail
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to create address object: {0}".format(
                    result.get_error()))

    def show_shared_address_group_object(self, address_group_name):
        """
        Get active config by using action=show
        """
        pass

    def show_vsys_address_group_object(
            self,
            address_group_name,
            vsys=constants.VSYS_DEFAULT):
        """
        Get active config by using action=show
        """
        pass

    def get_shared_address_group_object(self, address_group_name):
        """
        Get candidate config by using action=get
        """
        xpath_head = self.build_shared_address_group_object_xpath_head()
        xpath_entry = constants.XPATH_ENTRY.format(address_group_name)
        xpath = xpath_head + xpath_entry
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_GET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get address group object: {0}".format(
                    result.get_error()))
        xml_path = constants.TAG_RESULT + constants.FORWARD_SLASH + constants.TAG_ENTRY
        xml_object = self.extract_xml_object_from_response(
            response_text, xml_path)
        return xml_object

    def get_vsys_address_group_object(
            self,
            address_group_name,
            vsys=constants.VSYS_DEFAULT):
        """
        Get candidate config by using action=get
        """
        pass

    def get_panorama_address_group_object(
            self,
            address_group_name,
            vsys=constants.VSYS_DEFAULT):
        xpath_head = self.build_panorama_address_group_object_xpath_head(vsys)
        xpath_entry = constants.XPATH_ENTRY.format(address_group_name)
        xpath = xpath_head + xpath_entry
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_GET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get address group object: {0}".format(
                    result.get_error()))
        xml_path = constants.TAG_RESULT + constants.FORWARD_SLASH + constants.TAG_ENTRY
        xml_object = self.extract_xml_object_from_response(
            response_text, xml_path)
        return xml_object

    def get_panorama_service_group_object(
            self,
            service_group_name,
            vsys=constants.VSYS_DEFAULT):
        xpath_head = self.build_panorama_service_group_object_xpath_head(vsys)
        xpath_entry = constants.XPATH_ENTRY.format(service_group_name)
        xpath = xpath_head + xpath_entry
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_GET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get service group object: {0}".format(
                    result.get_error()))
        xml_path = constants.TAG_RESULT + constants.FORWARD_SLASH + constants.TAG_ENTRY
        xml_object = self.extract_xml_object_from_response(
            response_text, xml_path)
        return xml_object

    def show_panorama_service_group_object(
            self, service_group_name, vsys=constants.VSYS_DEFAULT):
        pass

    def get_shared_service_group_object(self, service_group_name):
        """
        Get candidate config by using action=get
        """
        xpath_head = self.build_shared_service_group_object_xpath_head()
        xpath_entry = constants.XPATH_ENTRY.format(service_group_name)
        xpath = xpath_head + xpath_entry
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_GET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get service group object: {0}".format(
                    result.get_error()))
        xml_path = constants.TAG_RESULT + constants.FORWARD_SLASH + constants.TAG_ENTRY
        xml_object = self.extract_xml_object_from_response(
            response_text, xml_path)
        return xml_object

    def show_shared_service_group_object(self, service_group_name):
        pass

    def get_vsys_service_group_object(
            self,
            service_group_name,
            vsys=constants.VSYS_DEFAULT):
        """
        Get candidate config by using action=get
        """
        pass

    def show_vsys_service_group_object(
            self,
            service_group_name,
            vsys=constants.VSYS_DEFAULT):
        pass

    # ADDRESS UPDATE
    def add_address_to_shared_static_group(
            self, element_address_xpath, address_group_name):
        """
        address_group_name: Attribute of AddressGroup object
        element_address_xpath: xpath built in a method of AddressGroup object,
        i.e element=<static><member>H-1.1.1.1</member></static>
        """
        xpath_head = self.build_shared_address_group_object_xpath_head()
        xpath_entry = constants.XPATH_ENTRY.format(address_group_name)
        xpath_tail = element_address_xpath
        xpath = xpath_head + xpath_entry + xpath_tail
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to create add address to address group object: {0}".format(
                    result.get_error()))

    def add_address_to_vsys_static_group(
            self,
            element_address_xpath,
            address_group_name,
            vsys=constants.VSYS_DEFAULT):
        """
        address_group_name: Attribute of AddressGroup object
        element_address_xpath: xpath built in a method of AddressGroup object,
        i.e element=<static><member>H-1.1.1.1</member></static>
        """
        xpath_head = self.build_vsys_address_group_object_xpath_head(vsys)
        xpath_entry = constants.XPATH_ENTRY.format(address_group_name)
        xpath_tail = element_address_xpath
        xpath = xpath_head + xpath_entry + xpath_tail
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to create add address to address group object: {0}".format(
                    result.get_error()))

    def remove_address_from_shared_static_group(
            self, xpath_tail, address_group_name):
        """
        =/config/shared/address-group/entry[@name='group_name']/static/member[text()='H-1.1.1.1']
        """
        xpath_head = self.build_shared_address_group_object_xpath_head()
        xpath_entry = constants.XPATH_ENTRY.format(address_group_name)
        xpath = xpath_head + xpath_entry + xpath_tail
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_DELETE, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to remove address to address group object: {0}".format(
                    result.get_error()))

    def remove_address_from_vsys_static_group(
            self, xpath_tail, address_group_name, vsys):
        xpath_head = self.build_vsys_address_group_object_xpath_head(vsys)
        xpath_entry = constants.XPATH_ENTRY.format(address_group_name)
        xpath = xpath_head + xpath_entry + xpath_tail
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_DELETE, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to remove address to addres group object: {0}".format(
                    result.get_error()))

    def set_shared_address_group_description(
            self, xpath_tail, address_group_name):
        """
        =/config/shared/address-group/entry[@name='group_name']/static/member[text()='H-1.1.1.1']
        """
        xpath_head = self.build_shared_address_group_object_xpath_head()
        xpath_entry = constants.XPATH_ENTRY.format(address_group_name)
        xpath = xpath_head + xpath_entry + xpath_tail

        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to set address group description: {0}".format(
                    result.get_error()))

    def set_vsys_address_group_description(
            self, xpath_tail, address_group_name, vsys):
        xpath_head = self.build_vsys_address_group_object_xpath_head(vsys)
        xpath_entry = constants.XPATH_ENTRY.format(address_group_name)
        xpath = xpath_head + xpath_entry + xpath_tail

        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to set address group description: {0}".format(
                    result.get_error()))

    def set_vsys_address_object_description(
            self, xpath_tail, address_name, vsys):
        xpath_head = self.build_vsys_address_object_xpath_head(vsys)
        xpath_entry = constants.XPATH_ENTRY.format(address_name)
        xpath = xpath_head + xpath_entry + xpath_tail

        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to set address group description: {0}".format(
                    result.get_error()))

    # SERVICE
    def get_shared_service_object(self, service_name):
        """
        Get candidate config by using action=get
        """
        xpath_head = self.build_shared_service_object_xpath_head()
        xpath_entry = constants.XPATH_ENTRY.format(service_name)
        xpath = xpath_head + xpath_entry
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_GET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get service object: {0}".format(
                    result.get_error()))
        xml_path = constants.TAG_RESULT + constants.FORWARD_SLASH + constants.TAG_ENTRY
        xml_object = self.extract_xml_object_from_response(
            response_text, xml_path)
        return xml_object

    def get_vsys_service_object(
            self,
            service_name,
            vsys=constants.VSYS_DEFAULT):
        xpath_head = self.build_vsys_service_object_xpath_head(vsys)
        xpath_entry = constants.XPATH_ENTRY.format(service_name)
        xpath = xpath_head + xpath_entry
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_GET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get service object: {0}".format(
                    result.get_error()))
        xml_path = constants.TAG_RESULT + constants.FORWARD_SLASH + constants.TAG_ENTRY
        xml_object = self.extract_xml_object_from_response(
            response_text, xml_path)
        return xml_object

    def get_panorama_service_object(
            self,
            service_name,
            vsys=constants.VSYS_DEFAULT):
        xpath_head = self.build_panorama_service_object_xpath_head(vsys)
        xpath_entry = constants.XPATH_ENTRY.format(service_name)
        xpath = xpath_head + xpath_entry
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_GET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get service object: {0}".format(
                    result.get_error()))
        xml_path = constants.TAG_RESULT + constants.FORWARD_SLASH + constants.TAG_ENTRY
        xml_object = self.extract_xml_object_from_response(
            response_text, xml_path)
        return xml_object

    # SERVICE UDPATE
    def add_shared_service_object(self, xpath_tail):
        """
        Adding new service object using full xpath
        xpath_tail: String attribute of the Service object
        i.e. /entry[@name='tcp-10231-10236']&element=<protocol><tcp><port>10231-10236</port></tcp></protocol>
        """
        xpath_head = self.build_shared_service_object_xpath_head()
        xpath = xpath_head + xpath_tail
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to create service object: {0}".format(
                    result.get_error()))

    def add_vsys_service_object(self, xpath_tail, vsys=constants.VSYS_DEFAULT):
        """
        Adding new service object using full xpath
        xpath_tail: String attribute of the Service object
        i.e. /entry[@name='tcp-10231-10236']&element=<protocol><tcp><port>10231-10236</port></tcp></protocol>
        """
        xpath_head = self.build_vsys_service_object_xpath_head(vsys)
        xpath = xpath_head + xpath_tail
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to create service object: {0}".format(
                    result.get_error()))

    def add_shared_service_group_object(self, xpath_tail):
        xpath_head = self.build_shared_service_group_object_xpath_head()
        xpath = xpath_head + xpath_tail
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to create service group object: {0}".format(
                    result.get_error()))

    def add_vsys_service_group_object(
            self, xpath_tail, vsys=constants.VSYS_DEFAULT):
        xpath_head = self.build_vsys_service_group_object_xpath_head(vsys)
        xpath = xpath_head + xpath_tail
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to create service group object: {0}".format(
                    result.get_error()))

    def add_member_to_shared_service_group(
            self, element_xpath, service_group_name):
        """
        service_group_name: Attribute of ServiceGroup object
        element_xpath: xpath built in a method of ServiceGroup object,
        i.e element=<static><member>H-1.1.1.1</member></static>
        """
        xpath_head = self.build_shared_service_group_object_xpath_head()
        xpath_entry = constants.XPATH_ENTRY.format(service_group_name)
        xpath_tail = element_xpath
        xpath = xpath_head + xpath_entry + xpath_tail
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to add member to service group object: {0}".format(
                    result.get_error()))

    def add_member_to_vsys_service_group(
            self,
            element_xpath,
            service_group_name,
            vsys=constants.VSYS_DEFAULT):
        """
        service_group_name: Attribute of ServiceGroup object
        element_xpath: xpath built in a method of ServiceGroup object,
        i.e element=<member>H-1.1.1.1</member>
        """
        xpath_head = self.build_vsys_address_group_object_xpath_head(vsys)
        xpath_entry = constants.XPATH_ENTRY.format(service_group_name)
        xpath_tail = element_xpath
        xpath = xpath_head + xpath_entry + xpath_tail
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to add member to service group object: {0}".format(
                    result.get_error()))

    def remove_service_from_shared_service_group(
            self, xpath_tail, service_group_name):
        """
        =/config/shared/service-group/entry[@name='http-https']/members/member[text()='H-1.1.1.1']
        """
        xpath_head = self.build_shared_service_group_object_xpath_head()
        xpath_entry = constants.XPATH_ENTRY.format(service_group_name)
        xpath = xpath_head + xpath_entry + xpath_tail
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_DELETE, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to delete service from service group object: {0}".format(
                    result.get_error()))

    def remove_service_from_vsys_service_group(
            self, xpath_tail, service_group_name, vsys):
        xpath_head = self.build_vsys_service_group_object_xpath_head(vsys)
        xpath_entry = constants.XPATH_ENTRY.format(service_group_name)
        xpath = xpath_head + xpath_entry + xpath_tail
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_DELETE, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to delete service from service group object: {0}".format(
                    result.get_error()))

    # API METHODS - POLICIES
    def get_panorama_security_policies(
            self,
            vsys=constants.VSYS_DEFAULT,
            policy_order=constants.XPATH_PRE_RULEBASE):
        # =/config/panorama/vsys/entry[@name='vsys1']/pre-rulebase/security/rules
        xpath_head = self.build_panorama_security_policy_xpath_head(
            vsys, policy_order)
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_GET, xpath=xpath_head)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get Panorama managed security policy: {0}".format(
                    result.get_error()))
        xml_path = constants.TAG_RESULT + constants.FORWARD_SLASH + \
            constants.TAG_RULES
        xml_object = self.extract_xml_object_from_response(
            response_text, xml_path)
        return xml_object

    def get_panorama_security_policy_names(
            self,
            vsys=constants.VSYS_DEFAULT,
            policy_order=constants.XPATH_PRE_RULEBASE):
        # =/config/panorama/vsys/entry[@name='vsys1']/pre-rulebase/security/rules/entry/@name
        xpath_head = self.build_panorama_security_policy_xpath_head(
            vsys, policy_order)
        xpath_entry_name_attr = constants.XPATH_ENTRY_NAME_ALL
        xpath = xpath_head + xpath_entry_name_attr

        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_GET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get shared security policy: {0}".format(
                    result.get_error()))

        # xml_path = '.' <=> find('.') to keep the whole response_text
        xml_path = constants.XML_ROOT
        xml_object = self.extract_xml_object_from_response(
            response_text, xml_path)
        return xml_object

    def get_local_security_policies(self, vsys=constants.VSYS_DEFAULT,
                                    policy_order=constants.XPATH_RULEBASE):
        xpath_head = self.build_local_security_policy_xpath_head(
            vsys, policy_order)
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_GET, xpath=xpath_head)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get local firewall security policy: {0}".format(
                    result.get_error()))
        xml_path = constants.TAG_RESULT + constants.FORWARD_SLASH + constants.TAG_RULES
        xml_object = self.extract_xml_object_from_response(
            response_text, xml_path)
        return xml_object

    def get_local_security_policy_names(self, vsys=constants.VSYS_DEFAULT,
                                        policy_order=constants.XPATH_RULEBASE):
        xpath_head = self.build_local_security_policy_xpath_head(
            vsys, policy_order)
        xpath_entry_name_attr = constants.XPATH_ENTRY_NAME_ALL
        xpath = xpath_head + xpath_entry_name_attr

        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_GET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get shared security policy: {0}".format(
                    result.get_error()))

        # xml_path = '.' <=> find('.') to keep the whole response_text
        xml_path = constants.XML_ROOT
        xml_object = self.extract_xml_object_from_response(
            response_text, xml_path)
        return xml_object

    def add_local_security_policy(
            self,
            xpath_tail,
            vsys=constants.VSYS_DEFAULT,
            policy_order=constants.XPATH_RULEBASE):
        xpath_head = self.build_local_security_policy_xpath_head(
            vsys, policy_order)
        xpath = xpath_head + xpath_tail
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to create local firewall security policy: {0}".format(
                    result.get_error()))

    # NETWORK
    def get_firewall_virtual_wire(self, vwire_name):
        """
        - Input: vwire_name - virtual wire name as string
        - Output: ET xml object of string:
        <entry name="vwire1">
                <interface1>ethernet1/13</interface1>
                <interface2>ethernet1/15</interface2>
        </entry>
        """
        xpath_head = self.build_virtual_wire_xpath_head()
        xpath_entry = constants.XPATH_ENTRY.format(vwire_name)
        xpath = xpath_head + xpath_entry
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_GET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get firewall virtual wire: {0}".format(
                    result.get_error()))
        xml_path = constants.TAG_RESULT + constants.FORWARD_SLASH + constants.TAG_ENTRY
        xml_object = self.extract_xml_object_from_response(
            response_text, xml_path)
        return xml_object

    def show_firewall_virtual_wire(self, vwire_name):
        pass

    def get_firewall_virtual_wires(self):
        """
        Get a tuple of (Boolean, list of virtual wires).
        Boolean is True if self.__host is v-wire.
        Boolean is False otherwise and list is empty.
        """
        xpath_head = self.build_virtual_wire_xpath_head()
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_GET, xpath=xpath_head)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get firewall virtual wires: {0}".format(
                    result.get_error()))
        # Get a list of virtual wires if self.__host is a v-wire firewall.
        root = result.root
        virtual_wires = []
        virtual_wires = [
            x.get('name') for x in root.findall(
                constants.RESPONSE_XPATH_VIRTUAL_WIRE_ENTRY)]
        if len(virtual_wires) > 0:
            return [True, virtual_wires]
        else:
            return [False, virtual_wires]

    def test_security_policy(
            self,
            src,
            dst,
            dport,
            prot='6',
            szone=None,
            dzone=None,
            app='bonpoo',
            showall='yes',
            vwire=False):
        """
        Run test security-policy-match command to check firewall permission on firewall self.__host.
        Return a list of dictionaries of 'Policy Name':<value>, 'Order Number':<value>, 'Policy Content':{dict}
        """
        cmd = ''
        # If service is any, use reserved protocol number 255 in test security
        if dport == 'any':
            prot = constants.RESERVED_PROTOCOL_NUMBER
        if vwire:
            if dport == 'any':
                cmd = constants.CMD_TEST_SECURITY_POLICY_VWIRE_SERVICE_ANY.format(
                    src, dst, prot, app, showall)
            else:
                cmd = constants.CMD_TEST_SECURITY_POLICY_VWIRE.format(
                    src, dst, dport, prot, app, showall)
        else:
            if szone is None:
                szone = self.get_firewall_zone(src)
            if dzone is None:
                dzone = self.get_firewall_zone(dst)
            # If service is not any
            if dport != 'any':
                cmd = constants.CMD_TEST_SECURITY_POLICY_LAYER3.format(
                    src, dst, dport, prot, szone, dzone, app, showall)
            # If service is any, use reserved protocol number 255 in test
            # security
            else:
                #prot = constants.RESERVED_PROTOCOL_NUMBER
                cmd = constants.CMD_TEST_SECURITY_POLICY_LAYER3_SERVICE_ANY.format(
                    src, dst, prot, szone, dzone, showall)
        response_text = self.op_command(cmd)
        logger.debug(
            'test_security_policy response_text: {0}'.format(response_text))
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to test security policy: {0}".format(
                    result.get_error()))

        security_policy_list = []
        # Process the test security policy responses
        """
        - PAN-OS 7.1.8 & PA-5020:
        The response is <result><rules><entry>2294</entry></rules><rules><entry>...</entry></rules></result>
        - PAN-OS 7.1.21:
        The response is <result><rules><entry name='171'><from>...</from><to>...</to></entry></rules></result>
        - PAN-OS 8.0.6-h3 & PA-5220:
        The response is <result><rules><entry>3; index: 7</entry></rules><rules><entry>...</entry></rules></result>
        - PAN-OS 8.0.10 & PA-5250:
        <result><rules><entry name="5"><index>27</index><from>any</from><source>any</source>
        """
        security_policy_list = []
        #dict_key_list = ['Policy Name', 'Order Number', 'Policy Content']
        root = result.root
        # Only in PAN-OS 8.0.10 & PA-5250, entry tag has attribute 'name',
        # otherwise attrib is empty dict {}
        if not root.find(constants.RESPONSE_XPATH_RULES_ENTRY).attrib:
            # PAN-OS 7.1.8 & PA-5020
            if 'index' not in root.find(
                    constants.RESPONSE_XPATH_RULES_ENTRY).text:
                policy_names = [
                    x.text for x in root.findall(
                        constants.RESPONSE_XPATH_RULES_ENTRY)]
                order_numbers = ['N/A'] * len(policy_names)
                #policy_content = [{}]*len(policy_names)
            else:  # PAN-OS 8.0.6-h3 & PA-5220
                policy_names = [
                    x.text.split('; ')[0] for x in root.findall(
                        constants.RESPONSE_XPATH_RULES_ENTRY)]
                order_numbers = [
                    x.text.split('; ')[1].split(': ')[1] for x in root.findall(
                        constants.RESPONSE_XPATH_RULES_ENTRY)]
                #policy_content = [{}]*len(policy_names)
        # For PAN-OS 7.1.21 case
        elif 'index' not in response_text:
            policy_names = [x.attrib[constants.TAG_ATTRIBUTE_NAME]
                            for x in root.findall(constants.RESPONSE_XPATH_RULES_ENTRY)]
            order_numbers = ['N/A'] * len(policy_names)
        else:  # PAN-OS 8.0.10 & PA-5250
            policy_names = [x.attrib[constants.TAG_ATTRIBUTE_NAME]
                            for x in root.findall(constants.RESPONSE_XPATH_RULES_ENTRY)]
            order_numbers = [
                x.text for x in root.findall(
                    constants.RESPONSE_XPATH_RULES_ENTRY_INDEX)]
        # for i in range(len(policy_names)):
        for idx, policyname in enumerate(policy_names):
            policy_dict = {}
            #policy_dict['Policy Name'] = policy_names[i]
            policy_dict['Policy Name'] = policyname
            #policy_dict['Order Number'] = order_numbers[i]
            policy_dict['Order Number'] = order_numbers[idx]
            policy_xml_object = self.get_panorama_security_policy(
                policyname, policy_order=constants.XPATH_PRE_RULEBASE)
            if policy_xml_object is None:
                policy_xml_object = self.get_panorama_security_policy(
                    policyname, policy_order=constants.XPATH_POST_RULEBASE)
                if policy_xml_object is None:
                    policy_xml_object = self.get_local_security_policy(
                        policyname)
            policy_dict['Policy Content'] = {}
            policy_dict['Policy Content'] = self.get_security_policy_content(
                policy_xml_object)
            security_policy_list.append(policy_dict)
        return security_policy_list

    def check_flow_permission(self, src, dst, dport, prot='6',
                              app='bonpoo', showall='yes'):
        """
        Method to check if firewall permission is there for a particular flow.
        Return True if it is there. Otherwise return False.
        """
        is_vwire, vwires = self.get_firewall_virtual_wires()  # pylint: disable=unused-variable
        if is_vwire:
            security_policy_list = self.test_security_policy(
                src, dst, dport, prot, app=app, showall=showall, vwire=is_vwire)
        else:
            szone = self.get_firewall_zone(src)
            dzone = self.get_firewall_zone(dst)
            security_policy_list = self.test_security_policy(
                src, dst, dport, prot, szone, dzone, app)
        ruleno = 0
        #final_verdict = 'DENY'
        for security_policy_dict in security_policy_list:
            ruleno += 1
            if (security_policy_dict['Policy Content']
                    ['Action'].upper() == 'ALLOW') and (ruleno == 1):
                #final_verdict = 'ALLOW'
                return True
        return False

    def get_panorama_security_policy(
            self,
            policy_name,
            vsys=constants.VSYS_DEFAULT,
            policy_order=constants.PRE_RULEBASE):
        """
        Return xml object of the Panorama security policy policy_name
        Return None if no policy_name is found
        """
        xpath_head = self.build_panorama_security_policy_xpath_head(
            vsys, policy_order)
        xpath_entry = constants.XPATH_ENTRY.format(policy_name)
        xpath = xpath_head + xpath_entry
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_GET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get security policy: {0}".format(
                    result.get_error()))
        root = result.root
        """
        If policy is not found => response: '<response status="success" code="7">\n<result/>\n</response>'
        """
        if not root.find(constants.TAG_RESULT).attrib:
            return None
        else:
            xml_path = constants.TAG_RESULT + constants.FORWARD_SLASH + \
                constants.TAG_ENTRY
            xml_object = self.extract_xml_object_from_response(
                response_text, xml_path)
            return xml_object

    def get_local_security_policy(
            self,
            policy_name,
            vsys=constants.VSYS_DEFAULT,
            policy_order=constants.XPATH_RULEBASE):
        """
        Return xml object of the local security policy policy_name
        """
        xpath_head = self.build_local_security_policy_xpath_head(
            vsys, policy_order)
        xpath_entry = constants.XPATH_ENTRY.format(policy_name)
        xpath = xpath_head + xpath_entry
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_GET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get security policy: {0}".format(
                    result.get_error()))
        root = result.root
        """
        If policy is not found => response: '<response status="success" code="7">\n<result/>\n</response>'
        """
        if not root.find(constants.TAG_RESULT).attrib:
            return None
        else:
            xml_path = constants.TAG_RESULT + constants.FORWARD_SLASH + \
                constants.TAG_ENTRY
            xml_object = self.extract_xml_object_from_response(
                response_text, xml_path)
            return xml_object

    @staticmethod
    def get_security_policy_content(xmlobject):
        """
        - Input: xmlobject of security policy <entry name="rule_name">...</entry>
        - Output: A dictionary of {'source':<value>, 'destination':<value>}
        """
        szone = [
            x.text if x is not None else None for x in xmlobject.findall(
                constants.RESPONSE_XPATH_FROM_MEMBER)]
        source = [
            x.text if x is not None else None for x in xmlobject.findall(
                constants.RESPONSE_XPATH_SOURCE_MEMBER)]
        nsource = [
            x.text if x is not None else None for x in xmlobject.findall(
                constants.RESPONSE_XPATH_NEGATE_SOURCE_MEMBER)]
        suser = [x.text if x is not None else None for x in xmlobject.findall(
            constants.RESPONSE_XPATH_SOURCE_USER_MEMBER)]
        hip = [x.text if x is not None else None for x in xmlobject.findall(
            constants.RESPONSE_XPATH_HIP_PROFILES_MEMBER)]

        dzone = [
            x.text if x is not None else None for x in xmlobject.findall(
                constants.RESPONSE_XPATH_TO_MEMBER)]
        destination = [
            x.text if x is not None else None for x in xmlobject.findall(
                constants.RESPONSE_XPATH_DESTINATION_MEMBER)]
        ndestination = [
            x.text if x is not None else None for x in xmlobject.findall(
                constants.RESPONSE_XPATH_NEGATE_DESTINATION_MEMBER)]

        application = [
            x.text if x is not None else None for x in xmlobject.findall(
                constants.RESPONSE_XPATH_APPLICATION_MEMBER)]
        service = [
            x.text if x is not None else None for x in xmlobject.findall(
                constants.RESPONSE_XPATH_SERVICE_MEMBER)]
        category = [
            x.text if x is not None else None for x in xmlobject.findall(
                constants.RESPONSE_XPATH_CATEGORY_MEMBER)]
        action = xmlobject.find(constants.RESPONSE_XPATH_ACTION).text
        if xmlobject.find(constants.RESPONSE_XPATH_DISABLED) is not None:
            disabled = xmlobject.find(constants.RESPONSE_XPATH_DISABLED).text
        else:
            disabled = None

        sp_group = [x.text if x is not None else None for x in xmlobject.findall(
            constants.RESPONSE_XPATH_SECURITY_PROFILE_GROUP_MEMBER)]
        # If profile setting consist of invidiual profiles
        sp_virus = [x.text if x is not None else None for x in xmlobject.findall(
            constants.RESPONSE_XPATH_SECURITY_PROFILE_VIRUS_MEMBER)]
        sp_fb = [x.text if x is not None else None for x in xmlobject.findall(
            constants.RESPONSE_XPATH_SECURITY_PROFILE_FILEBLOCKING_MEMBER)]
        sp_spyware = [x.text if x is not None else None for x in xmlobject.findall(
            constants.RESPONSE_XPATH_SECURITY_PROFILE_SPYWARE_MEMBER)]
        sp_wfa = [x.text if x is not None else None for x in xmlobject.findall(
            constants.RESPONSE_XPATH_SECURITY_PROFILE_WILDFIRE_MEMBER)]
        sp_url = [x.text if x is not None else None for x in xmlobject.findall(
            constants.RESPONSE_XPATH_SECURITY_PROFILE_URL_MEMBER)]

        # Options
        if xmlobject.find(constants.RESPONSE_XPATH_OPTION_DSRI) is not None:
            dsri = xmlobject.find(constants.RESPONSE_XPATH_OPTION_DSRI).text
        else:
            dsri = None

        if xmlobject.find(
                constants.RESPONSE_XPATH_OPTION_LOGSTART) is not None:
            logstart = xmlobject.find(
                constants.RESPONSE_XPATH_OPTION_LOGSTART).text
        else:
            logstart = None

        if xmlobject.find(constants.RESPONSE_XPATH_OPTION_LOGEND) is not None:
            logend = xmlobject.find(
                constants.RESPONSE_XPATH_OPTION_LOGEND).text
        else:
            logend = None
        if xmlobject.find(
                constants.RESPONSE_XPATH_OPTION_LOG_SETTING) is not None:
            logsetting = xmlobject.find(
                constants.RESPONSE_XPATH_OPTION_LOG_SETTING).text
        else:
            logsetting = None
        if xmlobject.find(constants.RESPONSE_XPATH_DESCRIPTION) is not None:
            description = xmlobject.find(
                constants.RESPONSE_XPATH_DESCRIPTION).text
        else:
            description = None
        tag = [
            x.text if x is not None else None for x in xmlobject.findall(
                constants.RESPONSE_XPATH_TAG_MEMBER)]

        policy_content = {}
        policy_content['Source Zone'] = szone
        policy_content['Source'] = source
        policy_content['Negate Source'] = nsource
        policy_content['Source User'] = suser
        policy_content['Host Info'] = hip
        policy_content['Destination Zone'] = dzone
        policy_content['Destination'] = destination
        policy_content['Negate Destination'] = ndestination
        policy_content['Application'] = application
        policy_content['Service'] = service
        policy_content['Category'] = category
        policy_content['Action'] = action
        policy_content['Disabled'] = disabled
        policy_content['Security Profile Group'] = sp_group
        policy_content['Virus Profile'] = sp_virus
        policy_content['File Blocking Profile'] = sp_fb
        policy_content['Spyware Profile'] = sp_spyware
        policy_content['Wildfire Profile'] = sp_wfa
        policy_content['URL Profile'] = sp_url
        policy_content['Disable Server Response Inspection'] = dsri
        policy_content['Log Start'] = logstart
        policy_content['Log End'] = logend
        policy_content['Log Setting'] = logsetting
        policy_content['Description'] = description
        policy_content['Tag'] = tag

        return policy_content

    def get_all_firewall_zones(self):
        """
        Get a list of all zones configured on firewall self.__host
        """
        cmd = constants.CMD_SHOW_INTERFACE_LOGICAL
        response_text = self.op_command(cmd)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get firewall zone: {0}".format(
                    result.get_error()))

        root = ET.fromstring(response_text)
        zones = [x.text for x in root.findall(
            constants.RESPONSE_XPATH_ZONE_NAME)]
        return zones

    def get_firewall_zone(self, ip):
        """
        Get forwarding firewall zone for specified interface on
        firewall self.__host based on provided ip.
        """
        zone = ''
        zones = self.get_all_firewall_zones()

        is_vwire, vwires = self.get_firewall_virtual_wires()  # pylint: disable=unused-variable
        if is_vwire:
            # SSH TO MANAGEMENT SERVER mgmthost
            #print("Connecting to management server {0} via SSH...\n".format(mgmthost))
            mgmthost = common_constants.MGMT_HOST

            sshsess = sshsession.SSHSession(
                mgmthost, keypath=common_constants.SSH_PRIVATE_KEY_PATH_PROD)
            sshsess.connect_ssh_key()
            #print("Management SSH connection established!\n")
            sshsess.read_output_buffer()

            # print("Doing traceroute from {0} to source {1}...\n".\
            # format(mgmthost, source))
            iptrace = sshsess.do_traceroute(ip)

            #print('Initializing source traceroute object...\n')
            iproute = traceroute.FirewallIPTraceRoute(
                mgmthost, 'LINUX', ip, iptrace)
            # print("Ordered list of firewalls and unresolved IPs from {0} to SOURCE {1}:\
            # \n{2}\n".format(mgmthost, source, srcroute.fwip_list))

            if iproute.is_target_in_gwan_remote_sites():
                lzone = [z for z in constants.MAIN_DC_VWIRE_GWAN_ZONES
                         if z in zones]
            else:
                lzone = [z for z in constants.MAIN_DC_VWIRE_CORE_ZONES
                         if z in zones]
            zone = lzone[0]
        else:
            interface = self.get_firewall_forwarding_interface(ip)
            cmd = constants.CMD_SHOW_INTERFACE_LOGICAL
            response_text = self.op_command(cmd)
            result = responses.Response(response_text)
            if not result.ok():
                raise BadResponseError(
                    "Failed to get firewall zone: {0}".format(
                        result.get_error()))

            root = ET.fromstring(response_text)

            interfaces = [
                x.text for x in root.findall(
                    constants.RESPONSE_XPATH_INTERFACE_NAME)]
            index = interfaces.index(interface)
            zone = zones[index]

        return zone

    def get_firewall_forwarding_interface(self, ip):
        """
        Get forwarding interface for specified IP on firewall self.__host.
        """
        vr = self.get_firewall_virtual_router()

        cmd = constants.CMD_TEST_ROUTING.format(ip, vr)
        response_text = self.op_command(cmd)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get firewall forwarding interface: {0}".format(
                    result.get_error()))

        root = ET.fromstring(response_text)
        return root.find(constants.RESPONSE_XPATH_RESULT_INTERFACE).text

    def get_firewall_virtual_router(self):
        """
        Get virtual router on single vsys firewall.
        Return None if firewall is v-wire
        """
        xpath_head = self.build_virtual_router_xpath_head()
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_GET, xpath=xpath_head)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get firewall virtual router: {0}".format(
                    result.get_error()))
        """
        If there are more than one VR, stop automation. Manual actions are require.
        Automation only support one VR per firewall
        """
        root = ET.fromstring(response_text)
        virtual_routers = [
            x.get(
                constants.TAG_ATTRIBUTE_NAME) for x in root.findall(
                constants.RESPONSE_XPATH_VIRTUAL_ROUTER_ENTRY)]
        if len(virtual_routers) > 1:
            sys.exit("More than one VRs not supported by automation!")
        elif len(virtual_routers) == 1:
            return virtual_routers[0]
        else:
            return None

    def get_forwarding_interface_address(self, target):
        """
        - Input:
         + target: The IP address used to locate the fw interface
        - Output: Return the forwarding interface ID if fw is layer 3
        elif fw is vwire, return None
        """
        vr = self.get_firewall_virtual_router()

        cmd = constants.CMD_TEST_ROUTING.format(target, vr)
        response_text = self.op_command(cmd)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get firewall forwarding interface: {0}".format(
                    result.get_error()))

        root = ET.fromstring(response_text)
        if root.find(constants.RESPONSE_XPATH_RESULT_SOURCE) is None:
            return None
        return root.find(constants.RESPONSE_XPATH_RESULT_SOURCE).text

    def get_firewall_interface_addresses(self):
        cmd = constants.CMD_SHOW_INTERFACE_LOGICAL
        response_text = self.op_command(cmd)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to show logical interface: {0}".format(
                    result.get_error()))

        root = ET.fromstring(response_text)

        return [x.text for x in root.findall(
            constants.RESPONSE_XPATH_INTERFACE_IP)]

    # COMMIT
    def commit_partial(
            self,
            description='Firewall-Automation',
            admin='fwauto'):
        """
        Commit any changes.
        Returns jobid
        """
        cmd = constants.CMD_COMMIT_PARTIAL.format(admin, description)
        response_text = self.commit_command(cmd)

        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to perform partial commit: {0}".format(
                    result.get_error()))

        root = ET.fromstring(response_text)
        job_id = root.find(constants.RESPONSE_XPATH_RESULT_JOB).text

        """
        r = self.__make_request(type='commit', cmd='<commit><partial><admin><member>{0}</member></admin></partial>
        <description>{1}</description></commit>'.format(admin, description))
        """
        return job_id

    def get_commit_progress(self, job_id):
        """
        Get commit progress.
        Returns job progress
        """
        cmd = constants.CMD_SHOW_JOBS_ID.format(job_id)
        response_text = self.op_command(cmd)

        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to retrieve commit progress: {0}".format(
                    result.get_error()))

        root = ET.fromstring(response_text)
        job_progress = root.find(
            constants.RESPONSE_XPATH_RESULT_JOB_PROGRESS).text

        return job_progress

    def get_commit_result(self, job_id):
        """
        Get commit result. Returns job result: OK or FAIL
        """
        cmd = constants.CMD_SHOW_JOBS_ID.format(job_id)
        response_text = self.op_command(cmd)

        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get commit result: {0}".format(
                    result.get_error()))

        root = ET.fromstring(response_text)
        job_status = root.find(constants.RESPONSE_XPATH_RESULT_JOB_RESULT).text

        return job_status

    def wait_for_job(self, job_id):
        """
        Wait for a commit job to complete and show the progress.
        Note: Doesn't have a timeout so if the job hangs we will still wait.
        """
        prog = 0
        while prog < 100:
            job_progress = self.get_commit_progress(job_id)
            prog = int(job_progress)
            self.print_progress(prog, 100, 'Commit progress:', 'complete')
            time.sleep(1)
        result_str = self.get_commit_result(job_id)
        print(('Commit finished with result: {0}'.format(result_str)))
        return result_str == 'OK'

    @staticmethod
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

        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        progbar = fill * filledLength + '-' * (length - filledLength)
        sys.stdout.write(
            '\r%s |%s| %s%% %s\r' %
            (prefix, progbar, percent, suffix))
        sys.stdout.flush()
        # Print New Line on Complete
        if iteration == total:
            print('')
