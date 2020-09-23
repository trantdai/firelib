"A module to contains both PAN API (Commit) and SSH (SSHCommit) commit classes"

from typing import Optional, Union
import xml.etree.ElementTree as ET

from .objectbase import CommitBase
from ..common import firelogging
from .panapi import PANAPISession
from .panssh import PANSSHSession
from . import constants, responses

# START LOGGING TO FILE
logger = firelogging.FireLogger(name=__name__).firelogger
logger.debug('*** Start of panoapi.py ***')


class BadResponseError(RuntimeError):
    pass


class Commit(CommitBase):
    """
    A class to represent commit actions on both Panorama and firewalls
    """

    def __init__(self, name: str, apisession: Union[PANAPISession, PANSSHSession], action: Optional[str] = "partial") -> None:
        """Initialize object

        :param name: Name of the commit type
        :type name: str
        :param apisession: Either firewall or Panorama API session
        :type apisession: Union[PANAPISession, PANSSHSession]
        :param action: Commit action either partial or all
        :type action: None or str
        """
        CommitBase.__init__(self, name, apisession)
        self._action = action

    def commit(self, admin: Optional[str] = 'firewallauto', force=False, device_and_network: Optional[str] = None, shared_object: Optional[str] = None, description: Optional[str] = 'Firewall-Automation') -> None:
        """A method cover all API Commit actions. See https://docs.paloaltonetworks.com/pan-os/9-0/pan-os-panorama-api/pan-os-xml-api-request-types/commit-configuration-api/commit.html
        :param admin: Commit changes done by firewall admin, defaults to 'firewallauto'
        :type admin: str, optional
        :param description: Commit description, defaults to 'Firewall-Automation'
        :type description: str, optional
        :param force: Is it force commit, defaults to False
        :type force: bool, optional
        :param device_and_network: Does commit include device and network, defaults to None. Other values are 'included' and 'excluded'
        :type device_and_network: str, optional
        :param shared_object: Deos commit include shared object, defaults to to None. Other values are 'included' and 'excluded'
        :type shared_object: str, optional
        """
        cmd = "<commit>"
        if self._session.panos == "8.1.0":
            pass
        elif self._session.panos == "8.0.0":
            pass
        else:  # self._session.panos == "default":
            if self._action == "partial":
                cmd += "<partial>"
            if admin is not None:
                cmd += "<admin><member>{0}</member></admin>".format(admin)
            if force:
                cmd += "<force></force>"
            if device_and_network is not None:
                if device_and_network in ('included', 'excluded'):
                    cmd += "<device-and-network>{0}</device-and-network>".format(device_and_network)
            if shared_object is not None:
                if shared_object in ('included', 'excluded'):
                    cmd += "<shared-object>{0}</shared-object>".format(shared_object)
            if "partial" in cmd:
                cmd += "</partial>"
            if description is not None:
                cmd += "<description>{0}</description>".format(description)
            cmd += "</commit>"

        # Make commit
        response_text = self._session.commit_command(cmd, action=self._action)
        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to perform partial commit: {0}".format(
                    result.get_error()))
        self._xmlobject = ET.fromstring(response_text)


class CommitAll(CommitBase):
    """
    A class to represent commit actions on Panorama to push changes to firewalls
    """

    def __init__(self, name: str, apisession: PANAPISession) -> None:
        """Initialize object

        :param name: Name of the commit type
        :type name: str
        :param apisession: Either firewall or Panorama API session
        :type apisession: PANAPISession
        :param action: Commit action either partial or all
        :type action: None or str
        """
        CommitBase.__init__(self, name, apisession)
        self._action = "all"

    def commit_all_device_group(
            self,
            device_group,
            description='Firewall-Automation',
            device_list=None,
            template='no',
            merge='yes',
            force='no',
            validate='no') -> None:
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
            # Generate new ET node from device_list: <devices><entry
            # name="s/n"/><entry name="s/n"/></devices>
            devices_text = constants.NODE_DEVICES.format(serial_node_text)
            devices_node = ET.fromstring(devices_text)
            # Current device node
            cmd_devices_node = cmdroot.find(constants.XPATH_DEVICE_GROUP_ENTRY)
            cmd_devices_node.append(devices_node)
            cmd = ET.tostring(cmdroot)

        response_text = self._session.commit_command(
            cmd, action=constants.CMD_COMMIT_ALL_ACTION)

        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to perform commit-all to device group {0} - Error: {1}\n\n\
					Possible failure reason: Wrong DEVICE GROUP provided!\n".format(
                    device_group, result.get_error()))

        self._xmlobject = ET.fromstring(response_text)

    def commit_all_template(
            self,
            template_stack,
            description='Firewall-Automation',
            device_list=None,
            merge='yes',
            force='no',
            validate='no') -> None:
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
        # Generate new ET node from device_list: <entry
        # name="s/n"/><entry name="s/n"/>
        devices_node = ET.fromstring(devices_text)
        # Current device node
        cmd_devices_node = cmdroot.find(constants.XPATH_TEMPLATE_STACK_DEVICE)
        cmd_devices_node.append(devices_node)
        cmd = ET.tostring(cmdroot, encoding='unicode')

        response_text = self._session.commit_command(cmd)

        result = responses.Response(response_text)
        if not result.ok():
            raise BadResponseError(
                "Failed to perform device group commit-all: {0}".format(result.get_error()))

        self._xmlobject = ET.fromstring(response_text)
