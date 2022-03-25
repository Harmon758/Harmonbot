
from discord.ext import commands

import datetime
import html
import math
import re
import textwrap

import dateutil.parser
import more_itertools
import tabulate

from utilities import checks

async def setup(bot):
	await bot.add_cog(Finance(bot))

class Finance(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden().predicate(ctx)
	
	@commands.group(description = "Powered by [CoinDesk](https://www.coindesk.com/price/)", 
					invoke_without_command = True, case_insensitive = True)
	async def bitcoin(self, ctx, currency: str = ""):
		'''
		Bitcoin Price Index (BPI)
		To specify a currency, enter the three-character currency code (e.g. USD, GBP, EUR)
		'''
		if currency:
			url = "https://api.coindesk.com/v1/bpi/currentprice/" + currency
			async with ctx.bot.aiohttp_session.get(url) as resp:
				if resp.status == 404:
					error = await resp.text()
					return await ctx.embed_reply(":no_entry: Error: " + error)
				data = await resp.json(content_type = "application/javascript")
			currency_data = data["bpi"][currency.upper()]
			title = currency_data["description"]
			description = f"{currency_data['code']} {currency_data['rate']}\n"
			fields = ()
		else:
			url = "https://api.coindesk.com/v1/bpi/currentprice.json"
			async with ctx.bot.aiohttp_session.get(url) as resp:
				data = await resp.json(content_type = "application/javascript")
			title = data["chartName"]
			description = ""
			fields = []
			for currency in data["bpi"].values():
				field_value = f"{currency['code']} {html.unescape(currency['symbol'])}{currency['rate']}"
				fields.append((currency["description"], field_value))
		description += "Powered by [CoinDesk](https://www.coindesk.com/price/)"
		footer_text = data["disclaimer"].rstrip('.') + ". Updated"
		timestamp = dateutil.parser.parse(data["time"]["updated"])
		await ctx.embed_reply(description, title = title, fields = fields, 
								footer_text = footer_text, timestamp = timestamp)
	
	@bitcoin.command(name = "currencies")
	async def bitcoin_currencies(self, ctx):
		'''Supported currencies for BPI conversion'''
		async with ctx.bot.aiohttp_session.get("https://api.coindesk.com/v1/bpi/supported-currencies.json") as resp:
			data = await resp.json(content_type = "text/html")
		await ctx.embed_reply(", ".join("{0[currency]} ({0[country]})".format(c) for c in data[:int(len(data) / 2)]))
		await ctx.embed_reply(", ".join("{0[currency]} ({0[country]})".format(c) for c in data[int(len(data) / 2):]))
		# TODO: paginate
	
	@bitcoin.command(name = "historical", aliases = ["history", "past", "previous", "day", "date"])
	async def bitcoin_historical(self, ctx, date: str = "", currency: str = ""):
		'''
		Historical BPI
		Date must be in YYYY-MM-DD format (Default is yesterday)
		To specify a currency, enter the three-character currency code
		(e.g. USD, GBP, EUR) (Default is USD)
		'''
		# TODO: date converter
		if date:
			params = {"start": date, "end": date}
			if currency:
				params["currency"] = currency
		else:
			params = {"for": "yesterday"}
		url = "https://api.coindesk.com/v1/bpi/historical/close.json"
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			if resp.status == 404:
				error = await resp.text()
				await ctx.embed_reply(":no_entry: Error: " + error)
				return
			data = await resp.json(content_type = "application/javascript")
		if date:
			description = str(data.get("bpi", {}).get(date, "N/A"))
		else:
			description = str(list(data["bpi"].values())[0])
		description += "\nPowered by [CoinDesk](https://www.coindesk.com/price/)"
		footer_text = data["disclaimer"] + " Updated"
		timestamp = dateutil.parser.parse(data["time"]["updated"])
		await ctx.embed_reply(description, footer_text = footer_text, timestamp = timestamp)
	
	@commands.group(aliases = ["exchange", "rates"], invoke_without_command = True, case_insensitive = True)
	async def currency(self, ctx, against: str = "", request: str = ""):
		'''
		Current foreign exchange rates
		Hourly Updates
		Exchange rate data delivered is collected from over 15 reliable data sources
		Sources include banks and financial data providers
		All exchange rate data delivered is midpoint data
		Midpoint rates are determined by calculating the average 
		median rate of Bid and Ask at a certain time
		[against]: currency to quote against (base) (default is EUR)
		[request]: currencies to request rate for (separated by commas with no spaces)
		To specify a currency, enter the three-character currency code (e.g. USD, GBP, EUR)
		'''
		# TODO: acknowledge Fixer
		await self.process_currency(ctx, against, request)
	
	@currency.command(name = "historical", aliases = ["history", "past", "previous", "day", "date"])
	async def currency_historical(self, ctx, date: str, against: str = "", request: str = ""):
		'''
		Historical foreign exchange rates
		End Of Day historical exchange rates, which become available at 00:05 am GMT 
		for the previous day and are time stamped at one second before midnight
		Date must be in YYYY-MM-DD format
		[against]: currency to quote against (base) (default is EUR)
		[request]: currencies to request rate for (separated by commas with no spaces)
		To specify a currency, enter the three-character currency code (e.g. USD, GBP, EUR)
		'''
		# TODO: date converter
		await self.process_currency(ctx, against, request, date)
	
	@currency.command(name = "symbols", aliases = ["acronyms", "abbreviations"])
	async def currency_symbols(self, ctx):
		'''Currency symbols'''
		url = "http://data.fixer.io/api/symbols"
		params = {"access_key": ctx.bot.FIXER_API_KEY}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			# TODO: handle errors
			data = await resp.json()
		if not data.get("success"):
			return await ctx.embed_reply(":no_entry: Error: API Response was unsucessful")
		symbols = list(data["symbols"].items())
		tabulated_symbols = tabulate.tabulate(symbols, tablefmt = "plain").split('\n')
		fields = []
		while tabulated_symbols:
			formatted_symbols = ""
			if not len(fields) % 3:
				inline_field_count = min(math.ceil((len('\n'.join(tabulated_symbols)) + 8) / ctx.bot.EFVCL), 3)
				# 8 = len("```\n" + "\n```") for code block
				# EFVCL = Embed Field Value Character Limit
				# TODO: Handle possibility of textwrap indents increasing inline field count by 1 when < 3?
			while tabulated_symbols and len(
				formatted_symbols + (
					formatted_line := '\n'.join(textwrap.wrap(tabulated_symbols[0], 
																ctx.bot.EDCBRCL // inline_field_count, 
																subsequent_indent = ' ' * 5))
				)
			) < ctx.bot.EMBED_FIELD_VALUE_CHARACTER_LIMIT - 8:
			# EDCBRCL = Embed Description Code Block Row Character Limit
			# 5 = len(symbol + "  "), e.g. "USD  "
				formatted_symbols += '\n' + formatted_line
				tabulated_symbols.pop(0)
			if fields:
				fields.append((ctx.bot.ZERO_WIDTH_SPACE, ctx.bot.CODE_BLOCK.format(formatted_symbols)))
				# Zero-width space for empty field title
			else:
				fields.append(("Currency Symbols", ctx.bot.CODE_BLOCK.format(formatted_symbols)))
		# TODO: paginate
		await ctx.embed_reply(fields = fields)
	
	async def process_currency(self, ctx, against, request, date = ""):
		params = {"access_key": ctx.bot.FIXER_API_KEY}
		if against:
			params["base"] = against
		if request:
			params["symbols"] = request.upper()
		url = "http://data.fixer.io/api/"
		url += str(date) if date else "latest"
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			# TODO: use ETags
			if resp.status in (404, 422):
				# TODO: handle other errors
				data = await resp.json(content_type = "text/html")
				return await ctx.embed_reply(f":no_entry: Error: {data['error']}")
			data = await resp.json()
		if not data.get("success"):
			# TODO: Include error message
			return await ctx.embed_reply(":no_entry: Error: API Response was unsucessful")
		rates = list(data["rates"].items())
		parts = len(tabulate.tabulate(rates, tablefmt = "plain", floatfmt = 'f')) // ctx.bot.EFVCL + 1
		# EFVCL = Embed Field Value Character Limit
		if len(rates) >= 3:
			parts = max(parts, 3)
		rates_parts = more_itertools.divide(parts, rates)
		tabulated_rates = tabulate.tabulate(rates_parts[0], tablefmt = "plain", floatfmt = 'f')
		field_title = f"Currency {ctx.bot.inflect_engine.plural('Rate', len(rates))} Against {data['base']}"
		fields = [(field_title, ctx.bot.CODE_BLOCK.format(tabulated_rates))]
		for rates_part in rates_parts[1:]:
			tabulated_rates = tabulate.tabulate(rates_part, tablefmt = "plain", floatfmt = 'f')
			fields.append((ctx.bot.ZERO_WIDTH_SPACE, ctx.bot.CODE_BLOCK.format(tabulated_rates)))
			# Zero-width space for empty field title
		# TODO: paginate
		footer_text = ctx.bot.inflect_engine.plural("Rate", len(rates)) + " from"
		timestamp = datetime.datetime.utcfromtimestamp(data["timestamp"])
		await ctx.embed_reply(fields = fields, footer_text = footer_text, timestamp = timestamp)
	
	# TODO: Handle ServerDisconnectedError ?
	@commands.group(aliases = ["stocks"], 
					description = "Data provided for free by [IEX](https://iextrading.com/developer).", 
					invoke_without_command = True, case_insensitive = True)
	async def stock(self, ctx, symbol: str):
		'''
		WIP
		https://iextrading.com/api-exhibit-a
		'''
		# TODO: Add https://iextrading.com/api-exhibit-a to TOS
		url = f"https://api.iextrading.com/1.0/stock/{symbol}/price"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.text()
		attribution = "\nData provided for free by [IEX](https://iextrading.com/developer)."
		await ctx.embed_reply(data + attribution)
	
	@stock.command(name = "company")
	async def stock_company(self, ctx, symbol: str):
		'''Company Information'''
		url = f"https://api.iextrading.com/1.0/stock/{symbol}/company"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.json()
		url = f"https://api.iextrading.com/1.0/stock/{symbol}/logo"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			logo_data = await resp.json()
		description = f"{data['description']}\nWebsite: {data['website']}"
		attribution = "\nData provided for free by [IEX](https://iextrading.com/developer)."
		title = f"{data['companyName']} ({data['symbol']})"
		fields = (("Exchange", data["exchange"]), ("Industry", data["industry"]), ("CEO", data["CEO"]))
		thumbnail_url = logo_data.get("url")
		await ctx.embed_reply(description + attribution, title = title, 
								fields = fields, thumbnail_url = thumbnail_url)
	
	@stock.command(name = "earnings")
	async def stock_earnings(self, ctx, symbol: str):
		'''Earnings data from the most recent reported quarter'''
		url = f"https://api.iextrading.com/1.0/stock/{symbol}/earnings"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.json()
		report = data["earnings"][0]
		# TODO: paginate other reports
		fields = []
		for key, value in report.items():
			if key != "EPSReportDate":
				# Add spaces: l( )U and U( )Ul [l = lowercase, U = uppercase]
				field_title = re.sub(r"([a-z](?=[A-Z])|[A-Z](?=[A-Z][a-z]))", r'\1 ', key)
				# Capitalize first letter
				field_title = field_title[0].upper() + field_title[1:]
				fields.append((field_title, value))
		footer_text = "EPS Report Date: " + report["EPSReportDate"]
		await ctx.embed_reply(title = data["symbol"], fields = fields, footer_text = footer_text)
	
	@stock.command(name = "financials")
	async def stock_financials(self, ctx, symbol: str):
		'''Income statement, balance sheet, and cash flow data from the most recent reported quarter'''
		url = f"https://api.iextrading.com/1.0/stock/{symbol}/financials"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.json()
		report = data["financials"][0]
		# TODO: paginate other reports
		fields = []
		for key, value in report.items():
			if key != "reportDate":
				# Add spaces: l( )U and U( )Ul [l = lowercase, U = uppercase]
				field_title = re.sub(r"([a-z](?=[A-Z])|[A-Z](?=[A-Z][a-z]))", r'\1 ', key)
				# Capitalize first letter
				field_title = field_title[0].upper() + field_title[1:]
				# Replace And with & to fit Research And Development into field title nicely
				field_title = field_title.replace("And", '&')
				if isinstance(value, int):
					value = f"{value:,}"
				fields.append((field_title, value))
		footer_text = "Report Date: " + report["reportDate"]
		await ctx.embed_reply(title = data["symbol"], fields = fields, footer_text = footer_text)
	
	@stock.command(name = "quote")
	async def stock_quote(self, ctx, symbol: str):
		'''WIP'''
		url = f"https://api.iextrading.com/1.0/stock/{symbol}/quote"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.json()
		description = data["companyName"] + "\nData provided for free by [IEX](https://iextrading.com/developer)."
		fields = []
		if "iexRealtimePrice" in data:
			fields.append(("IEX Real-Time Price", data["iexRealtimePrice"]))
		timestamp = None
		iex_last_updated = data.get("iexLastUpdated")
		if iex_last_updated and iex_last_updated != -1:
			timestamp = datetime.datetime.utcfromtimestamp(iex_last_updated / 1000)
		await ctx.embed_reply(description, title = data["symbol"], fields = fields, 
								footer_text = data["primaryExchange"], timestamp = timestamp)

