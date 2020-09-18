# -*- coding: utf-8 -*-
"""
celery cli handlers params module.
"""

import pyrin.configuration.services as config_services

from pyrin.task_queues.celery.cli.interface import CeleryCLIParamBase
from pyrin.cli.arguments import KeywordArgument, BooleanArgument, \
    PositionalArgument, CompositeKeywordArgument, CompositePositionalArgument


class LogFileParam(KeywordArgument, CeleryCLIParamBase):
    """
    log file param class.
    """

    def __init__(self, default=None):
        """
        initializes an instance of LogFileParam.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
        """

        super().__init__('logfile', '--logfile', default=default)


class PIDFileParam(KeywordArgument, CeleryCLIParamBase):
    """
    pid file param class.
    """

    def __init__(self, default=None):
        """
        initializes an instance of PIDFileParam.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
        """

        super().__init__('pidfile', '--pidfile', default=default)


class LogLevelParam(KeywordArgument, CeleryCLIParamBase):
    """
    log level param class.
    """

    def __init__(self, default=None):
        """
        initializes an instance of LogLevelParam.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
        """

        super().__init__('loglevel', '--loglevel', default=default)


class WorkerLogFileParam(LogFileParam):
    """
    worker log file param class.
    """

    def __init__(self, default=None):
        """
        initializes an instance of WorkerLogFileParam.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
                               defaults to `worker_log_file` value
                               form `celery` config store if not provided.
        """

        if default is None:
            default = config_services.get_active('celery', 'worker_log_file')

        super().__init__(default=default)


class WorkerPIDFileParam(PIDFileParam):
    """
    worker pid file param class.
    """

    def __init__(self, default=None):
        """
        initializes an instance of WorkerPIDFileParam.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
                               defaults to `worker_pid_file` value
                               form `celery` config store if not provided.
        """

        if default is None:
            default = config_services.get_active('celery', 'worker_pid_file')

        super().__init__(default=default)


class WorkerLogLevelParam(LogLevelParam):
    """
    worker log level param class.
    """

    def __init__(self, default=None):
        """
        initializes an instance of WorkerLogLevelParam.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
                               defaults to `worker_log_level` value
                               form `celery` config store if not provided.
        """

        if default is None:
            default = config_services.get_active('celery', 'worker_log_level')

        super().__init__(default=default)


class ConcurrencyParam(KeywordArgument, CeleryCLIParamBase):
    """
    concurrency param class.
    """

    def __init__(self, default=None):
        """
        initializes an instance of ConcurrencyParam.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
                               defaults to `worker_concurrency` value
                               form `celery` config store if not provided.
        """

        if default is None:
            default = config_services.get_active('celery', 'worker_concurrency')

        super().__init__('concurrency', '--concurrency', default=default)


class HostnameParam(KeywordArgument, CeleryCLIParamBase):
    """
    hostname param class.
    """

    def __init__(self, default=None):
        """
        initializes an instance of HostnameParam.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
                               defaults to `worker_hostname` value
                               form `celery` config store if not provided.
        """

        if default is None:
            default = config_services.get_active('celery', 'worker_hostname')

        super().__init__('hostname', '--hostname', default=default)


class BeatParam(BooleanArgument, CeleryCLIParamBase):
    """
    beat param class.
    """

    def __init__(self, default=None):
        """
        initializes an instance of BeatParam.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
        """

        super().__init__('beat', '--beat', default=default)


class AutoScaleParam(CompositeKeywordArgument, CeleryCLIParamBase):
    """
    autoscale param class.
    """

    def __init__(self, default=None):
        """
        initializes an instance of AutoScaleParam.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
                               defaults to `worker_autoscale` value
                               form `celery` config store if not provided.
        """

        if default is None:
            default = config_services.get_active('celery', 'worker_autoscale')

        super().__init__('autoscale', '--autoscale', default=default, separator=',')


class QueuesParam(CompositeKeywordArgument, CeleryCLIParamBase):
    """
    queues param class.
    """

    def __init__(self, default=None):
        """
        initializes an instance of QueuesParam.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
                               defaults to `worker_queues` value
                               form `celery` config store if not provided.
        """

        if default is None:
            default = config_services.get_active('celery', 'worker_queues')

        super().__init__('queues', '--queues', default=default, separator=',')


class PurgeParam(BooleanArgument, CeleryCLIParamBase):
    """
    purge param class.
    """

    def __init__(self, default=None):
        """
        initializes an instance of PurgeParam.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
        """

        super().__init__('purge', '--purge', default=default)


