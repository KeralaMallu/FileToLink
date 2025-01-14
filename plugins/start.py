import random
import humanize
from Script import script
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from info import AUTH_CHANNEL, LOG_CHANNEL, START_IMAGE_URL, URL, SHORTLINK
from urllib.parse import quote_plus
from TechVJ.util.file_properties import get_name, get_hash, get_media_file_size
from TechVJ.util.human_readable import humanbytes
from database.users_chats_db import db
from utils import temp, get_shortlink

async def is_subscribed(bot, user_id, channels):
    btn = []
    for channel_id in channels:
        try:
            chat = await bot.get_chat(channel_id)
            invite_link = chat.invite_link or await bot.export_chat_invite_link(channel_id)
            await bot.get_chat_member(channel_id, user_id)
        except UserNotParticipant:
            btn.append([InlineKeyboardButton(f"Join {chat.title}", url=invite_link)])
        except Exception as e:
            print(f"Error with channel {channel_id}: {e}")
    return btn

@Client.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_id = message.from_user.id

    # Force subscription logic
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
            photo=START_IMAGE_URL,  # Use image URL defined in your config
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

@Client.on_message(filters.private & (filters.document | filters.video))
async def stream_start(client, message):
    file = getattr(message, message.media.value)
    filename = file.file_name
    filesize = humanize.naturalsize(file.file_size) 
    fileid = file.file_id
    user_id = message.from_user.id
    username = message.from_user.mention 

    log_msg = await client.send_cached_media(
        chat_id=LOG_CHANNEL,
        file_id=fileid,
    )
    file_name_quoted = quote_plus(get_name(log_msg))
    if not SHORTLINK:
        stream = f"{URL}watch/{log_msg.id}/{file_name_quoted}?hash={get_hash(log_msg)}"
        download = f"{URL}{log_msg.id}/{file_name_quoted}?hash={get_hash(log_msg)}"
    else:
        stream = await get_shortlink(f"{URL}watch/{log_msg.id}/{file_name_quoted}?hash={get_hash(log_msg)}")
        download = await get_shortlink(f"{URL}{log_msg.id}/{file_name_quoted}?hash={get_hash(log_msg)}")
        
    msg_text = f"""
<i><u>Your Link is Ready!</u></i>\n
<b>📂 File Name:</b> <i>{get_name(log_msg)}</i>\n
<b>📦 File Size:</b> <i>{humanbytes(get_media_file_size(message))}</i>\n
<b>📥 Download:</b> <i>{download}</i>\n
<b>🖥 Watch Online:</b> <i>{stream}</i>\n
<b>⚠️ Note:</b> Links won't expire until I delete them.
"""

    await message.reply_text(
        text=msg_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Stream 🖥", url=stream), InlineKeyboardButton("Download 📥", url=download)]
        ]),
        parse_mode=enums.ParseMode.HTML,
        disable_web_page_preview=True
        )
