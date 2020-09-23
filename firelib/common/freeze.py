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


class Freeze:
    """
    Represent the Freeze event objects
    """

    def __init__(self):
        """
        Read .freeze file content that has only one line of TRUE or FALSE.
        """
        self._fullfreeze = False

        path = os.path.abspath(os.path.dirname(__file__))
        fwhome = os.path.sep + \
            os.path.join(path.split(os.path.sep)[1], path.split(os.path.sep)[2])
        freezepath = os.path.join(fwhome, '.freeze')

        freezefile = open(freezepath)
        freezedata = freezefile.read()
        freezefile.close()

        freezeline = freezedata.strip("\n")
        # print(freezeline)
        if freezeline == "TRUE":
            self._fullfreeze = True

    def get_freeze(self):
        """
        Return a boolen of True or False. If True, then complete freeze
        """
        return self._fullfreeze
