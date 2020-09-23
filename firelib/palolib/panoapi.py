"REPLACED BY panapi.py and commits.py"

import sys
import time
import xml.etree.ElementTree as ET

import requests

from ..common import constants as common_constants
from ..common import firelogging, firepass, util
from . import responses, constants

# START LOGGING TO FILE
logger = firelogging.FireLogger(name=__name__).firelogger
logger.debug('*** Start of panoapi.py ***')


class NotConnectedError(AssertionError):
    pass


class BadResponseError(RuntimeError):
    pass


class BadHTTPResponseError(RuntimeError):
    pass


class PanoramaAPISession:
    "Panorama API session class"

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

    def __init__(self, host=constants.PANORAMA_PROD_HOST_A):
        """
        host is the host address of the Panorama to be connected to.
        """
        self.__host = host
        if host == constants.PANORAMA_DEV_HOST:
            self.__host = host + constants.DEV_HOST_POSTFIX
        elif '.' not in host:
            self.__host = host + constants.PROD_HOST_POSTFIX
        #self.__apikey = None
        self.__apikey = self.__get_palo_api_key()

    @property
    def hostname(self):
        return self.__host

    def get_session_host_role(self):
        """
        Get the role of the session host.
        Return: "panorama" or "firewall"
        """
        return 'panorama'

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
        kwargs is a easy way to set the url parameters. For instance to add a parameter action=set,
        you call the function with __make_request(action='set').
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
    # def commit_command(self, cmd, type=constants.URL_REQUEST_TYPE_COMMIT):
    def commit_command(
            self,
            cmd,
            commit_type=constants.URL_REQUEST_TYPE_COMMIT,
            action=None):
        if action is None:
            r = self.__make_request(type=commit_type, cmd=cmd)
        else:
            r = self.__make_request(type=commit_type, action=action, cmd=cmd)
        response_text = self.__check_response(r)
        return response_text

    def config_command(self, config_type=constants.URL_REQUEST_TYPE_CONFIG,
                       action=constants.URL_REQUEST_ACTION_GET, xpath=None):
        r = self.__make_request(type=config_type, action=action, xpath=xpath)
        response_text = self.__check_response(r)
        return response_text

    # /api/?type=op&cmd=
    def op_command(self, cmd, op_type=constants.URL_REQUEST_TYPE_OP):
        r = self.__make_request(type=op_type, cmd=cmd)
        response_text = self.__check_response(r)
        return response_text

    # HEAD XPATH BUILD

    def build_shared_address_object_xpath_head(self):
        """
        Build xpath=config/shared/address
        """
        xpath_head = constants.XPATH_CONFIG + \
            constants.XPATH_SHARED + constants.XPATH_ADDRESS
        return xpath_head

    def build_device_group_address_object_xpath_head(self, device_group):
        """
        Build xpath=/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='device_group']/address
        """
        xpath_head = constants.XPATH_CONFIG + constants.XPATH_DEVICES + \
            constants.XPATH_ENTRY.format(constants.XPATH_ENTRY_LOCALHOST_LOCALDOMAIN) + \
            constants.XPATH_DEVICE_GROUP + constants.XPATH_ENTRY.format(device_group) + \
            constants.XPATH_ADDRESS
        return xpath_head

    def build_device_group_address_group_object_xpath_head(self, device_group):
        """
        Build xpath=/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='device_group']
        /address-group
        """
        xpath_head = constants.XPATH_CONFIG + constants.XPATH_DEVICES + \
            constants.XPATH_ENTRY.format(constants.XPATH_ENTRY_LOCALHOST_LOCALDOMAIN) + \
            constants.XPATH_DEVICE_GROUP + constants.XPATH_ENTRY.format(device_group) + \
            constants.XPATH_ADDRESS_GROUP
        return xpath_head

    def build_shared_address_group_object_xpath_head(self):
        """
        Build xpath=config/shared/address-group
        """
        xpath_head = constants.XPATH_CONFIG + \
            constants.XPATH_SHARED + constants.XPATH_ADDRESS_GROUP
        return xpath_head

    def build_shared_service_object_xpath_head(self):
        """
        Build xpath=config/shared/service
        """
        xpath_head = constants.XPATH_CONFIG + \
            constants.XPATH_SHARED + constants.XPATH_SERVICE
        return xpath_head

    def build_device_group_service_object_xpath_head(self, device_group):
        """
        Build xpath=/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='device_group']/service
        """
        xpath_head = constants.XPATH_CONFIG + constants.XPATH_DEVICES + \
            constants.XPATH_ENTRY.format(constants.XPATH_ENTRY_LOCALHOST_LOCALDOMAIN) + \
            constants.XPATH_DEVICE_GROUP + constants.XPATH_ENTRY.format(device_group) + \
            constants.XPATH_SERVICE
        return xpath_head

    def build_shared_service_group_object_xpath_head(self):
        """
        Build xpath=config/shared/service-group
        """
        xpath_head = constants.XPATH_CONFIG + \
            constants.XPATH_SHARED + constants.XPATH_SERVICE_GROUP
        return xpath_head

    def build_device_group_service_group_object_xpath_head(self, device_group):
        """
        Build xpath=/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='device_group']
        /service-group
        """
        xpath_head = constants.XPATH_CONFIG + constants.XPATH_DEVICES + \
            constants.XPATH_ENTRY.format(constants.XPATH_ENTRY_LOCALHOST_LOCALDOMAIN) + \
            constants.XPATH_DEVICE_GROUP + constants.XPATH_ENTRY.format(device_group) + \
            constants.XPATH_SERVICE_GROUP
        return xpath_head

    def build_shared_security_policy_xpath_head(
            self,
            policy_order=constants.XPATH_PRE_RULEBASE,
            default_security_policy=False):
        """
        Build xpath=/config/shared/pre-rulebase/security/rules
        or
        /config/shared/post-rulebase/default-security-rules/rules
        """
        if not default_security_policy:
            xpath_head = constants.XPATH_CONFIG + constants.XPATH_SHARED + \
                policy_order + constants.XPATH_SECURITY + \
                constants.XPATH_RULES
        else:
            xpath_head = constants.XPATH_CONFIG + constants.XPATH_SHARED + \
                policy_order + constants.XPATH_DEFAULT_SECURITY_RULES + \
                constants.XPATH_RULES
        return xpath_head

    def build_device_group_security_policy_xpath_head(
            self,
            device_group,
            policy_order=constants.XPATH_PRE_RULEBASE,
            default_security_policy=False):
        """
        Build xpath=/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='device_group']
        /pre-rulebase/security/rules
        or xpath=/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='device_group']
        /post-rulebase/default-security-rules/rules
        """
        if not default_security_policy:
            xpath_head = constants.XPATH_CONFIG + constants.XPATH_DEVICES + \
                constants.XPATH_ENTRY.format(constants.XPATH_ENTRY_LOCALHOST_LOCALDOMAIN) + \
                constants.XPATH_DEVICE_GROUP + constants.XPATH_ENTRY.format(device_group) + \
                policy_order + constants.XPATH_SECURITY + constants.XPATH_RULES
        else:
            xpath_head = constants.XPATH_CONFIG + constants.XPATH_DEVICES + \
                constants.XPATH_ENTRY.format(constants.XPATH_ENTRY_LOCALHOST_LOCALDOMAIN) + \
                constants.XPATH_DEVICE_GROUP + constants.XPATH_ENTRY.format(device_group) + \
                policy_order + constants.XPATH_DEFAULT_SECURITY_RULES + constants.XPATH_RULES
        return xpath_head

    def build_shared_custom_url_category_xpath_head(self):
        """
        Build xpath=/config/shared/profiles/custom-url-category
        """
        xpath_head = constants.XPATH_CONFIG + constants.XPATH_SHARED + \
            constants.XPATH_PROFILES + constants.XPATH_CUSTOM_URL_CATEGORY
        return xpath_head

    def build_device_group_custom_url_category_xpath_head(self, device_group):
        """
        Build xpath=/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='device_group']
        /profiles/custom-url-category
        """
        xpath_head = constants.XPATH_CONFIG + constants.XPATH_DEVICES + constants.XPATH_ENTRY.format(
            constants.XPATH_ENTRY_LOCALHOST_LOCALDOMAIN) + constants.XPATH_DEVICE_GROUP + constants.XPATH_ENTRY.format(device_group) + constants.XPATH_PROFILES + constants.XPATH_CUSTOM_URL_CATEGORY
        return xpath_head

    # API METHODS
    # ADDRESS
    def set_shared_address_object_description(self, xpath_tail, address_name):
        xpath_head = self.build_shared_address_object_xpath_head()
        xpath_entry = constants.XPATH_ENTRY.format(address_name)
        xpath = xpath_head + xpath_entry + xpath_tail

        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to set address group description: {0}".format(
                    result.get_error()))

    def set_device_group_address_object_description(
            self, xpath_tail, address_name, device_group):
        xpath_head = self.build_device_group_address_object_xpath_head(
            device_group)
        xpath_entry = constants.XPATH_ENTRY.format(address_name)
        xpath = xpath_head + xpath_entry + xpath_tail

        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to set address group description: {0}".format(
                    result.get_error()))

    def add_shared_address_object(self, xpath_tail):
        """
        Adding new address object using full xpath
        xpath_tail: String attribute of the Address object
        i.e. /entry[@name='H-1.1.1.1']&element=<ip-netmask>1.1.1.1</ip-netmask>
        """
        xpath_head = self.build_shared_address_object_xpath_head()
        xpath = xpath_head + xpath_tail

        logger.debug('add_shared_address_object - xpath: {0}'.format(xpath))

        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to create address object: {0}".format(
                    result.get_error()))

    def add_device_group_address_object(self, xpath_tail, device_group):
        """
        Adding new address object using full xpath
        xpath_tail: String attribute of the Address object
        i.e. /entry[@name='H-1.1.1.1']&element=<ip-netmask>1.1.1.1</ip-netmask>
        """
        xpath_head = self.build_device_group_address_object_xpath_head(
            device_group)
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

    def show_device_group_address_object(self, address_name, device_group):
        pass

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

    def get_device_group_address_object(self, address_name, device_group):
        pass

    def get_panorama_address_object(self, address_name, device_group):
        """
        Get Panorama managed address on firewall
        """
        pass

    def get_vsys_address_object(self, address_name, device_group):
        """
        Get address on firewall virtual system
        """
        pass

    def add_shared_address_group_object(self, xpath_tail):
        xpath_head = self.build_shared_address_group_object_xpath_head()
        xpath = xpath_head + xpath_tail
        logger.debug(
            'add_shared_address_group_object - xpath: {0}'.format(xpath))
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to create address object: {0}".format(
                    result.get_error()))

    def add_device_group_address_group_object(self, xpath_tail, device_group):
        xpath_head = self.build_device_group_address_group_object_xpath_head(
            device_group)
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

    def show_device_group_address_group_object(
            self, address_group_name, device_group):
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

    def get_device_group_address_group_object(
            self, address_group_name, device_group):
        """
        Get candidate config by using action=get
        """
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
                "Failed to add address to address group object: {0}".format(
                    result.get_error()))

    def add_address_to_device_group_static_group(
            self, element_address_xpath, address_group_name, device_group):
        pass

    def add_address_to_shared_dynamic_group(self):
        pass

    def add_address_to_device_group_dynamic_group(self):
        pass

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
                "Failed to delete address from address group object: {0}".format(
                    result.get_error()))

    def remove_address_from_device_group_static_group(
            self, xpath_tail, address_group_name, device_group):
        """
        =/config/shared/address-group/entry[@name='group_name']/static/member[text()='H-1.1.1.1']
        """
        xpath_head = self.build_device_group_address_group_object_xpath_head(
            device_group)
        xpath_entry = constants.XPATH_ENTRY.format(address_group_name)
        xpath = xpath_head + xpath_entry + xpath_tail

        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_DELETE, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to delete address from address group object: {0}".format(
                    result.get_error()))

    def set_shared_address_group_description(
            self, xpath_tail, address_group_name):
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

    def set_device_group_address_group_description(
            self, xpath_tail, address_group_name, device_group):
        xpath_head = self.build_device_group_address_object_xpath_head(
            device_group)
        xpath_entry = constants.XPATH_ENTRY.format(address_group_name)
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

    def show_shared_service_object(self, service_name):
        pass

    def get_device_group_service_object(self, service_name, device_group):
        pass

    def show_device_group_service_object(self, service_name, device_group):
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

    def get_device_group_service_group_object(
            self, service_group_name, device_group):
        """
        Get candidate config by using action=get
        """
        xpath_head = self.build_device_group_service_group_object_xpath_head(
            device_group)
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

    def show_device_group_service_group_object(
            self, service_group_name, device_group):
        pass

    # SERVICE UPDATE
    def add_shared_service_object(self, xpath_tail):
        """
        Adding new service object using full xpath
        xpath_tail: String attribute of the Service object
        i.e. /entry[@name='tcp-complex-object']&element=<protocol><tcp>
        <port>10959,10960,10961,40959,40960,40961,10977,21271,40977,51271</port></tcp></protocol>
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

    def add_device_group_service_object(self, xpath_tail, device_group):
        """
        Adding new address object using full xpath
        xpath_tail: String attribute of the Address object
        i.e. /entry[@name='H-1.1.1.1']&element=<ip-netmask>1.1.1.1</ip-netmask>
        """
        xpath_head = self.build_device_group_service_object_xpath_head(
            device_group)
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
        logger.debug(
            'add_shared_service_group_object - xpath: {0}'.format(xpath))
        #print('add_shared_service_group_object - xpath: {0}'.format(xpath))
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to create service group object: {0}".format(
                    result.get_error()))

    def add_device_group_service_group_object(self, xpath_tail, device_group):
        xpath_head = self.build_device_group_service_group_object_xpath_head(
            device_group)
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
        i.e element=<member>H-1.1.1.1</member>
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
                "Failed to add service to service group object: {0}".format(
                    result.get_error()))

    def add_member_to_device_group_service_group(
            self, element_xpath, service_group_name, device_group):
        pass

    def remove_member_from_shared_service_group(
            self, xpath_tail, service_group_name):
        """
        =/config/shared/service-group/entry[@name='http-https']/members/member[text()='http']
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

    def remove_member_from_device_group_service_group(
            self, xpath_tail, service_group_name, device_group):
        """
        =/config/shared/service-group/entry[@name='http-https']/members/member[text()='http']
        """
        xpath_head = self.build_device_group_service_group_object_xpath_head(
            device_group)
        xpath_entry = constants.XPATH_ENTRY.format(service_group_name)
        xpath = xpath_head + xpath_entry + xpath_tail

        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_DELETE, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to delete service from service group object: {0}".format(
                    result.get_error()))

    # API METHODS - CUSTOM URL CATEGORIES
    def get_shared_custom_url_category_object(self, url_cat_name):
        """
        Get candidate config by using action=get
        """
        xpath_head = self.build_shared_custom_url_category_xpath_head()
        xpath_entry = constants.XPATH_ENTRY.format(url_cat_name)
        xpath = xpath_head + xpath_entry
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_GET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get URl category object: {0}".format(
                    result.get_error()))
        xml_path = constants.TAG_RESULT + constants.FORWARD_SLASH + constants.TAG_ENTRY
        xml_object = self.extract_xml_object_from_response(
            response_text, xml_path)
        return xml_object

    def show_shared_custom_url_category_object(self, url_cat_name):
        pass

    def get_device_group_custom_url_category_object(
            self, url_cat_name, device_group):
        """
        Get candidate config by using action=get
        """
        xpath_head = self.build_device_group_custom_url_category_xpath_head(
            device_group)
        xpath_entry = constants.XPATH_ENTRY.format(url_cat_name)
        xpath = xpath_head + xpath_entry
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_GET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get URl category object: {0}".format(
                    result.get_error()))
        xml_path = constants.TAG_RESULT + constants.FORWARD_SLASH + constants.TAG_ENTRY
        xml_object = self.extract_xml_object_from_response(
            response_text, xml_path)
        return xml_object

    def show_device_group_custom_url_category_object(
            self, url_cat_name, device_group):
        pass

    # API METHODS - CUSTOM URL CATEGORY UPDATE
    def add_shared_custom_url_category_object(self, xpath_tail):
        xpath_head = self.build_shared_custom_url_category_xpath_head()
        xpath = xpath_head + xpath_tail
        logger.debug(
            'add_shared_custom_url_category_object - xpath: {0}'.format(xpath))
        #print('add_shared_service_group_object - xpath: {0}'.format(xpath))
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to create URl category object: {0}".format(
                    result.get_error()))

    def add_device_group_custom_url_category_object(self, xpath_tail, device_group):
        xpath_head = self.build_device_group_custom_url_category_xpath_head(
            device_group)
        xpath = xpath_head + xpath_tail
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to create URl category object: {0}".format(
                    result.get_error()))

    def add_member_to_shared_custom_url_category(
            self, element_xpath, url_cat_name):
        """
        url_cat_name: Name attribute of URLCategory object
        element_xpath: xpath built in a method of URLCategory object,
        i.e &element=<list><member>abc.com</member></list>
        """
        xpath_head = self.build_shared_custom_url_category_xpath_head()
        xpath_entry = constants.XPATH_ENTRY.format(url_cat_name)
        xpath_tail = element_xpath
        xpath = xpath_head + xpath_entry + xpath_tail
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to add URL to custom URL category object: {0}".format(
                    result.get_error()))

    def add_member_to_device_group_custom_url_category(
            self, element_xpath, url_cat_name, device_group):
        xpath_head = self.build_device_group_custom_url_category_xpath_head(
            device_group)
        xpath_entry = constants.XPATH_ENTRY.format(url_cat_name)
        xpath = xpath_head + xpath_entry + element_xpath

        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to add URL to device group custom URL category object: {0}".format(
                    result.get_error()))

    def remove_member_from_shared_custom_url_category(
            self, xpath_tail, url_cat_name):
        """
        =/config/shared/profiles/custom-url-category/entry[@name='url-test']/list/member[text()='abc.com']
        """
        xpath_head = self.build_shared_service_group_object_xpath_head()
        xpath_entry = constants.XPATH_ENTRY.format(url_cat_name)
        xpath = xpath_head + xpath_entry + xpath_tail

        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_DELETE, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to delete URL from shared custom URL category object: {0}".format(
                    result.get_error()))

    def remove_member_from_device_group_custom_url_category(
            self, xpath_tail, url_cat_name, device_group):
        """
        =/config/ devices/entry[@name='localhost.localdomain']/device-group/entry[@name='device_group']/profiles/custom-url-category/entry[@name='url-test']/list/member[text()='abc.com']
        """
        xpath_head = self.build_device_group_custom_url_category_xpath_head(
            device_group)
        xpath_entry = constants.XPATH_ENTRY.format(url_cat_name)
        xpath = xpath_head + xpath_entry + xpath_tail

        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_DELETE, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to delete URL from device group custom URL category object: {0}".format(
                    result.get_error()))

    def edit_shared_custom_url_category(
            self, node_xpath, element_xpath, url_cat_name):
        """
        node_xpath: Location of object to be replaced by edit like /list
        element_xpath: xpath built in a method of URLCategory object,
        i.e &element=<list><member>abc.com</member></list>
        url_cat_name: Name attribute of URLCategory object
        """
        xpath_head = self.build_shared_custom_url_category_xpath_head()
        xpath_entry = constants.XPATH_ENTRY.format(url_cat_name)
        xpath_tail = element_xpath
        xpath = xpath_head + xpath_entry + node_xpath + xpath_tail
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_EDIT, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to edit shared custom URL category object: {0}".format(
                    result.get_error()))

    def edit_device_group_custom_url_category(
            self, node_xpath, element_xpath, url_cat_name, device_group):
        xpath_head = self.build_device_group_custom_url_category_xpath_head(
            device_group)
        xpath_entry = constants.XPATH_ENTRY.format(url_cat_name)
        xpath = xpath_head + xpath_entry + node_xpath + element_xpath

        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_EDIT, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to edit device group custom URL category object: {0}".format(
                    result.get_error()))

    # API METHODS - POLICIES

    def get_shared_security_policies(self, policy_order, default_policy):
        xpath_head = self.build_shared_security_policy_xpath_head(
            policy_order, default_policy)

        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_GET, xpath=xpath_head)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get shared security policy: {0}".format(
                    result.get_error()))

        xml_path = constants.TAG_RESULT + constants.FORWARD_SLASH + constants.TAG_RULES
        xml_object = self.extract_xml_object_from_response(
            response_text, xml_path)
        return xml_object

    def get_shared_security_policy(self, policy_name, policy_order,
                                   default_policy):
        xpath_head = self.build_shared_security_policy_xpath_head(
            policy_order, default_policy)
        xpath_entry = constants.XPATH_ENTRY.format(policy_name)
        xpath = xpath_head + xpath_entry

        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_GET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get shared security policy: {0}".format(
                    result.get_error()))

        xml_path = constants.TAG_RESULT + constants.FORWARD_SLASH + constants.TAG_ENTRY
        xml_object = self.extract_xml_object_from_response(
            response_text, xml_path)
        return xml_object

    def get_shared_security_policy_names(self, policy_order, default_policy):
        xpath_head = self.build_shared_security_policy_xpath_head(
            policy_order, default_policy)
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

    def get_device_group_security_policies(self, device_group,
                                           policy_order, default_policy):
        xpath_head = self.build_device_group_security_policy_xpath_head(
            device_group, policy_order, default_policy)

        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_GET, xpath=xpath_head)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get device group security policy: {0}".format(
                    result.get_error()))

        xml_path = constants.TAG_RESULT + constants.FORWARD_SLASH + constants.TAG_RULES
        xml_object = self.extract_xml_object_from_response(
            response_text, xml_path)
        return xml_object

    def get_device_group_security_policy(self, policy_name, device_group,
                                         policy_order, default_policy):
        xpath_head = self.build_device_group_security_policy_xpath_head(
            device_group, policy_order, default_policy)
        xpath_entry = constants.XPATH_ENTRY.format(policy_name)
        xpath = xpath_head + xpath_entry

        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_GET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get device group security policy: {0}".format(
                    result.get_error()))

        xml_path = constants.TAG_RESULT + constants.FORWARD_SLASH + constants.TAG_ENTRY
        xml_object = self.extract_xml_object_from_response(
            response_text, xml_path)
        return xml_object

    def get_all_device_group_security_policy_names(
            self, device_group, policy_order, default_policy):
        xpath_head = self.build_device_group_security_policy_xpath_head(
            device_group, policy_order, default_policy)
        xpath_entry_name_attr = constants.XPATH_ENTRY_NAME_ALL
        xpath = xpath_head + xpath_entry_name_attr
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_GET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get device group security policy: {0}".format(
                    result.get_error()))

        # xml_path = '.' <=> find('.') to keep the whole response_text
        xml_path = constants.XML_ROOT
        xml_object = self.extract_xml_object_from_response(
            response_text, xml_path)
        return xml_object

    def add_shared_security_policy(
            self,
            xpath_tail,
            policy_order=constants.XPATH_PRE_RULEBASE,
            default_policy=False):
        xpath_head = self.build_shared_security_policy_xpath_head(
            policy_order, default_policy)
        xpath = xpath_head + xpath_tail
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to create shared security policy: {0}".format(
                    result.get_error()))

    def add_device_group_security_policy(
            self,
            xpath_tail,
            device_group,
            policy_order=constants.XPATH_PRE_RULEBASE,
            default_policy=False):
        xpath_head = self.build_device_group_security_policy_xpath_head(
            device_group, policy_order, default_policy)
        xpath = xpath_head + xpath_tail
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to create device group security policy: {0}".format(
                    result.get_error()))

    def move_shared_security_policy(self, policy_name, where, dst,
                                    policy_order=constants.XPATH_PRE_RULEBASE,
                                    default_policy=False):
        xpath_head = self.build_shared_security_policy_xpath_head(
            policy_order, default_policy)
        xpath_entry = constants.XPATH_ENTRY.format(policy_name)
        xpath = xpath_head + xpath_entry + '&' + \
            constants.MOVE_POLICY_WHERE.format(where) + \
            '&' + constants.MOVE_POLICY_DST.format(dst)
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_MOVE, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to move shared security policy: {0}".format(
                    result.get_error()))

    def move_device_group_security_policy(
            self,
            device_group,
            policy_name,
            where,
            dst,
            policy_order=constants.XPATH_PRE_RULEBASE):
        xpath_head = self.build_device_group_security_policy_xpath_head(
            device_group, policy_order)
        xpath_entry = constants.XPATH_ENTRY.format(policy_name)
        xpath = xpath_head + xpath_entry + '&' + \
            constants.MOVE_POLICY_WHERE.format(where) + \
            '&' + constants.MOVE_POLICY_DST.format(dst)
        response_text = self.config_command(
            action=constants.URL_REQUEST_ACTION_MOVE, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to move shared security policy: {0}".format(
                    result.get_error()))

    # OPERATIONAL COMMANDS
    def show_device_groups(self, device_group=None):
        """
        - Show device groups in Panorama tab
        - Return: A dictionary of dictionaries that have device group name as key and dictionary as value.
        This dictionary has serial as key and dictionary as value. This last dictionary has attributes such as serial,
        hostname as keys and values as value. Example:
        device_group_list = {'dg1': {},
        'dg2': {'00112233445566': {'serial': '00112233445566', 'hostname': 'fw1a'},
        '00112233445567': {'serial': '00112233445567', 'hostname': 'fw1b'}}}
        Empty device group has empty dictionary, e.g. device_group_list['empty_group'] = {}
        - Retrieve: device_group_list['dg2']['00112233445566']['hostname']
        """
        if device_group is not None:
            cmd = constants.CMD_SHOW_DEVICE_GROUPS_NAME.format(device_group)
        else:
            cmd = constants.CMD_SHOW_DEVICE_GROUPS_ALL
        response_text = self.op_command(cmd)

        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to show device group(s): {0} - Error: {1}\n\nPossible failure reasons: \n\t\
                    + Wrong DEVICE GROUP provided\n\t+ Wrong FIREWALL NAME provided!\n".format(
                    device_group, result.get_error()))

        root = ET.fromstring(response_text)

        # Get list of device groups
        device_group_names = [x.attrib[constants.TAG_ATTRIBUTE_NAME]
                              for x in root.findall(constants.RESPONSE_XPATH_DEVICEGROUPS_ENTRY)]
        device_group_list = {}
        for device_group in device_group_names:
            serial_names = []
            # Get firewall serial names
            # Code work with Python 2.7.13
            #serial_names = [x.attrib['name'] for x in root.findall(constants.RESPONSE_XPATH_DEVICEGROUPS_DEVICES_ENTRY.format(device_group))]
            # Workaround for Python 2.6.6
            device_group_entries = root.findall(
                constants.RESPONSE_XPATH_DEVICEGROUPS_ENTRY)
            for entry in device_group_entries:
                if entry.attrib[constants.TAG_ATTRIBUTE_NAME] == device_group:
                    # Only retrieve serials of connected devices
                    if constants.RESPONSE_NODE_CONNECTED_YES in ET.tostring(
                            entry, encoding='unicode'):
                        serial_names = [
                            x.get(
                                constants.TAG_ATTRIBUTE_NAME) for x in entry.findall(
                                constants.RESPONSE_XPATH_DEVICES_ENTRY)]
            # End of workaround
            device_group_list[device_group] = {}
            """
            If device group is an empty one like the parent device group,
            then the serial_names will be empty list []. Therefore this device group need to be ignored
            """
            if len(serial_names) == 0:
                continue
            """
            For each firewall - serial name, get all attributes such as
            hostname, connected, ip-address, uptime, etc.
            """
            for serial_name in serial_names:
                device_group_list[device_group][serial_name] = {}
                device_group_list[device_group][serial_name]['serial'] = serial_name
                # Code work with Python 2.7.13
                #device_group_list[device_group][serial_name]['hostname'] = root.find(constants.RESPONSE_XPATH_DEVICEGROUPS_DEVICES_ENTRY_HOSTNAME.format(device_group, serial_name)).text
                # Workaround for Python 2.6.6
                device_group_entries = root.findall(
                    constants.RESPONSE_XPATH_DEVICEGROUPS_ENTRY)
                for device_group_entry in device_group_entries:
                    if device_group_entry.attrib[constants.TAG_ATTRIBUTE_NAME] == device_group:
                        device_entries = device_group_entry.findall(
                            constants.RESPONSE_XPATH_DEVICES_ENTRY)
                        for device_entry in device_entries:
                            if device_entry.attrib[constants.TAG_ATTRIBUTE_NAME] == serial_name:
                                device_group_list[device_group][serial_name][constants.TAG_HOSTNAME] = device_entry.find(
                                    constants.TAG_HOSTNAME).text
                # End of workaround
                """
                device_group_list[device_group][serial_name]['connected'] = \
                    root.find('result/devicegroups/entry[@name="{0}"]/devices/entry[@name="{1}"]/connected'
                    .format(device_group, serial_name))
                device_group_list[device_group][serial_name]['ip-address'] = \
                    root.find('result/devicegroups/entry[@name="{0}"]/devices/entry[@name="{1}"]/ip-address'
                    .format(device_group, serial_name))
                device_group_list[device_group][serial_name]['uptime'] = \
                    root.find('result/devicegroups/entry[@name="{0}"]/devices/entry[@name="{1}"]/uptime'
                    .format(device_group, serial_name))
                device_group_list[device_group][serial_name]['model'] = \
                    root.find('result/devicegroups/entry[@name="{0}"]/devices/entry[@name="{1}"]/model'
                    .format(device_group, serial_name))
                device_group_list[device_group][serial_name]['sw-version'] = \
                    root.find('result/devicegroups/entry[@name="{0}"]/devices/entry[@name="{1}"]/sw-version'
                    .format(device_group, serial_name))
                """
        return device_group_list

    def show_template_stacks(self, template_stack=None):
        pass

    def show_active_devices(self):
        """
        List all connected active/standalone PAN firewalls from Panorama and return the FQDN list
        """
        #print('Showing active firewalls from connected devices on Panorama...\n')
        cmd = constants.CMD_SHOW_DEVICES_CONNECTED
        response_text = self.op_command(cmd)

        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to show active devices - Error: {0}\n".format(result.get_error()))

        root = ET.fromstring(response_text)

        single = [hostname.text.lower() for hostname in root.findall(
            constants.RESPONSE_XPATH_DEVICES_ENTRY_HOSTNAME) if not(
            hostname.text.lower().endswith("a") or hostname.text.lower().endswith("b"))]

        actives = [tag.text.lower() for tag in root.findall(
            constants.RESPONSE_XPATH_DEVICES_ENTRY_HA_ACTIVE_HOSTNAME)]

        active_devices = actives + single

        return util.append_postfix(active_devices, common_constants.
                                   DOMAIN_NAME_POSTFIX_PROD_FIREWALL)

    # COMBINED MULTIPLE OPERATIONAL COMMANDS
    def extract_device_group_from_firewall_name(self, firewall_name):
        """
        - firewall_name: Name of the firewall either in the short or FQDN
        - The method is to:
        + check if the firewall_name is a standalone or part of a cluster
        + return device group where firewall_name belongs to
        """
        device_group_list = {}
        device_group = None
        # Is standalone firewall?
        standalone = False

        # Try to extract device group from firewall name
        print((
            'Exacting device group from {0}... \n'.format(
                firewall_name.lower())))
        firewall_name = firewall_name.lower().split('.')[0]
        if any(l in firewall_name for l in ['a', 'b']):
            device_group = firewall_name[:-1]
        else:
            device_group = firewall_name
            standalone = True
        try:
            device_group_list = self.show_device_groups(device_group)
        except Exception:
            # If device group cannot be extracted from fw name
            # Reset device group back to None for later if condition
            device_group = None
            print('Firewall name and device group name are not the same... \n')
            print('Extracting device group from Panorama... \n')
            device_group_list = self.show_device_groups()

        # Variable to track if the firewall_name is found in all device groups
        found_in_all = False
        #device_group = ''
        """
        Extract device group name and serial numbers of provided firewall from
        device_group_list
        """
        # If device group is extracted from firewall name, all is good
        if device_group is not None:
            found_in_all = True
        else:  # if device_group is None:
            for k, v in list(device_group_list.items()):
                # If v is empty dict {}, skip to next round of the loop
                if bool(v) is False:
                    continue
                for kk, vv in list(v.items()):  # pylint: disable=unused-variable
                    # Variable to track if firewall_name is found in device
                    # group k
                    found_in_device_group = False
                    # If there is no 'hostname' in vv, skip to next vv
                    if 'hostname' not in vv:
                        continue
                    # If standalone firewall
                    if standalone:
                        found_in_device_group = vv['hostname'].upper(
                        ) == firewall_name.upper()
                    # Remove A or B character from firewall names
                    else:
                        found_in_device_group = vv['hostname'][:-
                                                               1].upper() == firewall_name[:-1].upper()
                    if found_in_device_group:
                        found_in_all = True
                if found_in_all:
                    device_group = k
                    break
        if found_in_all is False:
            sys.exit(
                '{0} is not a valid PAN firewall name. Please double check and run the automation again!\n'
                .format(firewall_name))
        print((
            'Device group "{0}" extracted from {1}!\n'.format(
                device_group,
                firewall_name)))
        return device_group

    # COMMIT
    def commit_partial(
            self,
            description='Firewall-Automation',
            admin='firewallauto'):
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
        if root.find('result/job') is None:
            """
            <response status="success" code="13"><msg>The result of this commit would be the same as
            the previous commit queued/processed.
            No edits have been made between these subsequent commits.
            Please check the previous commit status. If still needed, use commit force instead.
            </msg></response>
            """
            if root.find('msg') is not None:
                job_id = '-1'
        else:
            """
            <response status="success" code="19">
            <result>
            <msg>
            <line>Commit job enqueued with jobid 363067</line>
            </msg>
            <job>363067</job>
            </result>
            </response>
            """
            job_id = root.find('result/job').text

        return job_id

    def commit_all_device_group(
            self,
            device_group,
            description='Firewall-Automation',
            device_list=None,
            template='no',
            merge='yes',
            force='no',
            validate='no'):
        """
        - Input:
          + device_group: Name of device group
          + device_list: List of devices (serials) to be committed
          + template: If template is included in commit
          + merge: If merge with candidate config is selected
          + force: If force template values is selected
          + validate: If validate only, not commit
         - Output: Return jobid from response
                <response status="success" code="19">
                        <result>
                                <msg>
                                        <line>Job enqueued with jobid 311996</line>
                                </msg>
                                <job>311996</job>
                        </result>
                </response>
        """
        if device_list is None:
            cmd = constants.CMD_COMMIT_ALL_DEVICE_GROUP_ONLY.format(
                device_group, description)
        else:
            cmd = constants.CMD_COMMIT_ALL_DEVICE_GROUP_FULL.format(
                device_group, description, template, merge, force, validate)
            cmdroot = ET.fromstring(cmd)
            serial_node_text = ''.join(
                constants.NODE_ENTRY_NAME.format(x) for x in device_list)
            devices_text = constants.NODE_DEVICES.format(serial_node_text)
            devices_node = ET.fromstring(devices_text)
            # Current device node
            cmd_devices_node = cmdroot.find(constants.XPATH_DEVICE_GROUP_ENTRY)
            cmd_devices_node.append(devices_node)
            cmd = ET.tostring(cmdroot)

        response_text = self.commit_command(
            cmd, action=constants.CMD_COMMIT_ALL_ACTION)

        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to perform commit-all to device group {0} - Error: {1}\n\n\
                    Possible failure reason: Wrong DEVICE GROUP provided!\n".format(
                    device_group, result.get_error()))

        root = ET.fromstring(response_text)
        job_id = root.find('result/job').text

        return job_id

    def commit_all_template(
            self,
            template_stack,
            description='Firewall-Automation',
            device_list=None,
            merge='yes',
            force='no',
            validate='no'):
        """ Permit commit to template stacks
        """
        """
        - Input:
          + template_stack: Name of template stack
          + device_list: List of firewall serials to be committed
          + merge: If merge with candidate config is selected
          + force: If force template values is selected
          + validate: If validate only, not commit
         - Output: Return jobid from response
            <response status="success" code="19">
                <result>
                    <msg>
                        <line>Job enqueued with jobid 311996</line>
                    </msg>
                    <job>311996</job>
                </result>
            </response>
        """
        if device_list is None:
            cmd = constants.CMD_COMMIT_ALL_TEMPLATE_ONLY.format(template_stack,
                                                                description)
        else:
            cmd = constants.CMD_COMMIT_ALL_TEMPLATE_FULL.format(
                template_stack, description, merge, force, validate)
        cmdroot = ET.fromstring(cmd)
        devices_text = ''.join(constants.NODE_MEMBER.format(x)
                               for x in device_list)
        devices_node = ET.fromstring(devices_text)
        # Current device node
        cmd_devices_node = cmdroot.find(constants.XPATH_TEMPLATE_STACK_DEVICE)
        cmd_devices_node.append(devices_node)
        cmd = ET.tostring(cmdroot, encoding='unicode')

        response_text = self.commit_command(cmd)

        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to perform device group commit-all: {0}".format(result.get_error()))

        root = ET.fromstring(response_text)
        job_id = root.find('result/job').text

        return job_id

    def get_commit_progress(self, job_id):
        """
        Get commit progress. Returns job progress like 55%.
        """
        cmd = constants.CMD_SHOW_JOBS_ID.format(job_id)
        response_text = self.op_command(cmd)

        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to get commit progress: {0}".format(
                    result.get_error()))

        root = ET.fromstring(response_text)
        job_progress = root.find('result/job/progress').text

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
        job_status = root.find('result/job/result').text

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
        print(('\nCommit finished with result: {0}\n'.format(result_str)))
        return result_str == 'OK'

    # OTHERS
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

        percent = ("{0:." + str(decimals) + "f}").format(100 *
                                                         (iteration / float(total)))
        filledLength = int(length * iteration // total)
        progbar = fill * filledLength + '-' * (length - filledLength)
        sys.stdout.write(
            '\r%s |%s| %s%% %s\r' %
            (prefix, progbar, percent, suffix))
        sys.stdout.flush()
        # Print New Line on Complete
        if iteration == total:
            print('')
