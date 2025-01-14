import random
from Script import script
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from info import AUTH_CHANNEL, LOG_CHANNEL, START_IMAGE_URL
from database.users_chats_db import db
from utils import temp

async def is_subscribed(bot, user_id, channels):
    btn = []
    for channel_id in channels:
        try:
            chat = await bot.get_chat(channel_id)
            invite_link = chat.invite_link or await bot.export_chat_invite_link(channel_id)
            await bot.get_chat_member(channel_id, user_id)
        except Exception:
            btn.append([InlineKeyboardButton(f"Join {chat.title}", url=invite_link)])
    return btn

@Client.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_id = message.from_user.id

    # Force subscription check
    if AUTH_CHANNEL:
        try:
            subscription_buttons = await is_subscribed(client, user_id, AUTH_CHANNEL)
            if subscription_buttons:
                subscription_buttons.append([InlineKeyboardButton("♻️ Try Again ♻️", url=f"https://t.me/{(await client.get_me()).username}?start=true")])
                await message.reply_text(
                    text=f"👋 Hello {message.from_user.mention},\n\nPlease join the required channel(s) to use this bot. Click 'Try Again' after joining.",
                    reply_markup=InlineKeyboardMarkup(subscription_buttons)
                )
                return
        except Exception as e:
            print(f"Error in subscription check: {e}")

    # Add user to the database if they don't exist
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)
        await client.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(user_id, message.from_user.mention))

    # Send welcome message with image
    try:
        await client.send_photo(
            chat_id=message.chat.id,
            photo=START_IMAGE_URL,
            caption=script.START_TXT.format(message.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Update Channel", url="https://t.me/KeralaCaptain")]]
            ),
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        print(f"Error sending start image: {e}")
        await message.reply_text(
            text=script.START_TXT.format(message.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Update Channel", url="https://t.me/KeralaCaptain")]]
            ),
            parse_mode=enums.ParseMode.HTML
)
