
import discord
from discord.ext import commands

import datetime
import sys

import emoji
import pycountry

from utilities import checks

sys.path.insert(0, "..")
from units.time import duration_to_string
sys.path.pop(0)

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
		if data.get("closed"):
			raise commands.BadArgument("This account is closed")
		return data

class Lichess(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		
		self.modes = ("ultraBullet", "bullet", "blitz", "rapid", "classical", "correspondence", 
						"crazyhouse", "chess960", "kingOfTheHill", "threeCheck", "antichess", 
						"atomic", "horde", "racingKings", "puzzle")
		self.mode_names = ("Ultrabullet", "Bullet", "Blitz", "Rapid", "Classical", "Correspondence", 
							"Crazyhouse", "Chess960", "King of the Hill", "Three-Check", "Antichess", 
							"Atomic", "Horde", "Racing Kings", "Training")
		
		self.load_emoji()
		self.generate_user_mode_commands()
	
	@commands.Cog.listener()
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
		self.horde_emoji = discord.utils.get(self.bot.emojis, name = "lichess_horde") or ""  # TODO: Fallback Emoji
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
		self.mode_emojis = (self.ultrabullet_emoji, self.bullet_emoji, self.blitz_emoji, 
							self.rapid_emoji, self.classical_emoji, self.correspondence_emoji, 
							self.crazyhouse_emoji, self.chess960_emoji, self.kingofthehill_emoji, 
							self.threecheck_emoji, self.antichess_emoji, self.atomic_emoji, 
							self.horde_emoji, self.racingkings_emoji, self.training_emoji)
	
	def generate_user_mode_commands(self):
		# Creates user subcommand for a mode
		def user_mode_wrapper(mode, name, emoji):
			async def user_mode_command(ctx, username : LichessUser):
				mode_data = username["perfs"][mode]
				prov = ""
				if username["perfs"][mode].get("prov"):
					prov = '?'
				if username["perfs"][mode]["prog"] >= 0:
					arrow = self.uprightarrow_emoji
				else:
					arrow = self.downrightarrow_emoji
				await ctx.embed_reply(f"{emoji} {name} | **Games**: {mode_data['games']}, "
										f"**Rating**: {mode_data['rating']}{prov}±{mode_data['rd']} "
										f"{arrow} {mode_data['prog']}", 
										title = username["username"])
			return user_mode_command
		# Generate user subcommands for each mode
		for mode, name, emoji in zip(self.modes, self.mode_names, self.mode_emojis):
			internal_name = name.lower().replace(' ', "").replace('-', "")
			# Remove existing command in cases where already generated
			# Such as on ready after cog initialized
			self.user.remove_command(internal_name)
			command = commands.Command(user_mode_wrapper(mode, name, emoji), 
										name = name.lower().replace(' ', "").replace('-', ""), 
										help = f"User {name} stats", checks = [checks.not_forbidden().predicate])
			setattr(self, "user_" + internal_name, command)
			self.user.add_command(command)
	
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
			value = (f"{tournament['clock']['limit'] / 60:g}+{tournament['clock']['increment']} "
						f"{tournament['perf']['name']} {'Rated' if tournament['rated'] else 'Casual'}"
						f"\nEnds in: {(finishes_at - datetime.datetime.utcnow()).total_seconds() // 60:g}m"
						# TODO: Use 'h' for hours?
						f"\n[Link](https://en.lichess.org/tournament/{tournament['id']})")
			fields.append((tournament["fullName"], value))
		await ctx.embed_reply(title = "Current Lichess Tournaments", fields = fields)
	
	@lichess.group(aliases = ["stats", "statistics", "stat", "statistic"], 
					invoke_without_command = True, case_insensitive = True)
	async def user(self, ctx, username : LichessUser):
		'''User stats'''
		# TODO: Separate stats subcommand?
		title = username.get("title", "") + ' ' + username["username"]
		fields = []
		for mode, name, emoji in zip(self.modes, self.mode_names, self.mode_emojis):
			if not username["perfs"].get(mode, {}).get("games", 0):
				continue
			mode_data = username["perfs"][mode]
			prov = ""
			if username["perfs"][mode].get("prov"):
				prov = '?'
			if username["perfs"][mode]["prog"] >= 0:
				arrow = self.uprightarrow_emoji
			else:
				arrow = self.downrightarrow_emoji
			value = (f"Games: {mode_data['games']}\nRating:\n"
						f"{mode_data['rating']}{prov} ± {mode_data['rd']} {arrow} {mode_data['prog']}")
			fields.append((str(emoji) + ' ' + name, value))
		if "seenAt" in username:
			footer_text = "Last seen"
			timestamp = datetime.datetime.utcfromtimestamp(username["seenAt"] / 1000.0)
		else:
			footer_text = timestamp = discord.Embed.Empty
		await ctx.embed_reply(title = title, title_url = username["url"], fields = fields, 
								footer_text = footer_text, timestamp = timestamp)
	
	@user.command(name = "activity")
	async def user_activity(self, ctx, username : str):
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
					activity += (f"{self.practice_emoji} Practiced {practice['nbPositions']} positions on "
									f"[{practice['name']}](https://lichess.org{practice['url']})\n")
			if "puzzles" in day:
				puzzle_wins = day["puzzles"]["score"]["win"]
				puzzle_losses = day["puzzles"]["score"]["loss"]
				puzzle_draws = day["puzzles"]["score"]["draw"]
				rating_before = day["puzzles"]["score"]["rp"]["before"]
				rating_after = day["puzzles"]["score"]["rp"]["after"]
				total_puzzles = puzzle_wins + puzzle_losses + puzzle_draws
				rating_change = rating_after - rating_before
				activity += (f"{self.training_emoji} Solved {total_puzzles} tactical "
								f"{ctx.bot.inflect_engine.plural('puzzle', total_puzzles)}\t")
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
					mode_index = self.modes.index(mode)
					total_matches = mode_wins + mode_losses + mode_draws
					rating_change = rating_after - rating_before
					activity += (f"{self.mode_emojis[mode_index]} Played {total_matches} "
									f"{self.mode_names[mode_index]} "
									f"{ctx.bot.inflect_engine.plural('game', total_matches)}\t")
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
					activity += (f"{self.forum_emoji} Posted {len(post['posts'])} "
									f"{ctx.bot.inflect_engine.plural('message', len(post['posts']))}"
									f" in [{post['topicName']}](https://lichess.org{post['topicUrl']})\n")
			if "correspondenceMoves" in day:
				activity += (f"{self.correspondence_emoji} Played {day['correspondenceMoves']['nb']} "
								f"{ctx.bot.inflect_engine.plural('move', day['correspondenceMoves']['nb'])}")
				game_count = len(day["correspondenceMoves"]["games"])
				activity += f" in {game_count}"
				if game_count == 15:
					activity += '+'
				activity += f" correspondence {ctx.bot.inflect_engine.plural('game', game_count)}\n"
				# TODO: Include game details?
			if "correspondenceEnds" in day:
				correspondence_wins = day["correspondenceEnds"]["score"]["win"]
				correspondence_losses = day["correspondenceEnds"]["score"]["loss"]
				correspondence_draws = day["correspondenceEnds"]["score"]["draw"]
				rating_before = day["correspondenceEnds"]["score"]["rp"]["before"]
				rating_after = day["correspondenceEnds"]["score"]["rp"]["after"]
				total_matches = correspondence_wins + correspondence_losses + correspondence_draws
				rating_change = rating_after - rating_before
				activity += (f"{self.correspondence_emoji} Completed {total_matches} correspondence "
								f"{ctx.bot.inflect_engine.plural('game', total_matches)}\t")
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
					activity += (f"{self.thumbsup_emoji} Gained "
									f"{day['follows']['in'].get('nb', len(follows_in))} new "
									f"{ctx.bot.inflect_engine.plural('follower', len(follows_in))}"
									f"\n\t{', '.join(follows_in)}\n")
				if "out" in day["follows"]:
					follows_out = day["follows"]["out"]["ids"]
					activity += (f"{self.thumbsup_emoji} Started following "
									f"{day['follows']['out'].get('nb', len(follows_out))} "
									f"{ctx.bot.inflect_engine.plural('player', len(follows_out))}"
									f"\n\t{', '.join(follows_out)}\n")
			if "tournaments" in day:
				activity += (f"{self.trophy_emoji} Competed in {day['tournaments']['nb']} "
								f"{ctx.bot.inflect_engine.plural('tournament', day['tournaments']['nb'])}\n")
				for tournament in day["tournaments"]["best"]:
					activity += (f"\tRanked #{tournament['rank']} (top {tournament['rankPercent']}%) "
									f"with {tournament['nbGames']} "
									f"{ctx.bot.inflect_engine.plural('game', tournament['nbGames'])}"
									f" in [{tournament['tournament']['name']}]"
									f"(https://lichess.org/tournament/{tournament['tournament']['id']})\n")
			if "teams" in day:
				activity += (f"{self.team_emoji} Joined {len(day['teams'])} "
								f"{ctx.bot.inflect_engine.plural('team', len(day['teams']))}\n\t")
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
	async def user_games(self, ctx, username : LichessUser):
		'''User games'''
		title = username.get("title", "") + ' ' + username["username"]
		fields = (("Games", username["count"]["all"]), 
					("Rated", username["count"]["rated"]), 
					("Wins", username["count"]["win"]), 
					("Losses", username["count"]["loss"]), 
					("Draws", username["count"]["draw"]), 
					("Playing", username["count"]["playing"]), 
					("Bookmarks", username["count"]["bookmark"]), 
					("Imported", username["count"]["import"]), 
					("AI", username["count"]["ai"]))
		if "seenAt" in username:
			footer_text = "Last seen"
			timestamp = datetime.datetime.utcfromtimestamp(username["seenAt"] / 1000.0)
		else:
			footer_text = timestamp = discord.Embed.Empty
		await ctx.embed_reply(title = title, title_url = username["url"], fields = fields, 
								footer_text = footer_text, timestamp = timestamp)
	
	@user.command(name = "profile", aliases = ["bio"])
	async def user_profile(self, ctx, username : LichessUser):
		'''User profile'''
		user_data = username
		title = user_data.get("title", "") + ' ' + user_data["username"]
		description = None
		fields = []
		profile = user_data.get("profile", {})
		if "firstName" in profile or "lastName" in profile:
			fields.append((f"{profile.get('firstName', '')} {profile.get('lastName', '')}", 
							profile.get("bio"), False))
		else:
			description = profile.get("bio")
		fields.append(("Online", "Yes" if user_data["online"] else "No"))
		fields.append(("Patron", "Yes" if user_data.get("patron") else "No"))
		if "fideRating" in profile:
			fields.append(("FIDE Rating", profile["fideRating"]))
		if "uscfRating" in profile:
			fields.append(("USCF Rating", profile["uscfRating"]))
		# TODO: Add ECF Rating
		if "country" in profile:
			country = profile["country"]
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
		fields.append(("Followers", user_data["nbFollowers"]))
		fields.append(("Following", user_data["nbFollowing"]))
		playtime = user_data.get("playTime", {})
		if "total" in playtime:
			fields.append(("Time Spent Playing", 
							duration_to_string(datetime.timedelta(seconds = playtime["total"]), abbreviate = True)))
		if tv_time := playtime.get("tv"):
			fields.append(("Time On TV", 
							duration_to_string(datetime.timedelta(seconds = tv_time), abbreviate = True)))
		if "links" in profile:
			fields.append(("Links", profile["links"], False))
		if "seenAt" in user_data:
			footer_text = "Last seen"
			timestamp = datetime.datetime.utcfromtimestamp(user_data["seenAt"] / 1000.0)
		else:
			footer_text = timestamp = discord.Embed.Empty
		await ctx.embed_reply(description, title = title, title_url = user_data["url"], 
								fields = fields, footer_text = footer_text, timestamp = timestamp)

