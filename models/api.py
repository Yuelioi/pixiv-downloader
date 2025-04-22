from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


def parse_iso_date(date_str: str) -> datetime:
  """解析 ISO8601 格式的日期字符串（保留时区信息）"""
  # datetime.fromisoformat 支持带时区的 ISO 字符串
  return datetime.fromisoformat(date_str)


@dataclass
class Urls:
  original: str
  regular: str
  small: str
  thumb_mini: str

  def to_dict(self) -> Dict[str, Any]:
    return asdict(self)


@dataclass
class TitleCaptionTranslation:
  work_title: Optional[str]
  work_caption: Optional[str]

  @classmethod
  def from_dict(cls, data: Dict[str, Any]) -> "TitleCaptionTranslation":
    return cls(
      work_title=data.get("workTitle"),
      work_caption=data.get("workCaption"),
    )


@dataclass
class IllustMeta:
  urls: Urls
  width: int
  height: int

  @classmethod
  def from_dict(cls, data: Dict[str, Any]) -> "IllustMeta":
    return cls(
      width=data.get("width", 0),
      height=data.get("height", 0),
      urls=Urls(
        original=data.get("urls", {}).get("original", ""),
        regular=data.get("urls", {}).get("regular", ""),
        small=data.get("urls", {}).get("small", ""),
        thumb_mini=data.get("urls", {}).get("thumb_mini", ""),
      ),
    )

  def to_dict(self) -> Dict[str, Any]:
    return {"width": self.width, "height": self.height, "urls": self.urls.to_dict()}


@dataclass
class Illust:
  id: str  # 插画的唯一标识符（Pixiv内部ID）
  title: str  # 插画标题
  illust_type: int  # 插画类型：0=插画，1=漫画，2=动图(ugoira)
  x_restrict: int  # 分级限制：0=正常，1=R-18，2=R-18G（暴力）
  restrict: int  # 公开范围：0=公开，1=仅关注用户，2=私密
  sl: int  # 附加限制字段（例如仅限关注者）
  url: str  # 原图地址，通常是第一张图
  description: str  # 插画的文字说明或介绍
  tags: List[str]  # 插画标签列表
  user_id: str  # 作者的用户ID
  user_name: str  # 作者的用户名
  width: int  # 插画宽度（像素）
  height: int  # 插画高度（像素）
  page_count: int  # 插画页数（多图时大于1）
  is_bookmarkable: bool  # 当前用户是否可以收藏该作品
  bookmark_data: Optional[Any]  # 当前用户的收藏信息（可能为None）
  alt: str  # 可选的替代表达（用于无障碍、SEO等）
  title_caption_translation: TitleCaptionTranslation  # 标题与描述的翻译信息
  create_date: datetime  # 插画的创建时间
  update_date: datetime  # 插画的更新时间
  is_unlisted: bool  # 是否为未列出的隐藏作品
  is_masked: bool  # 是否为屏蔽作品（可能受限或违规）
  ai_type: int  # AI属性：0=非AI，1=AI辅助，2=AI生成
  visibility_scope: int  # 可见性范围（未来拓展字段）
  profile_image_url: str  # 作者头像URL
  meta: list[IllustMeta] = field(default_factory=list)  # 附加图片信息（如多页图的每张图meta）

  @classmethod
  def from_dict(cls, data: Dict[str, Any]) -> "Illust":
    # 日期字段转换
    created = parse_iso_date(data["createDate"])
    updated = parse_iso_date(data["updateDate"])

    return cls(
      id=str(data["id"]),
      title=data.get("title", ""),
      illust_type=data.get("illustType", 0),
      x_restrict=data.get("xRestrict", 0),
      restrict=data.get("restrict", 0),
      sl=data.get("sl", 0),
      url=data.get("url", ""),
      description=data.get("description", ""),
      tags=data.get("tags", []),
      user_id=str(data.get("userId", "")),
      user_name=data.get("userName", ""),
      width=data.get("width", 0),
      height=data.get("height", 0),
      page_count=data.get("pageCount", 0),
      is_bookmarkable=data.get("isBookmarkable", False),
      bookmark_data=data.get("bookmarkData"),
      alt=data.get("alt", ""),
      title_caption_translation=TitleCaptionTranslation.from_dict(data.get("titleCaptionTranslation", {})),
      create_date=created,
      update_date=updated,
      is_unlisted=data.get("isUnlisted", False),
      is_masked=data.get("isMasked", False),
      ai_type=data.get("aiType", 0),
      visibility_scope=data.get("visibilityScope", 0),
      profile_image_url=data.get("profileImageUrl", ""),
    )

  def to_dict(self) -> Dict[str, Any]:
    """将对象转换回符合 Pixiv API 格式的字典"""
    return {
      "id": self.id,
      "title": self.title,
      "illustType": self.illust_type,
      "xRestrict": self.x_restrict,
      "restrict": self.restrict,
      "sl": self.sl,
      "url": self.url,
      "description": self.description,
      "tags": self.tags,
      "userId": self.user_id,
      "userName": self.user_name,
      "width": self.width,
      "height": self.height,
      "pageCount": self.page_count,
      "isBookmarkable": self.is_bookmarkable,
      "bookmarkData": self.bookmark_data,
      "alt": self.alt,
      "titleCaptionTranslation": {
        "workTitle": self.title_caption_translation.work_title,
        "workCaption": self.title_caption_translation.work_caption,
      },
      "createDate": self.create_date.isoformat(),
      "updateDate": self.update_date.isoformat(),
      "isUnlisted": self.is_unlisted,
      "isMasked": self.is_masked,
      "aiType": self.ai_type,
      "visibilityScope": self.visibility_scope,
      "profileImageUrl": self.profile_image_url,
    }


