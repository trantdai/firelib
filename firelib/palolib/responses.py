import xml.etree.ElementTree as ET

from .errors import Error


class Response:
    """
    Base class for responses from the API
    """

    def __init__(self, xml):
        self._root = ET.fromstring(xml)

    @property
    def root(self):
        return self._root

    def status(self):
        return self._root.attrib['status']

    def ok(self):
        return self.status() == "success"

    def get_error_code(self):
        if 'code' in self._root.attrib:
            return self._root.attrib['code']
        return None

    def get_error(self):
        code = self.get_error_code()
        return Error(code) if code is not None else None
