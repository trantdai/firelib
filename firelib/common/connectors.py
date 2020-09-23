"A module acts as the interface between user's CLI and automation scripts"
import collections
import importlib
import json

from . import firelogging, firepass, objects, util
from . import constants as common_constants
from ..palolib import panapi, panssh

# START LOGGING TO FILE
logger = firelogging.FireLogger(name=__name__).firelogger
logger.debug('\n***START OF CONNECTORS ***\n')

_INPUT_KWARG_SEPARATOR = ';'

# ADDRESS
_INPUT_KWARG_ADD_IP_NETMASK = 'add ip netmask'
_INPUT_KWARG_ADD_IP_RANGE = 'add ip range'
_INPUT_KWARG_ADD_IP_HOST = 'add ip host'
_INPUT_KWARG_ADD_IP_FQDN = 'add ip fqdn'
_INPUT_KWARG_ADD_IP_OBJECT = 'add ip object'
_INPUT_KWARG_ADD_IP_GROUP_OBJECT = 'add ip group object'

_INPUT_KWARG_DELETE_IP_NETMASK = 'delete ip netmask'
_INPUT_KWARG_DELETE_IP_RANGE = 'delete ip range'
_INPUT_KWARG_DELETE_IP_HOST = 'delete ip host'
_INPUT_KWARG_DELETE_IP_FQDN = 'delete ip fqdn'
_INPUT_KWARG_DELETE_IP_OBJECT = 'delete ip object'
_INPUT_KWARG_DELETE_IP_GROUP_OBJECT = 'delete ip group object'

# SERVICE
_INPUT_KWARG_ADD_SERVICE = 'add service'
_INPUT_KWARG_ADD_SERVICE_RANGE = 'add service range'
_INPUT_KWARG_ADD_SERVICE_COMPLEX = 'add service complex'
_INPUT_KWARG_ADD_SERVICE_OBJECT = 'add service object'
_INPUT_KWARG_ADD_SERVICE_GROUP_OBJECT = 'add service group object'

_INPUT_KWARG_DELETE_SERVICE = 'delete service'
_INPUT_KWARG_DELETE_SERVICE_RANGE = 'delete service range'
_INPUT_KWARG_DELETE_SERVICE_COMPLEX = 'delete service complex'
_INPUT_KWARG_DELETE_SERVICE_OBJECT = 'delete service object'
_INPUT_KWARG_DELETE_SERVICE_GROUP_OBJECT = 'delete service group object'

# URL
_INPUT_KWARG_ADD_URL = 'add url'

_INPUT_KWARG_DELETE_URL = 'delete url'

_INPUT_KWARGS_FIREOBJECTUPDATER = [
    _INPUT_KWARG_ADD_IP_NETMASK,
    _INPUT_KWARG_ADD_IP_RANGE,
    _INPUT_KWARG_ADD_IP_HOST,
    _INPUT_KWARG_ADD_IP_FQDN,
    _INPUT_KWARG_ADD_IP_OBJECT,
    _INPUT_KWARG_ADD_IP_GROUP_OBJECT,
    _INPUT_KWARG_DELETE_IP_NETMASK,
    _INPUT_KWARG_DELETE_IP_RANGE,
    _INPUT_KWARG_DELETE_IP_HOST,
    _INPUT_KWARG_DELETE_IP_FQDN,
    _INPUT_KWARG_DELETE_IP_OBJECT,
    _INPUT_KWARG_DELETE_IP_GROUP_OBJECT,
    _INPUT_KWARG_ADD_SERVICE,
    _INPUT_KWARG_ADD_SERVICE_RANGE,
    _INPUT_KWARG_ADD_SERVICE_COMPLEX,
    _INPUT_KWARG_ADD_SERVICE_OBJECT,
    _INPUT_KWARG_ADD_SERVICE_GROUP_OBJECT,
    _INPUT_KWARG_DELETE_SERVICE,
    _INPUT_KWARG_DELETE_SERVICE_RANGE,
    _INPUT_KWARG_DELETE_SERVICE_COMPLEX,
    _INPUT_KWARG_DELETE_SERVICE_OBJECT,
    _INPUT_KWARG_DELETE_SERVICE_GROUP_OBJECT,
    _INPUT_KWARG_ADD_URL,
    _INPUT_KWARG_DELETE_URL
]


