import os
import time
import threading
from typing import List, Dict

from aiogram import Bot, Dispatcher, executor, types

from modules import rss
from log import get_logger

logger = get_logger("bot")

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
dp = Dispatcher(bot)


def main_menu() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup([[
        types.KeyboardButton("/add"),
        types.KeyboardButton("/list"),
    ]])


def feeds_menu(feeds: List[Dict]) -> types.InlineKeyboardMarkup:
    logger.info("feeds_menu")
    
# Message handlers
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("start", reply_markup=main_menu())


@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    await message.reply("help")


@dp.message_handler(commands=['add'])
async def send_add_prompt(message: types.Message):
    await message.reply(rss.prompt_feed())


@dp.message_handler(commands=['list'])
async def send_list_of_feeds(message: types.Message):
    inline_keyboard = types.InlineKeyboardMarkup(row_width=1)
    for feed in rss.get_feeds(message.from_user.id):
        logger.info("feeds_menu " + feed['title'])
        inline_keyboard.add(types.InlineKeyboardButton(feed['title'], callback_data="feed_" + str(feed["_id"])))
    await message.reply("Feeds: ", reply_markup=inline_keyboard)

# Keyboards process
@dp.callback_query_handler(lambda c: "feed_" in c.data)
async def process_feed_button(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id, "Posts:")
    for post in rss.get_unreaded_posts(callback_query.data[5:]):
        logger.info(post['title'])
        await bot.send_message(
            callback_query.from_user.id,
            post['link'] + "\n" + post['title'] + "\n" + post["d_summ"],
        )


regexp_url = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
@dp.message_handler(regexp=regexp_url)
async def take_link(message: types.Message):
    if rss.add_feed(message.text, message.from_user.id):
        await message.reply("RSS saved.")
    else:
        await message.reply("Wrong or duplicate RSS link.")


def refreshing():
    while True:
        rss.refresh_all_feeds()
        time.sleep(60)


if __name__ == '__main__':
    rss_refresh_thread = threading.Thread(target=refreshing)
    rss_refresh_thread.start()
    executor.start_polling(dp, skip_updates=True)
