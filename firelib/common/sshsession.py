"""
##############################################
*Author:   Dai Tran
*Email:    trantdaiau@gmail.com
*Project:  Firewall Automation
*Script:   Common library
*Release:  Version 1.1
##############################################
"""

import sys
import time
import paramiko
from . import firelogging, util
from . import constants as common_constants

# START LOGGING TO FILE
logger = firelogging.FireLogger(name=__name__).firelogger
logger.debug(
    '*** Start of sshsession.py - SSH connection management module ***')


class InvalidAuthenticationError(ValueError):
    pass


class BadReturnValueError(ValueError):
    pass


class NotConnectedError(AssertionError):
    pass


class BadHTTPResponseError(RuntimeError):
    pass


class SSHSession:
    """
    Represents a ssh session with target hosts.
    connect() must be called prior to using any of the other API accessing functions.
    """

    def __init__(self, host, dport=22, user='fireauto',
                 keypath=common_constants.SSH_PRIVATE_KEY_PATH_PROD):
        """
        host is the SSH target host name or IP address to be connected to.
        If SSH connection is based username/password, keypath is set to None.
        """
        self._host = util.append_postfix(
            host, common_constants.DOMAIN_NAME_POSTFIX_PROD_FIREWALL)
        self._dport = dport
        self._user = user
        # Copied from firepath_fork_initial_backup
        self._sshclient = None
        self._chan = None
        # If SSH connection is based username/password, keypath is set to None
        if keypath:
            try:
                """
                print('Retrieving private key from {0} for the SSH connection to {1}...\n'.\
                format(keypath, host))
                """
                keyfile = open(keypath)
            except IOError:
                devkeypath = r'id_rsa'
                """
                print('No permission for accessing {0}!\nRetrieving the key from {1} instead...\n'.\
                format(keypath, devkeypath))
                """
                keyfile = open(devkeypath)

            if keyfile:
                sshkey = paramiko.RSAKey.from_private_key(keyfile)
                self._sshkey = sshkey
                keyfile.close()
            else:
                print('Unable to retrieve SSH private key. Automation aborted!\n')
                sys.exit(1)

    def __del__(self):
        """
        Close SSH channel and connection
        """
        self.disconnect_ssh_session()

    # Copied from firepath_fork_initial_backup
    @property
    def sshhost(self):
        return self._host

    @sshhost.setter
    def sshhost(self, h):
        self._host = h

    @property
    def sshchannel(self):
        return self._chan

    def connect_user_pwd(self, user, pwd):
        """
        Connect to the shared management server with the given credentials.
        Must be called successfully before using any of the other accessing functions.
        Return the connected SSH channel.
        """
        """
        logging.info("Begin")
        logging.getLogger("paramiko").setLevel(logging.DEBUG)
        """
        ssh = paramiko.SSHClient()
        self._sshclient = ssh
        # print(ssh)
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # print("AutoAdDPolicy")
        tries = attempts = 3
        while attempts > 0:
            try:
                #print("trying connect...")
                ssh.connect(
                    self._host,
                    self._dport,
                    username=user,
                    password=pwd,
                    pkey=None,
                    compress=True,
                    look_for_keys=False)
                break
            except Exception as e:
                print(("Fail to connect to {0}. The error was {1}.\n".format(self._host, e)))
                attempts -= 1
                # Try the HA peer instead
                peer = self._host.split('.')[0][:-1]
                if self._host.split('.')[0][-1] == 'a':
                    peer += 'b'
                else:
                    peer += 'a'
                self._host = peer + \
                    common_constants.DOMAIN_NAME_POSTFIX_PROD_FIREWALL
                # time.sleep(0.5)
                time.sleep(0.25)
        if not attempts:
            print(("Tried {0} times and failed, exiting...\n".format(tries)))
            sys.exit()
        #self._chan = ssh.get_transport().open_session()
        self._chan = ssh.invoke_shell()

    # Copied from firepath_fork_initial_backup
    @staticmethod
    def connect_target_user_pwd(target, port, user, pwd, keypath=None):
        """
        Connect to the "target" using the given credentials.
        Return the connected child nested SSH channel.
        """
        childsess = SSHSession(target, dport=port, user=user, keypath=keypath)
        # print(childsess)
        childsess.connect_user_pwd(user, pwd)
        return childsess

    @staticmethod
    def get_ha_peer_name(firewall):
        """
        Parameters
        ----------
        firewall: str
                FQDN of the firewall to activate/deactivate rule permit any any

        Return
        ------
        str
                Name of HA peer
        """
        # Remove 'a' or 'b' bit
        fwname = firewall.split('.')[0][:-1]
        ha_part = firewall.split('.')[0][-1].lower()

        peername = ''
        if ha_part == 'a':
            peername = fwname + 'b' + common_constants.DOMAIN_NAME_POSTFIX_PROD_FIREWALL
        else:
            peername = fwname + 'a' + common_constants.DOMAIN_NAME_POSTFIX_PROD_FIREWALL

        return peername

    def connect_ssh_key(self):
        """
        Connect to the target host using ssh key
        """
        ssh = paramiko.SSHClient()
        self._sshclient = ssh
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        tries = attempts = 3
        while attempts > 0:
            try:
                #print("trying connect...")
                ssh.connect(
                    self._host,
                    self._dport,
                    username=self._user,
                    pkey=self._sshkey)
                break
            except Exception as e:
                print((
                    "There was a problem connecting to {0} via ssh, error was: {1}".format(
                        self._host, e)))
                attempts -= 1
                # time.sleep(0.5)
                time.sleep(0.25)
        if not attempts:
            print(("Tried {0} times and failed, exiting".format(tries)))
            sys.exit()
        self._chan = ssh.invoke_shell()

    def disconnect_ssh_session(self):
        """
        Close SSH channel and connection
        """
        if self._chan:
            self._chan.close()
        if self._sshclient:
            self._sshclient.close()

    def exit_ssh_session(self, cmd='exit'):
        """
        Exit the SSH session using explicit cmd and close SSH channel and connection
        """
        if self._chan:
            self._chan.send(cmd + '\n')
        self.disconnect_ssh_session()

    def _check_connected(self):
        if self._chan is None:
            raise NotConnectedError("Need to connect() first")

    def read_output_buffer(self, prompt='$', sleeptime=0.15):
        """
        Read SSH output buffer after SSH connection is established or a command executed.
        Called after connect() and return the read output.
        """
        self._check_connected()
        output = ''
        while not output.endswith(prompt + ' '):
            # while not output.endswith(prompt + ' ') or '<--- More --->' not
            # in output:
            if self._chan.recv_ready():
                # https://stackoverflow.com/questions/13979764/python-converting-sock-recv-to-string
                # https://stackoverflow.com/questions/40235855/python-convert-string-to-byte
                # Code works in Python2
                #resp = self._chan.recv(9999)
                # In Python3, it's are byte string that needs to be decoded to Unicode
                resp = self._chan.recv(9999).decode('utf-8')
                output += resp
                # if '<--- More --->' in resp and prompt == '#':
                if '<--- More --->' in resp:
                    """
                    Sending 'qs\n' to avoid read_output_buffer(prompt) action hangs
                    at '<--- More --->'. See firepath for more details.
                    """
                    # self._chan.send('qs\n')
                    self._chan.send('qs\n'.encode('utf-8'))
                # print(resp)
            else:
                continue
                #print('output: {0}'.format(output))
            # time.sleep(0.25)
            time.sleep(sleeptime)
        return output

    def run_command(self, cmd):
        """
        Execute cmd over the connected self._chan.
        Return the outcome of the execution
        """
        self._chan.send(cmd + '\n')
        output = self.read_output_buffer()
        return output

    def do_traceroute(self, target):
        """
        Inputs: target
        Output: traceroute
        """
        # For muccws09
        #traceroute = "/usr/sbin/traceroute {0}".format(target)
        # For muccws11
        traceroute = "/bin/traceroute {0}".format(target)
        #print("Perform traceroute from {} to source {}...".format(host, source))
        trace = self.run_command(traceroute)
        #print("Parsing traceroute output...")
        return trace

    def resolve_ips_to_hostnames(self, iplist):
        """
        Input: Establised SSH session and mixed list of IP addresses and hostnames
        Output: List of unresolved addresses and hostnames
        """
        for (i, iphost) in enumerate(iplist):
            if util.is_ip_address(iphost):
                nslookup = "nslookup {0}".format(iphost)
                output = self.run_command(nslookup)
                lines = output.split("\n")
                for line in lines:
                    if "NXDOMAIN" in line:
                        break
                    if "name =" in line:
                        iplist[i] = line.split()[-1][:-1]
                        break
                    else:
                        continue
        return iplist

    def resolve_fqdn_to_ip(self, fqdn):
        """Resolve single fqdn to IP address

        Args:
                fqdn (str): Fully qualified domain name

        Returns:
                str: IP string if DNS resolution is successful
                None: if DNS resolution is not successful

        """
        nslookup = "nslookup {0}".format(fqdn)
        output = self.run_command(nslookup)
        lastline = output.split("\n")[-1]
        if 'Address' in lastline:
            ip = lastline.split(':')[1]
            return ip
        return None