class MissingArgument(RuntimeError):
    """
    Exceptions thrown on parsing invalid IP strings
    """


class InvalidArgument(ValueError):
    """
    Exceptions thrown on parsing invalid IP strings
    """


def unicode_to_utf8_hook(data, ignore_dicts=False):
    """
    Used as the object_hook callback function in the json.loads() method to
    remove the unicode format of the loaded dictionary.
    json.loads('{\n    "__class__": "IPObject", \n    "__module__": "firelib.common.objects", \n    "_instance": {\n        "__class__": "IPHost", \n        "__module__": "firelib.common.objects", \n        "_str": "1.1.1.1"\n    }\n}') or json.loads(u'{\n    "__class__": "IPObject", \n    "__module__": "firelib.common.objects", \n    "_instance": {\n        "__class__": "IPHost", \n        "__module__": "firelib.common.objects", \n        "_str": "1.1.1.1"\n    }\n}') = {u'__module__': u'firelib.common.objects', u'__class__': u'IPObject', u'_instance': {u'__module__': u'firelib.common.objects', u'_str': u'1.1.1.1', u'__class__': u'IPHost'}}
    json.loads('{\n    "__class__": "IPObject", \n    "__module__": "firelib.common.objects", \n    "_instance": {\n        "__class__": "IPHost", \n        "__module__": "firelib.common.objects", \n        "_str": "1.1.1.1"\n    }\n}', object_hook=str_hook) = {'__module__': 'firelib.common.objects', '__class__': 'IPObject', '_instance': {'__module__': 'firelib.common.objects', '_str': '1.1.1.1', '__class__': 'IPHost'}}
    """
    # if this is a unicode string, return its string representation
    if isinstance(data, str):
        return data.encode('utf-8')
    # if this is a list of values, return list of byteified values
    if isinstance(data, list):
        return [unicode_to_utf8_hook(item, ignore_dicts=True) for item in data]
    # if this is a dictionary, return dictionary of byteified keys and values
    # but only if we haven't already byteified it
    if isinstance(data, dict) and not ignore_dicts:
        return {
            unicode_to_utf8_hook(key, ignore_dicts=True): unicode_to_utf8_hook(
                value, ignore_dicts=True)
            for key, value in data.items()
        }
    # if it's anything else, return it in its original form
    return data


def convert_object_to_dict(obj):
    """
    A function takes in a custom object and returns a dictionary representation of the object.
    This dict representation includes meta data such as the object's module and class names.
    """

    #  Populate the dictionary with object meta data
    obj_dict = {
        "__class__": obj.__class__.__name__,
        "__module__": obj.__module__
    }

    #  Populate the dictionary with object properties
    obj_dict.update(obj.__dict__)

    return obj_dict


# def convert_dict_to_object(obj_dict, fromlist=None):


