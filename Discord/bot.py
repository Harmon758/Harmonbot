
import discord
from discord import app_commands
from discord.ext import commands, menus

import asyncio
import contextlib
import datetime
import functools
import json
import logging
import os
from platform import python_version
import random
import sys
import traceback
from urllib import parse
# TODO: use urllib.parse

import aiml
import aiohttp
from aiohttp import web
import asyncpg
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import service_pb2_grpc
import gidgethub.aiohttp
import git
import google.auth
import google.cloud.translate
import imgurpython
import inflect
import pydealer
import pyowm
import requests
import sentry_sdk
import tomli  # Use tomllib in Python 3.11
import tweepy
import tweepy.asynchronous
import twitchio
import wolframalpha
from wordnik import swagger, WordApi, WordsApi
import yt_dlp as youtube_dl

from tree import CommandTree
from units.files import create_folder
from utilities import errors
from utilities.audio_player import AudioPlayer
from utilities.context import Context
from utilities.database import create_database_pool
from utilities.help_command import HelpCommand
from utilities.logging import AiohttpAccessLogger, initialize_aiohttp_access_logging, initialize_logging


class Bot(commands.Bot):

    def __init__(self):

        # Constants necessary for initialization
        self.beta = any("beta" in arg.lower() for arg in sys.argv)
        self.data_path = "data/beta" if self.beta else "data"

        # Initialize logging
        initialize_logging(self.data_path)

        # Initialization
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(
            activity = discord.Streaming(
                name = random.choice(self.game_statuses), url = self.stream_url
            ),
            case_insensitive = True,
            command_prefix = self.get_command_prefix,
            help_command = HelpCommand(
                command_attrs = {"aliases": ["commands"], "hidden": True}
            ),
            intents = intents,
            tree_cls = CommandTree
        )

        # Constants
        ## Custom
        self.version = "1.0.0-rc.10+g" + git.Repo("..").git.rev_parse("--short", "HEAD")
        self.owner_id = 115691005197549570
        self.listener_id = 180994984038760448
        self.changelog = "https://discord.gg/a2rbZPu"
        self.console_line_limit = 167
        self.console_message_prefix = "Discord Harmonbot: "
        self.library_path = "D:/Music/"
        self.simple_user_agent = "Harmonbot (Discord Bot)"
        self.user_agent = (
            "Harmonbot (Discord Bot) "
            f"Python/{python_version()} "
            f"aiohttp/{aiohttp.__version__}"
        )
        self.bot_color = self.bot_colour = discord.Color.blurple()  # previously 0x738bd7
        self.rss_color = self.rss_colour = 0xfa9b39  # other options: f26522, ee802f, ff6600; http://www.strawpoll.me/12384409
        self.twitter_color = self.twitter_colour = 0x00ACED
        self.twitch_icon_url = "https://s.jtvnw.net/jtv_user_pictures/hosted_images/GlitchIcon_purple.png"
        self.twitter_icon_url = "https://abs.twimg.com/icons/apple-touch-icon-192x192.png"
        ### Emoji
        self.emoji_skin_tone = self.emote_skin_tone = '\N{EMOJI MODIFIER FITZPATRICK TYPE-3}'  # TODO: use everywhere
        self.error_emoji = self.error_emote = '\N{NO ENTRY}'
        ## Constant
        self.CODE_BLOCK = "```\n{}\n```"  # TODO: Change to method?
        self.ANSI_CODE_BLOCK = "```ansi\n{}\n```"  # TODO: Change to method?
        self.PY_CODE_BLOCK = "```py\n{}\n```"  # TODO: Change to method?
        self.ZERO_WIDTH_SPACE = self.ZWSP = self.ZWS = '\N{ZERO WIDTH SPACE}'
        ### Discord
        self.EMBED_DESCRIPTION_CHARACTER_LIMIT = self.EMBED_DESCRIPTION_CHAR_LIMIT = self.EDCL = 4096
        self.EMBED_DESCRIPTION_CODE_BLOCK_ROW_CHARACTER_LIMIT = self.EDCBRCL = 56
        self.EMBED_DESCRIPTION_CODE_BLOCK_WIDTH_CHARACTER_LIMIT = self.EDCBWCL = self.EDCBRCL
        self.EMBED_FIELD_AMOUNT_LIMIT = self.EFAL = 25
        self.EMBED_FIELD_VALUE_CHARACTER_LIMIT = self.EMBED_FIELD_VALUE_CHAR_LIMIT = self.EFVCL = 1024
        self.EMBED_FIELD_VALUE_CODE_BLOCK_ROW_CHARACTER_LIMIT = self.EFVCBRCL = 55
        self.EMBED_FIELD_VALUE_CODE_BLOCK_WIDTH_CHARACTER_LIMIT = self.EFVCBWCL = self.EFVCBRCL
        self.EMBED_THUMBNAIL_URL_CHARACTER_LIMIT = self.ETUCL = 2048
        self.EMBED_TITLE_CHARACTER_LIMIT = self.EMBED_TITLE_CHAR_LIMIT = self.ETiCL = 256
        self.EMBED_TOTAL_CHARACTER_LIMIT = self.EMBED_TOTAL_CHAR_LIMIT = self.EToCL = 6000
        ## Functional
        ### Set on ready
        self.custom_emojis = {}
        self.invite_url = None
        self.last_resort_notices_channel = None
        self.listener_bot = None  # User object
        self.listing_sites = {}
        # TODO: Include owner variable for user object?
        # TODO: emote constants/variables

        # Variables
        self.guild_settings = {}
        self.online_time = datetime.datetime.now(datetime.timezone.utc)
        self.session_commands_invoked = {}
        self.session_slash_commands_invoked = {}
        self.socket_events = {}
        self.views = []

        # Credentials
        for credential in (
            "BRAWLHALLA_API_KEY", "CLARIFAI_API_KEY", "CLEVERBOT_API_KEY",
            "DISCORDBOTLIST.COM_API_TOKEN", "DISCORD.BOTS.GG_API_TOKEN",
            "DISCORDBOTS.ORG_API_KEY", "FIXER_API_KEY", "FONO_API_TOKEN",
            "GIPHY_API_KEY", "GITHUB_PERSONAL_ACCESS_TOKEN", "GOOGLE_API_KEY",
            "GOOGLE_CUSTOM_SEARCH_ENGINE_ID", "HTTP_SERVER_CALLBACK_URL",
            "IMGUR_CLIENT_ID", "IMGUR_CLIENT_SECRET", "NEWSAPI.ORG_API_KEY",
            "OMDB_API_KEY", "OSU_API_KEY", "OWM_API_KEY",
            "PAGE2IMAGES_REST_API_KEY", "READ_THE_DOCS_API_TOKEN",
            "SENTRY_DSN", "SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET_KEY",
            "STEAM_WEB_API_KEY", "TWITCH_CLIENT_ID", "TWITCH_CLIENT_SECRET",
            "TWITTER_BEARER_TOKEN", "TWITTER_CONSUMER_KEY",
            "TWITTER_CONSUMER_SECRET", "TWITTER_ACCESS_TOKEN",
            "TWITTER_ACCESS_TOKEN_SECRET","UNSPLASH_ACCESS_KEY",
            "WARGAMING_APPLICATION_ID", "WOLFRAM_ALPHA_APP_ID",
            "WORDNIK_API_KEY"
        ):
            setattr(self, credential.replace('.', '_'), os.getenv(credential))

        # Sentry
        sentry_sdk.init(self.SENTRY_DSN, release = self.version)

        # External Clients
        ## Clarifai
        self.clarifai_stub = service_pb2_grpc.V2Stub(
            ClarifaiChannel.get_grpc_channel()
        )
        ## Google Cloud Translation Service
        self.google_cloud_project_id = "discord-bot-harmonbot"
        ## Imgur
        try:
            self.imgur_client = imgurpython.ImgurClient(
                self.IMGUR_CLIENT_ID, self.IMGUR_CLIENT_SECRET
            )
        except imgurpython.helpers.error.ImgurClientError as e:
            self.print(f"Failed to initialize Imgur Client: {e}")
        ## OpenWeatherMap
        try:
            self.owm_client = pyowm.OWM(self.OWM_API_KEY)
            self.geocoding_manager = self.owm_client.geocoding_manager()
            self.weather_manager = self.owm_client.weather_manager()
        except AssertionError as e:
            self.print(f"Failed to initialize OpenWeatherMap client: {e}")
        ## Twitter
        self.twitter_client = tweepy.asynchronous.AsyncClient(
            bearer_token = self.TWITTER_BEARER_TOKEN,
            consumer_key = self.TWITTER_CONSUMER_KEY,
            consumer_secret = self.TWITTER_CONSUMER_SECRET,
            access_token = self.TWITTER_ACCESS_TOKEN,
            access_token_secret = self.TWITTER_ACCESS_TOKEN_SECRET
        )
        ## Wolfram Alpha
        self.wolfram_alpha_client = wolframalpha.Client(self.WOLFRAM_ALPHA_APP_ID)
        ## Wordnik
        try:
            self.wordnik_client = swagger.ApiClient(
                self.WORDNIK_API_KEY, "http://api.wordnik.com/v4"
            )
            self.wordnik_word_api = WordApi.WordApi(self.wordnik_client)
            self.wordnik_words_api = WordsApi.WordsApi(self.wordnik_client)
        except Exception as e:
            self.print(f"Failed to initialize Wordnik Client: {e}")
        ## youtube-dl
        self.ytdl_download_options = {
            "default_search": "auto", "noplaylist": True, "quiet": True,
            "format": "bestaudio/best", "extractaudio": True,
            "outtmpl": self.data_path + "/audio_cache/%(id)s-%(title)s.%(ext)s",
            "restrictfilenames": True
        }  # "audioformat": "mp3" ?
        self.ytdl_download = youtube_dl.YoutubeDL(self.ytdl_download_options)
        self.ytdl_info_options = {
            "default_search": "auto", "noplaylist": True, "quiet": True,
            "format": "webm[abr>0]/bestaudio/best", "prefer_ffmpeg": True
        }
        self.ytdl_info = youtube_dl.YoutubeDL(self.ytdl_info_options)
        self.ytdl_playlist_options = {
            "default_search": "auto", "ignoreerrors": True, "quiet": True,
            "format": "webm[abr>0]/bestaudio/best", "prefer_ffmpeg": True
        }
        self.ytdl_playlist = youtube_dl.YoutubeDL(self.ytdl_playlist_options)

        # AIML Kernel
        self.aiml_kernel = aiml.Kernel()
        for predicate, value in self.aiml_predicates.items():
            self.aiml_kernel.setBotPredicate(predicate, value)
        if os.path.isfile(self.data_path + "/aiml/aiml_brain.brn"):
            self.aiml_kernel.bootstrap(
                brainFile = self.data_path + "/aiml/aiml_brain.brn"
            )
        elif os.path.isfile(self.data_path + "/aiml/std-startup.xml"):
            self.aiml_kernel.bootstrap(
                learnFiles = self.data_path + "/aiml/std-startup.xml",
                commands = "load aiml b"
            )
            self.aiml_kernel.saveBrain(self.data_path + "/aiml/aiml_brain.brn")

        # Inflect engine
        self.inflect_engine = inflect.engine()

        # PostgreSQL database connection
        self.db = self.database = self.database_connection_pool = None
        self.connected_to_database = asyncio.Event()
        self.connected_to_database.set()

        # HTTP Web Server
        self.aiohttp_web_app = web.Application()
        self.aiohttp_web_app.add_routes([
            web.get('/', self.web_server_get_handler),
            web.post('/', self.web_server_post_handler),
            web.get("/robots.txt", self.web_server_robots_txt)
        ])
        self.aiohttp_app_runner = web.AppRunner(
            self.aiohttp_web_app,
            access_log_class = AiohttpAccessLogger
        )
        self.aiohttp_site = None  # Initialized when starting web server

        # Create temp folder
        create_folder(self.data_path + "/temp")

        # Add load, unload, and reload commands
        self.add_command(load)
        self.add_command(unload)
        self.add_command(reload)
        load.add_command(load_aiml)
        unload.add_command(unload_aiml)

    @property
    def aiml_predicates(self):
        # https://code.google.com/archive/p/aiml-en-us-foundation-alice/wikis/BotProperties.wiki
        return (
            self.config["aiml_predicates"] | {
                "build": self.version, "version": self.version
            }
        )
        # TODO: Add?: arch, boyfriend, city, dailyclients, developers, email,
        # favoriteartist, favoriteband, favoritequestion, favoritesong, hair,
        # hockeyteam, kindmusic, nclients, ndevelopers, orientation, party,
        # president, question, religion, state, totalclients

    @property
    @functools.cache
    def config(self):
        with open("../config.toml", "rb") as config_file:
            return tomli.load(config_file)

    @property
    def emoji_guild_ids(self):
        return self.config["Discord"]["emoji_guild_ids"]

    @property
    def game_statuses(self):
        return self.config["Discord"]["game_statuses"]

    @property
    def last_resort_notices_channel_id(self):
        return self.config["Discord"]["last_resort_notices_channel_id"]

    @property
    def mock_ip(self):
        return self.config["mock"]["ip"]

    @property
    def mock_location(self):
        return self.config["mock"]["location"]

    @property
    def stream_url(self):
        return self.config["Discord"]["stream_url"]

    @property
    def twitter_test_handle(self):
        return self.config["Twitter"]["test_handle"]

    async def setup_hook(self):
        self.loop.create_task(
            self.initialize_constant_objects(),
            name = "Initialize Discord objects as constant attributes of Bot"
        )

        self.loop.create_task(
            self.initialize_custom_emoji(),
            name = "Initialize custom emoji as constant attributes of Bot"
        )

        self.aiohttp_session = aiohttp.ClientSession(loop = self.loop)

        self.github_api = gidgethub.aiohttp.GitHubAPI(
            self.aiohttp_session, self.user_agent,
            oauth_token = self.GITHUB_PERSONAL_ACCESS_TOKEN
        )

        try:
            self.google_cloud_translation_service_client = (
                google.cloud.translate.TranslationServiceAsyncClient()
            )
        except google.auth.exceptions.DefaultCredentialsError as e:
            self.print(
                f"Failed to initialize Google Cloud Translation Service Client: {e}"
            )

        self.twitch_client = twitchio.Client(
            client_id = self.TWITCH_CLIENT_ID,
            client_secret = self.TWITCH_CLIENT_SECRET,
            loop = self.loop
        )

        await self.initialize_database()

        await initialize_aiohttp_access_logging(self.database)

        self.loop.create_task(self.startup_tasks(), name = "Bot startup tasks")

        # Fetch AppCommand models
        await self.tree.fetch_commands()

        # Load cogs
        try:
            for file in sorted(os.listdir("cogs")):
                if file.endswith(".py") and not file.startswith("reactions"):
                    await self.load_extension("cogs." + file[:-3])
            await self.load_extension("cogs.reactions")
        except Exception as e:
            sentry_sdk.capture_exception(e)
            # TODO: Include name of specific cog
            print(f"Unhandled exception when loading cogs", file = sys.stderr)
            traceback.print_exception(
                type(e), e, e.__traceback__, file = sys.stderr
            )
            logging.getLogger("errors").error(
                "Uncaught exception\n",
                exc_info = (type(e), e, e.__traceback__)
            )
            raise RuntimeError from e

    def print(self, message):
        print(f"[{datetime.datetime.now().isoformat()}] {self.console_message_prefix}{message}")

    async def connect_to_database(self):
        if self.database_connection_pool:
            return
        if self.connected_to_database.is_set():
            self.connected_to_database.clear()
            self.db = self.database = self.database_connection_pool = await create_database_pool()
            self.connected_to_database.set()
        else:
            await self.connected_to_database.wait()

    async def initialize_database(self):
        await self.connect_to_database()
        await self.db.execute("CREATE SCHEMA IF NOT EXISTS chat")
        await self.db.execute("CREATE SCHEMA IF NOT EXISTS direct_messages")
        await self.db.execute("CREATE SCHEMA IF NOT EXISTS meta")
        await self.db.execute("CREATE SCHEMA IF NOT EXISTS guilds")
        await self.db.execute("CREATE SCHEMA IF NOT EXISTS users")
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS chat.messages (
                created_at            TIMESTAMPTZ,
                message_id            BIGINT PRIMARY KEY,
                author_id             BIGINT,
                author_name           TEXT,
                author_discriminator  TEXT,
                author_display_name   TEXT,
                direct_message        BOOL,
                channel_id            BIGINT,
                channel_name          TEXT,
                guild_id              BIGINT,
                guild_name            TEXT,
                message_content       TEXT,
                embeds                JSONB [],
                thread                BOOL,
                thread_id             BIGINT,
                thread_name           TEXT
            )
            """
        )
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS chat.edits (
                edited_at       TIMESTAMPTZ,
                message_id      BIGINT REFERENCES chat.messages(message_id) ON DELETE CASCADE,
                before_content  TEXT,
                after_content   TEXT,
                before_embeds   JSONB [],
                after_embeds    JSONB [],
                PRIMARY KEY     (edited_at, message_id)
            )
            """
        )
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS direct_messages.prefixes (
                channel_id  BIGINT PRIMARY KEY,
                prefixes    TEXT []
            )
            """
        )
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS guilds.prefixes (
                guild_id  BIGINT PRIMARY KEY,
                prefixes  TEXT []
            )
            """
        )
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS guilds.settings (
                guild_id     BIGINT,
                name         TEXT,
                setting      BOOL,
                PRIMARY KEY  (guild_id, name)
            )
            """
        )
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS meta.commands_invoked (
                command  TEXT PRIMARY KEY,
                invokes  BIGINT
            )
            """
        )
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS meta.message_context_menu_commands (
                command      TEXT PRIMARY KEY,
                invocations  BIGINT
            )
            """
        )
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS meta.restart_channels (
                channel_id              BIGINT PRIMARY KEY,
                player_text_channel_id  BIGINT,
                restart_message_id      BIGINT
            )
            """
        )
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS meta.slash_commands (
                command      TEXT PRIMARY KEY,
                invocations  BIGINT
            )
            """
        )
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS meta.stats (
                timestamp           TIMESTAMPTZ PRIMARY KEY DEFAULT NOW(),
                uptime              INTERVAL,
                restarts            INT,
                cogs_reloaded       INT,
                commands_invoked    BIGINT,
                reaction_responses  BIGINT,
                menu_reactions      BIGINT
            )
            """
        )
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS meta.user_context_menu_commands (
                command      TEXT PRIMARY KEY,
                invocations  BIGINT
            )
            """
        )
        previous = await self.db.fetchrow(
            """
            SELECT * FROM meta.stats
            ORDER BY timestamp DESC
            LIMIT 1
            """
        )
        if previous:
            await self.db.execute(
                """
                INSERT INTO meta.stats (timestamp, uptime, restarts, cogs_reloaded, commands_invoked, reaction_responses, menu_reactions)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT DO NOTHING
                """,
                self.online_time, previous["uptime"], previous["restarts"],
                previous["cogs_reloaded"], previous["commands_invoked"], previous["reaction_responses"], previous["menu_reactions"]
            )
        else:
            await self.db.execute(
                """
                INSERT INTO meta.stats (timestamp, uptime, restarts, cogs_reloaded, commands_invoked, reaction_responses, menu_reactions)
                VALUES ($1, INTERVAL '0 seconds', 0, 0, 0, 0, 0)
                """,
                self.online_time
            )
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS users.stats (
                user_id                                   BIGINT PRIMARY KEY,
                commands_invoked                          INT,
                slash_command_invocations                 BIGINT,
                message_context_menu_command_invocations  BIGINT,
                user_context_menu_command_invocations     BIGINT
            )
            """
        )

    async def web_server_get_handler(self, request):
        '''
        async for line in request.content:
            print(line)
        '''
        hub_mode = request.query.get("hub.mode")
        if hub_mode == "denied":
            # TODO: Handle denied request
            return web.Response(stats = 501)  # Return 501 Not Implemented
        elif hub_mode in ("subscribe", "unsubscribe"):
            if "YouTube" not in self.cogs:
                return web.Response(status = 503)  # Return 503 Service Unavailable
            channel_id = parse.parse_qs(parse.urlparse(request.query.get("hub.topic")).query)["channel_id"][0]
            if (
                (channel_id in self.get_cog("YouTube").uploads_following and hub_mode == "subscribe") or
                (channel_id not in self.get_cog("YouTube").uploads_following and hub_mode == "unsubscribe")
            ):
                return web.Response(body = request.query.get("hub.challenge"))
            else:
                return web.Response(status = 404)  # Return 404 Not Found
        else:
            return web.Response(status = 400)  # Return 400 Bad Request

    async def web_server_post_handler(self, request):
        '''
        async for line in request.content:
            print(line)
        '''
        if (
            request.headers.get("User-Agent") == "FeedFetcher-Google; (+http://www.google.com/feedfetcher.html)" and
            request.headers.get("From") == "googlebot(at)googlebot.com" and
            request.content_type == "application/atom+xml"
        ):
            if "YouTube" not in self.cogs:
                return web.Response(status = 503)  # Return 503 Service Unavailable
            for link in requests.utils.parse_header_links(request.headers.get("Link")):
                if link["rel"] == "hub":
                    if link["url"] != "http://pubsubhubbub.appspot.com/":
                        return web.Response(status = 400)  # Return 400 Bad Request
                elif link["rel"] == "self":
                    channel_id = parse.parse_qs(parse.urlparse(link["url"]).query)["channel_id"][0]
                    if channel_id not in self.get_cog("YouTube").uploads_following:
                        return web.Response(status = 404)  # Return 404 Not Found
                        # TODO: Handle unsubscribe?
                else:
                    return web.Response(status = 400)  # Return 400 Bad Request
            request_content = await request.content.read()
            await self.get_cog("YouTube").process_upload(channel_id, request_content)
            return web.Response()
        else:
            return web.Response(status = 400)  # Return 400 Bad Request

    async def web_server_robots_txt(self, request):
        return web.Response(text = "User-agent: *\nDisallow: /")

    async def initialize_constant_objects(self):
        await self.wait_until_ready()
        self.invite_url = discord.utils.oauth_url(self.application_id)
        self.last_resort_notices_channel = self.get_channel(
            self.last_resort_notices_channel_id
        )
        self.listener_bot = await self.fetch_user(self.listener_id)
        # TODO: Handle NotFound and HTTPException?
        self.listing_sites = {
            "discord.bots.gg": {
                "name": "Discord Bots",
                "token": self.DISCORD_BOTS_GG_API_TOKEN,
                "url": f"https://discord.bots.gg/api/v1/bots/{self.user.id}/stats",
                "data": {"guildCount": len(self.guilds)},
                "guild_count_name": "guildCount"
            },
            "discordbots.org": {
                "name": "Discord Bot List",
                "token": self.DISCORDBOTS_ORG_API_KEY,
                "url": f"https://discordbots.org/api/bots/{self.user.id}/stats",
                "data": {"server_count": len(self.guilds)},
                "guild_count_name": "server_count"
            },
            "discordbotlist.com": {
                "name": "Discord Bot List",
                "token": f"Bot {self.DISCORDBOTLIST_COM_API_TOKEN}",
                "url": f"https://discordbotlist.com/api/bots/{self.user.id}/stats",
                "data": {"guilds": len(self.guilds)},
                "guild_count_name": "guilds"
            }
        }
        # TODO: Add users and voice_connections for discordbotlist.com
        # TODO: https://bots.ondiscord.xyz/
        # TODO: https://botlist.space/
        #       https://botsfordiscord.com/
        #       https://discord.boats/
        await self.update_all_listing_stats()

    async def initialize_custom_emoji(self):
        await self.wait_until_ready()
        for guild_id in self.emoji_guild_ids:
            guild = self.get_guild(guild_id)
            for emoji in guild.emojis:
                self.custom_emojis[emoji.name] = emoji

    def cards_to_string(
        self, cards, custom_emoji = False, hidden_card_indexes = ()
    ):
        if isinstance(cards, pydealer.Card):
            cards = (cards,)
        if isinstance(hidden_card_indexes, int):
            hidden_card_indexes = (hidden_card_indexes,)

        if custom_emoji and self.custom_emojis:
            card_count = 0
            first_line = ""
            second_line = ""
            third_line = ""
            for card in cards:
                while card_count in hidden_card_indexes:
                    first_line += (
                        str(self.custom_emojis["back_top_left_segment"]) +
                        str(self.custom_emojis["back_top_right_segment"]) + ' '
                    )
                    second_line += (
                        str(self.custom_emojis["back_middle_left_segment"]) +
                        str(self.custom_emojis["back_middle_right_segment"]) +
                        ' '
                    )
                    third_line += (
                        str(self.custom_emojis["back_bottom_left_segment"]) +
                        str(self.custom_emojis["back_bottom_right_segment"]) +
                        ' '
                    )
                    card_count += 1
                color = "black" if card.suit in ("Clubs", "Spades") else "red"
                value = card.value if len(card.value) < 3 else card.value[0]
                first_line += (
                    str(
                        self.custom_emojis[f"{color}_top_left_{value}_segment"]
                    ) +
                    str(self.custom_emojis["blank_top_right_segment"]) + ' '
                )
                second_line += (
                    str(
                        self.custom_emojis[f"{card.suit.lower()}_segment"]
                    ) * 2 + ' '
                )
                third_line += (
                    str(self.custom_emojis["blank_bottom_left_segment"]) +
                    str(
                        self.custom_emojis[
                            f"{color}_bottom_right_{value}_segment"
                        ]
                    ) + ' '
                )
                card_count += 1
            while card_count in hidden_card_indexes:
                first_line += (
                    str(self.custom_emojis["back_top_left_segment"]) +
                    str(self.custom_emojis["back_top_right_segment"]) + ' '
                )
                second_line += (
                    str(self.custom_emojis["back_middle_left_segment"]) +
                    str(self.custom_emojis["back_middle_right_segment"]) +
                    ' '
                )
                third_line += (
                    str(self.custom_emojis["back_bottom_left_segment"]) +
                    str(self.custom_emojis["back_bottom_right_segment"]) +
                    ' '
                )
                card_count += 1
            return f"{first_line[:-1]}\n{second_line[:-1]}\n{third_line[:-1]}"
        else:
            # TODO: Unicode card characters option
            # TODO: non-emoji version option
            SUIT_EMOJI = {
                "Clubs": "\N{BLACK CLUB SUIT}\N{VARIATION SELECTOR-16}",
                "Diamonds": "\N{BLACK DIAMOND SUIT}\N{VARIATION SELECTOR-16}",
                "Hearts": "\N{BLACK HEART SUIT}\N{VARIATION SELECTOR-16}",
                "Spades": "\N{BLACK SPADE SUIT}\N{VARIATION SELECTOR-16}"
            }
            return " | ".join(
                f"{SUIT_EMOJI[card.suit]} {card.value}" for card in cards
            )

    async def startup_tasks(self):
        await self.wait_until_ready()
        print(f"Started up Discord {self.user} ({self.user.id})")
        if (record := await self.db.fetchrow(
            """
            DELETE FROM meta.restart_channels
            WHERE player_text_channel_id IS NULL
            RETURNING *
            """
        )) and (restart_channel := self.get_channel(record["channel_id"])) and (restart_message_id := record["restart_message_id"]):
            try:
                restart_message = await restart_channel.fetch_message(restart_message_id)
                embed = restart_message.embeds[0]
                embed.description += f"\n\N{THUMBS UP SIGN}{self.emoji_skin_tone} Restarted"
                await restart_message.edit(embed = embed)
            except discord.NotFound:
                await self.send_embed(restart_channel, f"\N{THUMBS UP SIGN}{self.emoji_skin_tone} Restarted")
        if audio_cog := self.get_cog("Audio"):
            for record in await self.db.fetch("DELETE FROM meta.restart_channels RETURNING *"):
                if text_channel := self.get_channel(record["player_text_channel_id"]):
                    audio_cog.players[text_channel.guild.id] = AudioPlayer(self, text_channel)
                    await self.get_channel(record["channel_id"]).connect()
        # TODO: DM if joined new server
        # TODO: DM if left server
        # TODO: Track guild names
        # await voice.detectvoice()

    @staticmethod
    async def get_command_prefix(bot, message):
        if message.channel.type is discord.ChannelType.private:
            prefixes = await bot.db.fetchval(
                """
                SELECT prefixes
                FROM direct_messages.prefixes
                WHERE channel_id = $1
                """,
                message.channel.id
            )
        else:
            prefixes = await bot.db.fetchval(
                """
                SELECT prefixes
                FROM guilds.prefixes
                WHERE guild_id = $1
                """,
                message.guild.id
            )
        return prefixes if prefixes else '!'

    async def on_ready(self):
        self.print("readied")

    async def on_resumed(self):
        self.print("resumed")

    async def on_disconnect(self):
        self.print("disconnected")

    async def on_guild_join(self, guild):
        self.loop.create_task(
            self.update_all_listing_stats(),
            name = "Update all bot listing stats"
        )
        me = (
            discord.utils.get(self.get_all_members(), id = self.owner_id) or
            await self.fetch_user(self.owner_id)
        )
        guild_owner = guild.owner or await self.fetch_user(guild.owner_id)
        await self.send_embed(
            me,
            title = "Joined Server",
            thumbnail_url = guild.icon.url if guild.icon else None,
            fields = (
                ("Name", guild.name),
                ("ID", guild.id),
                ("Owner", str(guild_owner)),
                ("Members", str(guild.member_count))
            ),
            timestamp = guild.created_at
        )
        # TODO: Track guild names

    async def on_guild_remove(self, guild):
        # Despite what the discord.py documentation says, this can be
        # dispatched with `guild` being unavailable, because GUILD_DELETE
        # events can be received with no corresponding GUILD_CREATE for guilds
        # in the READY event list.
        # discord.py dispatches these to `on_guild_remove` instead of
        # `on_guild_unavailable` because `unavailable` is not set in the
        # GUILD_DELETE data. According to Danny, Discord says this is
        # "intended" even though their API documentation indicates otherwise.
        # https://discord.com/channels/336642139381301249/886973276541304832/887021755535863899
        # https://discord.com/developers/docs/topics/gateway#guild-delete
        # Possibly related: https://github.com/discord/discord-api-docs/issues/2850
        if guild.unavailable:
            self.print(f"Unavailable guild in on_guild_remove: {guild.id}")
            return
        self.loop.create_task(
            self.update_all_listing_stats(),
            name = "Update all bot listing stats"
        )
        me = (
            discord.utils.get(self.get_all_members(), id = self.owner_id) or
            await self.fetch_user(self.owner_id)
        )
        guild_owner = guild.owner or await self.fetch_user(guild.owner_id)
        await self.send_embed(
            me,
            title = "Left Server",
            thumbnail_url = guild.icon.url if guild.icon else None,
            fields = (
                ("Name", guild.name),
                ("ID", guild.id),
                ("Owner", str(guild_owner)),
                ("Members", str(guild.member_count))
            ),
            timestamp = guild.created_at
        )

    # TODO: on_command_completion
    async def on_command(self, ctx):
        if ctx.interaction:  # Ignore hybrid commands invoked as slash commands
            return

        self.session_commands_invoked[ctx.command.name] = self.session_commands_invoked.get(ctx.command.name, 0) + 1
        await self.db.execute(
            """
            UPDATE meta.stats
            SET commands_invoked = commands_invoked + 1
            WHERE timestamp = $1
            """,
            self.online_time
        )
        await self.db.execute(
            """
            INSERT INTO meta.commands_invoked (command, invokes)
            VALUES ($1, 1)
            ON CONFLICT (command) DO
            UPDATE SET invokes = commands_invoked.invokes + 1
            """,
            ctx.command.name
        )
        # TODO: Handle subcommand names
        await self.db.execute(
            """
            INSERT INTO users.stats (user_id, commands_invoked)
            VALUES ($1, 1)
            ON CONFLICT (user_id) DO
            UPDATE SET commands_invoked = COALESCE(stats.commands_invoked, 0) + 1
            """,
            ctx.author.id
        )
        # TODO: Track names
        if points_cog := self.get_cog("Points"):
            await points_cog.add(user = ctx.author)

    async def on_interaction(self, interaction):
        if not interaction.command:
            return

        if points_cog := self.get_cog("Points"):
            await points_cog.add(user = interaction.user)

        if isinstance(interaction.command, app_commands.Command):
            self.session_slash_commands_invoked[interaction.command.qualified_name] = (
                self.session_slash_commands_invoked.get(interaction.command.qualified_name, 0) + 1
            )
            await self.db.execute(
                """
                INSERT INTO meta.slash_commands (command, invocations)
                VALUES ($1, 1)
                ON CONFLICT (command) DO
                UPDATE SET invocations = slash_commands.invocations + 1
                """,
                interaction.command.qualified_name
            )
            await self.db.execute(
                """
                INSERT INTO users.stats (user_id, slash_command_invocations)
                VALUES ($1, 1)
                ON CONFLICT (user_id) DO
                UPDATE SET slash_command_invocations = COALESCE(stats.slash_command_invocations, 0) + 1
                """,
                interaction.user.id
            )
            # TODO: Track command names?
        elif isinstance(interaction.command, app_commands.ContextMenu):
            if interaction.command.type is discord.AppCommandType.message:
                await self.db.execute(
                    """
                    INSERT INTO meta.message_context_menu_commands (command, invocations)
                    VALUES ($1, 1)
                    ON CONFLICT (command) DO
                    UPDATE SET invocations = message_context_menu_commands.invocations + 1
                    """,
                    interaction.command.name
                )
                await self.db.execute(
                    """
                    INSERT INTO users.stats (user_id, message_context_menu_command_invocations)
                    VALUES ($1, 1)
                    ON CONFLICT (user_id) DO
                    UPDATE SET message_context_menu_command_invocations = COALESCE(stats.message_context_menu_command_invocations, 0) + 1
                    """,
                    interaction.user.id
                )
                # TODO: Track command names?
            elif interaction.command.type is discord.AppCommandType.user:
                await self.db.execute(
                    """
                    INSERT INTO meta.user_context_menu_commands (command, invocations)
                    VALUES ($1, 1)
                    ON CONFLICT (command) DO
                    UPDATE SET invocations = user_context_menu_commands.invocations + 1
                    """,
                    interaction.command.name
                )
                await self.db.execute(
                    """
                    INSERT INTO users.stats (user_id, user_context_menu_command_invocations)
                    VALUES ($1, 1)
                    ON CONFLICT (user_id) DO
                    UPDATE SET user_context_menu_command_invocations = COALESCE(stats.user_context_menu_command_invocations, 0) + 1
                    """,
                    interaction.user.id
                )
                # TODO: Track command names?

    async def on_command_error(self, ctx, error):
        # Ignore
        match error:
            # Not owner
            case commands.NotOwner():
                return
            # Command disabled or not found
            case commands.CommandNotFound() | commands.DisabledCommand():
                return
        # Check Failure
        if isinstance(error, commands.CheckAnyFailure):
            # Use last error in case where all checks in any failed
            error = error.errors[0]
        match error:
            # Guild only
            case commands.NoPrivateMessage():
                await ctx.embed_reply("Please use that command in a server")
                return
            # User missing permissions
            case errors.NotGuildOwner() | commands.MissingPermissions():
                # Also for commands.NotOwner?
                await ctx.embed_reply(
                    f"{self.error_emoji} You don't have permission to do that"
                )
                return
            # Bot missing permissions
            case commands.BotMissingPermissions():
                missing_permissions = self.inflect_engine.join(
                    [f"`{permission}`" for permission in error.missing_permissions]
                )
                await ctx.embed_reply(
                    "I don't have permission to do that here\n"
                    f"I need the {missing_permissions} {self.inflect_engine.plural('permission', len(error.missing_permissions))}"
                )
                return
            # User not permitted to use command
            case errors.NotPermitted():
                await ctx.embed_reply(
                    f"{self.error_emoji} You don't have permission to use that command here"
                )
                return
            # Not in voice channel + user permitted
            case errors.PermittedVoiceNotConnected():
                await ctx.embed_reply(
                    "I'm not in a voice channel\n"
                    f"Please use `{ctx.prefix}join` first"
                )
                return
            # Not in voice channel + user not permitted
            case errors.NotPermittedVoiceNotConnected():
                await ctx.embed_reply(
                    "I'm not in a voice channel\n"
                    f"Please ask someone with permission to use `{ctx.prefix}join` first"
                )
                return
        # User Input Error
        match error:
            # Missing required input
            case commands.MissingRequiredArgument():
                await ctx.embed_reply(
                    str(error).rstrip('.').replace("argument", "input")
                )
                return
            # Input parsing error
            case commands.ArgumentParsingError():
                await ctx.embed_reply(
                    f"{self.error_emoji} Error parsing input: " +
                    str(error).replace("'", '`')
                )
                return
            # Invalid input
            case (
                commands.BadArgument() | commands.BadLiteralArgument() |
                commands.BadUnionArgument()
            ):
                await ctx.embed_reply(
                    f"{self.error_emoji} Error: Invalid Input: {error}"
                )
                return
        # Command Invoke Error
        if isinstance(error, commands.CommandInvokeError):
            match error.original:
                # Unable to bulk delete messages older than 14 days
                case discord.HTTPException() if error.original.code == 50034:
                    await ctx.embed_reply(
                        f"{self.error_emoji} Error: You can only bulk delete messages that are under 14 days old"
                    )
                    return
                # Menus
                case menus.CannotEmbedLinks():
                    await ctx.embed_reply(
                        "I need to be able to send embeds to show menus\n"
                        "Plese give me permission to Embed Links"
                    )
                    return
                case menus.CannotAddReactions():
                    await ctx.embed_reply(
                        "I need to be able to add reactions to show menus\n"
                        "Please give me permission to Add Reactions"
                    )
                    return
                case menus.CannotReadMessageHistory():
                    await ctx.embed_reply(
                        "I need to be able to read message history to show menus\n"
                        "Please give me permission to Read Message History"
                    )
                    return
                # Bot missing permissions (Unhandled)
                case discord.Forbidden() | menus.CannotSendMessages():
                    self.print(
                        f"Missing Permissions for {ctx.command.qualified_name} in #{ctx.channel.name} in {ctx.guild.name}"
                    )
                    return
                # Discord Server Error
                case discord.DiscordServerError():
                    self.print(
                        f"Discord Server Error for {ctx.command.qualified_name}: {error.original}"
                    )
                    return
        # Handled with cog error handler
        if isinstance(error, commands.MaxConcurrencyReached):
            return
        # TODO: check embed links permission
        # Unhandled
        sentry_sdk.capture_exception(error)
        print(
            f"Ignoring exception in command {ctx.command}", file = sys.stderr
        )
        traceback.print_exception(
            type(error), error, error.__traceback__, file = sys.stderr
        )
        logging.getLogger("errors").error(
            "Uncaught exception\n",
            exc_info = (type(error), error, error.__traceback__)
        )

    async def on_error(self, event_method, *args, **kwargs):
        error_type, value, error_traceback = sys.exc_info()
        if error_type is discord.Forbidden:
            for arg in args:
                if isinstance(arg, commands.context.Context):
                    return self.print(f"Missing Permissions for {arg.command.qualified_name} in #{arg.channel.name} in {arg.guild.name}")
                if isinstance(arg, discord.Message):
                    return self.print(f"Missing Permissions for #{arg.channel.name} in {arg.guild.name}")
        await super().on_error(event_method, *args, **kwargs)
        logging.getLogger("errors").error("Uncaught exception\n", exc_info = (error_type, value, error_traceback))

    async def on_message_edit(self, before, after):
        try:
            if after.edited_at != before.edited_at:
                if before.content != after.content:
                    await self.db.execute(
                        """
                        INSERT INTO chat.edits (edited_at, message_id, before_content, after_content)
                        SELECT $1, $2, $3, $4
                        WHERE EXISTS (SELECT * FROM chat.messages WHERE chat.messages.message_id = $2)
                        ON CONFLICT (edited_at, message_id) DO
                        UPDATE SET before_content = $3, after_content = $4
                        """,
                        after.edited_at.replace(tzinfo = datetime.timezone.utc), after.id,
                        before.content.replace('\N{NULL}', ""), after.content.replace('\N{NULL}', "")
                    )
                before_embeds = [embed.to_dict() for embed in before.embeds]
                after_embeds = [embed.to_dict() for embed in after.embeds]
                if before_embeds != after_embeds:
                    await self.db.execute(
                        """
                        INSERT INTO chat.edits (edited_at, message_id, before_embeds, after_embeds)
                        SELECT $1, $2, $3, $4
                        WHERE EXISTS (SELECT * FROM chat.messages WHERE chat.messages.message_id = $2)
                        ON CONFLICT (edited_at, message_id) DO
                        UPDATE SET before_embeds = CAST($3 AS jsonb[]), after_embeds = CAST($4 AS jsonb[])
                        """,
                        after.edited_at.replace(tzinfo = datetime.timezone.utc), after.id, before_embeds, after_embeds
                    )
        except OSError as e:
            self.print(f"Error processing message edit: {e}")

    async def on_socket_event_type(self, event_type):
        self.socket_events[event_type] = self.socket_events.get(event_type, 0) + 1

    async def increment_menu_reactions_count(self):
        await self.db.execute(
            """
            UPDATE meta.stats
            SET menu_reactions = menu_reactions + 1
            WHERE timestamp = $1
            """,
            self.online_time
        )

    # TODO: optimize/overhaul
    def send_embed(
        self, destination, description = None, *, title = None,
        title_url = None, author_name = "", author_url = None,
        author_icon_url = None, image_url = None, thumbnail_url = None,
        footer_text = None, footer_icon_url = None, timestamp = None,
        fields = []
    ):
        embed = discord.Embed(
            title = title, url = title_url, timestamp = timestamp,
            color = self.bot_color
        )
        embed.description = str(description) if description else None
        if author_name:
            embed.set_author(
                name = author_name, url = author_url,
                icon_url = author_icon_url
            )
        if image_url:
            embed.set_image(url = image_url)
        if thumbnail_url:
            embed.set_thumbnail(url = thumbnail_url)
        embed.set_footer(text = footer_text, icon_url = footer_icon_url)
        for field_name, field_value in fields:
            embed.add_field(name = field_name, value = field_value)
        return destination.send(embed = embed)

    async def attempt_delete_message(self, message):
        with contextlib.suppress(discord.HTTPException):
            await message.delete()

    async def attempt_edit_message(self, message, **fields):
        with contextlib.suppress(
            aiohttp.ClientConnectionError, discord.HTTPException
        ):
            await message.edit(**fields)

    async def wait_for_raw_reaction_add_or_remove(self, *, emoji = None, message = None, user = None, timeout = None):
        def raw_reaction_check(payload):
            if emoji:
                if isinstance(emoji, (discord.Emoji, discord.PartialEmoji)):
                    if payload.emoji != emoji:
                        return False
                elif isinstance(emoji, str):
                    if payload.emoji.name != emoji:
                        return False
                elif payload.emoji.is_unicode_emoji():
                    if payload.emoji.name not in emoji:
                        return False
                elif payload.emoji not in emoji:
                    return False
            if message and payload.message_id != message.id:
                return False
            if user and payload.user_id != user.id:
                return False
            return True

        add = self.wait_for("raw_reaction_add", check = raw_reaction_check)
        remove = self.wait_for("raw_reaction_remove", check = raw_reaction_check)
        done, pending = await asyncio.wait((add, remove), return_when = asyncio.FIRST_COMPLETED, timeout = timeout)
        for task in pending:
            task.cancel()
        if not done:
            raise asyncio.TimeoutError
        return done.pop().result()

    async def wait_for_yes_or_no(
        self, *, channel = None, message = None, user = None, timeout = None,
        accept_text = True, use_reactions = False, cleanup = True
    ):
        def message_check(message):
            if channel and message.channel != channel:
                return False
            if user and message.author != user:
                return False
            if message.content not in ("yes", "no", 'y', 'n'):
                return False
            return True

        def raw_reaction_check(payload):
            if payload.message_id != message.id:
                return False
            if user and payload.user_id != user.id:
                return False
            if not payload.emoji.is_unicode_emoji():
                return False
            if payload.emoji.name not in (
                '\N{HEAVY CHECK MARK}', '\N{HEAVY MULTIPLICATION X}'
            ):
                return False
            return True

        to_wait_for = []

        if accept_text:
            to_wait_for.append(self.wait_for("message", check = message_check))

        if message and use_reactions:
            # TODO: Handle unable to add reactions
            await message.add_reaction('\N{HEAVY CHECK MARK}')
            await message.add_reaction('\N{HEAVY MULTIPLICATION X}')
            to_wait_for.append(
                self.wait_for("raw_reaction_add", check = raw_reaction_check)
            )
            to_wait_for.append(
                self.wait_for(
                    "raw_reaction_remove", check = raw_reaction_check
                )
            )

        done, pending = await asyncio.wait(
            to_wait_for, return_when = asyncio.FIRST_COMPLETED,
            timeout = timeout
        )
        for task in pending:
            task.cancel()

        if message and use_reactions and cleanup:
            await message.remove_reaction(
                '\N{HEAVY CHECK MARK}', message.guild.me
            )
            await message.remove_reaction(
                '\N{HEAVY MULTIPLICATION X}', message.guild.me
            )

        if not done:
            raise asyncio.TimeoutError

        result = done.pop().result()
        if isinstance(result, discord.Message):
            if cleanup:
                await self.attempt_delete_message(result)
            return result.content in ("yes", 'y')
        if isinstance(result, discord.RawReactionActionEvent):
            if cleanup:
                member = await message.guild.fetch_member(result.user_id)
                await message.remove_reaction(result.emoji.name, member)
                # TODO: Handle no permission to remove reaction
            return result.emoji.name == '\N{HEAVY CHECK MARK}'

    # Override Context class
    async def get_context(self, message, *, cls = Context):
        ctx = await super().get_context(message, cls = cls)
        return ctx

    # TODO: Case-Insensitive subcommands (override Group)

    async def get_guild_setting(self, guild_id, name):
        if guild_id not in self.guild_settings:
            await self.retrieve_guild_settings(guild_id)
        return self.guild_settings[guild_id].get(name)

    async def get_guild_settings(self, guild_id):
        if guild_id not in self.guild_settings:
            await self.retrieve_guild_settings(guild_id)
        return self.guild_settings[guild_id]

    async def retrieve_guild_settings(self, guild_id):
        self.guild_settings[guild_id] = {}
        records = await self.db.fetch(
            """
            SELECT name, setting
            FROM guilds.settings
            WHERE guild_id = $1
            """,
            guild_id
        )
        for record in records:
            self.guild_settings[guild_id][record["name"]] = record["setting"]

    async def set_guild_setting(self, guild_id, name, setting):
        await self.db.execute(
            """
            INSERT INTO guilds.settings (guild_id, name, setting)
            VALUES ($1, $2, $3)
            ON CONFLICT (guild_id, name) DO
            UPDATE SET setting = $3
            """,
            guild_id, name, setting
        )
        self.guild_settings.setdefault(guild_id, {})[name] = setting

    # Update stats on sites listing Discord bots
    async def update_listing_stats(self, site):
        site = self.listing_sites.get(site)
        if not site:
            # TODO: Print/log error
            return "Site not found"
        token = site["token"]
        if not token:
            # TODO: Print/log error
            return "Site token not found"
        url = site["url"]
        headers = {"authorization": token, "content-type": "application/json"}
        site["data"][site["guild_count_name"]] = len(self.guilds)
        # TODO: Add users and voice_connections for discordbotlist.com
        data = json.dumps(site["data"])
        async with self.aiohttp_session.post(url, headers = headers, data = data) as resp:
            if resp.status == 204:
                return "204 No Content"
            return await resp.text()

    # Update stats on all sites listing Discord bots
    async def update_all_listing_stats(self):
        for site in self.listing_sites:
            await self.update_listing_stats(site)

    async def restart_tasks(self, channel_id, message_id):
        # Increment restarts counter
        await self.db.execute(
            """
            UPDATE meta.stats
            SET restarts = restarts + 1
            WHERE timestamp = $1
            """,
            self.online_time
        )
        # Save restart text channel + voice channels
        await self.db.execute(
            """
            INSERT INTO meta.restart_channels (channel_id, restart_message_id)
            VALUES ($1, $2)
            ON CONFLICT (channel_id) DO NOTHING
            """,
            channel_id, message_id
        )
        if audio_cog := self.get_cog("Audio"):
            for voice_client in self.voice_clients:
                if player := audio_cog.players.get(voice_client.guild.id):
                    await self.db.execute(
                        """
                        INSERT INTO meta.restart_channels (channel_id, player_text_channel_id)
                        VALUES ($1, $2)
                        ON CONFLICT (channel_id) DO
                        UPDATE SET player_text_channel_id = $2
                        """,
                        voice_client.channel.id, player.text_channel.id
                    )
        # Stop views
        for count, view in enumerate(self.views, start = 1):
            if not view.is_finished():
                self.print(f"Stopping View {count} / {len(self.views)}")
                await view.stop()
        # TODO: Move to shutdown tasks?

    async def shutdown_tasks(self):
        # Save uptime
        now = datetime.datetime.now(datetime.timezone.utc)
        uptime = now - self.online_time
        with contextlib.suppress(asyncpg.UndefinedTableError):
            # Table might not have been created yet for CI
            if self.db:  # Might not be connected to database yet for CI
                await self.db.execute(
                    """
                    UPDATE meta.stats
                    SET uptime = uptime + $2
                    WHERE timestamp = $1
                    """,
                    self.online_time, uptime
                )
        # Close aiohttp session
        with contextlib.suppress(AttributeError):
            # Might not be initialized yet for CI
            await self.aiohttp_session.close()
        # Close database connection
        if self.database_connection_pool:
            # Might not be connected to database yet for CI
            await self.database_connection_pool.close()
        # Stop web server
        await self.aiohttp_app_runner.cleanup()


