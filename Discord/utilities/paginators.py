
import discord
from discord import ui
from discord.ext import commands


class ButtonPaginator(discord.ui.View):

    # TODO: Track pages paginated and number of paginators

    def __init__(self, ctx, source, *, initial_page = 1, selection = None):
        super().__init__(timeout = 600)

        self.ctx = ctx
        self.source = source
        self.current_page = initial_page - 1
        self.selection = selection

        self.message = None

    @discord.ui.button(
        style = discord.ButtonStyle.grey,
        emoji = (
            '\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}'
            '\N{VARIATION SELECTOR-16}'
        )
    )
    async def start_button(self, interaction, button):
        await interaction.response.defer()
        await self.show_page(interaction, 0)

    @discord.ui.button(
        style = discord.ButtonStyle.grey,
        emoji = (
            '\N{LEFTWARDS BLACK ARROW}'
            '\N{VARIATION SELECTOR-16}'
        )
    )
    async def previous_button(self, interaction, button):
        await interaction.response.defer()
        await self.show_page(interaction, self.current_page - 1)

    @discord.ui.button(style = discord.ButtonStyle.blurple)
    async def current_button(self, interaction, button):
        await interaction.response.send_modal(
            ButtonPaginatorPageSelectionModal(self)
        )

    @discord.ui.button(
        style = discord.ButtonStyle.grey,
        emoji = (
            '\N{BLACK RIGHTWARDS ARROW}'
            '\N{VARIATION SELECTOR-16}'
        )
    )
    async def next_button(self, interaction, button):
        await interaction.response.defer()
        await self.show_page(interaction, self.current_page + 1)

    @discord.ui.button(
        style = discord.ButtonStyle.grey,
        emoji = (
            '\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}'
            '\N{VARIATION SELECTOR-16}'
        )
    )
    async def end_button(self, interaction, button):
        await interaction.response.defer()
        await self.show_page(interaction, self.source.get_max_pages() - 1)

    async def interaction_check(self, interaction):
        if interaction.user.id not in (
            self.ctx.author.id, self.ctx.bot.owner_id
        ):
            await interaction.response.send_message(
                "You didn't invoke this command.",
                ephemeral = True
            )
            return False
        return True

    @discord.ui.select()
    async def select_menu(self, interaction, select):
        await interaction.response.defer()
        selected = int(select.values[0])
        await self.show_page(interaction, selected)

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
            if self.selection:
                options = [
                    discord.SelectOption(
                        label = self.selection[page_number],
                        value = page_number,
                        default = (page_number == self.current_page)
                    )
                    for page_number in range(self.source.get_max_pages())
                ]
                self.select_menu.options = options[:25]
            else:
                self.remove_item(self.select_menu)
        else:
            self.clear_items()

        self.message = await self.ctx.send(**kwargs, view = self)
        if not self.ctx.interaction:
            await self.ctx.bot.attempt_delete_message(self.ctx.message)

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
        if self.selection:
            for option in self.select_menu.options:
                option.default = (int(option.value) == self.current_page)

        await interaction.edit_original_response(**kwargs, view = self)

    async def on_timeout(self):
        await self.stop()

    async def stop(self, interaction = None):
        self.start_button.disabled = True
        self.previous_button.disabled = True
        self.next_button.disabled = True
        self.end_button.disabled = True
        self.select_menu.disabled = True

        if interaction:
            await interaction.response.edit_message(view = self)
        elif self.message:
            await self.ctx.bot.attempt_edit_message(self.message, view = self)

        super().stop()


class ButtonPaginatorPageSelectionModal(ui.Modal):

    def __init__(self, button_paginator: ButtonPaginator):
        super().__init__(title = "Page Selection")
        self.button_paginator = button_paginator

    number = ui.TextInput(label = "Page Number")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            page_number = int(self.number.value) - 1
        except ValueError:
            await interaction.response.send_message(
                "That is not a valid number.", ephemeral = True
            )
            return

        await interaction.response.defer()

        page_number = max(page_number, 0)
        page_number = min(
            page_number, self.button_paginator.source.get_max_pages() - 1
        )
        await self.button_paginator.show_page(interaction, page_number)


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