class OptimizationParam(KeywordArgument, CeleryCLIParamBase):
    """
    optimization param class.
    """

    def __init__(self, default=None):
        """
        initializes an instance of OptimizationParam.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
                               defaults to `worker_optimization` value
                               form `celery` config store if not provided.
        """

        if default is None:
            default = config_services.get_active('celery', 'worker_optimization')

        super().__init__('optimization', '-O', default=default)


class BeatLogFileParam(LogFileParam):
    """
    beat log file param class.
    """

    def __init__(self, default=None):
        """
        initializes an instance of BeatLogFileParam.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
                               defaults to `beat_log_file` value
                               form `celery` config store if not provided.
        """

        if default is None:
            default = config_services.get_active('celery', 'beat_log_file')

        super().__init__(default=default)


class BeatPIDFileParam(PIDFileParam):
    """
    beat pid file param class.
    """

    def __init__(self, default=None):
        """
        initializes an instance of BeatPIDFileParam.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
                               defaults to `beat_pid_file` value
                               form `celery` config store if not provided.
        """

        if default is None:
            default = config_services.get_active('celery', 'beat_pid_file')

        super().__init__(default=default)


class BeatLogLevelParam(LogLevelParam):
    """
    beat log level param class.
    """

    def __init__(self, default=None):
        """
        initializes an instance of BeatLogLevelParam.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
                               defaults to `beat_log_level` value
                               form `celery` config store if not provided.
        """

        if default is None:
            default = config_services.get_active('celery', 'beat_log_level')

        super().__init__(default=default)


class TaskIDParam(PositionalArgument, CeleryCLIParamBase):
    """
    task id param class.
    """

    def __init__(self, index=None, default=None, **options):
        """
        initializes an instance of TaskIDParam.

        :param int index: zero based index of this param in cli command inputs.
                          defaults to 0 if not provided.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
                               defaults to None if not provided.

        :keyword bool validate_index: specifies that index of this argument
                                      must be validated. it could be helpful
                                      to set this to False when there are multiple
                                      arguments with the same index that will appear
                                      in different situations.
                                      defaults to True if not provided.
        """

        if index is None:
            index = 0

        super().__init__('task_id', index, default=default, **options)


class TracebackParam(BooleanArgument, CeleryCLIParamBase):
    """
    traceback param class.
    """

    def __init__(self, default=None):
        """
        initializes an instance of TracebackParam.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
        """

        super().__init__('traceback', '--traceback', default=default)


class TaskNameParam(KeywordArgument, CeleryCLIParamBase):
    """
    task name param class.
    """

    def __init__(self, default=None):
        """
        initializes an instance of TaskNameParam.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
        """

        super().__init__('task', '--task', default=default)


class InspectMethodParam(PositionalArgument, CeleryCLIParamBase):
    """
    inspect method param class.
    """

    def __init__(self, index=None, default=None, **options):
        """
        initializes an instance of InspectMethodParam.

        :param int index: zero based index of this param in cli command inputs.
                          defaults to 0 if not provided.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
                               defaults to None if not provided.

        :keyword bool validate_index: specifies that index of this argument
                                      must be validated. it could be helpful
                                      to set this to False when there are multiple
                                      arguments with the same index that will appear
                                      in different situations.
                                      defaults to True if not provided.
        """

        if index is None:
            index = 0

        super().__init__('method', index, default=default, **options)


class TimeoutParam(KeywordArgument, CeleryCLIParamBase):
    """
    timeout param class.
    """

    def __init__(self, default=None):
        """
        initializes an instance of TimeoutParam.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
        """

        super().__init__('timeout', '--timeout', default=default)


class DestinationParam(CompositeKeywordArgument, CeleryCLIParamBase):
    """
    destination param class.
    """

    def __init__(self, default=None):
        """
        initializes an instance of DestinationParam.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
        """

        super().__init__('destination', '--destination',
                         default=default, separator=',')


class JSONParam(BooleanArgument, CeleryCLIParamBase):
    """
    json param class.
    """

    def __init__(self, default=None):
        """
        initializes an instance of JSONParam.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
        """

        super().__init__('json', '--json', default=default)


