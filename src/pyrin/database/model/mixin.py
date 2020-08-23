# -*- coding: utf-8 -*-
"""
model mixin module.

this module provides mixin classes for different features of declarative base entity.
if you want to implement a new declarative base class and not use the `CoreEntity`
provided by pyrin, you could define your new base class and it must be inherited
from `BaseEntity`, because application will check isinstance() on `BaseEntity` type
to detect models. and then implement your customized or new features in your base class.
then you must put `@as_declarative` decorator on your new base class. now all your concrete
entities must be inherited from the new declarative base class. note that you must use a
unique declarative base class for all your models, do not mix `CoreEntity` and your new
declarative base class usage. otherwise you will face problems in migrations and also
multi-database environments.
"""

import inspect

from abc import abstractmethod

from sqlalchemy import inspect as sqla_inspect
from sqlalchemy.exc import NoInspectionAvailable
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property

import pyrin.database.model.services as model_services
import pyrin.configuration.services as config_services
import pyrin.utils.misc as misc_utils

from pyrin.caching.decorators import local_cached
from pyrin.core.globals import LIST_TYPES, SECURE_TRUE, SECURE_FALSE
from pyrin.utils.custom_print import print_warning
from pyrin.core.exceptions import CoreNotImplementedError
from pyrin.database.services import get_current_store
from pyrin.core.structs import CoreObject, DTO
from pyrin.database.model.exceptions import ColumnNotExistedError, \
    InvalidDeclarativeBaseTypeError, InvalidDepthProvidedError
from pyrin.database.model.cache import ColumnCache, PrimaryKeyCache, \
    ForeignKeyCache, RelationshipCache, HybridPropertyCache, AttributeCache, MetadataCache


class ColumnMixin(CoreObject):
    """
    column mixin class.

    this class adds functionalities about columns (other than pk and fk) to its subclasses.
    """

    @property
    @local_cached(container=ColumnCache)
    def all_columns(self):
        """
        gets all column names of this entity.

        note that primary and foreign keys are not included in columns.
        column names will be calculated once and cached.

        :rtype: tuple[str]
        """

        return self.exposed_columns + self.not_exposed_columns

    @property
    @local_cached(container=ColumnCache)
    def exposed_columns(self):
        """
        gets exposed column names of this entity.

        which are those that have `exposed=True` in their definition
        and their name does not start with underscore `_`.
        note that primary and foreign keys are not included in columns.
        column names will be calculated once and cached.

        :rtype: tuple[str]
        """

        info = sqla_inspect(type(self))
        columns = tuple(attr.key for attr in info.column_attrs
                        if self.is_exposed(attr.key) is True and
                        attr.columns[0].is_foreign_key is False and
                        attr.columns[0].primary_key is False and
                        attr.columns[0].exposed is True)

        return columns

    @property
    @local_cached(container=ColumnCache)
    def not_exposed_columns(self):
        """
        gets not exposed column names of this entity.

        which are those that have `exposed=False` in their definition
        or their name starts with underscore `_`.
        note that primary and foreign keys are not included in columns.
        column names will be calculated once and cached.

        :rtype: tuple[str]
        """

        info = sqla_inspect(type(self))
        columns = tuple(attr.key for attr in info.column_attrs
                        if (self.is_exposed(attr.key) is False or
                            attr.columns[0].exposed is False) and
                        attr.columns[0].is_foreign_key is False and
                        attr.columns[0].primary_key is False)

        return columns


class RelationshipMixin(CoreObject):
    """
    relationship mixin class.

    this class adds functionalities about relationship properties to its subclasses.
    """

    @property
    @local_cached(container=RelationshipCache)
    def relationships(self):
        """
        gets all relationship property names of this entity.

        property names will be calculated once and cached.

        :rtype: tuple[str]
        """

        return self.exposed_relationships + self.not_exposed_relationships

    @property
    @local_cached(container=RelationshipCache)
    def exposed_relationships(self):
        """
        gets exposed relationship property names of this entity.

        which are those that their name does not start with underscore `_`.
        property names will be calculated once and cached.

        :rtype: tuple[str]
        """

        info = sqla_inspect(type(self))
        relationships = tuple(attr.key for attr in info.relationships
                              if self.is_exposed(attr.key) is True)
        return relationships

    @property
    @local_cached(container=RelationshipCache)
    def not_exposed_relationships(self):
        """
        gets not exposed relationship property names of this entity.

        which are those that their name starts with underscore `_`.
        property names will be calculated once and cached.

        :rtype: tuple[str]
        """

        info = sqla_inspect(type(self))
        relationships = tuple(attr.key for attr in info.relationships
                              if self.is_exposed(attr.key) is False)
        return relationships


