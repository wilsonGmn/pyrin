# -*- coding: utf-8 -*-
"""
authentication interface module.
"""

from abc import abstractmethod
from threading import Lock

from pyrin.core.structs import CoreObject, MultiSingletonMeta
from pyrin.core.exceptions import CoreNotImplementedError


class AuthenticatorSingletonMeta(MultiSingletonMeta):
    """
    authenticator singleton meta class.

    this is a thread-safe implementation of singleton.
    """

    _instances = dict()
    _lock = Lock()


class AbstractAuthenticatorBase(CoreObject, metaclass=AuthenticatorSingletonMeta):
    """
    abstract authenticator base class.
    """

    @abstractmethod
    def authenticate(self, request, **options):
        """
        authenticates the user for given request.

        :param CoreRequest request: current request object.

        :raises CoreNotImplementedError: core not implemented error.
        """

        raise CoreNotImplementedError()

    @property
    @abstractmethod
    def name(self):
        """
        gets the name of this authenticator.

        :raises CoreNotImplementedError: core not implemented error.

        :rtype: str
        """

        raise CoreNotImplementedError()
