
import discord
from discord.ext import commands

import datetime
import html

import dateutil.parser
import more_itertools
import tabulate

import clients
import credentials
from utilities import checks

def setup(bot):
	bot.add_cog(Finance(bot))

class Finance:
	
	def __init__(self, bot):
		self.bot = bot

	@commands.group(invoke_without_command = True, description = "Powered by [CoinDesk](https://www.coindesk.com/price/)")
	@checks.not_forbidden()
	async def bitcoin(self, ctx, currency : str = ""):
		'''
		Bitcoin Price Index (BPI)
		To specify a currency, enter the three-character currency code (e.g. USD, GBP, EUR)
		'''
		if currency:
			async with clients.aiohttp_session.get("https://api.coindesk.com/v1/bpi/currentprice/{}".format(currency)) as resp:
				if resp.status == 404:
					error = await resp.text()
					await ctx.embed_reply(":no_entry: Error: {}".format(error))
					return
				data = await resp.json(content_type = "application/javascript")
			await ctx.embed_reply("{0[code]} {0[rate]}\nPowered by [CoinDesk](https://www.coindesk.com/price/)".format(data["bpi"][currency.upper()]), title = data["bpi"][currency.upper()]["description"], footer_text = data["disclaimer"].rstrip('.') + ". Updated", timestamp = dateutil.parser.parse(data["time"]["updated"]))
		else:
			async with clients.aiohttp_session.get("https://api.coindesk.com/v1/bpi/currentprice.json") as resp:
				data = await resp.json(content_type = "application/javascript")
			await ctx.embed_reply("Powered by [CoinDesk](https://www.coindesk.com/price/)", title = data["chartName"], fields = [(data["bpi"][currency]["description"], "{0[code]} {1}{0[rate]}".format(data["bpi"][currency], html.unescape(data["bpi"][currency]["symbol"]))) for currency in data["bpi"]], footer_text = data["disclaimer"] + ". Updated", timestamp = dateutil.parser.parse(data["time"]["updated"]))
	
	@bitcoin.command(name = "currencies")
	@checks.not_forbidden()
	async def bitcoin_currencies(self, ctx):
		'''Supported currencies for BPI conversion'''
		async with clients.aiohttp_session.get("https://api.coindesk.com/v1/bpi/supported-currencies.json") as resp:
			data = await resp.json(content_type = "text/html")
		await ctx.embed_reply(", ".join("{0[currency]} ({0[country]})".format(c) for c in data[:int(len(data) / 2)]))
		await ctx.embed_reply(", ".join("{0[currency]} ({0[country]})".format(c) for c in data[int(len(data) / 2):]))
		# TODO: paginate
	
	@bitcoin.command(name = "historical", aliases = ["history", "past", "previous", "day", "date"])
	@checks.not_forbidden()
	async def bitcoin_historical(self, ctx, date : str = "", currency : str = ""):
		'''
		Historical BPI
		Date must be in YYYY-MM-DD format (Default is yesterday)
		To specify a currency, enter the three-character currency code (e.g. USD, GBP, EUR) (Default is USD)
		'''
		# TODO: date converter
		if date:
			params = {"start": date, "end": date}
			if currency: params["currency"] = currency
		else: params = {"for": "yesterday"}
		async with clients.aiohttp_session.get("https://api.coindesk.com/v1/bpi/historical/close.json", params = params) as resp:
			if resp.status == 404:
				error = await resp.text()
				await ctx.embed_reply(":no_entry: Error: {}".format(error))
				return
			data = await resp.json(content_type = "application/javascript")
		await ctx.embed_reply("{}\nPowered by [CoinDesk](https://www.coindesk.com/price/)".format(data.get("bpi", {}).get(date, "N/A") if date else list(data["bpi"].values())[0]), footer_text = data["disclaimer"] + " Updated", timestamp = dateutil.parser.parse(data["time"]["updated"]))
	
	@commands.group(aliases = ["exchange", "rates"], invoke_without_command = True)
	@checks.not_forbidden()
	async def currency(self, ctx, against : str = "", request : str = ""):
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
	@checks.not_forbidden()
	async def currency_historical(self, ctx, date : str, against : str = "", request : str = ""):
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
	@checks.not_forbidden()
	async def currency_symbols(self, ctx):
		'''Currency symbols'''
		url = "https://data.fixer.io/api/symbols"
		params = {"access_key": credentials.fixer_io_api_key}
		async with clients.aiohttp_session.get(url, params = params) as resp:
			# TODO: handle errors
			data = await resp.json()
		if not data.get("success"):
			await ctx.embed_reply(":no_entry: Error: API Response was unsucessful")
			return
		symbols = list(data["symbols"].items())
		parts = len(tabulate.tabulate(symbols, tablefmt = "plain")) // 1024 + 1
		# TODO: use embed field limit constant
		symbols_parts = more_itertools.divide(parts, symbols)
		tabulated_symbols = tabulate.tabulate(symbols_parts[0], tablefmt = "plain")
		fields = [('Currency Symbols', clients.code_block.format(tabulated_symbols))]
		for symbols_part in symbols_parts[1:]:
			tabulated_symbols = tabulate.tabulate(symbols_part, tablefmt = "plain")
			fields.append(('Continued', clients.code_block.format(tabulated_symbols)))
		# TODO: paginate
		await ctx.embed_reply(fields = fields)
	
	async def process_currency(self, ctx, against, request, date = ""):
		params = {"access_key": credentials.fixer_io_api_key}
		if against:
			params["base"] = against
		if request:
			params["symbols"] = request.upper()
		url = "https://data.fixer.io/api/"
		url += str(date) if date else "latest"
		async with clients.aiohttp_session.get(url, params = params) as resp:
			# TODO: use ETags
			if resp.status in (404, 422):
				# TODO: handle other errors
				data = await resp.json(content_type = "text/html")
				await ctx.embed_reply(":no_entry: Error: {}".format(data["error"]))
				return
			data = await resp.json()
		if not data.get("success"):
			await ctx.embed_reply(":no_entry: Error: API Response was unsucessful")
			return
		rates = list(data["rates"].items())
		parts = len(tabulate.tabulate(rates, tablefmt = "plain", floatfmt = 'f')) // 1024 + 1
		# TODO: use embed field limit constant
		parts = max(parts, 3)
		rates_parts = more_itertools.divide(parts, rates)
		tabulated_rates = tabulate.tabulate(rates_parts[0], tablefmt = "plain", floatfmt = 'f')
		fields = [('Currency Rates', clients.code_block.format(tabulated_rates))]
		for rates_part in rates_parts[1:]:
			tabulated_rates = tabulate.tabulate(rates_part, tablefmt = "plain", floatfmt = 'f')
			fields.append(('Continued', clients.code_block.format(tabulated_rates)))
		# TODO: paginate
		timestamp = datetime.datetime.utcfromtimestamp(data["timestamp"])
		await ctx.embed_reply(title = f"Against {data['base']}", fields = fields, 
								footer_text = "Rates from", timestamp = timestamp)
	
	# TODO: Handle ServerDisconnectedError ?
	@commands.group(aliases = ["stocks"], description = "Data provided for free by [IEX](https://iextrading.com/developer).", invoke_without_command = True)
	@checks.not_forbidden()
	async def stock(self, ctx, symbol : str):
		'''
		WIP
		https://iextrading.com/api-exhibit-a
		'''
		# TODO: Add https://iextrading.com/api-exhibit-a to TOS
		async with clients.aiohttp_session.get("https://api.iextrading.com/1.0/stock/{}/price".format(symbol)) as resp:
			data = await resp.text()
		await ctx.embed_reply("{}\nData provided for free by [IEX](https://iextrading.com/developer).".format(data))
	
	@stock.command(name = "company")
	@checks.not_forbidden()
	async def stock_company(self, ctx, symbol : str):
		'''Company Information'''
		async with clients.aiohttp_session.get("https://api.iextrading.com/1.0/stock/{}/company".format(symbol)) as resp:
			data = await resp.json()
		async with clients.aiohttp_session.get("https://api.iextrading.com/1.0/stock/{}/logo".format(symbol)) as resp:
			logo_data = await resp.json()
		await ctx.embed_reply("{0[description]}\nWebsite: {0[website]}\nData provided for free by [IEX](https://iextrading.com/developer).".format(data), title = "{0[companyName]} ({0[symbol]})".format(data), fields = (("Exchange", data["exchange"]), ("Industry", data["industry"]), ("CEO", data["CEO"])), thumbnail_url = logo_data.get("url", discord.Embed.Empty))
	
	@stock.command(name = "earnings")
	@checks.not_forbidden()
	async def stock_earnings(self, ctx, symbol : str):
		'''Earnings data from the most recent reported quarter'''
		async with clients.aiohttp_session.get("https://api.iextrading.com/1.0/stock/{}/earnings".format(symbol)) as resp:
			data = await resp.json()
		report = data["earnings"][0]
		# TODO: paginate other reports
		await ctx.embed_reply(title = data["symbol"], fields = [("".join(map(lambda c: c if c.islower() else ' ' + c, key)).title().replace("E P S", "EPS"), value) for key, value in report.items()if key != "EPSReportDate"], footer_text = "EPS Report Date: {}".format(report["EPSReportDate"]))
	
	@stock.command(name = "financials")
	@checks.not_forbidden()
	async def stock_financials(self, ctx, symbol : str):
		'''Income statement, balance sheet, and cash flow data from the most recent reported quarter'''
		async with clients.aiohttp_session.get("https://api.iextrading.com/1.0/stock/{}/financials".format(symbol)) as resp:
			data = await resp.json()
		report = data["financials"][0]
		# TODO: paginate other reports
		await ctx.embed_reply(title = data["symbol"], fields = [("".join(map(lambda c: c if c.islower() else ' ' + c, key)).title().replace("And", '&'), "{:,}".format(value) if isinstance(value, int) else value) for key, value in report.items()if key != "reportDate"], footer_text = "Report Date: {}".format(report["reportDate"]))
	
	@stock.command(name = "quote")
	@checks.not_forbidden()
	async def stock_quote(self, ctx, symbol : str):
		'''WIP'''
		async with clients.aiohttp_session.get("https://api.iextrading.com/1.0/stock/{}/quote".format(symbol)) as resp:
			data = await resp.json()
		fields = [("IEX Real-Time Price", data["iexRealtimePrice"])] if "iexRealtimePrice" in data else []
		timestamp = datetime.datetime.utcfromtimestamp(data["iexLastUpdated"] / 1000) if data.get("iexLastUpdated") and data["iexLastUpdated"] != -1 else discord.Embed.Empty
		await ctx.embed_reply("{}\nData provided for free by [IEX](https://iextrading.com/developer).".format(data["companyName"]), title = data["symbol"], fields = fields, footer_text = data["primaryExchange"], timestamp = timestamp)

