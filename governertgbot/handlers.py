#!/usr/bin/env python

from .helpers import (_send_replies_batch, _send_yes_only_keyboard,
                      _update_callback_message, _send_numbers_keyboard,
                      _send_governer_reply)

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
    reply = "Привет! Я вводный текст который не написали... \n Давай начнем?"
    _send_yes_only_keyboard(update.message, reply, 'Начнем?')
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
    _update_callback_message(message, bot, "Окей, поехали!")
    _send_replies_batch(message, ["Раз, два...", "Фредди заберёт тебя",])
    _send_numbers_keyboard(message, "Выбирай число!")
    return GET_SECOND_NUMBER


def get_second_number(bot, update):
    """ Step three: Same as two but with flavor!
    """
    message = update.callback_query.message
    callback_data = update.callback_query.data
    _update_callback_message(message, bot, f"На барабане {callback_data}!")
    _send_replies_batch(message, [f"Кстати, отличное число {callback_data}",
                                   "Мое любимое! Продолжаем...",
                                   "Три, четыре", "Запирайте дверь в квартире"])
    _send_numbers_keyboard(message, "Еще одно число...")
    return SEND_GOVERNER


def send_governer(bot, update):
    """ Step four: send reply from cached google table, and go to the beginig
    """
    message = update.callback_query.message
    callback_data = update.callback_query.data
    _update_callback_message(message, bot, f"Я календарь перевернул, а там {callback_data}!")
    _send_replies_batch(message, ["Выбираем направление", "Пативен выехал"])
    _send_governer_reply(message, bot.redis)
    return GET_FIRST_NUMBER


def fallback_handler(bot, update):
    """ Fallback handler if user trying to do something funny
    """
    replies = ("Окей, ты делаешь это неправильно", "На дворе 2к17!",
               "Тебе дали кнопочки, вот и пользуйся ими. Давай с начала...")
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

