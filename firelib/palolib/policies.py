import xml.etree.ElementTree as ET

from . import constants


class BadActionError(RuntimeError):
    pass


class SecurityPolicy:
    """
    A class covers all types of security policies: Panorama and firewall.

    """

    def __init__(self, name, apisession, location, vsys=None,
                 policy_order=constants.PRE_RULEBASE, default_policy=False):
        """
        - Input:
          + name: security policy name
          + apisession: Panorama or firewall api session
          + location:
                *if panorama: Shared or device-group name
                *if firewall: Panorama (policy managed by Panorama) or Local (local policy)
                /config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='device_group']
                /post-rulebase/default-security-rules
          + vsys: applicable to policies located on firewall and firewall is multivsys only
          + policy_order: pre-rulebase or post-rulebase. default-security-rules is \
          part of post-rulebase. If local policy, it is rulebase.
          + default_policy: It is default-security-rule or not
        """
        self._name = name
        self._session = apisession
        self._policy_order = '/' + policy_order
        self._location = location
        self._vsys = vsys
        self._default_policy = default_policy

        if apisession.get_session_host_role() == 'panorama':
            self._host_type = 'panorama'
        else:
            self._host_type = 'firewall'

        #self.xmlobject = None
        self._xmlobject = None

    # @staticmethod
    def build_xml_object(self, **kwargs):
        """
        **kwargs:
        + from: list of source zones, ['any'] if any
        + to: list of destination zones
        + source: list of names of addresses/IPs/networks/groups
        + destination: list of names of addresses/IPs/networks/groups
        + source-user: list of users, default <member>any</member>
        + application: list of applications, default <member>any</member>
        + service: list of services/groups
        + hip-profiles: list of hip profiles, default <member>any</member>
        + category: list of categories
        + action: allow, deny, etc
        + log-end: yes, no
        + log-start: yes, no
        + log-setting: log-all-to-panorama-and-ext or default
        + description: string
        + profile-setting:
          - If <profiles> then include profiles <url-filtering>, <file-blocking>, <virus>, <spyware>, <vulnerability>,
          <wildfire-analysis>
          - If <group> then include <member>SG-alert-all</member>
        + target-negate: <negate>no</negate>. N/A most of time
        + target-device: List of device entries/serials
        + disabled: yes, no
        + tag: list of tags
        + negate-source: yes or no
        + negate-destination: yes or no

        - Example: from=['inside', 'dmz'], to=['outside'], source/destination=['1.2.3.4', 'H-1.2.3.4', 'gn-networks'],
        source-user=[constants.NODE_MEMBER_DEFAULT_ANY],
        service=['gs-web'], application=[constants.NODE_MEMBER_DEFAULT_ANY],
        hip-profiles=[constants.NODE_MEMBER_DEFAULT_ANY],
        category=[constants.NODE_MEMBER_DEFAULT_ANY], action='allow',
        log-end='yes', log-setting=constants.NODE_LOG_SETTING.format(constants.LOG_SETTING_DEFAULT),
        description=constants.NODE_DESCRIPTION.format('TR'),
        profile-setting=constants.NODE_PROFILE_SETTING_GROUP.format(constants.PROFILE_SETTING_GROUP_DEFAULT),
        disabled='no'
        **xmlobject = <entry name="rule1" loc="device_group"><to></to>...</entry>
        ** Return xmlobject as ET object
        """
        policy_content = ''

        # Attach from zone to policy content
        from_zone = ''.join(constants.NODE_MEMBER.format(x)
                            for x in kwargs['from'])
        from_zone = constants.NODE_FROM_ZONE.format(from_zone)
        policy_content += from_zone

        # Attach to zone to policy content
        to_zone = ''.join(constants.NODE_MEMBER.format(x)
                          for x in kwargs['to'])
        to_zone = constants.NODE_TO_ZONE.format(to_zone)
        policy_content += to_zone

        # Attach source to policy content
        sources = ''.join(constants.NODE_MEMBER.format(x)
                          for x in kwargs['source'])
        sources = constants.NODE_SOURCE.format(sources)
        policy_content += sources

        # Attach destination to policy content
        destinations = ''.join(constants.NODE_MEMBER.format(x)
                               for x in kwargs['destination'])
        destinations = constants.NODE_DESTINATION.format(destinations)
        policy_content += destinations

        # Attach source user to policy content
        if kwargs['source-user']:
            srcuser = ''.join(constants.NODE_MEMBER.format(x)
                              for x in kwargs['source-user'])
            srcuser = constants.NODE_SOURCE_USER.format(srcuser)
            policy_content += srcuser

        # Attach application user to policy content
        # if application is not None:
        if kwargs['application']:
            app = ''.join(constants.NODE_MEMBER.format(x)
                          for x in kwargs['application'])
            app = constants.NODE_APPLICATION.format(app)
            policy_content += app

        # Attach service to policy content
        services = ''.join(constants.NODE_MEMBER.format(x)
                           for x in kwargs['service'])
        services = constants.NODE_SERVICE.format(services)
        policy_content += services

        # Attach hip profiles to policy content
        if kwargs['hip-profiles']:
            hip = ''.join(constants.NODE_MEMBER.format(x)
                          for x in kwargs['hip-profiles'])
            hip = constants.NODE_HIP_PROFILES.format(hip)
            policy_content += hip

        # Attach URL category to policy content
        if kwargs['category']:
            categories = ''.join(constants.NODE_MEMBER.format(x)
                                 for x in kwargs['category'])
            categories = constants.NODE_CATEGORY.format(categories)
            policy_content += categories

        # Attach action to policy content
        rule_action = constants.NODE_ACTION.format(kwargs['action'])
        policy_content += rule_action

        # Attach log start to policy content
        if kwargs['log-start']:
            logstart = constants.NODE_LOG_START.format(kwargs['log-start'])
            policy_content += logstart

        # Attach log end to policy content
        # if log-end is not None:
        if kwargs['log-end']:
            logend = constants.NODE_LOG_END.format(kwargs['log-end'])
            policy_content += logend

        # Attach log-setting to policy content
        logsetting = constants.NODE_LOG_SETTING.format(kwargs['log-setting'])
        policy_content += logsetting

        # Attach description to policy content
        if kwargs['description']:
            desc = constants.NODE_DESCRIPTION.format(kwargs['description'])
            policy_content += desc

        # Attach security profiles/group to policy content
        if kwargs['profile-type'] == 'profiles':
            profiles = ''
            if kwargs['url-filtering'] is not None:
                url = constants.NODE_URL_FILTERING.format(
                    kwargs['url-filtering'])
                profiles += url
            if kwargs['file-blocking'] is not None:
                fileblock = constants.NODE_FILE_BLOCKING.format(
                    kwargs['file-blocking'])
                profiles += fileblock
            if kwargs['virus'] is not None:
                vr = constants.NODE_VIRUS.format(kwargs['virus'])
                profiles += vr
            if kwargs['spyware'] is not None:
                sp = constants.NODE_SPYWARE.format(kwargs['spyware'])
                profiles += sp
            if kwargs['vulnerability'] is not None:
                vul = constants.NODE_VULNERABILITY.format(
                    kwargs['vulnerability'])
                profiles += vul
            if kwargs['wildfire'] is not None:
                wfa = constants.NODE_WILDFIRE_ANALYSIS.format(
                    kwargs['wildfire'])
                profiles += wfa
            #profiles = constants.NODE_PROFILE_SETTING_PROFILES.format(profiles)
            policy_content += constants.NODE_PROFILE_SETTING_PROFILES.format(
                profiles)
        elif kwargs['profile-type'] == 'group':
            group_member = constants.NODE_MEMBER.format(
                kwargs['group-profile'])
            # profile_group = constants.NODE_PROFILE_SETTING_GROUP.format(
            #    group_member)
            #profiles = constants.NODE_PROFILE_SETTING_GROUP.format(group_member)
            policy_content += constants.NODE_PROFILE_SETTING_GROUP.format(
                group_member)

        # Attach target settings
        target = ''
        if kwargs['target-negate']:
            target += constants.NODE_NEGATE.format(kwargs['target-negate'])
        if kwargs['target-device']:
            devices = ''.join(constants.NODE_ENTRY_NAME.format(x)
                              for x in kwargs['target-device'])
            target += constants.NODE_DEVICES.format(devices)
        policy_content += target

        # Attach disabled setting
        if kwargs['disabled']:
            policy_content += constants.NODE_DISABLED.format(
                kwargs['disabled'])

        # Attach tags setting
        if kwargs['tag']:
            tags = ''.join(constants.NODE_MEMBER.format(x)
                           for x in kwargs['tag'])
            policy_content += constants.NODE_TAG.format(tags)

        # Attach negate-source/negate-destination: 'yes' or 'no'
        if kwargs['negate-source']:
            policy_content += constants.NODE_NEGATE_SOURCE.format(
                kwargs['negate-source'])
        if kwargs['negate-destination']:
            policy_content += constants.NODE_NEGATE_DESTINATION.format(
                kwargs['negate-destination'])

        # XML string version of xmlobject
        xml = ''
        # If policy is in a device group
        if self.location not in ['Shared', 'Panorama', 'Local']:
            xml = constants.NODE_DEVICE_GROUP_POLICY_ENTRY.format(
                self.name, self.location, policy_content)
        else:  # If policy is in Panorama Shared or Firewall Panorama managed or Local
            xml = constants.NODE_POLICY_ENTRY.format(self.name, policy_content)

        # return ET.fromstring(xml)
        self._xmlobject = ET.fromstring(xml)

    def extract_policy_content_as_xml_string(self):
        """
        Input: self._xmlobject = <entry name="rule1" loc="device_group"><from>...<from><to>...</to>...</entry>
        Output: xml string <from>...<from><to>...</to>
        """
        return ''.join(ET.tostring(x, encoding='unicode') for x in self._xmlobject)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, n):
        self._name = n

    @property
    def policy_order(self):
        return self._policy_order

    @policy_order.setter
    def policy_order(self, po):
        self._policy_order = '/' + po

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, l):
        self._location = l

    @property
    def vsys(self):
        return self._vsys

    @vsys.setter
    def vsys(self, v):
        self._vsys = v

    @property
    def default_policy(self):
        return self._default_policy

    @default_policy.setter
    def default_policy(self, dp):
        self._default_policy = dp

    @property
    def host_type(self):
        return self._host_type

    @property
    def xmlobject(self):
        return self._xmlobject

    @xmlobject.setter
    def xmlobject(self, xml_object):
        self._xmlobject = xml_object

    def get_security_policy(self):
        """
        Call security policy API and store the result in self.xmlobject.
        """
        if self.host_type == 'panorama':
            if self.location == 'Shared':
                self.xmlobject = self._session.get_shared_security_policy(
                    self.name, self.policy_order, self.default_policy)
            else:  # self.location == '<device group name>'
                self.xmlobject = self._session.get_device_group_security_policy(
                    self.name, self.location, self.policy_order, self.default_policy)
        else:  # self.host_type == 'firewall'
            if self.location == 'Panorama':
                self.xmlobject = self._session.get_panorama_security_policy(
                    self.name, self.vsys, self.policy_order)
            else:  # self.location == 'Local'
                self.xmlobject = self._session.get_local_security_policy(
                    self.name, self.vsys, self.policy_order)

    def get_security_policy_content(self):
        if self.xmlobject is None:
            self.get_security_policy()

    def add_security_policy(self):
        """
        Method to create the security policy self.name to firewall management system
        using xmlobject initiated via build_xml_object().
        self.build_xml_object() needs to be called separately.
        """
        xpath_entry = constants.XPATH_ENTRY.format(
            self.xmlobject.attrib[constants.TAG_ATTRIBUTE_NAME])
        #element_node = self.xmlobject[0]
        #xpath_element = '&' + constants.XPATH_ELEMENT + '=' + ET.tostring(element_node)
        element_string = self.extract_policy_content_as_xml_string()
        xpath_element = '&' + constants.XPATH_ELEMENT + '=' + element_string
        xpath_tail = xpath_entry + xpath_element

        if self.host_type == 'panorama':
            if self.location == 'Shared':
                self._session.add_shared_security_policy(
                    xpath_tail, self.policy_order, self.default_policy)
            else:  # self.location == '<device group name>'
                self._session.add_device_group_security_policy(
                    xpath_tail, self.location, self.policy_order, self.default_policy)
        else:  # self.host_type == 'firewall'
            if self.location == 'Panorama':
                raise BadActionError(
                    'New local firewall policies cannot be added to Panorama managed section')
            # if self.location == 'Local'
            # /config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/
            # rulebase/security/rules/entry[@name='test']
            self._session.add_local_security_policy(
                xpath_tail, self.vsys, self.policy_order)

    def move_security_policy(self, where='after', dst='FWAUTO'):
        if self.host_type == 'panorama':
            if self.location == 'Shared':
                self._session.move_shared_security_policy(
                    self.name, where, dst, self.policy_order)
            else:  # self.location == '<device group name>'
                self._session.move_device_group_security_policy(
                    self.location, self.name, where, dst, self.policy_order)
        else:  # self.host_type == 'firewall'
            if self.location == 'Panorama':
                raise BadActionError(
                    'Panorama managed policies cannot be moved')
            # if self.location == 'Local'
            # /config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/
            # rulebase/security/rules/entry[@name='test']
            #self._session.move_local_security_policy(xpath_tail, self.vsys, self.policy_order)
            pass


