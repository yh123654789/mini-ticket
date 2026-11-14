# 3 分钟演示脚本

> 全程在浏览器完成，不需要命令行（除了最后一步验证降级要改 `.env` 重启）。
> 预期结果写在每步下面，照着做就能复现。

## 准备（10 秒）

```bash
cp .env.example .env
docker compose up --build
```

看到 `mini-ticket-backend-1 | Mini Ticket 已启动 | AI_PROVIDER=mock` 即可。
打开 **http://localhost:8080**。

---

## 第 1 步：未登录被拦（15 秒）

直接用浏览器访问 `http://localhost:8080/tickets`。

**预期**：页面自动跳到 `/login`，显示登录表单。

命令行版（说明后端也拦得住，不只是前端路由）：

```bash
curl -i http://localhost:8080/api/tickets
# HTTP/1.1 401 Unauthorized
# {"detail":"缺少 Authorization: Bearer <token>"}
```

---

## 第 2 步：登录（15 秒）

用 `alice@example.com` / `alice123` 登录。

**预期**：进入「我的工单」，右上角显示 `Alice Chen（alice@example.com）`，列表为空并提示「还没有工单」。

---

## 第 3 步：创建工单，看 AI 摘要与分类（40 秒）

点「+ 新建工单」，填写：

- 标题：`登录后报 500 错误`
- 描述：`点击登录按钮后页面直接报 500，控制台没有任何有效信息。`
- 优先级：`高`

提交。

**预期**：
- 列表出现一条工单，状态「待处理」、优先级「高」、分类「**缺陷**」；
- 标题下方有一行摘要：`点击登录按钮后页面直接报 500，控制台没有任何有效信息`（≤ 80 字，由 mock provider 截取首句）；
- 点进详情能看到完整描述、AI 摘要块和三个状态按钮。

再建 2 条不同优先级的工单（比如「希望支持导出 Excel」→ 分类应为 **需求**；「如何修改密码」→ 分类应为 **咨询**），说明分类不是写死的。

---

## 第 4 步：筛选与分页（30 秒）

列表页上方把「优先级」选成 `高`。

**预期**：只剩高优先级那一条；清空后恢复全部。状态筛选同理。

再造 5 条以上工单，把 `page_size` 换成小值（或直接看底部「第 1 / N 页」），点「下一页」。

**预期**：页码与条数正确，`total` 不变。

命令行等价验证：

```bash
curl "http://localhost:8080/api/tickets?page=1&page_size=2&priority=high" -H "Authorization: Bearer $TOKEN"
# {"items":[...2 条...],"total":6,"page":1,"page_size":2}
```

---

## 第 5 步：状态流转（20 秒）

进入任意工单详情，依次点「处理中」→「已完成」。

**预期**：标签实时变化；返回列表后状态同步更新。

非法值验证（应有明确报错，而不是 500）：

```bash
curl -i -X PATCH http://localhost:8080/api/tickets/1/status \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"status":"closed"}'
# HTTP/1.1 422
# {"detail":"参数校验失败","errors":[{"field":"status",...}]}
```

---

## 第 6 步：AI 故障降级（40 秒）—— 最关键的一步

编辑 `.env`：

```ini
AI_PROVIDER=openai
AI_BASE_URL=http://127.0.0.1:9/v1
AI_MODEL=gpt-4o-mini
AI_TIMEOUT_SECONDS=2
```

```bash
docker compose up -d      # 重启后端使配置生效
```

再创建一个工单。

**预期**：
- **工单照样创建成功**，HTTP 201；
- 摘要退化成「截断后的原文」；
- 分类显示「其他」，列表里带一个橙色的「AI 降级」标记；
- 后端日志里有一条 `AI 分析失败，已降级：请求模型失败: ...`。

命令行验证：

```bash
curl -s -X POST http://localhost:8080/api/tickets \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"导出白屏","description":"点击导出按钮后页面一片空白。","priority":"medium"}' \
  | jq '{ai_status, category, summary}'
# {"ai_status":"failed","category":"other","summary":"点击导出按钮后页面一片空白。"}
```

演示完记得把 `.env` 改回 `AI_PROVIDER=mock`。

---

## 第 7 步：数据隔离（20 秒）

右上角退出，用 `bob@example.com` / `bob123` 登录。

**预期**：列表是空的（看不到 alice 的任何工单）；直接在地址栏访问 alice 的工单详情 `/tickets/1`，显示「工单不存在，或你没有权限查看」（后端返回 404）。

---

## 收尾句（10 秒）

> 主链路是登录 → 建单 → AI 摘要分类 → 筛选分页 → 状态流转，AI 是全链路里唯一的外部依赖，所以它被单独包在 Provider 后面，挂了就走降级，不影响工单本身。后端 21 个测试覆盖了这些路径，包括三种 AI 失败场景。
