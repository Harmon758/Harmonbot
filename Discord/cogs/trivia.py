
import discord
from discord import ui
from discord.ext import commands

import asyncio
import datetime
import html
import random
import sys
from typing import Optional

import aiohttp
from bs4 import BeautifulSoup
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
        self.active_jeopardy = {}

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

    async def cog_check(self, ctx):
        return await checks.not_forbidden().predicate(ctx)

    max_concurrency = commands.MaxConcurrency(1, per = commands.BucketType.guild, wait = False)

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MaxConcurrencyReached):
            if trivia_question := self.trivia_questions.get(ctx.guild.id):
                description = "There's already an active trivia question here"
                if trivia_question.response:
                    description = f"[{description}]({trivia_question.response.jump_url})"
                elif (
                    channel_id := trivia_question.channel_id
                ) and ctx.channel.id != channel_id:
                    channel = ctx.guild.get_channel_or_thread(channel_id)
                    description = (
                        "There's already an active trivia question in " +
                        channel.mention
                    )
                await ctx.embed_reply(description)
                return
            elif ctx.guild.id in self.active_jeopardy:
                channel_id = self.active_jeopardy[ctx.guild.id].channel_id
                if ctx.channel.id == channel_id:
                    await ctx.embed_reply(
                        f"{ctx.bot.error_emoji} Error: There is already an ongoing game of jeopardy here"
                    )
                else:
                    channel = ctx.guild.get_channel_or_thread(channel_id)
                    await ctx.embed_reply(
                        f"{ctx.bot.error_emoji} Error: There is already an ongoing game of jeopardy in {channel.mention}"
                    )
            else:
                raise RuntimeError(
                    "Trivia max concurrency reached, "
                    "but neither active trivia nor jeopardy found."
                )

    @commands.hybrid_group(
        case_insensitive = True,
        fallback = "question",
        max_concurrency = max_concurrency
    )
    async def trivia(
        self, ctx, override_modal_answers: Optional[bool] = False,
        seconds: commands.Range[int, 1, 60] = 15
    ):
        """
        Trivia question
        Only your last answer is accepted
        Answers prepended with ! or > are ignored
        Questions are taken from Jeopardy!

        Parameters
        ----------
        override_modal_answers
            Whether or not to override modal answers with message answers
            (default is False)
        seconds
            How long to accept answers for, in seconds
            (1 - 60, default is 15)
        """
        await ctx.defer()
        try:
            self.trivia_questions[ctx.guild.id] = TriviaQuestion(
                seconds, override_modal_answers = override_modal_answers
            )
            await self.trivia_questions[ctx.guild.id].start(ctx)
        finally:
            del self.trivia_questions[ctx.guild.id]

    @commands.Cog.listener("on_message")
    async def on_trivia_question_message(self, message):
        if not message.guild or not (
            trivia_question := self.trivia_questions.get(message.guild.id)
        ):
            return
        if message.channel.id != trivia_question.channel_id:
            return
        if message.author.id == self.bot.user.id:
            return
        if trivia_question.bet_countdown and message.content.isdigit():
            ctx = await self.bot.get_context(message)
            money = await self.bot.db.fetchval(
                "SELECT money FROM trivia.users WHERE user_id = $1",
                message.author.id
            )
            if not money:
                money = await self.bot.db.fetchval(
                    """
                    INSERT INTO trivia.users (user_id, correct, incorrect, money)
                    VALUES ($1, 0, 0, 100000)
                    RETURNING money
                    """,
                    message.author.id
                )
            if int(message.content) <= money:
                trivia_question.bets[message.author] = int(message.content)
                await self.bot.attempt_delete_message(message)
            else:
                await ctx.embed_reply("You don't have that much money to bet!")
        elif trivia_question.question_countdown:
            if message.content.startswith(('!', '>')):
                return
            if (
                not trivia_question.override_modal_answers and
                message.author in trivia_question.answered_through_modal
            ):
                return
            trivia_question.responses[message.author] = message.content

    @trivia.command(
        name = "bet",
        max_concurrency = max_concurrency, with_app_command = False
    )
    async def trivia_bet(self, ctx):
        '''
        Trivia with betting
        The category is shown first during the betting phase
        Enter any amount under or equal to the money you have to bet
        Currently, you start with $100,000
        '''
        try:
            self.trivia_questions[ctx.guild.id] = TriviaQuestion(15)
            await self.trivia_questions[ctx.guild.id].start(ctx, bet = True)
        finally:
            del self.trivia_questions[ctx.guild.id]

    @trivia.command(aliases = ["jeopardy"])
    async def board(
        self, ctx, buzzer: bool = False,
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
        if match := self.trivia_boards.get(ctx.channel.id):
            await ctx.embed_reply(
                f"[There's already a trivia board in progress here]({match.message.jump_url})"
            )
            return

        if not (
            trivia_board := TriviaBoard(
                seconds, buzzer = buzzer, turns = turns
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
            await trivia_board.answer(message.author, message.content)
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
            f"\n{message.author.mention} chose `{category_title}` for `{value}`"
        )
        await trivia_board.message.edit(embed = embed, view = None)
        await trivia_board.select(category_number, value)

    # TODO: trivia board stats

    @trivia.command(name = "money", aliases = ["cash"], with_app_command = False)
    async def trivia_money(self, ctx):
        '''Trivia money'''
        money = await ctx.bot.db.fetchval("SELECT money FROM trivia.users WHERE user_id = $1", ctx.author.id)
        if not money:
            return await ctx.embed_reply("You have not played any trivia yet")
        await ctx.embed_reply(f"You have ${money:,}")

    @trivia.command(aliases = ["level", "points", "rank", "score", "stats"])
    async def statistics(self, ctx):
        """Trivia statistics"""
        await ctx.defer()
        record = await ctx.bot.db.fetchrow(
            "SELECT correct, incorrect FROM trivia.users WHERE user_id = $1",
            ctx.author.id
        )
        if not record:
            await ctx.embed_reply("You have not played any trivia yet")
            return
        total = record["correct"] + record["incorrect"]
        correct_percentage = record["correct"] / total * 100
        await ctx.embed_reply(
            f"You have answered {record['correct']:,} / {total:,} "
            f"({correct_percentage:.2f}%) trivia questions correctly"
        )

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
                    "SELECT * FROM trivia.users ORDER BY correct DESC LIMIT $1",
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
                        f"{record['correct']:,} correct ({correct_percentage:.2f}%)\n"
                        f"{total:,} answered"
                    ))
        await ctx.embed_reply(title = f"Trivia Top {number}", fields = fields)

    @commands.command()
    async def jeopardy(
        self, ctx, buzzer: bool = False,
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
                command, buzzer = buzzer, seconds = seconds, turns = turns
            )
        else:
            raise RuntimeError(
                "trivia board command not found when jeopardy command invoked"
            )