def convert_dict_to_object(obj_dict):
    """
    Function that takes in a dict and returns a custom object associated with the dict.
    This function makes use of the "__module__" and "__class__" metadata in the dictionary
    to know which object type to create.
    """
    obj = obj_dict
    if "__class__" in obj_dict:
        # Pop ensures we remove metadata from the dict to leave only the
        # instance arguments
        class_name = obj_dict.pop("__class__")

        # Get the module name from the dict and import it
        module_name = obj_dict.pop("__module__")

        # We use the built in __import__ function since the module name is not
        # yet known at runtime
        module = importlib.import_module(module_name)
        """
        if fromlist is not None:
            # module = __import__(module_name, fromlist=fromlist)
        else:
            module = __import__(module_name)
        """
        # Get the class from the module
        class_ = getattr(module, class_name)

        logger.debug('class_name: {0}, module_name: {1}, class_: {2}'.
                     format(class_name, module_name, class_))

        # For complex IPObject like
        # {\n    \"__class__\": \"IPObject\", \n    \"__module__\": \"firelib.common.objects\", \n    \"_instance\": {\n        \"__class__\": \"IPHost\", \n        \"__module__\": \"firelib.common.objects\", \n        \"_name\": null, \n        \"_value\": \"2.2.2.2\"\n    }\n}
        if class_name == 'IPObject' and '_instance' in obj_dict:
            # obj = class_(obj_dict['_instance']['_str'])
            obj = class_(obj_dict['_instance'])

        # For ServiceObject like
        # {\n    \"__class__\": \"ServiceObject\", \n    \"__module__\": \"firelib.common.objects\", \n    \"_instance\": {\n        \"__class__\": \"Service\", \n        \"__module__\": \"firelib.common.objects\", \n        \"_name\": null, \n        \"_port\": \"10038\", \n        \"_prot\": \"tcp\", \n        \"_sport\": null, \n        \"_value\": \"tcp/10038\"\n    }\n}
        elif class_name == 'ServiceObject' and '_instance' in obj_dict:
            obj = class_(obj_dict['_instance'])

        # For FWObject like
        # {\n    \"__class__\": \"FWObject\", \n    \"__module__\": \"firelib.common.objects\", \n    \"_name\": \"pc-auto\", \n    \"_type\": \"ip object\", \n    \"_value\": \"pc-auto\"\n}
        # elif '_type' in obj_dict:
        elif class_name == 'FWObject':
            # obj_dict: {u'_type': u'ip object', u'_str': u'pc-auto', u'_name': u'pc-auto'}
            # obj = class_(obj_dict['_str'], obj_dict['_name'], obj_dict['_type'])
            obj = class_(
                obj_dict['_value'],
                obj_dict['_name'],
                obj_dict['_type'])

        # For URLObject like
        # obj_dict: {'_hostname': 'contoso.net', '_name': None, '_path': None, '_port': None, '_type': 'url', '_value': #'contoso.net', '_wildcard': '*'}
        elif class_name == 'URLObject':
            obj = class_(
                obj_dict['_value'],
                obj_dict['_wildcard'])

        # For IPHost, IPRange, IPNetwork, Service, ServiceRange etc object like
        # {\n        \"__class__\": \"IPHost\", \n        \"__module__\": \"firelib.common.objects\", \n        \"_name\": null, \n        \"_value\": \"2.2.2.2\"\n    }\n}
        else:
            # obj = class_(obj_dict['_str'])
            logger.debug('obj_dict: {0}'.format(obj_dict))
            obj = class_(obj_dict['_value'])

        # Use dictionary unpacking to initialize the object
        # obj = class_(**obj_dict)
    # else:
    #    obj = obj_dict
    return obj


