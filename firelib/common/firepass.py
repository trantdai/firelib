"""
##############################################
*Author:   Dai Tran
*Email:    trantdaiau@gmail.com
*Project:  Firewall Automation
*Script:   Common library
*Release:  Version 1.1
##############################################
"""

import base64
import os
from . import firelogging

# START LOGGING TO FILE
logger = firelogging.FireLogger(name=__name__).firelogger
logger.debug('*** Start of firepass - Firewall credential management module')


class FirePass:
    """
    Represent the API key objects
    """

    def __init__(self):
        """
        Read pointer to identify location of the key file.
        """
        self.__paloapi = ""

        coding = 'utf-8'
        # path: location of application/script
        path = os.path.abspath(os.path.dirname(__file__))
        fwhome = os.path.sep + \
            os.path.join(path.split(os.path.sep)[1], path.split(os.path.sep)[2])
        passloc_path = os.path.join(fwhome, '.credloc')
        passloc_file = open(passloc_path)
        passloc = passloc_file.read()
        passloc_file.close()

        keyfile_path = passloc.strip("\n")
        #print('keyfile_path: {0}'.format(keyfile_path))
        try:
            keyfile_file = open(keyfile_path)
            keyfile = keyfile_file.read()
            keyfile_file.close()
            enkeylines = keyfile.split("\n")
            # Pthon2 code
            #salt = base64.b64decode(enkeylines[0])
            salt = base64.b64decode(enkeylines[0]).decode(coding)
            pankeyline = base64.b64decode(enkeylines[1][len(salt):-len(salt)]).decode(coding)

            self.__paloapi = pankeyline.split(":")[1]
        except Exception as e:
            print(("Error with reading key file: {0}\n".format(e)))

    def get_palo_apikey(self):
        if self.__paloapi == "":
            print("Empty PAN API key!\n")
        return self.__paloapi