class Policies:
    """
    A class covers all actions against the security rulebase like:
    - Check if a security policy exists
    - It should not cover policy level action like add, remove, update, disable
    - Security policy inventory like tell the number of security policies
    """

    def __init__(self, name, apisession, location, vsys=None,
                 policy_order=constants.PRE_RULEBASE):
        """
        - Input:
          + name: One of values: 'Security', 'NAT', 'QoS', 'Policy Based Forwarding',
                'Decryption', 'Tunnel Inspection', 'Application Override', 'Authentication',
                'DoS Protection'
          + apisession: Panorama or firewall api session
          + location:
                *if panorama: Shared or device-group name
                *if firewall: Panorama (policy managed by Panorama) or Local (local policy)
                /config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='device_group']/
                post-rulebase/default-security-rules
          + vsys: applicable to policies located on firewall and firewall is multivsys only
          + policy_order: pre-rulebase or post-rulebase. default-security-rules is \
          part of post-rulebase. If local policy, it is rulebase.
          + default_policy: It is default-security-rule or not
        """
        self._name = name
        self._session = apisession
        self._policy_order = '/' + policy_order
        self._location = location
        self._vsys = vsys

        if apisession.get_session_host_role() == 'panorama':
            self._host_type = 'panorama'
        else:
            self._host_type = 'firewall'

        #self.xmlobject = None
        self._xmlobject = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, n):
        self._name = n

    @property
    def policy_order(self):
        return self._policy_order

    @policy_order.setter
    def policy_order(self, po):
        self._policy_order = '/' + po

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, l):
        self._location = l

    @property
    def vsys(self):
        return self._vsys

    @vsys.setter
    def vsys(self, v):
        self._vsys = v

    @property
    def default_policy(self):
        return self._default_policy

    @default_policy.setter
    def default_policy(self, dp):
        self._default_policy = dp

    @property
    def host_type(self):
        return self._host_type

    @property
    def xmlobject(self):
        return self._xmlobject

    @xmlobject.setter
    def xmlobject(self, xml_object):
        self._xmlobject = xml_object

    def get_policies(self):
        """
        Call security policy API and store the result in self.xmlobject.
        """
        """
        if self.host_type == 'panorama':
            if self.location == 'Shared':
                self.xmlobject = self._session.get_shared_security_policy(self.name, self.policy_order,
                self.default_policy)
            else: #self.location == '<device group name>'
                self.xmlobject = self._session.get_device_group_security_policy(self.name, self.location,
                self.policy_order, self.default_policy)
        else: #self.host_type == 'firewall'
            if self.location == 'Panorama':
                self.xmlobject = self._session.get_panorama_security_policy(self.name, self.vsys, self.policy_order)
            else: #self.location == 'Local'
                self.xmlobject = self._session.get_local_security_policy(self.name, self.vsys, self.policy_order)
        """

    def get_policy_names(self):
        pass

    def get_first_policy_name(self):
        pass

    def is_policy_name_existent(self, policy_name='FWAUTO'):
        pass

    def add_policy(self, policy_name):
        pass

    def move_policy(self, where='after', dst='FWAUTO'):
        pass