class IncludeDefaultsParam(PositionalArgument, CeleryCLIParamBase):
    """
    include defaults param class.
    """

    def __init__(self, index=None, default=None, **options):
        """
        initializes an instance of IncludeDefaultsParam.

        :param int index: zero based index of this param in cli command inputs.
                          defaults to 0 if not provided.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
                               defaults to None if not provided.

        :keyword bool validate_index: specifies that index of this argument
                                      must be validated. it could be helpful
                                      to set this to False when there are multiple
                                      arguments with the same index that will appear
                                      in different situations.
                                      defaults to True if not provided.
        """

        if index is None:
            index = 0

        super().__init__('include_defaults', index, default=default, **options)


class SamplesCountParam(PositionalArgument, CeleryCLIParamBase):
    """
    samples count param class.
    """

    def __init__(self, index=None, default=None, **options):
        """
        initializes an instance of SamplesCountParam.

        :param int index: zero based index of this param in cli command inputs.
                          defaults to 0 if not provided.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
                               defaults to None if not provided.

        :keyword bool validate_index: specifies that index of this argument
                                      must be validated. it could be helpful
                                      to set this to False when there are multiple
                                      arguments with the same index that will appear
                                      in different situations.
                                      defaults to True if not provided.
        """

        if index is None:
            index = 0

        super().__init__('samples_count', index, default=default, **options)


class ObjectTypeParam(PositionalArgument, CeleryCLIParamBase):
    """
    object type param class.
    """

    def __init__(self, index=None, default=None, **options):
        """
        initializes an instance of ObjectTypeParam.

        :param int index: zero based index of this param in cli command inputs.
                          defaults to 0 if not provided.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
                               defaults to None if not provided.

        :keyword bool validate_index: specifies that index of this argument
                                      must be validated. it could be helpful
                                      to set this to False when there are multiple
                                      arguments with the same index that will appear
                                      in different situations.
                                      defaults to True if not provided.
        """

        if index is None:
            index = 0

        super().__init__('object_type', index, default=default, **options)


class CountParam(PositionalArgument, CeleryCLIParamBase):
    """
    count param class.
    """

    def __init__(self, index=None, default=None, **options):
        """
        initializes an instance of CountParam.

        :param int index: zero based index of this param in cli command inputs.
                          defaults to 0 if not provided.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
                               defaults to None if not provided.

        :keyword bool validate_index: specifies that index of this argument
                                      must be validated. it could be helpful
                                      to set this to False when there are multiple
                                      arguments with the same index that will appear
                                      in different situations.
                                      defaults to True if not provided.
        """

        if index is None:
            index = 0

        super().__init__('count', index, default=default, **options)


class MaxDepthParam(PositionalArgument, CeleryCLIParamBase):
    """
    max depth param class.
    """

    def __init__(self, index=None, default=None, **options):
        """
        initializes an instance of MaxDepthParam.

        :param int index: zero based index of this param in cli command inputs.
                          defaults to 0 if not provided.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
                               defaults to None if not provided.

        :keyword bool validate_index: specifies that index of this argument
                                      must be validated. it could be helpful
                                      to set this to False when there are multiple
                                      arguments with the same index that will appear
                                      in different situations.
                                      defaults to True if not provided.
        """

        if index is None:
            index = 0

        super().__init__('max_depth', index, default=default, **options)


class TaskIDListParam(CompositePositionalArgument, CeleryCLIParamBase):
    """
    task id list param class.
    """

    def __init__(self, index=None, default=None, **options):
        """
        initializes an instance of TaskIDListParam.

        :param int index: zero based index of this param in cli command inputs.
                          defaults to 0 if not provided.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
                               defaults to None if not provided.

        :keyword bool validate_index: specifies that index of this argument
                                      must be validated. it could be helpful
                                      to set this to False when there are multiple
                                      arguments with the same index that will appear
                                      in different situations.
                                      defaults to True if not provided.
        """

        if index is None:
            index = 0

        super().__init__('task_ids', index, default=default,
                         separator=' ', **options)


class AttributeListParam(CompositePositionalArgument, CeleryCLIParamBase):
    """
    attribute list param class.
    """

    def __init__(self, index=None, default=None, **options):
        """
        initializes an instance of AttributeListParam.

        :param int index: zero based index of this param in cli command inputs.
                          defaults to 0 if not provided.

        :param object default: default value to be emitted to
                               cli if this param is not available.
                               if set to None, this param will not
                               be emitted at all.
                               defaults to None if not provided.

        :keyword bool validate_index: specifies that index of this argument
                                      must be validated. it could be helpful
                                      to set this to False when there are multiple
                                      arguments with the same index that will appear
                                      in different situations.
                                      defaults to True if not provided.
        """

        if index is None:
            index = 0

        super().__init__('attributes', index, default=default,
                         separator=' ', **options)
