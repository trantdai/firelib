# URL
URL_HTTPS = 'https://'
URL_API = '/api/?'
URL_REQUEST_METHOD_GET = 'GET'
URL_REQUEST_METHOD_POST = 'POST'
URL_REQUEST_TYPE_CONFIG = 'config'
URL_REQUEST_TYPE_OP = 'op'
URL_REQUEST_TYPE_COMMIT = 'commit'
URL_REQUEST_ACTION_GET = 'get'
URL_REQUEST_ACTION_SHOW = 'show'
URL_REQUEST_ACTION_DELETE = 'delete'
URL_REQUEST_ACTION_SET = 'set'
URL_REQUEST_ACTION_MOVE = 'move'
URL_REQUEST_CMD = 'cmd'
URL_REQUEST_ACTION_EDIT = 'edit'

# XML
XML_ROOT = '.'
TAG_RESULT = 'result'
TAG_ENTRY = 'entry'
TAG_MEMBER_START = '<member>'
TAG_MEMBER_END = '</member>'
TAG_MEMBER = 'member'
TAG_STATIC_START = '<static>'
TAG_STATIC_END = '</static>'
TAG_STATIC = 'static'
TAG_DESCRIPTION_START = '<description>'
TAG_DESCRIPTION_END = '</description>'
TAG_DESCRIPTION = 'description'
TAG_TAG = 'tag'
TAG_ATTRIBUTE_NAME = 'name'
TAG_HOSTNAME = 'hostname'
TAG_RULES = 'rules'

# COMMIT
TAG_COMMIT_START = '<commit>'
TAG_COMMIT_END = '</commit>'
TAG_PARTIAL_START = '<partial>'
TAG_PARTIAL_END = '</partial>'
TAG_ADMIN_START = '<admin>'
TAG_ADMIN_END = '</admin>'
NODE_ENTRY_NAME = '<entry name="{0}"/>'
NODE_MEMBER = '<member>{0}</member>'
CMD_COMMIT_PARTIAL = '<commit><partial><admin><member>{0}</member></admin></partial><description>{1}</description></commit>'
#CMD_COMMIT_ALL_DEVICE_GROUP_ONLY = '<commit-all><shared-policy><device-group><entry name="{0}"/></device-group><description>{1}</description></shared-policy></commit-all>'
CMD_COMMIT_ALL_DEVICE_GROUP_ONLY = '<commit-all><shared-policy><device-group><entry name="{0}"/></device-group><description>{1}</description><include-template>no</include-template><merge-with-candidate-cfg>yes</merge-with-candidate-cfg><force-template-values>no</force-template-values><validate-only>no</validate-only></shared-policy></commit-all>'
#CMD_COMMIT_ALL_DEVICE_GROUP_FULL = '<commit-all><shared-policy><device-group><entry name="{0}"><devices></devices></entry></device-group><description>{1}</description><include-template>{2}</include-template><merge-with-candidate-cfg>{3}</merge-with-candidate-cfg><force-template-values>{4}</force-template-values><validate-only>{5}</validate-only></shared-policy></commit-all>'
CMD_COMMIT_ALL_DEVICE_GROUP_FULL = '<commit-all><shared-policy><device-group><entry name="{0}"></entry></device-group><description>{1}</description><include-template>{2}</include-template><merge-with-candidate-cfg>{3}</merge-with-candidate-cfg><force-template-values>{4}</force-template-values><validate-only>{5}</validate-only></shared-policy></commit-all>'
CMD_COMMIT_ALL_TEMPLATE_ONLY = '<commit-all><template-stack><name>{0}</name><description>{1}</description></template-stack></commit-all>'
#CMD_COMMIT_ALL_TEMPLATE_FULL = '<commit-all><template-stack><name>{0}</name><device></device><description>{1}</description><merge-with-candidate-cfg>{2}</merge-with-candidate-cfg><force-template-values>{3}</force-template-values><validate-only>{4}</validate-only></template-stack></commit-all>'
CMD_COMMIT_ALL_TEMPLATE_FULL = '<commit-all><template-stack><name>{0}</name><description>{1}</description><merge-with-candidate-cfg>{2}</merge-with-candidate-cfg><force-template-values>{3}</force-template-values><validate-only>{4}</validate-only></template-stack></commit-all>'
CMD_COMMIT_ALL_ACTION = 'all'
XPATH_DEVICE_GROUP_ENTRY = 'shared-policy/device-group/entry'
XPATH_TEMPLATE_STACK_DEVICE = 'template-stack/device'
NODE_DEVICES = '<devices>{0}</devices>'
NODE_DEVICE = '<device>{0}</device>'


