
import discord
from discord import ui
from discord.ext import commands

import asyncio
import datetime
import html
import random
import sys
from typing import Optional
import warnings

import aiohttp
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
import dateutil.parser

from utilities import checks

sys.path.insert(0, "..")
from units.ansi import affix_ansi, TextColor
from units.trivia import capwords, check_answer
sys.path.pop(0)


async def setup(bot):
    await bot.add_cog(Trivia(bot))

class Trivia(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.trivia_boards = {}
        self.trivia_questions = {}

    async def cog_load(self):
        await self.bot.connect_to_database()
        await self.bot.db.execute("CREATE SCHEMA IF NOT EXISTS trivia")
        await self.bot.db.execute(
            """
            CREATE TABLE IF NOT EXISTS trivia.users (
                user_id    BIGINT PRIMARY KEY,
                correct    INT,
                incorrect  INT,
                money      INT
            )
            """
        )

    async def cog_unload(self):
        for trivia_board in self.trivia_boards.values():
            await trivia_board.stop()

    async def cog_check(self, ctx):
        return await checks.not_forbidden().predicate(ctx)

    @commands.hybrid_group(case_insensitive = True, fallback = "question")
    async def trivia(
        self, ctx, betting: Optional[bool] = False, 
        override_modal_answers: Optional[bool] = False,
        react: Optional[bool] = True, seconds: commands.Range[int, 1, 60] = 15
    ):
        """
        Trivia question
        Only your last answer is accepted
        Answers prepended with !, >, or | are ignored
        Questions are taken from Jeopardy!

        Parameters
        ----------
        betting
            Whether or not to enable betting with points (¤) based on the category
            (Defaults to False)
        override_modal_answers
            Whether or not to override modal answers with message answers
            (Defaults to False)
        react
            Whether or not to add reactions to submitted bets
            (Defaults to True)
        seconds
            How long to accept answers (and bets) for, in seconds
            (1 - 60, default is 15)
        """
        # Note: trivia bet command invokes this command
        await ctx.defer()

        if question := self.trivia_questions.get(ctx.channel.id):
            description = "There's already an active trivia question here"
            if question.response:
                description = f"[{description}]({question.response.jump_url})"
            await ctx.embed_reply(description)
            return

        try:
            self.trivia_questions[ctx.channel.id] = TriviaQuestion(
                seconds,
                betting = betting,
                override_modal_answers = override_modal_answers,
                react = react
            )
            await self.trivia_questions[ctx.channel.id].start(ctx)
        finally:
            del self.trivia_questions[ctx.channel.id]

    @commands.Cog.listener("on_message")
    async def on_trivia_question_message(self, message):
        if not (
            trivia_question := self.trivia_questions.get(message.channel.id)
        ):
            return
        if message.author.id == self.bot.user.id:
            return
        if trivia_question.accepting_bets and message.content.isdigit():
            if points_cog := self.bot.get_cog("Points"):
                points = await points_cog.get(message.author)
            else:
                raise RuntimeError(
                    "Points cog not loaded during trivia betting"
                )
            input_bet = int(message.content)
            bet = min(input_bet, 100)
            if bet <= points:
                trivia_question.bets[message.author] = bet

                embeds = trivia_question.bet_message.embeds
                del embeds[1:]
                embeds.append(
                    discord.Embed(
                        description = '\n'.join(
                            f"{player.mention} has bet {bet} "
                            f"{self.bot.inflect_engine.plural('point', bet)} "
                            "(`\N{CURRENCY SIGN}`)"
                            for player, bet in trivia_question.bets.items()
                        ),
                        color = self.bot.bot_color
                    )
                )
                await trivia_question.bet_message.edit(embeds = embeds)

                if trivia_question.react:
                    if input_bet <= 100:
                        await message.add_reaction(
                            '\N{WHITE HEAVY CHECK MARK}'
                        )
                    else:
                        await message.add_reaction('\N{HUNDRED POINTS SYMBOL}')
            else:
                ctx = await self.bot.get_context(message)
                await ctx.embed_reply(
                    "You don't have that many points (`\N{CURRENCY SIGN}`) "
                    "to bet!"
                )
        elif trivia_question.accepting_answers:
            if message.content.startswith(('!', '>', '|')):
                return
            if (
                not trivia_question.override_modal_answers and
                message.author in trivia_question.answered_through_modal
            ):
                return
            trivia_question.responses[message.author] = message.content
            embeds = trivia_question.response.embeds
            del embeds[2:]
            users = self.bot.inflect_engine.join(
                [user.mention for user in trivia_question.responses]
            )
            has_declension = self.bot.inflect_engine.plural(
                'has', len(trivia_question.responses)
            )
            embeds.append(
                discord.Embed(
                    description = f"{users} {has_declension} answered",
                    color = self.bot.bot_color
                )
            )
            await self.bot.attempt_edit_message(
                trivia_question.response, embeds = embeds
            )

    @trivia.command(with_app_command = False)
    async def bet(
        self, ctx, override_modal_answers: Optional[bool] = False,
        react: Optional[bool] = True, seconds: commands.Range[int, 1, 60] = 15
    ):
        """
        Trivia question with betting
        Only your last answer is accepted
        Answers prepended with !, >, or | are ignored
        Questions are taken from Jeopardy!

        Parameters
        ----------
        override_modal_answers
            Whether or not to override modal answers with message answers
            (Defaults to False)
        react
            Whether or not to add reactions to submitted bets
            (Defaults to True)
        seconds
            How long to accept answers (and bets) for, in seconds
            (1 - 60, default is 15)
        """
        if command := ctx.bot.get_command("trivia"):
            await ctx.invoke(
                command, betting = True,
                override_modal_answers = override_modal_answers,
                react = react, seconds = seconds
            )
        else:
            raise RuntimeError(
                "trivia command not found when trivia bet command invoked"
            )

    @trivia.command(aliases = ["jeopardy"])
    async def board(
        self, ctx, buzzer: bool = False,
        delete_selection_messages: bool = True, react: bool = False,
        seconds: commands.Range[int, 1, 60] = 15, turns: bool = False
    ):
        """
        Trivia board
        Based on Jeopardy!
        [category number] [value] can also be used to select clues

        Parameters
        ----------
        buzzer
            True: penalizes incorrect answers;
            False: allows everyone to answer at once
            (Defaults to False)
        delete_selection_messages
            Whether or not to attempt to delete messages selecting clues
            (Defaults to True)
        react
            Whether or not to add reactions to submitted answers
            (Defaults to False)
        seconds
            How long to accept answers for, in seconds
            (1 - 60, default is 15)
        turns
            True: invoker and last person to answer correctly select;
            False: anyone selects
            (Defaults to False)
        """
        # Note: jeopardy command invokes this command
        # TODO: Daily Double?
        await ctx.defer()

        if board := self.trivia_boards.get(ctx.channel.id):
            description = "There's already an active trivia board here"
            if board.message:
                description = f"[{description}]({board.message.jump_url})"
            await ctx.embed_reply(description)
            return

        if not (
            trivia_board := TriviaBoard(
                seconds, buzzer = buzzer,
                delete_selection_messages = delete_selection_messages,
                react = react, turns = turns
            )
        ):
            return

        self.trivia_boards[ctx.channel.id] = trivia_board
        await self.trivia_boards[ctx.channel.id].start(ctx)
        await self.trivia_boards[ctx.channel.id].ended.wait()
        del self.trivia_boards[ctx.channel.id]

    @commands.Cog.listener("on_message")
    async def on_trivia_board_message(self, message):
        if not (trivia_board := self.trivia_boards.get(message.channel.id)):
            return
        if trivia_board.awaiting_answer:
            if message.author.id == self.bot.user.id:
                return
            correct = await trivia_board.answer(
                message.author, message.content
            )
            if trivia_board.react:
                if correct:
                    await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
                else:
                    await message.add_reaction('\N{CROSS MARK}')
            return
        if not trivia_board.awaiting_selection:
            return
        if len(message_parts := message.content.split()) < 2:
            return
        try:
            category_number = int(message_parts[0])
            value = int(message_parts[1])
        except ValueError:
            return
        if category_number < 1 or category_number > len(trivia_board.board):
            return
        if value not in trivia_board.VALUES:
            return
        if trivia_board.turns and message.author != trivia_board.turn:
            ctx = await self.bot.get_context(message)
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} It's not your turn"
            )
            return
        if not trivia_board.board[category_number - 1]["clues"][value]:
            ctx = await self.bot.get_context(message)
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} That question has already been chosen"
            )
            return
        category_title = trivia_board.board[category_number - 1]["title"]
        embed = trivia_board.message.embeds[0]
        embed.description += (
            f"\n{message.author.mention} chose "
            f"`{category_title}` for `{value}`"
        )
        await self.bot.attempt_edit_message(
            trivia_board.message, embed = embed, view = None
        )
        if trivia_board.delete_selection_messages:
            await self.bot.attempt_delete_message(message)
        await trivia_board.select(category_number, value)

    # TODO: trivia board stats

    @trivia.command(
        aliases = [
            "cash", "level", "money", "points", "rank", "score", "stats"
        ]
    )
    async def statistics(self, ctx):
        """Trivia statistics"""
        await ctx.defer()
        record = await ctx.bot.db.fetchrow(
            """
            SELECT correct, incorrect, money
            FROM trivia.users
            WHERE user_id = $1
            """,
            ctx.author.id
        )
        if not record:
            await ctx.embed_reply("You have not played any trivia yet")
            return
        total = record["correct"] + record["incorrect"]
        correct_percentage = record["correct"] / total * 100
        description = (
            f"You have answered {record['correct']:,} / {total:,} "
            f"({correct_percentage:.2f}%) trivia questions correctly"
        )
        if (money := record["money"]) is not None:
            description += (
                f"\nYou had ${money:,} before betting was updated "
                "to use points (`\N{CURRENCY SIGN}`)"
            )
        await ctx.embed_reply(description)

    @trivia.command(
        aliases = ["levels", "ranks", "scoreboard", "scores", "top"]
    )
    async def leaderboard(self, ctx, number: commands.Range[int, 1, 15] = 10):
        """
        Trivia leaderboard

        Parameters
        ----------
        number
            Number of users to display on the leaderboard
            (1 - 15, default is 10)
        """
        await ctx.defer()
        fields = []
        async with ctx.bot.database_connection_pool.acquire() as connection:
            async with connection.transaction():
                # Postgres requires non-scrollable cursors to be created
                # and used in a transaction.
                async for record in connection.cursor(
                    """
                    SELECT * FROM trivia.users
                    ORDER BY correct DESC LIMIT $1
                    """,
                    number
                ):
                    # SELECT user_id, correct, incorrect?
                    user = ctx.bot.get_user(record["user_id"])
                    if not user:
                        user = await ctx.bot.fetch_user(record["user_id"])
                    total = record["correct"] + record["incorrect"]
                    correct_percentage = record["correct"] / total * 100
                    fields.append((
                        str(user),
                        f"{record['correct']:,} correct "
                        f"({correct_percentage:.2f}%)\n"
                        f"{total:,} answered"
                    ))
        await ctx.embed_reply(title = f"Trivia Top {number}", fields = fields)

    @commands.command()
    async def jeopardy(
        self, ctx, buzzer: bool = False, react: bool = False,
        seconds: commands.Range[int, 1, 60] = 15, turns: bool = False
    ):
        """
        Trivia board
        Based on Jeopardy!
        [category number] [value] can also be used to select clues

        Parameters
        ----------
        buzzer
            True: penalizes incorrect answers;
            False: allows everyone to answer at once
            (Defaults to False)
        react
            Whether or not to add reactions to submitted answers
            (Defaults to False)
        seconds
            How long to accept answers for, in seconds
            (1 - 60, default is 15)
        turns
            True: invoker and last person to answer correctly select;
            False: anyone selects
            (Defaults to False)
        """
        if command := ctx.bot.get_command("trivia board"):
            await ctx.invoke(
                command, buzzer = buzzer, react = react, seconds = seconds,
                turns = turns
            )
        else:
            raise RuntimeError(
                "trivia board command not found when jeopardy command invoked"
            )


