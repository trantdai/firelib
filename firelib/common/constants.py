from datetime import datetime

# FORBIDDEN SERVICES IN OLD FIREWALL BIBLE
FORBIDDEN_SERVICES_VULNERABLE = [
    'udp/138',
    'udp/137',
    'tcp/137',
    'tcp/139',
    'tcp/2049',
    'udp/2049',
    'rpc/100003',
    'tcp/445',
    'udp/445',
    'tcp/111',
    'udp/111',
    'rpc/100000']
FORBIDDEN_SERVICES_CLEAR_TEXT = [
    'tcp/21',
    'tcp/143',
    'udp/143',
    'tcp/389',
    'tcp/110',
    'udp/110',
    'tcp/513',
    'tcp/514',
    'tcp/23',
    'udp/69',
    'tcp/161',
    'udp/161']

# SSH KEY LOCATION
SSH_PRIVATE_KEY_PATH_PROD = r'location of private ssh key'
SSH_PRIVATE_KEY_PATH_DEV = r'location of private ssh key'

SSH_FIREWALL_PRIVATE_KEY_PATH_PROD = r'location of private ssh key for key based authentication with firewall'
SSH_FIREWALL_PRIVATE_KEY_PATH_DEV = r'location of private ssh key for key based authentication with firewall'

# MANAGEMENT HOST
MGMT_HOST = 'Linux host'
PANORAMA_PRD_FQDN_HOST_A = '<name>'
PANORAMA_PRD_FQDN_HOST_B = '<name>'
PANORAMA_DEV_FQDN_HOST = '<name>'
PANORAMA_PPT_FQDN_HOST = '<name>'

# REGULAR EXPRESSION
#PAN_FIREWALL_REGEX = r"[a-z]{3}fw(p|t|o)(3|6)\d{2}"
#REGEX_PAN_FIREWALL_CLUSTER = r"[a-z]{3}fw(p|t|o)(3|6)\d{2}"
REGEX_PAN_FIREWALL_CLUSTER = r"[a-z]{3}fw(p|t|o)(3|6)\d{2,4}"
#ALL_FIREWALL_REGEX = r"[a-z]{3}fw(p|t|o)\d{2,3}"
#REGEX_ALL_FIREWALL_CLUSTER = r"[a-z]{3}fw(p|t|o)\d{2,3}"
REGEX_ALL_FIREWALL_CLUSTER = r"[a-z]{3}fw(p|t|o)\d{2,4}"
# https://stackoverflow.com/questions/14283605/issues-with-python-re-findall-when-matching-variables
REGEX_ALL_FIREWALL_CLUSTER_FINDALL = r"[a-z]{3}fw(?:p|t|o)\d{2,4}"
#IPV4_REGEX_SIMPLE = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
REGEX_IPV4_SIMPLE = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"

# DOMAIN
DOMAIN_NAME_POSTFIX_PROD = '.local.net'
DOMAIN_NAME_POSTFIX_PROD_FIREWALL = '.local.net'
CONTOSO_INTERNAL_POSTFIX_PROD = '.local.net'

# LOGGING
#DEFAULT_FORMATTER = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_FORMATTER = '%(asctime)s | %(name)s | %(levelname)-8s | %(lineno)04d | %(message)s'
DEFAULT_LOGGING_FILE_NAME = 'firewallauto_{:%Y-%m-%d}.log'.format(datetime.now())

# INPUT
INPUT_KWARG_SCRIPT = 'script'
INPUT_KWARG_RECORD = 'record'
INPUT_KWARG_FIREWALL = 'firewall'
INPUT_KWARG_FIREWALL_MANAGER = 'firewall manager'
INPUT_VALUE_PAN_FIREWALL_VENDOR = 'PAN'
