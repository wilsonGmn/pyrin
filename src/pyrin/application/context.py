# -*- coding: utf-8 -*-
"""
application context module.
"""

from datetime import datetime

from flask import Request, Response, jsonify

import pyrin.utils.unique_id as uuid_utils

from pyrin.application.exceptions import ComponentAttributeError, InvalidComponentNameError
from pyrin.core.context import Context, CoreObject
from pyrin.core.exceptions import ContextAttributeError
from pyrin.settings.static import DEFAULT_STATUS_CODE, JSONIFY_MIMETYPE, \
    APPLICATION_ENCODING, DEFAULT_COMPONENT_KEY


class ApplicationContext(Context):
    """
    context class to hold application contextual data.
    """

    def _raise_key_error(self, key):
        """
        raises an error for given key.

        :param object key: key object that caused the error.

        :raises ContextAttributeError: context attribute error.
        """

        raise ContextAttributeError('Property [{name}] not found in application context.'
                                    .format(name=key))


class ApplicationComponent(ApplicationContext):
    """
    context class to hold application components.
    """

    def _raise_key_error(self, key):
        """
        raises an error for given key.

        :param object key: key object that caused the error.

        :raises ComponentAttributeError: component attribute error.
        """

        raise ComponentAttributeError('Component [{name}] is not available '
                                      'in application components.'.format(name=key))


class Component(CoreObject):
    """
    base component class.
    all component classes must inherit from this class and their respective manager class.
    """

    def __init__(self, component_name, **options):
        """
        initializes an instance of Component.

        :param str component_name: component name.

        :keyword object component_custom_key: component custom key.
        """

        super(Component, self).__init__()

        # component id is a tuple(str, object) and should be unique for each
        # instance unless it's intended to replace an already existing one.
        self._component_id = self.make_component_id(component_name, **options)

    def get_id(self):
        """
        gets the component id of this instance.

        :rtype: tuple(str, object)
        """

        return self._component_id

    @staticmethod
    def make_component_id(component_name, **options):
        """
        makes a component id based on input values and returns it.

        :param str component_name: component name.

        :keyword object component_custom_key: component custom key.

        :raises InvalidComponentNameError: invalid component name.

        :rtype: tuple(str, object)
        """

        if component_name is None or component_name.strip() == '':
            raise InvalidComponentNameError('Component name should not be blank.')

        component_custom_key = options.get('component_custom_key', DEFAULT_COMPONENT_KEY)
        return component_name, component_custom_key


class CoreResponse(Response):
    """
    represents base response.
    this class should be used as server response.
    """

    # charset of the response.
    charset = APPLICATION_ENCODING

    # default status if none is provided.
    default_status = DEFAULT_STATUS_CODE

    # default mimetype if none is provided.
    default_mimetype = JSONIFY_MIMETYPE

    # function to use as response converter.
    response_converter = jsonify

    def __init__(self, response=None, **kwargs):
        super(CoreResponse, self).__init__(response, **kwargs)

    @classmethod
    def force_type(cls, response, environ=None):
        response = cls.response_converter(response)
        return super(CoreResponse, cls).force_type(response, environ)


class CoreRequest(Request):
    """
    represents base request class.
    this class should be used for server request.
    """

    # charset of the request.
    charset = APPLICATION_ENCODING

    def __init__(self, environ, populate_request=True,
                 shallow=False, **options):
        super(CoreRequest, self).__init__(environ, populate_request, shallow)

        self.request_id = uuid_utils.generate()
        self.request_date = datetime.utcnow()
        self.client_ip = None
        self.context = Context()
        a = self.method
        b = self.query_string
        c = self.args
        d = self.view_args

    def __str__(self):
        result = 'request id: [{request_id}], request date: [{request_date}], route: [{route}]'
        return result.format(request_id=self.request_id,
                             request_date=self.request_date,
                             route=self.path)
