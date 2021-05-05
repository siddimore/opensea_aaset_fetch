import asyncio
import aiohttp
from aiohttp import ClientSession
from loguru import logger
import concurrent.futures

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import time

url_list = [
    "https://nftmarketcapio-v1-2021-staging.herokuapp.com/api/fetchTokens",
    "https://pg-rnd-nftmarketcapio-v1-2021.herokuapp.com/api/fetchTokens"
]

def download_file(url):
    html = requests.get(url, stream=True)
    #return (html.text)
    return html.status_code

count = 1000
tries = 0
start = time()
processes = []
with ThreadPoolExecutor(max_workers=10) as executor:
    while tries < count:
        processes.append(executor.submit(download_file, "https://nftmarketcapio-v1-2021-staging.herokuapp.com/api/fetchTokens"))
        tries=tries+1

for task in as_completed(processes):
    if task.result() == 500:
        print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print(task.result())


print(f'Time taken for {count} request : {time() - start}')

# async def fetch_html(url: str, session: ClientSession, **kwargs) -> str:
#     resp = await session.request(method="GET", url=url, **kwargs)
#     resp.raise_for_status()
#     return await resp.text()

# async def make_requests(url: str, **kwargs) -> None:
#     async with ClientSession() as session:
#         tasks = []
#         for i in range(1,1000):
#             tasks.append(
#                 fetch_html(url=url, session=session, **kwargs)
#             )
#         results = await asyncio.gather(*tasks)
#         logger.debug(results)
#         # do something with results

# if __name__ == "__main__":
#     asyncio.run(make_requests(url='https://nftmarketcapio-v1-2021-staging.herokuapp.com/api/fetchTokens'))

# from urlparse import urlparse
# from threading import Thread
# import httplib, sys
# from Queue import Queue

# concurrent = 200

# def doWork():
#     while True:
#         url = q.get()
#         status, url = getStatus(url)
#         doSomethingWithResult(status, url)
#         q.task_done()

# def getStatus(ourl):
#     try:
#         url = urlparse(ourl)
#         conn = httplib.HTTPConnection(url.netloc)   
#         conn.request("HEAD", url.path)
#         res = conn.getresponse()
#         return res.status, ourl
#     except:
#         return "error", ourl

# def doSomethingWithResult(status, url):
#     print status, url

# q = Queue(concurrent * 2)
# for i in range(concurrent):
#     t = Thread(target=doWork)
#     t.daemon = True
#     t.start()
# try:
#     for url in open('urllist.txt'):
#         q.put(url.strip())
#     q.join()
# except KeyboardInterrupt:
#     sys.exit(1)