
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
		
		# TODO: Wait until ready
		
		# TODO: Check only within Emoji Server emojis?
		self.ultrabullet_emoji = discord.utils.get(self.bot.emojis, name = "Lichess_Ultrabullet") or ":arrow_upper_left:"
		self.bullet_emoji = discord.utils.get(self.bot.emojis, name = "Lichess_Bullet") or ":zap:"
		self.blitz_emoji = discord.utils.get(self.bot.emojis, name = "Lichess_Blitz") or ":fire:"
		self.classical_emoji = discord.utils.get(self.bot.emojis, name = "Lichess_Classical") or ":hourglass:"
		self.correspondence_emoji = discord.utils.get(self.bot.emojis, name = "Lichess_Correspondence") or ":envelope:"
		self.crazyhouse_emoji = discord.utils.get(self.bot.emojis, name = "Lichess_Crazyhouse") or ":pisces:"
		self.chess960_emoji = discord.utils.get(self.bot.emojis, name = "Lichess_Chess960") or ":game_die:"
		self.kingofthehill_emoji = discord.utils.get(self.bot.emojis, name = "Lichess_KingOfTheHill") or ":triangular_flag_on_post:"
		self.threecheck_emoji = discord.utils.get(self.bot.emojis, name = "Lichess_ThreeCheck") or ":three:"
		self.antichess_emoji = discord.utils.get(self.bot.emojis, name = "Lichess_Antichess") or ":arrows_clockwise:"
		self.atomic_emoji = discord.utils.get(self.bot.emojis, name = "Lichess_Atomic") or ":atom:"
		self.horde_emoji = discord.utils.get(self.bot.emojis, name = "Lichess_Horde") or "" # TODO: Fallback Emoji
		self.racingkings_emoji = discord.utils.get(self.bot.emojis, name = "Lichess_RacingKings") or ":checkered_flag:"
		self.training_emoji = discord.utils.get(self.bot.emojis, name = "Lichess_Training") or ":bow_and_arrow:"
		self.uprightarrow_emoji = discord.utils.get(self.bot.emojis, name = "Lichess_UpRightArrow") or ":arrow_upper_right:"
		# Also possible fallback emoji: :chart_with_upwards_trend:
		self.downrightarrow_emoji = discord.utils.get(self.bot.emojis, name = "Lichess_DownRightArrow") or ":arrow_lower_right:"
		# Also possible fallback emoji: :chart_with_downwards_trend:
		
		self.modes = ("ultraBullet", "bullet", "blitz", "classical", "correspondence", "crazyhouse", "chess960", "kingOfTheHill", "threeCheck", "antichess", "atomic", "horde", "racingKings", "puzzle")
		self.mode_names = ("Ultrabullet", "Bullet", "Blitz", "Classical", "Correspondence", "Crazyhouse", "Chess960", "King of the Hill", "Three-Check", "Antichess", "Atomic", "Horde", "Racing Kings", "Training")
		self.mode_emojis = (self.ultrabullet_emoji, self.bullet_emoji, self.blitz_emoji, self.classical_emoji, self.correspondence_emoji, self.crazyhouse_emoji, self.chess960_emoji, self.kingofthehill_emoji, self.threecheck_emoji, self.antichess_emoji, self.atomic_emoji, self.horde_emoji, self.racingkings_emoji, self.training_emoji)
		
		def user_mode_wrapper(mode, name, emoji):
			@self.user.command(name = name.lower().replace(' ', "").replace('-', ""), help = "User {} stats".format(name))
			@checks.not_forbidden()
			async def user_mode_command(ctx, username : self.LichessUser):
				prov = "?" if username["perfs"][mode].get("prov") else ""
				arrow = self.uprightarrow_emoji if username["perfs"][mode]["prog"] >= 0 else self.downrightarrow_emoji
				await ctx.embed_reply("{emoji} {name} | **Games**: {0[games]}, **Rating**: {0[rating]}{prov}±{0[rd]}, {arrow} {0[prog]}".format(username["perfs"][mode], emoji = emoji, name = name, prov = prov, arrow = arrow), title = username["username"])
			return user_mode_command
		
		for mode, name, emoji in zip(self.modes, self.mode_names, self.mode_emojis):
			setattr(self, "user_" + name.lower().replace(' ', "").replace('-', ""), user_mode_wrapper(mode, name, emoji))
	
	class LichessUser(commands.Converter):
		async def convert(self, ctx, argument):
			url = "https://en.lichess.org/api/user/{}".format(argument)
			async with clients.aiohttp_session.get(url) as resp:
				lichess_user_data = await resp.json()
			if lichess_user_data: return lichess_user_data
			else: raise BadArgument
			# await ctx.embed_reply(":no_entry: User not found")

	@commands.group()
	@checks.not_forbidden()
	async def lichess(self, ctx):
		'''WIP'''
		...
	
	@lichess.group(aliases = ["tournaments"])
	@checks.not_forbidden()
	async def tournament(self, ctx):
		'''WIP'''
		...
	
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