class HybridPropertyMixin(CoreObject):
    """
    hybrid property mixin class.

    this class adds functionalities about all hybrid properties to its subclasses.
    """

    @property
    @local_cached(container=HybridPropertyCache)
    def all_hybrid_properties(self):
        """
        gets all hybrid property names of this entity.

        property names will be calculated once and cached.

        :rtype: tuple[str]
        """

        return self.exposed_hybrid_properties + self.not_exposed_hybrid_properties

    @property
    @local_cached(container=HybridPropertyCache)
    def exposed_hybrid_properties(self):
        """
        gets exposed hybrid property names of this entity.

        exposed hybrid properties are those that their name does
        not start with underscore `_`.
        property names will be calculated once and cached.

        :rtype: tuple[str]
        """

        info = sqla_inspect(type(self))
        hybrid_properties = tuple(item.__name__ for item in info.all_orm_descriptors
                                  if isinstance(item, hybrid_property)
                                  and self.is_exposed(item.__name__) is True)

        return hybrid_properties

    @property
    @local_cached(container=HybridPropertyCache)
    def not_exposed_hybrid_properties(self):
        """
        gets not exposed hybrid property names of this entity.

        not exposed hybrid properties are those that their
        name starts with underscore `_`.
        property names will be calculated once and cached.

        :rtype: tuple[str]
        """

        info = sqla_inspect(type(self))
        hybrid_properties = tuple(item.__name__ for item in info.all_orm_descriptors
                                  if isinstance(item, hybrid_property)
                                  and self.is_exposed(item.__name__) is False)

        return hybrid_properties


class PrimaryKeyMixin(CoreObject):
    """
    primary key mixin class.

    this class adds functionalities about primary keys to its subclasses.
    """

    def _is_primary_key_comparable(self, primary_key):
        """
        gets a value indicating that given primary key is comparable.

        the primary key is comparable if it is not None for single
        primary keys and if all the values in primary key tuple are
        not None for composite primary keys.

        :param object | tuple[object] primary_key: primary key value.

        :rtype: bool
        """

        if primary_key is None:
            return False

        if isinstance(primary_key, tuple):
            if len(primary_key) <= 0:
                return False
            else:
                return all(pk is not None for pk in primary_key)

        return True

    def primary_key(self, as_tuple=False):
        """
        gets the primary key value for this entity.

        it could be a single value or a tuple of values
        for composite primary keys.
        it could return None if no primary key is set for this entity.

        :param bool as_tuple: specifies that primary key value must be returned
                              as a tuple even if it's a single value.
                              defaults to False if not provided.

        :rtype: object | tuple[object]
        """

        columns = self.primary_key_columns
        if len(columns) <= 0:
            return None

        if as_tuple is False and len(columns) == 1:
            return getattr(self, columns[0])
        else:
            return tuple(getattr(self, col) for col in columns)

    @property
    @local_cached(container=PrimaryKeyCache)
    def primary_key_columns(self):
        """
        gets all primary key column names of this entity.

        column names will be calculated once and cached.

        :rtype: tuple[str]
        """

        return self.exposed_primary_key_columns + self.not_exposed_primary_key_columns

    @property
    @local_cached(container=PrimaryKeyCache)
    def exposed_primary_key_columns(self):
        """
        gets the exposed primary key column names of this entity.

        which are those that have `exposed=True` in their definition
        and their name does not start with underscore `_`.
        column names will be calculated once and cached.

        :rtype: tuple[str]
        """

        info = sqla_inspect(type(self))
        pk = tuple(info.get_property_by_column(col).key for col in info.primary_key
                   if self.is_exposed(info.get_property_by_column(col).key) is True
                   and col.exposed is True)

        return pk

    @property
    @local_cached(container=PrimaryKeyCache)
    def not_exposed_primary_key_columns(self):
        """
        gets not exposed primary key column names of this entity.

        which are those that have `exposed=False` in their definition
        or their name starts with underscore `_`.
        column names will be calculated once and cached.

        :rtype: tuple[str]
        """

        info = sqla_inspect(type(self))
        pk = tuple(info.get_property_by_column(col).key for col in info.primary_key
                   if self.is_exposed(info.get_property_by_column(col).key) is False
                   or col.exposed is False)

        return pk


class ForeignKeyMixin(CoreObject):
    """
    foreign key mixin class.

    this class adds functionalities about foreign keys to its subclasses.
    """

    @property
    @local_cached(container=ForeignKeyCache)
    def foreign_key_columns(self):
        """
        gets all foreign key column names of this entity.

        column names will be calculated once and cached.

        :rtype: tuple[str]
        """

        return self.exposed_foreign_key_columns + self.not_exposed_foreign_key_columns

    @property
    @local_cached(container=ForeignKeyCache)
    def exposed_foreign_key_columns(self):
        """
        gets the exposed foreign key column names of this entity.

        which are those that have `exposed=True` in their definition
        and their name does not start with underscore `_`.
        column names will be calculated once and cached.

        :rtype: tuple[str]
        """

        info = sqla_inspect(type(self))
        fk = tuple(attr.key for attr in info.column_attrs
                   if attr.columns[0].is_foreign_key is True
                   and self.is_exposed(attr.key) is True
                   and attr.columns[0].exposed is True)

        return fk

    @property
    @local_cached(container=ForeignKeyCache)
    def not_exposed_foreign_key_columns(self):
        """
        gets not exposed foreign key column names of this entity.

        which are those that have `exposed=False` in their definition
        or their name starts with underscore `_`.
        column names will be calculated once and cached.

        :rtype: tuple[str]
        """

        info = sqla_inspect(type(self))
        fk = tuple(attr.key for attr in info.column_attrs
                   if attr.columns[0].is_foreign_key is True and
                   (self.is_exposed(attr.key) is False or
                    attr.columns[0].exposed is False))

        return fk


