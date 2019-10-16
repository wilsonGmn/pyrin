# -*- coding: utf-8 -*-
"""
api manager module.
"""

import pyrin.logging.services as logging_services
import pyrin.configuration.services as config_services

from pyrin.core.context import CoreObject
from pyrin.core.enumerations import ServerErrorResponseCodeEnum
from pyrin.utils import response as response_utils
from pyrin.core.globals import _


class APIManager(CoreObject):
    """
    api manager class.
    """

    LOGGER = logging_services.get_logger('api')

    def handle_http_error(self, exception):
        """
        handles http exceptions.
        note that normally you should never call this method manually.

        :param HTTPException exception: exception instance.

        :rtype: CoreResponse
        """

        self.LOGGER.exception(str(exception))
        return response_utils.make_exception_response(exception)

    def handle_server_error(self, exception):
        """
        handles server internal core exceptions.
        note that normally you should never call this method manually.

        :param CoreException exception: core exception instance.

        :rtype: CoreResponse
        """

        self.LOGGER.exception(str(exception))
        return response_utils.make_exception_response(exception)

    def handle_server_unknown_error(self, exception):
        """
        handles unknown server internal exceptions.
        note that normally you should never call this method manually.
        in any environment which debug mode is false, the original error
        message will be replaced by a generic error message before being
        sent to client for security reasons.

        :param Exception exception: exception instance.

        :rtype: CoreResponse
        """

        self.LOGGER.exception(str(exception))

        if config_services.get_active('environment', 'debug') is True:
            return response_utils.make_exception_response(exception,
                                                          code=ServerErrorResponseCodeEnum.
                                                          INTERNAL_SERVER_ERROR)

        return response_utils.make_error_response(_('Application has been encountered an error. '
                                                    'Please contact the support team if problem '
                                                    'persists.'),
                                                  code=ServerErrorResponseCodeEnum.
                                                  INTERNAL_SERVER_ERROR)
