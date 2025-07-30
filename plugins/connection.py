from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.connections_mdb import add_connection, all_connections, if_active, delete_connection
from info import ADMINS
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


@Client.on_message((filters.private | filters.group) & filters.command('connect'))
async def add_connection_handler(client, message):
    user = message.from_user
    if not user:
        return await message.reply("Anonymous admin detected.\nUse /connect <group_id> in PM.", quote=True)

    user_id = user.id
    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        # PM: user must send group ID
        try:
            _, group_id = message.text.strip().split(" ", 1)
            group_id = int(group_id)
        except ValueError:
            return await message.reply_text(
                "<b>⚠️ Invalid format!</b>\n\n"
                "Usage: <code>/connect group_id</code>\n\n"
                "🔍 Add this bot to your group and use /id to get the group ID.",
                quote=True
            )
    else:
        # In group/supergroup
        group_id = message.chat.id

    try:
        # Check if user is admin in the group
        member = await client.get_chat_member(group_id, user_id)
        if member.status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER] and user_id not in ADMINS:
            return await message.reply("You must be an admin in the group to use this command.", quote=True)

        # Check if bot is admin
        bot_member = await client.get_chat_member(group_id, "me")
        if bot_member.status != enums.ChatMemberStatus.ADMINISTRATOR:
            return await message.reply("❌ I need to be an admin in the group to connect it.", quote=True)

        chat = await client.get_chat(group_id)
        title = chat.title

        if await add_connection(str(group_id), str(user_id)):
            await message.reply_text(
                f"✅ Connected to **{title}**.\nNow you can manage this group from PM!",
                quote=True,
                parse_mode=enums.ParseMode.MARKDOWN
            )
            if chat_type != enums.ChatType.PRIVATE:
                await client.send_message(
                    user_id,
                    f"🔗 Connected to **{title}**.",
                    parse_mode=enums.ParseMode.MARKDOWN
                )
        else:
            await message.reply_text("⚠️ You're already connected to this group.", quote=True)

    except Exception as e:
        logger.exception(f"Error connecting group {group_id} by user {user_id}: {e}")
        await message.reply("❌ Error: Invalid group ID or I'm not present in the group.", quote=True)


@Client.on_message((filters.private | filters.group) & filters.command('disconnect'))
async def disconnect_handler(client, message):
    user = message.from_user
    if not user:
        return await message.reply("Anonymous admin detected. Use this in a private chat.", quote=True)

    user_id = user.id
    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        return await message.reply("🔌 Use /connections to manage your group connections.", quote=True)

    group_id = message.chat.id

    try:
        member = await client.get_chat_member(group_id, user_id)
        if member.status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER] and str(user_id) not in ADMINS:
            return

        if await delete_connection(str(user_id), str(group_id)):
            await message.reply("✅ Disconnected from this group.", quote=True)
        else:
            await message.reply("⚠️ This group is not connected. Use /connect to link it.", quote=True)
    except Exception as e:
        logger.exception(f"Error disconnecting group {group_id} by user {user_id}: {e}")
        await message.reply("❌ Something went wrong. Try again later.", quote=True)


@Client.on_message(filters.private & filters.command(["connections"]))
async def list_connections(client, message):
    user_id = message.from_user.id
    try:
        group_ids = await all_connections(str(user_id))
        if not group_ids:
            return await message.reply("📭 No active connections. Connect to a group first using /connect.", quote=True)

        buttons = []
        for group_id in group_ids:
            try:
                chat = await client.get_chat(int(group_id))
                title = chat.title
                is_active = await if_active(str(user_id), str(group_id))
                suffix = " - ACTIVE ✅" if is_active else ""
                buttons.append([
                    InlineKeyboardButton(f"{title}{suffix}", callback_data=f"groupcb:{group_id}:{int(is_active)}")
                ])
            except Exception as e:
                logger.warning(f"Failed to fetch group {group_id}: {e}")

        await message.reply(
            "🔗 Your connected group details:\n\n",
            reply_markup=InlineKeyboardMarkup(buttons),
            quote=True
        )
    except Exception as e:
        logger.exception(f"Error listing connections for user {user_id}: {e}")
        await message.reply("❌ Failed to retrieve your connections.", quote=True)
