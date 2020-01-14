# -*- coding: utf-8 -*-
"""
packaging manager module.
"""

import os
import inspect

from importlib import import_module

import pyrin.configuration.services as config_services

from pyrin.core.context import CoreObject, DTO
from pyrin.packaging.context import Package
from pyrin.packaging.exceptions import InvalidPackageNameError, \
    InvalidPackagingHookTypeError, ComponentModuleNotFoundError
from pyrin.packaging.hooks import PackagingHookBase
from pyrin.utils.custom_print import print_info
from pyrin.settings.packaging import IGNORED_MODULES, IGNORED_PACKAGES, \
    CORE_PACKAGES, TEST_PACKAGES, LOAD_TEST_PACKAGES
from pyrin.utils.path import resolve_application_root_path


class PackagingManager(CoreObject):
    """
    packaging manager class.
    """

    def __init__(self):
        """
        creates a new instance of PackagingManager.
        """

        CoreObject.__init__(self)

        # holds the absolute path of application root directory where
        # the main package is located. for example `/var/app_root/`.
        self._root_directory = resolve_application_root_path()

        # holds the loaded packages.
        # `pyrin.application` and `pyrin.packaging` will be loaded at
        # the beginning, so they will not included in this list.
        self._loaded_packages = []

        # holds the instance of all loaded modules.
        # in the form of: {str module_name: Module module}
        self._loaded_modules = DTO()

        self.__hooks = []

    def load_components(self, **options):
        """
        loads required packages and modules for application startup.
        """

        print_info('Loading application components...')

        core_packages, application_packages, test_packages = \
            self._get_loadable_components(**options)

        self._load_components(core_packages, **options)
        self._load_components(application_packages, **options)

        if LOAD_TEST_PACKAGES is True:
            self._load_components(test_packages, **options)

        self._after_packages_loaded()

        print_info('Total of [{count}] packages loaded.'
                   .format(count=len(self._loaded_packages)))

    def _after_packages_loaded(self):
        """
        this method will call `after_packages_loaded` method of all registered hooks.
        """

        for hook in self._get_hooks():
            hook.after_packages_loaded()

    def load(self, module_name, **options):
        """
        loads the specified module.

        :param str module_name: full module name.
                                example module_name = `pyrin.application.decorators`.

        :rtype: Module
        """

        module = import_module(module_name)
        self._loaded_modules[module.__name__] = module

        return module

    def _load_component(self, package_name, module_names, component_name, **options):
        """
        loads the given component.

        :param str package_name: full package name to be loaded.
        :param list[str] module_names: full module names to be loaded.
        :param str component_name: component name of this package.

        :raises ComponentModuleNotFoundError: component module not found error.
        """

        self.load(package_name)

        # component module should be loaded first if available, in case of
        # any other module needed package services in top level objects.
        component_module = None
        if component_name is not None:
            root_package = package_name.split('.')[0]
            component_module = '{root_package}.{component}'.format(root_package=root_package,
                                                                   component=component_name)

        if component_module is not None and component_module in module_names:
            self.load(component_module, **options)
        elif component_module is not None and component_module not in module_names:
            raise ComponentModuleNotFoundError('Component module [{name}] not '
                                               'found in [{package}] package.'
                                               .format(name=component_module,
                                                       package=package_name))

        for module in module_names:
            if module != component_module:
                self.load(module, **options)

        self._loaded_packages.append(package_name)

        print('[{package}] package loaded. including [{module_count}] modules.'
              .format(package=package_name,
                      module_count=len(module_names)))

    def _load_components(self, components, **options):
        """
        loads the given components considering their dependency on each other.

        :param dict(str: list[str]) components: full package names and their
                                                modules to be loaded.

        :type components: dict(list[str] package_name: modules)
        """

        # a dictionary containing all dependent package names and their respective modules.
        # in the form of {package_name: [modules]}.
        dependent_components = DTO()

        for package in components.keys():
            package_class = self._get_package_class(package)

            # checking whether this package has any dependencies.
            # if so, check those dependencies has been loaded or not.
            # if not, then put this package into dependent_packages and
            # load it later. otherwise load it now.
            if (package_class is None or
                len(package_class.DEPENDS) == 0 or
                self._is_dependencies_loaded(package_class.DEPENDS) is True) and \
               self._is_parent_loaded(package) is True:

                instance = None
                if package_class is not None:
                    instance = package_class()
                    instance.load_configs(config_services)

                component_name = None
                if instance is not None:
                    component_name = instance.COMPONENT_NAME
                self._load_component(package, components[package], component_name, **options)
            else:
                dependent_components[package] = components[package]

        # now, go through dependent components if any, and try to load them.
        if len(dependent_components) > 0:
            self._load_components(dependent_components, **options)

    def _get_loadable_components(self, **options):
        """
        gets all package and module names that should be loaded.

        :returns: tuple(core_components, application_components, test_components)

        :type core_components: dict(list[str] package_name: modules)

        :type application_components: dict(list[str] package_name: modules)

        :type test_components: dict(list[str] package_name: modules)

        :type package_name: list(str module: module name)

        :rtype: tuple(dict(str: list[str]), dict(str: list[str]), dict(str: list[str]))
        """

        # a dictionary containing all package names and their respective modules.
        # in the form of {package_name: [modules]}.
        core_components = DTO()
        application_components = DTO()
        test_components = DTO()

        for root, directories, file_names in os.walk(self._root_directory, followlinks=True):

            for directory in directories:
                combined_path = os.path.join(root, directory)
                if not self._is_package(combined_path):
                    continue

                package_name = self._get_package_name(combined_path)
                if self._is_ignored_package(package_name):
                    continue

                if self._is_core_package(package_name):
                    core_components[package_name] = []
                elif self._is_test_package(package_name):
                    test_components[package_name] = []
                else:
                    application_components[package_name] = []

                files = os.listdir(combined_path)
                for file_name in files:
                    if not self._is_module(file_name):
                        continue

                    module_name = file_name.replace('.py', '')
                    full_module_name = self._get_module_name(package_name, module_name)
                    if self._is_ignored_module(full_module_name):
                        continue

                    if self._is_core_module(full_module_name):
                        core_components[package_name].append(full_module_name)
                    elif self._is_test_module(full_module_name):
                        test_components[package_name].append(full_module_name)
                    else:
                        application_components[package_name].append(full_module_name)

        return core_components, application_components, test_components

    def _is_ignored_package(self, package_name):
        """
        gets a value indicating that given package should be ignored.

        :param str package_name: full package name.
                                 example package_name = `pyrin.database`.

        :rtype: bool
        """

        for ignored in IGNORED_PACKAGES:
            if package_name.startswith(ignored):
                return True

        return False

    def _is_ignored_module(self, module_name):
        """
        gets a value indicating that given module should be ignored.

        :param str module_name: full module name.
                                example module_name = `pyrin.api.error_handlers`.

        :rtype: bool
        """

        for ignored in IGNORED_MODULES:
            if module_name.endswith(ignored):
                return True

        return False

    def _is_core_component(self, component_name):
        """
        gets a value indicating that given component is a core component.

        :param str component_name: full package or module name.

        :rtype: bool
        """

        # this if condition is to make it possible for the top level
        # application package name to start with any of core packages names.
        # for example: 'pyrin_sample'
        root_package = component_name.split('.')[0]
        root_core_packages = [name.split('.')[0] for name in CORE_PACKAGES]
        if root_package not in root_core_packages:
            return False

        for core in CORE_PACKAGES:
            if component_name.startswith(core):
                return True

        return False

    def _is_core_package(self, package_name):
        """
        gets a value indicating that given package is a core package.

        :param str package_name: full package name.
                                 example package_name = 'pyrin.api'

        :rtype: bool
        """

        return self._is_core_component(package_name)

    def _is_core_module(self, module_name):
        """
        gets a value indicating that given module is a core module.

        :param str module_name: full module name.
                                example module_name = 'pyrin.api.error_handlers'

        :rtype: bool
        """

        return self._is_core_component(module_name)

    def _is_test_component(self, component_name):
        """
        gets a value indicating that given component is a test component.

        :param str component_name: full package or module name.

        :rtype: bool
        """

        for test in TEST_PACKAGES:
            if component_name.startswith(test):
                return True

        return False

    def _is_test_package(self, package_name):
        """
        gets a value indicating that given package is a test package.

        :param str package_name: full package name.
                                 example package_name = 'test.api'

        :rtype: bool
        """

        return self._is_test_component(package_name)

    def _is_test_module(self, module_name):
        """
        gets a value indicating that given module is a test module.

        :param str module_name: full module name.
                                example module_name = 'test.api.error_handlers'

        :rtype: bool
        """

        return self._is_test_component(module_name)

    def _get_package_name(self, path):
        """
        gets the full package name from provided path.

        :param str path: full path of package.
                         example path = `/home/src/pyrin/database`.

        :rtype: str
        """

        return path.replace(self._root_directory, '').replace('/', '.')

    def _get_module_name(self, package_name, module_name):
        """
        gets the full module name.

        :param str package_name: package name.
                                 example package_name = `pyrin.database`.

        :param str module_name: module name.
                                example module_name = `api`.

        :rtype: str
        """

        return '{package}.{module}'.format(package=package_name, module=module_name)

    def _is_package(self, path):
        """
        gets a value indicating that given path belongs to a python package.
        it simply checks that `__init__` module exists or not.

        :param str path: full path of package.
                         example path = `/home/src/pyrin/database`.

        :rtype: bool
        """

        return self._has_module(path, '__init__')

    def _is_module(self, file_name):
        """
        gets a value indicating that given file is a standalone
        python module (excluding `__init__` module which belongs to package).
        it simply checks that file name ends with '.py' and not being `__init__.py`.

        :param str file_name: file name.
                              example file_name = `services.py`
        :rtype: bool
        """

        return file_name.endswith('.py') and '__init__.py' not in file_name

    def _has_module(self, path, module_name):
        """
        gets a value indicating that given module exists in specified path.

        :param str path: path to check module availability in it.
                         example path = `/home/src/pyrin/database`.

        :param str module_name: module name.
                                example module_name = `__init__`.

        :rtype: bool
        """

        return os.path.isfile(os.path.join(path, '{module}.py'.format(module=module_name)))

    def _get_package_class(self, package_name):
        """
        gets the package class implemented in given package if available, otherwise returns None.

        :param str package_name: full package name.
                                 example package_name = `pyrin.api`.

        :rtype: type
        """

        module = self.load(package_name)
        package_class = None

        for cls in module.__dict__.values():
            if inspect.isclass(cls) and cls is not Package and issubclass(cls, Package):
                package_class = cls
        return package_class

    def _is_dependencies_loaded(self, dependencies):
        """
        gets a value indicating that given dependencies has been already loaded.

        :param list[str] dependencies: full dependency names.
                                       example dependencies = `pyrin.logging`

        :rtype: bool
        """

        for dependency in dependencies:
            if dependency not in self._loaded_packages:
                return False

        return True

    def _is_parent_loaded(self, package_name):
        """
        gets a value indicating that given package's parent package has been loaded.

        :param str package_name: full package name.
                                 example package_name = `pyrin.encryption.handlers`

        :raises InvalidPackageNameError: invalid package name error.

        :rtype: bool
        """

        items = package_name.split('.')
        parent_package = None

        length = len(items)
        if length == 1:
            parent_package = items[0]
        elif length > 1:
            parent_package = '.'.join(items[:-1])
        else:
            raise InvalidPackageNameError('Input package name [{package_name}] is invalid.'
                                          .format(package_name=package_name))

        # application root packages like `pyrin`, has no
        # parent so it should always return `True` for them.
        if parent_package == package_name:
            return True

        return self._is_dependencies_loaded([parent_package])

    def _get_hooks(self):
        """
        gets all registered hooks.

        :rtype: list[PackagingHookBase]
        """

        return self.__hooks

    def register_hook(self, instance):
        """
        registers the given instance into packaging hooks.

        :param PackagingHookBase instance: packaging hook instance to be registered.

        :raises InvalidPackagingHookTypeError: invalid packaging hook type error.
        """

        if not isinstance(instance, PackagingHookBase):
            raise InvalidPackagingHookTypeError('Input parameter [{instance}] is '
                                                'not an instance of PackagingHookBase.'
                                                .format(instance=str(instance)))

        self.__hooks.append(instance)