class AttributeMixin(CoreObject):
    """
    attribute mixin class.

    this class adds functionalities about all attributes to its subclasses.
    attributes includes pk, fk, columns, relationships and hybrid properties.
    """

    @property
    @local_cached(container=AttributeCache)
    def all_attributes(self):
        """
        gets all attribute names of current entity.

        attribute names will be calculated once and cached.

        :rtype: tuple[str]
        """

        return self.all_exposed_attributes + self.all_not_exposed_attributes

    @property
    @local_cached(container=AttributeCache)
    def all_exposed_attributes(self):
        """
        gets all exposed attribute names of current entity.

        which are those that have `exposed=True` (only for columns) in
        their definition and their name does not start with underscore `_`.
        attribute names will be calculated once and cached.

        :rtype: tuple[str]
        """

        return self.exposed_primary_key_columns + self.exposed_foreign_key_columns + \
            self.exposed_columns + self.exposed_relationships + self.exposed_hybrid_properties

    @property
    @local_cached(container=AttributeCache)
    def all_not_exposed_attributes(self):
        """
        gets all not exposed attribute names of current entity.

        which are those that have `exposed=False` (only for columns) in
        their definition or their name starts with underscore `_`.
        attribute names will be calculated once and cached.

        :rtype: tuple[str]
        """

        return self.not_exposed_primary_key_columns + self.not_exposed_foreign_key_columns + \
            self.not_exposed_columns + self.not_exposed_relationships + \
            self.not_exposed_hybrid_properties

    def is_exposed(self, name):
        """
        gets a value indicating that an attribute with given name is exposed.

        it simply checks that the given name starts with an underscore `_`.
        if so, it is considered as not exposed.

        :param str name: attribute name.

        :rtype: bool
        """

        return not name.startswith('_')


