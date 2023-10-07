
import discord

from units.wikis import get_article_beginning


class WikiArticlesView(discord.ui.View):

    def __init__(self, articles):
        super().__init__(timeout = 600)

        self.articles = articles

        for number, article in enumerate(articles):
            self.article.add_option(label = article.title, value = number)

        self.article.options[0].default = True

    async def initial_embed(self, ctx):
        article = self.articles[0]

        if article.extract:
            description = article.extract
        else:
            description = await get_article_beginning(
                article,
                aiohttp_session = ctx.bot.aiohttp_session
            )

        return discord.Embed(
            color = ctx.bot.bot_color,
            title = article.title,
            url = article.url,
            description = description
        ).set_image(
            url = article.image_url
        ).set_footer(
            icon_url = article.wiki.logo,
            text = article.wiki.name
        )

    @discord.ui.select()
    async def article(self, interaction, select):
        # TODO: Defer?

        for option in select.options:
            option.default = False

        selected = int(select.values[0])
        article = self.articles[selected]

        if article.extract:
            description = article.extract
        else:
            description = await get_article_beginning(
                article,
                aiohttp_session = interaction.client.aiohttp_session
            )

        embed = discord.Embed(
            color = interaction.client.bot_color,
            title = article.title,
            url = article.url,
            description = description
        ).set_image(
            url = article.image_url
        ).set_footer(
            icon_url = article.wiki.logo,
            text = article.wiki.name
        )

        select.options[selected].default = True

        await interaction.response.edit_message(embed = embed, view = self)

    async def stop(self):
        self.article.disabled = True

        await self.message.edit(view = self)

        super().stop()

    async def on_timeout(self):
        await self.stop()

