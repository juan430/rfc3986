# -*- coding: utf-8 -*-
from collections import namedtuple

from .exceptions import InvalidAuthority
from .misc import (
    FRAGMENT_MATCHER, PATH_MATCHER, QUERY_MATCHER, SCHEME_MATCHER,
    SUBAUTHORITY_MATCHER, URI_MATCHER, URI_COMPONENTS
    )


class URIReference(namedtuple('URIReference', URI_COMPONENTS)):
    slots = ()

    def __new__(cls, scheme, authority, path, query, fragment):
        return super(URIReference, cls).__new__(
            cls,
            scheme or None,
            authority or None,
            path or None,
            query or None,
            fragment or None)

    def __eq__(self, other):
        other_ref = other
        if isinstance(other, tuple):
            other_ref = URIReference(*other)
        elif isinstance(other, str):
            other_ref = URIReference.from_string(other)
        elif not isinstance(other, URIReference):
            raise TypeError(
                'Unable to compare URIReference() to {0}()'.format(
                    type(other).__name__))

        naive_equality = tuple(self) == tuple(other_ref)
        if not naive_equality:
            return False
        return True

    @classmethod
    def from_string(cls, uri_string):
        """Parse a URI reference from the given unicode URI string.

        :param str uri_string: Unicode URI to be parsed into a reference.
        :returns: :class:`URIReference` or subclass thereof
        """
        return URIReference(*URI_MATCHER.match(uri_string).groups())

    def authority_info(self):
        """Returns a dictionary with the ``userinfo``, ``host``, and ``port``.

        If the authority is not valid, it will raise a ``InvalidAuthority``
        Exception.

        :returns:
            ``{'userinfo': 'username:password', 'host': 'www.example.com',
            'port': '80'}``
        :rtype: dict
        :raises InvalidAuthority: If the authority is not ``None`` and can not
            be parsed.
        """
        if not self.authority:
            return {'userinfo': None, 'host': None, 'port': None}

        match = SUBAUTHORITY_MATCHER.match(self.authority)

        if match is None:
            # In this case, we have an authority that was parsed from the URI
            # Reference, but it cannot be further parsed by our
            # SUBAUTHORITY_MATCHER. In this case it must not be a valid
            # authority.
            raise InvalidAuthority(self.authority)

        return match.groupdict()

    @property
    def host(self):
        """If present, a string representing the host."""
        try:
            authority = self.authority_info()
        except InvalidAuthority:
            return None
        return authority['host']

    @property
    def port(self):
        """If present, the port (as a string) extracted from the authority."""
        try:
            authority = self.authority_info()
        except InvalidAuthority:
            return None
        return authority['port']

    @property
    def userinfo(self):
        """If present, the userinfo extracted from the authority."""
        try:
            authority = self.authority_info()
        except InvalidAuthority:
            return None
        return authority['userinfo']

    def is_valid(self):
        """Determines if the URI is valid.

        :returns: ``True`` if the URI is valid. ``False`` otherwise.
        :rtype: bool
        """
        validators = [self.authority_is_valid, self.scheme_is_valid,
                      self.path_is_valid, self.query_is_valid,
                      self.fragment_is_valid]
        return all(v() for v in validators)

    def authority_is_valid(self):
        """Determines if the authority component is valid.

        :returns: ``True`` if the authority is valid. ``False`` otherwise.
        :rtype: bool
        """
        if (self.authority is None or
                SUBAUTHORITY_MATCHER.match(self.authority)):
            return True
        return False

    def scheme_is_valid(self):
        """Determines if the scheme component is valid.

        :returns: ``True`` if the scheme is valid. ``False`` otherwise.
        :rtype: bool
        """
        if self.scheme is None or SCHEME_MATCHER.match(self.scheme):
            return True
        return False

    def path_is_valid(self):
        """Determines if the path component is valid.

        :returns: ``True`` if the path is valid. ``False`` otherwise.
        :rtype: bool
        """
        if self.path is None or PATH_MATCHER.match(self.path):
            return True
        return False

    def query_is_valid(self):
        """Determines if the query component is valid.

        :returns: ``True`` if the query is valid. ``False`` otherwise.
        :rtype: bool
        """
        if self.query is None or QUERY_MATCHER.match(self.query):
            return True
        return False

    def fragment_is_valid(self):
        """Determines if the fragment component is valid.

        :returns: ``True`` if the fragment is valid. ``False`` otherwise.
        :rtype: bool
        """
        if self.fragment is None or FRAGMENT_MATCHER.match(self.fragment):
            return True
        return False

    def unsplit(self):
        """Create a URI string from the components.

        :returns: The URI Reference reconstituted as a string.
        :rtype: str
        """
        # See http://tools.ietf.org/html/rfc3986#section-5.3
        result_list = []
        if self.scheme:
            result_list.extend([self.scheme, ':'])
        if self.authority:
            result_list.extend(['//', self.authority])
        if self.path:
            result_list.append(self.path)
        if self.query:
            result_list.extend(['?', self.query])
        if self.fragment:
            result_list.extend(['#', self.fragment])
        return ''.join(result_list)
