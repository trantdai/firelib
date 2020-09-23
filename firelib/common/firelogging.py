import logging
import sys
import os
from . import constants as common_constants


class StdoutPrint:
    """
    A class used to toggle the output destination of the print statements

    ...

    If attribute verbose is set to True, the output destination is
    sys.stdout which is terminal screen/console.
    Otherwise, the print message is sent to Null.

    Attributes:
    ---
    _stdout: sys.stdout
            an object to store original sys stdout that is console
    """

    def write(self, arg):
        pass

    @property
    def stdout(self):
        return self.stdout

    def disable_print(self):
        sys.stdout = self

    def enable_print(self):
        sys.stdout = self.stdout


class FireLogger:
    """ A class for logging all firewall automation activities
    """

    def __init__(
            self,
            name=__name__,
            filelevel=logging.DEBUG,
            consolelevel=logging.INFO,
            formatter=common_constants.DEFAULT_FORMATTER,
            logfile=common_constants.DEFAULT_LOGGING_FILE_NAME):
        self._firelogger = logging.getLogger(name)

        # Setting to logging.DEBUG means messages from debugging level
        # get logged
        self._firelogger.setLevel(logging.DEBUG)

        # Set formatter
        self._formatter = logging.Formatter(formatter)

        # Set logging level DEBUG for file and INFO for console
        self._filelevel = filelevel
        self._consolelevel = consolelevel

        # Get path to directory where file is located, not including the file
        path = os.path.abspath(os.path.dirname(__file__))
        #print('path: {0}'.format(path))
       
        fwhome = os.path.sep + \
            os.path.join(path.split(os.path.sep)[1], path.split(os.path.sep)[2])

        # Create logs directory if non-existent
        logsdir = os.path.join(fwhome, 'logs')
        if not os.path.exists(logsdir):
            os.makedirs(logsdir)

        logfile = os.path.join(
            logsdir, common_constants.DEFAULT_LOGGING_FILE_NAME)

        # Messages from level DEBUG sent to file
        fh = logging.FileHandler(logfile)
        fh.setLevel(filelevel)
        fh.setFormatter(self._formatter)
        self._firelogger.addHandler(fh)

        # Messages from level INFO sent to console
        ch = logging.StreamHandler()
        ch.setLevel(consolelevel)
        ch.setFormatter(self._formatter)
        self._firelogger.addHandler(ch)

        self._firelogger.debug(
            'Finished the initialization of FireLogger object %s', name)

    @property
    def firelogger(self):
        return self._firelogger
    """
    @firelogger.setter
    def firelogger(self, fl):
        self._firelogger = fl
    """

    @property
    def formatter(self):
        return self._formatter

    @formatter.setter
    def formatter(self, fmt):
        self._formatter = fmt

    @property
    def filelevel(self):
        return self._filelevel

    @filelevel.setter
    def filelevel(self, fll):
        self._filelevel = fll

    @property
    def consolelevel(self):
        return self._consolelevel

    @consolelevel.setter
    def consolelevel(self, cll):
        self._consolelevel = cll
