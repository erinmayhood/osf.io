# -*- coding: utf-8 -*-

import re
import httplib as http

import pymongo
from modularodm.query import QueryBase
from modularodm.exceptions import ValidationValueError, NoResultsFound

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


def get_or_http_error(Model, pk_or_query):

    name = str(Model)

    if isinstance(pk_or_query, QueryBase):
        try:
            instance = Model.find_one(pk_or_query)
        # TODO: shouldn't use rest-framework exceptions.  Why is HTTPError not working here?
        except NoResultsFound:
            # raise HTTPError(http.NOT_FOUND, data=dict(
            #     message_long="No {} resource matching that query could be found".format(name)
            # ))
            raise NotFound("No resource matching that query could be found.")
        return instance
    else:
        instance = Model.load(pk_or_query)
        if not instance:
            raise HTTPError(http.NOT_FOUND, data=dict(
                message_long="No {name} resource with that primary key could be found".format(name=name)
            ))
        if getattr(instance, 'is_deleted', False):
            raise HTTPError(http.GONE, data=dict(
                message_long="This {name} resource has been deleted".format(name=name)
            ))
        else:
            return instance
