# 会话存储

PiCode 在各代理程序原生的会话存储之上使用一份共享的元数据目录。写入对话记录与恢复自身会话仍由代理程序负责。不存在需要同步或迁移的第二份对话数据库。

| 代理程序 | 发现方式 | 恢复方式 |
| --- | --- | --- |
| Pi | 已配置的 Pi 会话目录 | 原生会话文件 |
| Oh My Pi | 代理目录下的 `sessions` JSONL 文件 | 原生会话文件 |
| Claude Code | `CLAUDE_CONFIG_DIR/projects`,默认 `~/.claude/projects` | 原生会话 ID |
| Codex | `CODEX_HOME/sessions`,默认 `~/.codex/sessions` | 原生线程 ID |
| DeepSeek | `DSH_HOME/storages/session_projcache/sessions`,默认 `~/.dsh` | 目前经由已安装的 JSON-RPC 服务器不可用 |
| OpenCode | 在存在运行时/会话适配器之前不建立索引 | 不可用 |

非 Pi 的侧栏标识按代理程序划分命名空间。恢复 ID 与存储路径是两回事:不透明线程 ID 绝不能当作删除路径使用。侧栏按规范化后的项目目录分组会话,与代理程序无关。缺失的代理程序安装不会隐藏它们已保存的历史。

PiCode 只在自身偏好中保存展示层的覆盖项(置顶、隐藏行与标题)。Pi/OMP 使用原生标题变更;其他被重命名的会话会获得一个本地标题覆盖。发现过程只读取 JSONL 文件有限的头部/尾部区域,因此长历史的消息计数只是估算值。Claude/Codex 的历史在打开对话时加载,文本历史会被规范化为 PiCode 的展示格式。这不会复现每一种原生工具/事件类型。

DeepSeek 的 `session/prompt` 调用的是 `agents.create`,而不是 `agents.resume`。已保存的 DeepSeek 会话会出现在目录中,但打开时会报告这一限制,而不是新建一个对话。实现原生恢复需要 DeepSeek 服务器协议扩展;增加一个本地对话数据库无法解决该运行时的限制。PiCode 新建的 DeepSeek 会话使用唯一 ID。

如果扫描变慢,可以加入一个可重建的 SQLite 元数据/搜索缓存。它应缓存文件路径、代理程序、原生 ID、修改时间与搜索字段;原生存储仍应保持权威。超出环境变量与默认路径的、特定于代理程序配置的根目录,需要显式的发现配置。
