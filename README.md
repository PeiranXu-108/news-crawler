# News Crawler

一个功能强大的新闻聚合爬虫应用，支持多种运行模式：命令行工具、Web API 和桌面应用。

## 特性

### 🚀 多平台支持
- **命令行工具**: 快速抓取新闻到 CSV/JSON 格式
- **Web API**: FastAPI 后端服务，支持任务管理和实时进度
- **桌面应用**: Vue 3 + Electron 现代化桌面界面

### 📰 新闻抓取
- **RSS 源聚合**: 支持多个主流新闻源
- **智能关键词过滤**: 基于查询词的相关性匹配
- **全文提取**: 使用 trafilatura 和 readability 提取完整文章内容
- **日期过滤**: 支持按时间范围筛选文章
- **去重机制**: 自动识别和去除重复文章

### 🔧 高级功能
- **异步并发**: 高性能并发抓取
- **速率限制**: 遵守 robots.txt 和礼貌爬取
- **实时进度**: WebSocket 实时更新任务进度
- **任务管理**: 完整的任务生命周期管理
- **摘要生成**: 智能文章摘要生成
- **多格式输出**: JSONL、CSV 格式支持

## 架构

```
├── backend/          # FastAPI 后端服务
│   ├── main.py      # API 服务器
│   ├── database.py  # 数据库模型
│   ├── crawler_service.py    # 爬虫服务
│   └── summary_service.py    # 摘要服务
├── frontend/        # Vue 3 桌面应用
│   ├── src/         # 前端源码
│   └── package.json # 前端依赖
├── config/          # 配置文件
│   └── feeds.default.txt  # 默认 RSS 源
├── output/          # 输出文件
└── main.py          # 命令行工具入口
```

##  快速开始

### 方式一：一键启动（推荐）

```bash
# 启动完整的桌面应用
python start_all.py

# 或者明确指定 Vue 版本
python start_all.py --vue
```

### 方式二：命令行工具

```bash
# 基本用法
python main.py --q "AI technology" --since 2025-01-01 --limit 50

# 使用自定义 RSS 源
python main.py --q "NVIDIA earnings" --feeds "https://example.com/rss,https://another.com/feed"
```

### 方式三：开发环境

```bash
# 后端 API 服务
python start_backend.py

# 前端开发服务器
python start_frontend.py

# 或直接使用 Vue 开发模式
cd frontend
npm install
npm run dev
```

## 📋 命令行参数

| 参数 | 描述 | 必需 | 默认值 |
|------|------|------|--------|
| `--q, --query` | 搜索关键词 | ✅ | - |
| `--since` | 开始日期 (YYYY-MM-DD) | ❌ | - |
| `--limit` | 最大文章数量 | ❌ | 50 |
| `--feeds` | 自定义 RSS 源（逗号分隔） | ❌ | 使用默认源 |

## 🌐 Web API

### 主要端点

```bash
# 健康检查
GET /health

# 任务管理
POST /tasks          # 创建爬取任务
GET /tasks           # 获取任务列表
GET /tasks/{id}      # 获取特定任务
DELETE /tasks/{id}   # 删除任务

# 文章管理
GET /articles        # 获取文章列表
GET /articles/{id}   # 获取特定文章
POST /articles/{id}/regenerate-summary  # 重新生成摘要

# RSS 源管理
GET /rss-sources     # 获取 RSS 源列表
POST /rss-sources    # 添加新 RSS 源

# 实时更新
WebSocket /ws        # 实时进度更新
```

### API 示例

```bash
# 创建新任务
curl -X POST "http://localhost:8000/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence",
    "since": "2025-01-01",
    "limit": 100
  }'
```

## 🖥️ 桌面应用

Vue 3 桌面应用提供完整的图形界面：

- **Dashboard**: 统计信息和最近任务概览
- **Tasks**: 任务创建、管理和监控
- **Articles**: 文章浏览、搜索和摘要管理
- **Sources**: RSS 源配置和管理

### 启动桌面应用

```bash
# 使用启动脚本
python start_desktop.py

# 或手动启动
cd frontend
npm install
npm run electron:dev
```

## 📦 安装依赖

### Python 依赖

```bash
pip install -r requirements.txt
```

主要依赖：
- `fastapi`: Web API 框架
- `httpx`: 异步 HTTP 客户端
- `feedparser`: RSS 解析
- `trafilatura`: 内容提取
- `sqlalchemy`: 数据库 ORM
- `uvicorn`: ASGI 服务器

### Node.js 依赖

```bash
cd frontend
npm install
```

主要依赖：
- `vue`: 前端框架
- `electron`: 桌面应用框架
- `pinia`: 状态管理
- `vue-router`: 路由管理
- `axios`: HTTP 客户端

## 配置

### RSS 源配置

编辑 `config/feeds.default.txt` 添加或修改 RSS 源：

```
# 支持查询参数的源（{query} 会被替换为搜索词）
https://www.bing.com/news/search?q={query}&format=rss
https://news.google.com/rss/search?q={query}

# 静态源
https://feeds.a.dj.com/rss/RSSMarketsMain.xml
https://www.reuters.com/markets/rss
```

### 数据库配置

默认使用 SQLite 数据库，数据存储在 `backend/news_crawler.db`。

## 输出格式

### JSONL 格式

```json
{
  "title": "Article Title",
  "source": "News Source",
  "url": "https://example.com/article",
  "published": "2025-01-15T10:30:00Z",
  "summary": "Article summary...",
  "text": "Full article content...",
  "tags": ["tag1", "tag2"]
}
```

### CSV 格式

包含相同字段的逗号分隔值文件，便于在 Excel 等工具中查看。

## 🛠️ 开发

### 项目结构

```
├── backend/              # 后端服务
│   ├── main.py          # FastAPI 应用
│   ├── database.py      # 数据库模型
│   ├── crawler_service.py      # 爬虫逻辑
│   └── summary_service.py      # 摘要生成
├── frontend/            # 前端应用
│   ├── src/
│   │   ├── components/  # Vue 组件
│   │   ├── views/       # 页面组件
│   │   ├── stores/      # Pinia 状态管理
│   │   └── services/    # API 服务
│   └── package.json
├── config/              # 配置文件
├── output/              # 输出文件
└── main.py              # CLI 入口
```

### 开发模式

```bash
# 后端开发（自动重载）
cd backend
uvicorn main:app --reload

# 前端开发（热重载）
cd frontend
npm run dev

# Electron 开发
npm run electron:dev
```

## 🐛 故障排除

### 常见问题

1. **端口冲突**
   - 后端默认端口：8000
   - 前端默认端口：5173
   - 检查端口占用：`lsof -i :8000`

2. **依赖安装失败**
   ```bash
   # 更新 pip
   pip install --upgrade pip
   
   # 清理缓存
   npm cache clean --force
   ```

3. **Electron 窗口不显示**
   - 手动访问：http://localhost:5173
   - 检查控制台错误信息

### 日志查看

```bash
# 查看后端日志
tail -f backend/logs/app.log

# 查看前端控制台
# 在 Electron 应用中按 F12
```

## 📄 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