class ConverterMixin(CoreObject):
    """
    converter mixin class.

    this class adds functionalities to convert dict to
    entity and vice versa to its subclasses.
    """

    # maximum allowed depth for conversion.
    # note that higher depth values may cause performance issues or
    # application failure in some cases. so if you do not know how
    # much depth is required for conversion, start without providing depth.
    # this value could be overridden in concrete entities if required.
    MAX_DEPTH = 5

    def to_dict(self, **options):
        """
        converts the entity into a dict and returns it.

        it could convert primary keys, foreign keys, other columns, hybrid
        properties and also relationship properties if `depth` is provided.
        the result dict by default only contains the exposed attributes of the
        entity which are those that have `exposed=True` (only for columns) and
        their name does not start with underscore `_`.

        :keyword SECURE_TRUE | SECURE_FALSE exposed_only: specifies that any column or attribute
                                                          which has `exposed=False` or its name
                                                          starts with underscore `_`, should not
                                                          be included in result dict. defaults to
                                                          `SECURE_TRUE` if not provided.

        :keyword dict[str, list[str]] | list[str] columns: column names to be included in result.
                                                           it could be a list of column names.
                                                           for example:
                                                           `columns=['id', 'name', 'age']`
                                                           but if you want to include
                                                           relationships, then columns for each
                                                           entity must be provided in a key for
                                                           that entity class name.
                                                           for example if there is `CarEntity` and
                                                           `PersonEntity`, it should be like this:
                                                           `columns=dict(CarEntity=
                                                                         ['id', 'name'],
                                                                         PersonEntity=
                                                                         ['id', 'age'])`
                                                           if provided column names are not
                                                           available in result, an error will
                                                           be raised.

        :note columns: dict[str entity_class_name, list[str column_name]] | list[str column_name]

        :keyword dict[str, dict[str, str]] | dict[str, str] rename: column names that must be
                                                                    renamed in the result.
                                                                    it could be a dict with keys
                                                                    as original column names and
                                                                    values as new column names
                                                                    that should be exposed instead
                                                                    of original column names.
                                                                    for example:
                                                                    `rename=dict(age='new_age',
                                                                                 name='new_name')`
                                                                    but if you want to include
                                                                    relationships, then you must
                                                                    provide a dict containing
                                                                    entity class name as key and
                                                                    for value, another dict
                                                                    containing original column
                                                                    names as keys, and column
                                                                    names that must be exposed
                                                                    instead of original names,
                                                                    as values. for example
                                                                    if there is `CarEntity` and `
                                                                    PersonEntity`, it should be
                                                                    like this:
                                                                    `rename=
                                                                    dict(CarEntity=
                                                                         dict(name='new_name'),
                                                                         PersonEntity=
                                                                         dict(age='new_age')`
                                                                    then, the value of `name`
                                                                    column in result will be
                                                                    returned as `new_name` column.
                                                                    and also value of `age` column
                                                                    in result will be returned as
                                                                    'new_age' column. if provided
                                                                    rename columns are not
                                                                    available in result, they
                                                                    will be ignored.

        :note rename: dict[str entity_class_name, dict[str original_column, str new_column]] |
                      dict[str original_column, str new_column]

        :keyword dict[str, list[str]] | list[str] exclude: column names to be excluded from
                                                           result. it could be a list of column
                                                           names. for example:
                                                           `exclude=['id', 'name', 'age']`
                                                           but if you want to include
                                                           relationships, then columns for each
                                                           entity must be provided in a key for
                                                           that entity class name.
                                                           for example if there is `CarEntity`
                                                           and `PersonEntity`, it should be
                                                           like this:
                                                           `exclude=dict(CarEntity=
                                                                         ['id', 'name'],
                                                                         PersonEntity=
                                                                         ['id', 'age'])`
                                                            if provided excluded columns are not
                                                            available in result, they will be
                                                            ignored.

        :note exclude: dict[str entity_class_name, list[str column_name]] | list[str column_name]

        :keyword int depth: a value indicating the depth for conversion.
                            for example if entity A has a relationship with
                            entity B and there is a list of B in A, if `depth=0`
                            is provided, then just columns of A will be available
                            in result dict, but if `depth=1` is provided, then all
                            B entities in A will also be included in the result dict.
                            actually, `depth` specifies that relationships in an
                            entity should be followed by how much depth.
                            note that, if `columns` is also provided, it is required to
                            specify relationship property names in provided columns.
                            otherwise they won't be included even if `depth` is provided.
                            defaults to `default_depth` value of database config store.
                            please be careful on increasing `depth`, it could fail
                            application if set to higher values. choose it wisely.
                            normally the maximum acceptable `depth` would be 2 or 3.
                            there is a hard limit for max valid `depth` which is set
                            in `ConverterMixin.MAX_DEPTH` class variable. providing higher
                            `depth` value than this limit, will cause an error.

        :raises ColumnNotExistedError: column not existed error.
        :raises InvalidDepthProvidedError: invalid depth provided error.

        :rtype: dict
        """

        all_attributes = None
        relations = None
        requested_columns, rename, excluded_columns = self._extract_conditions(**options)
        exposed_only = options.get('exposed_only', SECURE_TRUE)

        depth = options.get('depth', None)
        if depth is None:
            depth = config_services.get('database', 'conversion', 'default_depth')

        if exposed_only is SECURE_FALSE:
            all_attributes = self.all_attributes
            relations = self.relationships
        else:
            all_attributes = self.all_exposed_attributes
            relations = self.exposed_relationships

        requested_relationships = []
        all_attributes = set(all_attributes)
        if len(requested_columns) > 0:
            not_existed = requested_columns.difference(all_attributes)
            if len(not_existed) > 0:
                raise ColumnNotExistedError('Requested columns or relationship properties '
                                            '{columns} are not available in entity [{entity}]. '
                                            'it might be because of "exposed_only" '
                                            'parameter value passed to this method.'
                                            .format(columns=list(not_existed), entity=self))
        else:
            requested_columns = all_attributes.difference(excluded_columns)

        result = DTO()
        for col in requested_columns:
            if col in relations:
                requested_relationships.append(col)
            else:
                result[rename.get(col, col)] = getattr(self, col)

        if depth > 0 and len(requested_relationships) > 0:
            if depth > self.MAX_DEPTH:
                raise InvalidDepthProvidedError('Maximum valid "depth" for conversion '
                                                'is [{max_depth}]. provided depth '
                                                '[{invalid_depth}] is invalid.'
                                                .format(max_depth=self.MAX_DEPTH,
                                                        invalid_depth=depth))

            options.update(depth=depth - 1)
            for relation in requested_relationships:
                value = getattr(self, relation)
                new_name = rename.get(relation, relation)
                result[new_name] = None
                if value is not None:
                    if isinstance(value, LIST_TYPES):
                        result[new_name] = []
                        if len(value) > 0:
                            for entity in value:
                                result[new_name].append(entity.to_dict(**options))
                    else:
                        result[new_name] = value.to_dict(**options)

        return result

    def from_dict(self, **kwargs):
        """
        updates the column values of this entity with values in keyword arguments.

        it could fill primary keys, foreign keys, other columns and also
        relationship properties provided in keyword arguments.
        note that relationship values must be entities. this method could
        not convert relationships which are dict, into entities.

        :keyword SECURE_TRUE | SECURE_FALSE exposed_only: specifies that any column which has
                                                          `exposed=False` or its name starts
                                                          with underscore `_`, should not be
                                                          populated from given values. this
                                                          is useful if you want to fill an
                                                          entity with keyword arguments passed
                                                          from client and then doing the
                                                          validation. but do not want to expose
                                                          a security risk. especially in update
                                                          operations. defaults to `SECURE_TRUE`
                                                          if not provided.

        :keyword SECURE_TRUE | SECURE_FALSE ignore_invalid_column: specifies that if a key is
                                                                   not available in entity
                                                                   columns, do not raise an
                                                                   error. defaults to
                                                                   `SECURE_TRUE` if not provided.

        :keyword SECURE_TRUE | SECURE_FALSE ignore_pk: specifies that any primary key column
                                                       should not be populated with given
                                                       values. this is useful if you want to
                                                       fill an entity with keyword arguments
                                                       passed from client and then doing the
                                                       validation. but do not want to let user
                                                       set primary keys and exposes a security
                                                       risk. especially in update operations.
                                                       defaults to `SECURE_TRUE` if not provided.

        :keyword SECURE_TRUE | SECURE_FALSE ignore_fk: specifies that any foreign key column
                                                       should not be populated with given
                                                       values. this is useful if you want
                                                       to fill an entity with keyword arguments
                                                       passed from client and then doing the
                                                       validation. but do not want to let user
                                                       set foreign keys and exposes a security
                                                       risk. especially in update operations.
                                                       defaults to `SECURE_FALSE` if not provided.

        :keyword SECURE_TRUE | SECURE_FALSE ignore_relationships: specifies that any relationship
                                                                  property should not be populated
                                                                  with given values. defaults to
                                                                  `SECURE_TRUE` if not provided.

        :keyword SECURE_TRUE | SECURE_FALSE populate_all: specifies that all available values
                                                          must be populated from provided keyword
                                                          arguments. if set to `SECURE_TRUE`, all
                                                          other parameters will be bypassed.
                                                          this is for convenience of usage.
                                                          defaults to `SECURE_FALSE` if not
                                                          provided.

        :raises ColumnNotExistedError: column not existed error.
        """

        ignore_invalid = kwargs.pop('ignore_invalid_column', SECURE_TRUE)
        populate_all = kwargs.pop('populate_all', SECURE_FALSE)
        if populate_all is SECURE_TRUE:
            exposed_only = SECURE_FALSE
            ignore_pk = SECURE_FALSE
            ignore_fk = SECURE_FALSE
            ignore_relationships = SECURE_FALSE
        else:
            exposed_only = kwargs.pop('exposed_only', SECURE_TRUE)
            ignore_pk = kwargs.pop('ignore_pk', SECURE_TRUE)
            ignore_fk = kwargs.pop('ignore_fk', SECURE_FALSE)
            ignore_relationships = kwargs.pop('ignore_relationships', SECURE_TRUE)

        accessible_columns = self.exposed_columns
        if exposed_only is SECURE_FALSE:
            accessible_columns = accessible_columns + self.not_exposed_columns

        accessible_pk = ()
        if ignore_pk is SECURE_FALSE:
            if exposed_only is SECURE_FALSE:
                accessible_pk = self.primary_key_columns
            else:
                accessible_pk = self.exposed_primary_key_columns

        accessible_fk = ()
        if ignore_fk is not SECURE_TRUE:
            if exposed_only is SECURE_FALSE:
                accessible_fk = self.foreign_key_columns
            else:
                accessible_fk = self.exposed_foreign_key_columns

        accessible_relationships = ()
        if ignore_relationships is SECURE_FALSE:
            if exposed_only is SECURE_FALSE:
                accessible_relationships = self.relationships
            else:
                accessible_relationships = self.exposed_relationships

        all_accessible_columns = accessible_pk + accessible_fk + \
            accessible_columns + accessible_relationships

        provided_columns = set(kwargs.keys())
        result_columns = set(all_accessible_columns).intersection(provided_columns)
        if ignore_invalid is SECURE_FALSE:
            not_existed = provided_columns.difference(result_columns)
            if len(not_existed) > 0:
                raise ColumnNotExistedError('Provided columns or relationship properties '
                                            '{columns} are not available in entity [{entity}].'
                                            .format(entity=self,
                                                    columns=list(not_existed)))

        for column in result_columns:
            setattr(self, column, kwargs.get(column))

    def _extract_conditions(self, **options):
        """
        extracts all conditions available in given options.

        it extracts columns, rename and exclude values.

        :keyword dict[str, list[str]] | list[str] columns: column names to be included in result.
                                                           it could be a list of column names.
                                                           for example:
                                                           `columns=['id', 'name', 'age']`
                                                           but if you want to include
                                                           relationships, then columns for each
                                                           entity must be provided in a key for
                                                           that entity class name.
                                                           for example if there is `CarEntity` and
                                                           `PersonEntity`, it should be like this:
                                                           `columns=dict(CarEntity=
                                                                         ['id', 'name'],
                                                                         PersonEntity=
                                                                         ['id', 'age'])`
                                                           if provided column names are not
                                                           available in result, an error will
                                                           be raised.

        :note columns: dict[str entity_class_name, list[str column_name]] | list[str column_name]

        :keyword dict[str, dict[str, str]] | dict[str, str] rename: column names that must be
                                                                    renamed in the result.
                                                                    it could be a dict with keys
                                                                    as original column names and
                                                                    values as new column names
                                                                    that should be exposed instead
                                                                    of original column names.
                                                                    for example:
                                                                    `rename=dict(age='new_age',
                                                                                 name='new_name')`
                                                                    but if you want to include
                                                                    relationships, then you must
                                                                    provide a dict containing
                                                                    entity class name as key and
                                                                    for value, another dict
                                                                    containing original column
                                                                    names as keys, and column
                                                                    names that must be exposed
                                                                    instead of original names,
                                                                    as values. for example
                                                                    if there is `CarEntity` and
                                                                    `PersonEntity`, it should be
                                                                    like this:
                                                                    `rename=
                                                                    dict(CarEntity=
                                                                         dict(name='new_name'),
                                                                         PersonEntity=
                                                                         dict(age='new_age')`
                                                                    then, the value of `name`
                                                                    column in result will be
                                                                    returned as `new_name` column.
                                                                    and also value of `age` column
                                                                    in result will be returned as
                                                                    'new_age' column. if provided
                                                                    rename columns are not
                                                                    available in result, they
                                                                    will be ignored.

        :note rename: dict[str entity_class_name, dict[str original_column, str new_column]] |
                      dict[str original_column, str new_column]

        :keyword dict[str, list[str]] | list[str] exclude: column names to be excluded from
                                                           result. it could be a list of column
                                                           names. for example:
                                                           `exclude=['id', 'name', 'age']`
                                                           but if you want to include
                                                           relationships, then columns for each
                                                           entity must be provided in a key for
                                                           that entity class name.
                                                           for example if there is `CarEntity`
                                                           and `PersonEntity`, it should be
                                                           like this:
                                                           `exclude=dict(CarEntity=
                                                                         ['id', 'name'],
                                                                         PersonEntity=
                                                                         ['id', 'age'])`
                                                            if provided excluded columns are not
                                                            available in result, they will be
                                                            ignored.

        :note exclude: dict[str entity_class_name, list[str column_name]] | list[str column_name]

        :returns: tuple[set[str column_name],
                        dict[str original_column, str new_column],
                        set[str excluded_column]]

        :rtype: tuple[set[str], dict[str, str], set[str]]
        """

        columns = options.get('columns', None)
        rename = options.get('rename', None)
        exclude = options.get('exclude', None)

        if isinstance(columns, dict):
            columns = columns.get(self.get_class_name(), None)

        if isinstance(rename, dict) and len(rename) > 0 and \
                isinstance(list(rename.values())[0], dict):

            rename = rename.get(self.get_class_name(), None)

        if isinstance(exclude, dict):
            exclude = exclude.get(self.get_class_name(), None)

        if columns is None:
            columns = []

        if rename is None:
            rename = {}

        if exclude is None:
            exclude = []

        columns = set(columns)
        exclude = set(exclude)
        return columns.difference(exclude), rename, exclude


