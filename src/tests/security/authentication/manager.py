# -*- coding: utf-8 -*-
"""
authentication manager module.
"""

import pyrin.security.session.services as session_services

from pyrin.core.context import DTO
from pyrin.security.authentication.exceptions import AuthenticationFailedError
from pyrin.security.authentication.manager import AuthenticationManager as \
    BaseAuthenticationManager


class AuthenticationManager(BaseAuthenticationManager):
    """
    authentication manager class.
    """

    def _push_custom_data(self, header, payload, **options):
        """
        pushes the custom data into current request from input values.

        :param dict header: token header data.

        :param dict payload: payload data of authenticated token.
        :type payload: dict(str type: token type)
        """

        user_id = payload.pop('user_id')
        session_services.set_current_user(DTO(user_id=user_id))

    def _validate_custom(self, header, payload, **options):
        """
        validates the given inputs for custom attributes.
        an error will be raised if validation fails.

        :param dict header: token header data.

        :param dict payload: payload data to be validated.
        :type payload: dict(str type: token type)

        :raises AuthenticationFailedError: authentication failed error.
        """

        user_id = payload.get('user_id', 0)
        if user_id <= 0:
            raise AuthenticationFailedError('User identity must be provided in payload.')
