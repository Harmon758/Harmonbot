
import discord
from discord.ext import commands

import asyncio
import datetime
import io
import random
import subprocess

import chess
import chess.engine
import chess.pgn
import chess.svg
import cpuinfo
try:
    from wand.image import Image
except ImportError as e:
    print(f"Failed to import Wand in Chess cog:\n{e}")

from utilities import checks


# TODO: Dynamically load chess engine not locked to version?
STOCKFISH_EXECUTABLE = "stockfish_14.1_win_x64"
try:
    CPUID = cpuinfo.CPUID()
    CPU_FLAGS = CPUID.get_flags(CPUID.get_max_extension_support())
    if "bmi2" in CPU_FLAGS:
        STOCKFISH_EXECUTABLE += "_bmi2"
    elif "avx2" in CPU_FLAGS:
        STOCKFISH_EXECUTABLE += "_avx2"
    elif "sse4_1" in CPU_FLAGS and "popcnt" in CPU_FLAGS:
        STOCKFISH_EXECUTABLE += "_popcnt"
    elif "ssse3" in CPU_FLAGS:
        STOCKFISH_EXECUTABLE += "_ssse"
    # BMI2 >= AVX2 > SSE4.1 + POPCNT (modern) >= SSSE3 > none
    # https://stockfishchess.org/download/
    # TODO: Handle 32-bit?
    # TODO: Handle not Windows?
except:
    pass
STOCKFISH_EXECUTABLE += ".exe"


async def setup(bot):
    await bot.add_cog(ChessCog(bot))


class ChessCog(commands.Cog, name = "Chess"):

    def __init__(self):
        self.matches = []

    async def cog_check(self, ctx):
        return await checks.not_forbidden().predicate(ctx)

    def cog_unload(self):
        # TODO: Persistence - store running chess matches and add way to continue previous ones
        for match in self.matches:
            match.task.cancel()

    # TODO: Use max concurrency?
    @commands.group(name = "chess", invoke_without_command = True, case_insensitive = True)
    async def chess_command(self, ctx):
        '''
        Play chess
        You can play me as well
        Supports standard algebraic and UCI notation
        '''
        if match := self.get_match(ctx.channel, ctx.author):
            await ctx.embed_reply(
                f"[You're already playing a chess match here]({match.message.jump_url})"
            )
            return

        await ctx.embed_reply(
            "Who would you like to play?"
        )
        message = await ctx.bot.wait_for(
            "message",
            check = lambda message: (
                message.author == ctx.author and
                message.channel == ctx.channel
            )
        )

        if message.content.lower() in ("harmonbot", "you"):
            opponent = ctx.bot.user
        elif message.content.lower() in ("myself", "me"):
            opponent = ctx.author
        else:
            try:
                opponent = await commands.MemberConverter().convert(
                    ctx, message.content
                )
            except commands.BadArgument:
                await ctx.embed_reply(
                    f"{ctx.bot.error_emoji} Opponent not found"
                )
                return

        if opponent != ctx.bot.user and self.get_match(ctx.channel, opponent):
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} Your chosen opponent is already playing a chess match here"
            )
            return

        if opponent == ctx.author:
            color = 'w'
        else:
            await ctx.embed_reply(
                "Would you like to play white, black, or random?"
            )
            message = await ctx.bot.wait_for(
                "message",
                check = lambda message: (
                    message.author == ctx.author and
                    message.channel == ctx.channel and
                    message.content.lower() in (
                        "white", "black", "random", 'w', 'b', 'r'
                    )
                )
            )
            color = message.content.lower()

        if color in ("random", 'r'):
            color = random.choice(('w', 'b'))

        if color in ("white", 'w'):
            white_player = ctx.author
            black_player = opponent
        elif color in ("black", 'b'):
            white_player = opponent
            black_player = ctx.author

        if opponent != ctx.bot.user and opponent != ctx.author:
            view = ChessChallengeView(opponent)
            challenge = await ctx.send(
                f"{opponent.mention}: {ctx.author} has challenged you to a chess match\n"
                "Would you like to accept?",
                view = view
            )
            await view.wait()

            if view.accepted:
                await challenge.edit(
                    f"{opponent.mention}: You have accepted {ctx.author}'s challenge"
                )
                await ctx.send(
                    f"{ctx.author.mention}: {opponent} has accepted your challenge"
                )
            else:
                await challenge.edit(
                    f"{opponent.mention}: You have declined {ctx.author}'s challenge"
                )
                await ctx.send(
                    f"{ctx.author.mention}: {opponent} has declined your challenge"
                )
                return

        match = await ChessMatch.start(ctx, white_player, black_player)
        self.matches.append(match)
        await match.ended.wait()
        self.matches.remove(match)

    def get_match(self, text_channel, player):
        return discord.utils.find(
            lambda match: (
                match.ctx.channel == text_channel and
                player in (match.white_player, match.black_player)
            ), self.matches
        )

    # TODO: Handle matches in DMs
    # TODO: Allow resignation
    # TODO: Allow draw offers
    # TODO: Track stats
    # TODO: Log matches?

    """
    @chess_command.command(name = "(╯°□°）╯︵", hidden = True)
    async def flip(self, ctx):
        '''Flip the table over'''
        self._chess_board.clear()
        await ctx.say(ctx.author.name + " flipped the table over in anger!")
    """

    @chess_command.command(aliases = ["last"], hidden = True)
    async def previous(self, ctx):
        '''Previous move'''
        match = self.get_match(ctx.channel, ctx.author)
        if not match:
            return await ctx.embed_reply(":no_entry: Chess match not found")
        try:
            await ctx.embed_reply(match.peek())
        except IndexError:
            await ctx.embed_reply(":no_entry: There was no previous move")

    """
    @chess_command.command()
    async def reset(self, ctx):
        '''Reset the board'''
        self._chess_board.reset()
        await ctx.embed_reply("The board has been reset")
    """

    @chess_command.command(hidden = True)
    async def turn(self, ctx):
        '''Who's turn it is to move'''
        match = self.get_match(ctx.channel, ctx.author)
        if not match:
            return await ctx.embed_reply(":no_entry: Chess match not found")
        if match.turn:
            await ctx.embed_reply("It's white's turn to move")
        else:
            await ctx.embed_reply("It's black's turn to move")

    """
    @chess_command.command()
    async def undo(self, ctx):
        '''Undo the previous move'''
        try:
            self._chess_board.pop()
            await self._display_chess_board(ctx, message = "The previous move was undone")
        except IndexError:
            await ctx.embed_reply(":no_entry: There are no more moves to undo")
    """