class MagicMethodMixin(CoreObject):
    """
    magic method mixin class.

    this class adds different magic method implementations to its subclasses.
    """

    def __eq__(self, other):
        """
        gets the equality comparison result.

        first, it compares primary keys if they have value in both entities
        and both entities have a common root parent.
        otherwise it compares them using python default memory location comparison.

        :param CoreEntity other: other entity to compare for equality.

        :rtype: bool
        """

        if isinstance(other, self.root_base_class):
            if self._is_primary_key_comparable(self.primary_key()) is True:
                return self.primary_key() == other.primary_key()
            else:
                return self is other

        return False

    def __ne__(self, other):
        """
        gets the not equality comparison result.

        :param CoreEntity other: other entity to compare for not equality.

        :rtype: bool
        """

        return not self == other

    def __hash__(self):
        """
        gets the hash of current entity.

        if the entity has valid primary key values, it will be considered
        in hash generation. otherwise it falls back to general hash generation
        based on python defaults.

        :rtype: int
        """

        if self._is_primary_key_comparable(self.primary_key()) is True:
            return hash('{root_base}.{pk}'.format(root_base=self.root_base_class,
                                                  pk=self.primary_key()))

        return super().__hash__()

    def __repr__(self):
        """
        gets the string representation of current entity.

        :rtype: str
        """

        return '{module}.{name} [{pk}]'.format(module=self.__module__,
                                               name=self.get_name(),
                                               pk=self.primary_key())

    def _set_root_base_class(self, root_base_class):
        """
        sets root base class of this entity.

        root base class is the class which is direct subclass
        of declarative base class (which by default is CoreEntity)
        in inheritance hierarchy.

        for example if you use pyrin's default CoreEntity as your base model:
        {CoreEntity -> BaseEntity, A -> CoreEntity, B -> A, C -> B}
        then, root base class of A, B and C is A.

        if you implement a new base class named MyNewDeclarativeBase as base model:
        {MyNewDeclarativeBase -> BaseEntity, A -> MyNewDeclarativeBase, B -> A, C -> B}
        then, root base class of A, B and C is A.

        the inheritance rule also supports multi-branch hierarchy. for example:
        {CoreEntity -> BaseEntity, A -> CoreEntity, B -> A, C -> A}
        then, root base class of A, B and C is A.

        :param type root_base_class: root base class type.
        """

        setattr(root_base_class, '_root_base_class', root_base_class)

    def _get_root_base_class(self):
        """
        gets root base class of this entity and caches it.

        returns None if it's not set.

        root base class is the class which is direct subclass
        of declarative base class (which by default is CoreEntity)
        in inheritance hierarchy.

        for example if you use pyrin's default CoreEntity as your base model:
        {CoreEntity -> BaseEntity, A -> CoreEntity, B -> A, C -> B}
        then, root base class of A, B and C is A.

        if you implement a new base class named MyNewDeclarativeBase as base model:
        {MyNewDeclarativeBase -> BaseEntity, A -> MyNewDeclarativeBase, B -> A, C -> B}
        then, root base class of A, B and C is A.

        the inheritance rule also supports multi-branch hierarchy. for example:
        {CoreEntity -> BaseEntity, A -> CoreEntity, B -> A, C -> A}
        then, root base class of A, B and C is A.

        :rtype: type
        """

        return getattr(self, '_root_base_class', None)

    @property
    def root_base_class(self):
        """
        gets root base class of this entity.

        root base class will be calculated once and cached.

        :rtype: type
        """

        base = self._get_root_base_class()
        if base is None:
            bases = inspect.getmro(type(self))
            root_base_entity_index = bases.index(self.declarative_base_class) - 1
            base = bases[root_base_entity_index]
            self._set_root_base_class(base)

        return base

    @property
    def declarative_base_class(self):
        """
        gets declarative base class of application.

        :rtype: type
        """

        base = self._get_declarative_base_class()
        if base is None:
            bases = inspect.getmro(type(self))
            base_entity_index = bases.index(self._base_entity_class)
            potential_declarative_bases = bases[0:base_entity_index]
            base = self._extract_declarative_base(potential_declarative_bases)
            self._set_declarative_base_class(base)

        return base

    def _extract_declarative_base(self, types):
        """
        extracts the first declarative base found from given types.

        returns None if not found.

        :param tuple[type] types: class types to extract declarative base from them.

        :rtype: type
        """

        for item in types:
            try:
                sqla_inspect(item)
            except NoInspectionAvailable:
                return item

        return None

    def _set_declarative_base_class(self, declarative_base_class):
        """
        sets declarative base class of application.

        the value will be set and shared for all entities because there
        should be only one declarative base class.

        :param type declarative_base_class: a class type of application declarative base class.
                                            by default, it would be `CoreEntity` class.
        """

        self._validate_declarative_base_class(declarative_base_class)
        MagicMethodMixin._declarative_base_class = declarative_base_class

    def _get_declarative_base_class(self):
        """
        gets declarative base class of application.

        returns None if it's not set.

        :rtype: type
        """

        return getattr(MagicMethodMixin, '_declarative_base_class', None)

    @property
    @abstractmethod
    def _base_entity_class(self):
        """
        gets base entity class of application.

        this method must be overridden in `BaseEntity` class.
        it should return type of `BaseEntity` class itself.
        this method is required to overcome circular dependency problem as mixin
        module could not import `BaseEntity` because `BaseEntity` itself references
        to mixin module. and also we could not inject `BaseEntity` dependency through
        `__init__()` method of `MagicMethodMixin` class, because sqlalchemy does not
        call `__init__()` method of entities for populating database results, so
        `__init__()` call is not guaranteed and will only take place on user code.
        so we have to define this method to get `BaseEntity` type here.
        and this is more beautiful then importing `BaseEntity` inside a method
        of `MagicMethodMixin` class.

        :raises CoreNotImplementedError: core not implemented error.

        :rtype: type
        """

        raise CoreNotImplementedError()

    def _validate_declarative_base_class(self, declarative_base_class):
        """
        validates the given declarative base class.

        :param type declarative_base_class: a class type of application declarative base class.
                                            by default, it would be `CoreEntity` class.

        :raises InvalidDeclarativeBaseTypeError: invalid declarative base type error.
        """

        if declarative_base_class is None or not inspect.isclass(declarative_base_class):
            raise InvalidDeclarativeBaseTypeError('Input parameter [{declarative}] '
                                                  'is not a class.'
                                                  .format(declarative=declarative_base_class))

        if not issubclass(declarative_base_class, self._base_entity_class):
            raise InvalidDeclarativeBaseTypeError('Input parameter [{declarative}] '
                                                  'in not a subclass of [{base}].'
                                                  .format(declarative=declarative_base_class,
                                                          base=self._base_entity_class))

        if declarative_base_class is not model_services.get_declarative_base():
            print_warning('You have implemented a new declarative base type [{new}] '
                          'in your application. to make everything works as expected '
                          'you must override "pyrin.database.model.ModelManager.'
                          'get_declarative_base()" method in your application inside '
                          '"database.model" package. for more information on how to do '
                          'that or how to ignore it, see the documentation of specified '
                          'method.'.format(new=declarative_base_class))


