# -*- coding: utf-8 -*-
"""
authentication handlers base module.
"""

from abc import abstractmethod

import pyrin.security.token.services as token_services
import pyrin.security.session.services as session_services
import pyrin.utils.misc as misc_utils

from pyrin.core.globals import _
from pyrin.core.exceptions import CoreNotImplementedError
from pyrin.security.enumerations import TokenTypeEnum
from pyrin.security.authentication.interface import AbstractAuthenticatorBase
from pyrin.security.authentication.handlers.exceptions import RefreshTokenRequiredError, \
    AuthenticatorNameIsRequiredError, AccessTokenRequiredError, InvalidUserError, \
    AccessAndRefreshTokensDoesNotBelongToSameUserError, InvalidAccessTokenError, \
    InvalidTokenAuthenticatorError, InvalidRefreshTokenError, UserCredentialsRevokedError, \
    InvalidUserIdentityError


class AuthenticatorBase(AbstractAuthenticatorBase):
    """
    authenticator base class.

    all application authenticators must be subclassed from this.
    """

    # each subclass must set an authenticator name in this attribute.
    _name = None

    def __init__(self, *args, **options):
        """
        initializes and instance of AuthenticatorBase.

        :raises AuthenticatorNameIsRequiredError: authenticator name is required error.
        """

        super().__init__()

        if not self._name or self._name.isspace():
            raise AuthenticatorNameIsRequiredError('Authenticator [{instance}] does not '
                                                   'have a name.'.format(instance=self))

    def _get_info(self, payload, **options):
        """
        gets the info of given payload to be set in current request.

        :param dict | str payload: credential payload.

        :rtype: dict
        """

        result = dict()
        extra_info = self._get_extra_info(payload, **options)
        if extra_info:
            result.update(extra_info)

        return result

    def _get_extra_info(self, payload, **options):
        """
        gets the the info of given payload to be set in current request.

        it could be None if no extra info must be set in current request.

        :param dict | str payload: credential payload.

        :rtype: dict
        """

        return None

    def _get_user_info(self, user, **options):
        """
        gets the info of given user to be set in current request.

        it could be None if no extra info must be set in current request.

        :param BaseEntity | ROW_RESULT user: user entity to get its info.

        :rtype: object | dict
        """

        return None

    def _get_custom_component_key(self, user, *args, **options):
        """
        gets custom component key for given user if required to be set in current request.

        this method could be overridden in subclasses if required.

        :param BaseEntity | ROW_RESULT user: authenticated user entity.

        :rtype: object
        """

        return None

    def _set_custom_component_key(self, value):
        """
        sets the provided value as custom component key into current request.

        :param object value: value to be pushed as component custom key.

        :raises InvalidComponentCustomKeyError: invalid component custom key error.
        """

        session_services.set_component_custom_key(value)

    def _pre_authenticate(self, *payloads, **options):
        """
        pre-authenticates the user with given credentials.

        this method could be overridden in subclasses if pre-authentication is required.
        it must raise an `AuthenticationFailedError` if pre-authentication failed.

        :param dict | str payloads: credential payloads.
                                    it is usually an access token, refresh
                                    token or a session identifier.
                                    it can be multiple items if required.
        """
        pass

    def _authorize_user(self, user_info, **options):
        """
        authorizes the user with given info.

        this method could be overridden in subclasses if required.
        it must raise an error if authorization failed.

        :param dict user_info: user info to be authorized.
        """
        pass

    def _authenticate(self, *payloads, **options):
        """
        authenticates the user with given credentials.

        :param dict | str payloads: credential payloads.
                                    it is usually an access token, refresh
                                    token or a session identifier.
                                    it can be multiple items if required.

        :raises AuthenticationFailedError: authentication failed error.
        :raises InvalidUserError: invalid user error.
        :raises InvalidUserIdentityError: invalid user identity error.
        """

        self._pre_authenticate(*payloads, **options)
        user_payload = self._get_user_related_payload(*payloads, **options)
        user = self._get_user(user_payload, **options)
        if not user:
            raise InvalidUserError('User could not be None.')

        identity = self._get_user_identity(user, **options)
        if not identity:
            raise InvalidUserIdentityError('User identity could not be None.')

        info = self._get_info(user_payload, **options)
        user_info = self._get_user_info(user, **options)
        if user_info:
            info.update(user_info)

        session_services.set_current_user(identity, info)
        custom_component_key = self._get_custom_component_key(user, user_payload, **options)
        if custom_component_key is not None:
            self._set_custom_component_key(custom_component_key)

    def authenticate(self, request, **options):
        """
        authenticates the user for given request.

        :param CoreRequest request: current request object.

        :raises AuthenticationFailedError: authentication failed error.
        """

        credentials = self._get_credentials(request, **options)
        credentials = misc_utils.make_iterable(credentials, tuple)
        payloads = self._get_payloads(*credentials, **options)
        payloads = misc_utils.make_iterable(payloads, tuple)
        self._authenticate(*payloads, **options)

    def authorize(self, user_info, permissions, **options):
        """
        authorizes the user with given info for the specified permissions.

        if the user does not have each one of specified permissions,
        an error will be raised.

        :param user_info: user info to authorize permissions for.

        :param PermissionBase | list[PermissionBase] permissions: permissions to check
                                                                  for user authorization.

        :raises CoreNotImplementedError: core not implemented error.
        """

    @abstractmethod
    def _get_payloads(self, *credentials, **options):
        """
        gets the required payloads from given credentials.

        it can return multiple items if required.

        :param str credentials: user credentials.
                                it is usually the contents of
                                authorization or cookie headers.
                                it can be multiple items if required.

        :raises CoreNotImplementedError: core not implemented error.

        :rtype: tuple[dict | str] | dict | str
        """

        raise CoreNotImplementedError()

    @abstractmethod
    def _get_credentials(self, request, **options):
        """
        gets the required credentials from given request.

        credentials are usually the contents of authorization or cookie headers.
        it can return multiple items if required.

        :param CoreRequest request: current request object.

        :raises CoreNotImplementedError: core not implemented error.

        :rtype: tuple[str] | str
        """

        raise CoreNotImplementedError()

    @abstractmethod
    def _get_user_related_payload(self, *payloads, **options):
        """
        gets a single value as user related payload to be used to fetch related user.

        :param dict | str payloads: credential payloads.
                                    it is usually an access token, refresh
                                    token or a session identifier.
                                    it can be multiple items if required.

        :raises CoreNotImplementedError: core not implemented error.

        :rtype: dict | str
        """

        raise CoreNotImplementedError()

    @abstractmethod
    def _get_user_identity(self, user, **options):
        """
        gets the identity of given user to be set in current request.

        the identity is normally the primary key of user entity.
        but it could be a dict of multiple values if required.

        :param BaseEntity | ROW_RESULT user: user entity to get its identity.

        :raises CoreNotImplementedError: core not implemented error.

        :rtype: object | dict
        """

        raise CoreNotImplementedError()

    @abstractmethod
    def _get_user(self, payload, **options):
        """
        gets the user entity from given inputs.

        this method must return a user on success or raise an error
        if it can not fetch related user to given payload.

        :param dict | str payload: credential payload.

        :raises CoreNotImplementedError: core not implemented error.

        :rtype: BaseEntity | ROW_RESULT
        """

        raise CoreNotImplementedError()

    @property
    def name(self):
        """
        gets the name of this authenticator.

        :rtype: str
        """

        return self._name


