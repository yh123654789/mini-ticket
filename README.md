# Mini Ticket —— 带 AI 摘要与分类的内部工单系统

一个能 `docker compose up --build` 一键跑起来的轻量工单系统。登录后创建工单，系统调用大模型生成一句话摘要和分类标签，支持列表筛选、分页和状态流转；**AI 挂了也不影响工单创建**。

- 后端：Python 3.13 + FastAPI + SQLAlchemy 2 + SQLite
- 前端：Vue 3 + TypeScript + Vite
- 鉴权：JWT（bcrypt 存储密码哈希）
- AI：可插拔 Provider（`mock` / `openai-compatible`），失败自动降级

## 0. 在线演示（免安装，直接打开）

```
https://walt-founder-cards-applicant.trycloudflare.com
```

登录：`alice@example.com` / `alice123`　或　`bob@example.com` / `bob123`

> 演示地址通过 Cloudflare Tunnel 映射，随演示机启停；项目本身可部署到任意装有 Docker 的服务器或容器平台。

---

## 1. 快速开始

### 1.1 一条命令启动（推荐）

```bash
cp .env.example .env        # Windows PowerShell: Copy-Item .env.example .env
docker compose up --build
```

启动完成后，Docker 会把容器内的 80 端口映射到本机 **8080** 端口：

| 路径 | 说明 |
| --- | --- |
| `/` | 前端页面 |
| `/api/docs` | Swagger 交互式文档 |
| `/api/health` | 健康检查 |

端口可以在 `.env` 里用 `FRONTEND_PORT` 改。

### 1.2 预置账号

启动时会自动创建（密码以 bcrypt 哈希入库，可通过 `SEED_DEMO_USERS=false` 关闭）：

| 邮箱 | 密码 | 姓名 |
| --- | --- | --- |
| alice@example.com | alice123 | Alice Chen |
| bob@example.com | bob123 | Bob Li |

两个账号互相看不到对方的工单，可用来验证数据隔离。

### 1.3 不用 Docker 的本地启动

```bash
# 后端
cd backend
python -m venv .venv
.venv/Scripts/activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000

# 前端（另开一个终端）
cd frontend
npm install
npm run dev     # 前端开发服务器（5173 端口），已配置 /api 反向代理
```

---

## 2. 架构说明

```
浏览器 (Vue 3 SPA)
      │  /api/*  （同源，无跨域）
      ▼
   nginx  ──静态资源──► dist/
      │  反向代理 /api
      ▼
 FastAPI (uvicorn)
   ├── routers/auth.py      登录、获取当前用户
   ├── routers/tickets.py   工单 CRUD / 分页 / 筛选 / 状态
   ├── deps.py              JWT → User 的依赖注入
   ├── ai/service.py        Provider 选择 + 失败降级
   └── models / schemas     ORM 与请求响应模型
      │
      ▼
   SQLite（挂载在 ticket-data 卷上）
```

**分层原则**：路由层只做参数校验和编排；AI 调用被收在 `ai/` 里，业务代码只依赖 `AIProvider` 协议，替换模型供应商不需要改工单逻辑。

### 目录结构

```
mini-ticket/
├── backend/
│   ├── app/
│   │   ├── main.py            FastAPI 装配、异常处理、启动播种
│   │   ├── config.py          环境变量 → Settings
│   │   ├── database.py        engine / Session / init_db
│   │   ├── models.py          User、Ticket
│   │   ├── schemas.py         Pydantic 校验与输出模型
│   │   ├── security.py        bcrypt + JWT
│   │   ├── deps.py            当前用户依赖
│   │   ├── seed.py            演示账号
│   │   ├── routers/           auth.py / tickets.py
│   │   └── ai/                base.py、mock.py、openai_compat.py、service.py
│   ├── tests/                 pytest 集成测试
│   ├── Dockerfile
│   └── requirements*.txt
├── frontend/
│   ├── src/
│   │   ├── api/               client.ts（fetch 封装）、types.ts、session.ts
│   │   ├── stores/auth.ts     登录态
│   │   ├── views/             LoginView / TicketsView / TicketDetailView
│   │   ├── components/        TicketForm / StatusBadge（含单测）
│   │   └── router.ts          路由与登录守卫
│   ├── Dockerfile / nginx.conf
│   └── package.json
├── docker-compose.yml
├── .env.example
└── docs/DEMO.md               3 分钟演示脚本
```

---

## 3. API 说明

除登录与健康检查外，所有接口都需要请求头 `Authorization: Bearer <token>`。

