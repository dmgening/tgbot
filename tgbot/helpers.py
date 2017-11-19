#!/usr/bin/env python
import logging
import json
from random import shuffle, randint
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

NUMBERS_IN_KEYBOARD = 9
NUMBERS_IN_ROW = 3


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
