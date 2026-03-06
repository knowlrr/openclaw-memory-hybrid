# OpenClaw Memory Hybrid（中文说明）

这是一个 **OpenClaw 记忆系统增强层**，定位是：

- 保留 OpenClaw 原生记忆能力（`memory-core + qmd`）
- 增加更工程化的流程层（checkpoint / decisions / 索引）
- 不替换、不绕过 OpenClaw 的原生内存后端

---

## 一、为什么要做 Hybrid

OpenClaw 原生 QMD 的优势：
- 语义检索能力好
- 引用链路清晰
- 和 OpenClaw 配置/作用域控制高度一致

memory-hub 风格的优势：
- 决策和任务有结构化轨迹
- 有可审计的 checkpoint 过程
- 便于做自动化维护

Hybrid 的目标就是两者取长补短：
- 检索靠 QMD
- 过程靠轻量脚本
- 文件格式保持 OpenClaw 默认兼容（`MEMORY.md`、`memory/YYYY-MM-DD.md`）

---

## 二、目录说明

- `scripts/checkpoint_hybrid.py`：混合记忆 checkpoint 执行器
- `docs/qmd-config-template.jsonc`：QMD 配置模板

运行后会写入：
- `memory/YYYY-MM-DD.md`（每日日志）
- `memory/decisions.jsonl`（结构化决策事件）
- `memory/MEMORY_INDEX.md`（轻量索引）

---

## 三、快速开始

```bash
python3 scripts/checkpoint_hybrid.py --workspace ~/.openclaw/workspace
```

可选：每 6 小时执行一次

```bash
0 */6 * * * /opt/homebrew/opt/python@3.10/bin/python3.10 /path/to/openclaw-memory-hybrid/scripts/checkpoint_hybrid.py --workspace /Users/you/.openclaw/workspace >> /Users/you/.openclaw/workspace/memory/hybrid-checkpoint.log 2>&1
```

---

## 四、v2 加固点（重点）

### 1) 幂等保护（防重复写）
- 支持 `--window hour|day`（默认 `hour`）
- 同一时间窗内重复触发会 `skipped (idempotent)`，不重复写入

### 2) 并发安全写入
- 关键 append 使用 `flock` 文件锁
- 写后 `fsync`，降低并发和异常中断下的数据丢失风险

### 3) 避免长期记忆污染
- checkpoint **不再直接写入 `MEMORY.md`**
- 长期记忆建议由人工/整理任务定期提炼

### 4) 权限收敛
- `memory/` 目录默认 `700`
- 新建记忆文件默认 `600`
- 降低同机其他账号读取风险

---

## 五、建议的运维策略

1. **`MEMORY.md` 只放长期结论**
   - 偏好、关键决策、稳定事实
   - 不要放高频流水 checkpoint

2. **`decisions.jsonl` 定期归档**
   - 建议按月切分（如 `decisions-2026-03.jsonl`）

3. **QMD 路径做白名单**
   - 避免 `**/*.md` 全量扫描私密目录

4. **做健康巡检**
   - 检查重复 checkpoint
   - 检查文件体积增长
   - 检查权限漂移（非 600/700）

---

## 六、非目标（明确边界）

- 不替换 OpenClaw memory 插件
- 不直接修改向量库内部数据
- 不绕过 QMD 的 scope / update 策略

---

## 七、适用场景

- 希望保留 OpenClaw 原生记忆生态
- 同时希望有可审计、可自动化、可维护的记忆流程层
- 需要长期运行且降低“记忆文件失控增长”风险
