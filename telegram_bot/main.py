import os
import json
import threading
import time


import telegram
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
)
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,

)


import states
import buttons_inline
from modules import rss
from log import get_logger

logger = get_logger("tg_bot")


class Bot:
    def __init__(self):
        logger.info("Main bot init")
        self.is_debug = os.environ.get("IS_DEBUG")
        logger.info("Debug: " + str(self.is_debug))
        server_url = os.getenv("SERVER_URL")
        ssl_key = os.getenv("TELEGRAM_SSL_KEY")
        ssl_cert = os.getenv("TELEGRAM_SSL_CERT")
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.__bot = telegram.Bot(token=token)
        self.__updater = Updater(token=token)
        self.__dispatcher = self.__updater.dispatcher
        self.__dispatcher.add_handler(CommandHandler("start", self.__start_command))
        self.__dispatcher.add_handler(MessageHandler(Filters.text, self.__messages_handler))
        self.__dispatcher.add_handler(CallbackQueryHandler(self.__buttons_handler))
        self.__languages = self.__load_languages()
        self.__admins = os.getenv("TELEGRAM_ADMINS").split(",")
        self.__users_states = {}
        self.__users_module_states = {}
        self.users_data = {}

        if server_url and ssl_key and ssl_cert:
            self.__updater.start_webhook(
                listen="0.0.0.0",
                port=8443,
                url_path=token,
                key=ssl_key,
                cert=ssl_cert,
                webhook_url="https://" + server_url + ":8443/" + token,
            )
            logger.info("Bot running in production state.")
        else:
            self.__updater.start_polling(bootstrap_retries=10)
            logger.info("Bot running in debug state.")

    def __start_command(self, bot, update) -> bool:
        logger.info("start: " + str(update.effective_user.id))
        self.set_state(update.effective_user.id, states.START)
        button_list = [[
            InlineKeyboardButton("Add feed", callback_data=str(buttons_inline.RSS_ADD)),
            InlineKeyboardButton("List of feeds", callback_data=str(buttons_inline.RSS_LIST)),
        ]]
        reply_markup = InlineKeyboardMarkup(button_list)

        self.send_msg(
            tid=update.effective_user.id,
            text=self.trans(update.effective_user.language_code, "msg_welcome"),
            reply_markup=reply_markup,
        )

    def __is_admin(self, update) -> bool:
        if str(update.effective_user.id) in self.__admins:
            return True
        else:
            return False

    def __admin_messages_handler(self, bot, update) -> bool:
        """
        Handle messages from bot admin users
        return True if hit in any case, False if not hit
        """

    def __messages_handler(self, bot, update) -> bool:
        """
        Handle messages from users
        """
        state = self.get_state(update.effective_user.id)

        # Admin messages handle
        if self.__is_admin(update):
            if state:
                # check admin states
                pass
            elif update.message is not None:
                # check admin messages
                pass

        # User messages handle
        if state:
            # check states
            if state == states.WAIT_RSS:
                return self.send_msg(
                    tid=update.effective_user.id,
                    text=rss.add_feed(update.message.text, update.effective_user.id)
                )
                self.set_state(update.effective_user.id, states.START)
        elif update.message is not None:
            # check messages
            pass

    def __buttons_handler(self, bot, update) -> bool:
        """
        Handle inline callback buttons
        """
        callback_splitted = update.callback_query.data.split("_")
        callback_code = int(callback_splitted[0])
        if len(callback_splitted) > 1:
            # callback_data = callback_splitted[1]
            pass

        # Admin buttons handle
        if self.__is_admin(update):
            pass

        # User buttons handle
        if callback_code == buttons_inline.RSS_ADD:
            self.set_state(update.effective_user.id, states.WAIT_RSS)
            return self.send_msg(
                tid=update.effective_user.id,
                text=rss.prompt_feed()
            )

        elif callback_code == buttons_inline.RSS_LIST:
            return self.send_msg(
                tid=update.effective_user.id,
                text=rss.get_feeds(update.effective_user.id)
            )

    def get_state(self, tid):
        return self.__users_states.get(tid, states.START)

    def set_state(self, tid, state):
        self.__users_states[tid] = state

    def __load_languages(self):
        with open("languages.json") as f:
            data = json.load(f)
            return data

    def trans(self, lang, key):
        try:
            return self.__languages[lang][key]
        except Exception:
            return self.__languages["en"][key]

    def send_msg(self, tid, text, reply_markup=None, parse_mode=telegram.ParseMode.HTML):
        res = self.__bot.send_message(
            chat_id=tid,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        return res


def send_unreader_posts(bot):
    while True:
        logger.info("send_unreader_posts")
        rss.refresh_all()
        for unreaded_post in rss.get_unreaders_posts():
            bot.send_msg(unreaded_post['tid'], unreaded_post['post'])
        time.sleep(1)


if __name__ == "__main__":
    bot = Bot()
    #distribution_thread = threading.Thread(send_unreader_posts, bot)
    #distribution_thread.start()
    send_unreader_posts(bot)
