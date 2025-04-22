import asyncio
import urllib.parse
from typing import Any, Dict, Optional, Unpack

import aiohttp
from anyio import Path

from models.api import (
  SearchArtWorkResult,
  SearchIllustMetaResult,
  SearchUserResult,
)
from models.api_query import SearchParams, SearchParamsDict

userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"


class PixivAPIError(Exception):
  """Pixiv API 异常基类"""

  pass


class NetworkError(PixivAPIError):
  """网络请求异常"""

  pass


class APIResponseError(PixivAPIError):
  """API 响应异常"""

  pass


class PixivAPIParser:
  """
  Pixiv API 解析器

  :param headers: 请求头，必须包含有效的 cookie
  :param proxy: 代理地址，例如 "http://127.0.0.1:10808"
  :param timeout: 请求超时时间（秒）
  """

  def __init__(
    self,
    headers: Dict[str, str] = {},
    timeout: int = 10,
  ):
    base_headers = {
      "referer": "https://www.pixiv.net/",
      "origin": "https://www.pixiv.net",
      "user-agent": userAgent,
    }
    self.headers = {**base_headers, **headers}
    self.timeout = timeout
    self._session: Optional[aiohttp.ClientSession] = None

  async def __aenter__(self) -> "PixivAPIParser":
    return self

  async def __aexit__(self, exc_type, exc_val, exc_tb):
    await self.close()

  async def _get_session(self) -> aiohttp.ClientSession:
    """获取或创建异步会话"""
    if self._session is None or self._session.closed:
      self._session = aiohttp.ClientSession(
        headers=self.headers,
        timeout=aiohttp.ClientTimeout(total=self.timeout),
      )
    return self._session

  async def close(self) -> None:
    """关闭会话"""
    if self._session and not self._session.closed:
      await self._session.close()

  async def _request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    执行异步 GET 请求并返回 JSON
    """
    try:
      session = await self._get_session()
      async with session.get(url, params=params, proxy=self.proxy) as response:
        text = await response.text()
        if response.status != 200:
          raise APIResponseError(f"API 请求失败: 状态码={response.status}, 内容={text}")
        data = await response.json()
        if data.get("error"):
          raise APIResponseError(f"API 返回错误: {data.get('message')}")
        return data
    except aiohttp.ClientError as e:
      raise NetworkError(f"网络请求失败: {e}") from e
    except asyncio.TimeoutError:
      raise NetworkError("请求超时")

  def set_token(self, token: str) -> None:
    """
    设置 API 访问令牌
    """
    self.headers["cookie"] = f"PHPSESSID={token}"

  def set_proxy(self, proxy: str) -> None:
    """ """
    self.proxy = proxy

  async def search_illust(self, illust_id: str):
    """
    搜索插画作品

    :param illust_id: 插画 ID
    """
    base_url = f"https://www.pixiv.net/ajax/illust/{illust_id}/pages"
    raw = await self._request(base_url)
    return SearchIllustMetaResult.from_response(raw)

  async def search_keyword(self, **kwargs: Unpack[SearchParamsDict]) -> SearchArtWorkResult:
    params = SearchParams(**kwargs)

    # 后续处理逻辑保持不变
    base_url = "https://www.pixiv.net/ajax/search/artworks/"
    encoded = urllib.parse.quote_plus(params.keyword)
    url = f"{base_url}{encoded}"

    query_params = {
      "order": params.order,
      "mode": params.mode,
      "p": params.p,
      "csw": params.csw,
      "s_mode": params.s_mode,
      "type": params.media_type,
      "lang": params.lang,
    }

    for key in ["scd", "ecd", "wgt", "hgt", "ratio", "ai_type"]:
      value = getattr(params, key)
      if value is not None:
        query_params[key] = value

    raw = await self._request(url, params=query_params)
    return SearchArtWorkResult.from_response(raw)

  async def search_following(
    self,
    user_id: int,
    offset: int = 0,
    limit: int = 24,
    rest: str = "show",
    tag: str = "",
    lang: str = "zh",
  ) -> SearchUserResult:
    """
    搜索关注用户（正在关注的用户列表）

    :param user_id: 用户 ID
    :param offset: 偏移量
    :param limit: 返回数量
    :param rest: 显示类型 (show: 全部, hide: 隐藏)
    :param tag: 过滤标签
    :param accepting_requests: 是否接受约稿 (0: 不筛选, 1: 只看接受约稿)
    :param lang: 返回语言
    """
    base_url = f"https://www.pixiv.net/ajax/user/{user_id}/following"
    params: Dict[str, Any] = {
      "offset": offset,
      "limit": limit,
      "rest": rest,
      "tag": tag,
      "lang": lang,
    }

    raw = await self._request(base_url, params=params)
    return SearchUserResult.from_response(raw)

  async def download(self, url, filepath: Path, headers: Dict[str, str] = {}):
    """
    下载 Pixiv 图片

    :param url: 图片 URL
    :param filepath: 保存路径
    :param headers: 请求头
    """
    headers = {
      "User-Agent": "PixivApp/7.13.3 (Android 11; Pixel 5)",
      "Referer": "https://www.pixiv.net/",
      **headers,
    }

    async with aiohttp.ClientSession(headers=headers, proxy=self.proxy) as session:
      async with session.get(url) as resp:
        if resp.status != 200:
          text = await resp.text()
          raise Exception(f"下载失败: 状态码={resp.status}, 内容={text}")

        await filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "wb") as f:
          while True:
            chunk = await resp.content.read(1024)
            if not chunk:
              break
            f.write(chunk)
