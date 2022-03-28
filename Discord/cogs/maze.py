
import discord
from discord import app_commands
from discord.ext import commands

import asyncio
from enum import IntEnum
import io
import random

from utilities import checks


async def setup(bot):
    await bot.add_cog(MazeCog())


class Direction(IntEnum):
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3

    @property
    def reverse(self):
        return {
            self.UP: self.DOWN,
            self.LEFT: self.RIGHT,
            self.DOWN: self.UP,
            self.RIGHT: self.LEFT
        }[self]

    @property
    def vector(self):
        # (-y, x) to match vertical, horizontal / row, column
        return {
            self.UP: (-1, 0),
            self.RIGHT: (0, 1),
            self.DOWN: (1, 0),
            self.LEFT: (0, -1)
        }[self]


class Maze:

    def __init__(self, rows, columns, random_start = False, random_end = False):
        self.rows = min(max(2, rows), 100)
        self.columns = min(max(2, columns), 100)
        self.move_counter = 0

        # Generate connections
        self.connections = [[[False] * 4 for column in range(self.columns)] for row in range(self.rows)]
        visited = [[False] * self.columns for row in range(self.rows)]
        to_visit = [(random.randint(0, self.rows - 1), random.randint(0, self.columns - 1))]
        while to_visit:
            row, column = to_visit[-1]
            visited[row][column] = True
            for direction in random.sample(tuple(Direction), 4):
                vertical, horizontal = direction.vector
                new_row, new_column = row + vertical, column + horizontal
                if not (0 <= new_row < self.rows and 0 <= new_column < self.columns):
                    continue
                if visited[new_row][new_column]:
                    continue
                self.connections[row][column][direction] = True
                self.connections[new_row][new_column][direction.reverse] = True
                to_visit.append((new_row, new_column))
                break
            else:
                to_visit.pop()

        # self.visited = [[False] * self.columns for row in range(self.rows)]
        if random_start:
            self.row = random.randint(0, self.rows - 1)
            self.column = random.randint(0, self.columns - 1)
        else:
            self.row = 0
            self.column = 0
        # self.visited[self.row][self.column] = True
        if random_end:
            self.end_row = random.randint(0, self.rows - 1)
            self.end_column = random.randint(0, self.columns - 1)
        else:
            self.end_row = self.rows - 1
            self.end_column = self.columns - 1

        self.string = ""
        for row in range(self.rows):
            for column in range(self.columns):
                if self.connections[row][column][Direction.UP]:
                    self.string += "+   "
                else:
                    self.string += "+---"
            self.string += "+\n"
            for column in range(self.columns):
                if self.connections[row][column][Direction.LEFT]:
                    self.string += "    "
                else:
                    self.string += "|   "
            self.string += "|\n"
        self.string += "+---" * self.columns + "+\n"
        self.row_strings = self.string.split('\n')

        self.visible = [None] * (2 * self.rows + 1)
        self.visible[::2] = ["+---" * self.columns + '+'] * (self.rows + 1)
        self.visible[1::2] = ["| X " * self.columns + '|'] * self.rows
        self.update_visible()
        row_offset = 2 * self.end_row + 1
        column_offset = 4 * self.end_column + 2
        self.visible[row_offset] = self.visible[row_offset][:column_offset] + 'E' + self.visible[row_offset][column_offset + 1:]

    def __repr__(self):
        return self.string
        # Tuple of connection directions for each cell:
        # return str(
        #     tuple(
        #         tuple(
        #             tuple(
        #                 filter(
        #                     None, (
        #                         direction.name if self.connections[row][column][direction] else None
        #                         for direction in Direction
        #                     )
        #                 )
        #             ) for column in range(self.columns)
        #         ) for row in range(self.rows)
        #     )
        # )
        # Grid of first letter of connection directions:
        # return (
        #     '\n'.join(
        #         "".join(
        #             "".join(
        #                 direction.name[0] if self.connections[row][column][direction] else ""
        #                 for direction in Direction
        #             ).ljust(5, ' ') for column in range(self.columns)
        #         ) for row in range(self.rows)
        #     )
        # )

    def __str__(self):
        if self.rows <= 10 and self.columns <= 10:
            return '\n'.join(self.visible)
        start_row = self.row - self.row % 10
        start_column = self.column - self.column % 10
        visible = self.visible[2 * start_row:2 * start_row + 21]
        for row_number, row in enumerate(visible):
            visible[row_number] = row[4 * start_column:4 * start_column + 41]
        return '\n'.join(visible)

    def update_visible(self):
        row_offset = 2 * self.row
        column_offset = 4 * self.column
        for row in range(row_offset, row_offset + 3):
            self.visible[row] = self.visible[row][:column_offset] + self.row_strings[row][column_offset:column_offset + 5] + self.visible[row][column_offset + 5:]
        row_offset += 1
        column_offset += 2
        self.visible[row_offset] = self.visible[row_offset][:column_offset] + 'I' + self.visible[row_offset][column_offset + 1:]

    def move(self, direction):
        '''Move inside the maze'''
        if not isinstance(direction, Direction) or not self.connections[self.row][self.column][direction]:
            return False

        row_offset = 2 * self.row + 1
        column_offset = 4 * self.column + 2
        self.visible[row_offset] = self.visible[row_offset][:column_offset] + ' ' + self.visible[row_offset][column_offset + 1:]
        if direction is Direction.UP:
            self.row -= 1
        elif direction is Direction.RIGHT:
            self.column += 1
        elif direction is direction.DOWN:
            self.row += 1
        elif direction is direction.LEFT:
            self.column -= 1

        # self.visited[self.row][self.column] = True
        self.move_counter += 1
        self.update_visible()
        return True

    @property
    def reached_end(self):
        return self.row == self.end_row and self.column == self.end_column


