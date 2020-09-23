from typing import Optional, Union
import sys
import time
import xml.etree.ElementTree as ET

from ..common import firelogging
from .panapi import PANAPISession
from .panssh import PANSSHSession
from . import constants, responses

# START LOGGING TO FILE LIKE
logger = firelogging.FireLogger(name=__name__).firelogger
logger.debug('*** Start of palolib objects ***')


class _ObjectBase:
    """
    Private class as base class for all other object classes like config, commit, ops
    """

    def __init__(self, name: str, apisession: Union[PANAPISession, PANSSHSession]) -> None:
        """Initialize _BaseObject object

        :param name: Object name
        :type name: str
        :param apisession: Either firewall or Panorama API session
        :type apisession: PANAPISession
        """
        self._name = name
        self._session = apisession

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, n):
        self._name = n

    def print_object(self):
        pass


class ConfigBase(_ObjectBase):
    """
    A class to represent the base object of all objects modified by Configuration commands like security police, address, service, group, network, template
    """

    def __init__(self, name: str, apisession: Union[PANAPISession, PANSSHSession]) -> None:
        """[summary]

        :param name: Name of object in DEVICE GROUP SECTION
        :type name: str
        :param apisession: Either firewall or Panorama API session
        :type apisession: PANAPISession
        """
        _ObjectBase.__init__(self, name, apisession)
        self._xmlobject = None
        self._xpath_head = '/config'
        self._desc = None

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
        # else:
        #    self._desc = None
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

    def extract_string_content_from_xmlobject(self) -> Optional[str]:
        """
        Example input: <entry name="gs-web">
        <members><member>tcp-80</member><member>tcp-443</member></members>
        <tag><member>FWAUTO</member></tag>
        </entry>

        Example output: xml string - <members><member>tcp-80</member><member>tcp-443</member></members>
        <tag><member>FWAUTO</member></tag>
        """
        if self._xmlobject is not None:
            return ''.join(ET.tostring(x, encoding='unicode') for x in self._xmlobject)
        return None

    def is_object_defined(self) -> bool:
        """
        Check if self exists in FW system. Return: True if defined, else False
        """
        # Retrieve xmlobject
        if self.xmlobject is None:
            self.get_object()

        # If object does not exist in FW system
        if self.xmlobject is None:
            return False
        return True

    def get_object(self) -> None:
        """
        - Read service group object config from the host (Panorama or Firewall)
        - Extract the content at the entry level and assign it to xmlobject
        """
        response_text = self._session.config_command(
            action=constants.URL_REQUEST_ACTION_GET, xpath=self._xpath_head)
        result = responses.Response(response_text)
        if not result.ok():
            raise RuntimeError(
                "Failed to get address object: {0}".format(
                    result.get_error()))
        xml_path = constants.TAG_RESULT + constants.FORWARD_SLASH + constants.TAG_ENTRY
        self._xmlobject = self._session.extract_xml_object_from_response(response_text, xml_path)

    def create_object(self) -> None:
        """
        Create new object in FW system using self._xmlobject
        """
        element_tail = ''.join([ET.tostring(x, encoding='unicode') for x in self.xmlobject])
        xpath_element = '&' + constants.XPATH_ELEMENT + '=' + element_tail
        xpath = self._xpath_head + xpath_element
        response_text = self._session.config_command(
            action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise RuntimeError(
                "Failed to get address object: {0}".format(
                    result.get_error()))
        #xml_path = constants.TAG_RESULT + constants.FORWARD_SLASH + constants.TAG_ENTRY
        #self._xmlobject = self._session.extract_xml_object_from_response(response_text, xml_path)

    def set_description(self, desc: str) -> None:
        """
        Set the object description to desc
        """
        if self.desc is None:
            return

        # Update self._xmlobject
        self.desc = desc

        member_node = ET.Element(constants.TAG_DESCRIPTION)
        member_node.text = self.desc
        # &element=<description>11224488</description>
        element_xpath = '&' + constants.XPATH_ELEMENT + \
            '=' + ET.tostring(member_node, encoding='unicode')
        xpath = self._xpath_head + element_xpath
        response_text = self._session.config_command(action=constants.URL_REQUEST_ACTION_SET, xpath=xpath)
        result = responses.Response(response_text)
        if not result.ok():
            raise RuntimeError(
                "Failed to set object description: {0}".format(
                    result.get_error()))

    def append_description(self, desc, desc_max_length=1023) -> None:  # pylint: disable=unused-argument
        """
        PAN only support max desc length of 1023 for address, address group and service objects and 255 for custom URL category objects. If len of new description is greater than 1023, remove the first record number in current description, and then append new record number to it.
        - Algorithm:
        + If self.desc is not set from xmlobject, set it
        + Check if len(self._desc) + len(' ') + len(desc) > desc_max_length, remove first record number and space from self._desc
        + Append desc to self.desc
        """
        if self.desc is None:
            return

        new_description = ''
        if len(self.desc) == 0:
            new_description = desc
        # If new description is already in the description field, do nothing
        elif desc in self.desc:
            return
        elif len(self.desc) + len(' ') + len(desc) > desc_max_length:
            # Find index of the first space character
            idx = self.desc.index(' ')
            # Slice current desc removing first record number and space
            # then append new desc
            new_description = self.desc[idx + 1:] + ' ' + desc
        else:
            new_description = self.desc + ' ' + desc
        # Update self._xmlobject
        #self.desc = new_description
        self.set_description(new_description)
        """
		if self.host_type == 'panorama':
			if self.location == 'Shared':
				self._session.set_shared_address_object_description(
					xpath_tail, self.name)
			else:  # self.location == '<device group name>'
				self._session.set_device_group_address_object_description(
					xpath_tail, self.name, self.location)
		else:  # self.host_type == 'firewall'
			if self.location == 'Panorama':
				raise BadActionError("Address group {0} is read-only as it is managed by
									 Panorama".format(self.name))
			elif self.location == 'Shared':
				self.xmlobject = self._session.set_shared_address_object_description(
					xpath_tail, self.name)
			else:  # self.location = '<vsys no>'
				self._session.set_vsys_address_object_description(
					xpath_tail, self.name, self.location)
		"""


class OpsBase(_ObjectBase):
    """
    A class to represent the base object of all objects modified by Operational commands
    """


class CommitBase(_ObjectBase):
    """
    A class to represent the base object of all objects modified by Commit commands
    """

    def __init__(self, name: str, apisession: Union[PANAPISession, PANSSHSession]) -> None:
        """Initialize object

        :param name: Name of the commit type
        :type name: str
        :param apisession: Either firewall or Panorama API session
        :type apisession: Union[PANAPISession, PANSSHSession]
        """
        _ObjectBase.__init__(self, name, apisession)
        self._xmlobject = None
        #self._cmd = '<commit></commit>'

    @property
    def xmlobject(self):
        return self._xmlobject

    """
    @xmlobject.setter
    def xmlobject(self, xml_object):
        self._xmlobject = xml_object
    """

    def get_job_id(self):
        """
        Get the commit job ID after calling self.commit()
        """
        if self._xmlobject is None:
            raise RuntimeError('Commit has not been trigger yet. Make sure to call Commit.commit() first!')

        if self._xmlobject.find('result/job') is None:
            """
            <response status="success" code="13"><msg>The result of this commit would be the same as
            the previous commit queued/processed.
            No edits have been made between these subsequent commits.
            Please check the previous commit status. If still needed, use commit force instead.
            </msg></response>
            """
            if self._xmlobject.find('msg') is not None:
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
            job_id = self._xmlobject.find('result/job').text

        return job_id

    def get_commit_progress(self, job_id):
        """
        Get commit progress. Returns job progress like 55%.
        """
        cmd = constants.CMD_SHOW_JOBS_ID.format(job_id)
        response_text = self._session.op_command(cmd)

        result = responses.Response(response_text)
        if not result.ok():
            raise RuntimeError(
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
        response_text = self._session.op_command(cmd)

        result = responses.Response(response_text)
        if not result.ok():
            raise RuntimeError(
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
