# -*- coding: utf-8 -*-
import functools
import re
import httplib as http

import pymongo
from modularodm.query import QueryBase
from modularodm.exceptions import ValidationValueError, NoResultsFound, MultipleResultsFound

from rest_framework.exceptions import NotFound
from framework.exceptions import HTTPError

# MongoDB forbids field names that begin with "$" or contain ".". These
# utilities map to and from Mongo field names.

mongo_map = {
    '.': '__!dot!__',
    '$': '__!dollar!__',
}


def to_mongo(item):
    for key, value in mongo_map.items():
        item = item.replace(key, value)
    return item


def to_mongo_key(item):
    return to_mongo(item).strip().lower()


def from_mongo(item):
    for key, value in mongo_map.items():
        item = item.replace(value, key)
    return item


sanitize_pattern = re.compile(r'<\/?[^>]+>')
def sanitized(value):
    if value != sanitize_pattern.sub('', value):
        raise ValidationValueError('Unsanitary string')


def unique_on(*groups):
    """Decorator for subclasses of `StoredObject`. Add a unique index on each
    group of keys provided.

    :param *groups: List of lists of keys to be indexed
    """
    def wrapper(cls):
        cls.__indices__ = getattr(cls, '__indices__', [])
        cls.__indices__.extend([
            {
                'key_or_list': [
                    (key, pymongo.ASCENDING)
                    for key in group
                ],
                'unique': True,
            }
            for group in groups
        ])
        return cls
    return wrapper


def get_or_http_error(Model, pk_or_query, display_name=None):
    """Load an instance of Model by primary key or modularodm.Q query. Raise an appropriate
    HTTPError if no record is found or if the query fails to find a unique record

    :param type Model: StoredObject subclass to query
    :param pk_or_query:
    :type pk_or_query: either
      - a <basestring> representation of the record's primary key, e.g. 'abcdef'
      - a <QueryBase> subclass query to uniquely select a record, e.g.
        Q('title', 'eq', 'Entitled') & Q('version', 'eq', 1)
    :param basestring display_name:
    :return: Model instance
    """
    display_name = display_name or ''

    if isinstance(pk_or_query, QueryBase):
        try:
            instance = Model.find_one(pk_or_query)
        # TODO: shouldn't use rest-framework exceptions.  Why is HTTPError not working here?
        except NoResultsFound:
            raise HTTPError(http.NOT_FOUND, data=dict(
                message_long="No {name} record matching that query could be found".format(name=display_name)
            ))
        except MultipleResultsFound:
            raise HTTPError(http.BAD_REQUEST, data=dict(
                message_long="The query must match exactly one {name} record".format(name=display_name)
            ))
        return instance
    else:
        instance = Model.load(pk_or_query)
        if not instance:
            raise HTTPError(http.NOT_FOUND, data=dict(
                message_long="No {name} record with that primary key could be found".format(name=display_name)
            ))
        if getattr(instance, 'is_deleted', False):
            raise HTTPError(http.GONE, data=dict(
                message_long="This {name} record has been deleted".format(name=display_name)
            ))
        else:
            return instance

def autoload(Model, extract_key, inject_key, func):
    """Decorator to autoload a StoredObject instance by primary key and inject into kwargs. Raises
    an appropriate HTTPError (see #get_or_http_error)

    :param type Model: StoredObject subclass to query
    :param basetring extract_key: kwargs key to extract Model instance's primary key
    :param basestring inject_key: kwargs key to inject loaded Model instance into kwargs

    Example usage: ::
      def get_node(node_id):
          node = Node.load(node_id)
          ...

      becomes

      @autoload(Node, 'node_id', 'node')
      def get_node(node):
          ...

    Alternatively:
      import functools
      autoload_node = functools.partial(autoload, Node, 'node_id', 'node')

      @autoload_node
      def get_node(node):
          ...
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        primary_key = kwargs.get(extract_key)
        instance = get_or_http_error(Model, primary_key)

        kwargs[inject_key] = instance
        return func(*args, **kwargs)
    return wrapper
