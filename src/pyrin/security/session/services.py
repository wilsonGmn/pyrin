# -*- coding: utf-8 -*-
"""
session services module.
"""

from pyrin.application.services import get_component
from pyrin.security.session import SessionPackage


def get_current_user():
    """
    gets current user.

    :rtype: dict
    """

    return get_component(SessionPackage.COMPONENT_NAME).get_current_user()


def get_current_request():
    """
    gets current request object.

    :rtype: CoreRequest
    """

    return get_component(SessionPackage.COMPONENT_NAME).get_current_request()


def get_current_request_context():
    """
    gets current request context.

    :rtype: dict
    """

    return get_component(SessionPackage.COMPONENT_NAME).get_current_request_context()


def add_request_context(key, value):
    """
    adds the given key/value pair into request context.

    :param str key: key to be added.
    :param object value: value to be added.

    :raises InvalidRequestContextKeyNameError: invalid request context key name error.
    """

    return get_component(SessionPackage.COMPONENT_NAME).add_request_context(key, value)