| 方法 | 路径 | 说明 | 鉴权 |
| --- | --- | --- | --- |
| POST | `/api/auth/login` | 邮箱 + 密码换取 JWT | 否 |
| GET | `/api/auth/me` | 当前用户信息 | 是 |
| POST | `/api/tickets` | 创建工单，同步生成 AI 摘要与分类 | 是 |
| GET | `/api/tickets` | 我的工单列表（分页 + 筛选） | 是 |
| GET | `/api/tickets/{id}` | 工单详情 | 是 |
| PATCH | `/api/tickets/{id}/status` | 更新状态 | 是 |
| GET | `/api/health` | 健康检查 | 否 |

### 3.1 登录

下面的示例用 `$BASE` 代表你的访问地址：

```bash
BASE="https://walt-founder-cards-applicant.trycloudflare.com"
```

```bash
curl -X POST "$BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"alice123"}'
```

```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user": { "id": 1, "name": "Alice Chen", "email": "alice@example.com" }
}
```

### 3.2 创建工单

```bash
curl -X POST "$BASE/api/tickets" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"登录后报 500","description":"点击登录按钮后页面报 500，控制台没有信息。","priority":"high"}'
```

```json
{
  "id": 1,
  "title": "登录后报 500",
  "status": "open",
  "priority": "high",
  "summary": "点击登录按钮后页面报 500，控制台没有信息",
  "category": "bug",
  "ai_status": "ok",
  "owner_id": 1,
  "created_at": "2026-11-14T13:05:00Z",
  "updated_at": "2026-11-14T13:05:00Z"
}
```

### 3.3 列表（分页 + 筛选）

```bash
curl "$BASE/api/tickets?status=open&priority=high&page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```

| 参数 | 取值 | 默认 |
| --- | --- | --- |
| `status` | `open` / `in_progress` / `done`，留空为全部 | 全部 |
| `priority` | `low` / `medium` / `high`，留空为全部 | 全部 |
| `page` | ≥ 1 | 1 |
| `page_size` | 1–100 | 10 |

响应：`{ "items": [...], "total": 12, "page": 1, "page_size": 10 }`

### 3.4 错误码

| 状态码 | 场景 | 响应体 |
| --- | --- | --- |
| 401 | 未带 token / token 过期 / 密码错误 | `{"detail": "未登录或登录已过期"}` |
| 404 | 工单不存在，**或不属于当前用户** | `{"detail": "工单不存在"}` |
| 422 | 字段校验失败 | `{"detail": "参数校验失败", "errors": [{"field": "title", "message": "..."}]}` |

> 别人的工单统一返回 404 而不是 403，避免通过状态码探测工单是否存在。

---

## 4. 数据库设计

SQLite 单文件（容器内 `/data/tickets.db`，挂载在 `ticket-data` 卷）。表由 SQLAlchemy `create_all` 在启动时创建，演示账号在启动时幂等写入。

### users

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER PK | |
| email | VARCHAR(255) UNIQUE INDEX | 登录名，存小写 |
| name | VARCHAR(120) | 显示名 |
| password_hash | VARCHAR(255) | bcrypt，明文不落库 |
| created_at | DATETIME | |

### tickets

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER PK | |
| title | VARCHAR(200) | 必填，去空白后非空 |
| description | TEXT | 必填，≤ 4000 字 |
| status | VARCHAR(20) INDEX | `open` / `in_progress` / `done` |
| priority | VARCHAR(20) INDEX | `low` / `medium` / `high` |
| summary | VARCHAR(200) | AI 摘要，≤ 80 字 |
| category | VARCHAR(20) | `bug` / `feature` / `consult` / `other` |
| ai_status | VARCHAR(20) | `ok` / `failed`，记录本次 AI 是否成功 |
| owner_id | INTEGER FK users.id INDEX | |
| created_at / updated_at | DATETIME | |

复合索引 `(owner_id, status)`：列表接口永远是「先按 owner 过滤，再按 status 筛」，这个索引正好覆盖。

**为什么枚举用字符串而不是数据库 ENUM**：SQLite 没有原生 ENUM，字符串更直白，改枚举值不需要迁移；取值合法性由 Pydantic 的 `Literal` 在入口处卡死。

---

## 5. AI Provider 设计

### 5.1 抽象

```python
class AIProvider(Protocol):
    name: str
    def analyze(self, title: str, description: str) -> AIResult: ...
```

`AIResult = (summary, category, status, provider, error)`。业务代码只调 `analyze_ticket()`，不关心背后是谁。

### 5.2 两种实现

| Provider | 触发条件 | 行为 |
| --- | --- | --- |
| `mock` | `AI_PROVIDER=mock`（默认） | 关键词匹配分类 + 取首句做摘要，**确定性输出**，不需要任何密钥，测试依赖它 |
| `openai-compatible` | `AI_PROVIDER=openai` | 调 `{AI_BASE_URL}/chat/completions`，要求模型输出 JSON |

