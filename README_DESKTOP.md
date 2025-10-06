# News Crawler Desktop Application

一个功能完整的桌面端新闻爬取和可视化应用，采用"本地后端服务 + 桌面前端"架构。

## 功能特性

### 🚀 核心功能
- **智能新闻爬取**: 基于关键词从多个RSS源爬取新闻文章
- **实时进度监控**: WebSocket实时推送爬取进度和状态更新
- **多策略摘要生成**: 支持RSS摘要、AI生成、混合策略等多种摘要方式
- **可视化界面**: 现代化的桌面应用界面，支持任务管理、文章浏览、源配置等

### 📊 管理功能
- **任务仪表板**: 查看任务统计、最近任务、运行状态等
- **文章管理**: 文章列表、搜索过滤、详情查看、摘要重新生成
- **RSS源管理**: 添加、编辑、删除RSS源，支持查询参数
- **配置管理**: 摘要策略、API配置等设置

### 🔧 技术特性
- **异步处理**: 后端采用FastAPI + 异步爬取，支持高并发
- **数据库存储**: SQLite数据库存储任务、文章、配置等数据
- **实时通信**: WebSocket实现实时进度推送
- **跨平台**: 支持Windows、macOS、Linux桌面环境

## 架构设计

```
┌─────────────────┐    HTTP/WebSocket    ┌─────────────────┐
│   Electron      │ ◄─────────────────► │   FastAPI       │
│   Frontend      │                     │   Backend       │
│                 │                     │                 │
│ • 任务仪表板     │                     │ • CrawlerService │
│ • 文章列表      │                     │ • ArticlePipeline│
│ • 源管理        │                     │ • SummaryService │
│ • 设置页面      │                     │ • WebSocket API  │
└─────────────────┘                     └─────────────────┘
                                                │
                                                ▼
                                        ┌─────────────────┐
                                        │   SQLite        │
                                        │   Database      │
                                        │                 │
                                        │ • 任务存储      │
                                        │ • 文章存储      │
                                        │ • 配置存储      │
                                        └─────────────────┘
```

## 安装和运行

### 环境要求
- Python 3.8+
- Node.js 16+
- npm 或 yarn

### 快速开始

1. **克隆项目**
```bash
git clone <repository-url>
cd news
```

2. **一键启动** (推荐)
```bash
python start_all.py
```

这将自动安装依赖并启动后端服务和前端应用。

### 手动启动

#### 启动后端服务
```bash
# 安装后端依赖
cd backend
pip install -r requirements.txt

# 启动后端服务
python main.py
# 或者
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### 启动前端应用
```bash
# 安装前端依赖
cd frontend
npm install

# 启动桌面应用
npm start
```

## 使用指南

### 1. 创建爬取任务
1. 点击"New Task"按钮
2. 输入搜索关键词（必填）
3. 选择时间范围（可选）
4. 设置文章数量限制
5. 添加自定义RSS源（可选）
6. 点击"Create Task"开始爬取

### 2. 监控任务进度
- 在Dashboard查看任务统计和最近任务
- 在Tasks页面查看所有任务状态
- 实时进度条显示爬取进度
- WebSocket推送实时状态更新

### 3. 浏览和管理文章
- 在Articles页面浏览所有爬取的文章
- 使用搜索框和过滤器筛选文章
- 点击文章查看详细内容和摘要
- 支持重新生成文章摘要

### 4. 管理RSS源
- 在Sources页面管理RSS源
- 添加新的RSS源
- 配置是否支持查询参数
- 设置源优先级

### 5. 配置设置
- 在Settings页面配置摘要生成策略
- 修改API服务地址
- 查看摘要生成统计

## API接口

### 任务管理
- `POST /tasks` - 创建新任务
- `GET /tasks` - 获取任务列表
- `GET /tasks/{id}` - 获取特定任务
- `DELETE /tasks/{id}` - 删除任务
- `POST /tasks/{id}/retry` - 重试失败的任务

### 文章管理
- `GET /articles` - 获取文章列表
- `GET /articles/{id}` - 获取特定文章
- `POST /articles/{id}/regenerate-summary` - 重新生成摘要

### RSS源管理
- `GET /rss-sources` - 获取RSS源列表
- `POST /rss-sources` - 添加新RSS源
- `PUT /rss-sources/{id}` - 更新RSS源
- `DELETE /rss-sources/{id}` - 删除RSS源

### WebSocket
- `ws://localhost:8000/ws` - 实时进度推送

## 配置说明

### 摘要生成策略
- **rss_first**: 优先使用RSS摘要，否则生成简单摘要
- **ai_generated**: 使用AI模型生成摘要（需要transformers库）
- **hybrid**: 结合RSS摘要和AI生成
- **simple**: 简单的文本提取摘要

### RSS源配置
支持两种类型的RSS源：
- **查询支持**: 使用`{query}`占位符，如`https://news.google.com/rss/search?q={query}`
- **通用源**: 固定URL，如`https://feeds.a.dj.com/rss/RSSMarketsMain.xml`

## 开发说明

### 后端开发
- 使用FastAPI框架
- SQLAlchemy ORM
- 异步HTTP客户端（httpx）
- WebSocket实时通信
- 结构化日志（loguru）

### 前端开发
- Electron桌面应用
- 原生HTML/CSS/JavaScript
- 模块化API客户端
- 响应式设计

### 数据库模型
- `CrawlTask`: 爬取任务
- `Article`: 文章内容
- `RSSSource`: RSS源配置
- `AppConfig`: 应用配置

## 故障排除

### 常见问题

1. **后端服务无法启动**
   - 检查Python版本（需要3.8+）
   - 安装所有依赖：`pip install -r backend/requirements.txt`
   - 检查端口8000是否被占用

2. **前端应用无法启动**
   - 检查Node.js版本（需要16+）
   - 安装依赖：`cd frontend && npm install`
   - 确保后端服务正在运行

3. **WebSocket连接失败**
   - 检查后端服务是否运行在localhost:8000
   - 检查防火墙设置
   - 查看浏览器控制台错误信息

4. **爬取任务失败**
   - 检查网络连接
   - 验证RSS源URL是否有效
   - 查看后端日志获取详细错误信息

### 日志查看
- 后端日志：控制台输出
- 前端日志：开发者工具控制台
- 数据库：SQLite文件位于`backend/news_crawler.db`

## 扩展开发

### 添加新的RSS源
1. 在Sources页面添加新的RSS源
2. 配置URL模板和参数
3. 设置优先级和状态

### 自定义摘要策略
1. 在`backend/summary_service.py`中添加新策略
2. 更新前端设置选项
3. 实现策略逻辑

### 添加新的导出格式
1. 在`backend/main.py`中添加新的API端点
2. 在前端添加导出按钮
3. 实现格式转换逻辑

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 更新日志

### v1.0.0
- 初始版本发布
- 基础爬取功能
- 桌面应用界面
- WebSocket实时通信
- 多策略摘要生成
