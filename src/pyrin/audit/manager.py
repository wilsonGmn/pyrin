# -*- coding: utf-8 -*-
"""
audit manager module.
"""

import traceback
import platform

import pyrin
import pyrin.application.services as application_services
import pyrin.packaging.services as packaging_services
import pyrin.globalization.datetime.services as datetime_services
import pyrin.processor.response.status.services as status_services
import pyrin.configuration.services as config_services

from pyrin.audit.enumerations import InspectionStatusEnum
from pyrin.audit.exceptions import InvalidAuditHookTypeError
from pyrin.audit.hooks import AuditHookBase
from pyrin.core.enumerations import ServerErrorResponseCodeEnum
from pyrin.core.mixin import HookMixin
from pyrin.core.structs import Manager
from pyrin.audit import AuditPackage


class AuditManager(Manager, HookMixin):
    """
    audit manager class.

    this class provides some hooks to let different packages expose some audit services.
    it could be helpful to check system stability and status after a new deployment.
    """

    package_class = AuditPackage
    hook_type = AuditHookBase
    invalid_hook_type_error = InvalidAuditHookTypeError

    def _inspect_packages(self, **options):
        """
        this method will call `inspect` method of all registered hooks.

        it includes available info of all registered hooks, but it could be customized.
        each registered hook could be excluded from result if the related name of the hook
        is passed with False value. for example `database=False`.

        it returns a tuple of two values. first value is a dict containing the data provided
        by all registered hooks, and the second value is a bool value indicating that all
        hooks have been succeeded or not.

        :keyword bool traceback: specifies that on failure report, it must include
                                 the traceback of errors.
                                 defaults to True if not provided.

        :rtype: tuple[dict, bool]
        """

        data = {}
        all_succeeded = True
        include_traceback = options.get('traceback', True)
        for hook in self._get_hooks():
            try:
                should_inspect = options.get(hook.audit_name, True)
                if should_inspect is True:
                    result, succeeded = hook.inspect(**options)
                    if succeeded is False:
                        all_succeeded = False
                    data[hook.audit_name] = result
            except Exception as error:
                all_succeeded = False
                error_data = dict(status=InspectionStatusEnum.FAILED,
                                  error=str(error))
                if include_traceback is not False:
                    error_data.update(traceback=traceback.format_exc())
                data[hook.audit_name] = error_data

        return data, all_succeeded

    def inspect(self, **options):
        """
        inspects all registered packages and gets inspection data.

        it includes all available info, but it could be customized using different options.
        other custom implementations could also be excluded from result if the related name
        of their hook is passed with False value. for example `database=False`.

        it returns a tuple of two values. the first value is a dict containing the
        inspection data, and the second value is the related status code for the response.
        in case of any inspection has been failed, the status code will be internal
        server error 500.

        :keyword bool application: specifies that application info must be included.
        :keyword bool packages: specifies that loaded packages info must be included.
        :keyword bool framework: specifies that framework info must be included.
        :keyword bool python: specifies that python info must be included.
        :keyword bool os: specifies that operating system info must be included.
        :keyword bool hardware: specifies that hardware info must be included.

        :keyword bool traceback: specifies that on failure report, it must include
                                 the traceback of errors.
                                 defaults to True if not provided.

        :returns: tuple[dict(dict application: application info,
                             dict packages: loaded packages info,
                             dict framework: framework info,
                             dict python: python info,
                             dict platform: platform info),
                        int status_code]
        :rtype: tuple[dict, int]
        """

        application = options.get('application', True)
        packages = options.get('packages', True)
        framework = options.get('framework', True)
        python = options.get('python', True)

        data, succeeded = self._inspect_packages(**options)

        if application is True:
            data.update(application=self.get_application_info(**options))

        if packages is True:
            packages = packaging_services.get_loaded_packages()
            packages_info = dict(names=packages,
                                 count=len(packages))
            data.update(packages=packages_info)

        if framework is True:
            data.update(framework=self.get_framework_info(**options))

        if python is True:
            data.update(python=self.get_python_info(**options))

        platform_info = self.get_platform_info(**options)
        if len(platform_info) > 0:
            data.update(platform=platform_info)

        if succeeded is False:
            return data, ServerErrorResponseCodeEnum.INTERNAL_SERVER_ERROR

        return data, status_services.get_status_code()

    def get_application_info(self, **options):
        """
        gets the info of current application.

        :returns: dict(str name: application name,
                       datetime datetime: application current datetime)
        :rtype: dict
        """

        data = {}
        data.update(name=application_services.get_application_name(),
                    datetime=datetime_services.now())
        return data

    def get_framework_info(self, **options):
        """
        gets the info of current framework.

        :returns: dict(str name: framework name,
                       str version: framework version)
        :rtype: dict
        """

        data = {}
        data.update(name='pyrin', version=pyrin.__version__)
        return data

    def get_python_info(self, **options):
        """
        gets the current python version info which application is running on it.

        :returns: dict(str version: python version,
                       str implementation: python implementation)
        :rtype: dict
        """

        data = {}
        data.update(version=platform.python_version(),
                    implementation=platform.python_implementation())

        return data

    def get_operating_system_info(self, **options):
        """
        gets the current operating system info.

        :returns: dict(str name: os name,
                       str release: os release,
                       str version: os version)
        :rtype: dict
        """

        data = {}
        data.update(name=platform.system(),
                    release=platform.release(),
                    version=platform.version())

        return data

    def get_hardware_info(self, **options):
        """
        gets the current machine's hardware info.

        :returns: dict(str processor: processor name,
                       str machine: machine name)
        :rtype: dict
        """

        data = {}
        data.update(processor=platform.processor(),
                    machine=platform.machine())

        return data

    def get_platform_info(self, **options):
        """
        gets the platform info of current machine.

        it includes all available info, but it could be customized using different options.

        :keyword bool os: specifies that operating system info must be included.
        :keyword bool hardware: specifies that hardware info must be included.

        :returns: dict(dict os: os info,
                       dict hardware: hardware info)
        :rtype: dict
        """

        os = options.get('os', True)
        hardware = options.get('hardware', True)

        data = {}

        if os is True:
            data.update(os=self.get_operating_system_info(**options))

        if hardware is True:
            data.update(hardware=self.get_hardware_info(**options))

        return data

    def get_audit_configurations(self):
        """
        gets the audit api configurations.

        :returns: dict(bool enabled: enable audit api,
                       bool authenticated: audit api access type,
                       int request_limit: audit api request count limit,
                       str url: audit api exposed url)
        :rtype: dict
        """

        return config_services.get_active_section('audit')