`openai-compatible` 的 Prompt 明确限定输出格式，解析时做了三层兜底：

1. 去掉 ```json 代码块包裹；
2. 直接 `json.loads` 失败则用正则抓第一个 `{...}` 再解；
3. 解析出的 `category` 若不在枚举内，一律归一为 `other`。

摘要统一走 `truncate()`，按字符截断到 80 字以内（中文按字算）。

兼容性：任何实现 `/chat/completions` 的服务都能接 —— OpenAI、DeepSeek、通义、vLLM、本机 Ollama（`http://host.docker.internal:11434/v1`，`AI_API_KEY` 随便填）。

### 5.3 失败降级（核心）

```
创建工单
  └─ analyze_ticket()
       ├─ 成功 → summary=模型输出, category=模型分类, ai_status=ok
       └─ 异常 → 吞掉，记 warning 日志
                  summary=原文截断 80 字, category=other, ai_status=failed
                然后照常保存工单并返回 201
```

**任何异常都不会让创建失败**：连接超时、DNS 失败、401/500、返回非 JSON、字段缺失、甚至 Provider 未配置。对应测试见 `backend/tests/test_ai_fallback.py`。

验证方式：把 `AI_PROVIDER=openai` 且 `AI_BASE_URL` 指向一个不存在的地址，创建工单仍然 201，`ai_status` 为 `failed`。

---

## 6. 测试

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

21 个用例，覆盖：

- 登录成功 / 密码错误 / 未知账号（同样返回 401，避免账号枚举）；
- 未登录访问工单接口被拒（401）；
- 创建工单 + mock AI 摘要与分类正确；
- 标题空白、优先级非法 → 422 且带字段名；
- 分页（`total` 与每页条数）；
- 状态筛选、优先级筛选、组合筛选；
- 用户隔离：bob 看不到、也改不了 alice 的工单（404）；
- 状态更新成功 / 非法状态 422；
- **AI 降级**：地址不可达、Provider 抛异常、模型名未配置，三种情况工单都创建成功。

前端：

```bash
cd frontend
npm run build       # vue-tsc 类型检查 + vite 构建
npm run test:unit   # StatusBadge 组件测试（3 个用例）
```

### 6.1 按验收清单逐条自测的结果

下面这份是在本机跑起来（非容器）后逐条打的，命令等价于验收时会执行的操作：

| 验收项 | 实测结果 |
| --- | --- |
| ① `docker compose up --build` 能启动 | ✅ 镜像构建成功，backend `healthy`，frontend 监听 8080；`/`、`/api/health`、`/tickets/1` 均 200 |
| ② 预置账号能登录、未登录被拒 | ✅ alice / bob 均登录成功；无 token 访问 `/api/tickets` → 401；错误密码 → 401 |
| ③ 创建工单生成 mock AI 摘要与分类 | ✅ `category=bug`、`ai_status=ok`、摘要 58 字；「希望支持导出 Excel」→ `feature` |
| ④ AI 配错地址仍能建单、降级生效 | ✅ 把 `AI_BASE_URL` 指向死地址后：HTTP 201、`ai_status=failed`、`category=other`、摘要退化为原文截断（60 字），阻塞 2.1 秒后返回 |
| ⑤ 分页 + 状态筛选 + 优先级筛选 | ✅ 7 条数据，`page_size=2` 返回 2 条；`status=done` → 1 条；`priority=high` → 3 条；组合筛选 → 1 条 |
| ⑥ 普通用户看不到别人的工单 | ✅ bob 列表 `total=0`；读 alice 工单 → 404；改 alice 工单 → 404 |
| ⑦ 状态更新可用、非法输入有明确错误 | ✅ open→in_progress 成功；`"closed"` → 422 且带 `detail`/`errors`；空白标题 → 422 |
| ⑧ 后端测试能跑通 | ✅ `pytest` 21 passed |
| ⑨ README 能照着完成启动与验证 | ✅ 本文档即验证路径 |
| ⑩ 代码结构 / 提交记录 / AI 使用说明 | ✅ 10+ 个语义化提交，见第 8 节 |

---

## 7. 取舍与未完成项

### 做了什么简化

| 简化 | 原因 | 如果要生产化 |
| --- | --- | --- |
| SQLite 而非 PostgreSQL | 零运维，`docker compose up` 不需要额外服务 | 换 PG：改 `DATABASE_URL` + 引入 Alembic |
| `create_all` 而非迁移工具 | 单表结构，没有历史数据要兼容 | 引入 Alembic，第一个版本生成 baseline |
| AI 同步调用 | 主链路最简单，验收时行为可预期 | 改成后台任务（FastAPI BackgroundTasks / Celery）+ 前端轮询 |
| 无角色/权限分级 | 需求明确说不要求复杂权限 | 加 `role` 字段 + 管理员可见全部 |
| 单 JWT，无 refresh token | 演示够用 | 加 refresh token + 黑名单 |
| 前端无状态管理库 | 三个页面，`ref` + 一个模块级 store 足够 | 引入 Pinia |
| CORS 全开 | 开发期方便 | 收敛到具体域名 |