class TriviaBoard:

    VALUES = (200, 400, 600, 800, 1000)

    def __init__(
        self, seconds, buzzer = True, delete_selection_messages = True,
        react = True, turns = True
    ):
        self.answered = asyncio.Event()  # This is not used if buzzer is True
        self.awaiting_answer = False  # This is not used if buzzer is True
        self.awaiting_selection = False  # TODO: Selection timeout?
        self.board = []
        self.board_lines = []
        # Whether or not to have a buzzer
        # If not, allows everyone to answer at once
        self.buzzer = buzzer
        self.delete_selection_messages = delete_selection_messages
        self.message = None
        # Whether or not to add reactions to submitted answers
        self.react = react
        self.scores = {}
        self.seconds = seconds
        self.turn = None  # Who's turn it is
        # Whether or not to enforce turns
        # with last person to answer correctly selecting
        self.turns = turns

        self.ended = asyncio.Event()

    async def start(self, ctx):
        self.bot = ctx.bot
        self.ctx = ctx
        self.message = await ctx.embed_reply(
            author_name = None,
            title = "Trivia Board",
            description = "Generating board..",
            footer_text = None
        )
        if self.turns:
            self.turn = ctx.author  # Command invoker goes first

        if not (await self.generate_board()):
            return False

        embed = self.message.embeds[0]
        embed.description = ctx.bot.ANSI_CODE_BLOCK.format(
            '\n'.join(self.board_lines)
        )
        if self.turns:
            embed.description += f"\nIt's {self.turn.mention}'s turn"

        self.view = TriviaBoardSelectionView(self)
        await self.message.edit(
            embed = embed, view = self.view
        )

        self.awaiting_selection = True
        return True

    async def answer(self, player, answer = None):
        if self.buzzer:
            embed = self.message.embeds[0]
            await self.message.edit(embed = embed)

            self.players_answered.append(player)
            self.answerer = player

            answer_prompt_message = await self.ctx.embed_send(
                title = "Trivia Board",
                title_url = self.message.jump_url,
                description = (
                    f"{player.mention} hit the buzzer\n"
                    f"{player.mention}: What's your answer?"
                ),
                embeds = [
                    discord.Embed(
                        description = "Time's up " + discord.utils.format_dt(
                            datetime.datetime.now(datetime.timezone.utc) +
                            datetime.timedelta(seconds = self.seconds),
                            style = 'R'
                        ),
                        color = self.bot.bot_color
                    )
                ]
            )

            try:
                message = await self.bot.wait_for(
                    "message",
                    check = self.answer_check, timeout = self.seconds
                )
            except asyncio.TimeoutError:
                self.scores[player] = (
                    self.scores.get(player, 0) - int(self.value)
                )
                await self.ctx.embed_send(
                    title = "Trivia Board",
                    title_url = answer_prompt_message.jump_url,
                    description = (
                        f"{player.mention} ran out of time and lost `{self.value}`\n"
                        f"{player.mention} now has `{self.scores[player]}`"
                    )
                )
                self.view = TriviaBoardBuzzerView(self, self.seconds)
                self.message = await self.ctx.send(
                    embed = self.message.embeds[0],
                    view = self.view
                )
                return
            finally:
                embed = answer_prompt_message.embeds[0]
                await answer_prompt_message.edit(embed = embed)

            answer = message.content

        if check_answer(
            self.correct_answer, answer,
            inflect_engine = self.bot.inflect_engine
        ):
            # Correct answer
            self.awaiting_answer = False
            self.answered.set()

            embed = self.message.embeds[0]
            await self.message.edit(embed = embed)

            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore", category = MarkupResemblesLocatorWarning
                )
                answer = BeautifulSoup(
                    html.unescape(self.correct_answer),
                    "html.parser"
                ).get_text().replace("\\'", "'")

            self.scores[player] = self.scores.get(player, 0) + int(self.value)

            response = (
                f"The answer was: `{answer}`\n"
                f"{player.mention} was correct and won `{self.value}`\n\n"
            )
            if scores := ", ".join(
                f"{player.mention}: `{score}`"
                for player, score in self.scores.items()
            ):
                response += scores + '\n'

            self.board[self.category_number - 1]["clues"][self.value] = None
            self.board_lines[2 * self.category_number - 1] = (
                (len(str(self.value)) * ' ').join(
                    self.board_lines[2 * self.category_number - 1].split(
                        str(self.value), maxsplit = 1
                    )
                )
            )
            response += self.bot.ANSI_CODE_BLOCK.format(
                '\n'.join(self.board_lines)
            )

            if clues_left := any(
                clue
                for category in self.board
                for clue in category["clues"].values()
            ):
                if self.turns:
                    self.turn = player
                    response += f"\nIt's {self.turn.mention}'s turn"
                self.view = TriviaBoardSelectionView(self)
            else:
                self.view = None

            self.message = await self.ctx.embed_send(
                title = "Trivia Board",
                title_url = (
                    answer_prompt_message.jump_url if self.buzzer
                    else self.message.jump_url
                ),
                description = response,
                view = self.view
            )
            self.awaiting_selection = True

            if not clues_left:
                await self.send_winner()
                self.ended.set()

            return True

        # Incorrect answer
        if self.buzzer:
            self.scores[player] = self.scores.get(player, 0) - int(self.value)
            await self.ctx.embed_send(
                title = "Trivia Board",
                title_url = answer_prompt_message.jump_url,
                description = (
                    f"{player.mention} was incorrect and lost `{self.value}`\n"
                    f"{player.mention} now has `{self.scores[player]}`"
                )
            )
            self.view = TriviaBoardBuzzerView(self, self.seconds)
            self.message = await self.ctx.send(
                embeds = [
                    self.message.embeds[0], 
                    discord.Embed(
                        description = "Time's up " + discord.utils.format_dt(
                            datetime.datetime.now(datetime.timezone.utc) +
                            datetime.timedelta(seconds = self.seconds),
                            style = 'R'
                        ),
                        color = self.bot.bot_color
                    )
                ],
                view = self.view
            )
        else:
            return False

    def answer_check(self, message):
        if message.channel != self.ctx.channel:
            return False

        return message.author == self.answerer

    async def select(self, category_number, value):
        if not self.awaiting_selection:
            return

        self.awaiting_selection = False

        self.category_number = category_number
        self.value = value

        clue = self.board[category_number - 1]["clues"][self.value]

        self.correct_answer = clue["answer"]
        self.players_answered = []  # This is only used if buzzer is True

        self.view = (
            TriviaBoardBuzzerView(self, self.seconds) if self.buzzer
            else None
        )
        self.message = await self.ctx.embed_send(
            title = (
                f"{self.board[category_number - 1]['title']}\n(for {value})"
            ),
            title_url = self.message.jump_url,
            description = clue["question"],
            footer_text = "Air Date",
            timestamp = dateutil.parser.parse(clue["airdate"]),
            embeds = [
                discord.Embed(
                    description = "Time's up " + discord.utils.format_dt(
                        datetime.datetime.now(datetime.timezone.utc) +
                        datetime.timedelta(seconds = self.seconds),
                        style = 'R'
                    ),
                    color = self.bot.bot_color
                )
            ],
            view = self.view
        )

        if not self.buzzer:
            self.answered.clear()
            self.awaiting_answer = True
            try:
                await asyncio.wait_for(
                    self.answered.wait(), timeout = self.seconds
                )
            except asyncio.TimeoutError:
                # Replace with TimeoutError in Python 3.11
                self.awaiting_answer = False
                await self.timeout()

    async def timeout(self):
        embed = self.message.embeds[0]
        await self.message.edit(embed = embed)

        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", category = MarkupResemblesLocatorWarning
            )
            answer = BeautifulSoup(
                html.unescape(self.correct_answer),
                "html.parser"
            ).get_text().replace("\\'", "'")

        response = (
            f"The answer was: `{answer}`\n"
            "Nobody got it right\n\n"
        )
        if scores := ", ".join(
            f"{player.mention}: `{score}`"
            for player, score in self.scores.items()
        ):
            response += scores + '\n'

        self.board[self.category_number - 1]["clues"][self.value] = None
        self.board_lines[2 * self.category_number - 1] = (
            (len(str(self.value)) * ' ').join(
                self.board_lines[2 * self.category_number - 1].split(
                    str(self.value), maxsplit = 1
                )
            )
        )
        response += self.bot.ANSI_CODE_BLOCK.format(
            '\n'.join(self.board_lines)
        )

        if clues_left := any(
            clue
            for category in self.board
            for clue in category["clues"].values()
        ):
            if self.turn:
                response += f"\nIt's {self.turn.mention}'s turn"
            self.view = TriviaBoardSelectionView(self)
        else:
            self.view = None

        self.message = await self.ctx.embed_send(
            title = "Trivia Board",
            title_url = self.message.jump_url,
            description = response,
            view = self.view
        )
        self.awaiting_selection = True

        if not clues_left:
            await self.send_winner()
            self.ended.set()

    async def generate_board(self):
        while len(self.board) < 6:
            async with self.bot.aiohttp_session.get(
                "http://jservice.io/api/random",
                params = {"count": 6 - len(self.board)}
            ) as resp:
                if resp.status in (500, 503):
                    embed = self.message.embeds[0]
                    embed.description = (
                        f"{self.ctx.bot.error_emoji} Error: "
                        "Error connecting to API"
                    )
                    await self.message.edit(embed = embed)
                    return False
                data = await resp.json()

            for random_clue in data:
                category_id = random_clue["category_id"]

                if category_id is None or category_id in self.board:
                    # TODO: Fix duplicate category check
                    continue

                async with self.bot.aiohttp_session.get(
                    "http://jservice.io/api/category",
                    params = {"id": category_id}
                ) as resp:
                    if resp.status == 404:
                        continue
                    elif resp.status == 503:
                        embed = self.message.embeds[0]
                        embed.description = (
                            f"{self.ctx.bot.error_emoji} Error: Error connecting to API"
                        )
                        await self.message.edit(embed = embed)
                        return False
                    data = await resp.json()

                # The first round originally ranged from $100 to $500
                # and was doubled to $200 to $1,000 on November 26, 2001
                # https://en.wikipedia.org/wiki/Jeopardy!
                # http://www.j-archive.com/showgame.php?game_id=1062
                # jService uses noon UTC for airdates
                # jService doesn't include Double Jeopardy! clues
                transition_date = datetime.datetime(
                    2001, 11, 26, 12, tzinfo = datetime.timezone.utc
                )
                clues = {value: [] for value in self.VALUES}
                for clue in data["clues"]:
                    if not clue["question"] or not clue["value"]:
                        continue
                    if dateutil.parser.parse(clue["airdate"]) < transition_date:
                        clues[clue["value"] * 2].append(clue)
                    else:
                        clues[clue["value"]].append(clue)
                if not all(clues.values()):
                    continue

                self.board.append({
                    "title": capwords(random_clue["category"]["title"]),
                    "clues": {
                        value: random.choice(clues[value])
                        for value in self.VALUES
                    }
                })

        for number, category in enumerate(self.board, start = 1):
            self.board_lines.append(
                affix_ansi(
                    str(number) + ')',
                    bold = True,
                    text_color = TextColor.GREEN
                ) + ' ' + affix_ansi(
                    category["title"],
                    bold = True,
                    text_color = TextColor.CYAN
                )
            )
            self.board_lines.append(
                affix_ansi(
                    "   200 400 600 800 1000",
                    text_color = TextColor.BLUE
                )
            )

        return True

    async def send_winner(self):
        highest_score = max(self.scores.values())
        winners = [
            answerer.mention
            for answerer, score in self.scores.items()
            if score == highest_score
        ]
        is_declension = self.bot.inflect_engine.plural("is", len(winners))
        winner_declension = self.bot.inflect_engine.plural(
            "winner", len(winners)
        )
        await self.ctx.embed_send(
            title = "Trivia Board",
            title_url = self.message.jump_url,
            description = (
                f"{self.bot.inflect_engine.join(winners)} {is_declension} "
                f"the {winner_declension} with `{highest_score}`!"
            )
        )

    async def stop(self):
        if self.view:
            await self.view.stop()

        self.ended.set()