# XPATH
XPATH_CONFIG = '/config'
XPATH_SHARED = '/shared'
XPATH_ELEMENT = 'element'

XPATH_PRE_RULEBASE = '/pre-rulebase'
XPATH_POST_RULEBASE = '/post-rulebase'
XPATH_RULEBASE = '/rulebase'
XPATH_SECURITY = '/security'
XPATH_RULES = '/rules'
XPATH_DEFAULT_SECURITY_RULES = '/default-security-rules'
XPATH_ENTRY = "/entry[@name='{0}']"
XPATH_ENTRY_NAME_ALL = "/entry/@name"
XPATH_DEVICES = '/devices'
XPATH_ENTRY_LOCALHOST_LOCALDOMAIN = 'localhost.localdomain'
XPATH_DEVICE_GROUP = '/device-group'

XPATH_VSYS = '/vsys'
XPATH_PANORAMA = '/panorama'

# OBJECTS
XPATH_ADDRESS = '/address'
XPATH_ADDRESS_GROUP = '/address-group'
XPATH_STATIC = '/static'
XPATH_LIST = '/list'
XPATH_MEMBERS = '/members'
XPATH_MEMBER_TEXT = "/member[text()='{0}']"
ADDRESS_TYPE_FQDN = 'fqdn'
ADDRESS_TYPE_IP_NETMASK = 'ip-netmask'
ADDRESS_TYPE_IP_RANGE = 'ip-range'
TAG_SERVICE_PROTOCOL = 'protocol'
TAG_SERVICE_PORT = 'port'
SERVICE_PROTOCOL_TCP = 'tcp'
SERVICE_PROTOCOL_UDP = 'tcp'
SERVICE_PROTOCOL_SCTP = 'sctp'
XPATH_SERVICE = '/service'
XPATH_SERVICE_GROUP = '/service-group'
PAN_SERVICE_PROTOCOLS = ['tcp', 'udp', 'sctp']
XPATH_PROFILES = '/profiles'
XPATH_CUSTOM_URL_CATEGORY = '/custom-url-category'

# POLICIES
XPATH_POLICY_LOC = './result/entry[@loc="{0}"]'
#XPATH_POLICY_LOC = 'result/entry[@loc="{0}"]'
#XPATH_POLICY_LOC = './/entry[@loc="{0}"]'
XPATH_POLICY_NAME = './result/entry[@name="{0}"]'
NODE_MEMBER_DEFAULT_ANY = '<member>any</member>'
NODE_FROM_ZONE = '<from>{0}</from>'
NODE_TO_ZONE = '<to>{0}</to>'
NODE_SOURCE = '<source>{0}</source>'
NODE_DESTINATION = '<destination>{0}</destination>'
NODE_SOURCE_USER = '<source-user>{0}</source-user>'
NODE_APPLICATION = '<application>{0}</application>'
NODE_SERVICE = '<service>{0}</service>'
NODE_HIP_PROFILES = '<hip-profiles>{0}</hip-profiles>'
NODE_CATEGORY = '<category>{0}</category>'
NODE_ACTION = '<action>{0}</action>'
NODE_LOG_START = '<log-start>{0}</log-start>'
NODE_LOG_END = '<log-end>{0}</log-end>'
NODE_DESCRIPTION = '<description>{0}</description>'
NODE_PROFILE_SETTING_PROFILES = '<profile-setting><profiles>{0}</profiles></profile-setting>'
NODE_PROFILE_SETTING_GROUP = '<profile-setting><group>{0}</group></profile-setting>'
NODE_LOG_SETTING = '<log-setting>{0}</log-setting>'
NODE_DISABLED = '<disabled>{0}</disabled>'
NODE_TAG = '<tag>{0}</tag>'
NODE_NEGATE = '<negate>{0}</negate>'
#NODE_DEVICES = '<devices>{0}</devices>'
NODE_TARGET = '<target>{0}</target>'
NODE_POLICY_ENTRY = '<entry name="{0}">{1}</entry>'
NODE_DEVICE_GROUP_POLICY_ENTRY = '<entry name="{0}" loc="{1}">{2}</entry>'
NODE_URL_FILTERING = '<url-filtering>{0}</url-filtering>'
NODE_FILE_BLOCKING = '<file-blocking>{0}</file-blocking>'
NODE_VIRUS = '<virus>{0}</virus>'
NODE_SPYWARE = '<spyware>{0}</spyware>'
NODE_VULNERABILITY = '<vulnerability>{0}</vulnerability>'
NODE_WILDFIRE_ANALYSIS = '<wildfire-analysis>{0}</wildfire-analysis>'
NODE_NEGATE_SOURCE = '<negate-source>{0}</negate-source>'
NODE_NEGATE_DESTINATION = '<negate-destination>{0}</negate-destination>'

