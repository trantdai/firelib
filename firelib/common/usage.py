"""
##############################################
*Author:   Dai Tran
*Email:    trantdaiau@gmail.com
*Project:  Firewall Automation
*Script:   Common library
*Release:  Version 1.1
##############################################
"""
import os


class Usage:
    """
    Represent the automation application usage
    """

    def __init__(self, app_name):
        """
        app_name: name of the application whose usage needs to be shown
        usage: a number (string) showing the number of times app_name has been triggered
        location: absolute path of usage.txt file
        """
        self.app_name = app_name
        self.usage = 0
        #self.location = location
        path = os.path.abspath(os.path.dirname(__file__))
        fwhome = os.path.sep + \
            os.path.join(path.split(os.path.sep)[
                         1], path.split(os.path.sep)[2])
        usage_path = os.path.join(fwhome, 'usage.txt')
        #print('usage_path: {0}'.format(usage_path))
        self.location = usage_path

    def show_current_usage(self):
        try:
            fusage = open(self.location, 'r')
        except Exception:
            print("Reading usage stats in development... ")
            self.location = 'usage.txt'
            fusage = open(self.location, 'r')
        for line in fusage:
            if line.lower().startswith(self.app_name.lower()):
                lst = line.rstrip().split(':')
                self.usage = int(lst[1])
                break
        fusage.close()
        print(("Current {0} usage stats: {1}".format(
            self.app_name, self.usage)))

    def update_current_usage(self):
        try:
            fold = open(self.location, 'r')
        except Exception:
            print("Reading usage stats in development... ")
            self.location = 'usage.txt'
            fold = open(self.location, 'r')
        # pylint: disable=unused-variable
        dirname, basename = os.path.split(self.location)
        # pylint: enable=unused-variable
        new_path = os.path.join(dirname, "usage-new.txt")
        fnew = open(new_path, 'w')
        for line in fold:
            if line.lower().startswith(self.app_name.lower()):
                lst = line.rstrip().split(':')
                lst[1] = str(int(lst[1]) + 1)
                if self.usage == 0:
                    self.usage = int(lst[1])
                line = ":".join(lst)
                line += "\n"
            fnew.write(line)
        fold.close()
        fnew.close()
        os.remove(self.location)
        os.rename(new_path, self.location)
        self.usage += 1
        print(("Updated {0} usage stats: {1}".format(
            self.app_name, self.usage)))
