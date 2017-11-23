#!/usr/bin/env python

import json
from random import randint

from .helpers import (_send_replies_batch, _send_yes_only_keyboard,
                      _update_callback_message, _send_numbers_keyboard)

#
# States & const
#
GET_FIRST_NUMBER, GET_SECOND_NUMBER, SEND_GOVERNER, RETRY, COOLDOWN = range(5)


#
# Handlers
#

def start_handler(bot, update):
    """ Initial state for a bot. Greet person, skip preroll handler for firsttimers
    """
    reply = ("Привет! Я прототип бота отдающий случайный ответ из гугл таблиц. \n"
             "Я могу в inline клавиатуры, редактрование сообщений и rich text \n"
             "*Как-то* _вот_ `так`. [Моя БД](https://docs.google.com/spreadsheets/d"
             "/1du6quNJ-_IrHO44b5eAtrdDk1m6ig_Kq4stCWsZ9ric/edit)")
    _send_yes_only_keyboard(update.message, reply, 'Посмотришь как работаю?',
                            parse_mode='markdown')
    return GET_FIRST_NUMBER


def preroll_handler(bot, update):
    """ Step one: Ask user nicely to begin
    """
    message = update.callback_query.message
    _update_callback_message(message, bot, "")
    _send_yes_only_keyboard(message, 'Готов выбрать губернатора?', 'Да!')
    return GET_FIRST_NUMBER


def get_first_number(bot, update):
    """ Step two: Ask for first number
    """
    message = update.callback_query.message
    _update_callback_message(message, bot, f"\n\nПосле выбора мы обновляем сообщение убирая клавиатуру")
    _send_replies_batch(message, ["Тут может оставаться flavor", ])
    _send_numbers_keyboard(message, "Выбирай число!")
    return GET_SECOND_NUMBER


def get_second_number(bot, update):
    """ Step three: Same as two but with flavor!
    """
    message = update.callback_query.message
    callback_data = update.callback_query.data
    _update_callback_message(message, bot, f"\n\nМожно использовать пользовательские данные: {callback_data}")
    _send_numbers_keyboard(message, "Выбирай второе число!")
    return SEND_GOVERNER


def send_governer(bot, update):
    """ Step four: send reply from cached google table, and go to the beginig
    """
    message = update.callback_query.message
    callback_data = update.callback_query.data
    _update_callback_message(message, bot, f"")
    _send_replies_batch(message, ["Или мы можем просто убирать клавиатуру", ])
    try:
        max_id = bot.redis.hlen('sheet') - 1
        row = json.loads(bot.redis.hget('sheet', randint(0, max_id)))
        header = ('Город:', 'Сайт:', 'Губернатор:', 'Промо:')
        reply = '\n'.join(f'{k} {v}' for k, v in zip(header, row))
        _send_yes_only_keyboard(message, reply, 'Еще разок?')
    except:
        fallback_callback_handler(bot, update)
    return GET_FIRST_NUMBER


def fallback_handler(bot, update):
    """ Fallback handler if user trying to do something funny
    """
    replies = ("Мы можем реагировать на действия пользователя вне нашего процесса скидывая его на начало", )
    _send_replies_batch(update.message, replies)
    return start_handler(bot, update)


def fallback_callback_handler(bot, update):
    """ Fallback handler if user trying to do something funny
    """
    reply = "Прости друг, что-то пошло не так. Давай попробуем сначала..."
    _update_callback_message(message, bot, reply)
    return preroll_handler(bot, update)


def error(bot, update, error):
    """ Log Errors caused by Updates.
    """
    logger.exception('Update "%s" caused error "%s"', update, error)

