# 原始 stream 溯源与脱敏说明（PROVENANCE）

正式盲测的**原始** CLI stream（`claude_stream.raw.jsonl`）包含本机运行元数据——主机名、
宿主绝对路径、`session_id`、临时 workspace 路径——因此**不在公开仓库中分发**。

公开仓库提供的是逐条脱敏后的 `claude_stream.sanitized.jsonl`：
- 保留全部消息结构、工具调用、模型输出、逐字轨迹（内容零改动）；
- 仅将主机名 / 宿主绝对路径 / `session_id` / `agent_ws` 临时路径 / 内部代理主机
  替换为占位符（`<HOST>` / `<HOME>` / `<PROJECT_ROOT>` / `<WORKSPACE>` /
  `<SESSION_ID>` / `<PROXY_HOST>`）；
- **不改动** 每条消息自带的随机 `uuid` / `parentUuid`（属 stream 内部结构，非 PII）。

## 原始 raw 文件的 SHA256（本地留存，可按需私下提供核验）

| 文件（原始，未公开） | SHA256 |
|---|---|
| `submission/official_run/claude_stream.raw.jsonl` | `6329e20108e33ce1f56620837c4f52e9301866e4223e634d48627ce24eeb4a34` |
| `runs/skfolio_002_official_20260722_03/records/claude_stream.raw.jsonl` | `6329e20108e33ce1f56620837c4f52e9301866e4223e634d48627ce24eeb4a34`（与上同一文件） |
| `runs/skfolio_002_official_20260722_01_invalid/records/claude_stream.raw.jsonl` | `3bc414a52fa5ec0ba995200daf59018292bde0427b86ef1773c13d9957b8f9a5` |
| `runs/skfolio_002_official_20260722_02_invalid/records/claude_stream.raw.jsonl` | `08856cdebbd2d82cfe2cf47056393410454175972ef8d99beac9c781decf3043` |
| `submission/official_run/claude_stream.redacted.jsonl`（旧脱敏版，已被 sanitized 取代） | `3d970ba38042d204e2d21fa39bc63ee5066314f1fd18135115bd2b954ade671f` |

> 原始 raw 未做任何内容修改；上表 SHA256 为其未修改状态的指纹。如需核对
> sanitized 版确由该原始 raw 派生（仅占位符替换、无内容增删），可对照原始 raw
> 与 sanitized 的逐行 diff（差异应仅限于上述占位符 token）。
