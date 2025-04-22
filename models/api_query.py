from typing import Optional, TypedDict

from pydantic import BaseModel, Field


class SearchParams(BaseModel):
  keyword: str = Field(description="搜索关键词（必填）")
  p: int = Field(1, description="页码，默认为1")
  order: str = Field("date_d", description="排序方式，默认为date_d")
  mode: str = Field("all", description="搜索模式，safe/all/r18")
  scd: Optional[str] = Field(None, description="开始时间")
  ecd: Optional[str] = Field(None, description="结束时间")
  csw: int = Field(1, description="子搜索权重")
  s_mode: str = Field("s_tag_full", description="搜索模式")
  media_type: str = Field("illust", description="媒体类型")
  wgt: Optional[int] = Field(None, description="宽度限制")
  hgt: Optional[int] = Field(None, description="高度限制")
  ratio: Optional[int] = Field(None, description="宽高比")
  ai_type: Optional[int] = Field(None, description="AI类型过滤")
  lang: str = Field("zh", description="语言，默认为zh")


class SearchParamsDict(TypedDict, total=False):
  keyword: str
  p: int
  order: str
  mode: str
  scd: Optional[str]
  ecd: Optional[str]
  csw: int
  s_mode: str
  media_type: str
  wgt: Optional[int]
  hgt: Optional[int]
  ratio: Optional[int]
  ai_type: Optional[int]
  lang: str
