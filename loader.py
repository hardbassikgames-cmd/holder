import discord
import asyncio
import json
import os
import logging
import re
import pytz
import dotenv
from discord import app_commands
from mcstatus import JavaServer
from datetime import datetime, timezone
from typing import Optional

# 🟥 - ошибка
# 🟨 - варн\недостаток прав
# 🟩 - все нормис
# 🟦 - системное оповещение
# 🟪 - фатал ошибка

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

# SERVER_function
SE_Rules = "<:SE_Rules:1461405300677410951>"
SE_Punishment = "<:SE_Punishment:1461405237712654472>"
SE_Logs = "<:SE_Logs:1461408861637574882>"
SE_Warn = "<:SE_Warn:1461409018051301600>"
SE_Web = "<:SE_Web:1461439886321127515>"

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

# BOT_Utilities
B_Info = "<:B_Info:1461446330470891787>"
B_BotIcon = "<:B_Bot:1461405137359736903>"
# name = "markdown"

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
        "reaction_roles": {}
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
            color = 0xf6d98e                    # Зеленый
            ping_emoji = f"{SE_PingGood}"
            ping_status = "Шикарный пинг"
        elif status.latency < 150:
            color = 0xf6d98e                    # Светло-зеленый
            ping_emoji = f"{SE_Web}"
            ping_status = "Хороший пинг"
        elif status.latency < 300:
            color = 0xf6d98e                    # Желтый
            ping_emoji = f"{SE_PingNormal}"
            ping_status = "Такой себе пинг"
        else:
            color = 0xf6d98e                    # Красный
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
        
#        embed.add_field(
#            name=f"{status_emoji} a",
#            value=f"**{server_status}**",
#            inline=True
#        )
        
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
    
    async def setup_hook(self):
        try:
            await self.tree.sync()
            logger.info(f"[🟩] команды синхронизированы")  
        except Exception as e:
            logger.error(f"[🟥] команды не синхронизированы: {e}")  
    
    async def on_ready(self):
        print(f"{YELLOW}{'━'*62}{RESET}")
        print(f"{YELLOW} ███{RESET}{YELLOW}      SEA_bot v5.2 {GREEN}{self.user}{RESET}{YELLOW} • Готов к работе{RESET}     {YELLOW}███{RESET}")
        print(f"{YELLOW}{'                    ━━━━━━━━━━━━━━━━━━━━'}{RESET}")
        print(f"{YELLOW} ███{RESET}{YELLOW}           Серверов: • {GREEN}{len(self.guilds)}{RESET}{YELLOW} Команды: {GREEN}загружены{RESET}          {YELLOW}███{RESET}")
        print(f"{YELLOW}{'━'*62}{RESET}")
        
        await self.minecraft.start()
        
        await self.change_presence(
            activity=discord.Game(name="SEA_bot • dev-bot"),
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

# ━━━━━━━━[ основные командлы ]━━━━━━━━

@bot.tree.command(name="ping", description="проверка бота")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    uptime = datetime.now(timezone.utc) - bot.start_time
    hours = uptime.seconds // 3600
    minutes = (uptime.seconds % 3600) // 60
    seconds = uptime.seconds % 60
    
    if latency < 100:
        color = 0xf6d98e
        status = "Отлично"
    elif latency < 300:
        color = 0xf6d98e
        status = "Нормально"
    else:
        color = 0xf6d98e
        status = "Медленно"
    
    embed = discord.Embed(title="🏓 Понг!", color=color)
    embed.add_field(name="Задержка", value=f"{latency}ms ({status})")
    embed.add_field(name="Время работы", value=f"{hours}ч {minutes}м {seconds}с")
    embed.add_field(name="Серверов", value=len(bot.guilds))
    embed.set_footer(text=f"Запросил: {interaction.user.name}")
    
    await interaction.response.send_message(embed=embed)
    logger.info(f"[🟩] ping от {interaction.user}")  

@bot.tree.command(name="help", description="все команды")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title=f"{B_BotIcon} Все Команды",
        description="бувально, вот все команды :P",
        color=0xf6d98e
    )
    
    embed.add_field(
        name="Основные",
        value=(
            "• `/ping` - Проверить статус бота\n"
            "• `/help` - Эта справка\n"
            "• `/mcplayers` - Кто онлайн на сервере\n"
            "• `/roleinfo` - Инфо об авто-роли"
        ),
        inline=False
    )
    
    if is_allowed_user(interaction.user.id):
        embed.add_field(
            name="Админские",
            value=(
                "• `/autorole` - Настроить авто-роль\n"
                "• `/setwelcome` - Канал для приветствий\n"
                "• `/setmcstats` - Канал для статистики\n"
                "• `/mcsetip` - Изменить IP сервера\n"
                "• `/speak` - Отправить сообщение\n"
                "• `/fixeveryone` - Выдать роль всем\n"
                "• `/reactionrole` - Создать реакцию-роль"
            ),
            inline=False
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)
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
                                                                    # Определяем качество и цвет
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

        embed.add_field(name=f"{M_3}Игроки", value=f"{status.players.online}/{status.players.max}", inline=True)
        embed.add_field(name="Пинг", value=ping_str, inline=True)

        if status.players.sample:
            players = [p.name for p in status.players.sample]
            player_list = "\n".join(players[:10])
            embed.add_field(name="Онлайн", value=player_list, inline=False)
        else:
            embed.add_field(name="Онлайн", value="Никого нет", inline=False)

        embed.set_footer(text=f"{status.version.name} | {server_ip}")
        await interaction.followup.send(embed=embed)
        logger.info(f"[🟩] mcplayers от {interaction.user}")

    except Exception as e:
        await interaction.followup.send(f"**MC ERROR:** `{str(e)[:50]}`")
        logger.error(f"[🟥] mcplayers error: {e}")