class TriviaBoardSelectionView(ui.View):

    def __init__(self, match):
        super().__init__(timeout = None)
        # TODO: Timeout?

        self.match = match

        for number, category in enumerate(self.match.board, start = 1):
            if any(category["clues"].values()):
                self.category.add_option(
                    label = number, description = category["title"]
                )
                # TODO: Handle description longer than 50 characters?

        for value in self.match.VALUES:
            self.add_item(TriviaBoardValueButton(value))

    @ui.select(placeholder = "Select a category")
    async def category(self, interaction, select):
        for item in self.children:
            if isinstance(item, ui.Button):
                item.disabled = not self.match.board[int(select.values[0]) - 1]["clues"][int(item.label)]

        select.placeholder = select.values[0]

        await interaction.response.edit_message(view = self)

    async def stop(self):
        for item in self.children:
            item.disabled = True

        await self.match.message.edit(view = self)

        super().stop()


class TriviaBoardValueButton(ui.Button):

    def __init__(self, label):
        super().__init__(
            style = discord.ButtonStyle.blurple, disabled = True, label = label
        )

    async def callback(self, interaction):
        if self.view.match.turns and interaction.user != self.view.match.turn:
            await interaction.response.send_message(
                "It's not your turn", ephemeral = True
            )
            return

        category_number = int(self.view.category.values[0])
        value = int(self.label)

        if not self.view.match.board[category_number - 1]["clues"][value]:
            await interaction.response.send_message(
                "That question has already been chosen", ephemeral = True
            )
            return

        category_title = self.view.match.board[category_number - 1]["title"]
        embed = interaction.message.embeds[0]
        embed.description += (
            f"\n{interaction.user.mention} chose "
            f"`{category_title}` for `{value}`"
        )
        await interaction.response.edit_message(embed = embed, view = None)

        await self.view.match.select(category_number, value)


