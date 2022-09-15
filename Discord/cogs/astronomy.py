
import discord
from discord.ext import commands, menus

import datetime
import dateutil.parser
import inspect
import io
import re
import sys
from typing import Optional

from utilities import checks
from utilities.paginators import ButtonPaginator

sys.path.insert(0, "..")
from units.time import duration_to_string
sys.path.pop(0)

async def setup(bot):
	await bot.add_cog(Astronomy(bot))

class Astronomy(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		# Add specific astronomy subcommands as commands
		for name, command in inspect.getmembers(self):
			if isinstance(command, commands.Command) and name in ("exoplanet", "iss", "observatory", "telescope"):
				self.bot.add_command(command)
		
		self.telescopes = []
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden().predicate(ctx)
	
	# TODO: random exoplanet, observatory, telescope
	
	@commands.group(aliases = ["space"], invoke_without_command = True, case_insensitive = True)
	async def astronomy(self, ctx):
		'''exoplanet, iss, observatory, and telescope are also commands as well as subcommands'''
		await ctx.send_help(ctx.command)
	
	@astronomy.command()
	async def chart(self, ctx, *, chart: str):
		'''WIP'''
		# paginate, https://api.arcsecond.io/findingcharts/HD%205980/
		...
	
	@astronomy.group(aliases = ["archive", "archives"], invoke_without_command = True, case_insensitive = True)
	async def data(self, ctx):
		'''Data Archives'''
		await ctx.send_help(ctx.command)
	
	@data.command(name = "eso")
	async def data_eso(self, ctx, program_id: str):
		'''
		European Southern Observatory
		http://archive.eso.org/wdb/wdb/eso/sched_rep_arc/query
		http://archive.eso.org/wdb/help/eso/schedule.html
		http://archive.eso.org/eso/eso_archive_main.html
		http://telbib.eso.org/
		'''
		url = f"https://api.arcsecond.io/archives/ESO/{program_id}/summary/"
		params = {"format": "json"}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			if resp.status == 404:
				return await ctx.embed_reply(":no_entry: Error: Not Found")
			data = await resp.json()
		# TODO: handle errors
		# TODO: include programme_type?, remarks?, abstract?, observer_name?
		links = []
		if data["abstract_url"]:
			links.append("[Abstract]({})".format(data["abstract_url"].replace(')', "\\)")))
		if data["raw_files_url"]:
			links.append("[Raw Files]({})".format(data["raw_files_url"].replace(')', "\\)")))
		if data["publications_url"]:
			links.append(f"[Publications]({data['publications_url']})")
		if data["programme_title"] != "(Undefined)":
			title = data["programme_title"]
		else:
			title = None
		fields = []
		if data["period"]:
			fields.append(("Period", data["period"]))
		if data["observing_mode"] != "(Undefined)":
			fields.append(("Observing Mode", data["observing_mode"]))
		if data["allocated_time"]:
			fields.append(("Allocated Time", data["allocated_time"]))
		if data["telescope_name"]:
			fields.append(("Telescope", data["telescope_name"]))
		if data["instrument_name"]:
			fields.append(("Instrument", data["instrument_name"]))
		if data["investigators_list"]:
			fields.append(("Investigators", data["investigators_list"]))
		await ctx.embed_reply('\n'.join(links), title = title, fields = fields)
	
	@data.command(name = "hst")
	async def data_hst(self, ctx, proposal_id: int):
		'''
		Hubble Space Telescope (HST)
		https://archive.stsci.edu/hst/
		'''
		async with ctx.bot.aiohttp_session.get("https://api.arcsecond.io/archives/HST/{}/summary/".format(proposal_id), params = {"format": "json"}) as resp:
			data = await resp.json()
		# TODO: include allocation?, pi_institution?, programme_type_auxiliary?, programme_status?, related_programmes?
		fields = []
		if data["cycle"]: fields.append(("Cycle", data["cycle"]))
		if data["principal_investigator"]: fields.append(("Principal Investigator", data["principal_investigator"]))
		if data["programme_type"] and data["programme_type"] != "(Undefined)": fields.append(("Proposal Type", data["programme_type"]))
		await ctx.embed_reply(data["abstract"], title = data["title"], fields = fields)
	
	@astronomy.command()
	async def exoplanet(self, ctx, *, exoplanet: str):
		'''Exoplanets'''
		# TODO: list?
		async with ctx.bot.aiohttp_session.get("https://api.arcsecond.io/exoplanets/{}".format(exoplanet), params = {"format": "json"}) as resp:
			if resp.status in (404, 500):
				await ctx.embed_reply(":no_entry: Error")
				return
			data = await resp.json()
			'''
			if resp.status == 404:
				await ctx.embed_reply(":no_entry: Error: {}".format(data["detail"]))
				return
			'''
		# TODO: include mass?, radius?, bibcodes?, omega_angle?, anomaly angle?, angular_distance?, time_radial_velocity_zero?, hottest_point_longitude?, surface_gravity?, mass_detection_method?, radius_detection_method?
		# TODO: handle one of error_min or error_max, but not other? (SWEEPS-11)
		# TODO: improve efficiency with for loop?
		fields = [("System", data["coordinates"]["system"])]
		if data["coordinates"]["right_ascension"]: fields.append(("Right Ascension", "{}{}".format(data["coordinates"]["right_ascension"], '°' if data["coordinates"]["right_ascension_units"] == "degrees" else ' ' + data["coordinates"]["right_ascension_units"])))
		if data["coordinates"]["declination"]: fields.append(("Right Declination", "{}{}".format(data["coordinates"]["declination"], '°' if data["coordinates"]["declination_units"] == "degrees" else ' ' + data["coordinates"]["declination_units"])))
		# Inclination
		inclination = ""
		if data["inclination"]["value"]: inclination += str(data["inclination"]["value"])
		if data["inclination"]["error_min"] or data["inclination"]["error_max"]:
			if data["inclination"]["error_min"] == data["inclination"]["error_max"]: inclination += '±' + str(data["inclination"]["error_min"])
			else: inclination += "(-{0[error_min]}/+{0[error_max]})".format(data["inclination"])
		if data["inclination"]["value"]: inclination += data["inclination"]["unit"]
		if inclination: fields.append(("Inclination", inclination))
		# Semi-Major Axis
		semi_major_axis = ""
		if data["semi_major_axis"]["value"]: semi_major_axis += str(data["semi_major_axis"]["value"])
		if data["semi_major_axis"]["error_min"] or data["semi_major_axis"]["error_max"]:
			if data["semi_major_axis"]["error_min"] == data["semi_major_axis"]["error_max"]: semi_major_axis += '±' + str(data["semi_major_axis"]["error_min"])
			else: semi_major_axis += "(-{0[error_min]}/+{0[error_max]})".format(data["semi_major_axis"])
		if data["semi_major_axis"]["value"]: semi_major_axis += " AU" if data["semi_major_axis"]["unit"] == "astronomical unit" else ' ' + data["semi_major_axis"]["unit"]
		if semi_major_axis: fields.append(("Semi-Major Axis", semi_major_axis))
		# Orbital Period
		# TODO: include orbital_period error_max + error_min?
		if data["orbital_period"]["value"]: fields.append(("Orbital Period", "{} {}".format(data["orbital_period"]["value"], data["orbital_period"]["unit"])))
		# Eccentricity
		eccentricity = ""
		if data["eccentricity"]["value"]: eccentricity += str(data["eccentricity"]["value"])
		if data["eccentricity"]["error_min"] or data["eccentricity"]["error_max"]:
			if data["eccentricity"]["error_min"] == data["eccentricity"]["error_max"]: eccentricity += '±' + str(data["eccentricity"]["error_min"])
			else: eccentricity += "(-{0[error_min]}/+{0[error_max]})".format(data["eccentricity"])
		if eccentricity: fields.append(("Eccentricity", eccentricity))
		# Lambda Angle
		# Spin-Orbit Misalignment
		# Sky-projected angle between the planetary orbital spin and the stellar rotational spin
		lambda_angle = ""
		lambda_angle_data = data.get("lambda_angle") or {}
		if lambda_angle_data.get("value"):
			lambda_angle += str(lambda_angle_data["value"])
		if lambda_angle_data.get("error_min") or lambda_angle_data.get("error_max"):
			if lambda_angle_data.get("error_min") == lambda_angle_data.get("error_max"):
				lambda_angle += '±' + str(lambda_angle_data["error_min"])
			else:
				lambda_angle += "(-{0[error_min]}/+{0[error_max]})".format(lambda_angle_data)
		if lambda_angle_data.get("value"):
			lambda_angle += lambda_angle_data["unit"]
		if lambda_angle:
			fields.append(("Spin-Orbit Misalignment", lambda_angle))
		# Periastron Time
		# https://exoplanetarchive.ipac.caltech.edu/docs/parhelp.html#Obs_Time_Periastron
		time_periastron = ""
		if data["time_periastron"]["value"]: time_periastron += str(data["time_periastron"]["value"])
		if data["time_periastron"]["error_min"] or data["time_periastron"]["error_max"]:
			if data["time_periastron"]["error_min"] == data["time_periastron"]["error_max"]: time_periastron += '±' + str(data["time_periastron"]["error_min"])
			else: time_periastron += "(-{0[error_min]}/+{0[error_max]})".format(data["time_periastron"]) # Necessary?
		if time_periastron: fields.append(("Periastron Time", time_periastron))
		# Conjunction Time
		time_conjonction = ""
		time_conjonction_data = data.get("time_conjonction") or {}
		if time_conjonction_data.get("value"):
			time_conjonction += str(time_conjonction_data["value"])
		if time_conjonction_data.get("error_min") or time_conjonction_data.get("error_max"):
			if time_conjonction_data.get("error_min") == time_conjonction_data("error_max"):
				time_conjonction += '±' + str(time_conjonction_data["error_min"])
			else:
				time_conjonction += "(-{0[error_min]}/+{0[error_max]})".format(time_conjonction_data) # Necessary?
		if time_conjonction:
			fields.append(("Conjunction Time", time_conjonction))
		# Primary Transit
		# in Julian Days (JD)
		primary_transit = ""
		primary_transit_data = data.get("primary_transit") or {}
		if primary_transit_data.get("value"):
			primary_transit += str(primary_transit_data["value"])
		if primary_transit_data.get("error_min") or primary_transit_data.get("error_max"):
			if primary_transit_data.get("error_min") == primary_transit_data.get("error_max"):
				primary_transit += '±' + str(primary_transit_data["error_min"])
			else:
				primary_transit += "(-{0[error_min]}/+{0[error_max]})".format(primary_transit_data) # Necessary?
		if primary_transit:
			fields.append(("Primary Transit", primary_transit))
		# Secondary Transit
		# in Julian Days (JD)
		secondary_transit = ""
		secondary_transit_data = data.get("secondary_transit") or {}
		if secondary_transit_data.get("value"):
			secondary_transit += str(secondary_transit_data["value"])
		if secondary_transit_data.get("error_min") or secondary_transit_data.get("error_max"):
			if secondary_transit_data.get("error_min") == secondary_transit_data.get("error_max"):
				secondary_transit += '±' + str(secondary_transit_data["error_min"])
			else:
				secondary_transit += "(-{0[error_min]}/+{0[error_max]})".format(secondary_transit_data)
		if secondary_transit:
			fields.append(("Secondary Transit", secondary_transit))
		# Impact Parameter
		impact_parameter = ""
		impact_parameter_data = data.get("impact_parameter") or {}
		if impact_parameter_data.get("value"):
			impact_parameter += str(impact_parameter_data["value"])
		if impact_parameter_data.get("error_min") or impact_parameter_data.get("error_max"):
			if impact_parameter_data.get("error_min") == impact_parameter_data.get("error_max"):
				impact_parameter += '±' + str(impact_parameter_data["error_min"])
			else:
				impact_parameter += "(-{0[error_min]}/+{0[error_max]})".format(impact_parameter_data) # Necessary?
		if impact_parameter_data.get("value"):
			impact_parameter += impact_parameter_data["unit"]
		if impact_parameter:
			fields.append(("Impact Parameter", impact_parameter))
		# Radial Velocity Semi-Amplitude
		velocity_semiamplitude = ""
		if data["velocity_semiamplitude"]["value"]: velocity_semiamplitude += str(data["velocity_semiamplitude"]["value"])
		if data["velocity_semiamplitude"]["error_min"] or data["velocity_semiamplitude"]["error_max"]:
			if data["velocity_semiamplitude"]["error_min"] == data["velocity_semiamplitude"]["error_max"]: velocity_semiamplitude += '±' + str(data["velocity_semiamplitude"]["error_min"])
			else: velocity_semiamplitude += "(-{0[error_min]}/+{0[error_max]})".format(data["velocity_semiamplitude"]) # Necessary?
		if data["velocity_semiamplitude"]["value"]: velocity_semiamplitude += ' ' + data["velocity_semiamplitude"]["unit"]
		if velocity_semiamplitude: fields.append(("Radial Velocity Semi-Amplitude", velocity_semiamplitude))
		# Calculated Temperature
		calculated_temperature = ""
		calculated_temperature_data = data.get("calculated_temperature") or {}
		if calculated_temperature_data.get("value"):
			calculated_temperature += str(calculated_temperature_data["value"])
		if calculated_temperature_data.get("error_min") or calculated_temperature_data.get("error_max"):
			if calculated_temperature_data.get("error_min") == calculated_temperature_data.get("error_max"):
				calculated_temperature += '±' + str(calculated_temperature_data["error_min"])
			else:
				calculated_temperature += "(-{0[error_min]}/+{0[error_max]})".format(calculated_temperature_data) # Necessary?
		if calculated_temperature_data.get("value"):
			calculated_temperature += " K" if calculated_temperature_data.get("unit") == "Kelvin" else ' ' + calculated_temperature_data.get("unit")
		if calculated_temperature:
			fields.append(("Calculated Temperature", calculated_temperature))
		# Measured Temperature
		# TODO: include measured_temperature error_max + error_min?
		measured_temperature_data = data.get("measured_temperature") or {}
		if measured_temperature_data.get("value"):
			fields.append(("Measured Temperature", "{} {}".format(measured_temperature_data["value"], 'K' if measured_temperature_data.get("unit") == "Kelvin" else measured_temperature_data.get("unit"))))
		# Geometric Albedo
		# TODO: include geometric_albedo error_max + error_min?
		if data["geometric_albedo"]["value"]: fields.append(("Geometric Albedo", data["geometric_albedo"]["value"]))
		# Detection Method
		if data["detection_method"] != "Unknown": fields.append(("Detection Method", data["detection_method"]))
		# Parent Star
		parent_star_data = data.get("parent_star") or {}
		if parent_star_data.get("name"):
			fields.append(("Parent Star", parent_star_data["name"]))
		elif parent_star_data.get("url"):
			async with ctx.bot.aiohttp_session.get(parent_star_data["url"]) as resp:
				parent_star_data = await resp.json()
			fields.append(("Parent Star", parent_star_data["name"]))
		await ctx.embed_reply(title = data["name"], fields = fields)
	
	@astronomy.command(aliases = ["international_space_station", "internationalspacestation"])
	async def iss(self, ctx, latitude: float = 0.0, longitude: float = 0.0):
		'''
		Current location of the International Space Station (ISS)
		Enter a latitude and longitude to compute an estimate of the next time the ISS will be overhead
		Overhead is defined as 10° in elevation for the observer at an altitude of 100m
		'''
		if latitude and longitude:
			url = "http://api.open-notify.org/iss-pass.json"
			params = {"n": 1, "lat": str(latitude), "lon": str(longitude)}
			async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
				if resp.status == 500:
					return await ctx.embed_reply(":no_entry: Error")
				data = await resp.json()
			if data["message"] == "failure":
				return await ctx.embed_reply(f":no_entry: Error: {data['reason']}")
			duration = duration_to_string(datetime.timedelta(seconds = data["response"][0]["duration"]))
			timestamp = datetime.datetime.utcfromtimestamp(data["response"][0]["risetime"])
			await ctx.embed_reply(fields = (("Duration", duration),), 
									footer_text = "Rise Time", timestamp = timestamp)
		else:
			url = "http://api.open-notify.org/iss-now.json"
			async with ctx.bot.aiohttp_session.get(url) as resp:
				data = await resp.json()
			latitude = data["iss_position"]["latitude"]
			longitude = data["iss_position"]["longitude"]
			timestamp = datetime.datetime.utcfromtimestamp(data["timestamp"])
			map_icon = "http://i.imgur.com/KPfeEcc.png"  # 64x64 satellite emoji png
			url = "https://maps.googleapis.com/maps/api/staticmap"
			params = {"center": f"{latitude},{longitude}", "zoom": 3, "maptype": "hybrid", "size": "640x640", 
						"markers": f"icon:{map_icon}|anchor:center|{latitude},{longitude}", 
						"key": ctx.bot.GOOGLE_API_KEY}
			async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
				data = await resp.read()
			await ctx.embed_reply(fields = (("Latitude", latitude), ("Longitude", longitude)), 
									image_url = "attachment://map.png", 
									file = discord.File(io.BytesIO(data), filename = "map.png"), 
									timestamp = timestamp)
	
	@astronomy.command(name = "object")
	async def astronomy_object(self, ctx, *, object: str):
		'''WIP'''
		# https://api.arcsecond.io/objects/alpha%20centurai/
		...
	
	@astronomy.command()
	async def observatory(self, ctx, *, observatory: str):
		'''
		Observatories
		Observing sites on Earth
		'''
		# TODO: list?
		async with ctx.bot.aiohttp_session.get("https://api.arcsecond.io/observingsites/", params = {"format": "json"}) as resp:
			data = await resp.json()
		for _observatory in data:
			if observatory.lower() in _observatory["name"].lower():
				fields = [("Latitude", _observatory["coordinates"]["latitude"]), ("Longitude", _observatory["coordinates"]["longitude"]), ("Height", "{}m".format(_observatory["coordinates"]["height"])), ("Continent", _observatory["address"]["continent"]), ("Country", _observatory["address"]["country"])]
				time_zone = "{0[time_zone_name]}\n({0[time_zone]})".format(_observatory["address"])
				if len(time_zone) <= 22: time_zone = time_zone.replace('\n', ' ') # 22: embed field value limit without offset
				fields.append(("Time Zone", time_zone))
				if _observatory["IAUCode"]: fields.append(("IAU Code", _observatory["IAUCode"]))
				telescopes = []
				for telescope in _observatory["telescopes"]:
					async with ctx.bot.aiohttp_session.get(telescope) as resp:
						telescope_data = await resp.json()
					telescopes.append(telescope_data["name"])
				if telescopes: fields.append(("Telescopes", '\n'.join(telescopes)))
				await ctx.embed_reply(title = _observatory["name"], title_url = _observatory["homepage_url"] or None, fields = fields)
				return
		await ctx.embed_reply(":no_entry: Observatory not found")
	
	@astronomy.command()
	async def people(self, ctx):
		'''Current people in space'''
		# TODO: add input/search option
		async with ctx.bot.aiohttp_session.get("http://api.open-notify.org/astros.json") as resp:
			data = await resp.json()
		await ctx.embed_reply('\n'.join("{0[name]} ({0[craft]})".format(person) for person in data["people"]), title = "Current People In Space ({})".format(data["number"]))
	
	@astronomy.command()
	async def publication(self, ctx, *, bibcode: str):
		'''Publications'''
		async with ctx.bot.aiohttp_session.get("https://api.arcsecond.io/publications/{}/".format(bibcode), params = {"format": "json"}) as resp:
			data = await resp.json()
		if not data:
			await ctx.embed_reply(":no_entry: Publication not found")
			return
		if isinstance(data, list): data = data[0]
		await ctx.embed_reply(title = data["title"], fields = (("Journal", data["journal"]), ("Year", data["year"]), ("Authors", data["authors"])))
	
	@astronomy.group(invoke_without_command = True, case_insensitive = True)
	async def telegram(self, ctx):
		'''Quick publications, often related to ongoing events occuring in the sky'''
		await ctx.send_help(ctx.command)
	
	@telegram.command(name = "atel", aliases = ["astronomerstelegram"])
	async def telegram_atel(self, ctx, number: int):
		'''
		The Astronomer's Telegram
		http://www.astronomerstelegram.org/
		'''
		# TODO: use textwrap
		async with ctx.bot.aiohttp_session.get("https://api.arcsecond.io/telegrams/ATel/{}/".format(number), params = {"format": "json"}) as resp:
			if resp.status == 500:
				await ctx.embed_reply(":no_entry: Error")
				return
			data = await resp.json()
		# TODO: include credential_certification?, authors?, referring_telegrams?, external_links?
		description = data["content"].replace('\n', ' ')
		if len(description) > 1000: description = description[:1000] + "..."
		fields = []
		if len(data["subjects"]) > 1 or data["subjects"][0] != "Undefined": fields.append(("Subjects", ", ".join(sorted(data["subjects"]))))
		related = ["[{0}](http://www.astronomerstelegram.org/?read={0})".format(related_telegram) for related_telegram in sorted(data["related_telegrams"])]
		if related:
			for i in range(0, len(related), 18):
				fields.append(("Related Telegrams", ", ".join(related[i: i + 18])))
		if data["detected_objects"]: fields.append(("Detected Objects", ", ".join(sorted(data["detected_objects"]))))
		await ctx.embed_reply(description, title = data["title"], title_url = "http://www.astronomerstelegram.org/?read={}".format(number), fields = fields)
	
	@telegram.command(name = "gcn", aliases = ["circulars"])
	async def telegram_gcn(self, ctx, number: str):
		'''
		GCN Circulars
		https://gcn.gsfc.nasa.gov/
		'''
		# TODO: use textwrap
		url = f"https://api.arcsecond.io/telegrams/GCN/Circulars/{number}/"
		params = {"format": "json"}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			if resp.status in (404, 500):
				return await ctx.embed_reply(":no_entry: Error")
			data = await resp.json()
		# TODO: include submitter?, authors?, related_circulars?, external_links?
		description = re.sub("([^\n])\n([^\n])", r"\1 \2", data["content"])
		description = re.sub(r"\n\s*\n", '\n', description)
		if len(description) > 1000:
			description = description[:1000] + "..."
		description = ctx.bot.CODE_BLOCK.format(description)
		await ctx.embed_reply(description, title = data["title"] or None, 
								title_url = f"https://gcn.gsfc.nasa.gov/gcn3/{number}.gcn3", 
								timestamp = dateutil.parser.parse(data["date"]) if data["date"] else None)
	
	@astronomy.command(aliases = ["instrument"])
	async def telescope(self, ctx, *, telescope: Optional[str]):
		'''
		Telescopes and instruments
		At observing sites on Earth
		'''
		if not self.telescopes:
			data = {"next": "https://api.arcsecond.io/telescopes/?format=json"}
			while data["next"]:
				async with ctx.bot.aiohttp_session.get(data["next"]) as resp:
					data = await resp.json()
				self.telescopes.extend(data["results"])
		
		if telescope:
			telescopes = [
				_telescope for _telescope in self.telescopes
				if telescope.lower() in _telescope["name"].lower()
			]
			if not telescopes:
				await ctx.embed_reply(
					f"{ctx.bot.error_emoji} Telescope/Instrument not found"
				)
				return
		else:
			telescopes = self.telescopes
		
		paginator = ButtonPaginator(ctx, TelescopeSource(telescopes))
		await paginator.start()
		ctx.bot.views.append(paginator)

class TelescopeSource(menus.ListPageSource):
	
	def __init__(self, telescopes):
		super().__init__(telescopes, per_page = 1)
	
	async def format_page(self, menu, telescope):
		url = f"https://api.arcsecond.io/observingsites/{telescope['observing_site']}/"
		async with menu.ctx.bot.aiohttp_session.get(url) as resp:
			observatory_data = await resp.json()
		
		embed = discord.Embed(
			title = telescope["name"],
			color = menu.ctx.bot.bot_color
		).set_author(
			name = menu.ctx.author.display_name,
			icon_url = menu.ctx.author.display_avatar.url
		).set_footer(
			text = f"In response to: {menu.ctx.message.clean_content}"
		)
		
		if observatory_url := observatory_data["homepage_url"]:
			observatory = (
				f"[{observatory_data['name']}]({observatory_url})"
			)
		else:
			observatory = observatory_data["name"]
		
		embed.add_field(
			name = "Observatory", value = observatory
		)

		if telescope["mounting"] != "Unknown":
			embed.add_field(
				name = "Mounting", value = telescope["mounting"]
			)
		
		if telescope["optical_design"] != "Unknown":
			embed.add_field(
				name = "Optical Design", value = telescope["optical_design"]
			)
		
		properties = []
		if telescope["has_active_optics"] == "true":
			properties.append("Active Optics")
		if telescope["has_adaptative_optics"] == "true":
			properties.append("Adaptative Optics")
		if telescope["has_laser_guide_star"] == "true":
			properties.append("Laser Guide Star")
		
		if properties:
			embed.add_field(
				name = "Properties", value = '\n'.join(properties)
			)
		
		return {"embed": embed}