@bot.tree.command(name="autorole", description="авторолка вкл/выкл")
@app_commands.describe(role="роль (оставь пустым чтобы выключить)")
@ace_check()
async def autorole(interaction: discord.Interaction, role: Optional[discord.Role] = None):
    config = load_config()
    
    if role is None:
        config["auto_role_id"] = None
        save_config(config)
        await interaction.response.send_message("авторолка выключена", ephemeral=True)
        logger.info(f"[🟩] autorole выключена от {interaction.user}")  
        return
    
    bot_member = interaction.guild.get_member(bot.user.id)
    if bot_member and bot_member.top_role <= role:
        await interaction.response.send_message(
            f"бот ниже роли `{role.name}`", 
            ephemeral=True
        )
        logger.warning(f"[🟨] autorole недостаток прав для {interaction.user}: бот ниже роли {role.name}")
        return
    
    config["auto_role_id"] = role.id
    save_config(config)
    await interaction.response.send_message(f"{role.mention} теперь авто", ephemeral=True)
    logger.info(f"[🟩] autorole установлена: {role.name} от {interaction.user}")  

@bot.tree.command(name="roleinfo", description="статус авторолки")
async def role_info(interaction: discord.Interaction):
    config = load_config()
    role_id = config.get("auto_role_id")
    
    if role_id:
        role = discord.utils.get(interaction.guild.roles, id=role_id)
        if role:
            embed = discord.Embed(title="Авто-роль", color=0xf6d98e)
            embed.add_field(name="Роль", value=role.mention)
            embed.add_field(name="Цвет", value=str(role.color))
            embed.add_field(name="Участников", value=len(role.members))
            embed.set_footer(text=f"ID: {role.id}")
            await interaction.response.send_message(embed=embed)
            logger.info(f"[🟩] roleinfo от {interaction.user}")  
        else:
            await interaction.response.send_message(f"**роль не найдена** (ID: {role_id})")
            logger.warning(f"[🟨] roleinfo роль не найдена: {role_id}")  
    else:
        await interaction.response.send_message("**авторолка выключена**")
        logger.info(f"[🟦] roleinfo от {interaction.user}: авторолка выключена")

@bot.tree.command(name="setwelcome", description="канал для велкома")
@app_commands.describe(channel="канал (оставь пустым чтобы выключить)")
@ace_check()
async def set_welcome(interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None):
    config = load_config()
    config["welcome_channel_id"] = channel.id if channel else None
    save_config(config)
    
    status = f"**{channel.mention}**" if channel else "**выключен**"
    await interaction.response.send_message(f"велком → {status}", ephemeral=True)
    logger.info(f"[🟩] setwelcome: {status} от {interaction.user}")  

@bot.tree.command(name="setmcstats", description="канал для MC статистики")
@app_commands.describe(channel="канал для статистики")
@ace_check()
async def set_mc_stats(interaction: discord.Interaction, channel: discord.TextChannel):
    config = load_config()
    config["mc_stats_channel"] = channel.id
    save_config(config)
    
    await bot.minecraft.start()
    
    await interaction.response.send_message(
        f"статистика → {channel.mention}", 
        ephemeral=True
    )
    logger.info(f"[🟩] setmcstats: {channel.name} от {interaction.user}")  