LOG_SETTING_DEFAULT = 'default'
LOG_SETTING_COMMON = 'common'
PROFILE_SETTING_GROUP_DEFAULT = 'default'
PROFILE_SETTING_GROUP_COMMON = 'profile_group_common'
PROFILE_SETTING_GROUP_COMMON_URL = 'profile_group_url_common'

POLICY_NAME_PREFIX = 'firewauto-'
FWAUTO_POLICY = 'firewauto'
SERVICE_NAME_TCP_PREFIX = 'tcp-'
SERVICE_NAME_UDP_PREFIX = 'tcp-'
MOVE_POLICY_WHERE = 'where={0}'
MOVE_POLICY_DST = 'dst={0}'

POLICY_TYPE_SECURITY = 'Security'
POLICY_TYPE_NAT = 'NAT'
POLICY_TYPE_DOS = 'QoS'
POLICY_TYPE_POLICY_BASED_ROUTING = 'Policy Based Forwarding'
POLICY_TYPE_DECRYPTION = 'Decryption'
POLICY_TYPE_TUNNEL_INSPECTION = 'Tunnel Inspection'
POLICY_TYPE_APPLICATION_OVERRIDE = 'Application Override'
POLICY_TYPE_AUTHENTICATION = 'Authentication'
POLICY_TYPE_DOS_PROTECTION = 'DoS Protection'

SECURITY_POLICY_OPTION_KWARGS = {
    'from': None,
    'to': None,
    'source': None,
    'destination': None,
    'service': None,
    'application': None,
    'source-user': None,
    'category': 'any',
    'hip-profiles': None,
    'log-setting': 'default',
    'description': None,
    'profile-type': 'group',
    'group-profile': 'default',
    'url-filtering': None,
    'file-blocking': None,
    'virus': None,
    'spyware': None,
    'vulnerability': None,
    'wildfire': None,
    'log-start': 'no',
    'log-end': 'yes',
    'target-negate': None,
    'target-device': None,
    'disabled': 'no',
    'tag': 'FWAUTO',
    'action': 'allow',
    'negate-source': None,
    'negate-destination': None}

FWAUTO_SECURITY_POLICY_OPTION_KWARGS = {
    'from': ['any'],
    'to': ['any'],
    'source': ['1.2.3.4'],
    'destination': ['1.2.3.4'],
    'service': ['any'],
    'application': ['any'],
    'source-user': ['any'],
    'category': ['any'],
    'hip-profiles': ['any'],
    'log-setting': None,
    'description': 'Section managed by Firewall Automation',
    'profile-type': 'None',
    'group-profile': 'None',
    'url-filtering': None,
    'file-blocking': None,
    'virus': None,
    'spyware': None,
    'vulnerability': None,
    'wildfire': None,
    'log-start': 'no',
    'log-end': 'yes',
    'target-negate': None,
    'target-device': None,
    'disabled': 'yes',
    'tag': [
        'New Section',
        'FWAUTO'],
    'action': 'allow',
    'negate-source': None,
    'negate-destination': None}

