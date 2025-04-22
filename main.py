import asyncio
import os
import time
from datetime import datetime, timedelta

from dotenv import load_dotenv

from db import ImageDB
from downloader import PixivDownloader
from utils import batch_create_images

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
PROXY = os.getenv("PROXY")
TOKEN = os.getenv("PHPSESSID")


async def run_scrap():
  tag = "アロナ(ブルーアーカイブ)"
  tag = "プラナ(ブルーアーカイブ)"
  tag = "キサキ(ブルーアーカイブ)"
  tag = "空崎ヒナ"
  tag = "小鳥遊ホシノ"
  tag = "聖園ミカ"
  tag = "宇沢レイサ"
  tag = "下江コハル"
  tag = "伊落マリー"
  tag = "月雪ミヤコ"
  tag = "百合園セイア"
  tag = "丹花イブキ"
  tag = "ニヤニヤ教授"
  tag = "霞沢ミユ"
  tag = "内海アオバ"
  tag = "シュポガキ"
  tag = "クズノハ(ブルーアーカイブ)"
  tag = "浅黄ムツキ"
  tag = "陸八魔アル"
  tag = "白洲アズサ"
  tag = "阿慈谷ヒフミ"
  tag = "柚鳥ナツ"
  tag = "天童アリス"
  tag = "春原ココナ"
  tag = "丹花イブキ"
  tag = "杏山カズサ"
  tag = "砂狼シロコ"
  tag = "才羽モモイ"
  tag = "飛鳥馬トキ"
  tag = "黒見セリカ"
  tag = "調月リオ"
  tag = "正義実現委員会のモブ"

  db = ImageDB()
  await db.connect()

  page = 1

  async with PixivDownloader(token=TOKEN or "", proxy=PROXY) as downloader:
    data, pages, total = await downloader.download_by_tag(
      keyword=tag,
      p=page,
    )
    if pages == 1000:
      print("🚨 爬取失败，超过 1000 页限制")
      return

    print(f" {tag}📥 {pages} 页，共 {total} 张插画")

    max_retries = 10
    retry_delay = 20

    while page <= pages:
      print(f"📥 第 {page}/{pages} 页")
      retries = 0
      while retries < max_retries:
        try:
          data, _, _ = await downloader.download_by_tag(
            keyword=tag,
            p=page,
          )
          if data:
            break
        except Exception as e:
          print(f"❌ 第 {page} 页请求出错：{e}")

        retries += 1
        print(f"🔁 第 {page} 页重试 {retries}/{max_retries} 次…")
        await asyncio.sleep(retry_delay)

      if not data:
        print(f"⚠️ 第 {page} 页数据获取失败，跳过")
        page += 1
        continue

      try:
        await batch_create_images(data)
      except Exception as e:
        print(f"❌ 第 {page} 页入库失败：{e}")

      if page % 90 == 0 and pages - page > 50:
        print("⏸️ 每 90 页暂停 30 秒，防止封 IP")
        await asyncio.sleep(30)

      page += 1

  c = await db.get_image_count()
  print("\n", c)


async def query():
  db = ImageDB()
  await db.connect()

  c = await db.get_image_count()
  print("\n", c)


if __name__ == "__main__":
  asyncio.run(run_scrap())
  # asyncio.run(query())