@bot.tree.command(name="mcsetip", description="мц сервер IP")
@app_commands.describe(ip_port="ip:port")
@ace_check()
async def mc_set_ip(interaction: discord.Interaction, ip_port: str):
    config = load_config()
    config["mc_server_ip"] = ip_port.strip()
    save_config(config)
    
    await bot.minecraft.start()
    
    await interaction.response.send_message(f"**MC:** `{ip_port.strip()}`", ephemeral=True)
    logger.info(f"[🟩] mcsetip: {ip_port} от {interaction.user}")  

# ━━━━━━━━[ сказать от имени бота, потом добавлю true\false типо ShowName(Optional) [true\false\да\нет\yes\no\nah\t\f\д\н\y\n] ]━━━━━━━━
@bot.tree.command(name="speak", description="custom embed spammer")
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
@ace_check()
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
                ping2: str = None
                ):
    
    title = title[:256]
    desc = desc[:4000]
    
    embed_color = parse_hex_color(color)
    
    embed = discord.Embed(
        title=title, 
        description=desc, 
        color=embed_color,
        timestamp=datetime.now(timezone.utc)
    )
    
    if thumbnail:
        if thumbnail.content_type and thumbnail.content_type.startswith('image/'):
            embed.set_thumbnail(url=thumbnail.url)
            logger.info(f"[🟦] Использован thumbnail: {thumbnail.filename}")
        else:
            logger.warning(f"[🟨] Файл thumbnail не является изображением: {thumbnail.filename}")
    
    if image:
        if image.content_type and image.content_type.startswith('image/'):
            embed.set_image(url=image.url)
            logger.info(f"[🟦] Использовано изображение: {image.filename}")
        else:
            logger.warning(f"[🟨] Файл image не является изображением: {image.filename}")
    

    if field1_name and field1_value:
        formatted_value = field1_value.replace(' | ', '\n')
        embed.add_field(
            name=field1_name[:256],
            value=formatted_value,
            inline=False
        )
        
    if field2_name and field2_value:
        formatted_value = field2_value.replace(' | ', '\n')
        embed.add_field(
            name=field2_name[:256],
            value=formatted_value,
            inline=False
        )

    if field3_name and field3_value:
        formatted_value = field3_value.replace(' | ', '\n')
        embed.add_field(
            name=field3_name[:256],
            value=formatted_value,
            inline=False
        )
        
    if field4_name and field4_value:
        formatted_value = field4_value.replace(' | ', '\n')
        embed.add_field(
            name=field4_name[:256],
            value=formatted_value,
            inline=False
        )

    mentions = []
    if ping: mentions.append(ping)
    if ping2: mentions.append(ping2)
    if mentions:
        embed.add_field(
            name="Пинги",
            value=" • ".join(mentions),
            inline=True
        )
    
# хочу пицу бляэ -Ace

    # автор
    if view_creator:
        view_creator_lower = view_creator.lower().strip() # парсим бул
        
        true_values = [
            'true', 't', 'yes', 'y', 'да', 'д',
            'true', 't', 'yes', 'y', 'да', 'д'
        ]
        
        false_values = [
            'false', 'f', 'no', 'n', 'нет', 'н',
            'false', 'f', 'no', 'n', 'нет', 'н'
        ]
        
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
    
    if footer:
        embed.set_footer(text=footer)
    else:
        embed.set_footer(text=f"SEA_Developers")
    
    try: 
        await channel.send(embed=embed)
        
        await interaction.response.send_message(f"{B_Info} • Успешно Отправлено в {channel.mention}.", ephemeral=True)
        logger.info(f"[🟩] /Speak был использован\n{YELLOW}███ Куда: [{channel.name}]\n███ От [{interaction.user}]{RESET}")  
    except Exception as e:
        await interaction.response.send_message(f"{B_Info} • ошибка лол кек {str(e)[:100]}", ephemeral=True)
        logger.error(f"[🟥] speak error: {e} от {interaction.user}")  