# NETWORK
XPATH_NETWORK = '/network'
XPATH_VIRTUAL_WIRE = '/virtual-wire'
XPATH_VIRTUAL_ROUTER = '/virtual-router'

# VSYS
VSYS_DEFAULT = 'vsys1'

# OP COMMANDS
CMD_SHOW_JOBS_ID = '<show><jobs><id>{0}</id></jobs></show>'
CMD_TEST_SECURITY_POLICY_VWIRE = '<test><security-policy-match><source>{0}</source><destination>{1}</destination><destination-port>{2}</destination-port><protocol>{3}</protocol><application>{4}</application><show-all>{5}</show-all></security-policy-match></test>'
CMD_TEST_SECURITY_POLICY_VWIRE_SERVICE_ANY = '<test><security-policy-match><source>{0}</source><destination>{1}</destination><protocol>{2}</protocol><application>{3}</application><show-all>{4}</show-all></security-policy-match></test>'
CMD_TEST_SECURITY_POLICY_LAYER3 = '<test><security-policy-match><source>{0}</source><destination>{1}</destination><destination-port>{2}</destination-port><protocol>{3}</protocol><from>{4}</from><to>{5}</to><application>{6}</application><show-all>{7}</show-all></security-policy-match></test>'
CMD_TEST_SECURITY_POLICY_LAYER3_SERVICE_ANY = '<test><security-policy-match><source>{0}</source><destination>{1}</destination><protocol>{2}</protocol><from>{3}</from><to>{4}</to><show-all>{5}</show-all></security-policy-match></test>'
CMD_SHOW_INTERFACE_LOGICAL = '<show><interface>logical</interface></show>'
CMD_TEST_ROUTING = '<test><routing><fib-lookup><ip>{0}</ip><virtual-router>{1}</virtual-router></fib-lookup></routing></test>'
CMD_SHOW_DEVICE_GROUPS_ALL = '<show><devicegroups/></show>'
CMD_SHOW_DEVICE_GROUPS_NAME = '<show><devicegroups><name>{0}</name></devicegroups></show>'
CMD_SHOW_TEMPLATE_STACK_ALL = '<show><template-stack/></show>'
CMD_SHOW_TEMPLATE_STACK_NAME = '<show><template-stack><name>{0}</name></template-stack></show>'
CMD_SHOW_DEVICES_CONNECTED = '<show><devices><connected></connected></devices></show>'

# OTHERS
FORWARD_SLASH = '/'
PANORAMA_PROD_HOST_A = 'panoa'
PANORAMA_PROD_HOST_B = 'panob'
PROD_HOST_POSTFIX = '.local.net'
PANORAMA_DEV_HOST = 'devpano'
DEV_HOST_POSTFIX = '.dev.local.net'
FIREWALL_DEV_HOST_A = 'devfwa'
FIREWALL_DEV_HOST_B = 'devfwa'
PRE_RULEBASE = 'pre-rulebase'
POST_RULEBASE = 'post-rulebase'
RESERVED_PROTOCOL_NUMBER = '255'