class MazeCog(commands.Cog, name = "Maze"):

    def __init__(self):
        self.mazes = {}
        self.tasks = []
        self.move_mapping = {
            'w': Direction.UP,
            'a': Direction.LEFT,
            's': Direction.DOWN,
            'd': Direction.RIGHT, 
            "up": Direction.UP,
            "left": Direction.LEFT,
            "down": Direction.DOWN,
            "right": Direction.RIGHT
        }

    async def cog_check(self, ctx):
        return await checks.not_forbidden().predicate(ctx)

    def cog_unload(self):
        # TODO: Persistence - store running mazes and add way to continue previous ones
        for task in self.tasks:
            task.cancel()

    @commands.group(invoke_without_command = True, case_insensitive = True)
    async def maze(self, ctx, height: int = 5, width: int = 5, random_start: bool = False, random_end: bool = False):
        '''
        Maze game
        height: 2 - 100
        width: 2 - 100
        [w, a, s, d] or [up, left, down, right] to move
        '''
        # TODO: Add option to restrict to command invoker
        if maze := self.mazes.get(ctx.channel.id):
            return await ctx.embed_reply(ctx.bot.CODE_BLOCK.format(str(maze)))
        self.mazes[ctx.channel.id] = maze = Maze(height, width, random_start = random_start, random_end = random_end)
        message = await ctx.embed_reply(ctx.bot.CODE_BLOCK.format(str(maze)), 
                                        footer_text = f"Your current position: {maze.column + 1}, {maze.row + 1}")
        reached_end = False
        while not reached_end:
            task = ctx.bot.loop.create_task(ctx.bot.wait_for(
                "message", 
                check = lambda message: 
                    message.channel == ctx.channel and message.content.lower() in self.move_mapping.keys()
                    # author = ctx.author
            ), name = "Wait for maze move message")
            self.tasks.append(task)
            try:
                await task
            except asyncio.CancelledError:
                break
            else:
                move = task.result()
            moved = maze.move(self.move_mapping[move.content.lower()])
            response = ctx.bot.CODE_BLOCK.format(str(maze))
            if not moved:
                response += "\n:no_entry: You can't go that way"
            elif (reached_end := maze.reached_end):
                response += f"\nCongratulations! You reached the end of the maze in {maze.move_counter} moves"
            new_message = await ctx.embed_reply(response, 
                                                footer_text = f"Your current position: {maze.column + 1}, {maze.row + 1}")
            ctx.bot.loop.create_task(ctx.bot.attempt_delete_message(move), name = "Maze move message deletion")
            ctx.bot.loop.create_task(ctx.bot.attempt_delete_message(message), name = "Previous maze message deletion")
            message = new_message
        del self.mazes[ctx.channel.id]

    @maze.command(aliases = ["print"])
    async def file(self, ctx):
        '''Text file of the current maze game'''
        if maze := self.mazes.get(ctx.channel.id):
            await ctx.reply(
                "Your maze is attached",
                file = discord.File(
                    io.BytesIO(('\n'.join(maze.visible)).encode()),
                    filename = "maze.txt"
                )
            )
        else:
            await ctx.embed_reply(
                ":no_entry: There's no maze game currently going on"
            )

    @app_commands.command(name = "maze")
    @app_commands.describe(height = "Maze height")
    @app_commands.describe(width = "Maze width")
    @app_commands.describe(
        random_start = "Whether to start at a random place in the Maze"
    )
    @app_commands.describe(
        random_end = "Whether to end at a random place in the Maze"
    )
    async def maze_slash(
        self, interaction, height: app_commands.Range[int, 2, 100] = 5,
        width: app_commands.Range[int, 2, 100] = 5, random_start: bool = False,
        random_end: bool = False
    ):
        """Maze Game"""
        maze = Maze(height, width, random_start, random_end)
        embed = discord.Embed(
            color = interaction.client.bot_color,
            description = interaction.client.CODE_BLOCK.format(str(maze))
        ).set_footer(
            text = f"Your current position: {maze.column + 1}, {maze.row + 1}"
        )
        view = MazeView(maze, interaction.user)
        await interaction.response.send_message(embed = embed, view = view)

        message = await interaction.original_message()
        # Fetch Message, as InteractionMessage token expires after 15 min.
        view.message = await message.fetch()
        interaction.client.views.append(view)

    # TODO: maze stats


