"""New designed module that is the combination of panoapi and panfwapi modules.
It is going to replace them"""

#import sys
#import time
import xml.etree.ElementTree as ET

import requests

#from ..common import constants as common_constants
from ..common import firelogging, firepass
from . import constants

# START LOGGING TO FILE LIKE
logger = firelogging.FireLogger(name=__name__).firelogger
logger.debug('*** Start of panoapi.py ***')


class NotConnectedError(AssertionError):
    pass


class BadResponseError(RuntimeError):
    pass


class BadHTTPResponseError(RuntimeError):
    pass


class PANAPISession:
    "PAN API session class for both Panorama and firewalls"

    def __init__(self, host=constants.PANORAMA_PROD_HOST_A, hosttype='manager', panos='default'):
        """
        host: The host address of the Panorama or firewall device to be connected to.
        hosttype: Either 'manager' or 'firewall'
        panos: PANOS version. 'default' is currently active one in production
        """
        self._host = host
        if host == constants.PANORAMA_DEV_HOST:
            self._host = host + constants.DEV_HOST_POSTFIX
        elif '.' not in host:
            self._host = host + constants.PROD_HOST_POSTFIX

        self._hosttype = hosttype
        self._panos = panos

        self.__apikey = self.__get_palo_api_key()

    @property
    def hostname(self):
        return self._host

    @property
    def hosttype(self):
        """
        Replace method get_session_host_role()
        """
        return self._hosttype

    @hosttype.setter
    def hosttype(self, ht):
        self._hosttype = ht

    @property
    def panos(self):
        """
        Replace method get_session_host_role()
        """
        return self._panos

    @panos.setter
    def panos(self, po):
        self._panos = po

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

    # def get_session_host_role(self):
    #    """
    #    Get the role of the session host.
    #    Return: "panorama" or "firewall"
    #    """
    #    return 'panorama'

    def __get_palo_api_key(self):
        """
        Retrieve PAN API key from file
        """
        fp = firepass.FirePass()
        return fp.get_palo_apikey()

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
            url = constants.URL_HTTPS + self._host + constants.URL_API
            if key:
                self.__check_connected()
                url += 'key=' + self.__apikey + '&'
            url += '&'.join('{0}={1}'.format(k, v)
                            for k, v in kwargs.items())
            response = requests.get(url, verify=False)
        if method == constants.URL_REQUEST_METHOD_POST:
            url = constants.URL_HTTPS + self._host + constants.URL_API
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            body = 'key=' + self.__apikey + '&' + '&'.join('{0}={1}'.format(k, v) for k, v in kwargs.items())
            response = requests.post(url, data=body, headers=headers, verify=False)

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

    def config_command(self, config_type=constants.URL_REQUEST_TYPE_CONFIG, method=constants.URL_REQUEST_METHOD_GET, action=constants.URL_REQUEST_ACTION_GET, xpath=None):
        r = self.__make_request(method=method, type=config_type, action=action, xpath=xpath)
        response_text = self.__check_response(r)
        return response_text

    # /api/?type=op&cmd=
    def op_command(self, cmd, op_type=constants.URL_REQUEST_TYPE_OP):
        r = self.__make_request(type=op_type, cmd=cmd)
        response_text = self.__check_response(r)
        return response_text