class Connector:
    def __init__(self, input_source):
        self._source = input_source
        self._indict = None
        self._script = None
        self._record = None
        self._vendor = None
        self._target_system = None
        self._target_environment = None

        self._parse_input()
        self._check_input()

    def source(self):
        return self._source

    @property
    def indict(self):
        """
        Return dictionary format input
        """
        return self._indict

    @property
    def script(self):
        return self._script

    @property
    def record(self):
        return self._record

    @property
    def vendor(self):
        return self._vendor

    @property
    def target_system(self):
        return self._target_system

    @property
    def target_environment(self):
        return self._target_environment

    @staticmethod
    def get_interactive_input(prompt):
        """
        Give the user a prompt and ask them whether to continue.
        The prompt should include something like [Y/N] at the end.
        Returns True if they confirm, false otherwise.
        """
        while True:
            check = input(prompt)
            if check.upper() == 'N':
                return False
            if check.upper() == 'Y':
                return True

    def print_input(self, heading='*** SELECTED SETTINGS ***', ignore_keys=None):
        print((heading + '\n'))
        """
        tempdict = self.indict.copy()
        print('{0}: {1}'.format('script', tempdict.pop('script')))
        if 'record' in tempdict.keys():
            print('{0}: {1}'.format('record', tempdict.pop('record')))
        if 'firewall vendor' in tempdict.keys():
            print('{0}: {1}'.format('firewall vendor', tempdict.pop(\
            'firewall vendor')))
        if 'target system' in tempdict.keys():
            print('{0}: {1}'.format('target system', tempdict.pop(\
            'target system')))
        for k, v in tempdict.items():
            if k not in ignore_keys:
                print('{0}: {1}'.format(k.lower(), v))
        print('')
        """
        if ignore_keys is None:
            ignore_keys = []

        for k, v in list(self.indict.items()):
            if k not in ignore_keys:
                # To avoid target environment: ['D', 'E', 'V']
                if k != 'target environment':
                    # Remove duplicates from list v while maintaining the order
                    unique_v = list(collections.OrderedDict.fromkeys(v))
                    # print('{0}: {1}'.format(k.lower(), v))
                    print(('{0}: {1}'.format(k.lower(), unique_v)))
                else:
                    print(('{0}: {1}'.format(k.lower(), v)))
        print('')

    def _get_check_method(self):
        return '_check_' + self.script + '_input'

    def _get_parse_method(self):
        return '_parse_' + self.script + '_input'

    def _parse_input(self):
        pass

    def _check_input(self):
        pass

    def get_json_standardized_input(
            self,
            sort_keys=True,
            indent=4,
            ensure_ascii=True):
        """
        Return JSON format based string of the input. encode('utf8') is used to
        """
        """
        # In Python2 json.dumps().encode('utf8') generate str  but in Python3 it generates bytes object
        # like b'{"1": "one", "2": "two"}'
        return json.dumps(self.indict, sort_keys=sort_keys, indent=indent,
                          ensure_ascii=ensure_ascii).encode('utf8')
        """
        return json.dumps(self.indict, sort_keys=sort_keys, indent=indent,
                          ensure_ascii=ensure_ascii)

    @staticmethod
    def serialize_custom_object_to_json(
            obj,
            default=convert_object_to_dict,
            sort_keys=True,
            indent=4,
            ensure_ascii=True):
        """
        def serialize_custom_object_to_json(obj, default=\
        util.convert_object_to_dict, sort_keys=True, indent=4, ensure_ascii=False):
        """
        return json.dumps(obj, default=default, sort_keys=sort_keys,
                          indent=indent, ensure_ascii=ensure_ascii)

    @staticmethod
    def deserialize_json_to_custom_object(dict_json,
                                          object_hook=convert_dict_to_object):
        """
        def deserialize_json_to_custom_object(dict_json, \
        object_hook=util.convert_dict_to_object):
        """
        return json.loads(dict_json, object_hook=object_hook)


