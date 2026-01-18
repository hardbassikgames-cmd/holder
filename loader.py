import discord
import asyncio
import json
import os
import logging
import re
import pytz
import dotenv
import random
import platform
import psutil
from discord import app_commands
from mcstatus import JavaServer
from datetime import datetime, timezone
from typing import Optional

# 🟥 - ошибка
# 🟨 - варн\недостаток прав
# 🟩 - все нормис
# 🟦 - системное оповещение
# 🟪 - фатал ошибка


# Добавьте в константы (после иконок):

# ━━━━━━━━[ Управление командами ]━━━━━━━━
CMD_DEFAULT_ENABLED = {
    # Основные команды
    "ping": True,
    "help": True,
    "mcplayers": True,
    "roleinfo": True,
    
    # Информационные
    "serverinfo": True,
    "userinfo": True,
    "botstats": True,
    
    # Minecraft
    "mcquery": True,
    "mcseed": True,
    
    # Развлекательные
    "poll": True,
    "random": True,
    
    # Админские
    "autorole": True,
    "setwelcome": True,
    "setmcstats": True,
    "mcsetip": True,
    "speak": True,
    "fixeveryone": True,
    "reactionrole": True,
    "clean": True,
    "slowmode": True,
}

#                                               ━━━━━━━━[ КОНСТАНТЫ ]━━━━━━━━
#                       ━━━━━━━━[ Иконки ]━━━━━━━━

# OG
CREDITS_EMOJI = "<:_OG_Credits:1459744318804856962>"
AL_LIDA_EMOJI = "<:_OG_Lida:1459744275745996902>"
AL_OWNER_EMOJI = "<:_OG_Owner:1459744119806230629>"
AL_ADMIN_EMOJI = "<:_OG_Admin:1459744075052744714>"
ALORIS_LOGO = "<:_OG_Aloris_S1_V1:1461388104098119854>"

# STAFF_rank
S_Trial = "<:S_Trial:1461406219452547072>"
S_Staff = "<:S_Staff:1461406285961367829>"
S_Admin = "<:S_Admin:1461406330718781440>"
S_Manager = "<:S_Manager:1461405636180050021>"
S_Root = "<:S_Root:1462261164074598502>"

# SERVER_function
SE_Rules = "<:SE_Rules:1461405300677410951>"
SE_Punishment = "<:SE_Punishment:1461405237712654472>"
SE_Logs = "<:SE_Logs:1461408861637574882>"
SE_Warn = "<:SE_Warn:1461409018051301600>"
SE_Web = "<:SE_Web:1461439886321127515>"
SE_Welcome = "<:SE_Welcome:1462257962289598484>"
SE_Home = "<:SE_Home:1462258264761700513>"
SE_Role = "<:SE_Role:1462267942761791549>"
SE_IdkReally = "<:SE_IdkReally:1462269266337206397>"
SE_PingGood = "<:Ping_good:1461450551823696079>"
SE_PingNormal = "<:Ping_normal:1461450547445104807>"
SE_PingBad = "<:Ping_Bad:1461450550255161445>"

# Partners
P_TW = "<:Partner_TW:1461405680949792829>"
P_OTHER = "<:Partner:1461405727506829605>"

# MEMBERS_C
M_1 = "<:M_1:1461446455670608041>"
M_2 = "<:M_2:1461446454135619696>"
M_3 = "<:M_3:1461446451036164213>"
M_ONLINE = "<:M_ONLINE:1462263408576434309>"
M_AFK = "<:M_AFK:1462263407347630080>"
M_DND = "<:M_DND:1462263493905354835>"

# BOT_Utilities
B_Info = "<:B_Info:1461446330470891787>"
B_BotIcon = "<:B_Bot:1461405137359736903>"

R_Booster = "<:R_Booster:1462260261883875378>"
# Colors
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
RESET = "\033[0m"

CONFIG_FILE = 'config.json'
LOG_FILE = 'bot.log'
TOKEN_FILE = 'other/SEA_cfg.env'

# ━━━━━━━━[ сетап логов ]━━━━━━━━ #
def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # цветной вывод в консоль
    class ColorHandler(logging.StreamHandler):
        COLORS = {
            'INFO': GREEN,                                  # 🟩
            'WARNING': YELLOW,                              # 🟨
            'ERROR': RED,                                   # 🟥
            'CRITICAL': RED,                                # 🟪
            'DEBUG': BLUE                                   # 🟦
        }
        
        def emit(self, record):
            try:
                msg = self.format(record)
                color = self.COLORS.get(record.levelname, RESET)
                self.stream.write(f"{color}{msg}{RESET}\n")
                self.flush()
            except Exception:
                self.handleError(record)
    
    console_handler = ColorHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

# ━━━━━━━━[ конфиг ]━━━━━━━━ #
def load_config():
    default_config = {
        "auto_role_id": None,
        "welcome_channel_id": None,
        "mc_stats_channel": None,
        "mc_server_ip": "d2.skynodes.net:25007",
        "allowed_users": [904051099244310578],
        "reaction_roles": {},
        "commands_enabled": {
            "ping": True,
            "help": True,
            "mcplayers": True,
            "roleinfo": True,
            "serverinfo": True,
            "userinfo": True,
            "botstats": True,
            "poll": True,
            "random": True,
            "autorole": True,
            "setwelcome": True,
            "setmcstats": True,
            "mcsetip": True,
            "speak": True,
            "fixeveryone": True,
            "reactionrole": True,
            "clean": True,
            "slowmode": True,
        }
    }
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                default_config.update(loaded)
        except Exception as e:
            logger.error(f"[🟪] config error: {e}")  
    else:
        logger.info(f"[🟦] создан новый конфиг")  
    
    return default_config

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        logger.info(f"[🟩] конфиг сохранён")  
    except Exception as e:
        logger.error(f"[🟪] save error: {e}")  

# ━━━━━━━━[ штукесы ]━━━━━━━━ #
def parse_hex_color(color_str):
    if not color_str:
        return 0xf6d98e
    
    color_str = color_str.strip().lower()
    
    if color_str.startswith('#'):
        color_str = color_str[1:]
    
    presets = {
        'red': 0xff0000, 'green': 0x00ff00, 'blue': 0x0000ff,
        'yellow': 0xffff00, 'purple': 0x800080, 'orange': 0xffa500,
        'pink': 0xff69b4, 'cyan': 0x00ffff
    }
    
    if color_str in presets:
        return presets[color_str]
    
    try:
        if len(color_str) == 3:
            color_str = ''.join(c*2 for c in color_str)
        return int(color_str, 16)
    except:
        logger.warning(f"[🟨] невалидный цвет: {color_str}, использую дефолтный")  
        return 0xf6d98e

def is_allowed_user(user_id):
    config = load_config()
    allowed = config.get("allowed_users", [904051099244310578]) # челы из конфига и я [SEA_owner]
    is_allowed = user_id in allowed
    if not is_allowed:
        logger.warning(f"[🟨] доступ запрещён для user_id: {user_id}")  
    return is_allowed

def ace_check():
    def predicate(interaction: discord.Interaction) -> bool:
        if not is_allowed_user(interaction.user.id):
            logger.warning(f"[🟨] недостаток прав: {interaction.user} → {interaction.command.name}")
            return False
        
        command_name = interaction.command.name
        now = datetime.now().timestamp()
        
        if not hasattr(ace_check, "cooldowns"):
            ace_check.cooldowns = {}
        
        user_id = interaction.user.id
        if user_id not in ace_check.cooldowns:
            ace_check.cooldowns[user_id] = {}
        
        if command_name not in ace_check.cooldowns[user_id]:
            ace_check.cooldowns[user_id][command_name] = now
            return True
        
        last_used = ace_check.cooldowns[user_id][command_name]
        if now - last_used < 3:
            logger.warning(f"[🟨] кулдаун: {interaction.user} → {command_name}")  
            return False
        
        ace_check.cooldowns[user_id][command_name] = now
        logger.info(f"[🟩] команда разрешена: {interaction.user} → {command_name}")  
        return True
    
    return app_commands.check(predicate)

def cmd_check():
    """Умный декоратор для проверки команд"""
    async def predicate(interaction: discord.Interaction) -> bool:
        config = load_config()
        cmd_enabled = config.get("commands_enabled", CMD_DEFAULT_ENABLED)
        command_name = interaction.command.name
        
        # Если команда отключена
        if not cmd_enabled.get(command_name, True):
            logger.warning(f"[🟨] команда отключена: {interaction.user} → {command_name}")
            
            embed = discord.Embed(
                title="🚫 Команда отключена",
                description=(
                    f"Команда `/{command_name}` временно отключена.\n\n"
                    f"*Причина: администратор отключил эту команду.*"
                ),
                color=0xff9900
            )
            
            # Получаем категорию команды
            category = get_command_category(command_name)
            if category:
                embed.add_field(name="Категория", value=category, inline=True)
            
            embed.set_footer(text=f"Используйте /help для списка доступных команд")
            
            # Отправляем сообщение
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
            
            return False
        
        return True
    
    return app_commands.check(predicate)

