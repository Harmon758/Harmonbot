
import discord
from discord import ui
from discord.ext import commands

import asyncio
import datetime
from pathlib import Path
from typing import Literal, NamedTuple, Optional

import emoji
import pycountry

from units.time import duration_to_string
from utilities import checks


class Mode(NamedTuple):
    key: str
    name: str
    emoji_name: str
    emoji_icon: str

MODES = (
    Mode("ultraBullet", "Ultrabullet", "ultrabullet", "UltraBullet"),
    Mode("bullet", "Bullet", "bullet", "Bullet"),
    Mode("blitz", "Blitz", "blitz", "FlameBlitz"),
    Mode("rapid", "Rapid", "rapid", "Rabbit"),
    Mode("classical", "Classical", "classical", "Turtle"),
    Mode("correspondence", "Correspondence", "correspondence", "PaperAirplane"),
    Mode("crazyhouse", "Crazyhouse", "crazyhouse", "Crazyhouse"),
    Mode("chess960", "Chess960", "chess960", "DieSix"),
    Mode("kingOfTheHill", "King of the Hill", "king_of_the_hill", "FlagKingHill"),
    Mode("threeCheck", "Three-Check", "three_check", "ThreeCheckStack"),
    Mode("antichess", "Antichess", "antichess", "Antichess"),
    Mode("atomic", "Atomic", "atomic", "Atom"),
    Mode("horde", "Horde", "horde", "Keypad"),
    Mode("racingKings", "Racing Kings", "racing_kings", "FlagRacingKings"),
    Mode("puzzle", "Puzzles", "puzzles", "ArcheryTarget"),
    Mode("storm", "Puzzle Storm", "storm", "Storm"),
    Mode("racer", "Puzzle Racer", "racer", "FlagChessboard"),
    Mode("streak", "Puzzle Streak", "streak", "ArrowThruApple"),
)

MODE_KEYS = {mode.key: mode for mode in MODES}
MODE_NAMES = {mode.name: mode for mode in MODES}

EMOJIS = {mode.emoji_name: mode.emoji_icon for mode in MODES} | {
    "up_right_arrow": "ArrowUpRight",
    "down_right_arrow": "ArrowDownRight",
    "forum": "BubbleConvo",
    "practice": "Bullseye",
    "stream": "Mic",
    "team": "Group",
    "thumbsup": "ThumbsUp",
    "trophy": "Trophy",
}

FALLBACK_UP_RIGHT_ARROW_EMOJI = "\N{NORTH EAST ARROW}\N{VARIATION SELECTOR-16}"
FALLBACK_DOWN_RIGHT_ARROW_EMOJI = "\N{SOUTH EAST ARROW}\N{VARIATION SELECTOR-16}"


async def setup(bot):
    await bot.add_cog(Lichess(bot))

class LichessUser(commands.Converter):
    async def convert(self, ctx, argument):
        url = f"https://en.lichess.org/api/user/{argument}"
        async with ctx.bot.aiohttp_session.get(url) as resp:
            if resp.status == 404:
                raise commands.BadArgument("User not found")
            data = await resp.json()
        if not data:
            raise commands.BadArgument("User not found")
        if data.get("closed") or data.get("disabled"):
            raise commands.BadArgument("This account is closed")
        return data

