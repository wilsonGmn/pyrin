# -*- coding: utf-8 -*-
"""
babel manager module.
"""

import pyrin.utils.path as path_utils
import pyrin.application.services as application_services

from pyrin.cli.mixin.handler import CLIMixin
from pyrin.core.context import Manager
from pyrin.globalization.locale.babel.interface import BabelCLIHandlerBase
from pyrin.utils.custom_print import print_warning
from pyrin.utils.exceptions import DirectoryAlreadyExistedError


class BabelManager(Manager, CLIMixin):
    """
    babel manager class.
    """

    _cli_handler_type = BabelCLIHandlerBase

    def enable(self, include_pyrin=True, include_app=True):
        """
        enables locale management for the application.

        :param bool include_pyrin: specifies that it should extract pyrin localizable
                                   messages. defaults to True if not provided.

        :param bool include_app: specifies that it should extract application
                                 localizable messages. defaults to True if not provided.
        """

        locale_path = application_services.get_locale_path()

        try:
            path_utils.create_directory(locale_path)
        except DirectoryAlreadyExistedError:
            print_warning('Locale has been already enabled.', force=True)

        if include_pyrin or include_app:
            self._extract(include_pyrin, include_app)

    def rebuild(self, include_pyrin=True, include_app=True, locale=None):
        """
        it will do the three complete steps needed to
        update and compile locales with new messages.

        it will do:
            1. extract
            2. update
            3. compile

        this command is defined for convenient of usage, but if you need
        to do these steps separately, you could ignore this command and
        use the relevant command for each step.

        :keyword bool include_pyrin: specifies that it must extract pyrin localizable
                                     messages as well. defaults to True if not provided.

        :keyword bool include_app: specifies that it must extract application localizable
                                   messages as well. defaults to True if not provided.

        :keyword str locale: locale name of the catalog to compile.
                             it will compile all catalogs if not provided.
        """

        self._extract(include_pyrin, include_app)
        self.execute('update', locale=locale)
        self.execute('compile', locale=locale)

    def _extract(self, include_pyrin=True, include_app=True):
        """
        extracts messages from source files and generates a `.pot` file.

        :keyword bool include_pyrin: specifies that it must extract pyrin localizable
                                     messages as well. defaults to True if not provided.

        :keyword bool include_app: specifies that it must extract application localizable
                                   messages as well. defaults to True if not provided.
        """

        self.execute('extract', include_pyrin=include_pyrin, include_app=include_app)
