"""
##############################################
*Author:   Dai Tran
*Email:    trantdaiau@gmail.com
*Project:  Firewall Automation
*Script:   Firelib Library
*Release:  Version 1
##############################################
"""


class Author:
    """
    Represent author of the script
    """

    def __init__(self, author="Dai Tran", email="trantdaiau@gmail.com",
                 project="Firewall Automation",
                 script="Firelib Library", release="Version 1",
                 shash="##############################################"):
        """
        Init author's details
        """
        self._author = author
        self._email = email
        self._project = project
        self._script = script
        self._release = release
        self._shash = shash

    def print_author(self):
        """
        Print author's and project details
        """
        scriptinfo11 = "Author:"
        scriptinfo21 = "Email:"
        scriptinfo31 = "Project:"
        scriptinfo41 = "Script:"
        scriptinfo51 = "Release:"
        scriptinfo = self._shash + "\n*{0:10s}" + self._author + "\n*{1:10s}" \
            + self._email + "\n*{2:10s}" + self._project + "\n*{3:10s}" \
            + self._script + "\n*{4:10s}" + self._release + "\n" + self._shash
        print("\n")
        print((
            scriptinfo.format(
                scriptinfo11,
                scriptinfo21,
                scriptinfo31,
                scriptinfo41,
                scriptinfo51)))
        print("")
