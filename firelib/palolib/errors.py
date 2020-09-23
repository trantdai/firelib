_ERRORS = {
    '1': ('Unknown command', 'The specific config or operational command is not recognized.'),
    '2': ('Internal errors', 'Check with technical support when seeing these errors.'),
    '3': ('Internal errors', 'Check with technical support when seeing these errors.'),
    '4': ('Internal errors', 'Check with technical support when seeing these errors.'),
    '5': ('Internal errors', 'Check with technical support when seeing these errors.'),
    '6': ('Bad Xpath', 'The xpath specified in one or more attributes of the command is invalid. Check the API browser for proper xpath values.'),
    '7': ('Object not present', "Object specified by the xpath is not present. For example, entry[@name='value'] where no object with name 'value' is present."),
    '8': ('Object not unique', 'For commands that operate on a single object, the specified object is not unique.'),
    '10': ('Reference count not zero', 'Object cannot be deleted as there are other objects that refer to it. For example, address object still in use in policy.'),
    '11': ('Internal error', 'Check with technical support when seeing these errors.'),
    '12': ('Invalid object', 'Xpath or element values provided are not complete.'),
    '14': ('Operation not possible', 'Operation is allowed but not possible in this case. For example, moving a rule up one position when it is already at the top.'),
    '15': ('Operation denied', 'Operation is allowed. For example, Admin not allowed to delete own account, Running a command that is not allowed on a passive device.'),
    '16': ('Unauthorized', 'The API role does not have access rights to run this query.'),
    '17': ('Invalid command', 'Invalid command or parameters.'),
    '18': ('Malformed command', 'The XML is malformed.'),
    '19': ('Success', 'Command completed successfully.'),
    '20': ('Success', 'Command completed successfully.'),
    '400': ('Bad request', 'A required parameter is missing, an illegal parameter value is used.'),
    '403': ('Forbidden', 'Authentication or authorization errors including invalid key or insufficient admin access rights.'),
}


class Error:
    def __init__(self, code):
        self.code = str(code)
        if self.code in _ERRORS:
            (self.name, self.desc) = _ERRORS[self.code]
        else:
            self.name = "Unknown"
            self.desc = "Unknown"

    def __str__(self):
        return 'Error: {0} - {1}: {2}'.format(self.code, self.name, self.desc)