@commands.group(invoke_without_command = True, case_insensitive = True)
@commands.is_owner()
async def load(ctx, cog: str):
    '''Load cog'''
    try:
        await ctx.bot.load_extension("cogs." + cog)
    except commands.ExtensionAlreadyLoaded:
        await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: Cog already loaded")
    except commands.ExtensionFailed as e:
        await ctx.embed_reply(f"{ctx.bot.error_emoji} Error loading cog: {e.original.__class__.__name__}: {e.original}")
    except commands.ExtensionNotFound:
        await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: Cog not found")
    except commands.NoEntryPointError:
        await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: Setup function not found")
    except commands.ExtensionError as e:
        await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: {e}")
    except Exception as e:
        await ctx.embed_reply(f"\N{THUMBS DOWN SIGN}{ctx.bot.emoji_skin_tone} Failed to load `{cog}` cog\n{type(e).__name__}: {e}")
    else:
        await ctx.embed_reply(f"\N{THUMBS UP SIGN}{ctx.bot.emoji_skin_tone} Loaded `{cog}` cog \N{GEAR}")

@commands.group(invoke_without_command = True, case_insensitive = True)
@commands.is_owner()
async def unload(ctx, cog: str):
    '''Unload cog'''
    try:
        await ctx.bot.unload_extension("cogs." + cog)
    except commands.ExtensionNotLoaded:
        await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: Cog not found/loaded")
    except commands.ExtensionError as e:
        await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: {e}")
    except Exception as e:
        await ctx.embed_reply(f"\N{THUMBS UP SIGN}{ctx.bot.emoji_skin_tone} Failed to unload `{cog}` cog\n{type(e).__name__}: {e}")
    else:
        await ctx.embed_reply(f"\N{OK HAND SIGN}{ctx.bot.emoji_skin_tone} Unloaded `{cog}` cog \N{GEAR}")