class TerminalConnector(Connector):
    def __init__(self, args, input_source='terminal'):
        logger.debug('Input from terminal: {0}'.format(' '.join(args)))
        # print('args: {0}'.format(args))
        self._args = args
        Connector.__init__(self, input_source)

    def _parse_input(self):
        # indict = {}
        self._indict = collections.OrderedDict()
        for arg in self._args:
            # if IPs containing periods (.) separated by command
            # if (_INPUT_KWARG_SEPARATOR in arg.split("=")[1] and
            # '.' in arg.split("=")[1]):
            # If multiple values provided per key like add ip host=1.1.1.1;1.1.1.2
            # or add service=tcp/80;tcp/443
            # print('arg: {0}'.format(arg))
            if _INPUT_KWARG_SEPARATOR in arg.split("=")[1]:
                if arg.split("=")[0].strip().lower() in list(self._indict.keys()):
                    self._indict[arg.split("=")[0].strip().lower()] += \
                        [x.strip() for x in
                         arg.split("=")[1].split(_INPUT_KWARG_SEPARATOR)]
                else:
                    self._indict[arg.split("=")[0].strip().lower()] = \
                        [x.strip() for x in
                         arg.split("=")[1].split(_INPUT_KWARG_SEPARATOR)]
            # If single value provided per key
            else:
                if arg.split("=")[0].strip().lower() in list(self._indict.keys()):
                    self._indict[arg.split("=")[0].strip().lower()] += \
                        [arg.split("=")[1].strip()]
                else:
                    self._indict[arg.split("=")[0].strip().lower()] = \
                        [arg.split("=")[1].strip()]

        # Remove duplicate values of IPs/networks/ranges or services
        # from action list
        for action, list_item in list(self._indict.items()):
            self._indict[action] = list(
                collections.OrderedDict.fromkeys(list_item))

        logger.debug('Input dict: %s', json.dumps(self._indict))
        # print('Input dict: {0}'.format(self._indict))

        if 'script' in list(self._indict.keys()):
            self._script = self._indict['script'][0]

        if 'record' in list(self._indict.keys()):
            self._record = self._indict['record'][0]

        if 'firewall vendor' in list(self._indict.keys()):
            self._vendor = self._indict['firewall vendor']

            self._set_target_environment_systems()

        try:
            script_parse_method = getattr(self, self._get_parse_method())
        except AttributeError:
            raise InvalidArgument(
                "\n\n*** Error: Argument 'script': invalid value given! ***\n")
        script_parse_method()

    def _check_input(self):
        if self.script is None:
            raise MissingArgument(
                '\n\n*** Error: Missing required argument: script=<script name>! ***\n')

        if 'target system' not in self.indict and 'target environment' not in self.indict:
            raise MissingArgument(
                '\n\n*** Error: Missing required argument: At least one argument "target system=<target system>" or "target environment=<target environment>" is required! ***\n')

        if self.target_environment:
            if self.target_environment[0].upper() not in ['DEV', 'PPT', 'PRD']:
                raise InvalidArgument(
                    "\n\n*** Error: Argument 'target enviroment' only accepts one of 3 case insensitive values: 'DEV', 'PPT', or 'PRD'! ***\n")
            if len(self.target_environment) > 1:
                raise InvalidArgument(
                    "\n\n*** Error: Argument 'target enviroment': more than 1 system given! ***\n")

        if self.target_system and len(self.target_system) > 2:
            raise InvalidArgument(
                "\n\n*** Error: Argument 'target system': more than 2 systems given! ***\n")

        try:
            script_check_method = getattr(self, self._get_check_method())
        except AttributeError:
            raise InvalidArgument(
                "\n\n*** Error: Argument 'script': invalid value given! ***\n")
        script_check_method()

    def _set_target_environment_systems(self):
        """
        Set correct target systems and execution environment (target environment)
        DEV and/or PROD from user input 'firewall vendor' and 'target system'
        """
        if 'target system' in list(self.indict.keys()):
            self._target_system = self.indict['target system']
        else:
            self._target_system = None

        # Only use target env when target system is not provided
        if not self._target_system:
            # Value of 'target environment' can be DEV, PPT, or PRD
            if 'target environment' in list(self.indict.keys()):
                self._target_environment = self.indict['target environment']
            else:
                self._target_environment = None

    def _parse_fireobjectupdater_input(self):
        """
        self._add_object_list = []
        self._delete_object_list = []
        """
        add_object_list = []
        delete_object_list = []
        self._action_list = []

        self._set_target_environment_systems()
        if 'target object' in list(self.indict.keys()):
            self._target_object = self.indict['target object']
        else:
            self._target_object = None

        for action, list_item in list(self.indict.items()):
            logger.debug('action in self.indict.keys(): {0}'.format(action))
            # Remove duplicate values of IPs/networks/ranges or services
            # from action list
            logger.debug("{0}: {1}".format(action, list_item))
            if 'delete ip' in action.lower():
                logger.debug('delete - self.indict[action]: {0}'.format(
                    self.indict[action]))
                # for address in self.indict[action]:
                for address in list_item:
                    if 'object' in action.lower():
                        if 'ip object' in action.lower():
                            obj_type = 'ip object'
                        else:
                            obj_type = 'ip group object'
                        ipobj = objects.FWObject(address, address, obj_type)
                    else:
                        ipobj = objects.IPObject(address)
                    serialized_ipobject = self.serialize_custom_object_to_json(
                        ipobj)
                    delete_object_list.append(serialized_ipobject)
            elif 'add ip' in action.lower():
                logger.debug('add - self.indict[action]: {0}'.format(
                    self.indict[action]))
                for address in list_item:
                    if 'object' in action.lower():
                        if 'ip object' in action.lower():
                            obj_type = 'ip object'
                        else:
                            obj_type = 'ip group object'
                        ipobj = objects.FWObject(address, address, obj_type)
                    else:
                        ipobj = objects.IPObject(address)
                    serialized_ipobject = self.serialize_custom_object_to_json(
                        ipobj)
                    add_object_list.append(serialized_ipobject)
            # If 'add service', 'add service range', 'add service object',
            # 'delete service complex',
            elif 'service' in action.lower():
                logger.debug(
                    'action: {0}, services: {1}'.format(
                        action, self.indict[action]))
                for service in list_item:
                    if 'object' in action.lower():
                        if 'service object' in action.lower():
                            obj_type = 'service object'
                        else:
                            obj_type = 'service group object'
                        serviceobj = objects.FWObject(
                            service, service, obj_type)
                    else:
                        serviceobj = objects.ServiceObject(service)
                    serialized_serviceobj = self.serialize_custom_object_to_json(
                        serviceobj)
                    logger.debug(
                        'service serialized_serviceobj: {0}'.format(serialized_serviceobj))
                    if 'add' in action.lower():
                        logger.debug('add - self.indict[action]: {0}'.format(
                            self.indict[action]))
                        add_object_list.append(serialized_serviceobj)
                    elif 'delete' in action.lower():
                        delete_object_list.append(serialized_serviceobj)
            # If 'add url', 'delete url' is in action
            elif 'url' in action.lower():
                logger.debug(
                    'action: {0}, urls: {1}'.format(
                        action, self.indict[action]))
                for url in list_item:
                    urlobj = objects.URLObject(url)
                    serialized_urlobj = self.serialize_custom_object_to_json(
                        urlobj)
                    logger.debug(
                        'url serialized_urlobj: {0}'.format(serialized_urlobj))
                    if 'add' in action.lower():
                        add_object_list.append(serialized_urlobj)
                    elif 'delete' in action.lower():
                        delete_object_list.append(serialized_urlobj)

            logger.debug(
                'add_object_list: {0}, delete_object_list: {1}'.format(
                    add_object_list, delete_object_list))
            if 'add' in action or 'delete' in action:
                self._action_list.append(action)
        # Remove duplicates from addition and deletion lists while
        # maintaining the order
        # self._indict['addition'] = list(collections.OrderedDict.fromkeys(add_object_list))
        # self._indict['deletion'] = list(collections.OrderedDict.fromkeys(delete_object_list))
        # logger.debug("self._indict['addition']: {0}, self._indict['deletion']: {1}".format(self._indict['addition'], self._indict['deletion']))
        self._indict['addition'] = add_object_list
        self._indict['deletion'] = delete_object_list

    def _check_fireobjectupdater_input(self):
        # if self.script is None:
        #    raise MissingArgument(
        #        '\n\n*** Error: Missing required argument: script=<script name>! ***\n')

        if self.record is None:
            if 'show' not in self._indict:
                raise MissingArgument(
                    '\n\n*** Error: Missing required argument: record=<ticket number>! ***\n')
        elif not self.record.isdigit():
            raise InvalidArgument(
                "\n\n*** Error: Argument 'record': given value is not numeric! ***\n")

        if self.vendor is None:
            raise MissingArgument(
                "\n\n*** Error: Missing required argument: 'firewall vendor'=<vendor name(s)>! ***\n")

        if self._target_object is None:
            raise MissingArgument(
                "\n\n*** Error: Missing required argument: 'target object=<target object name>'! ***\n")

        if len(self._target_object) > 1:
            raise InvalidArgument(
                "\n\n*** Error: Argument 'target object': only one value accepted! ***\n")

        logger.debug('self._action_list: {0}'.format(self._action_list))
        logger.debug('_INPUT_KWARGS_FIREOBJECTUPDATER: {0}'.format(
            _INPUT_KWARGS_FIREOBJECTUPDATER))

        logger.debug('set(self._action_list) - set(_INPUT_KWARGS_FIREOBJECTUPDATER): {0}'.format(
            set(self._action_list) - set(_INPUT_KWARGS_FIREOBJECTUPDATER)))

        if len(set(self._action_list) - set(_INPUT_KWARGS_FIREOBJECTUPDATER)) != 0:
            raise InvalidArgument(
                '\n\n*** Error: Invalid action keywords given!  ***\n')

    def _parse_vpndeco_input(self):
        """ Parse self.indict['peer'] to create a dictionary of peers.
        Each key in the dictionary is a firewall cluster name.
        Each key value is the list of namedtuples of maptag,mapid,peerip

        Returns: dictionary of peers

        """

        # New keys of peer_dict will get default value of list that is []
        peer_dict = collections.defaultdict(list)
        if 'peer' in list(self.indict.keys()):
            # List of strings 'maptag,mapid,peerip'
            in_peers = self.indict['peer']
            # peer = 'maptag,mapid,peerip'
            for peer in in_peers:
                single_peer_list = peer.split(',')
                PeerTuple = collections.namedtuple(
                    'peer', 'maptag, mapid, peerip')
                peertuple = PeerTuple(single_peer_list[0], single_peer_list[1],
                                      single_peer_list[2])
                # Extract firewall clustername as list from maptag
                clustername = util.get_firewall_names_from_string(
                    single_peer_list[0])
                if len(clustername) != 1:
                    raise InvalidArgument(
                        "\n\n*** Error: Invalid firewall name found in crypto map tag! ***\n")

                # If firewall name already exists in peer dict as a key,
                # just append peer tuple to the value of that key
                # if fwname in peer_dict.keys():
                peer_dict[clustername[0]].append(peertuple)

        self._indict['peer_dict'] = peer_dict

    def _parse_pancleanbuilder_input(self) -> None:
        """ Parse the 'address' and 'included range' arguments
        into the lists of IPObjects or FWObjects
        """
        clean_address_object_list = []
        included_range_object_list = []
        self._action_list = []

        self._set_target_environment_systems()

        for action, list_item in list(self.indict.items()):
            logger.debug('action in self.indict.keys(): {0}'.format(action))
            logger.debug("{0}: {1}".format(action, list_item))
            if 'clean' in action.lower():
                logger.debug('clean address - self.indict[action]: {0}'.format(
                    self.indict[action]))
                for address in list_item:
                    if 'object' in action.lower():
                        if 'ip object' in action.lower():
                            obj_type = 'ip object'
                        else:
                            obj_type = 'ip group object'
                        ipobj = objects.FWObject(address, address, obj_type)
                    else:
                        ipobj = objects.IPObject(address)
                    serialized_ipobject = self.serialize_custom_object_to_json(
                        ipobj)
                    clean_address_object_list.append(serialized_ipobject)
            if 'include' in action.lower():
                logger.debug('include range - self.indict[action]: {0}'.format(
                    self.indict[action]))
                for address in list_item:
                    ipobj = objects.IPObject(address)
                    serialized_ipobject = self.serialize_custom_object_to_json(
                        ipobj)
                    included_range_object_list.append(serialized_ipobject)

            logger.debug(
                'clean_address_object_list: {0}, included_range_object_list: {1}'.format(
                    clean_address_object_list, included_range_object_list))
            if 'clean' in action or 'include' in action:
                self._action_list.append(action.lower())
        self._indict['clean'] = clean_address_object_list
        self._indict['include'] = included_range_object_list

    def _check_pancleanbuilder_input(self):
        if self.record is None:
            if 'show' not in self._indict:
                raise MissingArgument(
                    '\n\n*** Error: Missing required argument: record=<ticket number>! ***\n')
        elif not self.record.isdigit():
            raise InvalidArgument(
                "\n\n*** Error: Argument 'record': given value is not numeric! ***\n")

        if self.target_system and len(self.target_system) > 1:
            raise InvalidArgument(
                '\n\n*** Error: Argument "target system": more than 1 system given! ***\n')

        if len(self._indict['clean']) == 0:
            raise InvalidArgument(
                '\n\n*** Error: Address(es) to be cleaned up are missing! ***\n')

        if len(self._indict['clean']) > 1 and len(self._indict['include']) > 0:
            raise InvalidArgument(
                '\n\n*** Error: Argument "include range" is only allowed when cleaning up one IP address or range! ***\n')

        logger.debug('self._action_list: {0}'.format(self._action_list))
        logger.debug('set(self._action_list) - set(INPUT_KWARGS): {0}'.format(
            set(self._action_list) - set(['clean address', 'include range'])))
        if len(set(self._action_list) - set(['clean address', 'include range'])) != 0:
            raise InvalidArgument(
                '\n\n*** Error: Invalid action keywords given!  ***\n')


