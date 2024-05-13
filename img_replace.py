import re

# from requests import Response, Session
from aiohttp import ClientError, ClientResponse, ClientSession
from bs4 import BeautifulSoup
import requests

from write_file import write_log


class ReplaceImg:
    @staticmethod
    def replaceimg(ean: str, imgs: list[str]) -> dict[str:str]:
        payload = list(
            {img_url + ">|<" + ean: "" for img_url in imgs if "assets" in img_url}
        )
        data = {"imgs": payload}
        print(payload) #test
        print("\n\n")
        page_content = ReplaceImg.get_new_urls(data, ean)
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
        print(replace_table) #test
        print("\n\n")
        return replace_table

    @staticmethod
    def get_new_urls(data, ean) -> ClientResponse:
        s = requests.Session()
        r = s.post("http://10.0.69.227:54390",
                data={"textarea":ean},
                headers={
                    "Origin": "http://10.0.69.227:54390",
                    "Referer": "http://10.0.69.227:54390",
                })
        print(r.status_code, "\n", r.text)
        try:
            response = s.post(
                "http://10.0.69.227:54390",
                data=data,
                headers={
                    "Origin": "http://10.0.69.227:54390",
                    "Referer": "http://10.0.69.227:54390/multi",
                },
            )
            print(response.status_code, "\n", response.text)
            if response.status_code<400:
                return response.content()
        except ConnectionError as e:
            write_log(exc_type=e, exc_trace=e.__traceback__)
            print(e)

        return ""