class TriviaBoardBuzzerView(ui.View):

    def __init__(self, match, timeout):
        super().__init__(timeout = timeout)

        self.match = match

        self.hit = False

    @ui.button(style = discord.ButtonStyle.red, label = "Buzzer")
    async def buzzer(self, interaction, button):
        if self.hit:
            return
        self.hit = True

        if interaction.user in self.match.players_answered:
            await interaction.response.send_message(
                "You already hit the buzzer", ephemeral = True
            )
            return

        await interaction.response.edit_message(view = None)
        await self.stop()

        await self.match.answer(interaction.user)

    async def on_timeout(self):
        await self.match.message.edit(view = None)
        await self.stop()

        await self.match.timeout()

    async def stop(self):
        self.buzzer.disabled = True
        await self.match.message.edit(view = self)

        super().stop()


class TriviaQuestion:

    def __init__(
        self, seconds, betting = False, override_modal_answers = False,
        react = True
    ):
        self.accepting_answers = False
        self.accepting_bets = False
        self.answered_through_modal = set()
        self.bet_message = None
        self.bets = {}
        self.betting = betting
        self.override_modal_answers = override_modal_answers
        self.react = react
        self.response = None  # Bot response to command
        self.responses = {}  # User responses to question
        self.seconds = seconds

    async def get_question(self, ctx):
        try:
            async with ctx.bot.aiohttp_session.get(
                "http://jservice.io/api/random"
            ) as resp:
                if resp.status in (500, 503):
                    await ctx.embed_reply(
                        f"{ctx.bot.error_emoji} Error: Error connecting to API"
                    )
                    return
                return (await resp.json())[0]
        except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} Error: Error connecting to API"
            )
            return

    async def start(self, ctx):
        if not (data := await self.get_question(ctx)):
            return

        tries = 1
        while (
            not data.get("question") or
            not data.get("category") or
            data["question"] == '=' or
            not data.get("answer")
        ):
            error_message = (
                ctx.bot.error_emoji +
                " Error: API response missing question/category/answer"
            )
            if tries >= 5:
                embed = self.response.embeds[0]
                embed.description += '\n' + error_message
                await self.response.edit(embed = embed)
                return
            if self.response:
                embed = self.response.embeds[0]
                embed.description += f"\n{error_message}\nRetrying..."
                await self.response.edit(embed = embed)
            else:
                self.response = await ctx.embed_reply(
                    f"{error_message}\nRetrying..."
                )
            if not (data := await self.get_question(ctx)):
                return
            tries += 1
        # Add message about making POST request to API/invalid with id?
        # Include site page to send ^?

        if self.betting:
            self.bet_message = await ctx.embed_reply(
                author_name = None,
                title = capwords(data["category"]["title"]),
                description = "Showing question " + discord.utils.format_dt(
                    datetime.datetime.now(datetime.timezone.utc) +
                    datetime.timedelta(seconds = self.seconds),
                    style = 'R'
                ),
                footer_text = None
            )

            self.accepting_bets = True
            await asyncio.sleep(self.seconds)
            self.accepting_bets = False

            embeds = self.bet_message.embeds
            embeds[0].description = None
            await self.bet_message.edit(embeds = embeds)

        embeds = [
            discord.Embed(
                description = "Showing answer " + discord.utils.format_dt(
                    datetime.datetime.now(datetime.timezone.utc) +
                    datetime.timedelta(seconds = self.seconds),
                    style = 'R'
                ),
                color = ctx.bot.bot_color
            )
        ]
        self.response = await ctx.embed_reply(
            author_name = None,
            title = capwords(data["category"]["title"]),
            description = data["question"],
            footer_text = "Air Date",
            timestamp = dateutil.parser.parse(data["airdate"]),
            view = TriviaQuestionView(self, self.seconds),
            embeds = embeds
        )

        self.accepting_answers = True
        await asyncio.sleep(self.seconds)
        self.accepting_answers = False

        embeds = self.response.embeds
        del embeds[1]
        await ctx.bot.attempt_edit_message(self.response, embeds = embeds)

        correct_players = []
        incorrect_players = []
        for player, response in self.responses.items():
            if check_answer(
                data["answer"], response,
                inflect_engine = ctx.bot.inflect_engine
            ):
                correct_players.append(player)
            else:
                incorrect_players.append(player)
        if correct_players:
            correct_players_output = ctx.bot.inflect_engine.join(
                [player.display_name for player in correct_players]
            )
            correct_players_output += f" {ctx.bot.inflect_engine.plural('was', len(correct_players))} right!"
        else:
            correct_players_output = "Nobody got it right!"
        for correct_player in correct_players:
            await ctx.bot.db.execute(
                """
                INSERT INTO trivia.users (user_id, correct, incorrect)
                VALUES ($1, 1, 0)
                ON CONFLICT (user_id) DO
                UPDATE SET correct = users.correct + 1
                """,
                correct_player.id
            )
            if points_cog := ctx.bot.get_cog("Points"):
                await points_cog.add(user = correct_player, points = 10)
        for incorrect_player in incorrect_players:
            await ctx.bot.db.execute(
                """
                INSERT INTO trivia.users (user_id, correct, incorrect)
                VALUES ($1, 0, 1)
                ON CONFLICT (user_id) DO
                UPDATE SET incorrect = users.incorrect + 1
                """,
                incorrect_player.id
            )

        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", category = MarkupResemblesLocatorWarning
            )
            answer = BeautifulSoup(
                html.unescape(data["answer"]),
                "html.parser"
            ).get_text().replace("\\'", "'")

        description = f"The answer was: `{answer}`\n\n"
        for player, response in self.responses.items():
            description += (
                f"{player.mention} answered:\n"
                f"> {response}\n\n"
            )
        await ctx.embed_reply(
            reference = self.response,
            author_name = None,
            footer_text = correct_players_output,
            description = description,
            in_response_to = False
        )

        if self.betting and self.bets:
            bets_output = []
            for player, player_bet in self.bets.items():
                if player in correct_players:
                    difference = player_bet
                    action_text = "won"
                else:
                    difference = -player_bet
                    action_text = "lost"
                if points_cog := ctx.bot.get_cog("Points"):
                    points = await points_cog.add(
                        user = player, points = difference
                    )
                else:
                    raise RuntimeError(
                        "Points cog not loaded during trivia betting"
                    )
                player_bet_point_declension = ctx.bot.inflect_engine.plural(
                    "point", player_bet
                )
                points_point_declension = ctx.bot.inflect_engine.plural(
                    "point", points
                )
                bets_output.append(
                    f"{player.mention} {action_text} "
                    f"{player_bet} {player_bet_point_declension} "
                    f"(`\N{CURRENCY SIGN}`) and now has "
                    f"{points:,} {points_point_declension} "
                    "(`\N{CURRENCY SIGN}`)"
                )
            await ctx.embed_reply(
                reference = self.bet_message,
                author_name = None,
                description = '\n'.join(bets_output),
                in_response_to = False
            )


class TriviaQuestionView(ui.View):

    def __init__(self, question, timeout):
        super().__init__(timeout = timeout)

        self.question = question

    @ui.button(style = discord.ButtonStyle.red, label = "Answer")
    async def answer(self, interaction, button):
        await interaction.response.send_modal(
            TriviaQuestionAnswerModal(self.question)
        )

    async def on_timeout(self):
        await self.question.response.edit(view = None)
        self.stop()


class TriviaQuestionAnswerModal(ui.Modal, title = "Answer"):

    answer = ui.TextInput(label = "Answer")

    def __init__(self, question):
        super().__init__()
        self.question = question

    async def on_submit(self, interaction):
        previously_answered = interaction.user in self.question.responses

        self.question.responses[interaction.user] = self.answer.value
        self.question.answered_through_modal.add(interaction.user)

        if previously_answered:
            await interaction.response.send_message(
                f"You've changed your answer to:\n> {self.answer.value}",
                ephemeral = True
            )

        else:
            await interaction.response.send_message(
                f"You've answered:\n> {self.answer.value}",
                ephemeral = True
            )

