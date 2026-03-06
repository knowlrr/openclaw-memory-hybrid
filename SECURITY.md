# SECURITY.md

## Threat Model

`openclaw-memory-hybrid` 主要风险来自以下场景：

1. **并发写入冲突**
   - 多个 cron / 手动触发同时写入同一记忆文件，导致覆盖或丢行。

2. **重复执行污染**
   - checkpoint 被高频重复触发，导致 `MEMORY_INDEX.md`/`decisions.jsonl` 噪声增长。

3. **长期记忆污染**
   - 将流水型 checkpoint 直接写入 `MEMORY.md`，造成长期记忆失真和 token 成本上升。

4. **权限泄露**
   - 记忆文件权限过宽（如 644）时，同机其他账户可读取敏感上下文。

5. **检索范围过宽**
   - QMD 路径配置为全量通配（`**/*.md`）时，可能将不应检索的私密内容纳入索引。

---

## Security Baseline (v2)

本项目当前安全基线：

- **Idempotency**: 支持 `--window hour|day`，同时间窗内防重复写。
- **File Locking**: 关键 append 使用 `flock`，并发写入可控。
- **Durability**: 写入后 `fsync`，降低异常中断导致的数据丢失概率。
- **Memory Hygiene**: checkpoint 不直接写 `MEMORY.md`。
- **Permission Hardening**:
  - `memory/` 目录：`700`
  - 新建 memory 文件：`600`

---

## Operational Hardening Checklist

建议在生产环境执行以下加固：

1. **最小检索范围**
   - 为 QMD 配置明确白名单路径（避免全量 `**/*.md`）。

2. **归档策略**
   - `decisions.jsonl` 按月归档，避免单文件无限增长。

3. **大小阈值监控**
   - 对 `MEMORY_INDEX.md`、`decisions.jsonl` 设置体积告警阈值。

4. **权限巡检**
   - 定期验证 memory 目录与文件权限是否漂移（700/600）。

5. **变更审计**
   - 所有记忆脚本改动必须经过 code review 与 commit 记录。

---

## Incident Response (Minimal)

当发现记忆污染/异常写入时：

1. 立即停掉相关 cron 任务。
2. 备份当前 `memory/` 目录。
3. 检查 `decisions.jsonl` 是否存在重复 idempotency key。
4. 清理异常重复行（保留最新一条有效事件）。
5. 恢复 cron 并观察下一轮执行日志。

---

## Reporting Security Issues

如果发现安全问题，请在仓库提交 issue（可标注 `security`），并提供：

- 复现步骤
- 影响范围
- 建议修复方案

> 当前仓库暂无专用私密披露邮箱，建议先通过私有渠道联系维护者。