@bot.tree.command(name="fixeveryone", description="чинит роли безролам")
@app_commands.default_permissions(administrator=True)
@ace_check()
async def fix_everyone(interaction: discord.Interaction):
    config = load_config()
    role_id = config.get("auto_role_id")
    
    if not role_id:
        await interaction.response.send_message("[🟨] авторолка не стоит", ephemeral=True)  
        return
    
    role = discord.utils.get(interaction.guild.roles, id=role_id)
    if not role:
        await interaction.response.send_message("[🟥] роль удалена", ephemeral=True)  
        return
    
    # ищем тех у кого только @everyone
    needs_role = [m for m in interaction.guild.members 
                  if len(m.roles) <= 1 and role not in m.roles and not m.bot]
    
    if not needs_role:
        await interaction.response.send_message("✅ у всех уже есть роль!", ephemeral=True)
        logger.info(f"[🟩] fixeveryone: всем уже есть роль от {interaction.user}")  
        return
    
    embed = discord.Embed(
        title=f"{AL_LIDA_EMOJI} 🔧 чиним...",
        description=f"{len(needs_role)} чел без роли",
        color=0xf6d98e
    )
    
    msg = await interaction.channel.send(embed=embed)
    await interaction.response.send_message("🔄 начинаю...", ephemeral=True)
    
    fixed = 0
    for i, member in enumerate(needs_role[:50], 1):  # лимит 50(дабы бота не крашнуло от такого)
        try:
            await member.add_roles(role, reason="fixeveryone")
            fixed += 1
            
            if i % 10 == 0:
                embed.description = f"{fixed}/{len(needs_role)} | {member.name}"
                await msg.edit(embed=embed)
            
            await asyncio.sleep(0.3)
        except Exception as e:
            logger.error(f"[🟥] fixeveryone error для {member}: {e}")  
    
    embed.color = 0xf6d98e
    embed.description = f"✅ чинил: {fixed}/{len(needs_role)}"
    await msg.edit(embed=embed)
    logger.info(f"[🟩] fixeveryone завершено: {fixed}/{len(needs_role)} от {interaction.user}")  

@bot.tree.command(name="reactionrole", description="простая реакция=роль")
@app_commands.describe(emoji="эмодзи", role="роль")
@ace_check()
async def reaction_role(interaction: discord.Interaction, emoji: str, role: discord.Role):
    embed = discord.Embed(
        title="Reaction Role", 
        description=f"кликни {emoji} дабы получить **{role.name}**\nубери дабы потерять",
        color=0xf6d98e,
        timestamp=datetime.now(timezone.utc)
    )
    
    try:
        msg = await interaction.channel.send(embed=embed)
        await msg.add_reaction(emoji)
        
        config = load_config()
        config.setdefault("reaction_roles", {})
        config["reaction_roles"][str(msg.id)] = {
            "emoji": emoji, 
            "role_id": role.id
        }
        save_config(config)
        
        await interaction.response.send_message("[✅] реакция готова", ephemeral=True)
        logger.info(f"[🟩] reaction role: {emoji} → {role.name} от {interaction.user}")  
    except Exception as e:
        await interaction.response.send_message(f"[❌] {str(e)[:100]}", ephemeral=True)
        logger.error(f"[🟥] reaction role error: {e} от {interaction.user}")  

# ━━━━━━━━[ для выдачи роли при клике на реакцию ]━━━━━━━━
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
        role = guild.get_role(data["role_id"])
        
        if role and role not in member.roles:
            try:
                await member.add_roles(role)
                logger.info(f"[🟩] {emoji} → {role.name} → {member}")  
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
        role = guild.get_role(data["role_id"])
        
        if role and role in member.roles:
            try:
                await member.remove_roles(role)
                logger.info(f"[🟩] {role.name} ← {member}")  
            except Exception as e:
                logger.error(f"[🟥] реакция роль ошибка удаления: {e}")  
        else:
            logger.warning(f"[🟨] реакция роль удаление: роль не найдена или нет у {member}")  

# ━━━━━━━━[ запуск ]━━━━━━━━
def load_token():
    try:
        dotenv.load_dotenv(TOKEN_FILE)
        token = os.getenv('TOKEN')
        
        if not token:
            raise ValueError("токен не найден!")
        
        print(f"{GREEN}[🟩] токен загружен{RESET}")  
        return token
        
    except Exception as e:
        print(f"{RED}[🟪] ОШИБКА ТОКЕНА: {e}{RESET}")  
        raise

if __name__ == "__main__":
    print(f"{YELLOW}{'━'*62}{RESET}")
    print(f"{YELLOW} ███{RESET}{YELLOW}        SEA_console {RESET}{YELLOW} • Подготовка к работе... {RESET}       {YELLOW}███{RESET}")
    print(f"{YELLOW}{'━'*62}{RESET}")
    
    try:
        TOKEN = load_token()
        bot.run(TOKEN)
        
    except KeyboardInterrupt:
        print(f"\n{YELLOW}[🟦] бот остановлен с [CTRL+C]{RESET}")
        
    except Exception as e:
        print(f"{RED}━{'━'*48}━{RESET}")
        print(f"{RED}[🟪] КРИТИЧЕСКАЯ ОШИБКА: {e}{RESET}")  
        print(f"{RED}━{'━'*48}━{RESET}")
        logger.critical(f"[🟪] КРИТИЧЕСКАЯ ОШИБКА ПРИ ЗАПУСКЕ: {e}")  
