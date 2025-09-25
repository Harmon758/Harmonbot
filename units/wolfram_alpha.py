
from wolframalpha import Client, Document

import httpx
import multidict
import xmltodict


# https://github.com/jaraco/wolframalpha/issues/35

async def aquery_monkey_patch(self, input, params=(), **kwargs):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            self.url,
            params=multidict.MultiDict(
                params, appid=self.app_id, input=input, **kwargs
            ),
        )
    # assert resp.headers['Content-Type'] == 'text/xml;charset=utf-8'
    doc = xmltodict.parse(resp.content, postprocessor=Document.make)
    return doc['queryresult']

Client.aquery = aquery_monkey_patch

