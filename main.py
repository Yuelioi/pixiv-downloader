import asyncio
import os

from dotenv import load_dotenv

from db import ImageDB
from downloader import PixivDownloader
from utils import batch_create_images

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
PROXY = os.getenv("PROXY")
TOKEN = os.getenv("PHPSESSID")


async def scrap():
  # tag = "アロナ(ブルーアーカイブ)"
  tag = "プラナ(ブルーアーカイブ)"
  async with PixivDownloader(token=TOKEN or "", proxy=PROXY) as downloader:
    _, lastPage, total = await downloader.download_by_tag(keyword=tag, p=1)

    if lastPage > 1000:
      raise Exception("超过最大页数限制")

    if total == 0:
      raise Exception("没有找到相关作品")

    print(f"共 {total} 张插画，{lastPage} 页")

    illusts = []

    page = 75

    while True:
      data, _, _ = await downloader.download_by_tag(keyword=tag, p=page)

      if not data:
        break

      if page > lastPage:
        break

      print(f"正在下载第 {page} 页", flush=True)

      page += 1
      illusts.extend(data)

    print(f"共 {len(illusts)} 张插画")

    await batch_create_images(illusts)


async def query():
  db = ImageDB()
  await db.connect()


if __name__ == "__main__":
  # asyncio.run(scrap())
  asyncio.run(query())
