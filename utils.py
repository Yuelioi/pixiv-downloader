import asyncio
import hashlib
import re
import traceback
from datetime import datetime, timezone
from pathlib import Path

from tortoise.exceptions import IntegrityError
from tortoise.transactions import in_transaction

from models.api import Illust
from models.db import Image

FILENAME_MAX_LENGTH = 200


def is_token_expired(data):
  try:
    expire_time_str = data.get("expire_time")
    if not expire_time_str:
      return True  # 没有 expire_time 字段，认为已过期

    expire_time = datetime.fromisoformat(expire_time_str)
    return datetime.now() >= expire_time

  except Exception as e:
    print("检查 token 是否过期时出错：", e)
    return True


def sanitize_filename(title: str) -> str:
  """清理文件名中的非法字符"""
  # 移除特殊字符并限制长度
  clean_title = re.sub(r'[\\/*?:"<>|]', "_", title)
  return clean_title[:FILENAME_MAX_LENGTH].rstrip("_")


def make_folder(save_dir: Path, userid: int):
  return save_dir / str(userid)


def sha256_from_bytes(stream: bytes | Path) -> str:
  """对字节内容计算 SHA-256 哈希"""
  if isinstance(stream, Path):
    hash_obj = hashlib.sha256()
    with open(stream, "rb") as f:
      for chunk in iter(lambda: f.read(4096), b""):
        hash_obj.update(chunk)
    return hash_obj.hexdigest()
  else:
    hash_obj = hashlib.sha256(stream)
    return hash_obj.hexdigest()


async def create_image_from_illust(illust: Illust) -> Image:
  # 下载原图 URL 或其他可用尺寸之一

  # 创建并返回 Image 实例
  url = illust.meta[0].urls.original

  try:
    image = await Image.create(
      img_id=illust.id,
      hash="",
      p=0,
      title=illust.title,
      description=illust.description,
      tags=illust.tags,
      urls=illust.meta[0].urls.to_dict(),
      user_id=illust.user_id,
      user_name=illust.user_name,
      user_avatar=illust.profile_image_url,
      width=illust.width,
      height=illust.height,
      bookmarks=illust.bookmark_data.get("count") if illust.bookmark_data else 0,
      views=0,
      source="pixiv",
      x_restrict=illust.x_restrict,
      ai_type=illust.ai_type,
      created=illust.create_date,
      file_ext=url.split(".")[-1],
    )

  except IntegrityError:
    raise IntegrityError("图片已存在")

  return image


async def batch_create_images(illust_list: list, batch_size=100, retry_on_fail=True, max_retries=3):
  """
  批量创建图片记录（自动过滤重复项，支持出错重试）
  :param illust_list: Pixiv API返回的作品列表
  :param batch_size: 每批插入数量（建议100-500）
  :param retry_on_fail: 插入失败时是否尝试重试
  :param max_retries: 最大重试次数
  """
  if not illust_list:
    return

  image_objs = []
  illust_count = 0

  now = datetime.now(timezone.utc)

  for illust in illust_list:
    illust_count += 1
    try:
      # 提取文件扩展名
      original_url = illust.meta[0].urls.original
      file_ext = original_url.split(".")[-1].lower().split("?")[0]
      file_ext = file_ext if file_ext in ("png", "jpg", "jpeg") else "jpg"
    except Exception as e:
      print(f"⚠️ illust {illust.id} 提取文件扩展名失败：{e}")
      file_ext = "jpg"

    try:
      for page in range(illust.page_count):
        urls = illust.meta[page].urls.to_dict()
        width = illust.meta[page].width
        height = illust.meta[page].height

        image_objs.append(
          Image(
            img_id=illust.id,
            title=illust.title[:255],
            tags=illust.tags,
            meta={},
            user_id=illust.user_id,
            user_name=illust.user_name[:255],
            user_avatar=illust.profile_image_url,
            width=width,
            height=height,
            url=illust.url,
            page=page,
            urls=urls,
            description=illust.description,
            bookmarks=illust.bookmark_data.get("count", 0) if illust.bookmark_data else 0,
            views=0,
            source="pixiv",
            x_restrict=illust.x_restrict,
            ai_type=illust.ai_type,
            created=illust.create_date,
            updated=now,
            file_ext=file_ext,
            hash="",
            score=-100,
            page_count=illust.page_count,
          )
        )

      # 批量提交
      if len(image_objs) >= batch_size:
        await insert_batch(image_objs, illust_count, retry_on_fail, max_retries)
        image_objs.clear()

    except Exception as e:
      print(f"❌ 构建 illust {illust.id} 出错：{e}")
      traceback.print_exc()

  # 插入剩余未提交的
  if image_objs:
    await insert_batch(image_objs, illust_count, retry_on_fail, max_retries)


async def insert_batch(image_objs: list, i: int, retry_on_fail: bool, max_retries: int):
  retries = 0
  while retries <= max_retries:
    try:
      async with in_transaction():
        # print(f"📤 正在插入 {len(image_objs)} 条图片（进度：{i}）")
        await Image.bulk_create(image_objs, ignore_conflicts=True)
      return  # 插入成功，直接返回
    except Exception as e:
      print(f"⚠️ 批量插入失败：{e}")
      traceback.print_exc()
      retries += 1
      if retry_on_fail and retries <= max_retries:
        print(f"🔁 重试插入（{retries}/{max_retries}）...")
        await asyncio.sleep(1)  # 简单延迟
      else:
        print("🚫 放弃本批插入")
        return