class TokenAuthenticatorBase(AuthenticatorBase):
    """
    token authenticator base class.

    all application token authenticators must be subclassed from this.
    """

    # header name to read access token from it.
    ACCESS_TOKEN_HOLDER = 'Authorization'

    # cookie name to read refresh token from it.
    REFRESH_TOKEN_HOLDER = 'Refresh-Auth'

    # a key name to hold user identity in token payloads.
    USER_IDENTITY_HOLDER = 'sub'

    # specifies that this authenticator requires refresh token.
    _refresh_token = True

    def _get_token_payload(self, token, **options):
        """
        gets the payload of given token.

        :param str token: token.

        :returns: tuple[dict header, dict payload]
        :rtype: tuple[dict, dict]
        """

        header = token_services.get_unverified_header(token, **options)
        payload = token_services.get_payload(token, **options)
        return header, payload

    def _get_access_token_payload(self, access_token, **options):
        """
        gets the given access token payload.

        :param str access_token: access token.

        :raises AccessTokenRequiredError: access token required error.

        :rtype: dict
        """

        if not access_token:
            raise AccessTokenRequiredError(_('Access token is required for authentication.'))

        header, payload = self._get_token_payload(access_token, **options)
        self._validate_access_token(header, payload, **options)
        return payload

    def _get_refresh_token_payload(self, refresh_token, **options):
        """
        gets the given refresh token payload.

        :param str refresh_token: refresh token.

        :raises RefreshTokenRequiredError: refresh token required error.

        :rtype: dict
        """

        if not refresh_token:
            raise RefreshTokenRequiredError(_('Refresh token is required for authentication.'))

        header, payload = self._get_token_payload(refresh_token, **options)
        self._validate_refresh_token(header, payload, **options)
        return payload

    def _get_payloads(self, access_token, refresh_token, **options):
        """
        gets the required payloads from given credentials.

        :param str access_token: access token.
        :param str refresh_token: refresh token.

        :returns: tuple[dict access_token_payload, dict refresh_token_payload]
        :rtype: tuple[dict]
        """

        access_token_payload = self._get_access_token_payload(access_token, **options)
        refresh_token_payload = None
        if self._refresh_token:
            refresh_token_payload = self._get_refresh_token_payload(refresh_token, **options)

        return access_token_payload, refresh_token_payload

    def _get_access_token_credential(self, request):
        """
        gets access token from given request.

        :param CoreRequest request: current request object.

        :rtype: str
        """

        return request.headers.get(self.ACCESS_TOKEN_HOLDER)

    def _get_refresh_token_credential(self, request):
        """
        gets refresh token from given request.

        :param CoreRequest request: current request object.

        :rtype: str
        """

        return request.cookies.get(self.REFRESH_TOKEN_HOLDER)

    def _get_credentials(self, request, **options):
        """
        gets the required credentials from given request.

        credentials are usually the contents of authorization or cookie headers.
        it can return multiple items if required.

        :param CoreRequest request: current request object.

        :returns: tuple[str access_token, str refresh_token]
        :rtype: tuple[str, str]
        """

        access_token = self._get_access_token_credential(request)
        refresh_token = None
        if self._refresh_token:
            refresh_token = self._get_refresh_token_credential(request)

        return access_token, refresh_token

    def _validate_same_user(self, access_token_payload, refresh_token_payload, **options):
        """
        validates that both tokens are related to the same user.

        :param dict access_token_payload: access token payload.
        :param dict refresh_token_payload: refresh token payload.

        :raises AccessAndRefreshTokensDoesNotBelongToSameUserError: access and refresh tokens
                                                                    does not belong to same
                                                                    user error.
        """

        access_user = access_token_payload.get(self.USER_IDENTITY_HOLDER)
        refresh_user = refresh_token_payload.get(self.USER_IDENTITY_HOLDER)
        if access_user != refresh_user:
            raise AccessAndRefreshTokensDoesNotBelongToSameUserError(_('Provided access and '
                                                                       'refresh tokens does not '
                                                                       'belong to the same user.'))

    def _validate_access_token(self, header, payload, **options):
        """
        validates given header and payload of an access token.

        :param dict header: token header.
        :param dict payload: token payload.

        :raises InvalidAccessTokenError: invalid access token error.
        :raises InvalidTokenAuthenticatorError: invalid token authenticator error.
        """

        if not header or not payload or not payload.get(self.USER_IDENTITY_HOLDER) or \
                payload.get('type') != TokenTypeEnum.ACCESS:
            raise InvalidAccessTokenError(_('Provided access token is invalid.'))

        generator = payload.get('auth')
        if generator != self.name:
            raise InvalidTokenAuthenticatorError(_('This access token is generated using '
                                                   'another authenticator with name [{name}].')
                                                 .format(name=generator))

    def _validate_refresh_token(self, header, payload, **options):
        """
        validates given header and payload of a refresh token.

        :param dict header: token header.
        :param dict payload: token payload.

        :raises InvalidRefreshTokenError: invalid refresh token error.
        :raises InvalidTokenAuthenticatorError: invalid token authenticator error.
        """

        if not header or not payload or not payload.get(self.USER_IDENTITY_HOLDER) or \
                payload.get('type') != TokenTypeEnum.REFRESH:
            raise InvalidRefreshTokenError(_('Provided refresh token is invalid.'))

        generator = payload.get('auth')
        if generator != self.name:
            raise InvalidTokenAuthenticatorError(_('This refresh token is generated using '
                                                   'another authenticator with name [{name}].')
                                                 .format(name=generator))

    def _is_revoked(self, *id):
        """
        gets a value indicating that tokens with given ids are revoked.

        this method could be overridden in subclasses to perform a database query
        on revoked tokens to check if this id is revoked.

        if you do not want to implement token revocation, you could
        leave this method unimplemented.

        :param uuid.UUID id: token unique id.

        :rtype: bool
        """

        return False

    def _get_extra_info(self, payload, **options):
        """
        gets the the info of given payload to be set in current request.

        :param dict payload: access token payload.

        :rtype: dict
        """

        return dict(is_fresh=payload.get('is_fresh', False))

    def _pre_authenticate(self,  access_token_payload, refresh_token_payload, **options):
        """
        pre-authenticates the user with given credentials.

        :param dict access_token_payload: access token payload.
        :param dict refresh_token_payload: refresh token payload.

        :raises AccessAndRefreshTokensDoesNotBelongToSameUserError: access and refresh tokens
                                                                    does not belong to same
                                                                    user error.

        :raises UserCredentialsRevokedError: user credentials revoked error.
        """

        if self._refresh_token:
            self._validate_same_user(access_token_payload, refresh_token_payload)

        ids = [access_token_payload.get('jti')]
        if self._refresh_token:
            ids.append(refresh_token_payload.get('jti'))

        if self._is_revoked(*ids):
            raise UserCredentialsRevokedError(_('User credentials are revoked.'))

    def _get_user_related_payload(self, access_token_payload,
                                  refresh_token_payload, **options):
        """
        gets a single value as user related payload to be used to fetch related user.

        it simply returns the access token payload.

        :param dict access_token_payload: access token payload.
        :param dict refresh_token_payload: refresh token payload.

        :rtype: dict
        """

        return access_token_payload
