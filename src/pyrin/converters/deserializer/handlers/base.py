# -*- coding: utf-8 -*-
"""
deserializer base module.
"""

from threading import Lock

from pyrin.core.context import CoreObject
from pyrin.core.exceptions import CoreNotImplementedError
from pyrin.utils.singleton import MultiSingletonMeta


class DeserializerSingletonMeta(MultiSingletonMeta):
    """
    deserializer singleton meta class.
    this is a thread-safe implementation of singleton.
    """

    # a dictionary containing an instance of each type.
    # in the form of: {type: instance}
    _instances = dict()
    _lock = Lock()


class DeserializerBase(CoreObject, metaclass=DeserializerSingletonMeta):
    """
    base deserializer class.
    """

    def __init__(self, **options):
        """
        initializes an instance of DeserializerBase.
        """

        CoreObject.__init__(self)

    def deserialize(self, value, **options):
        """
        deserializes the given value.
        returns `NULL` object if deserialization fails.

        :param object value: value to be deserialized.

        :raises CoreNotImplementedError: core not implemented error.

        :returns: deserialized value.

        :rtype: any
        """

        raise CoreNotImplementedError()

    def is_deserializable(self, value, **options):
        """
        gets a value indicating that the given input is deserializable.

        :param object value: value to be deserialized.

        :rtype: bool
        """

        return isinstance(value, self.get_accepted_type())

    def get_accepted_type(self):
        """
        gets the accepted type for this deserializer
        which could deserialize values from this type.

        :raises CoreNotImplementedError: core not implemented error.

        :rtype: type
        """

        raise CoreNotImplementedError()


class StringDeserializerBase(DeserializerBase):
    """
    base string deserializer class.
    """

    # these values will be used for accepted
    # formats that have no length restriction.
    UNDEF_LENGTH = None
    DEFAULT_MIN = 1
    DEFAULT_MAX = 1000000

    def __init__(self, **options):
        """
        initializes an instance of StringDeserializerBase.

        :keyword list[tuple(str, int)] accepted_formats: custom formats and their length
                                                         that this deserializer can
                                                         deserialize value from.

        :type accepted_formats: list[tuple(str format, int length)]
        """

        DeserializerBase.__init__(self, **options)

        self._accepted_formats = self.get_default_formats()

        custom_accepted_formats = options.get('accepted_formats', [])
        self._accepted_formats.extend(custom_accepted_formats)

        # min and max accepted length of strings
        # to be deserialized by this deserializer.
        self._min_length, self._max_length = self._calculate_accepted_length()

    def deserialize(self, value, **options):
        """
        deserializes the given value.
        returns `NULL` object if deserialization fails.

        :param str value: value to be deserialized.

        :raises CoreNotImplementedError: core not implemented error.

        :returns: deserialized value.

        :rtype: any
        """

        raise CoreNotImplementedError()

    def is_deserializable(self, value, **options):
        """
        gets a value indicating that the given input is deserializable.

        :param object value: value to be deserialized.

        :rtype: bool
        """

        if DeserializerBase.is_deserializable(self, value, **options) \
                and self.is_valid_length(value):
            return True

        return False

    def get_accepted_type(self):
        """
        gets the accepted type for this deserializer
        which could deserialize values from this type.

        :rtype: type
        """

        return str

    def get_accepted_length(self):
        """
        gets the min and max accepted length of strings to be
        deserialized by this deserializer.

        :returns tuple(int min, int max)

        :rtype: tuple(int, int)
        """

        return self._min_length, self._max_length

    def get_accepted_formats(self):
        """
        gets the accepted string formats that this deserializer
        can deserialize value from.

        :returns: list(tuple(str format, int length))

        :rtype: list(tuple(str, int))
        """

        return self._accepted_formats

    def is_valid_length(self, value):
        """
        gets a value indicating that input value has valid
        length to be deserialized by this deserializer.

        :param str value: value to be deserialized.

        :rtype: bool
        """

        length = len(value.strip())
        min_length, max_length = self.get_accepted_length()

        if length < min_length or length > max_length:
            return False

        return True

    def _calculate_accepted_length(self):
        """
        calculates the min and max accepted length of values
        to be deserialized by this deserializer.

        :returns: tuple(int min, int max)

        :rtype: tuple(int, int)
        """

        # if there is any format with length=UNDEF_LENGTH,
        # we should not enforce length restriction on values.
        if self.UNDEF_LENGTH in [item[1] for item in self.get_accepted_formats()]:
            return self.DEFAULT_MIN, self.DEFAULT_MAX

        return min([item[1] for item in self.get_accepted_formats()]), \
            max([item[1] for item in self.get_accepted_formats()])

    def get_default_formats(self):
        """
        gets default accepted formats that this
        deserializer could deserialize value from.

        :raises CoreNotImplementedError: core not implemented error.

        :return: list(tuple(str format, int length))

        :rtype: list(tuple(str, int))
        """

        raise CoreNotImplementedError()


class StringPatternDeserializerBase(StringDeserializerBase):
    """
    base string pattern deserializer class.
    this class uses regex to determine whether a value is deserializable or not.
    """

    def __init__(self, **options):
        """
        initializes an instance of StringPatternDeserializerBase.

        :keyword list[tuple(Pattern, int)] accepted_formats: custom patterns and their length
                                                             that this deserializer can
                                                             deserialize value from.

        :type accepted_formats: list[tuple(Pattern format, int length)]
        """

        StringDeserializerBase.__init__(self, **options)

    def is_deserializable(self, value, **options):
        """
        gets a value indicating that the given input is deserializable.
        if value is deserializable, the matching Pattern would be also returned.
        otherwise None would be returned instead of Pattern.

        :param object value: value to be deserialized.

        :rtype: tuple(bool, Union[Pattern, None])
        """

        if StringDeserializerBase.is_deserializable(self, value, **options):
            for pattern, length in self.get_accepted_formats():
                if pattern.match(value.strip()):
                    return True, pattern

        return False, None
