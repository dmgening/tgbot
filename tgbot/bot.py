# /usr/bin/env python3
# coding: utf8

import logging

from telegram.bot import Bot
from telegram.ext import (messagequeue, Updater, Filters, ConversationHandler,
                          CommandHandler, CallbackQueryHandler, MessageHandler)

from .handlers import (start_handler, fallback_handler, fallback_callback_handler,
                       get_first_number, get_second_number, send_governer,
                       GET_FIRST_NUMBER, GET_SECOND_NUMBER, SEND_GOVERNER)

# Enable logging
logger = logging.getLogger(__name__)


class TGBot(Bot):
    def __init__(self, *args, redis=None, msg_queue=None, **kwargs):
        super(TGBot, self).__init__(*args, **kwargs)
        self._redis_client = redis
        self._message_queue = msg_queue

    @property
    def redis(self):
        return self._redis_client

    def __del__(self):
        try:
            self._message_queue.stop()
        except:
            pass
        super(GovernorBot, self).__del__()


def main_loop(token, redis):
    """ * Initialize bot with tg access token.
        * Connect message handlers
        * Run main loop
    """
    logger.info('Creating Telegram bot')
    import ipdb; ipdb.set_trace()

    msg_queue = messagequeue.MessageQueue()
    updater = Updater(bot=TGBot(token, redis=redis, msg_queue=msg_queue))


    logger.debug('Attaching conversation handler')
    updater.dispatcher.add_handler(ConversationHandler(
        entry_points=[CommandHandler('start', start_handler)],
        fallbacks=[CallbackQueryHandler(fallback_callback_handler),
                   MessageHandler(Filters.all, fallback_handler)],
        states={
            GET_FIRST_NUMBER: [CallbackQueryHandler(get_first_number)],
            GET_SECOND_NUMBER: [CallbackQueryHandler(get_second_number)],
            SEND_GOVERNER: [CallbackQueryHandler(send_governer)],
        }
    ))

    logger.debug('Attaching managment handlers')

    logger.info('Telegram bot started')
    updater.start_polling()
    updater.idle()