class SecurityPolicies(Policies):
    """
    A class covers all actions against the security rulebase like:
    - Check if a security policy exists
    - It should not cover policy level action like add, remove, update, disable
    - Security policy inventory like tell the number of security policies
    """

    def __init__(self, apisession, location, vsys=None,
                 policy_order=constants.PRE_RULEBASE):
        """
        default-security-rules is part of post-rulebase.
        """
        Policies.__init__(self, constants.POLICY_TYPE_SECURITY, apisession,
                          location, vsys, policy_order)
        self._default_policy = False
        if policy_order == constants.POST_RULEBASE:
            self._default_policy = True

    @property
    def default_policy(self):
        return self._default_policy

    @default_policy.setter
    def default_policy(self, dp):
        self._default_policy = dp

    def get_policies(self):
        """
        Call security policy API and store the result in self.xmlobject.
        """
        if self.host_type == 'panorama':
            if self.location == 'Shared':
                self.xmlobject = self._session.get_shared_security_policies(
                    self.policy_order, self.default_policy)
            else:  # self.location == '<device group name>'
                self.xmlobject = self._session.get_device_group_security_policies(
                    self.name, self.location, self.policy_order, self.default_policy)
        else:  # self.host_type == 'firewall'
            if self.location == 'Panorama':
                self.xmlobject = self._session.get_panorama_security_policies(
                    self.vsys, self.policy_order)
            else:  # self.location == 'Local'
                self.xmlobject = self._session.get_local_security_policies(
                    self.vsys, self.policy_order)

    def get_policy_names(self):
        """
        Return a list of security policies in section self.policy_order of the
        device group self.location.
        Need to expand for local firewall as well
        """
        if self.host_type == 'panorama':
            if self.location == 'Shared':
                xmlobject = self._session.get_shared_security_policy_names(
                    self.policy_order, self.default_policy)
            else:  # self.location == '<device group name>'
                xmlobject = self._session.\
                    get_all_device_group_security_policy_names(
                        self.location, self.policy_order, self.default_policy)
        else:  # self.host_type == 'firewall'
            if self.location == 'Panorama':
                xmlobject = self._session.get_panorama_security_policy_names(
                    self.vsys, self.policy_order)
            else:  # self.location == 'Local'
                xmlobject = self._session.get_local_security_policy_names(
                    self.vsys, self.policy_order)

        # './result/entry[@loc="{0}"]'
        policy_loc = constants.XPATH_POLICY_LOC.format(self.location)

        policy_name_list = [x.attrib[constants.TAG_ATTRIBUTE_NAME] for x in
                            xmlobject.findall(policy_loc)]

        return policy_name_list

    def get_first_policy_name(self):
        """
        Get the first policy name in section self.policy_order of the
        device group self.location
        """
        if self.host_type == 'panorama':
            if self.location == 'Shared':
                xmlobject = self._session.get_shared_security_policy_names(
                    self.policy_order, self.default_policy)
            else:  # self.location == '<device group name>'
                xmlobject = self._session.\
                    get_all_device_group_security_policy_names(
                        self.location, self.policy_order, self.default_policy)
        else:  # self.host_type == 'firewall'
            if self.location == 'Panorama':
                xmlobject = self._session.get_panorama_security_policy_names(
                    self.vsys, self.policy_order)
            else:  # self.location == 'Local'
                xmlobject = self._session.get_local_security_policy_names(
                    self.vsys, self.policy_order)

        # './result/entry[@loc="{0}"]'
        policy_loc = constants.XPATH_POLICY_LOC.format(self.location)

        # policy_name_entry = <entry loc="internet" name="Next Rule ID 40" />
        policy_name_entry = xmlobject.find(policy_loc)

        return policy_name_entry.attrib[constants.TAG_ATTRIBUTE_NAME]

    def is_policy_name_existent(self, policy_name='FWAUTO'):
        """
        Return True if the policy name in section self.policy_order of the
        device group self.location exists. Otherwise return False.
        """
        if self.host_type == 'panorama':
            if self.location == 'Shared':
                xmlobject = self._session.get_shared_security_policy_names(
                    self.policy_order, self.default_policy)
            else:  # self.location == '<device group name>'
                xmlobject = self._session.\
                    get_all_device_group_security_policy_names(
                        self.location, self.policy_order, self.default_policy)
        else:  # self.host_type == 'firewall'
            if self.location == 'Panorama':
                xmlobject = self._session.get_panorama_security_policy_names(
                    self.vsys, self.policy_order)
            else:  # self.location == 'Local'
                xmlobject = self._session.get_local_security_policy_names(
                    self.vsys, self.policy_order)

        # './result/entry[@name="{0}"]'
        policy_name = constants.XPATH_POLICY_NAME.format(policy_name)

        # policy_name_entry = <entry loc="internet" name="FWAUTO" />
        policy_name_entry = xmlobject.find(policy_name)
        if policy_name_entry is None:
            return False
        return True

    def build_policy_content_from_kwargs(self, **kwargs):
        """
        **kwargs:
        + from: list of source zones, ['any'] if any
        + to: list of destination zones
        + source: list of names of addresses/IPs/networks/groups
        + destination: list of names of addresses/IPs/networks/groups
        + source-user: list of users, default <member>any</member>
        + application: list of applications, default <member>any</member>
        + service: list of services/groups
        + hip-profiles: list of hip profiles, default <member>any</member>
        + category: list of categories
        + action: allow, deny, etc
        + log-end: yes, no
        + log-start: yes, no
        + log-setting: log-all-to-panorama-and-ext or default
        + description: string
        + profile-setting:
          - If <profiles> then include profiles <url-filtering>, <file-blocking>, <virus>, <spyware>,
          <vulnerability>, <wildfire-analysis>
          - If <group> then include <member>SG-alert-all</member>
        + target-negate: <negate>no</negate>. N/A most of time
        + target-device: List of device entries/serials
        + disabled: yes, no
        + tag: list of tags
        + negate-source: yes or no
        + negate-destination: yes or no

        ** Return xmlobject as ET object
        """
        policy_content = ''

        # Attach from zone to policy content
        from_zone = ''.join(constants.NODE_MEMBER.format(x)
                            for x in kwargs['from'])
        from_zone = constants.NODE_FROM_ZONE.format(from_zone)
        policy_content += from_zone

        # Attach to zone to policy content
        to_zone = ''.join(constants.NODE_MEMBER.format(x)
                          for x in kwargs['to'])
        to_zone = constants.NODE_TO_ZONE.format(to_zone)
        policy_content += to_zone

        # Attach source to policy content
        sources = ''.join(constants.NODE_MEMBER.format(x)
                          for x in kwargs['source'])
        sources = constants.NODE_SOURCE.format(sources)
        policy_content += sources

        # Attach destination to policy content
        destinations = ''.join(constants.NODE_MEMBER.format(x)
                               for x in kwargs['destination'])
        destinations = constants.NODE_DESTINATION.format(destinations)
        policy_content += destinations

        # Attach source user to policy content
        if kwargs['source-user']:
            srcuser = ''.join(constants.NODE_MEMBER.format(x)
                              for x in kwargs['source-user'])
            srcuser = constants.NODE_SOURCE_USER.format(srcuser)
            policy_content += srcuser

        # Attach application user to policy content
        # if application is not None:
        if kwargs['application']:
            app = ''.join(constants.NODE_MEMBER.format(x)
                          for x in kwargs['application'])
            app = constants.NODE_APPLICATION.format(app)
            policy_content += app

        # Attach service to policy content
        services = ''.join(constants.NODE_MEMBER.format(x)
                           for x in kwargs['service'])
        services = constants.NODE_SERVICE.format(services)
        policy_content += services

        # Attach hip profiles to policy content
        if kwargs['hip-profiles']:
            hip = ''.join(constants.NODE_MEMBER.format(x)
                          for x in kwargs['hip-profiles'])
            hip = constants.NODE_HIP_PROFILES.format(hip)
            policy_content += hip

        # Attach URL category to policy content
        if kwargs['category']:
            categories = ''.join(constants.NODE_MEMBER.format(x)
                                 for x in kwargs['category'])
            categories = constants.NODE_CATEGORY.format(categories)
            policy_content += categories

        # Attach action to policy content
        rule_action = constants.NODE_ACTION.format(kwargs['action'])
        policy_content += rule_action

        # Attach log start to policy content
        if kwargs['log-start']:
            logstart = constants.NODE_LOG_START.format(kwargs['log-start'])
            policy_content += logstart

        # Attach log end to policy content
        # if log-end is not None:
        if kwargs['log-end']:
            logend = constants.NODE_LOG_END.format(kwargs['log-end'])
            policy_content += logend

        # Attach log-setting to policy content
        # if log-setting is not None:
        if kwargs['log-setting']:
            logsetting = constants.NODE_LOG_SETTING.format(
                kwargs['log-setting'])
            policy_content += logsetting

        # Attach description to policy content
        if kwargs['description']:
            desc = constants.NODE_DESCRIPTION.format(kwargs['description'])
            policy_content += desc

        # Attach security profiles/group to policy content
        if kwargs['profile-type'] == 'profiles':
            profiles = ''
            if kwargs['url-filtering'] is not None:
                url = constants.NODE_URL_FILTERING.format(
                    kwargs['url-filtering'])
                profiles += url
            if kwargs['file-blocking'] is not None:
                fileblock = constants.NODE_FILE_BLOCKING.format(
                    kwargs['file-blocking'])
                profiles += fileblock
            if kwargs['virus'] is not None:
                vr = constants.NODE_VIRUS.format(kwargs['virus'])
                profiles += vr
            if kwargs['spyware'] is not None:
                sp = constants.NODE_SPYWARE.format(kwargs['spyware'])
                profiles += sp
            if kwargs['vulnerability'] is not None:
                vul = constants.NODE_VULNERABILITY.format(
                    kwargs['vulnerability'])
                profiles += vul
            if kwargs['wildfire'] is not None:
                wfa = constants.NODE_WILDFIRE_ANALYSIS.format(
                    kwargs['wildfire'])
                profiles += wfa
            #profiles = constants.NODE_PROFILE_SETTING_PROFILES.format(profiles)
            policy_content += constants.NODE_PROFILE_SETTING_PROFILES.format(
                profiles)
        elif kwargs['profile-type'] == 'group':
            group_member = constants.NODE_MEMBER.format(
                kwargs['group-profile'])
            # profile_group = constants.NODE_PROFILE_SETTING_GROUP.format(
            #    group_member)
            #profiles = constants.NODE_PROFILE_SETTING_GROUP.format(group_member)
            policy_content += constants.NODE_PROFILE_SETTING_GROUP.format(
                group_member)
        # else: kwargs['profile-type'] == 'None'

        # Attach target settings
        target = ''
        if kwargs['target-negate']:
            target += constants.NODE_NEGATE.format(kwargs['target-negate'])
        if kwargs['target-device']:
            devices = ''.join(constants.NODE_ENTRY_NAME.format(x)
                              for x in kwargs['target-device'])
            target += constants.NODE_DEVICES.format(devices)
        policy_content += target

        # Attach disabled setting
        if kwargs['disabled']:
            policy_content += constants.NODE_DISABLED.format(
                kwargs['disabled'])

        # Attach tags setting
        if kwargs['tag']:
            tags = ''.join(constants.NODE_MEMBER.format(x)
                           for x in kwargs['tag'])
            policy_content += constants.NODE_TAG.format(tags)

        # Attach negate-source/negate-destination: 'yes' or 'no'
        if kwargs['negate-source']:
            policy_content += constants.NODE_NEGATE_SOURCE.format(
                kwargs['negate-source'])
        if kwargs['negate-destination']:
            policy_content += constants.NODE_NEGATE_DESTINATION.format(
                kwargs['negate-destination'])
        """
        #XML string version of xmlobject
        xml = ''
        #If policy is in a device group
        if self.location not in ['Shared', 'Panorama', 'Local']:
            xml = constants.NODE_DEVICE_GROUP_POLICY_ENTRY.format(self.name, \
            self.location, policy_content)
        else: #If policy is in Panorama Shared or Firewall Panorama managed or Local
            xml = constants.NODE_POLICY_ENTRY.format(self.name, policy_content)

        #return ET.fromstring(xml)
        self._xmlobject = ET.fromstring(xml)
        """
        return policy_content

    def add_policy(self, policy_name, **kwargs):
        xpath_entry = constants.XPATH_ENTRY.format(policy_name)
        #element_node = self.xmlobject[0]
        #xpath_element = '&' + constants.XPATH_ELEMENT + '=' + ET.tostring(element_node)
        element_string = self.build_policy_content_from_kwargs(**kwargs)
        xpath_element = '&' + constants.XPATH_ELEMENT + '=' + element_string
        xpath_tail = xpath_entry + xpath_element

        if self.host_type == 'panorama':
            if self.location == 'Shared':
                self._session.add_shared_security_policy(
                    xpath_tail, self.policy_order, self.default_policy)
            else:  # self.location == '<device group name>'
                self._session.add_device_group_security_policy(
                    xpath_tail, self.location, self.policy_order, self.default_policy)
        else:  # self.host_type == 'firewall'
            if self.location == 'Panorama':
                raise BadActionError(
                    'New local firewall policies cannot be added to Panorama managed section')
            # if self.location == 'Local'
            # /config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']
            # /rulebase/security/rules/entry[@name='test']
            self._session.add_local_security_policy(
                xpath_tail, self.vsys, self.policy_order)

    def move_policy(self, policy_name, where='after', dst='FWAUTO'):
        if self.host_type == 'panorama':
            if self.location == 'Shared':
                self._session.move_shared_security_policy(
                    policy_name, where, dst, self.policy_order)
            else:  # self.location == '<device group name>'
                self._session.move_device_group_security_policy(
                    self.location, policy_name, where, dst, self.policy_order)
        else:  # self.host_type == 'firewall'
            if self.location == 'Panorama':
                raise BadActionError(
                    'Panorama managed policies cannot be moved')
            # if self.location == 'Local'
            # /config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']
            # /rulebase/security/rules/entry[@name='test']
            #self._session.move_local_security_policy(xpath_tail, self.vsys, self.policy_order)
            pass
