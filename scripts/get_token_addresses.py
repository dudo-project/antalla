import json
import asyncio
import logging
import time
import re

from bs4 import BeautifulSoup

import aiohttp

URL_TEMPLATE = "https://etherscan.io/tokens?ps=100&p={page}"


def get_tokens_from_content(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    transfers = soup.find("div", id="transfers")
    if not transfers or not transfers.table:
        return {}
    rows = transfers.table.tbody.find_all("tr")
    tokens = {}
    for row in rows:
        address = row.a["href"].split("/")[-1]
        token_match = re.search(r"\(([A-Za-z0-9]+)\)", row.a.text)
        if not token_match:
            logging.warning("could not find token name for {0}".format(row.a.text))
            continue
        token = token_match.group(1)
        tokens[token] = address
    return tokens


async def get_tokens(session):
    page = 1
    tokens = {}
    while True:
        async with session.get(URL_TEMPLATE.format(page=page)) as r:
            if r.status != 200:
                logging.info("failed at page %s with code %s", page, r.status)
                break
            content = await r.text()
        page_tokens = get_tokens_from_content(content)
        if not page_tokens:
            break
        tokens.update(page_tokens)
        page += 1
        logging.info("sleep 3s, hoping for cloudflare to be nice")
        time.sleep(3)

    return tokens

async def run():
    async with aiohttp.ClientSession() as session:
        tokens = await get_tokens(session)
    with open("tokens.json", "w") as f:
        json.dump(tokens, f)


def main():
    asyncio.get_event_loop().run_until_complete(run())


if __name__ == "__main__":
    main()