class ChessMatch(chess.Board):

    @classmethod
    async def start(cls, ctx, white_player, black_player):
        self = cls()
        self.ctx = ctx
        self.white_player = white_player
        self.black_player = black_player
        self.bot = ctx.bot
        self.ended = asyncio.Event()
        self.engine_transport, self.chess_engine = await chess.engine.popen_uci(
            f"bin/{STOCKFISH_EXECUTABLE}",
            creationflags = subprocess.CREATE_NO_WINDOW
        )
        self.message = None
        self.task = ctx.bot.loop.create_task(
            self.match_task(), name = "Chess Match"
        )
        return self

    def make_move(self, move):
        try:
            self.push_san(move)
        except ValueError:
            try:
                self.push_uci(move)
            except ValueError:
                return False
        return True

    def valid_move(self, move):
        try:
            self.parse_san(move)
        except ValueError:
            try:
                self.parse_uci(move)
            except ValueError:
                return False
        return True

    async def match_task(self):
        self.message = await self.ctx.embed_send("Loading..")
        await self.update_match_embed()

        while not self.ended.is_set():
            player = [self.black_player, self.white_player][int(self.turn)]
            embed = self.message.embeds[0]

            if player == self.bot.user:
                await self.message.edit(
                    embed = embed.set_footer(text = "I'm thinking..")
                )

                result = await self.chess_engine.play(
                    self, chess.engine.Limit(time = 2)
                )
                self.push(result.move)

                if self.is_game_over():
                    footer_text = None
                    self.ended.set()
                else:
                    footer_text = f"I moved {result.move}"

                await self.update_match_embed(footer_text = footer_text)
            else:
                message = await self.bot.wait_for(
                    "message",
                    check = lambda msg: (
                        msg.author == player and
                        msg.channel == self.ctx.channel and
                        self.valid_move(msg.content)
                    )
                )
                # TODO: Allow direct input and invalid move error response

                await self.message.edit(
                    embed = embed.set_footer(text = "Processing move..")
                )

                self.make_move(message.content)

                if self.is_game_over():
                    footer_text = None
                    self.ended.set()
                else:
                    footer_text = f"It is {['black', 'white'][int(self.turn)]}'s ({[self.black_player, self.white_player][int(self.turn)]}'s) turn to move"
                await self.update_match_embed(footer_text = footer_text)

                await self.bot.attempt_delete_message(message)

    async def update_match_embed(
        self, *, orientation = None, footer_text = None,
        send = False
    ):
        if self.message:
            embed = self.message.embeds[0]
        else:
            embed = discord.Embed(color = self.bot.bot_color)

        chess_pgn = chess.pgn.Game.from_board(self)
        chess_pgn.headers["Site"] = "Discord"
        chess_pgn.headers["Date"] = datetime.datetime.utcnow().strftime("%Y.%m.%d")
        chess_pgn.headers["White"] = self.white_player.mention
        chess_pgn.headers["Black"] = self.black_player.mention

        embed.description = str(chess_pgn)

        ## svg = self._repr_svg_()
        svg = chess.svg.board(
            self, lastmove = self.peek() if self.move_stack else None,
            check = self.king(self.turn) if self.is_check() else None,
            orientation = orientation or self.turn
        )

        buffer = io.BytesIO()
        with Image(blob = svg.encode()) as image:
            image.format = "PNG"
            image.save(file = buffer)
        buffer.seek(0)

        embed.set_image(url = "attachment://chess_board.png")
        embed.set_footer(text = footer_text)

        if send:
            self.message = await self.ctx.send(
                embed = embed,
                file = discord.File(buffer, filename = "chess_board.png"),
                view = ChessMatchView(self.bot, self)
            )
        else:
            await self.message.edit(
                attachments = [
                    discord.File(buffer, filename = "chess_board.png")
                ], embed = embed, view = ChessMatchView(self.bot, self)
            )