class MazeView(discord.ui.View):

    def __init__(self, maze, user):
        super().__init__(timeout = None)
        self.arrows = {
            '\N{UPWARDS BLACK ARROW}': Direction.UP,
            '\N{LEFTWARDS BLACK ARROW}': Direction.LEFT,
            '\N{BLACK RIGHTWARDS ARROW}': Direction.RIGHT,
            '\N{DOWNWARDS BLACK ARROW}': Direction.DOWN
        }

        self.maze = maze
        self.user = user

        self.message = None

        # First row
        self.add_blank_disabled_button()
        self.add_item(MazeDirectionButton(emoji = '\N{UPWARDS BLACK ARROW}'))
        self.add_blank_disabled_button()
        self.add_blank_disabled_button()
        self.add_item(MazeFileButton())
        # Second row
        self.add_item(MazeDirectionButton(emoji = '\N{LEFTWARDS BLACK ARROW}'))
        self.add_blank_disabled_button()
        self.add_item(MazeDirectionButton(
            emoji = '\N{BLACK RIGHTWARDS ARROW}'
        ))
        self.add_blank_disabled_button()
        self.add_blank_disabled_button()
        # Third row
        self.add_blank_disabled_button()
        self.add_item(MazeDirectionButton(emoji = '\N{DOWNWARDS BLACK ARROW}'))
        self.add_blank_disabled_button()
        self.add_blank_disabled_button()
        self.add_blank_disabled_button()

    def add_blank_disabled_button(self):
        self.add_item(discord.ui.Button(label = ' ', disabled = True))

    async def interaction_check(self, interaction):
        if interaction.user.id not in (self.user.id, interaction.client.owner_id):
            await interaction.response.send_message(
                "This isn't your maze.", ephemeral = True
            )
            return False
        return True

    async def stop(self):
        self.children[1].disabled = True
        self.children[4].disabled = True
        self.children[5].disabled = True
        self.children[7].disabled = True
        self.children[11].disabled = True

        if self.message:
            try:
                await self.message.edit(view = self)
            except discord.HTTPException as e:
                if e.code != 50083:  # 50083 == Thread is archived
                    raise

        super().stop()

class MazeDirectionButton(discord.ui.Button):

    def __init__(self, emoji):
        super().__init__(emoji = emoji)
        self.emoji = emoji

    async def callback(self, interaction):
        embed = interaction.message.embeds[0]
        if not self.view.maze.move(self.view.arrows[str(self.emoji)]):
            await interaction.response.send_message(
                f"{interaction.client.error_emoji} You can't go that way",
                ephemeral = True
            )
        elif self.view.maze.reached_end:
            embed.description = (
                interaction.client.CODE_BLOCK.format(str(self.view.maze)) +
                "\nCongratulations! You reached the end of the maze in "
                f"{self.view.maze.move_counter} moves"
            )
            embed.remove_footer()
            await interaction.response.edit_message(embed = embed, view = None)
        else:
            embed.description = interaction.client.CODE_BLOCK.format(
                str(self.view.maze)
            )
            embed.set_footer(text = (
                "Your current position: "
                f"{self.view.maze.column + 1}, {self.view.maze.row + 1}"
            ))
            await interaction.response.edit_message(embed = embed)

class MazeFileButton(discord.ui.Button):

    def __init__(self):
        super().__init__(emoji = '\N{PRINTER}')

    async def callback(self, interaction):
        await interaction.response.send_message(
            "Your maze is attached",
            file = discord.File(
                io.BytesIO(('\n'.join(self.view.maze.visible)).encode()),
                filename = "maze.txt"
            )
    )

