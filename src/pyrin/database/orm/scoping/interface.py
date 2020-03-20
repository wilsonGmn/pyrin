# -*- coding: utf-8 -*-
"""
orm scoping interface module.
"""

from abc import abstractmethod

from pyrin.core.context import CoreObject
from pyrin.core.exceptions import CoreNotImplementedError


class AbstractScopedRegistryBase(CoreObject):
    """
    abstract scoped registry base class.

    all application scoped registry classes must be subclassed from this.
    it also supports atomic objects.
    """

    @abstractmethod
    def __call__(self, atomic=False):
        """
        gets the corresponding object from registry if available, otherwise creates a new one.

        :param bool atomic: specifies that it must get an atomic object.
                            it returns it from registry if available,
                            otherwise gets a new atomic object.
                            defaults to False if not provided.

        :raises CoreNotImplementedError: core not implemented error.

        :returns: object
        """

        raise CoreNotImplementedError()

    @abstractmethod
    def has(self, atomic=False):
        """
        gets a value indicating that an object is present in the current scope.

        :param bool atomic: specifies that it must check just for an atomic
                            object. defaults to False if not provided.

        :raises CoreNotImplementedError: core not implemented error.

        :rtype: bool
        """

        raise CoreNotImplementedError()

    @abstractmethod
    def set(self, obj, atomic=False):
        """
        sets the value for the current scope.

        :param object obj: object to be set in registry.

        :param bool atomic: specifies that it must set an atomic object.
                            defaults to False if not provided.

        :raises CoreNotImplementedError: core not implemented error.
        """

        raise CoreNotImplementedError()

    @abstractmethod
    def clear(self, atomic=False):
        """
        clears the current scope's objects, if any.

        it also clears if any atomic object is available.
        if `atomic=True` is provided, it only clears the atomic object if available.

        :param bool atomic: specifies that it must only clear an atomic object
                            of current scope. otherwise, it clears all objects of
                            current scope. defaults to False if not provided.

        :raises CoreNotImplementedError: core not implemented error.
        """

        raise CoreNotImplementedError()

    @abstractmethod
    def get(self, atomic=False):
        """
        gets the current object of this scope if available, otherwise returns None.

        :param bool atomic: specifies that it must get the atomic object of
                            current scope, otherwise it returns the normal object.
                            defaults to False if not provided.

        :raises CoreNotImplementedError: core not implemented error.

        :returns: object
        """

        raise CoreNotImplementedError()
