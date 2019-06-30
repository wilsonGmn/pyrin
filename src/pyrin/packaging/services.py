# -*- coding: utf-8 -*-
"""
packaging services module.
"""

from pyrin.packaging import PackagingPackage
from pyrin.application.services import get_component


def load_components(**options):
    """
    loads required packages and modules for application startup.
    """

    get_component(PackagingPackage.COMPONENT_NAME).load_components(**options)


def load(module_name, **options):
    """
    loads the specified module.

    :param str module_name: full module name.
                            example module_name = `pyrin.application.decorators`.

    :rtype: Module
    """

    return get_component(PackagingPackage.COMPONENT_NAME).load(module_name, **options)


def register_hook(instance):
    """
    registers the given instance into packaging hooks.

    :param PackagingHookBase instance: packaging hook instance to be registered.

    :raises InvalidPackagingHookTypeError: invalid packaging hook type error.
    """

    get_component(PackagingPackage.COMPONENT_NAME).register_hook(instance)