class FileConnector:
    pass


class WINAConnector:
    pass


class FWConnector:
    def __init__(self, hostname, host_type, vendor, os='default'):
        """
        Parameters
        ----------
        hostname: str
                                        Name of the firewall system in short or FQDN form
        host_type: str
                                        Either firewall 'device' or firewall 'manager'
        vendor: str
                                        Either 'PAN' or 'different vendor'
        os: str
                                        Either 'default' or firewall os version number
        """
        if '.' in hostname:
            self._hostname = hostname
        else:
            self._hostname = util.append_postfix(
                hostname, common_constants.DOMAIN_NAME_POSTFIX_PROD_FIREWALL)
        self._host_type = host_type
        self._vendor = vendor
        self._session = None
        self._os = os

    @property
    def hostname(self):
        return self._hostname

    @property
    def host_type(self):
        return self._host_type

    @property
    def vendor(self):
        return self._vendor

    @property
    def session(self):
        return self._session


class FWAPIConnector(FWConnector):
    def __init__(self, hostname, host_type, vendor, os='default'):
        """
        Parameters
        ----------
        hostname: str
                                        Name of the firewall system in short or FQDN form
        host_type: str
                                        Either firewall 'firewall' or firewall 'manager'
        vendor: str
                                        Either 'PAN' or 'different vendor'
        os: str
                                        Either 'default' or firewall os version number
        """
        FWConnector.__init__(self, hostname, host_type, vendor, os)
        session = None
        if vendor.upper() == 'PAN':
            """
            if host_type.lower() == 'manager':
                            session = panoapi.PanoramaAPISession(hostname)
            else:
                            session = panfwapi.PanFWAPISession(hostname)
            """
            session = panapi.PANAPISession(hostname, host_type, os)
        self._session = session


class FWSSHConnector(FWConnector):
    # def __init__(self, hostname, vendor, host_type=None):
    def __init__(self, hostname, host_type, vendor, os='default'):
        """
        Parameters
        ----------
        hostname: str
                                        Name of the firewall system in short or FQDN form
        host_type: str
                                        Either firewall 'firewall' or firewall 'manager'
        vendor: str
                                        Either 'PAN' or 'other vendor'
        """
        """
        self._hostname = hostname
        self._host_type = host_type
        self._vendor = vendor
        """
        FWConnector.__init__(self, hostname, host_type, vendor)
        session = None
        if vendor.upper() == 'PAN':
            session = panssh.PANSSHSession(hostname)
            # Establish SSH session via SSH key
            session.connect_ssh_key()
            '''
            Clear the intial message starting with 'Last login:' generated after the first login.
            '''
            session.read_output_buffer('>')
        self._session = session
