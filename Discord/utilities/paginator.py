
import discord
from discord.ext import commands


class ButtonPaginator(discord.ui.View):

    # TODO: Track pages paginated and number of paginators

    def __init__(self, ctx_or_interaction, source, initial_page = 1):
        super().__init__(timeout = None)

        self.ctx = self.ctx_or_interaction = ctx_or_interaction
        self.source = source
        self.current_page = initial_page - 1

        if isinstance(ctx_or_interaction, commands.Context):
            self.bot = ctx_or_interaction.bot
            self.user = ctx_or_interaction.author
        elif isinstance(ctx_or_interaction, discord.Interaction):
            self.bot = ctx_or_interaction.client
            self.user = ctx_or_interaction.user
        else:
            raise RuntimeError(
                "ButtonPaginator passed neither Context nor Interaction"
            )

        self.message = None

    @discord.ui.button(
        style = discord.ButtonStyle.grey,
        emoji = (
            '\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}'
            '\N{VARIATION SELECTOR-16}'
        )
    )
    async def start_button(self, interaction, button):
        await self.show_page(interaction, 0)

    @discord.ui.button(
        style = discord.ButtonStyle.grey,
        emoji = (
            '\N{LEFTWARDS BLACK ARROW}'
            '\N{VARIATION SELECTOR-16}'
        )
    )
    async def previous_button(self, interaction, button):
        await self.show_page(interaction, self.current_page - 1)

    @discord.ui.button(
        style = discord.ButtonStyle.blurple,
        disabled = True
    )
    async def current_button(self, interaction, button):
        return

    @discord.ui.button(
        style = discord.ButtonStyle.grey,
        emoji = (
            '\N{BLACK RIGHTWARDS ARROW}'
            '\N{VARIATION SELECTOR-16}'
        )
    )
    async def next_button(self, interaction, button):
        await self.show_page(interaction, self.current_page + 1)

    @discord.ui.button(
        style = discord.ButtonStyle.grey,
        emoji = (
            '\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}'
            '\N{VARIATION SELECTOR-16}'
        )
    )
    async def end_button(self, interaction, button):
        await self.show_page(interaction, self.source.get_max_pages() - 1)

    @discord.ui.button(
        style = discord.ButtonStyle.red,
        emoji = '\N{OCTAGONAL SIGN}'
    )
    async def stop_button(self, interaction, button):
        await self.stop(interaction = interaction)

    async def interaction_check(self, interaction):
        if interaction.user.id not in (self.user.id, self.bot.owner_id):
            await interaction.response.send_message(
                "You didn't invoke this command.",
                ephemeral = True
            )
            return False
        return True

    async def start(self):
        # TODO: Check embed permissions
        await self.source.prepare()

        if self.current_page <= 0:
            self.current_page = 0
            self.start_button.disabled = True
            self.previous_button.disabled = True
        elif self.current_page >= (
            max_page := self.source.get_max_pages() - 1
        ):
            self.current_page = max_page
            self.end_button.disabled = True
            self.next_button.disabled = True

        page = await self.source.get_page(self.current_page)
        kwargs = await self.source.format_page(self, page)

        if self.source.is_paginating():
            self.current_button.label = self.current_page + 1
            self.end_button.label = self.source.get_max_pages()
        else:
            self.clear_items()

        if isinstance(self.ctx_or_interaction, commands.Context):
            self.message = await self.ctx_or_interaction.send(
                **kwargs, view = self
            )
            await self.bot.attempt_delete_message(
                self.ctx_or_interaction.message
            )
        elif isinstance(self.ctx_or_interaction, discord.Interaction):
            await self.ctx_or_interaction.response.send_message(
                **kwargs, view = self
            )
            message = await self.ctx_or_interaction.original_message()
            self.message = await message.fetch()
        else:
            raise RuntimeError(
                "ButtonPaginator using neither Context nor Interaction"
            )

    async def show_page(self, interaction, page_number):
        self.current_page = page_number
        page = await self.source.get_page(page_number)
        kwargs = await self.source.format_page(self, page)

        self.start_button.disabled = self.previous_button.disabled = (
            page_number == 0
        )
        self.current_button.label = page_number + 1
        self.next_button.disabled = self.end_button.disabled = (
            page_number + 1 == self.source.get_max_pages()
        )

        await interaction.response.edit_message(**kwargs, view = self)

    async def stop(self, interaction = None):
        self.start_button.disabled = True
        self.previous_button.disabled = True
        self.next_button.disabled = True
        self.end_button.disabled = True
        self.remove_item(self.stop_button)

        if interaction:
            await interaction.response.edit_message(view = self)
        elif self.message:
            await self.bot.attempt_edit_message(self.message, view = self)

        super().stop()


class Paginator(commands.Paginator):

    def __init__(self, seperator = "\n", prefix='```', suffix='```', max_size=2000):
        super().__init__(prefix, suffix, max_size)
        self.seperator = seperator
        self._current_page = []

    def add_section(self, section='', *, empty=False):
        if len(section) > self.max_size - len(self.prefix) - 2:
            raise RuntimeError('Section exceeds maximum page size %s' % (self.max_size - len(self.prefix) - 2))

        if self._count + len(section) + len(self.seperator) > self.max_size:
            self.close_page()

        self._count += len(section) + len(self.seperator)
        self._current_page.append(section)

        if empty:
            self._current_page.append('')
            self._count += len(self.seperator)

    def close_page(self):
        self._pages.append(self.prefix + "\n" + self.seperator.join(self._current_page) + "\n" + self.suffix)
        self._current_page = []
        self._count = len(self.prefix) + len(self.seperator)

    @property
    def pages(self):
        if len(self._current_page) > 0:
            self.close_page()
        return self._pages

