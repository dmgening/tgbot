# /usr/bin/env python3
# coding: utf8

import logging

from telegram.bot import Bot
from telegram.ext import (messagequeue, Updater, Filters, ConversationHandler,
                          CommandHandler, CallbackQueryHandler, MessageHandler,
                          RegexHandler)

from .handlers import (start_handler, welcome_handler, WELCOME,
                       page_choise, page_choise_invalid, PAGE_CHOISE,
                       line_choise, line_choise_invalid, LINE_CHOISE,
                       send_book_quote, SEND_BOOK_QUOTE,
                       error_handler, fallback_handler)


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

    # def __del__(self):
    #     try:
    #         self._message_queue.stop()
    #     except:
    #         pass
    #     super(TGBot, self).__del__()


def main_loop(token, redis):
    """ * Initialize bot with tg access token.
        * Connect message handlers
        * Run main loop
    """
    logger.info('Creating Telegram bot')

    msg_queue = messagequeue.MessageQueue()
    updater = Updater(bot=TGBot(token, redis=redis, msg_queue=msg_queue))

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_handler),
                      MessageHandler(Filters.all, fallback_handler),
                      CallbackQueryHandler(fallback_handler)],
        states={
            WELCOME: [CallbackQueryHandler(welcome_handler)],
            PAGE_CHOISE: [RegexHandler('^\d{1,4}$', page_choise),
                          MessageHandler(Filters.text, page_choise_invalid)],
            LINE_CHOISE: [RegexHandler('^\d{1,3}$', line_choise),
                          MessageHandler(Filters.text, page_choise_invalid)],
        },
        fallbacks=[CallbackQueryHandler(fallback_handler),
                   MessageHandler(Filters.text, fallback_handler),
                   CommandHandler('start', start_handler)],
        per_chat=False, per_user=True
    )

    logger.debug('Attaching handlers')
    updater.dispatcher.add_handler(conversation_handler)
    updater.dispatcher.add_error_handler(error_handler)

    logger.debug('Attaching managment handlers')

    logger.info('Telegram bot started')
    updater.start_polling()
    updater.idle()