@dataclass
class User:
  user_id: str
  user_name: str
  profile_image_url: str
  profile_image_small_url: str
  user_comment: str
  premium: bool
  following: bool
  followed: bool
  is_blocking: bool
  is_mypixiv: bool
  illusts: List[Illust]
  novels: List[Any]
  commission: Optional[Any]

  @classmethod
  def from_dict(cls, data: Dict[str, Any]) -> "User":
    # 解析插画列表
    illusts = [Illust.from_dict(item) for item in data.get("illusts", [])]
    # novels 结构未知，暂以原始 dict 列表保存
    novels = data.get("novels", []) or []
    return cls(
      user_id=str(data.get("userId", "")),
      user_name=data.get("userName", ""),
      profile_image_url=data.get("profileImageUrl", ""),
      profile_image_small_url=data.get("profileImageSmallUrl", ""),
      user_comment=data.get("userComment", ""),
      premium=data.get("premium", False),
      following=data.get("following", False),
      followed=data.get("followed", False),
      is_blocking=data.get("isBlocking", False),
      is_mypixiv=data.get("isMypixiv", False),
      illusts=illusts,
      novels=novels,
      commission=data.get("commission"),
    )


@dataclass
class SearchArtWorkResult:
  Illusts: List[Illust]
  total: int
  lastPage: int
  error: bool

  @classmethod
  def from_response(cls, raw_data: Dict[str, Any]):
    body = raw_data.get("body", {})
    illusts = body.get("illustManga", {}).get("data", [])

    return cls(
      total=body.get("illustManga", {}).get("total", 0),
      lastPage=body.get("illustManga", {}).get("lastPage", 0),
      Illusts=[Illust.from_dict(i) for i in illusts],
      error=raw_data.get("error", False),
    )


@dataclass
class SearchUserResult:
  users: List[User]
  total: int
  error: bool

  @classmethod
  def from_response(cls, raw_data: Dict[str, Any]):
    body = raw_data.get("body", {})
    users = body.get("users", [])
    total = body.get("total", 0)
    return cls(
      total=total,
      users=[User.from_dict(i) for i in users],
      error=raw_data.get("error", False),
    )


@dataclass
class SearchIllustMetaResult:
  metas: List[IllustMeta]
  error: bool

  @classmethod
  def from_response(cls, raw_data: Dict[str, Any]):
    body = raw_data.get("body", [])
    return cls(
      metas=[IllustMeta.from_dict(i) for i in body],
      error=raw_data.get("error", False),
    )