def get_command_category(cmd_name: str) -> str:

    # Access lvls
    # M - Members
    # S - Staff
    # D - Developers [Managers]

    categories = {
        "ping": "Access: M",
        "help": "Access: M",
        "mcplayers": "Access: M",
        "roleinfo": "Access: M",
        "serverinfo": "Access: M",
        "userinfo": "Access: M",
        "botstats": "Access: M",
        "poll": "Access: M",
        "random": "Access: M",
        "autorole": "Access: D",
        "setwelcome": "Access: D",
        "setmcstats": "Access: D",
        "mcsetip": "Access: D",
        "speak": "Access: D",
        "fixeveryone": "Access: D",
        "reactionrole": "Access: D",
        "clean": "Access: D",
        "slowmode": "Access: D",
    }
    return categories.get(cmd_name, "Другое")

# ━━━━━━━━[ тот самый лайв статус ]━━━━━━━━
class MM:
    def __init__(self, bot):
        self.bot = bot
        self.task = None
        self.status_message_id = None
        self.last_status = None
        self.retry_count = 0
        self.max_retries = 5
        self.is_online = False
        self.last_update = None
        self.start_time = datetime.now(timezone.utc)
        self.total_updates = 0
        self.failed_updates = 0
        self.msk_tz = pytz.timezone('Europe/Moscow')

    async def start(self):
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        self.task = asyncio.create_task(self.update_loop())
        logger.info(f"[🟩] Minecraft монитор запущен")
    
    async def update_loop(self):
        base_delay = 30
        max_delay = 300
        
        while True:
            try:
                success = await self.update_status()
                self.total_updates += 1
                
                if not success:
                    self.failed_updates += 1
                
                await asyncio.sleep(base_delay)
                
            except asyncio.CancelledError:
                logger.info(f"[🟦] Цикл обновления остановлен")
                break
            except Exception as e:
                logger.error(f"[🟥] Ошибка в update_loop: {e}")
                await asyncio.sleep(60)
    
    async def update_status(self) -> bool:
        config = load_config()
        channel_id = config.get("mc_stats_channel")
        
        if not channel_id:
            logger.warning(f"[🟨] mc_stats_channel не установлен")
            return False

        server_ip = config.get("mc_server_ip", "d2.skynodes.net:25007")
        
        channel = None
        for guild in self.bot.guilds:
            channel = guild.get_channel(channel_id)
            if channel:
                break
        
        if not channel:
            logger.warning(f"[🟨] канал {channel_id} не найден")
            return False

        try:
            server = JavaServer.lookup(server_ip)
            timeout = 15
            
            try:
                status = await asyncio.wait_for(server.async_status(), timeout)
                self.is_online = True
                self.retry_count = 0
                self.last_update = datetime.now(timezone.utc)
                
            except asyncio.TimeoutError:
                raise Exception(f"Таймаут подключения ({timeout}сек)")
            
            embed = self.create_online_embed(status, server_ip)
            
            success = await self.update_or_create_message(channel, embed)
            
            if success:
                logger.info(f"[🟦] MC статус обновлён ({status.players.online}/{status.players.max})")
            else:
                logger.warning(f"[🟨] Не удалось обновить сообщение статуса")
            
            return success
            
        except Exception as e:
            logger.warning(f"[🟨] MC сервер недоступен: {e}")
            self.is_online = False
            self.retry_count += 1
            self.last_update = datetime.now(timezone.utc)
            
            embed = self.create_offline_embed(e, server_ip)
            
            await self.update_or_create_message(channel, embed)
            
            return False
    
    def msk_converter(self, utc_dt: datetime) -> datetime:
        return utc_dt.astimezone(self.msk_tz)
        
    def msk_current_str(self, utc_dt: datetime) -> str:
        if not utc_dt:
            return "никогда"
        
        try:
            msk_time = self.msk_converter(utc_dt)
            return msk_time.strftime("%H:%M:%S")
            
        except Exception as e:
            logger.warning(f"[🟨] Ошибка конвертации времени: {e}")
            return utc_dt.strftime("%H:%M:%S")
            
    def create_online_embed(self, status, server_ip) -> discord.Embed:
        if status.latency < 80:
            color = 0xf6d98e
            ping_emoji = f"{SE_PingGood}"
            ping_status = "Шикарный пинг"
        elif status.latency < 150:
            color = 0xf6d98e
            ping_emoji = f"{SE_Web}"
            ping_status = "Хороший пинг"
        elif status.latency < 300:
            color = 0xf6d98e
            ping_emoji = f"{SE_PingNormal}"
            ping_status = "Такой себе пинг"
        else:
            color = 0xf6d98e
            ping_emoji = f"{SE_PingBad}"
            ping_status = "ну... это жестть"
        
        player_percentage = (status.players.online / status.players.max * 100) if status.players.max > 0 else 0
        
        if player_percentage >= 6:
            server_status = "Много [>= 6]"
            status_emoji = f"{M_3}"
        elif player_percentage >= 3:
            server_status = "Нормально [>= 3]"
            status_emoji = f"{M_3}"
        elif player_percentage >= 2:
            server_status = "Мало"
            status_emoji = f"{M_2} [>= 2]"
        else:
            server_status = "Пусто [== 0]"
            status_emoji = f"{M_1}"
        
        embed = discord.Embed(
            title=f"{SE_Logs} ALORIS LIVE STATS",
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.description = f"*{server_ip}*"
        
        embed.add_field(
            name=f"{status_emoji} Количество игроков",
            value=f"*{status.players.online}/{status.players.max} • {server_status}*",
            inline=True
        )
        
        embed.add_field(
            name=f"{SE_Web} Пинг",
            value=f"*{ping_emoji} {status.latency:.0f}ms\n{ping_status}*",
            inline=True
        )
        
        if status.version:
            embed.add_field(
                name=f"{SE_Logs} Версия",
                value=f"*{status.version.name}*",
                inline=True
            )
        
        if hasattr(status, 'favicon') and status.favicon:
            embed.set_thumbnail(url=f"attachment://server_icon.png")
        
        if status.description:
            motd = str(status.description).strip()
            if motd and motd != "null":
                clean_motd = re.sub(r'§[0-9a-fk-or]', '', motd)
                embed.add_field(
                    name="Описание",
                    value=f"*{clean_motd[:200]}*",
                    inline=False
                )
        
        if status.players.sample:
            players = [p.name for p in status.players.sample]
            max_players_show = 12
            if len(players) <= max_players_show:
                player_list = " • ".join(players)
            else:
                player_list = " • ".join(players[:max_players_show]) + f" *и ещё {len(players) - max_players_show}*"
            
            embed.add_field(
                name=f"{status_emoji} Online ({len(players)})",
                value=f"*{player_list[:900]}*",
                inline=False
            )
        
        uptime = datetime.now(timezone.utc) - self.start_time
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60
        
        success_rate = ((self.total_updates - self.failed_updates) / self.total_updates * 100) if self.total_updates > 0 else 100
        
        embed.add_field(
            name=f"{B_BotIcon} Инфа Бота",
            value=f"*Циклов обновлений: {self.total_updates}\nРаботает: {hours}ч {minutes}м*",
            inline=True
        )
        
        if self.last_update:
            time_msk_str = self.msk_current_str(self.last_update)
            time_since_update = datetime.now(timezone.utc) - self.last_update
            seconds_ago = int(time_since_update.total_seconds())
            
            if seconds_ago < 60:
                time_ago = "только что"
            elif seconds_ago < 3600:
                minutes_ago = seconds_ago // 60
                if minutes_ago == 1:
                    time_ago = "1 минуту назад"
                elif minutes_ago < 5:
                    time_ago = f"{minutes_ago} минуты назад"
                else:
                    time_ago = f"{minutes_ago} минут назад"
            else:
                hours_ago = seconds_ago // 3600
                if hours_ago == 1:
                    time_ago = "1 час назад"
                elif hours_ago < 24:
                    time_ago = f"{hours_ago} часа назад"
                else:
                    days_ago = hours_ago // 24
                    time_ago = f"{days_ago} дней назад"
            
            embed.add_field(
                name=f"{B_Info} Последнее обновление",
                value=f"*{time_msk_str}\n({time_ago})*",
                inline=True
            )
        
        embed.set_footer(
            text=f"LIVE Status • S.IP: {server_ip}",
            icon_url="https://cdn.discordapp.com/emojis/1461405137359736903.webp"
        )
        
        return embed
    
    def create_offline_embed(self, error, server_ip) -> discord.Embed:
        
        embed = discord.Embed(
            title=f"{SE_Warn} ALORIS SERVER OFFLINE",  
            color=0xff4444,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.description = f"*{server_ip}* • {SE_Warn} *НЕДОСТУПЕН*"
        
        error_msg = str(error)
        if "timeout" in error_msg.lower():
            error_type = f"{SE_Warn} • Time-Out"
            error_desc = "Сервер не ответил вовремя"
        elif "refused" in error_msg.lower():
            error_type = f"{SE_Warn} • Declined"
            error_desc = "Подключение отклонено"
        elif "resolve" in error_msg.lower():
            error_type = f"{SE_Warn} • Server Error"
            error_desc = "Не удалось найти сервер"
        elif "network" in error_msg.lower():
            error_type = f"{SE_Warn} • NetWork"
            error_desc = "Проблемы с сетью"
        else:
            error_type = f"{SE_Warn} • Unknown"
            error_desc = "Неизвестная ошибка"
        
        embed.add_field(
            name=f"{SE_Web} Сервер",
            value=f"*{server_ip}*",
            inline=True
        )
        
        embed.add_field(
            name="Статус",
            value="*Оффлайн*",
            inline=True
        )
        
        embed.add_field(
            name="Попытка",
            value=f"*{self.retry_count}/{self.max_retries}*",
            inline=True
        )
        
        embed.add_field(
            name=f"{error_type} Ошибка",
            value=f"*{error_desc}*",
            inline=True
        )
        
        if len(error_msg) > 100:
            short_error = error_msg[:97] + "..."
        else:
            short_error = error_msg
        
        embed.add_field(
            name="Детали",
            value=f"*{short_error}*",
            inline=False
        )
        
        if self.last_update:
            time_msk_str = self.msk_current_str(self.last_update)
            
            time_since_update = datetime.now(timezone.utc) - self.last_update
            seconds_ago = int(time_since_update.total_seconds())
            
            if seconds_ago < 60:
                time_ago = "только что"
            elif seconds_ago < 3600:
                minutes_ago = seconds_ago // 60
                if minutes_ago == 1:
                    time_ago = "1 минуту назад"
                elif minutes_ago < 5:
                    time_ago = f"{minutes_ago} минуты назад"
                else:
                    time_ago = f"{minutes_ago} минут назад"
            else:
                hours_ago = seconds_ago // 3600
                if hours_ago == 1:
                    time_ago = "1 час назад"
                elif hours_ago < 24:
                    time_ago = f"{hours_ago} часа назад"
                else:
                    days_ago = hours_ago // 24
                    time_ago = f"{days_ago} дней назад"
            
            embed.add_field(
                name="Последнее обновление",
                value=f"*{time_msk_str}\n({time_ago})*",
                inline=True
            )
        
        uptime = datetime.now(timezone.utc) - self.start_time
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60
        
        embed.add_field(
            name=f"{B_BotIcon} Монитор",
            value=f"*Работает: {hours}ч {minutes}м\nЦиклов обновлений: {self.total_updates}*",
            inline=True
        )
        
        embed.set_footer(
            text=f"{SE_PingBad} • Перепроверка через 30 секунд.",
            icon_url="https://cdn.discordapp.com/emojis/1461405137359736903.webp"
        )
        
        return embed
    
    async def update_or_create_message(self, channel, embed) -> bool:
        try:
            if self.status_message_id:
                try:
                    message = await channel.fetch_message(self.status_message_id)
                    await message.edit(embed=embed)
                    return True
                except discord.NotFound:
                    self.status_message_id = None
                except discord.Forbidden:
                    return False
            
            async for msg in channel.history(limit=15):
                if msg.author == self.bot.user:
                    try:
                        await msg.edit(embed=embed)
                        self.status_message_id = msg.id
                        return True
                    except:
                        continue
            
            message = await channel.send(embed=embed)
            self.status_message_id = message.id
            return True
            
        except Exception as e:
            logger.error(f"[🟥] Ошибка обновления: {e}")
            return False
    
    async def stop(self):
        if self.task:
            self.task.cancel()
            self.task = None
            logger.info(f"[🟦] MC монитор остановлен")
    
    async def force_update(self):
        if self.task:
            await self.update_status()
            return True
        return False
    
    async def get_stats(self):
        uptime = datetime.now(timezone.utc) - self.start_time
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60
        
        success_rate = ((self.total_updates - self.failed_updates) / self.total_updates * 100) if self.total_updates > 0 else 0
        
        return {
            "is_running": self.task is not None,
            "is_online": self.is_online,
            "retry_count": self.retry_count,
            "total_updates": self.total_updates,
            "failed_updates": self.failed_updates,
            "success_rate": success_rate,
            "uptime": f"{hours}ч {minutes}м",
            "message_id": self.status_message_id,
            "last_update": self.last_update.strftime("%H:%M:%S") if self.last_update else "Никогда"
        }

# ━━━━━━━━[ мейн код ]━━━━━━━━
class SEA_main(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.guild_reactions = True
        
        super().__init__(intents=intents)
        
        self.tree = app_commands.CommandTree(self)
        self.minecraft = MM(self)
        self.start_time = datetime.now(timezone.utc)
        self.command_usage = {}
    
    async def setup_hook(self):
        try:
            await self.tree.sync()
            logger.info(f"[🟩] команды синхронизированы")  
        except Exception as e:
            logger.error(f"[🟥] команды не синхронизированы: {e}")  
    
    async def on_ready(self):
        print(f"{YELLOW}{'━'*62}{RESET}")
        print(f"{YELLOW} ███{RESET}{YELLOW}      SEA_bot v5.3 {GREEN}{self.user}{RESET}{YELLOW} • Готов к работе{RESET}     {YELLOW}███{RESET}")
        print(f"{YELLOW}{'                    ━━━━━━━━━━━━━━━━━━━━'}{RESET}")
        print(f"{YELLOW} ███{RESET}{YELLOW}           Серверов: • {GREEN}{len(self.guilds)}{RESET}{YELLOW} Команды: {GREEN}загружены{RESET}          {YELLOW}███{RESET}")
        print(f"{YELLOW}{'━'*62}{RESET}")
        
        await self.minecraft.start()
        
        await self.change_presence(
            activity=discord.Game(name="SEA_bot • /help"),
            status=discord.Status.online
        )
        
        logger.info(f"[🟩] бот запущен как {self.user}")  
    
    async def on_member_join(self, member):
        if member.bot:
            logger.info(f"[🟦] бот присоединился: {member}")  
            return
        
        config = load_config()
        role_id = config.get("auto_role_id")
        
        if not role_id or len(member.roles) > 1:
            logger.info(f"[🟦] авто-роль не применена для {member}")  
            return
        
        role = discord.utils.get(member.guild.roles, id=role_id)
        if role:
            try:
                await member.add_roles(role, reason="Авто-роль")
                logger.info(f"[🟩] ROLE → {role.name} → {member}")  
                
                channel_id = config.get("welcome_channel_id")
                if channel_id:
                    channel = member.guild.get_channel(channel_id)
                    if channel:
                        embed = discord.Embed(
                            title=f"Добро пожаловать, {member.name}!",
                            description=f"Рады видеть тебя на **{member.guild.name}**!",
                            color=0xf6d98e,
                            timestamp=datetime.now(timezone.utc)
                        )
                        if member.avatar:
                            embed.set_thumbnail(url=member.avatar.url)
                        await channel.send(embed=embed)
                        logger.info(f"[🟦] приветствие отправлено для {member}")  
                        
            except Exception as e:
                logger.error(f"[🟥] role error: {e}")  
        else:
            logger.warning(f"[🟨] роль {role_id} не найдена для {member}")  

# ━━━━━━━━[ делаем вызов покороче ]━━━━━━━━
bot = SEA_main()

# ==============================================
# ОСНОВНЫЕ КОМАНДЫ
# ==============================================

@bot.tree.command(name="ping", description="проверка бота")
@cmd_check() # чек включен ли он или нет
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    uptime = datetime.now(timezone.utc) - bot.start_time
    days = uptime.days
    hours = uptime.seconds // 3600
    minutes = (uptime.seconds % 3600) // 60
    seconds = uptime.seconds % 60
    
    if latency < 100:
        color = 0xf6d98e
        status = "Отлично"
        emoji = "🟢"
    elif latency < 300:
        color = 0xf6d98e
        status = "Нормально"
        emoji = "🟡"
    else:
        color = 0xf6d98e
        status = "Медленно"
        emoji = "🔴"
    
    embed = discord.Embed(
        title=f"{emoji} Понг!",
        color=color,
        timestamp=datetime.now(timezone.utc)
    )
    
    embed.add_field(name="Задержка", value=f"{latency}ms ({status})", inline=True)
    
    if days > 0:
        uptime_str = f"{days}д {hours}ч {minutes}м"
    else:
        uptime_str = f"{hours}ч {minutes}м {seconds}с"
    
    embed.add_field(name="Время работы", value=uptime_str, inline=True)
    embed.add_field(name="Серверов", value=str(len(bot.guilds)), inline=True)
    
    # Добавляем статистику использования команд
    total_commands = sum(bot.command_usage.values()) if bot.command_usage else 0
    if total_commands > 0:
        most_used = max(bot.command_usage, key=bot.command_usage.get) if bot.command_usage else "нет"
        embed.add_field(
            name="Статистика команд",
            value=f"Всего: {total_commands}\nЧаще всего: `/{most_used}`",
            inline=False
        )
    
    embed.set_footer(text=f"Запросил: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
    
    await interaction.response.send_message(embed=embed)
    
    # Логируем использование
    bot.command_usage["ping"] = bot.command_usage.get("ping", 0) + 1
    logger.info(f"[🟩] ping от {interaction.user}")  

@bot.tree.command(name="help", description="все команды")
@cmd_check() # чек включен ли он или нет
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title=f"{B_BotIcon} Все Команды SEA_bot",
        description="*Доступные команды для использования*",
        color=0xf6d98e
    )
    
    # Основные команды
    embed.add_field(
        name="🎮 Основные",
        value=(
            "• `/ping` - Проверить статус бота\n"
            "• `/help` - Эта справка\n"
            "• `/mcplayers` - Кто онлайн на сервере\n"
            "• `/roleinfo` - Инфо об авто-роли\n"
            "• `/serverinfo` - Инфо о сервере Discord\n"
            "• `/userinfo` - Инфо о пользователе\n"
            "• `/botstats` - Статистика бота"
        ),
        inline=False
    )
    
    # Админские команды
    if is_allowed_user(interaction.user.id):
        embed.add_field(
            name="⚙️ Админские",
            value=(
                "• `/autorole` - Настроить авто-роль\n"
                "• `/setwelcome` - Канал для приветствий\n"
                "• `/setmcstats` - Канал для статистики\n"
                "• `/mcsetip` - Изменить IP сервера\n"
                "• `/speak` - Отправить сообщение\n"
                "• `/fixeveryone` - Выдать роль всем\n"
                "• `/reactionrole` - Создать реакцию-роль\n"
                "• `/clean` - Очистить сообщения\n"
                "• `/slowmode` - Установить медленный режим"
            ),
            inline=False
        )
    
    # Развлекательные
    embed.add_field(
        name="🎲 Развлекательные",
        value=(
            "• `/poll` - Создать опрос\n"
            "• `/random` - Случайный выбор"
        ),
        inline=False
    )
    
    embed.set_footer(text=f"Всего команд: {len(bot.tree.get_commands())} | Используй /help")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Логируем использование
    bot.command_usage["help"] = bot.command_usage.get("help", 0) + 1
    logger.info(f"[🟩] help от {interaction.user}")  

@bot.tree.command(name="mcplayers", description="игроки онлайн")
async def mc_players(interaction: discord.Interaction):
    config = load_config()
    server_ip = config.get("mc_server_ip", "d2.skynodes.net:25007")

    await interaction.response.defer()

    try:
        server = JavaServer.lookup(server_ip)
        status = server.status()

        def format_ping_bar(ping_ms):
            if ping_ms < 100:
                quality = "Хорошо"
                bar = "█ █ █"
                embed_color = 0xf6d98e
            elif ping_ms < 300:
                quality = "Нормально"
                bar = "░ ░ ░"
                embed_color = 0xf6d98e
            else:
                quality = "Медленно"
                bar = "▒ ▒ ▒"
                embed_color = 0xf6d98e

            return f"**{ping_ms:.0f}ms**\n`{bar}` [{quality}]", embed_color

        ping_str, embed_color = format_ping_bar(status.latency)

        embed = discord.Embed(
            title=f"{B_Info} MC STATUS",
            color=embed_color,
            timestamp=datetime.now(timezone.utc)
        )

        embed.add_field(name=f"{M_3} Игроки", value=f"{status.players.online}/{status.players.max}", inline=True)
        embed.add_field(name="Пинг", value=ping_str, inline=True)
        
        # Версия сервера
        if status.version:
            embed.add_field(name="Версия", value=status.version.name, inline=True)

        if status.players.sample:
            players = [p.name for p in status.players.sample]
            player_list = "\n".join([f"• {player}" for player in players[:15]])
            if len(players) > 15:
                player_list += f"\n*... и ещё {len(players) - 15}*"
            embed.add_field(name="🎮 Онлайн игроки", value=player_list, inline=False)
        else:
            embed.add_field(name="🎮 Онлайн", value="Никого нет 😢", inline=False)
            
        # MOTD
        if status.description:
            motd = str(status.description).strip()
            if motd and motd != "null":
                clean_motd = re.sub(r'§[0-9a-fk-or]', '', motd)
                if len(clean_motd) > 0:
                    embed.add_field(name="📝 Описание", value=f"*{clean_motd[:150]}*", inline=False)

        embed.set_footer(text=f"{status.version.name} | {server_ip} | /mcplayers")
        await interaction.followup.send(embed=embed)
        
        # Логируем использование
        bot.command_usage["mcplayers"] = bot.command_usage.get("mcplayers", 0) + 1
        logger.info(f"[🟩] mcplayers от {interaction.user}")

    except Exception as e:
        error_msg = str(e)[:100]
        embed = discord.Embed(
            title="❌ Ошибка подключения",
            description=f"Не удалось подключиться к серверу `{server_ip}`",
            color=0xff4444
        )
        embed.add_field(name="Ошибка", value=f"```{error_msg}```", inline=False)
        embed.set_footer(text="Проверьте правильность IP-адреса")
        await interaction.followup.send(embed=embed)
        logger.error(f"[🟥] mcplayers error: {e}")

@bot.tree.command(name="roleinfo", description="статус авторолки")
@cmd_check() # чек включен ли он или нет
async def role_info(interaction: discord.Interaction):
    config = load_config()
    role_id = config.get("auto_role_id")
    
    if role_id:
        role = discord.utils.get(interaction.guild.roles, id=role_id)
        if role:
            # Создаем красивый embed
            embed = discord.Embed(
                title="⚙️ Информация об авто-роли",
                color=role.color if role.color.value != 0 else 0xf6d98e,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Основная информация
            embed.add_field(name="Роль", value=role.mention, inline=True)
            embed.add_field(name="ID", value=f"`{role.id}`", inline=True)
            embed.add_field(name="Цвет", value=f"`{str(role.color)}`", inline=True)
            
            # Детали
            embed.add_field(name="Участников", value=str(len(role.members)), inline=True)
            embed.add_field(name="Позиция", value=str(role.position), inline=True)
            embed.add_field(name="Отдельно показывать", value="✅" if role.hoist else "❌", inline=True)
            
            # Разрешения
            perms = []
            if role.permissions.administrator:
                perms.append("Администратор")
            if role.permissions.manage_messages:
                perms.append("Управление сообщениями")
            if role.permissions.manage_roles:
                perms.append("Управление ролями")
            
            if perms:
                embed.add_field(name="Ключевые разрешения", value=", ".join(perms[:3]), inline=False)
            
            # Дата создания
            embed.add_field(
                name="Создана", 
                value=role.created_at.strftime("%d.%m.%Y %H:%M"),
                inline=True
            )
            
            embed.set_footer(text=f"Запросил: {interaction.user.name}")
            await interaction.response.send_message(embed=embed)
            
            # Логируем использование
            bot.command_usage["roleinfo"] = bot.command_usage.get("roleinfo", 0) + 1
            logger.info(f"[🟩] roleinfo от {interaction.user}")  
        else:
            await interaction.response.send_message(
                f"**⚠️ Роль не найдена**\nID в конфиге: `{role_id}`\nВозможно роль была удалена.",
                ephemeral=True
            )
            logger.warning(f"[🟨] roleinfo роль не найдена: {role_id}")  
    else:
        embed = discord.Embed(
            title="⚙️ Авто-роль",
            description="**Авто-роль не настроена**\n\nИспользуйте `/autorole` для настройки.",
            color=0xf6d98e
        )
        await interaction.response.send_message(embed=embed)
        logger.info(f"[🟦] roleinfo от {interaction.user}: авторолка выключена")

# ==============================================
# НОВЫЕ КОМАНДЫ: СЕРВЕР ИНФО, ЮЗЕР ИНФО, СТАТУС БОТА
# ==============================================

@bot.tree.command(name="serverinfo", description="информация о сервере Discord")
@cmd_check() # чек включен ли он или нет
async def server_info(interaction: discord.Interaction):
    
    guild = interaction.guild
    
    online = len([m for m in guild.members if m.status == discord.Status.online])
    idle = len([m for m in guild.members if m.status == discord.Status.idle])
    dnd = len([m for m in guild.members if m.status == discord.Status.dnd])
    offline = len([m for m in guild.members if m.status == discord.Status.offline])
    
    text_channels = len(guild.text_channels)
    voice_channels = len(guild.voice_channels)
    categories = len(guild.categories)
    
    verification_levels = {
        discord.VerificationLevel.none: "Нет",
        discord.VerificationLevel.low: "Низкий",
        discord.VerificationLevel.medium: "Средний",
        discord.VerificationLevel.high: "Высокий",
        discord.VerificationLevel.highest: "Самый высокий"
    }
    
    embed = discord.Embed(
        title=f"{B_Info} {guild.name}",
        color=0xf6d98e,
        timestamp=datetime.now(timezone.utc)
    )
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    embed.add_field(name=f"{S_Root} Владелец", value=guild.owner.mention, inline=True)
    embed.add_field(name=f"{B_Info} ID сервера", value=f"`{guild.id}`", inline=True)
    embed.add_field(name=f"{SE_Home} Создан", value=guild.created_at.strftime("%d.%m.%Y"), inline=True)
    
    embed.add_field(
        name=f"> {B_Info} Members",
        value=(
            f"{M_3} Всего: **{guild.member_count}**\n\n"
            f"{M_ONLINE} Онлайн: {online}\n"
            f"{M_AFK} Неактивны: {idle}\n"
            f"{M_DND} Не беспокоить: {dnd}\n"
            f"{M_1} Оффлайн: {offline}\n"
        ),
        inline=True
    )
    
    embed.add_field(
        name=f"> {B_Info} Chanels",
        value=(
            f"{B_Info} Текстовые: **{text_channels}**\n"
            f"{B_Info} Голосовые: **{voice_channels}**\n"
            f"{B_Info} Категории: **{categories}**\n"
            f"{SE_Role} Ролей: **{len(guild.roles)}\n**"
        ),
        inline=True
    )
    
    embed.add_field(
        name=f"> {B_Info} Other",
        value=(
            f"{S_Manager} Уровень верификации: {verification_levels.get(guild.verification_level, 'Неизвестно')}\n"
            f"{R_Booster} Уровень буста: {guild.premium_tier}\n"
            f"{R_Booster} Бустов: {guild.premium_subscription_count}\n"
        ),
        inline=False
    )
    
    if guild.description:
        embed.add_field(
            name=f"> {B_Info} Описание",
            value=guild.description[:500],
            inline=False
        )
    
    if guild.banner:
        embed.set_image(url=guild.banner.url)
    
    embed.set_footer(text=f"Запросил: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
    
    await interaction.response.send_message(embed=embed)
    
    bot.command_usage["serverinfo"] = bot.command_usage.get("serverinfo", 0) + 1
    logger.info(f"[🟩] serverinfo от {interaction.user}")

@bot.tree.command(name="userinfo", description="информация о пользователе")
@app_commands.describe(user="/userinfo <@username or just /userinfo for your information>")
@cmd_check() # чек включен ли он или нет
async def user_info(interaction: discord.Interaction, user: Optional[discord.Member] = None):

    target = user or interaction.user
    
    async def get_actual_status(member_or_user):
        if isinstance(member_or_user, discord.Member) and member_or_user.guild == interaction.guild:
            return member_or_user.status
        
        guild_member = interaction.guild.get_member(member_or_user.id)
        if guild_member:
            return guild_member.status
        
        try:
            fetched = await interaction.guild.fetch_member(member_or_user.id)
            return fetched.status
        except discord.NotFound:
            return discord.Status.offline
        except Exception as e:
            logger.warning(f"[🟨] Ошибка получения статуса для {member_or_user}: {e}")
            return discord.Status.offline

    actual_status = await get_actual_status(target)

    status_emojis = {
        discord.Status.online: f"{M_ONLINE} Онлайн",
        discord.Status.idle: f"{M_AFK} Неактивен", 
        discord.Status.dnd: f"{M_DND} Не Беспокоить",
        discord.Status.offline: f"{M_1} Оффлайн",
        discord.Status.do_not_disturb: f"{M_DND} Не Беспокоить"
    }

    status_display = status_emojis.get(actual_status, f"{M_1} Оффлайн")

    activity_text = "Нет активности"
    if target.activities:
        activities = []
        for activity in target.activities:
            if isinstance(activity, discord.Game):
                activities.append(f"Играет в **{activity.name}**")
            elif isinstance(activity, discord.Streaming):
                activities.append(f"Стримит **{activity.name}**")
            elif isinstance(activity, discord.Spotify):
                activities.append(f"Слушает **{activity.title}** от **{activity.artist}**")
        activity_text = f"{B_Info} • " + " • ".join(activities[:2])
        if len(target.activities) > 2:
            activity_text += f" +{len(target.activities)-2}"

    user_color = target.color if target.color.value != 0 else 0xf6d98e
    
    embed = discord.Embed(
        title=f"{M_1} {target.display_name}",
        color=user_color,
        timestamp=datetime.now(timezone.utc)
    )
    
    embed.set_thumbnail(url=target.display_avatar.url)
    
#    embed.add_field(
#        name=f"{M_1} Имя пользователя",
#        value=f"{target.name}",
#        inline=True
#    )

    embed.add_field(
        name=f"{SE_Web} ID",
        value=f"{target.id}",
        inline=True
    )

    embed.add_field(
        name=f"{SE_Web} Статус",
        value=status_display,
        inline=True
    )
    
    embed.add_field(
        name=f"> {SE_Welcome} Присоединился", 
        value=target.joined_at.strftime("%d.%m.%Y %H:%M"),
        inline=True
    )
    
    embed.add_field(
        name=f"> {SE_Home} Cоздан", 
        value=target.created_at.strftime("%d.%m.%Y %H:%M"),
        inline=True
    )
    
    roles = [role.mention for role in target.roles[1:]]  # Исключаем @everyone
    if roles:
        roles_text = " ".join(roles[:7])
        if len(roles) > 7:
            roles_text += f" *и ещё {len(roles) - 7}*"
    else:
        roles_text = "Нет ролей"
    
    embed.add_field(
        name=f"> {SE_Role} Роли ({len(roles)})",
        value=roles_text,
        inline=False
    )

    embed.add_field(
        name=f"> {SE_IdkReally} Активность",
        value=activity_text,
        inline=True
    )
    
#    embed.add_field(
#        name="📊 Дополнительно",
#        value=(
#            f"🤖 Бот: {'✅ Да' if target.bot else '❌ Нет'}\n"
#            f"🎨 Цвет: `{str(target.color)}`\n"
#            f"📋 Никнейм: `{target.nick or 'Нет'}`"
#        ),
#        inline=True
#    )
    
    # Баннер пользователя (если есть)
    if target.banner:
        embed.set_image(url=target.banner.url)
    
    # Значки пользователя (если есть)
    badges = []
    if target.public_flags.staff:
        badges.append(f"{S_Staff} Discord Staff")
    if target.public_flags.partner:
        badges.append(f"{P_OTHER} Discord Partner")
    if target.public_flags.hypesquad:
        badges.append("HypeSquad Events")
    if target.public_flags.bug_hunter:
        badges.append("Bug Hunter")
    if target.public_flags.bug_hunter_level_2:
        badges.append("Bug Hunter Level 2")
    if target.public_flags.early_supporter:
        badges.append(f"{SE_PingGood} Early Supporter")
    
    if badges:
        embed.add_field(
            name=f"> {SE_Web} Badges",
            value="\n".join(badges),
            inline=True
        )
    
    embed.set_footer(text=f"Запросил: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
    
    await interaction.response.send_message(embed=embed)
    
    bot.command_usage["userinfo"] = bot.command_usage.get("userinfo", 0) + 1
    logger.info(f"[🟩] userinfo от {interaction.user} для {target}")

@bot.tree.command(name="botstats", description="статистика бота")
@cmd_check() # чек включен ли он или нет
async def bot_stats(interaction: discord.Interaction):
    
    mc_stats = await bot.minecraft.get_stats()
    
    uptime = datetime.now(timezone.utc) - bot.start_time
    days, remainder = divmod(int(uptime.total_seconds()), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    cpu_percent = psutil.cpu_percent()
    memory = psutil.Process().memory_info().rss / 1024 ** 2  # В МБ
    disk_usage = psutil.disk_usage('/').percent
    
    embed = discord.Embed(
        title=f"{B_BotIcon} Статистика SEA_bot",
        description="*Подробная информация о работе бота*",
        color=0xf6d98e,
        timestamp=datetime.now(timezone.utc)
    )
    
    embed.add_field(
        name="Bot Stats",
        value=(
            f"Серверов: **{len(bot.guilds)}**\n"
            f"Пинг: **{round(bot.latency * 1000)}ms**\n"
            f"Время работы: **{days}д {hours}ч {minutes}м**\n"
            f"Версия бота: **v5.3**"
        ),
        inline=True
    )
    
    embed.add_field(
        name="MC Stats",
        value=(
            f"Статус: **{f'{SE_PingGood} Вкл' if mc_stats['is_running'] else f'{SE_PingBad} Выкл'}**\n"
            f"Сервер: **{f'{SE_PingGood} Онлайн' if mc_stats['is_online'] else f'{SE_PingBad} Оффлайн'}**\n"
            f"Обновлений: **{mc_stats['total_updates']}**\n"
            f"Успешных: **{mc_stats['success_rate']:.1f}%**"
        ),
        inline=True
    )
    
    # Системная информация
    embed.add_field(
        name="SEA Server Stats",
        value=(
            f"ЦП: **{cpu_percent}%**\n"
            f"Память: **{memory:.1f} MB**\n"
            f"Диск: **{disk_usage}%**\n"
            f"Платформа: **{platform.system()}**"
        ),
        inline=True
    )
    
    # Статистика команд
    total_commands = sum(bot.command_usage.values()) if bot.command_usage else 0
    if total_commands > 0:
        most_used = max(bot.command_usage, key=bot.command_usage.get) if bot.command_usage else "нет"
        least_used = min(bot.command_usage, key=bot.command_usage.get) if bot.command_usage else "нет"
        
        embed.add_field(
            name="CMD Stats",
            value=(
                f"Всего вызовов: **{total_commands}**\n"
                f"Чаще всего: `/{most_used}`\n"
                f"Редко: `/{least_used}`\n"
                f"Уникальных: **{len(bot.command_usage)}**"
            ),
            inline=True
        )
    
    # Информация о библиотеках
    embed.add_field(
        name="Other",
        value=(
            f"Python ver: **{platform.python_version()}**\n"
            f"discord.py ver: **{discord.__version__}**\n"
            f"Servers added: **{len(bot.guilds)}**\n"
            f"Commands: **{len(bot.tree.get_commands())}**"
        ),
        inline=True
    )
    
    # Uptime подробно
    if days > 0:
        uptime_detail = f"{days} дней, {hours} часов, {minutes} минут"
    else:
        uptime_detail = f"{hours} часов, {minutes} минут, {seconds} секунд"
    
    embed.add_field(
        name=f"{B_BotIcon} Время работы",
        value=uptime_detail,
        inline=False
    )
    
    embed.set_footer(
        text=f"Запросил: {interaction.user.name} | Запущен: {bot.start_time.strftime('%d.%m.%Y %H:%M')}",
        icon_url=interaction.user.display_avatar.url
    )
    
    await interaction.response.send_message(embed=embed)
    
    # Логируем использование
    bot.command_usage["botstats"] = bot.command_usage.get("botstats", 0) + 1
    logger.info(f"[🟩] botstats от {interaction.user}")

# ==============================================
# РАЗВЛЕКАТЕЛЬНЫЕ КОМАНДЫ
# ==============================================

@bot.tree.command(name="random", description="случайный выбор")
@app_commands.describe(choices="/random <A,B,C>")
@cmd_check() # чек включен ли он или нет
async def random_choice(interaction: discord.Interaction, choices: str):
    
    items = [item.strip() for item in choices.split(",") if item.strip()]
    
    if len(items) < 2:
        await interaction.response.send_message("❌ Нужно минимум 2 варианта! Например: `яблоко, банан, апельсин`", ephemeral=True)
        return
    
    chosen = random.choice(items)
    
    total_votes = len(items)
    percentage = (1 / total_votes) * 100
    
    embed = discord.Embed(
        title=f"{SE_IdkReally} Случайный выбор",
        color=0xf6d98e,
        timestamp=datetime.now(timezone.utc)
    )
    
    options_text = "\n".join([f"• {item}" for item in items])
    embed.add_field(name="📋 Варианты", value=options_text, inline=False)
    
    embed.add_field(
        name=f"{SE_IdkReally} Выбрано",
        value=f"**{chosen}**\nШанс: {percentage:.1f}%",
        inline=False
    )
    
    comments = [
        "Вердикт вынесен!",
        "Судьба решила!",
        "Рулетка остановилась на...",
        "И победителем становится...",
        "Выбор сделан!",
        "Это был сложный выбор, но..."
    ]
    
    embed.add_field(
        name="💬 Комментарий",
        value=random.choice(comments),
        inline=False
    )
    
    embed.set_footer(text=f"Запросил: {interaction.user.name}")
    
    await interaction.response.send_message(embed=embed)
    
    bot.command_usage["random"] = bot.command_usage.get("random", 0) + 1
    logger.info(f"[🟩] random от {interaction.user}")

# ==============================================
# АДМИН КОМАНДЫ
# ==============================================

@bot.tree.command(name="autorole", description="авторолка вкл/выкл")
@app_commands.describe(role="роль (оставь пустым чтобы выключить)")
@ace_check() # чек на то, он для разрабов или нет [по айди в коде]
@cmd_check() # чек включен ли он или нет
async def autorole(interaction: discord.Interaction, role: Optional[discord.Role] = None):
    config = load_config()
    
    if role is None:
        config["auto_role_id"] = None
        save_config(config)
        
        embed = discord.Embed(
            title="⚙️ Авто-роль",
            description="✅ **Авто-роль выключена**\n\nНовые участники не будут получать роль автоматически.",
            color=0xf6d98e
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        logger.info(f"[🟩] autorole выключена от {interaction.user}")  
        return
    
    # Проверяем права бота
    bot_member = interaction.guild.get_member(bot.user.id)
    if bot_member and bot_member.top_role <= role:
        embed = discord.Embed(
            title="❌ Ошибка",
            description=f"Бот не может выдать роль {role.mention}, потому что она выше или равна самой высокой роли бота.",
            color=0xff4444
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        logger.warning(f"[🟨] autorole недостаток прав для {interaction.user}: бот ниже роли {role.name}")
        return
    
    # Сохраняем роль
    config["auto_role_id"] = role.id
    save_config(config)
    
    embed = discord.Embed(
        title="⚙️ Авто-роль",
        description=f"✅ **Авто-роль настроена!**\n\nНовые участники будут автоматически получать роль {role.mention}.",
        color=0xf6d98e
    )
    embed.add_field(name="Роль", value=role.mention, inline=True)
    embed.add_field(name="ID", value=f"`{role.id}`", inline=True)
    embed.add_field(name="Цвет", value=f"`{str(role.color)}`", inline=True)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)
    logger.info(f"[🟩] autorole установлена: {role.name} от {interaction.user}")  
    
    # Логируем использование
    bot.command_usage["autorole"] = bot.command_usage.get("autorole", 0) + 1

@bot.tree.command(name="setwelcome", description="канал для велкома")
@app_commands.describe(channel="канал (оставь пустым чтобы выключить)")
@ace_check() # чек на то, он для разрабов или нет [по айди в коде]
@cmd_check() # чек включен ли он или нет
async def set_welcome(interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None):
    config = load_config()
    config["welcome_channel_id"] = channel.id if channel else None
    save_config(config)
    
    if channel:
        embed = discord.Embed(
            title="🎉 Приветственные сообщения",
            description=f"✅ **Приветствия включены!**\n\nТеперь новые участники будут получать приветствие в канале {channel.mention}.",
            color=0xf6d98e
        )
        status = f"**{channel.mention}**"
    else:
        embed = discord.Embed(
            title="🎉 Приветственные сообщения",
            description="✅ **Приветствия выключены**\n\nНовые участники не будут получать приветственные сообщения.",
            color=0xf6d98e
        )
        status = "**выключен**"
    
    await interaction.response.send_message(embed=embed, ephemeral=True)
    logger.info(f"[🟩] setwelcome: {status} от {interaction.user}")  
    
    # Логируем использование
    bot.command_usage["setwelcome"] = bot.command_usage.get("setwelcome", 0) + 1

@bot.tree.command(name="setmcstats", description="канал для MC статистики")
@app_commands.describe(channel="канал для статистики")
@ace_check() # чек на то, он для разрабов или нет [по айди в коде]
@cmd_check() # чек включен ли он или нет
async def set_mc_stats(interaction: discord.Interaction, channel: discord.TextChannel):
    config = load_config()
    config["mc_stats_channel"] = channel.id
    save_config(config)
    
    # Перезапускаем монитор
    await bot.minecraft.start()
    
    embed = discord.Embed(
        title="🎮 Minecraft статистика",
        description=f"✅ **Статистика настроена!**\n\nАвтоматическая статистика Minecraft будет обновляться в канале {channel.mention}.",
        color=0xf6d98e
    )
    embed.add_field(name="Канал", value=channel.mention, inline=True)
    embed.add_field(name="ID канала", value=f"`{channel.id}`", inline=True)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)
    logger.info(f"[🟩] setmcstats: {channel.name} от {interaction.user}")  
    
    # Логируем использование
    bot.command_usage["setmcstats"] = bot.command_usage.get("setmcstats", 0) + 1

@bot.tree.command(name="mcsetip", description="мц сервер IP")
@app_commands.describe(ip_port="ip:port")
@ace_check() # чек на то, он для разрабов или нет [по айди в коде]
@cmd_check() # чек включен ли он или нет
async def mc_set_ip(interaction: discord.Interaction, ip_port: str):
    config = load_config()
    config["mc_server_ip"] = ip_port.strip()
    save_config(config)
    
    # Перезапускаем монитор
    await bot.minecraft.start()
    
    embed = discord.Embed(
        title="🎮 Minecraft сервер",
        description=f"✅ **IP сервера обновлен!**",
        color=0xf6d98e
    )
    embed.add_field(name="Новый адрес", value=f"`{ip_port.strip()}`", inline=False)
    embed.add_field(name="Старый адрес", value=f"`{config.get('mc_server_ip', 'не установлен')}`", inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)
    logger.info(f"[🟩] mcsetip: {ip_port} от {interaction.user}")  
    
    # Логируем использование
    bot.command_usage["mcsetip"] = bot.command_usage.get("mcsetip", 0) + 1

@bot.tree.command(name="speak", description="отправить сообщение от имени бота")
@app_commands.describe(
    channel="куда слать",
    title="заголовок",
    desc="текст",
    view_creator="[True/False/yes/no/да/нет]",
    color="#hex или red/green/blue",
    thumbnail="Загрузи изображение",
    image="Загрузи большое изображение",
    footer="футер",
    field1_name="поле 1 название",
    field1_value="поле 1 текст [ ' | ' для переноса строки ]",
    field2_name="поле 2 название",
    field2_value="поле 2 текст [ ' | ' для переноса строки ]",
    field3_name="поле 3 название",
    field3_value="поле 3 текст [ ' | ' для переноса строки ]",
    field4_name="поле 4 название",
    field4_value="поле 4 текст [ ' | ' для переноса строки ]",
    ping="упомянуть кого-то",
    ping2="упомянуть ещё кого-то"
)
@ace_check() # чек на то, он для разрабов или нет [по айди в коде]
@cmd_check() # чек включен ли он или нет
async def speak(interaction: discord.Interaction, 
                channel: discord.TextChannel,
                title: str,
                desc: str,
                view_creator: str = None,
                color: str = "#f6d98e",
                thumbnail: Optional[discord.Attachment] = None,
                image: Optional[discord.Attachment] = None,
                footer: str = None,
                field1_name: str = None,
                field1_value: str = None,
                field2_name: str = None,
                field2_value: str = None,
                field3_name: str = None,
                field3_value: str = None,
                field4_name: str = None,
                field4_value: str = None,
                ping: str = None,
                ping2: str = None):
    
    
    # Обрезаем слишком длинные тексты
    title = title[:256]
    desc = desc[:4000]
    
    # Парсим цвет
    embed_color = parse_hex_color(color)
    
    # Создаем embed
    embed = discord.Embed(
        title=title, 
        description=desc, 
        color=embed_color,
        timestamp=datetime.now(timezone.utc)
    )
    
    # Обрабатываем thumbnail
    if thumbnail:
        if thumbnail.content_type and thumbnail.content_type.startswith('image/'):
            embed.set_thumbnail(url=thumbnail.url)
            logger.info(f"[🟦] Использован thumbnail: {thumbnail.filename}")
        else:
            logger.warning(f"[🟨] Файл thumbnail не является изображением: {thumbnail.filename}")
    
    # Обрабатываем основное изображение
    if image:
        if image.content_type and image.content_type.startswith('image/'):
            embed.set_image(url=image.url)
            logger.info(f"[🟦] Использовано изображение: {image.filename}")
        else:
            logger.warning(f"[🟨] Файл image не является изображением: {image.filename}")
    
    # Добавляем поля
    fields = [
        (field1_name, field1_value),
        (field2_name, field2_value),
        (field3_name, field3_value),
        (field4_name, field4_value)
    ]
    
    for field_name, field_value in fields:
        if field_name and field_value:
            formatted_value = field_value.replace(' | ', '\n')
            embed.add_field(
                name=field_name[:256],
                value=formatted_value[:1024],
                inline=False
            )
    
    # Обрабатываем пинги
    mentions = []
    if ping: 
        # Проверяем, является ли пинг упоминанием или просто текстом
        if ping.startswith('<@') and ping.endswith('>'):
            mentions.append(ping)
        else:
            mentions.append(f"@{ping}")
    
    if ping2:
        if ping2.startswith('<@') and ping2.endswith('>'):
            mentions.append(ping2)
        else:
            mentions.append(f"@{ping2}")
    
    if mentions:
        embed.add_field(
            name="👥 Упоминания",
            value=" ".join(mentions),
            inline=False
        )
    
    # Обрабатываем отображение автора
    if view_creator:
        view_creator_lower = view_creator.lower().strip()
        
        true_values = ['true', 't', 'yes', 'y', 'да', 'д']
        false_values = ['false', 'f', 'no', 'n', 'нет', 'н']
        
        if view_creator_lower in true_values:
            embed.set_author(
                name=interaction.user.display_name, 
                icon_url=interaction.user.display_avatar.url
            )
            logger.info(f"[🟦] Автор показан: {interaction.user.display_name}")
        elif view_creator_lower in false_values:
            logger.info(f"[🟦] Автор скрыт")
        else:
            logger.warning(f"[🟨] Неизвестное значение view_creator: '{view_creator}', автор скрыт")
    else:
        logger.info(f"[🟦] view_creator не указан, автор скрыт")
    
    # Устанавливаем footer
    if footer:
        embed.set_footer(text=footer[:2048])
    else:
        embed.set_footer(text=f"SEA_bot • {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    
    try: 
        # Отправляем сообщение
        await channel.send(embed=embed)
        
        # Отправляем подтверждение
        confirm_embed = discord.Embed(
            title="✅ Сообщение отправлено",
            description=f"Ваше сообщение было успешно отправлено в {channel.mention}",
            color=0xf6d98e
        )
        confirm_embed.add_field(name="Канал", value=channel.mention, inline=True)
        confirm_embed.add_field(name="Автор", value=interaction.user.mention, inline=True)
        
        await interaction.response.send_message(embed=confirm_embed, ephemeral=True)
        
        logger.info(f"[🟩] /Speak использован | Канал: {channel.name} | От: {interaction.user}")  
        
        # Логируем использование
        bot.command_usage["speak"] = bot.command_usage.get("speak", 0) + 1
        
    except Exception as e:
        error_embed = discord.Embed(
            title="❌ Ошибка отправки",
            description=f"Не удалось отправить сообщение: {str(e)[:100]}",
            color=0xff4444
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        logger.error(f"[🟥] speak error: {e} от {interaction.user}")

@bot.tree.command(name="fixeveryone", description="чинит роли безролам")
@app_commands.default_permissions(administrator=True)
@ace_check() # чек на то, он для разрабов или нет [по айди в коде]
@cmd_check() # чек включен ли он или нет
async def fix_everyone(interaction: discord.Interaction):
    config = load_config()
    role_id = config.get("auto_role_id")
    
    if not role_id:
        embed = discord.Embed(
            title="❌ Ошибка",
            description="Авто-роль не настроена. Сначала настройте её командой `/autorole`.",
            color=0xff4444
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        logger.warning(f"[🟨] fixeveryone: авторолка не настроена")
        return
    
    role = discord.utils.get(interaction.guild.roles, id=role_id)
    if not role:
        embed = discord.Embed(
            title="❌ Ошибка",
            description=f"Роль с ID `{role_id}` не найдена. Возможно она была удалена.",
            color=0xff4444
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        logger.warning(f"[🟨] fixeveryone: роль {role_id} не найдена")
        return
    
    # Ищем участников без ролей (только @everyone)
    needs_role = [
        m for m in interaction.guild.members 
        if len(m.roles) == 1 and role not in m.roles and not m.bot
    ]
    
    if not needs_role:
        embed = discord.Embed(
            title="✅ Проверка завершена",
            description="У всех участников уже есть роли! Некого исправлять.",
            color=0xf6d98e
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        logger.info(f"[🟩] fixeveryone: всем уже есть роль от {interaction.user}")  
        return
    
    # Отправляем начальное сообщение
    initial_embed = discord.Embed(
        title=f"{AL_LIDA_EMOJI} 🔧 Исправление ролей",
        description=f"Найдено **{len(needs_role)}** участников без ролей.\nНачинаю выдачу роли {role.mention}...",
        color=0xf6d98e
    )
    
    msg = await interaction.channel.send(embed=initial_embed)
    await interaction.response.send_message("🔄 Начинаю процесс...", ephemeral=True)
    
    # Выдаем роли
    fixed = 0
    failed = 0
    
    for i, member in enumerate(needs_role[:50], 1):  # Ограничение: 50 участников за раз
        try:
            await member.add_roles(role, reason=f"fixeveryone by {interaction.user}")
            fixed += 1
            
            # Обновляем статус каждые 10 участников
            if i % 10 == 0 or i == len(needs_role[:50]):
                progress_embed = discord.Embed(
                    title=f"{AL_LIDA_EMOJI} 🔧 Исправление ролей",
                    description=f"Обработано: **{i}/{len(needs_role[:50])}**\nУспешно: **{fixed}** | Ошибок: **{failed}**",
                    color=0xf6d98e
                )
                progress_embed.add_field(name="Текущий участник", value=member.mention, inline=True)
                progress_embed.add_field(name="Роль", value=role.mention, inline=True)
                
                await msg.edit(embed=progress_embed)
            
            await asyncio.sleep(0.5)  # Задержка чтобы не спамить API
            
        except Exception as e:
            failed += 1
            logger.error(f"[🟥] fixeveryone error для {member}: {e}")
    
    # Финальное сообщение
    final_embed = discord.Embed(
        title="✅ Исправление завершено",
        color=0xf6d98e
    )
    
    if fixed > 0:
        final_embed.description = f"✅ Успешно выдано ролей: **{fixed}**\n"
    if failed > 0:
        final_embed.description += f"❌ Ошибок: **{failed}**"
    
    final_embed.add_field(name="Роль", value=role.mention, inline=True)
    final_embed.add_field(name="Обработано", value=f"{len(needs_role[:50])} участников", inline=True)
    final_embed.add_field(name="Выполнил", value=interaction.user.mention, inline=True)
    
    await msg.edit(embed=final_embed)
    logger.info(f"[🟩] fixeveryone завершено: {fixed}/{len(needs_role)} от {interaction.user}")  
    
    # Логируем использование
    bot.command_usage["fixeveryone"] = bot.command_usage.get("fixeveryone", 0) + 1

@bot.tree.command(name="reactionrole", description="простая реакция=роль")
@app_commands.describe(emoji="эмодзи", role="роль")
@ace_check() # чек на то, он для разрабов или нет [по айди в коде]
@cmd_check() # чек включен ли он или нет
async def reaction_role(interaction: discord.Interaction, emoji: str, role: discord.Role):
    
    # Проверяем права бота
    bot_member = interaction.guild.get_member(bot.user.id)
    if bot_member and bot_member.top_role <= role:
        embed = discord.Embed(
            title="❌ Ошибка",
            description=f"Бот не может управлять ролью {role.mention}, потому что она выше или равна самой высокой роли бота.",
            color=0xff4444
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    embed = discord.Embed(
        title="🎭 Reaction Role", 
        description=(
            f"Нажми на реакцию {emoji} чтобы получить роль **{role.name}**\n"
            f"Нажми ещё раз чтобы убрать роль\n\n"
            f"*Роль: {role.mention}*\n"
            f"*Реакция: {emoji}*"
        ),
        color=0xf6d98e,
        timestamp=datetime.now(timezone.utc)
    )
    
    embed.set_footer(text=f"Создал: {interaction.user.name}")
    
    try:
        msg = await interaction.channel.send(embed=embed)
        await msg.add_reaction(emoji)
        
        # Сохраняем в конфиг
        config = load_config()
        config.setdefault("reaction_roles", {})
        config["reaction_roles"][str(msg.id)] = {
            "emoji": emoji, 
            "role_id": role.id,
            "channel_id": interaction.channel_id,
            "guild_id": interaction.guild_id,
            "created_by": interaction.user.id,
            "created_at": datetime.now().isoformat()
        }
        save_config(config)
        
        # Отправляем подтверждение
        confirm_embed = discord.Embed(
            title="✅ Reaction Role создан",
            description=f"Сообщение с реакцией создано в {interaction.channel.mention}",
            color=0xf6d98e
        )
        confirm_embed.add_field(name="Сообщение", value=f"[Перейти]({msg.jump_url})", inline=True)
        confirm_embed.add_field(name="Роль", value=role.mention, inline=True)
        confirm_embed.add_field(name="Реакция", value=emoji, inline=True)
        
        await interaction.response.send_message(embed=confirm_embed, ephemeral=True)
        
        logger.info(f"[🟩] reaction role: {emoji} → {role.name} от {interaction.user}")  
        
        # Логируем использование
        bot.command_usage["reactionrole"] = bot.command_usage.get("reactionrole", 0) + 1
        
    except Exception as e:
        error_embed = discord.Embed(
            title="❌ Ошибка",
            description=f"Не удалось создать Reaction Role: {str(e)[:100]}",
            color=0xff4444
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        logger.error(f"[🟥] reaction role error: {e} от {interaction.user}")

@bot.tree.command(name="clean", description="очистить сообщения")
@app_commands.describe(amount="количество (1-100)", user="пользователь (необязательно)")
@app_commands.default_permissions(manage_messages=True)
@ace_check() # чек на то, он для разрабов или нет [по айди в коде]
@cmd_check() # чек включен ли он или нет
async def clean_messages(interaction: discord.Interaction, 
                        amount: app_commands.Range[int, 1, 100],
                        user: Optional[discord.Member] = None):
    
    await interaction.response.defer(ephemeral=True)
    
    def check(msg):
        if user:
            return msg.author.id == user.id and not msg.pinned
        return not msg.pinned
    
    try:
        deleted = await interaction.channel.purge(limit=amount, check=check)
        
        embed = discord.Embed(
            title="🧹 Очистка завершена",
            color=0xf6d98e
        )
        
        if user:
            embed.description = f"Удалено **{len(deleted)}** сообщений от {user.mention}"
        else:
            embed.description = f"Удалено **{len(deleted)}** сообщений"
        
        embed.add_field(name="Канал", value=interaction.channel.mention, inline=True)
        embed.add_field(name="Выполнил", value=interaction.user.mention, inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
        logger.info(f"[🟩] clean: {len(deleted)} сообщений удалено от {interaction.user}")
        
        # Логируем использование
        bot.command_usage["clean"] = bot.command_usage.get("clean", 0) + 1
        
    except Exception as e:
        await interaction.followup.send(f"❌ Ошибка: {str(e)[:100]}", ephemeral=True)

@bot.tree.command(name="slowmode", description="установить медленный режим")
@app_commands.describe(seconds="секунды (0-21600)")
@app_commands.default_permissions(manage_channels=True)
@ace_check() # чек на то, он для разрабов или нет [по айди в коде]
@cmd_check() # чек включен ли он или нет
async def set_slowmode(interaction: discord.Interaction, 
                      seconds: app_commands.Range[int, 0, 21600]):
    
    try:
        await interaction.channel.edit(slowmode_delay=seconds)
        
        embed = discord.Embed(
            title="⏱️ Медленный режим",
            color=0xf6d98e
        )
        
        if seconds == 0:
            embed.description = "✅ Медленный режим **выключен**"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            
            time_str = ""
            if hours > 0:
                time_str += f"{hours}ч "
            if minutes > 0:
                time_str += f"{minutes}м "
            if secs > 0:
                time_str += f"{secs}с"
            
            embed.description = f"✅ Медленный режим установлен на **{time_str.strip()}** ({seconds} сек)"
        
        embed.add_field(name="Канал", value=interaction.channel.mention, inline=True)
        embed.add_field(name="Выполнил", value=interaction.user.mention, inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        logger.info(f"[🟩] slowmode: {seconds} секунд установлено от {interaction.user}")
        
        # Логируем использование
        bot.command_usage["slowmode"] = bot.command_usage.get("slowmode", 0) + 1
        
    except Exception as e:
        await interaction.response.send_message(f"❌ Ошибка: {str(e)[:100]}", ephemeral=True)

# ==============================================
# ОБРАБОТЧИКИ СОБЫТИЙ
# ==============================================

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return
    
    config = load_config()
    rr = config.get("reaction_roles", {})
    msg_id = str(payload.message_id)
    
    if msg_id in rr:
        guild = bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        emoji = str(payload.emoji)
        
        data = rr[msg_id]
        
        # Проверяем совпадает ли эмодзи
        if emoji != data["emoji"]:
            return
        
        role = guild.get_role(data["role_id"])
        
        if role and role not in member.roles:
            try:
                await member.add_roles(role)
                logger.info(f"[🟩] {emoji} → {role.name} → {member}")  
                
                # Отправляем уведомление в ЛС
                try:
                    embed = discord.Embed(
                        title="🎭 Роль выдана",
                        description=f"Вам была выдана роль **{role.name}** на сервере **{guild.name}**",
                        color=role.color if role.color.value != 0 else 0xf6d98e
                    )
                    embed.set_footer(text="Нажмите на реакцию ещё раз чтобы убрать роль")
                    await member.send(embed=embed)
                except:
                    pass  # Если не удалось отправить ЛС
                    
            except Exception as e:
                logger.error(f"[🟥] реакция роль ошибка добавления: {e}")  
        else:
            logger.warning(f"[🟨] реакция роль: роль не найдена или уже есть у {member}")  

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.user_id == bot.user.id:
        return
    
    config = load_config()
    rr = config.get("reaction_roles", {})
    msg_id = str(payload.message_id)
    
    if msg_id in rr:
        guild = bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        
        data = rr[msg_id]
        
        # Проверяем совпадает ли эмодзи
        if str(payload.emoji) != data["emoji"]:
            return
        
        role = guild.get_role(data["role_id"])
        
        if role and role in member.roles:
            try:
                await member.remove_roles(role)
                logger.info(f"[🟩] {role.name} ← {member}")  
                
                # Отправляем уведомление в ЛС
                try:
                    embed = discord.Embed(
                        title="🎭 Роль убрана",
                        description=f"С вас была убрана роль **{role.name}** на сервере **{guild.name}**",
                        color=0xff4444
                    )
                    embed.set_footer(text="Нажмите на реакцию чтобы вернуть роль")
                    await member.send(embed=embed)
                except:
                    pass  # Если не удалось отправить ЛС
                    
            except Exception as e:
                logger.error(f"[🟥] реакция роль ошибка удаления: {e}")  
        else:
            logger.warning(f"[🟨] реакция роль удаление: роль не найдена или нет у {member}")  

# ==============================================
# ЗАПУСК БОТА
# ==============================================

def load_token():
    try:
        dotenv.load_dotenv(TOKEN_FILE)
        token = os.getenv('TOKEN')
        
        if not token:
            raise ValueError("Токен не найден в файле конфигурации!")
        
        print(f"{GREEN}[🟩] Токен успешно загружен{RESET}")  
        return token
        
    except Exception as e:
        print(f"{RED}[🟪] ОШИБКА ЗАГРУЗКИ ТОКЕНА: {e}{RESET}")  
        raise

if __name__ == "__main__":
    print(f"{YELLOW}{'━'*62}{RESET}")
    print(f"{YELLOW} ███{RESET}{YELLOW}        SEA_console v5.3 {RESET}{YELLOW} • Подготовка к работе... {RESET}       {YELLOW}███{RESET}")
    print(f"{YELLOW}{'━'*62}{RESET}")
    
    try:
        TOKEN = load_token()
        bot.run(TOKEN)
        
    except KeyboardInterrupt:
        print(f"\n{YELLOW}[🟦] Бот остановлен пользователем [CTRL+C]{RESET}")
        
    except discord.LoginFailure:
        print(f"{RED}━{'━'*48}━{RESET}")
        print(f"{RED}[🟪] ОШИБКА АВТОРИЗАЦИИ: Неверный токен бота!{RESET}")  
        print(f"{RED}━{'━'*48}━{RESET}")
        logger.critical(f"[🟪] Ошибка авторизации: неверный токен")
        
    except Exception as e:
        print(f"{RED}━{'━'*48}━{RESET}")
        print(f"{RED}[🟪] КРИТИЧЕСКАЯ ОШИБКА: {e}{RESET}")  
        print(f"{RED}━{'━'*48}━{RESET}")
        logger.critical(f"[🟪] Критическая ошибка при запуске: {e}")
