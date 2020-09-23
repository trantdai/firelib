import os
import re
import sys
import time

from typing import List, Union

from ..common import sshsession, util

"""
class PANSSHSession is copied from firelib.common.sshsession.
All new work should continue from here instead of from the obsolete
firelib.common.sshsession
"""


class PANSSHSession(sshsession.SSHSession):
    """
    Represents a ssh session with target PAN devices.
    connect() must be called prior to using any of the other API accessing functions.
    """

    # def __init__(self, host, dport=22, user='firewallauto',
    #             keypath=common_constants.SSH_FIREWALL_PRIVATE_KEY_PATH_PROD):
    def __init__(self, host, dport=22, user='firewallauto', keypath=None):
        # Compute keypath
        if keypath is None:
            script_path = os.path.abspath(os.path.dirname(__file__))
            fwhome = os.path.sep + os.path.join(script_path.split(os.path.sep)[1], script_path.split(os.path.sep)[2])
            keypath = os.path.join(fwhome, '.ssh', 'fw_id_rsa')

        sshsession.SSHSession.__init__(self, host, dport, user,
                                       keypath)
        self.__manager = False
        if "fwm" in host:
            self.__manager = True

    def run_pan_command(self, cmd, prompt='>'):
        """
        Execute cmd over the connected self.__chan.
        Return the outcome of the execution
        """
        self.sshchannel.send(cmd + '\n')
        output = self.read_output_buffer(prompt)
        return output

    def do_pan_traceroute(self, target):
        """
        Do traceroute on self.__host to target IP. Return trace.
        If traceroute is done on vwire firewall, return None.
        """
        traceroute = ''
        if self.__manager:
            traceroute = "traceroute host {0}".format(target)
        else:
            trace_source = self.get_forwarding_interface_address(target)
            # If vwire firewall
            if trace_source is None:
                return None
            traceroute = "traceroute source {0} host {1}".format(
                trace_source, target)
        trace = self.run_pan_command(traceroute)
        return trace

    def get_forwarding_interface_address(self, target):
        """
        - Input:
         + target: The IP address used to locate the fw interface address
        - Output: Return the forwarding interface address if firewall is layer 3
        elif firewall is vwire, return None
        """
        virtual_routers = self.get_virtual_routers()

        if len(virtual_routers) > 1:
            sys.exit("More than one VR not supported by automation!")
        elif len(virtual_routers) == 1 and virtual_routers[0] != 'vwire':
            vr = virtual_routers[0]
            #result = 'via 172.17.7.2 interface ae1.808, source 172.17.7.1, metric 10'
            result = self.test_routing_fib(vr, target)
            return result.split(', ')[1].split()[1]
        #virtual_routers[0] == 'vwire'
        else:
            return None

    def test_routing_fib(self, vr, target):
        """
        Run the command test routing fib-lookup ip {0} virtual-router {1}
        on layer3 firewall and return the result as string like:
        'via 10.10.10.2 interface ae1.10, source 10.10.10.1, metric 10'
        """
        cmd = "set cli pager off\n"
        self.run_pan_command(cmd)

        cmd = "test routing fib-lookup ip {0} virtual-router {1}\n".format(
            target, vr)
        output = self.run_pan_command(cmd)
        lines = output.split("\n")
        idx = util.get_index_of_string_list_item_that_has_pattern(
            lines, 'result:')
        # return 'via 172.17.7.2 interface ae1.808, source 172.17.7.1, metric
        # 10'
        if idx is None:
            raise RuntimeError(
                'No result found in the output test routing fib command')
        return lines[idx + 1]

    def get_virtual_routers(self):
        """
        Return all the virtual routers as a list configured on the firewall
        """
        if_dict_list = self.show_interface_logical()
        vrs = [if_dict['forwarding'].split(':')[1] for if_dict in if_dict_list
               if len(if_dict['forwarding'].split(':')) == 2]

        # Remove duplicate VRs
        vrs = list(set(vrs))

        return vrs

    def show_interface_logical(self):
        """
        Show logical interfaces. Return a list of dicts where keys are name, id, vsys, zone, forwarding, tag, address.
        For example, dict = {'name':'ae1.10', 'id':'256', 'vsys':'1', 'zone':'dmz10', 'forwarding':'vr:default',
        'tag':'10', 'address':'10.10.10.1/24'}
        """
        cmd = "set cli pager off\n"
        self.run_pan_command(cmd)
        cmd = "show interface logical\n"
        output = self.run_pan_command(cmd)
        lines = output.split("\n")
        """
        Extract only interested lines of name, id, vsys, zone,
        forwarding, tag, address
        """
        for i, v in enumerate(lines):
            if 'name' in v:
                iflines = lines[i + 2:]
                break
        if_dict_list = []
        for line in iflines:
            """
            line = 'ae1.999             256   1    dmz999
            vr:default               999    1.1.1.1/24     '
            """
            linelist = line.split()
            # Exclude junk lines at the end like '\r'
            # Upto interface name 'tunnel' is included
            linedict = None
            # For dedicated-ha, vlan, loopback, tunnel, zone column is empty,
            # thus the list has only 6 items
            if len(linelist) == 6:
                linedict = {
                    'name': linelist[0],
                    'id': linelist[1],
                    'vsys': linelist[2],
                    'zone': None,
                    'forwarding': linelist[3],
                    'tag': linelist[4],
                    'address': linelist[5]}
            if len(linelist) == 7:
                linedict = {
                    'name': linelist[0],
                    'id': linelist[1],
                    'vsys': linelist[2],
                    'zone': linelist[3],
                    'forwarding': linelist[4],
                    'tag': linelist[5],
                    'address': linelist[6]}
            if linedict is not None:
                if_dict_list.append(linedict)

        return if_dict_list

    def show_connected_devices(self):
        """
        Show all connected devices on Panorama via CLI. Return a list of devices.
        """
        cmd = "set cli pager off\n"
        self.run_pan_command(cmd)
        cmd = "show devices connected\n"
        output = self.run_pan_command(cmd)
        lines = output.split("\n")
        #fwregex = r"[a-z]{3}fw(p|t|o)\d{2,3}a"
        fwregex = r"[a-z]{3}fw(p|t|o)\d{3}a"
        devices = []
        for line in lines:
            fwa = re.search(fwregex, line.lower())
            if fwa:
                devices.append(fwa.group(0))
        return devices

    def show_firewall_interface_addresses(self):
        """
        Return a list of interface IP addresses on the firewall self.sshhost.
        """
        cmd = "set cli pager off\n"
        self.run_pan_command(cmd)
        cmd = "show interface logical\n"
        output = self.run_pan_command(cmd)
        lines = output.split("\n")
        ipregex = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        addresses = []
        for line in lines:
            ip = re.search(ipregex, line)
            if ip:
                addresses.append(ip.group(0))
        return addresses

    def toggle_paging_setting(self, off=True):
        """
        Turn the paging on/off
        """
        if off:
            cmd = "set cli pager off"
        else:
            cmd = "set cli pager on"
        return self.run_pan_command(cmd)

    def enter_configure_mode(self):
        """
        Enter configure mode
        """
        cmd = 'configure'
        prompt = '#'
        self.run_pan_command(cmd, prompt)

    def exit_configure_mode(self):
        """
        Enter configure mode
        """
        cmd = 'exit'
        #prompt = '>'
        self.run_pan_command(cmd)

    def set_cli_config_output_format(self, cliformat: str = 'set') -> None:
        """[summary]

        :param cliformat: cli format setting: default, json, set, xml
        :type cliformat: str
        """
        cmd = 'set cli config-output-format {0}'.format(cliformat)
        self.run_pan_command(cmd)

    def is_firewall_active(self):
        """
        Return True if self.sshhost is in HA active state. Else return False.
        """
        cmd = "show high-availability state | match State:"
        output = self.run_pan_command(cmd)
        line1 = output.split("\n")[0]
        if 'active' in line1.lower():
            return True
        return False

    # def grep_config_as_set_commands(self, pattern: str) -> str:
    #    """[summary]
    #
    #    :param pattern: Pattern used to search config references in config mode
    #    :type pattern: str
    #    :return: List of set command strings
    #    :rtype: str
    #    """
    #    '''
    #    # Turn cli pager off
    #    self.toggle_paging_setting()
    #    # Set config output format to set
    #    cmd = 'set cli config-output-format set'
    #    self.run_pan_command(cmd)
    #    # Enter config mode
    #    self.enter_configure_mode()
    #    '''
    #    #cmd = "show | match " + r'\b{0}\b'.format(pattern)
    #    cmd = "show | match " + r"'\b{0}\b'".format(pattern)
    #    output = self.run_pan_command(cmd, '#')
    #    '''
    #    # Exit config mode
    #    self.exit_configure_mode()
    #    # Turn cli pager back on
    #    self.toggle_paging_setting()
    #    '''
    #    # Format output by removing first line: firewallauto@fw1a#, the last line: firewallauto@fw1a#, and the 2nd last      line: [edit] from output and '\r' of each line
    #    output_list = output.split("\n")
    #    output_list = output_list[1:-2]
    #    multi_set_command_st = "\n".join([cmd.rstrip() if '\r' in cmd else cmd for cmd in output_list])
    #
    #    return multi_set_command_st

    def grep_config_as_set_commands(self, patterns: Union[str, List[str]]) -> str:
        """[summary]

        :param patterns: Pattern either str or List of strings used to search config references in config mode
        :type patterns: Union[str, List[str]]
        :return: Multi set command string
        :rtype: str
        """
        if isinstance(patterns, str):
            patterns = [patterns]

        multi_set_commands = []
        for pattern in patterns:
            cmd = "show | match " + r"'\b{0}\b'".format(pattern)
            output = self.run_pan_command(cmd, '#')
            '''
            # Exit config mode
            self.exit_configure_mode()
            # Turn cli pager back on
            self.toggle_paging_setting()
            '''
            # Format output by removing first line: firewallauto@fw1a#, the last line: firewallauto@fw1a#, and the 2nd last line: [edit] from output and '\r' of each line
            output_list = output.split("\n")
            output_list = output_list[1:-2]
            multi_set_commands.append("\n".join([cmd.rstrip() if '\r' in cmd else cmd for cmd in output_list]))

        multi_set_commands_st = "\n".join(set(multi_set_commands))
        # Remove duplicate set commands
        no_duplicates_multi_set_commands = util.remove_duplicates_from_order_list(multi_set_commands_st.split('\n'))
        return "\n".join(set(no_duplicates_multi_set_commands))

    def is_policy_disabled(self, full_policy_name: str) -> bool:
        """[summary]

        :param pansess: SSH session with Panorama/firewall
        :type pansess: PANSSHSession
        :param full_policy_name: Like 'device-group internet pre-rulebase security rules pc-auto6'
        :type full_policy_name: str
        :return: True if it is disabled else False
        :rtype: bool
        """
        policy_status = self.grep_config_as_set_commands(full_policy_name + ' disabled')
        if ' disabled yes' in policy_status:
            return True
        return False

    # PAN COMMIT

    def commit_partial(
            self,
            admin='firewallauto',
            description='Firewall-Automation',
            device_network_excluded=False,
            policy_objects_excluded=False,
            shared_object_excluded=False,
            ctrlc=True):
        """
        Assumption: SSH is already in configure mode.
        Commit any changes, send Ctrl+C to return to command prompt and returns jobid.
        """

        prompt = '#'

        # Build commit commad
        cmd = 'commit partial admin ' + admin
        if device_network_excluded:
            cmd += ' device-and-network excluded'
        if policy_objects_excluded:
            cmd += ' policy-and-objects'
        if shared_object_excluded:
            cmd += ' shared-object'
        cmd += description

        # Commit change
        result = self.run_pan_command(cmd, prompt)

        # Deal with commmit error

        # Get job id
        """
        If there is no commit error, the result should be like this:
        Commit job 3850 is in progress. Use Ctrl+C to return to command prompt
        .........55%70%.98%.......100%
        """
        # Get first line "Commit job 3850 is in progress. Use Ctrl+C to return
        # to command prompt"
        job_line = result.split('\n')[0]
        # Extract the job id
        job_id = [s for s in job_line.split() if s.isdigit()][0]

        #Send Ctrl+C ('\x03' or chr(3)) to return to command prompt #
        if ctrlc:
            cmd = chr(3)
            self.run_pan_command(cmd, prompt)

        return job_id

    def get_commit_progress(self, job_id):
        """
        Assumption: In operational mode. Get commit progress.
        Returns job progress (Completed column).
        """
        cmd = 'show jobs id {0}'.format(job_id)

        """result =
        Enqueued            Dequeued   ID   Type Status Result Completed
        -----------------------------------------------------------------
        2019/03/25 13:12:59 13:12:59 3850 Commit    ACT   PEND        70%
        """
        result = self.run_pan_command(cmd)

        # Deal with error

        # Get the commit progress in % and remove %
        job_line = result.split('\n')[2]
        job_progress = job_line.split()[-1][:-1]

        return job_progress

    def get_commit_result(self, job_id):
        """
        Assumption: In operational mode. Get commit result.
        Returns job result: OK or FAIL (Result column).
        """
        cmd = 'show jobs id {0}'.format(job_id)

        """result =
        Enqueued            Dequeued   ID   Type Status Result Completed
        -----------------------------------------------------------------
        2019/03/25 13:12:59 13:12:59 3850 Commit    ACT   PEND        70%
        """
        result = self.run_pan_command(cmd)

        # Deal with error

        # Get the commit progress in % and remove %
        job_line = result.split('\n')[2]
        job_status = job_line.split()[-2]

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
        print(('Commit finished with result: {0}\n'.format(result_str)))
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