### 本地验证记录

| 验证项 | 方式 | 结果 |
| --- | --- | --- |
| 后端接口 | 21 个 pytest 集成测试 | ✅ 全部通过 |
| 前端类型检查与构建 | `npm run build`（vue-tsc + vite） | ✅ 通过 |
| 组件测试 | vitest（StatusBadge） | ✅ 3 个用例通过 |
| 真实启动后端 + 走完整 HTTP | uvicorn + curl 两轮（mock / 降级） | ✅ 主链路与降级均符合预期 |
| compose 编排语法 | `docker compose config` | ✅ 解析通过，变量插值正确 |
| **nginx 反代 + SPA 回退** | 真实 nginx 1.31.8 加载同一份 `nginx.conf`（仅上游换成 127.0.0.1） | ✅ `/` 200、`/api/health` 正常代理、`/tickets/1` 回退到 index.html、`/api/tickets` 经反代仍返回 401 |
| **镜像构建 + 容器启动** | `docker compose up --build`（真实执行） | ✅ 两个镜像构建成功；backend 容器 `healthy`；frontend 映射 8080 |

### 已知限制

- 基础镜像来自 Docker Hub。在国内网络下直连 `registry-1.docker.io` 可能超时，需要给 Docker 配镜像加速器（本项目验证时用的是 `https://docker.m.daocloud.io`），配好后 `docker compose up --build` 可正常拉取。
- 首次构建需要下载基础镜像（python 3.13-slim / node 22-alpine / nginx 1.27-alpine，约 150 MB）并安装依赖，耗时取决于网络。
- 没有实现工单编辑和删除（需求里删除标记为可选）。
- 列表没有全文搜索。
- 状态流转没有约束（允许 `done` 直接回到 `open`）。

---

## 8. AI 使用说明

### 用了什么工具

- **AI 编码代理**：DeepSeek Harness 内的编码 Agent（基于 deepseek-flash），负责代码初稿、目录搭建、命令执行与验证。
- 运行时还用过本机 Ollama（`qwen3:14b-q4_K_M`）作为本地模型试验，但**项目本身不依赖它**。

### 哪些代码由 AI 生成

基本上所有初稿：后端 models/schemas/routers/ai 模块、前端视图与组件、Docker 配置、测试用例，都是 AI 先生成、再由作者逐文件审阅后保留或修改的。

### 人工介入与兜底

| 环节 | 现象 | 处理 |
| --- | --- | --- |
| bcrypt 密码 | AI 直接用 `hashpw`，长密码会因 72 字节限制抛异常 | 显式截断到 72 字节 |
| JWT 密钥 | 默认密钥短于 32 字节，PyJWT 报 `InsecureKeyLengthWarning` | 默认值加长，测试密钥同样加长 |
| SQLite 路径 | 测试把库放在系统临时目录，容器式进程无写权限 | 改为项目内路径 + 测试用 `tempfile` 的隔离目录 |
| 中文乱码 | PowerShell 5.1 按 ANSI 解码 JSON 响应，界面/命令行看到 `ç¹å»` | 确认是客户端显示问题（直接查库是正确中文），文档改用 curl / 浏览器验证 |
| AI 降级 | AI 初版把异常往上抛，工单创建会 500 | 改为 `analyze_ticket` 内统一兜底，并补三个降级测试 |

### AI 在哪些环节不可靠

1. **版本号**：AI 容易给出不存在的依赖版本；本项目依赖一律写成范围（`>=x,<y`），由 pip/npm 实际解析。
2. **环境差异**：AI 容易把「在我这边跑通了」当成「在目标环境也能跑」——容器、WSL、镜像源这些前置条件它感知不到。本项目把验证拆成「配置正确」和「真实跑通」两层分别记录，就是为此。
3. **编码问题**：中文乱码时 AI 第一反应容易误判为服务端 bug，实际要先确认是终端/客户端的解码问题。
4. **测试是否真的会失败**：AI 写的测试有时只断言 200，不对内容做断言；本项目补了字段级断言（分类、摘要长度、`ai_status`、total 计数）。

---

## 9. 演示

见 [docs/DEMO.md](docs/DEMO.md)，3 分钟走完：登录 → 建单看 AI 摘要 → 筛选分页 → 状态流转 → 把 AI 配错看降级 → 换 bob 登录验证隔离。
