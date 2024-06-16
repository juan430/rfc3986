"""Module containing the implementation of the IRIReference class."""
# Copyright (c) 2014 Rackspace
# Copyright (c) 2015 Ian Stapleton Cordasco
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import typing as t

from . import compat
from . import exceptions
from . import misc
from . import normalizers
from . import uri
from ._typing_compat import Self as _Self


try:
    import idna
except ImportError:  # pragma: no cover
    idna = None


class IRIReference(misc.URIReferenceBase, uri.URIMixin):
    """Immutable object representing a parsed IRI Reference.

    Can be encoded into an URIReference object via the procedure
    specified in RFC 3987 Section 3.1

     .. note::
        The IRI submodule is a new interface and may possibly change in
        the future. Check for changes to the interface when upgrading.
    """

    encoding: str

    def __new__(
        cls,
        scheme: t.Optional[str],
        authority: t.Optional[str],
        path: t.Optional[str],
        query: t.Optional[str],
        fragment: t.Optional[str],
        encoding: str = "utf-8",
    ):
        """Create a new IRIReference."""
        ref = super().__new__(
            cls,
            scheme or None,
            authority or None,
            path or None,
            query,
            fragment,
        )
        ref.encoding = encoding
        return ref

    __hash__ = tuple.__hash__

    def __eq__(self, other: object):
        """Compare this reference to another."""
        other_ref = other
        if isinstance(other, tuple):
            other_ref = type(self)(*other)
        elif not isinstance(other, IRIReference):
            try:
                other_ref = self.from_string(other)
            except TypeError:
                raise TypeError(
                    "Unable to compare {}() to {}()".format(
                        type(self).__name__, type(other).__name__
                    )
                )

        # See http://tools.ietf.org/html/rfc3986#section-6.2
        return tuple(self) == tuple(other_ref)

    def _match_subauthority(self) -> t.Optional[t.Match[str]]:
        return misc.ISUBAUTHORITY_MATCHER.match(self.authority)

    @classmethod
    def from_string(
        cls,
        iri_string: t.Union[str, bytes],
        encoding: str = "utf-8",
    ) -> _Self:
        """Parse a IRI reference from the given unicode IRI string.

        :param str iri_string: Unicode IRI to be parsed into a reference.
        :param str encoding: The encoding of the string provided
        :returns: :class:`IRIReference` or subclass thereof
        """
        iri_string = compat.to_str(iri_string, encoding)

        split_iri = misc.IRI_MATCHER.match(iri_string).groupdict()
        return cls(
            split_iri["scheme"],
            split_iri["authority"],
            normalizers.encode_component(split_iri["path"], encoding),
            normalizers.encode_component(split_iri["query"], encoding),
            normalizers.encode_component(split_iri["fragment"], encoding),
            encoding,
        )

    def encode(  # noqa: C901
        self,
        idna_encoder: t.Optional[  # pyright: ignore[reportRedeclaration]
            t.Callable[[str], t.Union[str, bytes]]
        ] = None,
    ) -> "uri.URIReference":
        """Encode an IRIReference into a URIReference instance.

        If the ``idna`` module is installed or the ``rfc3986[idna]``
        extra is used then unicode characters in the IRI host
        component will be encoded with IDNA2008.

        :param idna_encoder:
            Function that encodes each part of the host component
            If not given will raise an exception if the IRI
            contains a host component.
        :rtype: uri.URIReference
        :returns: A URI reference
        """
        authority = self.authority
        if authority:
            if idna_encoder is None:
                if idna is None:  # pragma: no cover
                    raise exceptions.MissingDependencyError(
                        "Could not import the 'idna' module "
                        "and the IRI hostname requires encoding"
                    )

                def idna_encoder(name: str) -> t.Union[str, bytes]:
                    assert idna  # Known to not be None at this point.

                    if any(ord(c) > 128 for c in name):
                        try:
                            return idna.encode(
                                name.lower(), strict=True, std3_rules=True
                            )
                        except idna.IDNAError:
                            raise exceptions.InvalidAuthority(self.authority)
                    return name

            authority = ""
            if self.host:
                authority = ".".join(
                    [
                        compat.to_str(idna_encoder(part))
                        for part in self.host.split(".")
                    ]
                )

            if self.userinfo is not None:
                authority = (
                    normalizers.encode_component(self.userinfo, self.encoding)
                    + "@"
                    + authority
                )

            if self.port is not None:
                authority += ":" + str(self.port)

        return uri.URIReference(
            self.scheme,
            authority,
            path=self.path,
            query=self.query,
            fragment=self.fragment,
            encoding=self.encoding,
        )
