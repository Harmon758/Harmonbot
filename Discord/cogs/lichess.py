
import discord
from discord import ui
from discord.ext import commands

import asyncio
import datetime
from pathlib import Path

import emoji
import pycountry

from units.time import duration_to_string
from utilities import checks


EMOJIS = {
    "ultrabullet": "UltraBullet",
    "bullet": "Bullet",
    "blitz": "FlameBlitz",
    "rapid": "Rabbit",
    "classical": "Turtle",
    "correspondence": "PaperAirplane",
    "crazyhouse": "Crazyhouse",
    "chess960": "DieSix",
    "king_of_the_hill": "FlagKingHill",
    "three_check": "ThreeCheckStack",
    "antichess": "Antichess",
    "atomic": "Atom",
    "horde": "Keypad",
    "racing_kings": "FlagRacingKings",
    "training": "ArcheryTarget",
    "up_right_arrow": "ArrowUpRight",
    "down_right_arrow": "ArrowDownRight",
    "forum": "BubbleConvo",
    "practice": "Bullseye",
    "stream": "Mic",
    "team": "Group",
    "thumbsup": "ThumbsUp",
    "trophy": "Trophy",
}

MODES = {
    "ultraBullet": "Ultrabullet",
    "bullet": "Bullet",
    "blitz": "Blitz",
    "rapid": "Rapid",
    "classical": "Classical",
    "correspondence": "Correspondence",
    "crazyhouse": "Crazyhouse",
    "chess960": "Chess960",
    "kingOfTheHill": "King of the Hill",
    "threeCheck": "Three-Check",
    "antichess": "Antichess",
    "atomic": "Atomic",
    "horde": "Horde",
    "racingKings": "Racing Kings",
    "puzzle": "Training",
}


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
        asyncio.create_task(
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

        self.ultrabullet_emoji = self.bot.application_emojis.get("lichess_ultrabullet", "\N{NORTH WEST ARROW}\N{VARIATION SELECTOR-16}")
        self.bullet_emoji = self.bot.application_emojis.get("lichess_bullet", "\N{HIGH VOLTAGE SIGN}")
        self.blitz_emoji = self.bot.application_emojis.get("lichess_blitz", "\N{FIRE}")
        self.rapid_emoji = self.bot.application_emojis.get("lichess_rapid", "\N{RABBIT}")
        self.classical_emoji = self.bot.application_emojis.get("lichess_classical", "\N{TURTLE}")
        self.correspondence_emoji = self.bot.application_emojis.get("lichess_correspondence", "\N{ENVELOPE}\N{VARIATION SELECTOR-16}")
        self.crazyhouse_emoji = self.bot.application_emojis.get("lichess_crazyhouse", "\N{PISCES}")
        self.chess960_emoji = self.bot.application_emojis.get("lichess_chess960", "\N{GAME DIE}")
        self.kingofthehill_emoji = self.bot.application_emojis.get("lichess_king_of_the_hill", "\N{TRIANGULAR FLAG ON POST}")
        self.threecheck_emoji = self.bot.application_emojis.get("lichess_three_check", "3\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}")
        self.antichess_emoji = self.bot.application_emojis.get("lichess_antichess", "\N{CLOCKWISE DOWNWARDS AND UPWARDS OPEN CIRCLE ARROWS}")
        self.atomic_emoji = self.bot.application_emojis.get("lichess_atomic", "\N{ATOM SYMBOL}\N{VARIATION SELECTOR-16}")
        self.horde_emoji = self.bot.application_emojis.get("lichess_horde", "")  # TODO: Fallback Emoji
        self.racingkings_emoji = self.bot.application_emojis.get("lichess_racing_kings", "\N{CHEQUERED FLAG}")
        self.training_emoji = self.bot.application_emojis.get("lichess_training", "\N{DIRECT HIT}")
        self.uprightarrow_emoji = self.bot.application_emojis.get("lichess_up_right_arrow", "\N{NORTH EAST ARROW}\N{VARIATION SELECTOR-16}")
        # Also possible fallback emoji: :chart_with_upwards_trend:
        self.downrightarrow_emoji = self.bot.application_emojis.get("lichess_down_right_arrow", "\N{SOUTH EAST ARROW}\N{VARIATION SELECTOR-16}")
        # Also possible fallback emoji: :chart_with_downwards_trend:
        self.forum_emoji = self.bot.application_emojis.get("lichess_forum", "\N{SPEECH BALLOON}")
        # Also possible fallback emoji: :speech_left:
        self.practice_emoji = self.bot.application_emojis.get("lichess_practice", "")  # TODO: Fallback Emoji
        self.stream_emoji = self.bot.application_emojis.get("lichess_stream", "\N{STUDIO MICROPHONE}\N{VARIATION SELECTOR-16}")
        self.team_emoji = self.bot.application_emojis.get("lichess_team", "")  # TODO: Fallback Emoji
        self.thumbsup_emoji = self.bot.application_emojis.get("lichess_thumbsup", "\N{THUMBS UP SIGN}")  # TODO: Add skin-tone
        self.trophy_emoji = self.bot.application_emojis.get("lichess_trophy", "\N{TROPHY}")
        self.mode_emojis = (
            self.ultrabullet_emoji, self.bullet_emoji, self.blitz_emoji,
            self.rapid_emoji, self.classical_emoji, self.correspondence_emoji,
            self.crazyhouse_emoji, self.chess960_emoji, self.kingofthehill_emoji,
            self.threecheck_emoji, self.antichess_emoji, self.atomic_emoji,
            self.horde_emoji, self.racingkings_emoji, self.training_emoji
        )

    async def cog_check(self, ctx):
        return await checks.not_forbidden().predicate(ctx)

    @commands.group(invoke_without_command = True, case_insensitive = True)
    async def lichess(self, ctx):
        '''Lichess'''
        await ctx.send_help(ctx.command)

    @lichess.group(aliases = ["tournaments"], invoke_without_command = True, case_insensitive = True)
    async def tournament(self, ctx):
        '''Tournaments'''
        await ctx.send_help(ctx.command)

    @tournament.command(name = "current", aliases = ["started"])
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
        invoke_without_command = True, case_insensitive = True
    )
    async def user(self, ctx, username: LichessUser):
        '''User stats'''
        # TODO: Separate stats subcommand?
        view = LichessUserView(ctx, username, self.mode_emojis)
        view.message = await ctx.reply(
            "",
            embed = view.overview_embed,
            view = view
        )
        ctx.bot.views.append(view)

    @user.command(name = "activity")
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
                        f"{self.practice_emoji} Practiced {practice['nbPositions']} positions on "
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
                    f"{self.training_emoji} Solved {total_puzzles} tactical "
                    f"{ctx.bot.inflect_engine.plural('puzzle', total_puzzles)}\t"
                )
                if rating_change != 0:
                    activity += str(rating_after)
                    if rating_change > 0:
                        activity += str(self.uprightarrow_emoji)
                    elif rating_change < 0:
                        activity += str(self.downrightarrow_emoji)
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
                    mode_index = list(MODES.keys()).index(mode)
                    total_matches = mode_wins + mode_losses + mode_draws
                    rating_change = rating_after - rating_before
                    activity += (
                        f"{self.mode_emojis[mode_index]} Played {total_matches} "
                        f"{MODES[mode]} "
                        f"{ctx.bot.inflect_engine.plural('game', total_matches)}\t"
                    )
                    if rating_change != 0:
                        activity += str(rating_after)
                        if rating_change > 0:
                            activity += str(self.uprightarrow_emoji)
                        elif rating_change < 0:
                            activity += str(self.downrightarrow_emoji)
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
                        f"{self.forum_emoji} Posted {len(post['posts'])} "
                        f"{ctx.bot.inflect_engine.plural('message', len(post['posts']))}"
                        f" in [{post['topicName']}](https://lichess.org{post['topicUrl']})\n"
                    )
            if "correspondenceMoves" in day:
                activity += (
                    f"{self.correspondence_emoji} Played {day['correspondenceMoves']['nb']} "
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
                    f"{self.correspondence_emoji} Completed {total_matches} correspondence "
                    f"{ctx.bot.inflect_engine.plural('game', total_matches)}\t"
                )
                if rating_change != 0:
                    activity += str(rating_after)
                    if rating_change > 0:
                        activity += str(self.uprightarrow_emoji)
                    elif rating_change < 0:
                        activity += str(self.downrightarrow_emoji)
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
                if "in" in day["follows"]:
                    follows_in = day["follows"]["in"]["ids"]
                    activity += (
                        f"{self.thumbsup_emoji} Gained "
                        f"{day['follows']['in'].get('nb', len(follows_in))} new "
                        f"{ctx.bot.inflect_engine.plural('follower', len(follows_in))}"
                        f"\n\t{', '.join(follows_in)}\n"
                    )
                if "out" in day["follows"]:
                    follows_out = day["follows"]["out"]["ids"]
                    activity += (
                        f"{self.thumbsup_emoji} Started following "
                        f"{day['follows']['out'].get('nb', len(follows_out))} "
                        f"{ctx.bot.inflect_engine.plural('player', len(follows_out))}"
                        f"\n\t{', '.join(follows_out)}\n"
                    )
            if "tournaments" in day:
                activity += (
                    f"{self.trophy_emoji} Competed in {day['tournaments']['nb']} "
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
                    f"{self.team_emoji} Joined {len(day['teams'])} "
                    f"{ctx.bot.inflect_engine.plural('team', len(day['teams']))}\n\t"
                )
                teams = [f"[{team['name']}](https://lichess.org{team['url']})" for team in day["teams"]]
                activity += f"{', '.join(teams)}\n"
            if day.get("stream"):
                activity += f"{self.stream_emoji} Hosted a live stream\n"
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

    @user.command(name = "games")
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

    @user.command(name = "profile", aliases = ["bio"])
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

    def __init__(self, ctx, lichess_user, mode_emojis):
        super().__init__(timeout = 600)

        self.bot = ctx.bot
        self.lichess_user = lichess_user
        self.mode_emojis = mode_emojis

        # https://github.com/Rapptz/discord.py/pull/10143
        for option in self.perf.options:
            option.default = False
        self.perf.options[0].default = True

        if len(self.perf.options) == 1:
            for mode, name in MODES.items():
                self.perf.add_option(
                    emoji = self.mode_emojis[list(MODES.keys()).index(mode)],
                    label = name,
                    value = mode
                )

        self.uprightarrow_emoji = self.bot.application_emojis.get("lichess_up_right_arrow", "\N{NORTH EAST ARROW}\N{VARIATION SELECTOR-16}")
        self.downrightarrow_emoji = self.bot.application_emojis.get("lichess_down_right_arrow", "\N{SOUTH EAST ARROW}\N{VARIATION SELECTOR-16}")

        self.overview_embed = discord.Embed(
            color = self.bot.bot_color,
            title = lichess_user.get("title", "") + ' ' + lichess_user["username"],
            url = lichess_user["url"]
        )
        for mode, name, emoji in zip(MODES.keys(), MODES.values(), self.mode_emojis):
            if not lichess_user["perfs"].get(mode, {}).get("games", 0):
                continue
            mode_data = lichess_user["perfs"][mode]
            prov = ""
            if lichess_user["perfs"][mode].get("prov"):
                prov = '?'
            if lichess_user["perfs"][mode]["prog"] >= 0:
                arrow = self.uprightarrow_emoji
            else:
                arrow = self.downrightarrow_emoji
            self.overview_embed.add_field(
                name = str(emoji) + ' ' + name,
                value = (
                    f"Games: {mode_data['games']}\nRating:\n"
                    f"{mode_data['rating']}{prov} ± {mode_data['rd']} {arrow} {mode_data['prog']}"
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
        for option in select.options:
            option.default = False

        if select.values[0] == "Overview":
            embed = self.overview_embed
            select.options[0].default = True
        else:
            mode = select.values[0]
            index = list(MODES.keys()).index(mode)
            mode_data = self.lichess_user["perfs"][mode]
            prov = ""
            if self.lichess_user["perfs"][mode].get("prov"):
                prov = '?'
            if self.lichess_user["perfs"][mode]["prog"] >= 0:
                arrow = self.uprightarrow_emoji
            else:
                arrow = self.downrightarrow_emoji
            embed = discord.Embed(
                color = self.bot.bot_color,
                title = self.lichess_user["username"],
                description = (
                    f"{self.mode_emojis[index]} {MODES[mode]} | **Games**: {mode_data['games']}, "
                    f"**Rating**: {mode_data['rating']}{prov}±{mode_data['rd']} "
                    f"{arrow} {mode_data['prog']}"
                )
            )
            select.options[index + 1].default = True

        await interaction.response.edit_message(embed = embed, view = self)

    async def stop(self):
        self.perf.disabled = True
        await self.message.edit(view = self)
        super().stop()

    async def on_timeout(self):
        await self.stop()