class QueryMixin(CoreObject):
    """
    query mixin class.

    this class adds query method to its subclasses.
    the query method will always use the correct session
    based on request context availability.
    """

    @classmethod
    def query(cls, *entities, **options):
        """
        gets the query object to perform queries on it.

        it always uses the correct session based on request context availability.

        :param BaseEntity entities: entities or columns to use them in query.
                                    if not provided, it uses all columns of this entity.

        :keyword type | tuple[type] scope: class type of the entities that this
                                           query instance will work on. if the
                                           query is working on multiple entities,
                                           this value must be a tuple of all class
                                           types of that entities.

                                           for example: if you set
                                           `entities=SomeEntity.id, AnotherEntity.name`
                                           you should leave `scope=None` to skip validation
                                           or you could set
                                           `scope=(SomeEntity, AnotherEntity)`
                                           this way validation succeeds, but if
                                           you set `scope=SomeEntity`
                                           then the query will not be executed
                                           and an error will be raised.

        :raises ColumnsOutOfScopeError: columns out of scope error.

        :rtype: CoreQuery
        """

        store = get_current_store()
        used_entities = entities
        if entities is None or len(entities) <= 0:
            used_entities = (cls,)

        return store.query(*used_entities, **options)


class CRUDMixin(CoreObject):
    """
    crud mixin class.

    this class adds CRUD functionalities to is subclasses.
    it includes save, update and delete.
    it uses the correct session based on request context availability.
    """

    def save(self):
        """
        saves the current entity.
        """

        store = get_current_store()
        store.add(self)
        return self

    def update(self, **kwargs):
        """
        updates the column values of this entity with values in keyword arguments.

        then persists changes into database.
        it could fill primary keys, foreign keys, other columns and also
        relationship properties provided in keyword arguments.
        note that relationship values must be entities. this method could
        not convert relationships which are dict, into entities.

        :keyword SECURE_TRUE | SECURE_FALSE exposed_only: specifies that any column which has
                                                          `exposed=False` or its name starts
                                                          with underscore `_`, should not be
                                                          populated from given values. this
                                                          is useful if you want to fill an
                                                          entity with keyword arguments passed
                                                          from client and then doing the
                                                          validation. but do not want to expose
                                                          a security risk. especially in update
                                                          operations. defaults to `SECURE_TRUE`
                                                          if not provided.

        :keyword SECURE_TRUE | SECURE_FALSE ignore_invalid_column: specifies that if a key is
                                                                   not available in entity
                                                                   columns, do not raise an
                                                                   error. defaults to
                                                                   `SECURE_TRUE` if not provided.

        :keyword SECURE_TRUE | SECURE_FALSE ignore_pk: specifies that any primary key column
                                                       should not be populated with given
                                                       values. this is useful if you want to
                                                       fill an entity with keyword arguments
                                                       passed from client and then doing the
                                                       validation. but do not want to let user
                                                       set primary keys and exposes a security
                                                       risk. especially in update operations.
                                                       defaults to `SECURE_TRUE` if not provided.

        :keyword SECURE_TRUE | SECURE_FALSE ignore_fk: specifies that any foreign key column
                                                       should not be populated with given
                                                       values. this is useful if you want
                                                       to fill an entity with keyword arguments
                                                       passed from client and then doing the
                                                       validation. but do not want to let user
                                                       set foreign keys and exposes a security
                                                       risk. especially in update operations.
                                                       defaults to `SECURE_FALSE` if not provided.

        :keyword SECURE_TRUE | SECURE_FALSE ignore_relationships: specifies that any relationship
                                                                  property should not be populated
                                                                  with given values. defaults to
                                                                  `SECURE_TRUE` if not provided.

        :keyword SECURE_TRUE | SECURE_FALSE populate_all: specifies that all available values
                                                          must be populated from provided keyword
                                                          arguments. if set to `SECURE_TRUE`, all
                                                          other parameters will be bypassed.
                                                          this is for convenience of usage.
                                                          defaults to `SECURE_FALSE` if not
                                                          provided.

        :raises ColumnNotExistedError: column not existed error.
        """

        self.from_dict(**kwargs)
        return self.save()

    def delete(self):
        """
        deletes the current entity.
        """

        store = get_current_store()
        store.delete(self)


