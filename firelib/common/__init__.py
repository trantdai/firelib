
# This is a hack to get rid of the warning message since we don't perform
# SSL verification when connecting to the firewall API. In Sydney at least
# the SSL certificate check will fail if we perform verification.

import requests

try:
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
except:  # pylint: disable=bare-except
    pass