@commands.command()
@commands.is_owner()
async def reload(ctx, cog: str):
    '''Reload cog'''
    try:
        await ctx.bot.reload_extension("cogs." + cog)
    except commands.ExtensionFailed as e:
        await ctx.embed_reply(f"{ctx.bot.error_emoji} Error loading cog: {e.original.__class__.__name__}: {e.original}")
    except commands.ExtensionNotFound:
        await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: Cog not found")
    except commands.ExtensionNotLoaded:
        await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: Cog not found/loaded")
    except commands.NoEntryPointError:
        await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: Setup function not found")
    except commands.ExtensionError as e:
        await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: {e}")
    except Exception as e:
        await ctx.embed_reply(f"\N{THUMBS DOWN SIGN}{ctx.bot.emoji_skin_tone} Failed to reload `{cog}` cog\n{type(e).__name__}: {e}")
    else:
        await ctx.bot.db.execute(
            """
            UPDATE meta.stats
            SET cogs_reloaded = cogs_reloaded + 1
            WHERE timestamp = $1
            """,
            ctx.bot.online_time
        )
        await ctx.embed_reply(f"\N{THUMBS UP SIGN}{ctx.bot.emoji_skin_tone} Reloaded `{cog}` cog \N{GEAR}")


@commands.command(name = "aiml", aliases = ["brain"])
@commands.is_owner()
async def load_aiml(ctx):
    '''Load AIML'''
    for predicate, value in ctx.bot.aiml_predicates.items():
        ctx.bot.aiml_kernel.setBotPredicate(predicate, value)
    if os.path.isfile(ctx.bot.data_path + "/aiml/aiml_brain.brn"):
        ctx.bot.aiml_kernel.bootstrap(brainFile = ctx.bot.data_path + "/aiml/aiml_brain.brn")
    elif os.path.isfile(ctx.bot.data_path + "/aiml/std-startup.xml"):
        ctx.bot.aiml_kernel.bootstrap(learnFiles = ctx.bot.data_path + "/aiml/std-startup.xml", commands = "load aiml b")
        ctx.bot.aiml_kernel.saveBrain(ctx.bot.data_path + "/aiml/aiml_brain.brn")
    await ctx.embed_reply(f"\N{OK HAND SIGN}{ctx.bot.emoji_skin_tone} Loaded AIML")

@commands.command(name = "aiml", aliases = ["brain"])
@commands.is_owner()
async def unload_aiml(ctx):
    '''Unload AIML'''
    ctx.bot.aiml_kernel.resetBrain()
    await ctx.embed_reply(f"\N{OK HAND SIGN}{ctx.bot.emoji_skin_tone} Unloaded AIML")

