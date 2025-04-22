import hashlib
import re
from datetime import datetime
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


async def batch_create_images(illust_list: list[Illust], batch_size=100):
  """
  批量创建图片记录（自动过滤重复项）
  :param illust_list: Pixiv API返回的作品列表
  :param batch_size: 每批插入数量（建议100-500）
  """
  if not illust_list:
    return

  image_objs = []

  # 这里可以不包一个全局事务，也可以每次 bulk_create 时启动子事务
  for illust in illust_list:
    # 提取文件扩展名
    try:
      original_url = illust.meta[0].urls.original
      file_ext = original_url.split(".")[-1].lower().split("?")[0]
      file_ext = file_ext if file_ext in ("png", "jpg", "jpeg") else "jpg"
    except Exception:
      file_ext = "jpg"

    for p in range(illust.page_count):
      image_objs.append(
        Image(
          img_id=illust.id,
          p=p,
          title=illust.title[:255],
          tags=illust.tags,
          urls=illust.meta[0] and illust.meta[0].urls.to_dict(),
          user_id=illust.user_id,
          user_name=illust.user_name[:255],
          user_avatar=illust.profile_image_url,
          width=illust.width,
          height=illust.height,
          bookmarks=illust.bookmark_data.get("count", 0) if illust.bookmark_data else 0,
          views=0,
          source="pixiv",
          x_restrict=illust.x_restrict,
          ai_type=illust.ai_type,
          created=illust.create_date,
          file_ext=file_ext,
          hash="",
        )
      )

    # 达到批量阈值，就插一次
    if len(image_objs) >= batch_size:
      async with in_transaction():
        # 忽略冲突，跳过已存在的记录
        await Image.bulk_create(image_objs, ignore_conflicts=True)
      image_objs.clear()

  # 插入剩余未提交的
  if image_objs:
    async with in_transaction():
      await Image.bulk_create(image_objs, ignore_conflicts=True)