class ChessChallengeView(discord.ui.View):

    def __init__(self, challengee):
        super().__init__(timeout = None)
        self.challengee = challengee

    @discord.ui.button(label = "Yes", style = discord.ButtonStyle.green)
    async def yes(self, interaction, button):
        if interaction.user != self.challengee:
            await interaction.response.send_message(
                "You are not the one being challenged",
                ephemeral = True
            )
            return

        self.accepted = True
        await interaction.response.edit_message(view = None)
        self.stop()

    @discord.ui.button(label = "No", style = discord.ButtonStyle.red)
    async def no(self, interaction, button):
        if interaction.user != self.challengee:
            await interaction.response.send_message(
                "You are not the one being challenged",
                ephemeral = True
            )
            return

        self.accepted = False
        await interaction.response.edit_message(view = None)
        self.stop()


class ChessMatchView(discord.ui.View):

    def __init__(self, bot, match):
        super().__init__(timeout = None)
        self.bot = bot
        self.match = match
        self.resending = False

    @discord.ui.button(label = "FEN")
    async def fen(self, interaction, button):
        embed = discord.Embed(color = self.bot.bot_color)
        embed.set_author(
            icon_url = interaction.user.display_avatar.url,
            name = interaction.user.display_name
        )
        embed.title = "FEN"
        embed.description = self.match.fen()
        await interaction.response.send_message(embed = embed)

    @discord.ui.button(label = "Text")
    async def text(self, interaction, button):
        embed = discord.Embed(color = self.bot.bot_color)
        embed.set_author(
            icon_url = interaction.user.display_avatar.url,
            name = interaction.user.display_name
        )
        embed.title = "Text"
        embed.description = self.bot.CODE_BLOCK.format(self.match)
        await interaction.response.send_message(embed = embed)

    @discord.ui.button(
        label = "Resend Message", style = discord.ButtonStyle.blurple
    )
    async def resend_message(self, interaction, button):
        if self.resending:
            return
        self.resending = True

        if self.match.is_game_over():
            footer_text = None
        else:
            footer_text = f"It's {['black', 'white'][int(self.match.turn)]}'s ({[self.match.black_player, self.match.white_player][int(self.match.turn)]}'s) turn to move"
        await self.match.update_match_embed(
            footer_text = footer_text, send = True
        )

        await self.match.bot.attempt_delete_message(interaction.message)

        self.resending = False

