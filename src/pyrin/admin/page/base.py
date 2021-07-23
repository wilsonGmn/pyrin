# -*- coding: utf-8 -*-
"""
admin page base module.
"""

import inspect

import pyrin.filtering.services as filtering_services
import pyrin.validator.services as validator_services
import pyrin.security.session.services as session_services
import pyrin.database.services as database_services

from pyrin.core.globals import _
from pyrin.admin.interface import AbstractAdminPage
from pyrin.admin.page.schema import AdminSchema
from pyrin.core.globals import SECURE_TRUE, SECURE_FALSE
from pyrin.admin.page.mixin import AdminPageCacheMixin
from pyrin.caching.mixin.decorators import fast_cache
from pyrin.database.services import get_current_store
from pyrin.database.model.base import BaseEntity
from pyrin.security.session.enumerations import RequestContextEnum
from pyrin.admin.page.exceptions import InvalidListFieldError, ListFieldRequiredError, \
    InvalidMethodNameError, InvalidAdminEntityTypeError, AdminNameRequiredError, \
    AdminRegisterNameRequiredError, RequiredValuesNotProvidedError, \
    CompositePrimaryKeysNotSupportedError


class AdminPage(AbstractAdminPage, AdminPageCacheMixin):
    """
    admin page class.

    all admin pages must be subclassed from this.
    """

    # ===================== REQUIRED CONFIGS ===================== #

    # the entity class that this admin page represents.
    entity = None

    # name of this admin page to be used for registration.
    # the register name is case-insensitive and must be unique for each admin page.
    register_name = None

    # name of this admin page for representation.
    name = None

    # ===================== LIST CONFIGS ===================== #

    # columns to show in list view. it could be a column attribute, an expression
    # level hybrid property or a string method name of this admin page.
    # the method should accept a single positional argument as current row.
    # for example: (UserEntity.id, UserEntity.fullname, 'title', UserDetailEntity.age)
    list_fields = ()

    # columns that will be selected from database and will be used to compute
    # another field's value but they will be removed from the final result and
    # will not be returned to client.
    # it could be a column attribute or an expression level hybrid property.
    # for example: (UserEntity.id, UserEntity.fullname, UserDetailEntity.age)
    list_temp_fields = ()

    # specifies that if 'list_fields' are not provided only show readable
    # columns of the entity in list view.
    list_only_readable = True

    # specifies that if 'list_fields' are not provided also show pk columns in list view.
    list_pk = True

    # specifies that if 'list_fields' are not provided also show fk columns in list view.
    list_fk = True

    # specifies that if 'list_fields' are not provided also show expression
    # level hybrid property columns in list view.
    list_expression_level_hybrid_properties = True

    # list of default ordering columns.
    # it must be string names. for example: ('first_name', '-last_name')
    list_ordering = ()

    # show the total count of records in list view.
    list_total_count = True

    # specifies that each row must have an index in it.
    list_indexed = False

    # list index name to be added to each row.
    list_index_name = None

    # start index of rows.
    list_start_index = 1

    # columns to show in list filter.
    list_filters = ()

    # max records per page.
    list_per_page = 100

    # max records to fetch on show all.
    list_max_show_all = 200

    # ===================== SERVICE CONFIGS ===================== #

    # a service to be used for create operation.
    # if not set, the default create operation of this admin page will be used.
    # the create service must also accept keyword arguments.
    create_service = None

    # a service to be used for update operation.
    # if not set, the default update operation of this admin page will be used.
    # the update service must accept a positional argument at the beginning as
    # the primary key of the related entity and also accept keyword arguments.
    update_service = None

    # a service to be used for remove operation.
    # if not set, the default remove operation of this admin page will be used.
    # the remove service must accept a single positional argument as the
    # primary key of the related entity.
    remove_service = None

    # ===================== PERMISSION CONFIGS ===================== #

    # specifies that this admin page has get permission.
    # note that if entity has composite primary key, it does not
    # have get permission and this value will be ignored.
    get_permission = True

    # specifies that this admin page has create permission.
    create_permission = True

    # specifies that this admin page has update permission.
    # note that if entity has composite primary key, it does not
    # have update permission and this value will be ignored.
    update_permission = True

    # specifies that this admin page has remove permission.
    # note that if entity has composite primary key, it does not
    # have remove permission and this value will be ignored.
    remove_permission = True

    # ===================== OTHER CONFIGS ===================== #

    # the category name to register this admin page in it.
    # all admin pages with the same category will be grouped together.
    # the category name is case-insensitive.
    category = None

    # plural name of this admin page for representation.
    plural_name = None

    # extra field names that are required to be provided for create and are
    # optional for update but they are not a field of the entity itself.
    # in the form of:
    # {str field_name: type field_type}
    # for example:
    # {'password': str, 'age': int, 'join_date': datetime}
    extra_data_fields = {}

    # column names to be used in search bar.
    search_fields = ()

    # related columns that need to open a separate form to be selected.
    raw_id_fields = ()

    # columns that are readonly in edit form.
    readonly_fields = ()

    def __init__(self, *args, **options):
        """
        initializes an instance of AdminPage.

        :raises InvalidAdminEntityTypeError: invalid admin entity type error.
        :raises AdminRegisterNameRequiredError: admin register name required error.
        :raises AdminNameRequiredError: admin name required error.
        """

        super().__init__()

        if not inspect.isclass(self.entity) or not issubclass(self.entity, BaseEntity):
            raise InvalidAdminEntityTypeError('The entity for [{admin}] class '
                                              'must be a subclass of [{base}].'
                                              .format(admin=self, base=BaseEntity))

        if self.register_name in (None, '') or self.register_name.isspace():
            raise AdminRegisterNameRequiredError('The register name for '
                                                 '[{admin}] class is required.'
                                                 .format(admin=self))

        if self.name in (None, '') or self.name.isspace():
            raise AdminNameRequiredError('The name for [{admin}] class is required.'
                                         .format(admin=self))

        self.__populate_caches()
        # list of method names of this admin page to be used for processing the results.
        self._method_names = self._extract_method_names()
        self._schema = AdminSchema(self,
                                   indexed=self.list_indexed,
                                   start_index=self.list_start_index,
                                   index_name=self.list_index_name,
                                   exclude=self._get_list_temp_field_names())

    def __populate_caches(self):
        """
        populates required caches of this admin page.
        """

        self._get_list_field_names()
        self._get_list_temp_field_names()
        self._get_selectable_fields()

    @classmethod
    @fast_cache
    def _get_primary_key_name(cls):
        """
        gets the name of the primary key of this admin page's related entity.

        note that if the entity has a composite primary key, this method raises an error.

        :rtype: str
        """

        if len(cls.entity.primary_key_columns) == 1:
            return cls.entity.primary_key_columns[0]

        raise CompositePrimaryKeysNotSupportedError('Composite primary keys are not '
                                                    'supported for admin page.')

    @classmethod
    def _get_primary_key_holder(cls, pk):
        """
        gets a dict with the primary key name of this page's entity set to the given value.

        :param object pk: value to be set to primary key.

        :rtype: dict
        """

        pk_name = cls._get_primary_key_name()
        pk_holder = dict()
        pk_holder[pk_name] = pk

        return pk_holder

    def _show_total_count(self):
        """
        gets a value indicating that total count must be shown on list view.

        :returns: SECURE_TRUE | SECURE_FALSE
        """

        if self.list_total_count is True:
            return SECURE_TRUE

        return SECURE_FALSE

    def _is_valid_field(self, field):
        """
        gets a value indicating that the provided field is a valid field for list fields.

        :param object field: field to be checked.

        :rtype: bool
        """

        return hasattr(field, 'key')

    def _is_valid_method(self, name):
        """
        gets a value indicating that the provided name is a valid method name of this admin page.

        :param str name: method name.

        :rtype: bool
        """

        method = getattr(self, name, None)
        return callable(method)

    @fast_cache
    def _extract_method_names(self):
        """
        extracts all valid method names from list fields.

        :rtype: tuple[str]
        """

        names = []
        for item in self.list_fields:
            if isinstance(item, str) and self._is_valid_method(item):
                names.append(item)

        return tuple(names)

    def _extract_field_names(self, fields, allow_string=True):
        """
        extracts fields names form given fields

        :param list | tuple fields: list of fields to extract their names.

        :param bool allow_string: specifies that string fields should also
                                  be accepted. defaults to True if not provided.

        :raises InvalidListFieldError: invalid list field error.

        :rtype: tuple[str]
        """

        names = []
        for item in fields:
            if self._is_valid_field(item):
                names.append(item.key)
            elif allow_string is True and isinstance(item, str) \
                    and self._is_valid_method(item):
                names.append(item)
            else:
                message = 'Provided field [{field}] is not a valid value. ' \
                          'it must be a column attribute{sign} ' \
                          'expression level hybrid property{end}'

                if allow_string is True:
                    message = message.format(
                        field=str(item), sign=',',
                        end=' or a string representing a method name of [{admin}] class.')
                else:
                    message = message.format(field=str(item), sign=' or',
                                             end='.')

                raise InvalidListFieldError(message.format(admin=self))

        return tuple(names)

    @fast_cache
    def _get_list_field_names(self):
        """
        gets all list field names of this admin page.

        :raises InvalidListFieldError: invalid list field error.

        :rtype: tuple[str]
        """

        all_fields = ()
        if not self.list_fields:
            all_fields = self._get_default_list_fields()
        else:
            all_fields = self.list_fields

        return self._extract_field_names(all_fields, allow_string=True)

    @fast_cache
    def _get_list_temp_field_names(self):
        """
        gets all list temp field names of this admin page.

        :raises InvalidListFieldError: invalid list field error.

        :rtype: tuple[str]
        """

        return self._extract_field_names(self.list_temp_fields, allow_string=False)

    @fast_cache
    def _get_default_list_fields(self):
        """
        gets defaults list fields for this admin page.

        :rtype: tuple
        """

        primary_keys = []
        primary_key_names = ()
        foreign_keys = []
        foreign_key_names = ()
        columns = []
        column_names = ()
        expression_level_hybrid_properties = []
        expression_level_hybrid_property_names = ()

        if self.list_only_readable is True:
            column_names = self.entity.readable_columns
            if self.list_pk is True:
                primary_key_names = self.entity.readable_primary_key_columns

            if self.list_fk is True:
                foreign_key_names = self.entity.readable_foreign_key_columns
        else:
            column_names = self.entity.all_columns
            if self.list_pk is True:
                primary_key_names = self.entity.primary_key_columns

            if self.list_fk is True:
                foreign_key_names = self.entity.foreign_key_columns

        if self.list_expression_level_hybrid_properties is True:
            expression_level_hybrid_property_names = \
                self.entity.expression_level_hybrid_properties

        for pk in primary_key_names:
            primary_keys.append(self.entity.get_attribute(pk))

        for fk in foreign_key_names:
            foreign_keys.append(self.entity.get_attribute(fk))

        for column in column_names:
            columns.append(self.entity.get_attribute(column))

        for hybrid_property in expression_level_hybrid_property_names:
            expression_level_hybrid_properties.append(
                self.entity.get_attribute(hybrid_property))

        primary_keys.extend(foreign_keys)
        primary_keys.extend(columns)
        primary_keys.extend(expression_level_hybrid_properties)
        return tuple(primary_keys)

    @fast_cache
    def _get_list_fields(self):
        """
        gets all fields from `list_fields` that are column or hybrid property.

        :rtype: tuple
        """

        if not self.list_fields:
            return self._get_default_list_fields()

        results = [item for item in self.list_fields if self._is_valid_field(item)]
        return tuple(results)

    @fast_cache
    def _get_list_temp_fields(self):
        """
        gets all fields from `list_temp_fields`.

        :rtype: tuple
        """

        results = [item for item in self.list_temp_fields if self._is_valid_field(item)]
        return tuple(results)

    @fast_cache
    def _get_selectable_fields(self):
        """
        gets all selectable fields of this admin page.

        :raises ListFieldRequiredError: list field required error.

        :rtype: tuple
        """

        results = self._get_list_fields() + self._get_list_temp_fields()
        if len(results) <= 0:
            raise ListFieldRequiredError('At least a single column attribute or '
                                         'expression level hybrid property must be '
                                         'provided in list fields or list temp fields '
                                         'of [{admin}] class.'.format(admin=self))

        return results

    def _perform_joins(self, query, **options):
        """
        performs joins on given query and returns a new query object.

        this method is intended to be overridden in subclasses if you want to
        provide columns of other entities in `list_fields` too.

        :param CoreQuery query: query instance.

        :rtype: CoreQuery
        """

        return query

    def _filter_query(self, query, **filters):
        """
        filters given query and returns a new query object.

        :param CoreQuery query: query instance.

        :rtype: CoreQuery
        """

        expressions = filtering_services.filter(self.entity, filters)
        return query.filter(*expressions)

    def _validate_filters(self, filters):
        """
        validates given filters.

        :param dict filters: filters to be validated.

        :raises ValidationError: validation error.
        """

        validator_services.validate_for_find(self.entity, filters)

    def _perform_order_by(self, query, **filters):
        """
        performs order by on given query and returns a new query object.

        :param CoreQuery query: query instance.

        :keyword str | list[str] order_by: order by columns.
                                           if not provided, defaults to `ordering`
                                           fields of this admin class.
        :rtype: CoreQuery
        """

        filters.setdefault(database_services.get_ordering_key(), self.list_ordering)
        return query.safe_order_by(self.entity,
                                   *self.entity.primary_key_columns,
                                   **filters)

    def _paginate_query(self, query, **filters):
        """
        paginates given query and returns a new query object.

        :param CoreQuery query: query instance.

        :keyword CoreColumn column: column to be used in count function.
                                    defaults to `*` if not provided.
                                    this is only used if `inject_total` is
                                    provided and a single query could be
                                    produced for count.

        :keyword bool distinct: specifies that count should
                                be executed on distinct select.
                                defaults to False if not provided.
                                note that `distinct` will only be
                                used if `column` is also provided.

        :keyword int __limit__: limit value.
        :keyword int __offset__: offset value.

        :rtype: CoreQuery
        """

        return query.paginate(inject_total=self._show_total_count(), **filters)

    def _process_find_results(self, results, **options):
        """
        processes the given results and returns a list of serialized values.

        :param list[ROW_RESULT] results: results to be processed.

        :rtype: list[dict]
        """

        paginator = session_services.get_request_context(RequestContextEnum.PAGINATOR)
        return self._schema.filter(results, paginator=paginator)

    def _has_single_primary_key(self):
        """
        gets a value indicating that the related entity has a single primary key.

        :rtype: bool
        """

        return len(self.entity.primary_key_columns) == 1

    @classmethod
    def _validate_extra_fields(cls, data):
        """
        validates that all extra required fields are available in data.

        :param dict data: data to be validated.

        :raises RequiredValuesNotProvidedError: required values not provided error.
        """

        not_present = []
        for name in cls.extra_data_fields:
            if data.get(name) is None:
                not_present.append(name)

        not_present = set(not_present)
        if len(not_present) > 0:
            raise RequiredValuesNotProvidedError(_('These values are required: {values}')
                                                 .format(values=list(not_present)))

    @classmethod
    def _process_created_entity(cls, entity, **data):
        """
        processes created entity if required.

        it must change the attributes of given entity in-place.

        :param pyrin.database.model.base.BaseEntity entity: created entity.

        :keyword **data: all data that has been passed to create method.
        """
        pass

    @classmethod
    def _create(cls, **data):
        """
        creates an entity with given data.

        :keyword **data: all data to be passed to create method.
        """

        entity = cls.entity(**data)
        cls._process_created_entity(entity, **data)
        entity.save()

    @classmethod
    def _process_updated_entity(cls, entity, **data):
        """
        processes updated entity if required.

        it must change the attributes of given entity in-place.

        :param pyrin.database.model.base.BaseEntity entity: updated entity.

        :keyword **data: all data that has been passed to update method.
        """
        pass

    @classmethod
    def _update(cls, pk, **data):
        """
        updates an entity with given data.

        :param object pk: entity primary key to be updated.

        :keyword **data: all data to be passed to update method.
        """

        store = get_current_store()
        entity = store.query(cls.entity).get(pk)
        entity.update(**data)
        cls._process_updated_entity(entity, **data)

    @classmethod
    def _remove(cls, pk):
        """
        deletes an entity with given pk.

        :param object pk: entity primary key to be deleted.
        """

        store = get_current_store()
        pk_name = cls._get_primary_key_name()
        pk_column = cls.entity.get_attribute(pk_name)
        store.query(cls.entity).filter(pk_column == pk).delete()

    def get_entity(self):
        """
        gets the entity class of this admin page.

        :rtype: BaseEntity
        """

        return self.entity

    def get_register_name(self):
        """
        gets the register name of this admin page.

        :rtype: str
        """

        return self.register_name.lower()

    def get_category(self):
        """
        gets the category of this admin page.

        it may return None if no category is set for this admin page.

        :rtype: str
        """

        if self.category not in (None, ''):
            return self.category.upper()

        return None

    def get(self, pk):
        """
        gets an entity with given primary key.

        :param object pk: primary key of entity to be get.

        :rtype: pyrin.database.model.base.BaseEntity
        """

        validator_services.validate(self.entity, **self._get_primary_key_holder(pk))
        store = get_current_store()
        entity = store.query(self.entity).get(pk)
        return entity

    def find(self, **filters):
        """
        finds entities with given filters.

        :keyword **filters: all filters to be passed to related find service.

        :raises ListFieldRequiredError: list field required error.

        :rtype: list[ROW_RESULT]
        """

        self._validate_filters(filters)
        store = get_current_store()
        query = store.query(*self._get_selectable_fields())
        query = self._perform_joins(query)
        query = self._filter_query(query, **filters)
        query = self._perform_order_by(query, **filters)
        query = self._paginate_query(query, **filters)
        results = query.all()
        return self._process_find_results(results, **filters)

    @classmethod
    def create(cls, **data):
        """
        creates an entity with given data.

        :keyword **data: all data to be passed to related create service.
        """

        validator_services.validate_dict(cls.entity, data)
        cls._validate_extra_fields(data)
        if cls.create_service is not None:
            cls.create_service(**data)
        else:
            cls._create(**data)

    @classmethod
    def update(cls, pk, **data):
        """
        updates an entity with given data.

        :param object pk: entity primary key to be updated.

        :keyword **data: all data to be passed to related update service.
        """

        validator_services.validate(cls.entity, **cls._get_primary_key_holder(pk))
        validator_services.validate_dict(cls.entity, data, for_update=True)
        if cls.update_service is not None:
            cls.update_service(pk, **data)
        else:
            cls._update(pk, **data)

    @classmethod
    def remove(cls, pk):
        """
        deletes an entity with given pk.

        :param object pk: entity primary key to be deleted.
        """

        validator_services.validate(cls.entity, **cls._get_primary_key_holder(pk))
        if cls.remove_service is not None:
            cls.remove_service(pk)
        else:
            cls._remove(pk)

    def call_method(self, name, argument):
        """
        calls the method with given name with given argument and returns the result.

        :param str name: method name.
        :param ROW_RESULT argument: the method argument.

        :raises InvalidMethodNameError: invalid method name error.

        :rtype: object
        """

        if name not in self.method_names:
            raise InvalidMethodNameError('Method [{method}] is not present in [{admin}] class.'
                                         .format(method=name, admin=self))

        method = getattr(self, name)
        return method(argument)

    def has_get_permission(self):
        """
        gets a value indicating that this admin page has get permission.

        note that entities with composite primary key does not support get.

        :rtype: bool
        """

        return self._has_single_primary_key() and self.get_permission

    def has_create_permission(self):
        """
        gets a value indicating that this admin page has create permission.

        :rtype: bool
        """

        return self.create_permission

    def has_update_permission(self):
        """
        gets a value indicating that this admin page has update permission.

        note that entities with composite primary key does not support update.

        :rtype: bool
        """

        return self._has_single_primary_key() and self.update_permission

    def has_remove_permission(self):
        """
        gets a value indicating that this admin page has remove permission.

        note that entities with composite primary key does not support remove.

        :rtype: bool
        """

        return self._has_single_primary_key() and self.remove_permission

    @property
    def method_names(self):
        """
        gets the list of all method names of this admin page to be used for result processing.

        :rtype: tuple[str]
        """

        return self._method_names
