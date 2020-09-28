# -*- coding: utf-8 -*-
"""
deserializer handlers datetime module.
"""

import pyrin.globalization.datetime.services as datetime_services

from pyrin.converters.deserializer.handlers.base import StringPatternDeserializerBase
from pyrin.converters.deserializer.decorators import deserializer
from pyrin.core.globals import NULL
from pyrin.utils.datetime import DEFAULT_DATE_TIME_ISO_REGEX, DEFAULT_DATE_ISO_REGEX, \
    DEFAULT_TIME_ISO_REGEX, DEFAULT_LOCAL_NAIVE_TIME_REGEX, DEFAULT_UTC_ZULU_DATE_TIME_REGEX, \
    DEFAULT_LOCAL_NAIVE_DATE_TIME_REGEX


@deserializer()
class DateDeserializer(StringPatternDeserializerBase):
    """
    date deserializer class.
    """

    def __init__(self, **options):
        """
        creates an instance of DateDeserializer.

        :keyword list[tuple[Pattern, int, int]] accepted_formats: a list of custom accepted
                                                                  formats and their min and
                                                                  max length for date
                                                                  deserialization.

        :note accepted_formats: list[tuple[Pattern format, int min_length, int max_length]]
        """

        super().__init__(**options)

    def _deserialize(self, value, **options):
        """
        deserializes the given value.

        returns `NULL` object if deserialization fails.

        :param str value: value to be deserialized.

        :keyword Pattern matching_pattern: the pattern that has matched the value.

        :rtype: date
        """

        try:
            converted_date = datetime_services.to_date(value)
            if converted_date is not None:
                return converted_date

            return NULL
        except Exception:
            return NULL

    @property
    def default_formats(self):
        """
        gets default accepted formats that this deserializer could deserialize value from.

        :returns: list[tuple[Pattern format, int min_length, int max_length]]
        :rtype: list[tuple[Pattern, int, int]]
        """

        return [(DEFAULT_DATE_ISO_REGEX, 10, 10)]


@deserializer()
class TimeDeserializer(StringPatternDeserializerBase):
    """
    time deserializer class.
    """

    def __init__(self, **options):
        """
        creates an instance of TimeDeserializer.

        :keyword list[tuple[Pattern, int, int]] accepted_formats: a list of custom accepted
                                                                  formats and their min and
                                                                  max length for time
                                                                  deserialization.

        :note accepted_formats: list[tuple[Pattern format, int min_length, int max_length]]
        """

        super().__init__(**options)

    def _deserialize(self, value, **options):
        """
        deserializes the given value.

        returns `NULL` object if deserialization fails.

        :param str value: value to be deserialized.

        :keyword Pattern matching_pattern: the pattern that has matched the value.

        :rtype: time
        """

        try:
            converted_time = datetime_services.to_time(value)
            if converted_time is not None:
                return converted_time

            return NULL
        except Exception:
            return NULL

    @property
    def default_formats(self):
        """
        gets default accepted formats that this deserializer could deserialize value from.

        :returns: list[tuple[Pattern format, int min_length, int max_length]]
        :rtype: list[tuple[Pattern, int, int]]
        """

        return [(DEFAULT_TIME_ISO_REGEX, 14, 21),
                (DEFAULT_LOCAL_NAIVE_TIME_REGEX, 8, 15)]


@deserializer()
class DateTimeDeserializer(StringPatternDeserializerBase):
    """
    datetime deserializer class.
    """

    def __init__(self, **options):
        """
        creates an instance of DateTimeDeserializer.

        :keyword list[tuple[Pattern, int, int]] accepted_formats: a list of custom accepted
                                                                  formats and their min and
                                                                  max length for datetime
                                                                  deserialization.

        :note accepted_formats: list[tuple[Pattern format, int min_length, int max_length]]
        """

        super().__init__(**options)

    def _deserialize(self, value, **options):
        """
        deserializes the given value.

        returns `NULL` object if deserialization fails.

        :param str value: value to be deserialized.

        :keyword Pattern matching_pattern: the pattern that has matched the value.

        :rtype: datetime
        """

        try:
            matching_pattern = options.get('matching_pattern')
            replace_server = None
            if matching_pattern == DEFAULT_LOCAL_NAIVE_DATE_TIME_REGEX:
                replace_server = False

            converted_datetime = datetime_services.to_datetime(value, server=True,
                                                               replace_server=replace_server)
            if converted_datetime is not None:
                return converted_datetime

            return NULL
        except Exception:
            return NULL

    @property
    def default_formats(self):
        """
        gets default accepted formats that this deserializer could deserialize value from.

        :returns: list[tuple[Pattern format, int min_length, int max_length]]
        :rtype: list[tuple[Pattern, int, int]]
        """

        return [(DEFAULT_DATE_TIME_ISO_REGEX, 25, 32),
                (DEFAULT_UTC_ZULU_DATE_TIME_REGEX, 20, 27),
                (DEFAULT_LOCAL_NAIVE_DATE_TIME_REGEX, 19, 26)]
