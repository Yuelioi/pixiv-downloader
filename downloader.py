import asyncio
from pathlib import Path
from typing import TypedDict, Unpack

from api import PixivAPIParser
from models.api_query import SearchParamsDict

SAVE_DIR = Path("downloads")
MAX_CONCURRENT = 5


class TaskItem(TypedDict):
  url: str
  path: Path


class PixivDownloader:
  def __init__(self, token: str, proxy: str | None = None):
    self.save_dir = SAVE_DIR
    self.parser = PixivAPIParser()
    self.parser.set_token(token)
    if proxy:
      self.parser.set_proxy(proxy)

  async def __aenter__(self):
    await self.parser.__aenter__()
    return self

  async def __aexit__(self, exc_type, exc_val, exc_tb):
    await self.parser.__aexit__(exc_type, exc_val, exc_tb)

  async def download_user_illusts(self, user_id: int):
    """下载用户作品"""
    try:
      result = await self.parser.search_following(user_id)
      return result
    except Exception as e:
      print(f"下载失败: {e}")

  async def download_by_tag(self, **kwargs: Unpack[SearchParamsDict]):
    """按标签下载作品

    :param keyword: 搜索关键词
    :param p: 页码
    :param order: 排序方式 (date_d: 新到旧)
    :param mode: 安全模式 (safe: all, r18)
    :param scd: 开始时间
    :param ecd: 结束时间
    :param csw: 单页作品数
    :param s_mode: 标签匹配模式 (s_tag_full: 完全匹配)
    :param media_type: 作品类型 (all / illust / manga)
    :param wgt: 作品宽度
    :param hgt: 作品高度
    :param ratio: 纵横比
    :param ai_type: AI 插画隐藏类型 (1: 隐藏)
    :param lang: 返回语言
    """
    try:
      illusts = await self.parser.search_keyword(**kwargs)

      async def fetch_meta(illust):
        try:
          meta = await self.parser.search_illust(illust.id)
          illust.meta = meta.metas
        except Exception as e:
          print(f"获取插画 {illust.id} 的 meta 失败: {e}")

          illust.meta = []
          raise RuntimeError("获取插画 meta 失败") from e

      await asyncio.gather(*(fetch_meta(illust) for illust in illusts.Illusts))
      return illusts.Illusts, illusts.lastPage, illusts.total

    except Exception as e:
      print(f"下载失败: {e}")
      return [], 0, 0
