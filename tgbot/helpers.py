#!/usr/bin/env python
import logging
import json
import hashlib

from datetime import timedelta

from random import shuffle, randint
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .observer import Observer

NUMBERS_IN_KEYBOARD = 9
NUMBERS_IN_ROW = 3
SECONDS_IN_DAY = timedelta(days=1).total_seconds()


class RedisMirroredMapping(object):

    def __init__(self, redis, key_prefix, ttl=SECONDS_IN_DAY,
                 dump=json.dumps, load=json.loads, factory=dict):

        self._redis = redis
        self._key_prefix = key_prefix
        self._ttl = ttl

        self._dump = dump
        self._load = load
        self._factory = factory

    def _format_key(self, key):
        return (f'{self.key_prefix}:'
                '{haslib.md5(self.serializer(key)).hexdigset()}')

    def _create_save_callback(self, key):
        """ Creates callback for observer to save value to redis on changes
        """
        def _callback(observer, instance, value):
            logging.debug(f'Observed change event on {key}')
            self[key] = value

    def __getitem__(self, key):
        try:
            logging.debug(f'Trying to load {key} from redis')
            item = self.load(self.redis.get(self._format_key(key)))
        except:
            logging.debug(f'Falling back to factory for {key}')
            item = self.factory()
        return Observer(item, self._save_callback(key))

    def __setitem__(self, key, value):
        logging.debug(f'Saving {key} to redis')
        self.redis.setex(self._format_key(key), self.dump(value), self.ttl)


#
# Generic helpers
#

class RuntimeConfig(dict):
    """ Simple config store monitoring changes
    """
    def __init__(self, redis, storage_key):
        dict.__init__(self)

        self._redis_client = redis
        self._storage_key = storage_key
        self._dirty = False

        self._logger = logging.getLogger(self.__class__.__name__)

        if self._redis_client.exists(self._storage_key):
            self.load()

    def load(self):
        try:
            serialized_config = self._redis_client.get(self._storage_key)
            self.update(json.loads(serialized_config))
            self._logger.debug('Loaded config from redis')
        except (TypeError, ValueError):
            self._logger.warning('Failed to load config')

    def save(self):
        if self._dirty:
            serialized_config = json.dumps(self)
            self._redis_client.set(self._storage_key, serialized_config)
            self._logger.debug('Saved config to redis')
        else:
            self._logger.debug('Skip saving config to redis')


    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self._dirty = True



#
# Telegram helpers
#

def _send_replies_batch(message, replies, **kwargs):
    """ Batch send replies to user, kwargs will be applied to each
        reply_text function call
    """
    for reply in replies:
        message.reply_text(reply, **kwargs)


def _send_yes_only_keyboard(message, reply, button, **kwargs):
    """ Send simple keyboard with one button
    """
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton(button, callback_data='yep')]],
    )
    _send_replies_batch(message, (reply, ), reply_markup=markup, **kwargs)


def _update_callback_message(message, bot, reply):
    """ Update callback sender message concating reply
        and removing keyboard
    """
    bot.edit_message_text(text=message.text + " " + reply,
                          chat_id=message.chat_id,
                          message_id=message.message_id)


def _send_numbers_keyboard(message, reply, **kwargs):
    """ Create inline keyboard for random number entry
    """
    meaningless = list(range(100))
    shuffle(meaningless)
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton(str(n), callback_data=str(n))
            for n in meaningless[offset:offset+NUMBERS_IN_ROW]]
            for offset in range(0, NUMBERS_IN_KEYBOARD, NUMBERS_IN_ROW)]
    )
    _send_replies_batch(message, (reply, ), reply_markup=markup, **kwargs)
