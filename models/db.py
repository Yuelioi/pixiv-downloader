from tortoise import fields
from tortoise.indexes import Index
from tortoise.models import Model


class Image(Model):
  # 核心标识
  id = fields.BigIntField(pk=True)  # 自增主键
  img_id = fields.CharField(max_length=255)  # 平台ID如129557899
  hash = fields.CharField(max_length=64)  # SHA-256哈希

  # 内容元数据
  title = fields.CharField(max_length=255)  # 完整标题
  description = fields.TextField(null=True)  # 原神水着等详细描述
  tags = fields.JSONField()  # ["原神", "水着", "Mona"]
  urls = fields.JSONField()  # 多尺寸URL
  p = fields.IntField(default=0)  # 分页id

  # 画师信息（直接内嵌）
  user_id = fields.CharField(max_length=255, index=True)
  user_name = fields.CharField(max_length=255)
  user_avatar = fields.CharField(max_length=512, null=True)  # 画师头像

  # 质量指标
  width = fields.IntField()
  height = fields.IntField()
  bookmarks = fields.IntField(index=True)  # 收藏数
  views = fields.IntField(null=True)  # 浏览数

  # 内容属性
  source = fields.CharField(max_length=20)  # pixiv/twitter
  x_restrict = fields.IntField()  # 内容分级 0:无 1:R18
  ai_type = fields.IntField()  # 人工智能类型  1:无 2ai绘画

  # 时间信息
  created = fields.DatetimeField(index=True)  # 作品发布时间
  updated = fields.DatetimeField(auto_now=True)  # 最后更新时间

  # 文件信息
  size_kb = fields.IntField(default=0)  # 文件大小KB
  file_ext = fields.CharField(max_length=5, default="")  # png/jpg

  score = fields.IntField(default=0)

  class Meta:
    indexes = [
      # 现有索引
      ("created", "x_restrict"),
      ("user_id", "created"),
      # 新增单字段索引（示例）
      Index(fields=["bookmarks"], name="idx_bookmarks"),
      Index(fields=["created"], name="idx_created"),
      # 新增JSON字段GIN索引（PostgreSQL专有）
      Index(
        fields=["tags"],
        name="idx_tags",
      ),
    ]
    unique_together = (("img_id", "p"),)
