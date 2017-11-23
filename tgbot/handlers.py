#!/usr/bin/env python

from time import time
from datetime import timedelta

import logging
import json
from random import randint

from .helpers import (_send_replies_batch, _send_yes_only_keyboard,
                      _update_callback_message, _send_numbers_keyboard)

#
# States & const
#
WELCOME, PAGE_CHOISE, LINE_CHOISE, SEND_BOOK_QUOTE = range(4)
SECONDS_IN_DAY = timedelta(days=1).total_seconds()

#
# Small helpers
#

def _validate_int(value, min_val, max_val):
    try:
        value = int(value)
    except:
        return False
    if value > 2000 or value < 0:
        return False
    return True


#
# Handlers
#

def start_handler(bot, update):
    reply = ("Бомборобот — усовершенствованная модель гадателя на книгах.\n"
             "Благодаря сложным внутренним алгоритмам, блокчейн-магии и "
             "рандомному бигдатору, Бомборобот не реагирует на погоду, "
             "магнитные бури, ретроградный меркурий и методику Илоны "
             "Давыдовой. \nВерсия 2.0 содержит более мощный заряд на долгое"
             " хранение овощей и встроенный антихайп.")
    _send_yes_only_keyboard(update.message, reply, 'ВСЕ ЯСНО',
                            parse_mode='markdown')
    return WELCOME


def welcome_handler(bot, update, user_data):
    if hasattr(update, 'callback_query'):
        message = update.callback_query.message
        _update_callback_message(message, bot, "")
    else:
        message = update.message

    user_data["attempts"] = [
        attempt_time for attempt_time in user_data.get('attempts', [])
        if time() - SECONDS_IN_DAY < attempt_time
    ]

    if len(user_data["attempts"]) > 4:
        message_text = "Кажется, на сегодня магия закончилась. Приходите завтра"
        _send_yes_only_keyboard(message, message_text, "А теперь можно?")
        return WELCOME

    message_text = ("Бомборобот гадает по неопределенному множеству книг.\n"
                    "Выберите страницу:")
    _send_replies_batch(message, [message_text, ])
    return PAGE_CHOISE


def page_choise_invalid(bot, update):
    message_text = "Выбери номер страницы от 1 до 2000"
    _send_replies_batch(update.message, [message_text, ])
    return PAGE_CHOISE


def page_choise(bot, update):
    if not _validate_int(update.message.text, 0, 2000):
        return page_choise_invalid(bot, update)

    message_text = "А теперь выбирайте строку:"
    _send_replies_batch(update.message, [message_text, ])
    return LINE_CHOISE


def line_choise_invalid(bot, update):
    message_text = "Выбери строчку от 1 до 200"
    _send_replies_batch(update.message, [message_text, ])
    return LINE_CHOISE


def line_choise(bot, update, user_data):
    if not _validate_int(update.message.text, 0, 200):
        return line_choise_invalid(bot, update)

    try:
        max_id = bot.redis.hlen('sheet') - 1
        row = json.loads(bot.redis.hget('sheet', randint(0, max_id)))
        quote, meta, link = row[:3]

        message_text = f"{quote}\n**{meta}**\n{link}"

        if len(row) > 3:
            message_text += f"\n\nПромокод: {row[3]}"

        button_text = "Вау! А еще можешь?"
        _send_yes_only_keyboard(update.message, message_text, button_text,
                                parse_mode='markdown')

        if "attempts" not in user_data:
            user_data["attempts"] = []
        user_data["attempts"].append(time())

    except:
        error_text = 'Упс! Что-то пошло не так. Давай попробуем с начала.'
        _send_yes_only_keyboard(update.message, error_text, 'Давай')
    return WELCOME


def fallback_handler(bot, update, user_data):
    if hasattr(update, 'callback_query'):
        message = update.callback_query.message
    else:
        message = message
    error_text = 'Упс! Что-то пошло не так. Давай попробуем с начала.'
    _send_replies_batch(message, (error_text, ))
    return welcome_handler(bot, update, user_data)


def error_handler(bot, update, error):
    """ Log Errors caused by Updates.
    """
    logging.exception('Update "%s" caused error "%s"',
                      update, error)


# def preroll_handler(bot, update):
#     """ Step one: Ask user nicely to begin
#     """
#     message = update.callback_query.message
#     _update_callback_message(message, bot, "")
#     _send_yes_only_keyboard(message, 'Готов выбрать губернатора?', 'Да!')
#     return GET_FIRST_NUMBER


