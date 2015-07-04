import logging
import lxml.etree
import lxml.objectify
import requests

API_HOST = "https://api.onelogin.com"
API_VERS = "/api/v3"
API_URL = "%s%s" % (API_HOST, API_VERS)


class OneLogin(object):
    """ OneLogin base class for common API management """

    # The URL for this OneLogin API target
    _url   = None

    # The XML cache of the OneLogin API target (for some operations)
    _cache = None


    def __init__(self, api_key):
        """ Initialize the OneLogin API, with the given API key

        Parameters:
            api_key - The API key to use when interacting with OneLogin. See
                http://developers.onelogin.com/v1.0/docs#section-get-an-api-key
        """
        # cache for calls that require listing for identification
        self._api_key = api_key
        self._conn = OneLogin.session(api_key)

        self.l = logging.getLogger(str(OneLogin.__class__))


    @staticmethod
    def session(_api_key):
        """ Create a new requests session for the OneLogin server, with the
        given API credentials.
        """
        l = logging.getLogger(str(OneLogin.__class__))
        l.info("Starting new OneLogin session with API Key: %s", _api_key)

        r = requests.Session()
        r.auth = (_api_key, "x")

        return r

    def _list(self, api_type, cls, refresh=False):
        """ Return a full list of the object represented by this APIObject.

        Parameters:
            api_type - The APIObject type to list
            refresh  - If we should reload fresh user information from the
                       OneLogin server
        Returns:
            lxml.etree.Element
        """
        if refresh or self._cache is None:
            self._reload(self._url)

        objlist = getattr(self._cache, api_type)

        return [cls.load(o.id, self._api_key) for o in objlist]


    def _filter(self, api_type, cls, search, field):
        """ Filter objects on OneLogin by some field for this APIObject type

        Parameters:
            api_type - The APIObject type to list
            search - The search term to use
            field  - The field to search on
        Return:
            [User, ...]
        """
        self.l.debug("filter (field %s): %s", field, search)

        if self._cache is None:
            self._reload()

        results = self._cache.xpath('//%s/%s[text()="%s"]/..' % (
            api_type, field, search,
        ))

        xp = [cls.load(el.id, self._api_key) for el in results]
        return xp


    def _find(self, api_type, cls, search, field):
        """ Find a single user, based on your search

        This function will return a single user, who is the first user to match
        the given search criteria

        Parameters:
            api_type - The APIObject type to list
            cls      - The class to use when instantiating in our filter
            search   - The search term to use
            field    - The field to search on
        Return:
            Users
        """
        apobj = self._filter(api_type, cls, search, field)

        if len(apobj) > 0:
            return apobj[0]

        return None


    def _reload(self, url=None):
        """ Reload OneLogin users from the OneLogin server """
        self.l.debug("reloading cache from %s", url)
        if url == None:
            url = self._url

        resp = self._conn.get(url)

        # pylint: disable=no-member
        self._cache = lxml.objectify.fromstring(resp.content)


class APIObject(object):
    """ A OneLogin API object

    See also http://developers.onelogin.com
    """
    def __init__(self, el):
        self.l = logging.getLogger(str(self.__class__))
        self.__details = el

        self._id = self._find("id").text  # pylint: disable=no-member

        self.l.info("Loaded %s", self._id)

    def __getattr__(self, key):
        f = self._find(key)
        if f is None:
            return None
        self.l.debug("getattr %s (for %s): %s", key, self._id, f.text)

        return f.text

    def _find(self, key):
        return self.__details.find(key)


class NetworkException(Exception):
    """ Exceptions on the network when preformation operations against OneLogin
    """
    pass