class TriviaBoard:

    VALUES = (200, 400, 600, 800, 1000)

    def __init__(self, seconds, buzzer = True, turns = True):
        self.awaiting_answer = False  # This is not used if buzzer == True
        self.awaiting_selection = False  # TODO: Selection timeout?
        self.board = []
        self.board_lines = []
        # Whether or not to have a buzzer
        # If not, allows everyone to answer at once
        self.buzzer = buzzer
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
        await self.message.edit(
            embed = embed, view = TriviaBoardSelectionView(self)
        )
        self.awaiting_selection = True
        return True

    async def answer(self, player, answer = None):
        if self.buzzer:
            self.answered.append(player)
            self.answerer = player

            second_declension = self.bot.inflect_engine.plural(
                "second", self.seconds
            )
            answer_prompt_message = await self.ctx.embed_send(
                title = "Trivia Board",
                title_url = self.message.jump_url,
                description = (
                    f"{player.mention} hit the buzzer\n"
                    f"{player.mention}: What's your answer?"
                ),
                footer_text = f"{self.seconds} {second_declension} to answer"
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
                self.message = await self.ctx.send(
                    embed = self.message.embeds[0],
                    view = TriviaBoardBuzzerView(self, self.seconds)
                )
                return

            answer = message.content

        if check_answer(
            self.correct_answer, answer,
            inflect_engine = self.bot.inflect_engine
        ):
            # Correct answer
            self.awaiting_answer = False

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
                view = TriviaBoardSelectionView(self)
            else:
                view = None

            self.message = await self.ctx.embed_send(
                title = "Trivia Board",
                title_url = (
                    answer_prompt_message.jump_url if self.buzzer
                    else self.message.jump_url
                ),
                description = response,
                view = view
            )
            self.awaiting_selection = True

            if not clues_left:
                await self.send_winner()
                self.ended.set()
        elif self.buzzer:
            # Incorrect answer
            self.scores[player] = self.scores.get(player, 0) - int(self.value)
            await self.ctx.embed_send(
                title = "Trivia Board",
                title_url = answer_prompt_message.jump_url,
                description = (
                    f"{player.mention} was incorrect and lost `{self.value}`\n"
                    f"{player.mention} now has `{self.scores[player]}`"
                )
            )
            self.message = await self.ctx.send(
                embed = self.message.embeds[0],
                view = TriviaBoardBuzzerView(self, self.seconds)
            )

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
        self.answered = []  # This is only used if buzzer == True

        action = "hit the buzzer" if self.buzzer else "answer"
        second_declension = self.bot.inflect_engine.plural(
            "second", self.seconds
        )
        self.message = await self.ctx.embed_send(
            title = (
                f"{self.board[category_number - 1]['title']}\n(for {value})"
            ),
            title_url = self.message.jump_url,
            description = clue["question"],
            footer_text = (
                f"{self.seconds} {second_declension} to {action} | Air Date"
            ),
            timestamp = dateutil.parser.parse(clue["airdate"]),
            view = (
                TriviaBoardBuzzerView(self, self.seconds) if self.buzzer
                else None
            )
        )

        if not self.buzzer:
            self.awaiting_answer = True
            countdown = self.seconds
            message = self.message
            embed = message.embeds[0]
            while countdown:
                await asyncio.sleep(1)
                if not self.awaiting_answer:
                    return
                countdown -= 1
                second_declension = self.bot.inflect_engine.plural(
                    "second", countdown
                )
                embed.set_footer(
                    text = f"{countdown} {second_declension} left to {action} | Air Date"
                )
                await message.edit(embed = embed)
            self.awaiting_answer = False
            await self.timeout()

    async def timeout(self):
        embed = self.message.embeds[0]
        embed.set_footer(text = "Time's up! | Air Date")
        await self.message.edit(embed = embed)

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
            view = TriviaBoardSelectionView(self)
        else:
            view = None

        self.message = await self.ctx.embed_send(
            title = "Trivia Board",
            title_url = self.message.jump_url,
            description = response,
            view = view
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
        await self.ctx.embed_send(
            title = "Trivia Board",
            title_url = self.message.jump_url,
            description = (
                f"{self.bot.inflect_engine.join(winners)} {self.bot.inflect_engine.plural('is', len(winners))} "
                f"the {self.bot.inflect_engine.plural('winner', len(winners))} with `{highest_score}`!"
            )
        )


class TriviaBoardSelectionView(ui.View):

    def __init__(self, match):
        super().__init__(timeout = None)
        # TODO: Timeout?

        self.match = match

        for number, category in enumerate(self.match.board, start = 1):
            if any(category["clues"].values()):
                self.category.add_option(label = number, description = category["title"])
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
            f"\n{interaction.user.mention} chose `{category_title}` for `{value}`"
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

        if interaction.user in self.match.answered:
            await interaction.response.send_message(
                "You already hit the buzzer", ephemeral = True
            )
            return

        await interaction.response.edit_message(view = None)
        self.stop()

        await self.match.answer(interaction.user)

    async def on_timeout(self):
        await self.match.message.edit(view = None)
        self.stop()

        await self.match.timeout()


class TriviaQuestion:

    def __init__(self, seconds, override_modal_answers = False):
        self.answered_through_modal = set()
        self.bet_countdown = 0
        self.bets = {}
        self.channel_id = None
        self.override_modal_answers = override_modal_answers
        self.question_countdown = 0
        self.response = None  # Bot response to command
        self.responses = {}  # User responses to question
        self.seconds = seconds
        self.wait_time = 15

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

    async def start(self, ctx, bet = False):
        self.channel_id = ctx.channel.id

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

        if bet:
            self.bet_countdown = self.wait_time
            second_declension = ctx.bot.inflect_engine.plural(
                "second", self.bet_countdown
            )
            bet_message = await ctx.embed_reply(
                author_name = None,
                title = capwords(data["category"]["title"]),
                footer_text = (
                    f"{self.bet_countdown} {second_declension} left to bet"
                )
            )
            embed = bet_message.embeds[0]
            while self.bet_countdown:
                await asyncio.sleep(1)
                self.bet_countdown -= 1
                embed.description = '\n'.join(
                    f"{player.mention} has bet ${bet}"
                    for player, bet in self.bets.items()
                )
                second_declension = ctx.bot.inflect_engine.plural(
                    "second", self.bet_countdown
                )
                embed.set_footer(
                    text = f"{self.bet_countdown} {second_declension} left to bet"
                )
                await bet_message.edit(embed = embed)
            embed.set_footer(text = "Betting is over")
            await bet_message.edit(embed = embed)

        self.question_countdown = self.seconds
        second_declension = ctx.bot.inflect_engine.plural(
            "second", self.question_countdown
        )
        self.response = await ctx.embed_reply(
            author_name = None,
            title = capwords(data["category"]["title"]),
            description = data["question"],
            footer_text = f"{self.question_countdown} {second_declension} left to answer | Air Date",
            timestamp = dateutil.parser.parse(data["airdate"]),
            view = TriviaQuestionView(self, self.seconds)
        )
        embed = self.response.embeds[0]

        while self.question_countdown:
            await asyncio.sleep(1)
            self.question_countdown -= 1
            embed.description = data["question"]
            if responses := self.responses:
                users = ctx.bot.inflect_engine.join(
                    [user.mention for user in responses]
                )
                has_or_have = ctx.bot.inflect_engine.plural(
                    'has', len(responses)
                )
                embed.description += f"\n\n{users} {has_or_have} answered"
            second_declension = ctx.bot.inflect_engine.plural(
                "second", self.question_countdown
            )
            embed.set_footer(
                text = f"{self.question_countdown} {second_declension} left to answer | Air Date"
            )
            try:
                await self.response.edit(embed = embed)
            except (aiohttp.ClientConnectionError, discord.NotFound):
                continue

        embed.set_footer(text = "Time's up! | Air Date")
        try:
            await self.response.edit(embed = embed)
        except discord.NotFound:
            pass

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
                INSERT INTO trivia.users (user_id, correct, incorrect, money)
                VALUES ($1, 1, 0, 100000)
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
                INSERT INTO trivia.users (user_id, correct, incorrect, money)
                VALUES ($1, 0, 1, 100000)
                ON CONFLICT (user_id) DO
                UPDATE SET incorrect = users.incorrect + 1
                """,
                incorrect_player.id
            )

        answer = BeautifulSoup(
            html.unescape(data["answer"]), "html.parser"
        ).get_text().replace("\\'", "'")
        description = f"The answer was: `{answer}`\n\n"
        for player, response in self.responses.items():
            description += (
                f"{player.mention} answered:\n"
                f"> {response}\n\n"
            )
        await ctx.embed_reply(
            author_name = None,
            footer_text = correct_players_output,
            description = description,
            in_response_to = False
        )

        if bet and self.bets:
            bets_output = []
            for player, player_bet in self.bets.items():
                if player in correct_players:
                    difference = player_bet
                    action_text = "won"
                else:
                    difference = -player_bet
                    action_text = "lost"
                money = await ctx.bot.db.fetchval(
                    """
                    UPDATE trivia.users
                    SET money = money + $2
                    WHERE user_id = $1
                    RETURNING money
                    """,
                    player.id, difference
                )
                bets_output.append(
                    f"{player.mention} {action_text} ${player_bet:,} and now has ${money:,}"
                )
            await ctx.embed_reply('\n'.join(bets_output), author_name = None)


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

