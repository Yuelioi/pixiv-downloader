import os

from dotenv import load_dotenv
from tortoise import Tortoise

from models.db import Image

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


async def create_custom_indexes():
  conn = Image._meta.db

  try:
    # 添加IF NOT EXISTS避免重复创建
    await conn.execute_script("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_image_tags_gin
            ON image USING GIN (tags);
        """)

    await conn.execute_script("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_image_search 
            ON image USING GIN (to_tsvector('simple', title));
        """)
  except Exception as e:
    print(f"索引可能已存在，忽略错误: {str(e)}")


class ImageDB:
  def __init__(self):
    self.db = None

  async def connect(self):
    await Tortoise.init(db_url=DATABASE_URL, modules={"models": ["models.db"]})
    await Tortoise.generate_schemas()
    await create_custom_indexes()

  async def get_all_unique_tags(self) -> list[str]:
    query = """
    SELECT DISTINCT jsonb_array_elements_text(tags) AS tag
    FROM image
    """
    rows = await Image._meta.db.execute_query_dict(query)
    return [row["tag"] for row in rows]

  async def get_images_by_tag(self, tag: str, page: int = 1, page_size: int = 20) -> list[Image]:
    offset = (page - 1) * page_size
    return await Image.filter(tags__contains=[tag]).offset(offset).limit(page_size).order_by("-created")

  async def get_image_count(self) -> int:
    return await Image.all().count()

  async def count_images_by_tag(self, tag: str) -> int:
    return await Image.filter(tags__contains=[tag]).count()

  async def get_top_tags(self, limit: int = 30) -> list[tuple[str, int]]:
    """
    获取最热tags
    :param limit: 限制返回数量

    [('ブルーアーカイブ', 26904), ('アロナ(ブルーアーカイブ)', 23511),...]
    """
    query = f"""
      SELECT tag, COUNT(*) as freq
      FROM (
        SELECT jsonb_array_elements_text(tags) AS tag
        FROM image
      ) AS all_tags
      GROUP BY tag
      ORDER BY freq DESC
      LIMIT {limit}
      """
    rows = await Image._meta.db.execute_query_dict(query)
    return [(row["tag"], row["freq"]) for row in rows]

  async def get_recent_images(self, limit: int = 20) -> list[Image]:
    return await Image.all().order_by("-created").limit(limit)

  async def get_images_by_user(self, user_id: str, page: int = 1, page_size: int = 20) -> list[Image]:
    offset = (page - 1) * page_size
    return await Image.filter(user_id=user_id).order_by("-created").offset(offset).limit(page_size)