# RESPONSE
# - GET VIRTUAL WIRES
RESPONSE_XPATH_VIRTUAL_WIRE_ENTRY = 'result/virtual-wire/entry'
# - TEST SECURITY POLICY
RESPONSE_XPATH_RULES_ENTRY = 'result/rules/entry'
RESPONSE_XPATH_RULES_ENTRY_INDEX = 'result/rules/entry/index'
# -- SECURITY POLICY - PREFIX: /result/entry/
RESPONSE_XPATH_FROM_MEMBER = 'from/member'
RESPONSE_XPATH_SOURCE_MEMBER = 'source/member'
RESPONSE_XPATH_NEGATE_SOURCE_MEMBER = 'negate-source/member'
RESPONSE_XPATH_SOURCE_USER_MEMBER = 'source-user/member'
RESPONSE_XPATH_HIP_PROFILES_MEMBER = 'hip-profiles/member'
RESPONSE_XPATH_TO_MEMBER = 'to/member'
RESPONSE_XPATH_DESTINATION_MEMBER = 'destination/member'
RESPONSE_XPATH_NEGATE_DESTINATION_MEMBER = 'negate-destination/member'
RESPONSE_XPATH_APPLICATION_MEMBER = 'application/member'
RESPONSE_XPATH_SERVICE_MEMBER = 'service/member'
RESPONSE_XPATH_CATEGORY_MEMBER = 'category/member'
RESPONSE_XPATH_ACTION = 'action'
RESPONSE_XPATH_DISABLED = 'disabled'
RESPONSE_XPATH_SECURITY_PROFILE_GROUP_MEMBER = 'profile-setting/group/member'
RESPONSE_XPATH_SECURITY_PROFILE_VIRUS_MEMBER = 'profile-setting/profiles/virus/member'
RESPONSE_XPATH_SECURITY_PROFILE_FILEBLOCKING_MEMBER = 'profile-setting/profiles/file-blocking/member'
RESPONSE_XPATH_SECURITY_PROFILE_SPYWARE_MEMBER = 'profile-setting/profiles/spyware/member'
RESPONSE_XPATH_SECURITY_PROFILE_WILDFIRE_MEMBER = 'profile-setting/profiles/wildfire-analysis/member'
RESPONSE_XPATH_SECURITY_PROFILE_URL_MEMBER = 'profile-setting/profiles/url-filtering/member'
RESPONSE_XPATH_OPTION_DSRI = 'option/disable-server-response-inspection'
RESPONSE_XPATH_OPTION_LOGSTART = 'log-start'
RESPONSE_XPATH_OPTION_LOGEND = 'log-end'
RESPONSE_XPATH_OPTION_LOG_SETTING = 'log-setting'
RESPONSE_XPATH_DESCRIPTION = 'description'
RESPONSE_XPATH_TAG_MEMBER = 'tag/member'
# - SHOW INTERFACE LOGICAL
RESPONSE_XPATH_INTERFACE_NAME = 'result/ifnet/entry/name'
RESPONSE_XPATH_ZONE_NAME = 'result/ifnet/entry/zone'
RESPONSE_XPATH_INTERFACE_IP = 'result/ifnet/entry/ip'
# - SHOW DEVICES CONNECTED
RESPONSE_XPATH_DEVICES_ENTRY_HOSTNAME = 'result/devices/entry/hostname'
RESPONSE_XPATH_DEVICES_ENTRY_HA_ACTIVE_HOSTNAME = "result/devices/entry/ha[state='active']/../hostname"

# - TEST ROUTING FIB-LOOKUP
RESPONSE_XPATH_RESULT_INTERFACE = 'result/interface'
RESPONSE_XPATH_RESULT_SOURCE = 'result/src'
# - GET VIRTUAL ROUTERS
RESPONSE_XPATH_VIRTUAL_ROUTER_ENTRY = 'result/virtual-router/entry'
# COMMIT
RESPONSE_XPATH_RESULT_JOB = 'result/job'
RESPONSE_XPATH_RESULT_JOB_RESULT = 'result/job/result'
RESPONSE_XPATH_RESULT_JOB_PROGRESS = 'result/job/progress'
# OPERATIONAL COMMAND RESPONSES
RESPONSE_XPATH_DEVICEGROUPS_ENTRY = 'result/devicegroups/entry'
RESPONSE_XPATH_DEVICES_ENTRY = 'devices/entry'
RESPONSE_XPATH_DEVICEGROUPS_DEVICES_ENTRY = 'result/devicegroups/entry[@name="{0}"]/devices/entry'
RESPONSE_XPATH_DEVICEGROUPS_DEVICES_ENTRY_HOSTNAME = 'result/devicegroups/entry[@name="{0}"]/devices/entry[@name="{1}"]/hostname'
RESPONSE_NODE_CONNECTED_YES = '<connected>yes</connected>'
