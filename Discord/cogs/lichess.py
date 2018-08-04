
import discord
from discord.ext import commands

import datetime

import clients
from modules import utilities
from utilities import checks

def setup(bot):
	bot.add_cog(Lichess(bot))

class Lichess:
	
	def __init__(self, bot):
		self.bot = bot
		
		self.modes = ("ultraBullet", "bullet", "blitz", "rapid", "classical", "correspondence", "crazyhouse", "chess960", "kingOfTheHill", "threeCheck", "antichess", "atomic", "horde", "racingKings", "puzzle")
		self.mode_names = ("Ultrabullet", "Bullet", "Blitz", "Rapid", "Classical", "Correspondence", "Crazyhouse", "Chess960", "King of the Hill", "Three-Check", "Antichess", "Atomic", "Horde", "Racing Kings", "Training")
		
		self.load_emoji()
		self.generate_user_mode_commands()
	
	async def on_ready(self):
		self.load_emoji()
		self.generate_user_mode_commands()
	
	def load_emoji(self):
		# TODO: Check only within Emoji Server emojis?
		# TODO: Use unicode code points
		self.ultrabullet_emoji = discord.utils.get(self.bot.emojis, name = "lichess_ultrabullet") or ":arrow_upper_left:"
		self.bullet_emoji = discord.utils.get(self.bot.emojis, name = "lichess_bullet") or ":zap:"
		self.blitz_emoji = discord.utils.get(self.bot.emojis, name = "lichess_blitz") or ":fire:"
		self.rapid_emoji = discord.utils.get(self.bot.emojis, name = "lichess_rapid") or ":rabbit2:"
		self.classical_emoji = discord.utils.get(self.bot.emojis, name = "lichess_classical") or ":turtle:"
		self.correspondence_emoji = discord.utils.get(self.bot.emojis, name = "lichess_correspondence") or ":envelope:"
		self.crazyhouse_emoji = discord.utils.get(self.bot.emojis, name = "lichess_crazyhouse") or ":pisces:"
		self.chess960_emoji = discord.utils.get(self.bot.emojis, name = "lichess_chess960") or ":game_die:"
		self.kingofthehill_emoji = discord.utils.get(self.bot.emojis, name = "lichess_king_of_the_hill") or ":triangular_flag_on_post:"
		self.threecheck_emoji = discord.utils.get(self.bot.emojis, name = "lichess_three_check") or ":three:"
		self.antichess_emoji = discord.utils.get(self.bot.emojis, name = "lichess_antichess") or ":arrows_clockwise:"
		self.atomic_emoji = discord.utils.get(self.bot.emojis, name = "lichess_atomic") or ":atom:"
		self.horde_emoji = discord.utils.get(self.bot.emojis, name = "lichess_horde") or "" # TODO: Fallback Emoji
		self.racingkings_emoji = discord.utils.get(self.bot.emojis, name = "lichess_racing_kings") or ":checkered_flag:"
		self.training_emoji = discord.utils.get(self.bot.emojis, name = "lichess_training") or ":dart:"
		self.uprightarrow_emoji = discord.utils.get(self.bot.emojis, name = "lichess_up_right_arrow") or ":arrow_upper_right:"
		# Also possible fallback emoji: :chart_with_upwards_trend:
		self.downrightarrow_emoji = discord.utils.get(self.bot.emojis, name = "lichess_down_right_arrow") or ":arrow_lower_right:"
		# Also possible fallback emoji: :chart_with_downwards_trend:
		self.forum_emoji = discord.utils.get(self.bot.emojis, name = "lichess_forum") or ":speech_balloon:"
		# Also possible fallback emoji: :speech_left:
		self.practice_emoji = discord.utils.get(self.bot.emojis, name = "lichess_practice") or ""  # TODO: Fallback Emoji
		self.stream_emoji = discord.utils.get(self.bot.emojis, name = "lichess_stream") or ":microphone2:"
		self.team_emoji = discord.utils.get(self.bot.emojis, name = "lichess_team") or ""  # TODO: Fallback Emoji
		self.thumbsup_emoji = discord.utils.get(self.bot.emojis, name = "lichess_thumbsup") or ":thumbsup:"  # TODO: add skin-tone
		self.trophy_emoji = discord.utils.get(self.bot.emojis, name = "lichess_trophy") or ":trophy:"
		self.mode_emojis = (self.ultrabullet_emoji, self.bullet_emoji, self.blitz_emoji, self.rapid_emoji, self.classical_emoji, self.correspondence_emoji, self.crazyhouse_emoji, self.chess960_emoji, self.kingofthehill_emoji, self.threecheck_emoji, self.antichess_emoji, self.atomic_emoji, self.horde_emoji, self.racingkings_emoji, self.training_emoji)
	
	def generate_user_mode_commands(self):
		# Creates user subcommand for a mode
		def user_mode_wrapper(mode, name, emoji):
			@self.user.command(name = name.lower().replace(' ', "").replace('-', ""), help = "User {} stats".format(name))
			@checks.not_forbidden()
			async def user_mode_command(ctx, username : self.LichessUser):
				prov = "?" if username["perfs"][mode].get("prov") else ""
				arrow = self.uprightarrow_emoji if username["perfs"][mode]["prog"] >= 0 else self.downrightarrow_emoji
				await ctx.embed_reply("{emoji} {name} | **Games**: {0[games]}, **Rating**: {0[rating]}{prov}±{0[rd]}, {arrow} {0[prog]}".format(username["perfs"][mode], emoji = emoji, name = name, prov = prov, arrow = arrow), title = username["username"])
			return user_mode_command
		# Generate user subcommands for each mode
		for mode, name, emoji in zip(self.modes, self.mode_names, self.mode_emojis):
			self.user.remove_command(name.lower().replace(' ', "").replace('-', ""))
			setattr(self, "user_" + name.lower().replace(' ', "").replace('-', ""), user_mode_wrapper(mode, name, emoji))
	
	class LichessUser(commands.Converter):
		async def convert(self, ctx, argument):
			url = "https://en.lichess.org/api/user/{}".format(argument)
			async with clients.aiohttp_session.get(url) as resp:
				data = await resp.json()
			if not data or data.get("closed"):
				raise commands.BadArgument
			# await ctx.embed_reply(":no_entry: User not found")
			# TODO: custom error message?
			return data

	@commands.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def lichess(self, ctx):
		'''Lichess'''
		await ctx.invoke(self.bot.get_command("help"), ctx.invoked_with)
	
	@lichess.group(aliases = ["tournaments"], invoke_without_command = True)
	@checks.not_forbidden()
	async def tournament(self, ctx):
		'''Tournaments'''
		await ctx.invoke(self.bot.get_command("help"), "lichess", ctx.invoked_with)
	
	@tournament.command(name = "current", aliases = ["started"])
	@checks.not_forbidden()
	async def tournament_current(self, ctx):
		'''WIP'''
		url = "https://en.lichess.org/api/tournament"
		async with clients.aiohttp_session.get(url) as resp:
			data = await resp.json()
		data = data["started"]
		fields = []
		for tournament in data:
			value = "{:g}+{} {} {rated}".format(tournament["clock"]["limit"] / 60, tournament["clock"]["increment"], tournament["perf"]["name"], rated = "Rated" if tournament["rated"] else "Casual")
			value += "\nEnds in: {:g}m".format((datetime.datetime.utcfromtimestamp(tournament["finishesAt"] / 1000.0) - datetime.datetime.utcnow()).total_seconds() // 60)
			value += "\n[Link](https://en.lichess.org/tournament/{})".format(tournament["id"])
			fields.append((tournament["fullName"], value))
		await ctx.embed_reply(None, title = "Current Lichess Tournaments", fields = fields)
	
	@lichess.group(aliases = ["stats", "statistics", "stat", "statistic"], invoke_without_command = True)
	@checks.not_forbidden()
	async def user(self, ctx, username : LichessUser):
		'''
		WIP
		User stats
		'''
		description = "Online: {}\n".format(username["online"])
		description += "Member since {}\n".format(datetime.datetime.utcfromtimestamp(username["createdAt"] / 1000.0).strftime("%b %#d, %Y")) # Why is this comment here?
		fields = [("Games", "Played: {0[all]}\nRated: {0[rated]}\nWins: {0[win]}\nLosses: {0[loss]}\nDraws: {0[draw]}\nBookmarks: {0[bookmark]}\nAI: {0[ai]}".format(username["count"]))]
		fields.append(("Follows", "Followers: {0[nbFollowers]}\nFollowing: {0[nbFollowing]}".format(username)))
		fields.append(("Time", "Spent playing: {}\nOn TV: {}".format(utilities.secs_to_letter_format(username["playTime"]["total"]), utilities.secs_to_letter_format(username["playTime"]["tv"]))))
		for mode, name, emoji in zip(self.modes, self.mode_names, self.mode_emojis):
			if username["perfs"].get(mode, {}).get("games", 0) == 0: continue
			prov = '?' if username["perfs"][mode].get("prov") else ""
			arrow = self.uprightarrow_emoji if username["perfs"][mode]["prog"] >= 0 else self.downrightarrow_emoji
			value = "Games: {0[games]}\nRating: {0[rating]}{1} ± {0[rd]}\n{2} {0[prog]}".format(username["perfs"][mode], prov, arrow)
			fields.append((str(emoji) + ' ' + name, value))
		await ctx.embed_reply(description, title = username["username"], title_url = username["url"], fields = fields, footer_text = "Last seen", timestamp = datetime.datetime.utcfromtimestamp(username["seenAt"] / 1000.0))
	
	@user.command(name = "activity")
	@checks.not_forbidden()
	async def user_activity(self, ctx, username : str):
		'''User activity'''
		url = "https://lichess.org/api/user/{}/activity".format(username)
		async with clients.aiohttp_session.get(url) as resp:
			data = await resp.json()
			if resp.status == 429 and "error" in data:
				await ctx.embed_reply(":no_entry: Error: {}".format(data["error"]))
				return
		if not data:
			await ctx.embed_reply(":no_entry: User activity not found")
			return
		fields = []
		total_length = 0
		for day in data:
			date = datetime.datetime.utcfromtimestamp(day["interval"]["start"])
			date = date.strftime("%b %#d, %Y")
			activity = ""
			if "practice" in day:
				for practice in day["practice"]:
					activity += "{} Practiced ".format(self.practice_emoji)
					activity += "{} positions on ".format(practice["nbPositions"])
					activity += "[{0[name]}](https://lichess.org{0[url]})\n".format(practice)
			if "puzzles" in day:
				puzzle_wins = day["puzzles"]["score"]["win"]
				puzzle_losses = day["puzzles"]["score"]["loss"]
				puzzle_draws = day["puzzles"]["score"]["draw"]
				rating_before = day["puzzles"]["score"]["rp"]["before"]
				rating_after = day["puzzles"]["score"]["rp"]["after"]
				total_puzzles = puzzle_wins + puzzle_losses + puzzle_draws
				rating_change = rating_after - rating_before
				activity += "{} Solved {} tactical ".format(self.training_emoji, total_puzzles)
				activity += clients.inflect_engine.plural("puzzle", total_puzzles)
				activity += '\t'
				if rating_change != 0:
					activity += str(rating_after)
					if rating_change > 0:
						activity += str(self.uprightarrow_emoji)
					elif rating_change < 0:
						activity += str(self.downrightarrow_emoji)
					activity += "{}\t".format(abs(rating_change))
				if puzzle_wins:
					activity += "{} ".format(puzzle_wins)
					activity += clients.inflect_engine.plural("win", puzzle_wins)
					activity += ' '
				if puzzle_draws:
					activity += "{} ".format(puzzle_draws)
					activity += clients.inflect_engine.plural("draw", puzzle_draws)
					activity += ' '
				if puzzle_losses:
					activity += "{} ".format(puzzle_losses)
					activity += clients.inflect_engine.plural("loss", puzzle_losses)
				activity += '\n'
			if "games" in day:
				for mode, mode_data in day["games"].items():
					mode_wins = mode_data["win"]
					mode_losses = mode_data["loss"]
					mode_draws = mode_data["draw"]
					rating_before = mode_data["rp"]["before"]
					rating_after = mode_data["rp"]["after"]
					mode_index = self.modes.index(mode)
					total_matches = mode_wins + mode_losses + mode_draws
					rating_change = rating_after - rating_before
					activity += "{} Played ".format(self.mode_emojis[mode_index])
					activity += "{} ".format(total_matches)
					activity += "{} ".format(self.mode_names[mode_index])
					activity += clients.inflect_engine.plural("game", total_matches)
					activity += '\t'
					if rating_change != 0:
						activity += str(rating_after)
						if rating_change > 0:
							activity += str(self.uprightarrow_emoji)
						elif rating_change < 0:
							activity += str(self.downrightarrow_emoji)
						activity += "{}\t".format(abs(rating_change))
					if mode_wins:
						activity += "{} ".format(mode_wins)
						activity += clients.inflect_engine.plural("win", mode_wins)
						activity += ' '
					if mode_draws:
						activity += "{} ".format(mode_draws)
						activity += clients.inflect_engine.plural("draw", mode_draws)
						activity += ' '
					if mode_losses:
						activity += "{} ".format(mode_losses)
						activity += clients.inflect_engine.plural("loss", mode_losses)
					activity += '\n'
			if "posts" in day:
				for post in day["posts"]:
					activity += "{} Posted ".format(self.forum_emoji)
					activity += "{} ".format(len(post["posts"]))
					activity += clients.inflect_engine.plural("message", len(post["posts"]))
					activity += " in [{0[topicName]}](https://lichess.org{0[topicUrl]})\n".format(post)
			if "correspondenceMoves" in day:
				activity += "{} Played ".format(self.correspondence_emoji)
				activity += "{} ".format(day["correspondenceMoves"]["nb"])
				activity += clients.inflect_engine.plural("move", day["correspondenceMoves"]["nb"])
				game_count = len(day["correspondenceMoves"]["games"])
				activity += " in {}".format(game_count)
				if game_count == 15:
					activity += '+'
				activity += " correspondence "
				activity += clients.inflect_engine.plural("game", game_count)
				activity += '\n'
				# TODO: include game details?
			if "correspondenceEnds" in day:
				correspondence_wins = day["correspondenceEnds"]["score"]["win"]
				correspondence_losses = day["correspondenceEnds"]["score"]["loss"]
				correspondence_draws = day["correspondenceEnds"]["score"]["draw"]
				rating_before = day["correspondenceEnds"]["score"]["rp"]["before"]
				rating_after = day["correspondenceEnds"]["score"]["rp"]["after"]
				total_matches = correspondence_wins + correspondence_losses + correspondence_draws
				rating_change = rating_after - rating_before
				activity += "{} Completed ".format(self.correspondence_emoji)
				activity += "{} correspondence ".format(total_matches)
				activity += clients.inflect_engine.plural("game", total_matches)
				activity += '\t'
				if rating_change != 0:
					activity += str(rating_after)
					if rating_change > 0:
						activity += str(self.uprightarrow_emoji)
					elif rating_change < 0:
						activity += str(self.downrightarrow_emoji)
					activity += "{}\t".format(abs(rating_change))
				if correspondence_wins:
					activity += "{} ".format(correspondence_wins)
					activity += clients.inflect_engine.plural("win", correspondence_wins)
					activity += ' '
				if correspondence_draws:
					activity += "{} ".format(correspondence_draws)
					activity += clients.inflect_engine.plural("draw", correspondence_draws)
					activity += ' '
				if correspondence_losses:
					activity += "{} ".format(correspondence_losses)
					activity += clients.inflect_engine.plural("loss", correspondence_losses)
				activity += '\n'
				# TODO: include game details?
			if "follows" in day:
				if "in" in day["follows"]:
					follows_in = day["follows"]["in"]["ids"]
					activity += "{} Gained ".format(self.thumbsup_emoji)
					activity += "{} new ".format(day["follows"]["in"].get("nb", len(follows_in)))
					activity += clients.inflect_engine.plural("follower", len(follows_in))
					activity += "\n\t"
					activity += ", ".join(follows_in)
					activity += '\n'
				if "out" in day["follows"]:
					follows_out = day["follows"]["out"]["ids"]
					activity += "{} Started following ".format(self.thumbsup_emoji)
					activity += "{} ".format(day["follows"]["out"].get("nb", len(follows_out)))
					activity += clients.inflect_engine.plural("player", len(follows_out))
					activity += "\n\t"
					activity += ", ".join(follows_out)
					activity += '\n'
			if "tournaments" in day:
				activity += "{} Competed in ".format(self.trophy_emoji)
				activity += "{} ".format(day["tournaments"]["nb"])
				activity += clients.inflect_engine.plural("tournament", day["tournaments"]["nb"])
				activity += '\n'
				for tournament in day["tournaments"]["best"]:
					activity += "\tRanked #{} ".format(tournament["rank"])
					activity += "(top {}%) ".format(tournament["rankPercent"])
					activity += "with {} ".format(tournament["nbGames"])
					activity += clients.inflect_engine.plural("game", tournament["nbGames"])
					activity += " in [{}]".format(tournament["tournament"]["name"])
					activity += "(https://lichess.org/tournament/{})".format(tournament["tournament"]["id"])
					activity += '\n'
			if "teams" in day:
				activity += "{} Joined {} ".format(self.team_emoji, len(day["teams"]))
				activity += clients.inflect_engine.plural("team", len(day["teams"]))
				activity += "\n\t"
				teams = ["[{0[name]}](https://lichess.org{0[url]})".format(team) for team in day["teams"]]
				activity += ", ".join(teams)
				activity += '\n'
			if day.get("stream"):
				activity += "{} Hosted a live stream\n".format(self.stream_emoji)
				# TODO: add link
			# TODO: use embed limit variables
			# TODO: better method of checking total embed size?
			total_length += len(date) + len(activity)
			if total_length > 6000:
				break
			if 0 < len(activity) <= 1024:  # > 0 check necessary?
				fields.append((date, activity, False))
			elif len(activity) > 1024:
				split_index = activity.rfind('\n', 0, 1024)
				# TODO: better method of finding split index, new line could be in between section
				fields.append((date, activity[:split_index], False))
				fields.append((date + " (continued)", activity[split_index:], False))
		await ctx.embed_reply(title = username + "'s Activity", fields = fields)

