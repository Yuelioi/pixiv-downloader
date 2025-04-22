# pixiv 下载器

一个获取p站图片数据以及下载的小工具

## Feature

- 下载用户的所有图片
- 基于关键词下载图片
- 储存图片数据

## 配置

### 获取token

浏览器登录p站, f12打开 Applicatio n=> Cookies => https://www.pixiv.net => 找到PHPSESSID字段

!tip

请妥善保管token

### 配置环境

把 `.env.example` 重命名为 `.env` 并安要求填写

```plaintext
RPOXY:代理设置
DATABASE_UR:数据库链接 (我使用的是postgresql)
PHPSESSID:P站token信息
```

## 使用

```plaintext


```