class Lichess(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.application_emojis_initialization_task = asyncio.create_task(
            self.initialize_application_emojis(),
            name = "Initialize Lichess application emojis"
        )

    async def initialize_application_emojis(self):
        for name, file_name in EMOJIS.items():
            if f"lichess_{name}" not in self.bot.application_emojis:
                self.bot.application_emojis[f"lichess_{name}"] = (
                    await self.bot.create_application_emoji(
                        name = f"lichess_{name}",
                        image = (Path(self.bot.assets_path) / "lichess_icons" / f"{file_name}.png").read_bytes()
                    )
                )

    async def cog_check(self, ctx):
        return await checks.not_forbidden().predicate(ctx)

    @commands.hybrid_group(case_insensitive = True)
    async def lichess(self, ctx):
        '''Lichess'''
        await ctx.send_help(ctx.command)

    @lichess.group(aliases = ["tournaments"], case_insensitive = True)
    async def tournament(self, ctx):
        '''Tournaments'''
        await ctx.send_help(ctx.command)

    @tournament.command(
        name = "current", aliases = ["started"], with_app_command = False
    )
    async def tournament_current(self, ctx):
        '''Current tournaments'''
        url = "https://en.lichess.org/api/tournament"
        async with ctx.bot.aiohttp_session.get(url) as resp:
            data = await resp.json()
        data = data["started"]
        fields = []
        for tournament in data:
            finishes_at = datetime.datetime.utcfromtimestamp(tournament["finishesAt"] / 1000.0)
            value = (
                f"{tournament['clock']['limit'] / 60:g}+{tournament['clock']['increment']} "
                f"{tournament['perf']['name']} {'Rated' if tournament['rated'] else 'Casual'}"
                f"\nEnds in: {(finishes_at - datetime.datetime.utcnow()).total_seconds() // 60:g}m"
                # TODO: Use 'h' for hours?
                f"\n[Link](https://en.lichess.org/tournament/{tournament['id']})"
            )
            fields.append((tournament["fullName"], value))
        await ctx.embed_reply(title = "Current Lichess Tournaments", fields = fields)

    @lichess.group(
        aliases = ["stats", "statistics", "stat", "statistic"],
        case_insensitive = True, fallback = "statistics"
    )
    async def user(
        self, ctx, username: LichessUser, *,
        mode: Optional[Literal[tuple(MODE_NAMES)]]  # noqa: UP045 (non-pep604-annotation-optional)
    ):
        '''
        View statistics of a Lichess user

        Parameters
        ----------
        username
            The username of the Lichess user of whom to view stats
        mode
            The speed, variant, or puzzle mode for which to view stats
        '''
        # TODO: Separate stats subcommand?
        await ctx.defer()
        view = LichessUserView(ctx, username)
        view.message = await ctx.reply(
            "",
            embed = (
                view.select_perf(MODE_NAMES[mode].key)
                if mode else view.overview_embed
            ),
            view = view
        )
        ctx.bot.views.append(view)

    @user.command(name = "activity", with_app_command = False)
    async def user_activity(self, ctx, username: str):
        '''User activity'''
        # TODO: Use converter?
        url = f"https://lichess.org/api/user/{username}/activity"
        async with ctx.bot.aiohttp_session.get(url) as resp:
            data = await resp.json()
            if resp.status == 429 and "error" in data:
                await ctx.embed_reply(f":no_entry: Error: {data['error']}")
                return
        if not data:
            await ctx.embed_reply(":no_entry: User activity not found")
            return
        fields = []
        total_length = 0
        for day in data:
            activity = ""
            if "practice" in day:
                for practice in day["practice"]:
                    activity += (
                        f"{ctx.bot.application_emojis.get('lichess_practice', '')} Practiced {practice['nbPositions']} positions on "
                        f"[{practice['name']}](https://lichess.org{practice['url']})\n"
                    )
            if "puzzles" in day:
                puzzle_wins = day["puzzles"]["score"]["win"]
                puzzle_losses = day["puzzles"]["score"]["loss"]
                puzzle_draws = day["puzzles"]["score"]["draw"]
                rating_before = day["puzzles"]["score"]["rp"]["before"]
                rating_after = day["puzzles"]["score"]["rp"]["after"]
                total_puzzles = puzzle_wins + puzzle_losses + puzzle_draws
                rating_change = rating_after - rating_before
                activity += (
                    f"{ctx.bot.application_emojis.get('lichess_puzzles', '')} Solved {total_puzzles} tactical "
                    f"{ctx.bot.inflect_engine.plural('puzzle', total_puzzles)}\t"
                )
                if rating_change != 0:
                    activity += str(rating_after)
                    if rating_change > 0:
                        activity += str(ctx.bot.application_emojis.get("lichess_up_right_arrow", FALLBACK_UP_RIGHT_ARROW_EMOJI))
                    elif rating_change < 0:
                        activity += str(ctx.bot.application_emojis.get("lichess_down_right_arrow", FALLBACK_DOWN_RIGHT_ARROW_EMOJI))
                    activity += f"{abs(rating_change)}\t"
                if puzzle_wins:
                    activity += f"{puzzle_wins} {ctx.bot.inflect_engine.plural('win', puzzle_wins)} "
                if puzzle_draws:
                    activity += f"{puzzle_draws} {ctx.bot.inflect_engine.plural('draw', puzzle_draws)} "
                if puzzle_losses:
                    activity += f"{puzzle_losses} {ctx.bot.inflect_engine.plural('loss', puzzle_losses)}"
                activity += '\n'
            if "games" in day:
                for mode, mode_data in day["games"].items():
                    mode_wins = mode_data["win"]
                    mode_losses = mode_data["loss"]
                    mode_draws = mode_data["draw"]
                    rating_before = mode_data["rp"]["before"]
                    rating_after = mode_data["rp"]["after"]
                    total_matches = mode_wins + mode_losses + mode_draws
                    rating_change = rating_after - rating_before
                    activity += (
                        str(ctx.bot.application_emojis.get(f"lichess_{MODE_KEYS[mode].emoji_name}", "")) +
                        f" Played {total_matches} "
                        f"{MODE_KEYS[mode].name} "
                        f"{ctx.bot.inflect_engine.plural('game', total_matches)}\t"
                    )
                    if rating_change != 0:
                        activity += str(rating_after)
                        if rating_change > 0:
                            activity += str(ctx.bot.application_emojis.get("lichess_up_right_arrow", FALLBACK_UP_RIGHT_ARROW_EMOJI))
                        elif rating_change < 0:
                            activity += str(ctx.bot.application_emojis.get("lichess_down_right_arrow", FALLBACK_DOWN_RIGHT_ARROW_EMOJI))
                        activity += f"{abs(rating_change)}\t"
                    if mode_wins:
                        activity += f"{mode_wins} {ctx.bot.inflect_engine.plural('win', mode_wins)} "
                    if mode_draws:
                        activity += f"{mode_draws} {ctx.bot.inflect_engine.plural('draw', mode_draws)} "
                    if mode_losses:
                        activity += f"{mode_losses} {ctx.bot.inflect_engine.plural('loss', mode_losses)}"
                    activity += '\n'
            if "posts" in day:
                for post in day["posts"]:
                    activity += (
                        f"{ctx.bot.application_emojis.get('lichess_forum', '')} Posted {len(post['posts'])} "
                        f"{ctx.bot.inflect_engine.plural('message', len(post['posts']))}"
                        f" in [{post['topicName']}](https://lichess.org{post['topicUrl']})\n"
                    )
            if "correspondenceMoves" in day:
                activity += (
                    f"{ctx.bot.application_emojis.get('lichess_correspondence', '')} Played {day['correspondenceMoves']['nb']} "
                    f"{ctx.bot.inflect_engine.plural('move', day['correspondenceMoves']['nb'])}"
                )
                game_count = len(day["correspondenceMoves"]["games"])
                activity += f" in {game_count}"
                if game_count == 15:
                    activity += '+'
                activity += f" correspondence {ctx.bot.inflect_engine.plural('game', game_count)}\n"
                # TODO: Include game details?
            if "correspondenceEnds" in day:
                correspondence_wins = day["correspondenceEnds"]["correspondence"]["score"]["win"]
                correspondence_losses = day["correspondenceEnds"]["correspondence"]["score"]["loss"]
                correspondence_draws = day["correspondenceEnds"]["correspondence"]["score"]["draw"]
                rating_before = day["correspondenceEnds"]["correspondence"]["score"]["rp"]["before"]
                rating_after = day["correspondenceEnds"]["correspondence"]["score"]["rp"]["after"]
                total_matches = correspondence_wins + correspondence_losses + correspondence_draws
                rating_change = rating_after - rating_before
                activity += (
                    f"{ctx.bot.application_emojis.get('lichess_correspondence', '')} Completed {total_matches} correspondence "
                    f"{ctx.bot.inflect_engine.plural('game', total_matches)}\t"
                )
                if rating_change != 0:
                    activity += str(rating_after)
                    if rating_change > 0:
                        activity += str(ctx.bot.application_emojis.get("lichess_up_right_arrow", FALLBACK_UP_RIGHT_ARROW_EMOJI))
                    elif rating_change < 0:
                        activity += str(ctx.bot.application_emojis.get("lichess_down_right_arrow", FALLBACK_DOWN_RIGHT_ARROW_EMOJI))
                    activity += f"{abs(rating_change)}\t"
                if correspondence_wins:
                    activity += f"{correspondence_wins} {ctx.bot.inflect_engine.plural('win', correspondence_wins)} "
                if correspondence_draws:
                    activity += f"{correspondence_draws} {ctx.bot.inflect_engine.plural('draw', correspondence_draws)} "
                if correspondence_losses:
                    activity += f"{correspondence_losses} {ctx.bot.inflect_engine.plural('loss', correspondence_losses)}"
                activity += '\n'
                # TODO: Include game details?
            if "follows" in day:
                thumbsup_emoji = ctx.bot.application_emojis.get("lichess_thumbsup", "")
                if "in" in day["follows"]:
                    follows_in = day["follows"]["in"]["ids"]
                    activity += (
                        f"{thumbsup_emoji} Gained "
                        f"{day['follows']['in'].get('nb', len(follows_in))} new "
                        f"{ctx.bot.inflect_engine.plural('follower', len(follows_in))}"
                        f"\n\t{', '.join(follows_in)}\n"
                    )
                if "out" in day["follows"]:
                    follows_out = day["follows"]["out"]["ids"]
                    activity += (
                        f"{thumbsup_emoji} Started following "
                        f"{day['follows']['out'].get('nb', len(follows_out))} "
                        f"{ctx.bot.inflect_engine.plural('player', len(follows_out))}"
                        f"\n\t{', '.join(follows_out)}\n"
                    )
            if "tournaments" in day:
                activity += (
                    f"{ctx.bot.application_emojis.get('lichess_trophy', '')} Competed in {day['tournaments']['nb']} "
                    f"{ctx.bot.inflect_engine.plural('tournament', day['tournaments']['nb'])}\n"
                )
                for tournament in day["tournaments"]["best"]:
                    activity += (
                        f"\tRanked #{tournament['rank']} (top {tournament['rankPercent']}%) "
                        f"with {tournament['nbGames']} "
                        f"{ctx.bot.inflect_engine.plural('game', tournament['nbGames'])}"
                        f" in [{tournament['tournament']['name']}]"
                        f"(https://lichess.org/tournament/{tournament['tournament']['id']})\n"
                    )
            if "teams" in day:
                activity += (
                    f"{ctx.bot.application_emojis.get('lichess_team', '')} Joined {len(day['teams'])} "
                    f"{ctx.bot.inflect_engine.plural('team', len(day['teams']))}\n\t"
                )
                teams = [f"[{team['name']}](https://lichess.org{team['url']})" for team in day["teams"]]
                activity += f"{', '.join(teams)}\n"
            if day.get("stream"):
                activity += f"{ctx.bot.application_emojis.get('lichess_stream', '')} Hosted a live stream\n"
                # TODO: Add link
            # TODO: Use embed limit variables
            # TODO: Better method of checking total embed size
            date = datetime.datetime.utcfromtimestamp(day["interval"]["start"] / 1000)
            date = date.strftime("%b %#d, %Y")
            # %#d for removal of leading zero on Windows with native Python executable
            total_length += len(date) + len(activity)
            if total_length > 6000:
                break
            if 0 < len(activity) <= 1024:  # > 0 check necessary?
                fields.append((date, activity, False))
            elif len(activity) > 1024:
                split_index = activity.rfind('\n', 0, 1024)
                # TODO: Better method of finding split index, new line could be in between section
                fields.append((date, activity[:split_index], False))
                fields.append((f"{date} (continued)", activity[split_index:], False))
                # TODO: Dynamically handle splits
                # TODO: Use zws?
        await ctx.embed_reply(title = f"{username}'s Activity", fields = fields)

    @user.command(name = "games", with_app_command = False)
    async def user_games(self, ctx, username: LichessUser):
        '''User games'''
        title = username.get("title", "") + ' ' + username["username"]
        fields = [
            ("Games", username["count"]["all"]),
            ("Rated", username["count"]["rated"]),
            ("Wins", username["count"]["win"]),
            ("Losses", username["count"]["loss"]),
            ("Draws", username["count"]["draw"]),
            ("Playing", username["count"]["playing"]),
            ("Bookmarks", username["count"]["bookmark"]),
            ("Imported", username["count"]["import"]),
        ]
        if "ai" in username["count"]:
            fields.append(("AI", username["count"]["ai"]))
        if "seenAt" in username:
            footer_text = "Last seen"
            timestamp = datetime.datetime.utcfromtimestamp(username["seenAt"] / 1000.0)
        else:
            footer_text = timestamp = None
        await ctx.embed_reply(
            title = title, title_url = username["url"], fields = fields,
            footer_text = footer_text, timestamp = timestamp
        )

    @user.command(
        name = "profile", aliases = ["bio"], with_app_command = False
    )
    async def user_profile(self, ctx, username: LichessUser):
        '''User profile'''
        user_data = username
        title = user_data.get("title", "") + ' ' + user_data["username"]
        description = None
        fields = []
        profile = user_data.get("profile", {})
        if "firstName" in profile or "lastName" in profile:
            fields.append((
                f"{profile.get('firstName', '')} {profile.get('lastName', '')}",
                profile.get("bio"), False
            ))
        else:
            description = profile.get("bio")
        fields.append(("Patron", "Yes" if user_data.get("patron") else "No"))
        if "fideRating" in profile:
            fields.append(("FIDE Rating", profile["fideRating"]))
        if "uscfRating" in profile:
            fields.append(("USCF Rating", profile["uscfRating"]))
        # TODO: Add ECF Rating
        if "flag" in profile:
            country = profile["flag"]
            country_name = pycountry.countries.get(alpha_2 = country[:2]).name
            country_flag = emoji.emojize(f":{country_name.replace(' ', '_')}:")
            if len(country) > 2:  # Subdivision
                country_name = pycountry.subdivisions.get(code = country).name
            # Wait for subdivision flag emoji support from Discord
            # From Unicode 10.0/Emoji 5.0/Twemoji 2.3
            # For England, Scotland, and Wales
            fields.append(("Location", f"{profile.get('location', '')}\n{country_flag} {country_name}"))
        elif "location" in profile:
            fields.append(("Location", profile["location"]))
        created_at = datetime.datetime.utcfromtimestamp(user_data["createdAt"] / 1000.0)
        fields.append(("Member Since", created_at.strftime("%b %#d, %Y")))
        # %#d for removal of leading zero on Windows with native Python executable
        if "completionRate" in user_data:
            fields.append(("Game Completion Rate", f"{user_data['completionRate']}%"))
        playtime = user_data.get("playTime", {})
        if "total" in playtime:
            fields.append((
                "Time Spent Playing",
                duration_to_string(datetime.timedelta(seconds = playtime["total"]), abbreviate = True)
            ))
        if tv_time := playtime.get("tv"):
            fields.append((
                "Time On TV",
                duration_to_string(datetime.timedelta(seconds = tv_time), abbreviate = True)
            ))
        if "links" in profile:
            fields.append(("Links", profile["links"], False))
        if "seenAt" in user_data:
            footer_text = "Last seen"
            timestamp = datetime.datetime.utcfromtimestamp(user_data["seenAt"] / 1000.0)
        else:
            footer_text = timestamp = None
        await ctx.embed_reply(
            description, title = title, title_url = user_data["url"],
            fields = fields, footer_text = footer_text, timestamp = timestamp
        )


class LichessUserView(ui.View):

    def __init__(self, ctx, lichess_user):
        super().__init__(timeout = 600)

        self.bot = ctx.bot
        self.lichess_user = lichess_user

        if len(self.perf.options) == 1:
            for mode in MODES:
                self.perf.add_option(
                    emoji = self.bot.application_emojis.get(
                        f"lichess_{mode.emoji_name}", None
                    ),
                    label = mode.name,
                    value = mode.key
                )

        self.overview_embed = discord.Embed(
            color = self.bot.bot_color,
            title = lichess_user.get("title", "") + ' ' + lichess_user["username"],
            url = lichess_user["url"]
        )
        for mode in MODES:
            if not (mode_data := lichess_user["perfs"].get(mode.key)):
                continue
            if mode_data.get("games", 0):
                prov = ""
                if mode_data.get("prov"):
                    prov = '?'
                if mode_data["prog"] >= 0:
                    arrow = self.bot.application_emojis.get("lichess_up_right_arrow", FALLBACK_UP_RIGHT_ARROW_EMOJI)
                else:
                    arrow = self.bot.application_emojis.get("lichess_down_right_arrow", FALLBACK_DOWN_RIGHT_ARROW_EMOJI)
                self.overview_embed.add_field(
                    name = str(self.bot.application_emojis.get(f"lichess_{mode.emoji_name}", "")) + ' ' + mode.name,
                    value = (
                        f"Games: {mode_data['games']}\nRating:\n"
                        f"{mode_data['rating']}{prov} ± {mode_data['rd']} {arrow} {mode_data['prog']}"
                    )
                )
            elif mode_data.get("runs", 0):
                self.overview_embed.add_field(
                    name = str(self.bot.application_emojis.get(f"lichess_{mode.emoji_name}", "")) + ' ' + mode.name,
                    value = (
                        f"Runs: {mode_data['runs']}\n"
                        f"Score: {mode_data['score']}"
                    )
                )
        if "seenAt" in lichess_user:
            self.overview_embed.set_footer(text = "Last seen")
            self.overview_embed.timestamp = datetime.datetime.utcfromtimestamp(lichess_user["seenAt"] / 1000.0)

    @ui.select(
        placeholder = "Select a speed, variant, or puzzle mode",
        options = [
            discord.SelectOption(
                label = "Overview",
                default = True
            ),
        ]
    )
    async def perf(self, interaction, select):
        await interaction.response.edit_message(
            embed = self.select_perf(select.values[0]), view = self
        )

    def select_perf(self, mode: str):
        for option in self.perf.options:
            option.default = False

        if mode == "Overview":
            embed = self.overview_embed
            self.perf.options[0].default = True
        else:
            index = list(MODE_KEYS).index(mode)
            mode_data = self.lichess_user["perfs"][mode]
            embed = discord.Embed(
                color = self.bot.bot_color,
                title = self.lichess_user["username"]
            )
            if mode_data.get("games", 0):
                prov = ""
                if mode_data.get("prov"):
                    prov = '?'
                if mode_data["prog"] >= 0:
                    arrow = self.bot.application_emojis.get("lichess_up_right_arrow", FALLBACK_UP_RIGHT_ARROW_EMOJI)
                else:
                    arrow = self.bot.application_emojis.get("lichess_down_right_arrow", FALLBACK_DOWN_RIGHT_ARROW_EMOJI)
                embed.add_field(
                    name = str(self.bot.application_emojis.get(f"lichess_{MODE_KEYS[mode].emoji_name}", "")) + f" {MODE_KEYS[mode].name}",
                    value = (
                        f"Games: {mode_data['games']}\n"
                        f"Rating: {mode_data['rating']}{prov}±{mode_data['rd']} "
                        f"{arrow} {mode_data['prog']}"
                    )
                )
            elif mode_data.get("runs", 0):
                embed.add_field(
                    name = str(self.bot.application_emojis.get(f"lichess_{MODE_KEYS[mode].emoji_name}", "")) + f" {MODE_KEYS[mode].name}",
                    value = (
                        f"Runs: {mode_data['runs']}\n"
                        f"Score: {mode_data['score']}"
                    )
                )
            self.perf.options[index + 1].default = True

        return embed

    async def stop(self):
        self.perf.disabled = True
        await self.message.edit(view = self)
        super().stop()

    async def on_timeout(self):
        await self.stop()

