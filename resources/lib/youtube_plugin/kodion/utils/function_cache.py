# -*- coding: utf-8 -*-
"""

    Copyright (C) 2014-2016 bromix (plugin.video.youtubemusic)
    Copyright (C) 2016-2019 plugin.video.youtubemusic

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only for more information.
"""

from functools import partial
import hashlib

from .storage import Storage


class FunctionCache(Storage):
    ONE_MINUTE = 60
    ONE_HOUR = 60 * ONE_MINUTE
    ONE_DAY = 24 * ONE_HOUR
    ONE_WEEK = 7 * ONE_DAY
    ONE_MONTH = 4 * ONE_WEEK

    def __init__(self, filename, max_file_size_mb=5):
        max_file_size_kb = max_file_size_mb * 1024
        Storage.__init__(self, filename, max_file_size_kb=max_file_size_kb)

        self._enabled = True

    def clear(self):
        self._clear()

    def enabled(self):
        """
        Enables the caching
        :return:
        """
        self._enabled = True

    def disable(self):
        """
        Disable caching e.g. for tests
        :return:
        """
        self._enabled = False

    @staticmethod
    def _create_id_from_func(partial_func):
        """
        Creats an id from the given function
        :param partial_func:
        :return: id for the given function
        """
        m = hashlib.md5()
        m.update(partial_func.func.__module__.encode('utf-8'))
        m.update(partial_func.func.__name__.encode('utf-8'))
        m.update(str(partial_func.args).encode('utf-8'))
        m.update(str(partial_func.keywords).encode('utf-8'))
        return m.hexdigest()

    def _get_cached_data(self, partial_func):
        cache_id = self._create_id_from_func(partial_func)
        return self._get(cache_id), cache_id

    def get_cached_only(self, func, *args, **keywords):
        partial_func = partial(func, *args, **keywords)

        # if caching is disabled call the function
        if not self._enabled:
            return partial_func()

        # only return before cached data
        data, cache_id = self._get_cached_data(partial_func)
        if data is not None:
            return data[0]

        return None

    def get(self, seconds, func, *args, **keywords):
        """
        Returns the cached data of the given function.
        :param partial_func: function to cache
        :param seconds: time to live in seconds
        :param return_cached_only: return only cached data and don't call the function
        :return:
        """

        partial_func = partial(func, *args, **keywords)

        # if caching is disabled call the function
        if not self._enabled:
            return partial_func()

        cached_data = None
        cached_time = None
        data, cache_id = self._get_cached_data(partial_func)
        if data is not None:
            cached_data = data[0]
            cached_time = data[1]

        diff_seconds = 0

        if cached_time is not None:
            # this is so stupid, but we have the function 'total_seconds' only starting with python 2.7
            diff_seconds = self.get_seconds_diff(cached_time)

        if cached_data is None or diff_seconds > seconds:
            cached_data = partial_func()
            self._set(cache_id, cached_data)

        return cached_data

    def _optimize_item_count(self):
        # override method from resources/lib/youtube_plugin/kodion/utils/storage.py
        # for function cache do not optimize by item count, using database size.
        pass