class MetadataMixin(CoreObject):
    """
    metadata mixin class.

    this class provides a simple and extensible api for declarative models configuration.
    """

    # table name
    _table = None

    # table args
    _schema = None
    _extend_existing = None

    # mapper args
    _polymorphic_on = None
    _polymorphic_identity = None
    _concrete = None

    @declared_attr
    def __tablename__(cls):
        """
        gets the table name of current entity type.

        it returns the value of `_table` class attribute of entity.

        :rtype: str
        """

        return cls._table

    @declared_attr
    @local_cached(container=MetadataCache)
    def __table_args__(cls):
        """
        gets the table args of current entity type.

        it returns a dict or tuple of all configured table args.

        for example: {'schema': 'database_name.schema_name',
                      'extend_existing': True}

        :rtype: dict | tuple
        """

        table_args = dict()
        if cls._schema is not None:
            table_args.update(schema=cls._schema)

        if cls._extend_existing is not None:
            table_args.update(extend_existing=cls._extend_existing)

        extra_args = cls._customize_table_args(table_args)
        if extra_args is None:
            return table_args

        extra_args = misc_utils.make_iterable(extra_args, tuple)
        if len(extra_args) <= 0:
            return table_args

        return extra_args + (table_args,)

    @declared_attr
    @local_cached(container=MetadataCache)
    def __mapper_args__(cls):
        """
        gets the mapper args of current entity type.

        :rtype: dict
        """

        mapper_args = dict()
        if cls._polymorphic_on is not None:
            mapper_args.update(polymorphic_on=cls._polymorphic_on)

        if cls._polymorphic_identity is not None:
            mapper_args.update(polymorphic_identity=cls._polymorphic_identity)

        if cls._concrete is not None:
            mapper_args.update(concrete=cls._concrete)

        cls._customize_mapper_args(mapper_args)
        return mapper_args

    @classmethod
    def _customize_table_args(cls, table_args):
        """
        customizes different table args for current entity type.

        this method is intended to be overridden by subclasses to customize
        table args per entity type if the required customization needs extra work.
        it must modify input dict values in-place if required.
        if other table args must be added (ex. UniqueConstraint or CheckConstraint ...)
        it must return those as a tuple. it could also return a single object as
        extra table arg (ex. a single UniqueConstraint).
        if no changes are required this method must return None.

        :param dict table_args: a dict containing different table args.
                                any changes to this dict must be done in-place.

        :rtype: tuple | object
        """

        return None

    @classmethod
    def _customize_mapper_args(cls, mapper_args):
        """
        customizes different mapper args for current entity type.

        this method is intended to be overridden by subclasses to customize
        mapper args per entity type if the required customization needs extra work.
        it must modify values of input dict in-place if required.

        :param dict mapper_args: a dict containing different mapper args.
        """
        pass

    @classmethod
    def table_name(cls):
        """
        gets the table name that this entity represents in database.

        :rtype: str
        """

        return cls._table

    @classmethod
    def table_schema(cls):
        """
        gets the table schema that this entity represents in database.

        it might be `None` if schema has not been set for this entity.

        :rtype: str
        """

        return cls._schema

    @classmethod
    def table_fullname(cls):
        """
        gets the table fullname that this entity represents in database.

        fullname is `schema.table_name` if schema is available, otherwise it
        defaults to `table_name`.

        :rtype: str
        """

        schema = cls.table_schema()
        name = cls.table_name()

        if schema is not None:
            return '{schema}.{name}'.format(schema=schema, name=name)
        else:
            return name
