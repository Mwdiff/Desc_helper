import re

# from requests import Response, Session
from aiohttp import ClientError, ClientResponse, ClientSession
from bs4 import BeautifulSoup

from write_file import write_log


class ReplaceImg:
    @staticmethod
    async def replaceimg(ean: str, imgs: list[str]) -> dict[str:str]:
        payload = list(
            {img_url + ">|<" + ean: "" for img_url in imgs if "assets" in img_url}
        )
        data = {imgs: payload}
        page_content = await ReplaceImg.get_new_urls(data)
        if not page_content:
            return {}

        page = BeautifulSoup(page_content, "lxml")
        sections = page.find_all("div", class_="summary_item")
        replace_table = {
            img.find("a", text="Oryginalny link")
            .get("href"): img.find("a", text=re.compile(r"Large"))
            .get("href")
            for img in sections
        }
        return replace_table

    @staticmethod
    async def get_new_urls(data) -> ClientResponse:
        try:
            with ClientSession() as session:
                response = await session.request(
                    "POST",
                    "10.0.69.227:54390",
                    data=data,
                    headers={
                        "Origin": "http://10.0.69.227:54390",
                        "Referer": "http://10.0.69.227:54390/multi",
                    },
                )
            if response.ok:
                return response.content.read()
        except ClientError as e:
            write_log(exc_type=e, exc_trace=e.__traceback__)
            print(e)

        return ""
