# PiCode — 构建与交接笔记

> 活文档。如果你是接手这份工作的编码代理:**先读这个文件,再读 `README.md`(原始产品规格)**。随着开发推进更新此文件 —— 它是代码里看不见的那些推理唯一栖息的地方。请保持它最新,否则下一个代理会重新踩一遍你的坑。

---

## 1. 这是什么

PiCode 是 **`pi` 编码代理的原生 macOS 客户端**。它**不是分支**:`pi` 仍是运行时,仍是会话/信任/设置的事实来源,也是唯一与模型对话的东西。PiCode 会:

- 把 `pi --mode rpc` 作为子进程启动(每个活动会话一个子进程),
- 在子进程的 stdio 上使用 Pi 文档化的 JSONL RPC 协议,
- 在受 Codex 启发的三栏窗口(侧栏 / 对话记录 / 检查器)中渲染对话,
- 读取 Pi 自己的会话文件、`trust.json`、`settings.json` 与 git 状态,为对话记录补充上下文(文件变更、用量、树、终端历史)。

PiCode 发明的一切都是附加的、可逆的。Pi 永远不会知道 PiCode 自己的偏好。

### 不可协商的规则(违反即为缺陷)

1. **绝不静默修改 Pi 的配置。** 不写 `~/.pi/agent/settings.json`、`auth.json`、`models.json`。PiCode 只写一个 Pi 拥有的文件,且仅作为用户操作的直接结果:`~/.pi/agent/trust.json`,使用与 Pi 的 `/trust` 相同的格式(§7)。
2. **绝不通过 shell 调用 `pi`。** 始终用 `Process` 配直接的 `executableURL`(见 `PiProcess.swift`)。永远不用 `sh -c`。这让进程树与信号可预测,也让用户数据不必经历 shell 引号转义。
3. **只使用 Pi 真正支持的 RPC 界面。** 若某能力仅限终端界面(树导航、`/trust`、主题列表、自定义 UI 组件……),PiCode 必须在界面中如实说明,而不是假装支持。这些情况在 §9 中列举,并且必须通过 `ExtensionCompatibilityNotice` / `CompatibilityCard` 呈现,绝不静默丢弃。
4. **只通过 Pi 的机制持久化信任。** 没有自制的信任存储,没有会写到别处的「记住我的回答」勾选框。
5. **绝不修改会话文件。** 它们只被只读解析。删除会话是独立的、需要显式确认的操作。
6. **只打开模型创作内容中的 http/https URL**(`WorkspaceLauncher.openWebURL`)。绝不替模型把本地 scheme、`file://` 或路径交给 `NSWorkspace.open`。
7. **「在终端中打开」不得要求自动化权限。** 它写一个临时 `.command` 文件并请访达打开它 —— 不用 AppleScript。
8. **使用 macOS 语义化颜色/材质与原生控件。** 绝不硬编码截图里的颜色。尊重减弱动态效果、键盘焦点与系统浅色/深色。不使用 OpenAI 的品牌、徽标或外观 —— 参考对象只影响信息架构。
9. **状态类是 `@Observable @MainActor`。** 不用 Combine 视图模型,不用 SwiftData。改用 JSON 存储(§6)。

---

## 2. 当前状态

| 领域 | 状态 |
| --- | --- |
| Xcode 项目(macOS 14 目标,Swift 5 模式) | ✅ 可构建:`** BUILD SUCCEEDED **` |
| 对全部源码执行 `swiftc -typecheck` | ✅ 干净 |
| RPC 层对照真实 `pi`(v0.85.1) | ✅ `./Tools/SmokeTest/run.sh` —— 全部检查通过 |
| JSON 边界(读 + 写) | ✅ `./Tools/SmokeTest/run-json.sh` —— 扫描器在每条真实会话行上与 Foundation 一致,2 万层嵌套安全 |
| 用全部真实会话做回放 | ✅ `./Tools/SmokeTest/run-replay.sh` —— 9908 行、9004 条对话记录行,无坏行/坏 ID/坏角色;同时证明折叠规则(见下一行) |
| 恢复真实会话(`--session`) | ✅ `./Tools/SmokeTest/run-open.sh` —— 只读验证,逐字节一致 |
| Pi 配置位置(重定位后的 `PI_CODING_AGENT_DIR` 等) | ✅ `./Tools/SmokeTest/run-paths.sh` —— PiCode 与 Pi 一致,已对照运行中的 `pi` 验证 |
| 对照真实扩展的扩展界面往返 | ✅ `./Tools/SmokeTest/run-extension.sh` —— 35 项检查全部通过,无模型调用 |
| 侧栏内容是真实的(没有隐藏的项目数据库) | ✅ `./Tools/SmokeTest/run-index.sh` —— 磁盘上 16 个会话文件 → 8 个项目,每个路径都存在 |
| 服务商、凭据、第三方服务商 | ✅ `./Tools/SmokeTest/run-providers.sh` —— 已对照运行中的 `pi` 验证,未触碰用户的任何凭据 |
| 侧栏行布局(同一尺寸,对话标题对齐项目名之下) | ✅ `./Tools/SmokeTest/run-sidebar-align.sh` —— 菜单第二轮改动后重跑:对齐偏差 0.0pt(项目名墨迹 38.0pt,会话标题 38.0pt),字形在搜索边距上(项目图标右移量)为完整 12.0pt,行距*精确*一致(28.0pt 接 28.0pt)。同一次运行还测量了搜索图标所在行:**图标中心 18.8pt,红绿灯按钮为 19.0pt** —— 应用的窗口是 `NavigationSplitView` 解析出的 `.unifiedCompact` 样式,因此 `SidebarStyle.titlebarRowCenter` 为 19,代理程序窗口已从 `.unified` 切换以保持一致(§10)。 |
| 侧栏行行为(点击项目折叠其对话;单一节奏;在搜索边距上高亮) | ⚠️ `./Tools/SmokeTest/run-sidebar-click.sh` —— 点击部分从绘制的胶囊测量:一次真实投递的点击让 5 行 → 3 行 → 5 行,项目高亮 28.0pt,对话同为 28.0pt(此前在行把内边距放在 `listRowBackground` *内部*时是 37.0pt)。节奏部分本轮为菜单的统一间距改动重写,**尚未运行**:它现在断言 项目→对话、对话→对话、对话→项目 的步距全部相等,而此前断言的是项目上方 12.0pt 的边距。 |
| 点击项目折叠其对话 | ✅ `./Tools/SmokeTest/run-sidebar-click.sh` 真实点击该行并测量胶囊与行距;搜索移到命令面板后,`AppState.showsChats` 现在是 `!isCollapsed`。 |
| 发现 / 启动 / 信任 / 会话索引 / git | ✅ 已实现 |
| 输入区:Return 发送,Shift+Return 换行,框形状,两行截断,框宽 | ✅ `./Tools/SmokeTest/run-composer.sh` —— 真实 `ComposerTextView`、真实按键事件:两种发送键模式下的 Return/Shift/Option/Command-Return;框对照 `ComposerMetrics.boxHeight(forEditor:)` 测量,编辑器在 1/2/3/6 行并截断到 `editorMaxHeight`,框在两个窗格宽度下对照对话记录行测量 —— **1300pt 时从 x 282.0 起 736.0pt,500pt 时从 x 22.0 起 456.0pt**,与 `maxContentWidth` 一致。`ComposerMetrics.boxTopPadding` 现为 0,因此框在两行下限时为 71.0pt,六行时为 135.0pt;测试夹具用同一套度量预测绘制的框,因此改动表现为测量数字随之移动。 |
| 输入区悬浮在对话记录之上,其下无内容 | ⚠️ 仅结构:`run-composer.sh` 断言源码中存在该覆盖层、内缩,且没有页脚。尚无人观察过长会话在框下滚动 —— 见 §11 |
| 对话记录、输入区、检查器(5 个窗格)、命令面板、设置 | ✅ 已实现 |
| 对模型的真实端到端提示词 | ⚠️ **尚未演练**(见 §11) |
| 对话记录对照 README 规格 | ✅ 已审计(§11);发现的差距已修复 |
| 安静行折叠(思考/命令/编辑/读取) | ✅ 规则,⚠️ 视图 —— `./Tools/SmokeTest/run-replay.sh`,本次改动后运行:8132 个安静步骤全部折叠(3190 个推理块、2809 条命令、1231 次编辑、902 次读取),0 项丢失,0 个非安静行被折叠,0 个相邻/被拆分的运行,每个折叠调用都有命令或路径可标识(9004 行 → 1608 行:872 个独立、87 个单步折叠、649 个运行;标题 `Run commands, thinking`×72、`Edited files, thinking`×60、`Thinking`×54、`Edited files, thinking, run commands`×48、`Edited files, thinking, run command`×41、`Run command, thinking`×40,以及更长的混合形式)。153 个真实折叠调用是失败或取消,必须保留其红色胶囊 —— 测试夹具会统计它们,但看不到胶囊。**未经**验证的是:视图本身 —— 折叠行看起来是否变暗、点击是否打开、嵌套步骤行及其差异统计是否渲染、推理是否以文本而非卡片形式打开。单独的步骤**没有折叠箭头**(该行本身就是控件);多步运行显示一个折叠箭头,打开其步骤列表。`Thinking` 按同一规则折叠,而不是由自己的行绘制;压缩也在同一区域重做;见 §11 第 12、13 项 |
| PROCESS.md | ✅ 本文件 |

仓库中没有任何内容是从 `/tmp` 生成或签入的;冒烟测试位于 `Tools/SmokeTest/`,它的用途是运行,不是随产品分发。

---

## 3. 构建、运行、验证

```bash
# 1. 快速类型检查(无需 Xcode,数秒)
SDK=$(xcrun --show-sdk-path --sdk macosx)
swiftc -typecheck -sdk "$SDK" -target arm64-apple-macos14.0 -swift-version 5 \
  $(find PiCode -name '*.swift')

# 2. 构建并运行应用
xcodebuild -scheme PiCode -configuration Debug -derivedDataPath /tmp/picode-dd build
open /tmp/picode-dd/Build/Products/Debug/PiCode.app

# 3. 对照真实二进制演练 RPC 层(无模型调用,无额度消耗)
./Tools/SmokeTest/run.sh

# 4. 其他检查(全部只读,无额度消耗)
./Tools/SmokeTest/run-json.sh     # JSON 扫描器 vs Foundation + 深嵌套
./Tools/SmokeTest/run-replay.sh   # 每个真实会话文件都过一遍对话记录构建器
./Tools/SmokeTest/run-open.sh     # 恢复最大的真实会话(副本)并重读
./Tools/SmokeTest/run-open.sh --small   # 最小的会话;同时对比本地树与 get_tree
./Tools/SmokeTest/run-paths.sh    # Pi 的配置/会话位置,对照运行中的 pi 检查
./Tools/SmokeTest/run-extension.sh     # 完整的扩展界面往返(对话框、状态、小组件)
./Tools/SmokeTest/run-providers.sh     # 凭据 + 模型配置文件,对照运行中的 pi 检查
./Tools/SmokeTest/run-index.sh    # 侧栏的项目是真实文件,不是隐藏数据库
./Tools/SmokeTest/run-sidebar-align.sh  # 侧栏行几何,按像素测量(图形界面)
./Tools/SmokeTest/run-sidebar-click.sh  # 点击项目折叠其对话,按像素测量(图形界面)
./Tools/SmokeTest/run-composer.sh       # 输入区的按键与框形状(图形界面)
```

冒烟测试是**对 `Models/`、`Services/` 或 `PiSessionController` 中 RPC 调用点任何改动的验收门禁。**它把应用仅依赖 Foundation 的那一半与 `Tools/SmokeTest/RPCSmokeTest.swift` 一起编译,在一个一次性目录里启动真实的 `pi --mode rpc`,并验证:

- 发现机制找到的是*可用的* `pi`(而不只是任何名为 `pi` 的可执行文件),
- 每条发出的命令都编码了文档化的方法名与字段名(Pi 会忽略未知字段,因此拼写错误否则不可见),
- `get_state`/`get_messages`/`get_available_models`/`get_available_thinking_levels`/`get_commands`/`get_session_stats`/`get_tree`/`get_fork_messages` 都有应答且能解析,
- `bash` 通过 Pi 自己的工具运行并返回输出,
- 未知命令产生 `success: false` 响应,并呈现为 `PiRPCError.commandFailed`,
- 事件被投递到 `onEvent`,
- `trust.json` **不会**被创建,
- 清理会移除一次性会话文件夹(通过 `get_state` 报告的路径找到,因此无需重新实现 Pi 的命名方案)。

冒烟测试为什么只编译 `Models/`、`Services/`、`Shared/`:这些文件按设计仅依赖 Foundation(§5),因此无需 SwiftUI 即可构建。请保持这一点 —— 如果需要新服务,不要在它里面 import SwiftUI。

其他检查之所以存在,是因为每一个都抓到过真实缺陷:

- **`run-json.sh`** 在每条真实会话行上把 `JSONScanner` 与 Foundation 交叉校验,另加转义、畸形输入、往返与 2 万层嵌套。它之所以存在,是因为 `JSONDecoder` 加递归 `JSONValue` 在 Pi 深度嵌套的 `get_tree` 响应上崩溃了(见 §10)—— 不要把扫描器「简化」回 `JSONDecoder`。
- **`run-replay.sh`** 把每个真实会话文件推过 `JSONLDecoder → PiSessionEntry → TranscriptBuilder`,并断言:没有无法解码的行,没有重复/空的标题 ID,没有未知角色或条目类型,每个工具结果都按 `toolCallId` 匹配到调用。它还检查对话记录的折叠规则(`TranscriptRows.group`,从 `Features/Conversation/` 引入,因为它只依赖 Foundation):折叠让每一项仍可到达,只有 思考/命令/编辑/读取 行会折叠,一次折叠是一个最大运行段(没有两个相邻分组,没有被拆开的运行段),每个可折叠项最终都折叠了(推理也算),每个折叠调用都带有可标识它的命令或路径。那里不绘制任何东西 —— 仍需人眼确认的部分见 §11。
- **`run-open.sh`** 完全按侧栏的方式恢复真实会话(`pi --mode rpc --session <copy>`),断言 Pi 恢复的是*那个*会话、本地构建的树与 Pi 的 `get_tree` 一致(小会话)、`get_state.messageCount == get_messages.count`、`get_entries(since:)` 恰好返回游标之后的条目,以及事后文件未改变。它在**副本**上工作,因此这里的缺陷不会损坏真实历史。不带参数时它选取已索引的最大会话 —— 但绝不选本进程所源自的那个(`PI_SESSION_FILE`),因为在这个仓库里工作的代理会让自己的会话成为最大,而一个仍在追加的多兆字节文件无法在测试夹具的 30 秒预算内翻页完成(`get_entries` 会超时,看起来像 PiCode 的缺陷,其实不是)。
- **`run-paths.sh`** 在子进程中解析 `PiPaths`(环境变量每进程只读一次,因此每个用例都需要新进程),然后在一个临时配置目录里启动一次性的 `pi --mode rpc`,确认 Pi 确实写在 PiCode 声称的位置:`PI_CODING_AGENT_DIR`、`PI_CODING_AGENT_SESSION_DIR`、`settings.json` 的 `sessionDir`、它们之间的优先级、波浪号展开,以及相对路径会被忽略而不是被猜测。它之所以存在,是因为 `PiPaths` 曾被硬编码为 `~/.pi/agent`(§7),那会让 PiCode 把信任决定写到一个 Pi 从不读取的文件里。
- **`run-extension.sh`** 让真实的 `PiSessionController` 对照真实的 `pi --mode rpc` 工作,使用一个安装在临时代理目录里的一次性扩展(`Fixtures/ExtensionUI/picode-ui-test.ts`),并像用户那样应答对话框。它覆盖 `select`(选择非默认项)、`confirm`、`input`、`editor`(预填 → 草稿 → 应答)、客户端取消、**Pi 自身的对话框超时**、`notify`(全部三个级别)、`setStatus`/`setWidget` 的设置*与*清除、`setTitle`、`setEditorText`,以及 `unsupported` 方法路径 —— 然后断言 `stats.assistantMessages == 0`、无对话记录行、无 token、无协议警告,且没有 `trust.json`。**它从不发送模型请求**:Pi 在本地执行扩展命令,而测试夹具除非 `get_commands` 先列出该斜杠命令(`source: extension` 条目),否则拒绝发送它。注意协议的形态:`prompt` 响应只在扩展的处理函数返回后才到达,因此测试夹具并发地触发发送,与应答对话框的循环同时进行。

以上没有任何一项发送模型提示词。请保持这样:PiCode 的额度属于用户。

- **`run-index.sh`** 通过列出 Pi 会话目录实际包含的每个会话文件,并检查每个文件都映射到磁盘上存在的项目目录、置顶/隐藏会话只是*装饰*该列表、`UserDefaults` 中没有缓存任何项目或会话列表,来回答「侧栏里的项目是真实的吗?」。PiCode 没有项目数据库:侧栏是 `SessionIndex.loadAllProjects()` 的投影,按每个会话规范化的 `cwd` 分组。请保持这样。
- **`run-sidebar-align.sh`** 与 **`run-sidebar-click.sh`** 是两个测量*像素*的检查工具。二者都在窗口中渲染真实行结构的模拟,自行捕获该窗口(无需屏幕录制权限),并对照从 `SidebarView.swift` 中提取的 `SidebarStyle` 编译,因此被测的数字就是随产品发布的那些;二者还会 grep 视图,检查这些数字所假定的接线。二者都需要图形界面会话(不能走 SSH)。
  - `run-sidebar-align.sh` 检查几何:对话标题与其项目名从同一 x 开始;项目字形以完整宽度落在距 `SidebarStyle.sidebarMargin`(搜索框左边缘)`projectIconRightShift` 的位置;对话与其项目名之下的距离,等于它与另一个对话之下的距离 —— 现在精确相等,因为不再有行给自己加垂直内边距。行距来自在项目名自身 x 列中测得的墨迹*中心* —— 测量整行会让文件夹字形进入项目的跨度并造成偏差,这正是它过去报告的 1.5pt 假差异。它还会 grep 视图,检查模拟无法覆盖的项:侧栏中没有任何 `.font` 携带 `.regular` 以外的字重,`SidebarRowChrome` 不添加垂直内边距,且恰好剩下一个 `Divider()`(页脚的那个 —— 搜索框下方的分隔线是有意去掉的)。它会转储 `/tmp/picode-sidebar-look.png`,即整列的模拟,以便人来判断机器无法判断的颜色。
  - `run-sidebar-click.sh` 检查行为与高亮的几何。其模拟中的每一行都绘制一种不同的饱和填充(红、品红、青、绿、黄 —— 各是一对不同的高亮通道),因此可以**按颜色**找到、测量并**统计**行:五行、折叠、胶囊高度与行距全部来自矩形,而不是墨迹。然后它*通过窗口自身的事件路径点击某一行* —— `NavigationSplitView` 侧栏、`List`、`Button` 等等都包含在内 —— 断言对话折叠消失又回来。是投递事件而不是分发事件:SwiftUI 在鼠标按下时运行事件跟踪循环,因此 `sendEvent` 派发按下与抬起会让测试夹具死锁。它的几何主张只有一条行距:四个胶囊的顶部给出 项目→对话、对话→对话、对话→项目,三者必须一致(它们过去在对话上方是 28.0pt、在项目上方是 40.0pt,同时 12pt 边距落在项目行上)。它会转储 `/tmp/picode-sidebar-click.png`。
  - 二者都通过 `Tools/SmokeTest/WindowPixels.swift` 读取像素,该文件用固定布局把捕获重绘进缓冲区。不要改回直接读取 `NSBitmapImageRep(cgImage:).bitmapData`:在这台机器上捕获返回的是 alpha *在前*,因此一个深灰像素会被读成亮红,颜色测试会测量错误的矩形却报告成功。
  - 二者捕获的是窗口的**内容视图**,不是窗口。见 §10:对位于另一个窗口之后的窗口做窗口服务器捕获会得到纯黑,而测试夹具可以与应用共享屏幕。
  - `run-sidebar-click.sh` 绘制自己的纯色背景(`.scrollContentBackground(.hidden)` 加整个分栏视图后面的一个 `Color`)。侧栏 `List` 使用材质,材质不会出现在 `cacheDisplay` 捕获中(它们解析为透明 → 黑),而包含两个表面的捕获没有统一的背景(§10)。同一次捕获还解释了为什么该测试夹具按颜色统计行:绘制在饱和填充上的文字返回时带色,因此按墨迹统计行会漏掉蓝色胶囊下的那一行,在画出五行时报告四行(§10)。
- **`run-composer.sh`** 是输入区的门禁:它对照真实源码编译 `ComposerTextView`,把它放进真实窗口中,并投递真实按键事件 —— 两种 `SendKey` 模式下的 Return、Shift-Return、Option-Return、Command-Return、Escape,带与不带建议列表 —— 断言输入区请求会话做什么*以及*编辑器里仍有什么,因为文本里多出一个换行符的「已发送」依然是错的。按键映射无法从选择器名推断(§10),因此测试夹具断言映射本身。然后它在真实编辑器里设置 1、2、3、5 行文本,并测量 SwiftUI 给它的高度(22/40/40/40pt),因为一个自身没有尺寸的 `NSViewRepresentable` 会被赋予它的最大高度,而输入框曾静默地是一个恒定的 220pt 高(§10)。它还会从捕获中测量提示框 —— 84pt 高,对照 `ComposerMetrics.boxHeight(forEditor:)` 而不是字面量 —— 以及框在同一捕获中对照绘制的对话记录行的宽度,分别在一个宽(1300pt)和一个窄(500pt)窗格下,因此「框与内容同宽」是一个测量得到的主张而不是期望。它会 grep 源码,检查两种编译方式都成立的结构:控件行顺序(附件 · 访问 · 模型 · 思考 · 发送)、有意移除的控件确实不存在、输入区后面没有容器背景、输入区是对话记录上的 `.overlay` 且其高度交给 `ConversationView.bottomInset`,以及其下没有页脚(没有 `ExtensionStatusBar`)。需要图形界面会话。它看不到的:从外部看覆盖层。渲染真实的 `SessionView` 需要活的控制器,因此「最后一行结束在框上方,更早的行从它下方经过」依赖于代码形态加上一次人工观察(§11)。
- **`run-providers.sh`** 在一个一次性的 `PI_CODING_AGENT_DIR` 中演练 `PiProviderService`,然后询问运行中的 `pi` 对这些文件的看法:`0600` 权限、掩码指纹(绝不打印密钥)、无临时残留的原子写入、编辑过程中 OAuth 条目与未知字段得到保留、畸形条目污染缺陷及其修复、拒绝覆盖无法解析的文件、自定义服务商往返(随后 Pi 自己的 `get_available_models` 会列出它们)、凭据对运行中的会话是活的而 `models.json` 服务商不是,以及读取用户真实配置不改变任何东西。

### 环境(本机)

- macOS 15.3.2,Xcode 16.4,Swift 6.1.2(语言模式 5),arm64。
- `pi` v0.85.1,位于 `~/.nvm/versions/node/v24.15.0/bin/pi`(包:`.../lib/node_modules/@earendil-works/pi-coding-agent`)。
- 安装命令(来自 Pi 文档):`npm install -g --ignore-scripts @earendil-works/pi-coding-agent`,或 `curl -fsSL https://pi.dev/install.sh | sh`。

---

## 4. 架构地图

```
PiCode/
├── PiCodeApp.swift            @main:WindowGroup(RootView) + .commands + Settings 场景
├── App/
│   ├── AppState.swift         @Observable @MainActor 根状态:启动阶段、发现、
│   │                          项目索引、打开的会话控制器、命令面板、表单、
│   │                          提示条/横幅、`run(_ PaletteCommand)`
│   └── PaletteCommand.swift   唯一的动作枚举(title/icon/requiresSession/group/…)。
│                              菜单、快捷键、命令面板与工具栏全部经由它路由。
├── Models/                    (仅 Foundation)
│   ├── JSONValue.swift        JSON 模型 + JSONCoding(解码/行编码器)
│   ├── JSONScanner.swift      迭代式 JSON 读写器(深层载荷下栈安全;键排序)—— 支撑 JSONCoding
│   ├── RPCModels.swift        RPCCommand/RPCResponse、PiModel、PiCommand、PiMessage、
│   │                          PiSessionEntry、PiTreeNode、PiForkPoint、PiSessionState、
│   │                          PiSessionStats、PiUsage、ExtensionUIRequest、兼容性提示
│   ├── PiEvent.swift          Pi 发出的每个 RPC 事件,作为类型化枚举 + `typeName`
│   ├── TranscriptItem.swift   可渲染模型:行、FileChange、QueueSnapshot、工具运行
│   ├── Project.swift          Project、SessionRef、ProjectTrustState、git 状态类型
│   └── ExtensionUI.swift      通知/状态/小组件/活动模型
├── Services/                  (仅 Foundation,不含 SwiftUI)
│   ├── PiRPCClient.swift      子进程 + JSONL 分帧 + 请求/响应关联
│   ├── PiProcess.swift        Process 封装:管道、直接执行、终止报告
│   ├── JSONLDecoder.swift     严格 LF 分帧(多字节安全,缓冲区有上限)
│   ├── PiDiscoveryService.swift  找到*经过验证*的 pi;拥有启动 PATH 规则(§8)
│   ├── SessionIndex.swift     只读扫描 Pi 的会话目录(绝不写入);
│   │                          `PiPaths` 拥有重定位规则(§7)
│   ├── ProjectTrustService.swift 与 Pi 兼容的 trust.json 读写 + 锁 + 最近祖先
│   ├── PiProviderService.swift 读取/报告/修复 Pi 的 auth.json + models.json,并询问
│   │                          `pi auth check` 判断就绪状态(§7)—— PiCode 写 Pi 拥有的
│   │                          配置的唯一位置
│   ├── GitStatusService.swift 经 /usr/bin/git -C 使用 porcelain v1 -z + numstat -z
│   ├── PreferencesStore.swift PiCode 自己的偏好(Application Support 中的 JSON)
│   ├── DraftStore.swift       按会话的输入区草稿(JSON)
│   ├── PiDiagnosticsLog.swift 内存中、需主动启用、有上限的环形缓冲(绝不持久化)
│   └── WorkspaceLauncher.swift 打开/显示/终端/剪贴板/URL 规则
├── Shared/
│   ├── Utilities/FileSystem.swift、Formatters.swift
│   └── Text/ANSI.swift、Markdown.swift、SyntaxHighlighter.swift   (仅语义化颜色)
├── Features/
│   ├── Root/            RootView(三栏 + 检查器 + 覆盖层宿主)、ContentHeader(会话
│   │                    列自带的页眉)、SetupViews(引导)
│   ├── Sidebar/         SidebarView(项目行折叠其对话)、搜索、置顶/隐藏/删除
│   ├── Session/         PiSessionController(大脑)、SessionView、TerminalPanel
│   │                    (对话下方的 Pi bash 界面)、TranscriptBuilder、
│   │                    TranscriptExporter
│   ├── Conversation/    ConversationView、ConversationLayout(共享的内容
│   │                    列)、MarkdownView、TranscriptRowView、ToolCallCard
│   ├── Composer/        ComposerView、ComposerTextView(AppKit NSTextView)、TrustViews
│   ├── Inspector/       InspectorView(单一产物查看器 + 通知)、
│   │                    InspectorPanes(TerminalPane 是面板的主体;旧的标签页
│   │                    在最后一个引用消失前保留)
│   ├── Extension/       ExtensionChrome(小组件/状态/通知)、ExtensionDialogHost
│   ├── Palette/         CommandPaletteView、Sheets(重命名/压缩/派生/删除)
│   ├── Settings/        SettingsView(通用/输入区/会话/服务商/Pi)、
│   │                    ProvidersSettingsView(凭据 + 自定义服务商)
│   └── Shared/          UIComponents(BannerView、StatusPill、DiffStatView,……)
└── Tools/SmokeTest/     run*.sh + *Test.swift + Fixtures/(见 §3)
```

**`PiSessionController` 是心脏。** 如果要添加行为,顺序通常是:(1)新的 `RPCCommand` 分支,(2)控制器里的刷新/`request` 调用,(3)控制器上的新字段或一个 `TranscriptItem` 分支,(4)视图。不要把协议逻辑放进视图。

---

## 5. 分层规则

- `Models/`、`Services/`、`Shared/` 是**仅 Foundation**。这正是 `Tools/SmokeTest` 得以存在的原因。不要在那里 import SwiftUI/AppKit。
- 只有 `App/`、`Features/`、`PiCodeApp.swift` 可以 import SwiftUI/AppKit。
- 视图读取状态并调用控制器方法;它们绝不解析 RPC,绝不触碰会话文件,绝不生成进程。
- 控制器是 `@MainActor`;进程 I/O 发生在 `PiProcess`/`PiRPCClient` 的后台队列上,并通过 FIFO 辅助函数 `PiSessionController.deliver { … }` 跳回。
  **原因:** 扩展界面对话框必须按 Pi 发送它们的顺序出现。`DispatchQueue.main.async { MainActor.assumeIsolated { … } }` 保持顺序;非结构化的 `Task {}` 不会。

---

## 6. 关键决策及其理由

| 决策 | 理由 |
| --- | --- |
| **用 JSON 存储而不是 SwiftData** | 持久化状态很小(偏好、草稿、置顶/隐藏 ID)。SwiftData 会带来 schema、迁移面和外部存储却毫无收益 —— 还会让模型层无法用于 `swiftc` 冒烟测试。`PreferencesStore`/`DraftStore` 把纯 JSON 写入 Application Support。 |
| **每个活动会话一个 `pi --mode rpc` 子进程** | Pi 的 RPC 模式按设计是单会话的。独立子进程意味着某个项目的崩溃或中止不会拖垮其他项目。`AppState.pruneControllers(limit: 4)` 关闭超出上限的最久未使用者。 |
| **确定性的对话记录 ID** | 实时流式行必须被 `get_messages`/`get_entries` 返回的持久行替换,且不能闪烁或产生重复行。ID 派生自稳定输入(消息 id/角色/序号、工具调用 id),因此同样的内容会哈希到同一行。`agent_settled` 触发完整对账。 |
| **工具/bash 执行状态放在侧表(`toolRuntime`/`bashRuntime`)** | 一次工具调用先作为实时事件出现,再作为持久对话记录内容出现,之后可能再次更新。把执行状态集中在一处并作为**覆盖层**应用到基础项与实时项之上,可防止两个来源互相矛盾。 |
| **实时助手行使用预测的基础索引** | 这样它们落地后 ID 就与持久行一致。 |
| **已有会话用 `--session <path>`,否则新建** | Pi 文档化的恢复方式。 |
| **信任按运行用 `--approve`/`--no-approve` 固定** | 让用户每次启动只回答一次「信任这个项目?」,而不必让 PiCode 背着用户写 Pi 的配置。 |
| **`NSViewRepresentable` 包 NSTextView 作为输入区** | 需要它来按 `PreferencesStore.SendKey` 决定 Return 的含义(`returnKey` 与 `commandReturn`)、禁用智能替换,并在不与 SwiftUI `TextField` 较劲的前提下支持斜杠/`@path` 补全。该判断读取的是**事件的修饰键**,不是选择器:纯文本视图把 Shift-Return 报告为普通的 `insertNewline:`,把 Command-Return 报告为 `noop:`,因此只看选择器的分支会在 Shift-Return 时发送,并让 Command-Return 模式无法发送(两者都曾发布,现在都由 `run-composer.sh` 断言)。Shift 始终表示「增加一行」,Option 始终表示「排队一条跟进」。 |
| **输入区是一个框加一行控件** | 编辑器、附件标签与控件都位于 `ComposerMetrics.cornerRadius` 的单一圆角形状内,其后没有任何东西绘制第二个形状 —— 输入区区域下方没有条形材质 —— 因此它读起来像页面上一个整体对象。一行,按提示词的组装顺序:附件 · 访问 · 模型 · 思考 · 发送。从这里移走的一切仍可到达:插话与跟进是 `Return`/`Option-Return`,排队消息是对话记录行,停止会把它们放回编辑器(`interrupt()`,文档化的 Stop),硬中止是「代理」菜单中的 `⌘.`。访问控件是 Pi 真正拥有的那个 —— 项目信任,在其弹出说明中解释为*项目资源*,而不是沙箱,因为 Pi 始终以用户自己的权限运行。 |
| **发送键上没有 `.keyboardShortcut(.return)`** | 它会与文本视图自己的 Return 处理重复触发。 |
| **图片走 RPC `images`;文本文件以内联的围栏 `@path` 块引入** | Pi 只接受图片作为附件。其他文件以内联 Markdown 方式引入以便模型读取,围栏块标出路径。`AttachmentLoader` 对既非图片也非文本的内容以清晰信息拒绝。 |
| **树检查器只读** | `navigateTree` 只属于 SDK/扩展,不在 RPC 中(§9)。PiCode 显示树,并提供派生/克隆加一条明确的兼容性说明。 |
| **终端窗格运行 Pi 的 `bash` RPC** | 它*不是*真正的 shell。它展示代理运行了什么,并让用户通过同一工具运行一次性命令。工作区菜单的终端面板(`TerminalPanel` → `TerminalPane`)是这个界面当前的家,绘制在对话下方,因此命令及其输出离开会话也能看见。若要交互式 shell,「在终端中打开」会打开一个真正的终端。 |
| **输入区悬浮,并在两行处停止** | 两个独立改动,目标相同:输入区应是页面上的小对象,而不是占据窗口底部的面板。(1)编辑器被截断到 `ComposerMetrics.editorMaxHeight`(40pt = 18pt 下两行),超过则滚动 —— 实测 1/2/3/5 行分别为 22/40/40/40pt。(2)对话记录占满整列高度,输入区作为 `.overlay(alignment: .bottom)` 绘制在其上,因此最后一行从框*下方*经过,框上方有淡出。两者都需要 `ConversationView.bottomInset = composerHeight + 16`:覆盖层不占空间,因此没有该内缩时最后一行会永久被遮住。高度是真实的,不是常量 —— `ComposerHeightKey` 通过 preference 把测得的高度回传。这块空间绘制在 1pt 底部锚点*之上*的同一个 `VStack(spacing: 0)` 中,而不是作为其下方的内边距:`scrollTo(anchor: .bottom)` 会把被标识视图的底边与视口对齐,因此在锚点之后绘制的空间会在回合自动滚动时被滚出视野,最新一行最终紧贴输入框。锚点保持 1pt,因此「固定到底部」仍指最底部,且这块空间无论对话记录是短(无需滚动)还是长(回合流式期间自动滚动)都必须一致。 |
| **对话记录与输入区共用一列** | `ConversationLayout` + `ConversationColumn` 持有内容列,对话记录行与悬浮输入区都在其中布局。人会说出名字的那个数字是*内容*的宽度 —— 736pt,行与框测得的宽度 —— 因此 `maxContentWidth` 保存它;框架的上限(`maxColumnWidth`,780pt)由它加上两侧各 22pt 的留白推导而来。覆盖层不从它所悬浮的视图继承任何东西,因此输入框过去与*窗格*同宽而行却停在上限处 —— 一条宽度是对话两倍的条。内边距位于上限*之内*(先 `padding` 再 `frame(maxWidth:)`),因此宽窗格停在 `maxColumnWidth` 并得到 `maxContentWidth` 的文本宽度,窄窗格仍能得到留白;把两者顺序颠倒会在每种尺寸下产生 44pt 的误差,而把留白放进 `maxContentWidth` 是同一个误差偏移一个常量 —— 这就是为什么测试夹具用*窗格减去留白再取上限*预测输入框,而不是用上限本身(那样它会与自己的错误一致)。输入框自身的内边距、控件行上方的间隙与 `boxHeight(forEditor:)` 出于同样原因都放在 `ComposerMetrics`:测试夹具用它们预测绘制的框,而不是用字面量。 |
| **终端面板是输入区下方唯一的东西** | 用户从工作区菜单打开的面板,不是这条规则所移除的常驻状态页脚:它是一块显式的、可调整大小的、可关闭的*区域*(VS Code 自己的安排),输入区仍锚定在它上方的对话记录而不是窗口底边。它只在 `isTerminalVisible` 时绘制,因此默认窗口仍是悬浮输入区的布局。它的主体运行 Pi 的 `bash` RPC,因此 PiCode 绝不 fork 登录 shell。 |
| **输入区下方不渲染任何内容** | 页脚状态行(`ExtensionStatusBar`:运行时、模型、思考、信任、分支、上下文百分比、工具计数、扩展状态)与编辑器下方的扩展小组件条都已移除。其中没有任何独有信息:对话记录有自己的系统行用于流式/压缩/重试/队列,上下文窗格有模型/思考/上下文/工具计数/状态/小组件,`InspectorView` 显示分支,窗口副标题显示模型。悬浮输入区下方的页脚还会把它重新锚定到底边,而这正是两行截断要避免的观感。编辑器上方的小组件、横幅、信任提示与连接通知都保留;扩展以 `belowEditor` 位置设置的小组件会绘制在框上方的同一个堆栈中而不是被丢弃,因为 PiCode 已没有它下方的位置。上方的终端面板是有意的例外,且仅因为它是一块面板而不是装饰。 |
| **检查器 → 输入区通过 `AppState.composerInsertion` 引用** | 无状态的一次性交接(设置字符串 → 输入区消费并清除)。避免跨视图树伸手进输入区的 `@State`。 |
| **「变更」窗格排除 `.read` 文件触碰** | 包含读取的变更列表不是变更列表。会话变更与 git 变更作为同一窗格的两个来源提供。 |
| **对话记录错误始终可见** | 绝不放折叠之后。 |
| **`PiDiagnosticsLog` 在内存中且需主动启用** | 它可能包含文件内容与提示词。有上限的环形缓冲,绝不写入磁盘;仅在 `recordRPCPayloads` 开启时渲染。 |

| **会话树在本地构建,绝不获取** | 在一个 787 条目的会话上 `get_tree` 耗时约 32 秒,并阻塞 Pi 的请求队列(因此会延迟用户的下一条提示词)。树是纯 `parentId` 结构,所以 `PiTreeNode.buildTree` 能瞬间从条目推导出来,并与 Pi 的输出完全一致(`run-open.sh --small` 证明了这一点)。 |
| **条目只读一次,之后用游标跟随** | 完整的 `get_entries` 耗时约 20 秒且 Pi 不会缓存它,而 `get_entries(since:lastId)` 耗时约 0.01 秒。每个会话完整读一次,之后每个回合增量追加 —— 热路径上没有任何东西会拖住下一条提示词。 |
| **手写的迭代式 JSON 扫描器** | `JSONDecoder` 加递归 `JSONValue` 在 Pi 嵌套的 `get_tree` 载荷上崩溃(SIGBUS)。该扫描器在任意深度都栈安全,并且比 `try?` 链式解码器更快;它还让发出的载荷具备确定性(键排序)。 |
| **`PiPaths` 解析 Pi 自己的重定位规则** | Pi 可以通过 `PI_CODING_AGENT_DIR`、`PI_CODING_AGENT_SESSION_DIR` 或 `settings.json` 的 `sessionDir` 被移动,而 PiCode 以继承的环境启动 `pi`,因此两者必须就配置所在位置达成一致。这是正确性问题,不是外观问题:PiCode 会写 `trust.json`,如果 Pi 读的是另一个文件,用户的回答会被忽略,而 PiCode 却报告该项目已受信任。 |
| **回复从提问的那条消息派生** | Pi 只在用户条目处分叉(`get_fork_messages`),因此规范中「每条助手消息支持分支/派生」是通过给每个助手/思考行关联产生它的用户条目来兑现的。Pi 得到一个它接受的派生点,返回的文本就是用户可以编辑并重发的提示词。`run-replay.sh` 断言每条回复都有一个,且它是活动分支上的用户条目。 |
| **`picode://` 链接由对话记录提供,而不是由每一行提供** | 链接处理器与 `\.piCodeOpenFile`/`\.piCodeOpenChange` 动作在 `ConversationView` 中一次性设置,那是唯一知道项目路径、可据此解析相对引用的地方。这个功能的第一版发布了一个从未被人提供的处理器,因此点击文件引用静默无反应。如果你新增对话记录动作,要在那里提供它,并检查点击路径,而不只是编译。 |
| **带超时的扩展对话框在本地解除** | Pi 会用 `timeout` 自行解决对话框且从不通知客户端,因此留在屏幕上的卡片会邀请用户回答一个已不存在的问题。PiCode 镜像该截止时间(提前四分之一秒,这样回答绝不会与 Pi 竞速)并在活动时间线中说明。这里有意不设「已过期」卡片状态 —— 一个死掉的问题不该看起来还能回答。 |
| **扩展命令获得耐心的 `prompt` 超时** | Pi 只在文本被处理后才应答 `prompt`,而扩展命令由它自己的处理函数处理,可能在一个对话框上停几分钟。普通提示词保持 60 秒的预检预算;Pi 报告为扩展命令的斜杠命令获得与 `bash` 相同的耐心预算。 |
| **PiCode 只写两种 Pi 文件** | `trust.json`(与 `/trust` 写入的同一份文档),以及仅在「设置 → 服务商」中显式点击时,按 Pi 文档化格式写入的 `auth.json` 与 `models.json`。Pi 配置目录下的其他一切都是只读的,且没有任何凭据会被读回界面。在添加第三种之前,先问为什么用户不能在 `pi` 自己里做。 |
| **侧栏是投影,不是数据库** | `SessionIndex.loadAllProjects()` 每次刷新都读取 Pi 的会话目录;置顶与「隐藏」标记只是装饰结果。`run-index.sh` 守护这一点:一旦加入缓存,侧栏就可能开始与终端对「存在什么」的判断产生分歧。 |
| **项目是一行,不是分区标题** | 侧栏列表样式中的 `Section` 是带展开箭头的可折叠分组 —— 对一份镜像磁盘内容的列表来说是错的。该行*就是*展开控件:点击它折叠其对话(`AppState.toggleCollapsed`,作为装饰持久化),且折叠优先于搜索 —— `showsChats` *首先*询问 `isCollapsed`,因为一个覆盖了已文档化点击行为的查询与一个坏掉的查询无法区分。作为一行,它还与它的对话共享前导内缩,这正让「对话标题与项目名从同一处开始」变得精确而不是两点修正。字形绘制在其行的左侧,因此它落在搜索框旁边,而这个位移只影响绘制,所以名称 —— 以及其下每个对话标题 —— 不会移动:`projectIconShift`(9pt)是它曾经左移的距离,`projectIconRightShift`(6pt)是菜单随后要求它回到的距离,`projectIconOffset`(3pt)是实际应用值的唯一名称。它的高亮是 `Button` 的高亮:一个由 `rowHighlightInset`(`= sidebarMargin`)内缩的 `listRowBackground` 胶囊,**内缩作用在形状上,而不是行上** —— `listRowBackground` 会填满行的整个单元格(包括它自己的内缩与任何内边距),因此给行加内边距会把空气放进胶囊*内部*。正因如此,菜单的第二轮改动删除了每一条垂直边距而不是微调某一条:一个项目高亮在带 12pt 内边距时变成 37.0pt 高,而对话是 28.0pt,而「一切之间等距」只有在没有任何行给自己加内边距时才是结构性的。两种行都经过同一个 `SidebarRowChrome`,因此绘制胶囊的地方只有一处,这也是项目与对话可以只在颜色上不同的原因。`run-sidebar-click.sh` 真实点击该行并测量胶囊与行距。 |
| **推理是一个步骤,安静行会折叠** | `bash`、`edit`/`write`、`read` 与 `thinking` 是真实会话会重复的东西:在这里的 16 个真实会话中,调用总共是 **4942** 次(2809 条命令、1231 次编辑、902 次读取),另有 **3190 个推理块** —— 8132 行在反复说同一件事。其他每个工具名都是人真正想读的东西,因此 `QuietFamily.of` 精确知道这些形态,其余一切保留自己的卡片:连续五次的 `grep` 与连续五次的命令不是同一种噪声形态,因为折叠的意义在于用户已经知道那一行会说什么。折叠是*呈现*,因此它是条目列表的**纯函数**(`TranscriptRows.group`),放在一个仅依赖 Foundation 的文件中 —— 回放测试夹具引入它,并在此处运行过的每个会话上检查该规则(8132/8132 个安静步骤被折叠,无丢失,无非安静行被折叠,无被拆分的运行段)。 |
| **折叠什么与如何命名这次运行,是同一个函数** | `QuietFamily.of(item)` 同时回答两个问题 —— 这一行是否折叠,以及这次运行叫什么 —— 因此一次运行的成员与其名称绝不可能是两个不同的集合。`TranscriptRows.group` 当且仅当 `of` 返回一个类别时折叠该项,而 `groupTitle` 恰好枚举这些类别;测试夹具通过要求*每个*可折叠项最终都落在某个分组内来断言二者一致(`foldedThinking == thinkingBlocks` 正是抓到「想把推理排除在运行之外」这一念头的检查)。因此添加一个类别就是在同一个枚举里加一个 case,而不是在分组逻辑里加一个新分支。 |
| **运行段在遇到任何非相邻安静步骤时结束** | 两个步骤之间的助手消息、孤立结果或不可折叠工具都是边界,因此一次运行就是*连续的*步骤,别无其他。「把一个回合里的所有编辑分组」会在一段解释文字下面画一条线并称之为一个动作,而那是对代理做了什么的一种 PiCode 实际无法知道的主张。它还意味着一处折叠始终是最大化的,这是测试夹具能够断言的属性(没有两个相邻分组;没有两个相邻的安静步骤留在各自的行里)。推理在运行段*内部*而不是边界,因为在 Pi 的输出里它与它所推理的调用交错:若把它当边界,几乎每个分组上方都会留下一行 `Thinking`,那是换了个排布的同样噪声。 |
| **折叠行以其*第一个*条目为键** | `.group` 的 id 是 `group-<首个条目 id>`。一个回合是流式的:分组会在用户阅读时从一次调用增长到六次,如果 id 跟随内容,每次追加调用都会给该行一个新身份,SwiftUI 就会重建它 —— 在用户光标下把折叠行重新合上。以头部为键,该行在增长期间保持其身份与 `@State isExpanded`。 |
| **折叠行保留其实时状态;失败留在其步骤上** | 折叠的全部意义在于用户没有在读那些调用,因此任何他们需要据此行动的东西都必须留在该行上:运行中的调用保留其转圈,且回合进行中时,包含失败或取消的运行会显示 `Failed`/`Cancelled`,即使其内容已关闭。该行不统计步骤数,也不绘制时长 —— 标签旁的摘要(命令、文件)设置在比正文字号小两档(`Typography.codeBlockCompact`),运行自身的行列出类别,步骤的耗时则不显示;已结束运行的 `Worked for …` 标题是唯一留下的时长,它属于回合而不是步骤。此处会话中有 150 个真实折叠调用是失败或取消。*已结束的* `Worked for …` 行不重复失败:那时回合已结束,红色胶囊会变成一条用户已经翻过去的状态条,因此失败属于步骤自身并留在运行内部的步骤上。同一规则适用于运行内部 —— `ToolActionRow` 标记失败的调用并给其图标上色,因为「哪一个坏了」正是展开列表存在的意义。这也是为什么失败句子(「该工具报告失败,但没有输出」)属于 `ToolCallContent` 而不是卡片的页眉:卡片可能被折叠,折叠行可能被展开,而这句话在两种形态下都必须存在。 |
| **两层展开,一个缩进步长** | 一次运行展开为一个列表,列表内的一个步骤展开为其内容。一次点击不可能打开六份输出 —— 那正是要被移除的噪声 —— 而*单个*步骤也不该需要一次点击,因此单步分组跳过中间列表直接打开其内容(`ToolGroupView` 依据 `items.count == 1` 分支)。每一个嵌套的东西 —— 运行内的步骤、调用摘要下方的输出、推理自己那行下方的文本 —— 都按同一个常量 `ConversationLayout.nestedIndent`(15pt)缩进,因为在 736pt 的列里缩进两步会让输出只剩明信片宽。 |
| **折叠箭头只表示一件事:这一行会打开一个列表** | 每条折叠行 —— 运行页眉、其中的 `Thinking` 步骤、嵌套的 `ToolActionRow` —— 都是用户点击的一行暗色文本。对话左侧一列小箭头比折叠本身更占地方,因此可供性主要就是那一行:整行是 `.plain` 按钮内的 `.contentShape(Rectangle())`,hover 会提起暗色,提示条说明点击会做什么。单独一步完全不显示折叠箭头 —— 它下面没有列表,点击会在右侧面板打开其内容。多步运行显示唯一的那个折叠箭头,表示将打开列表,因为那是唯一一种「点击做了这一行本身无法展示的事」的情形。绝不使用 `DisclosureGroup`:系统样式会在前导槽位画一个折叠箭头,*并且*把该行的字形挪得与其他所有行的图标不对齐。临时的「Pi 正在工作」行已移除;运行自身的行承载转圈。 |
| **一次压缩是一个事实,不是一份文档** | `.compaction` 行只画一行 —— `[图标] 压缩上下文`,用户切换分支时 Pi 写入的条目则显示 `分支摘要` —— 别无其他。旧行会在对话中间打印一个徽章加整个摘要的着色框,那正是对话记录折叠功能要移除的噪声,而摘要文本只是对刚被替换掉的回合的压缩,没有人会去读。Pi 的两种摘要是不同的事实(一个把上下文折叠掉了,另一个描述被留下的路径),因此构建器把消息*角色*映射到 `SummaryKind`,而行从中取标签与字形 —— 这些字形与 `PiSessionEntry` 在会话树中使用的相同,因此树与对话记录用同一种方式命名同一个事件。文本并未丢弃:它在行的上下文菜单里,并在导出的对话记录中完整地放在同一标题下。 |
| **共享内容从卡片里移了出来** | `ToolCallContent` 绘制参数、文件变更、输出、截断提示、失败句子与结构化结果;`ToolCallCard`(非安静工具)与 `QuietStepContent`(被折叠的,由 `ToolGroupView` 与 `ToolActionRow` 共同绘制)共享它。一次 `edit` 的差异统计与一次 `read` 的文件标签绝不能在两种形态之间产生分歧,卡片也因此少了约 140 行。卡片保留自己的装饰(图标、名称、状态胶囊、折叠箭头、拷贝按钮);折叠行保留自己的页眉。`QuietStepContent` 也是*另一种*形态所在之处:推理步骤绘制其文本而不是调用的卡片,因此它的行与主体在一处选定,而不是在两个都能打开单个步骤的视图里各选一次。 |

---

## 7. Pi 的磁盘格式(已对照 v0.85.1 验证)

### Pi 的文件在哪里

绝不硬编码 `~/.pi/agent`。Pi 会自我重定位,而 PiCode 以继承的环境启动 `pi`,因此它必须解析出与 Pi 的 `config.js` 相同的路径:

| 优先级 | 代理目录 | 会话目录 |
| --- | --- | --- |
| 1 | `PI_CODING_AGENT_DIR` | `PI_CODING_AGENT_SESSION_DIR` |
| 2 | `~/.pi/agent` | `settings.json` 中的 `sessionDir` |
| 3 | — | `<代理目录>/sessions` |

波浪号路径、`file://` URL 与绝对路径都被接受;*相对*的 `sessionDir` 会被忽略而不是被猜测,因为 Pi 会相对于工作目录解析它,而工作目录随项目变化。这一切都在 `PiPaths`(`SessionIndex.swift`)中,并由 `./Tools/SmokeTest/run-paths.sh` 对照运行中的 `pi` 检查。

已知缺口:Pi 会把项目的 `.pi/settings.json` 合并到全局配置之上,因此项目可以设置*自己的* `sessionDir`。PiCode 只索引一个全局目录,所以该项目的会话不会出现在侧栏中。目前无人遇到;若你遇到,修法是按项目发现会话,而不是改用全局 `sessionDir`。

### 服务商(PiCode 唯一写入的配置)

有两个文件决定会话可以使用哪些模型,二者都归 Pi 所有:

| 文件 | 形态 | 由谁写入 |
| --- | --- | --- |
| `<代理目录>/auth.json` | `{ "<provider>": { "type": "api_key", "key": … } }` 或 `{ "type": "oauth", "access", "refresh", "expires" }` | Pi 的 `/login`;PiCode 的「设置 → 服务商」 |
| `<代理目录>/models.json` | `{ "providers": { "<name>": { "baseUrl", "api", "apiKey", "models": [ … ] } } }` | Pi 的 `/setup-custom-providers`,或手工编辑;PiCode 的「设置 → 服务商」 |

由 `./Tools/SmokeTest/run-providers.sh` 对照运行中的 `pi` 证明的事实:

* `auth.json` 是**整体读取**的。一个 Pi 无法解析的条目(例如一个形似服务商但缺少 `"type"` 的条目)会让*每个*服务商都报告 `invalid_state`。修复意味着移除该条目,绝不靠猜。
* 会话运行期间新增的凭据**确实**会被拾取(Pi 会检查文件修订号),大约在半秒内 —— 无需重启。
* 添加到 `models.json` 的服务商在进程重启前**不会**生效:`get_available_models` 仍保留旧目录。这就是「设置」面板提供「重启会话以应用更改」的原因。
* `apiKey` 可以是字面量、`$ENV_VAR` 或 `!command`。PiCode 让引用保持可见,绝不展开它们。
* Pi 在读取时校验该文件,但 PiCode 拒绝覆盖它无法解析的文件,并保留它不编辑的字段(`compat`、`headers`、`samplingParams`、`thinkingLevelMap`),因此这里的编辑不会静默丢弃某人的定制。
* `pi auth check --provider <id> --json --no-refresh` 无需网络调用即可回答就绪状态。`pi auth print-api-key` / `print-bearer-token` 与 `--credentials` 存在但属禁区:凭据仍归 Pi 所有。

`settings.json` 中的 `enabledModels` 只是 Ctrl+P 的循环范围,且由 Pi 自行维护,因此 PiCode 不碰它。

### 会话

```
<会话目录>/--<将 / 与前导 / 替换后的路径>--/<ISO8601>_<uuid>.jsonl
```

- 每行一个 JSON 对象,LF 结尾。
- 头部行携带 `type`、`id`、`cwd`、时间戳;后续条目是**v3 树**,由 `id`/`parentId` 链接。
- 目录名是 `--private-var-…--` 风格:前导 `/` 变成 `--`,内部 `/` 变成 `-`,名称以 `--` 结尾。`SessionIndex.decodeDirectoryName` 会反转这一过程,且是**有损的** —— 它只在头部的 `cwd` 不可用时作为回退。
- PiCode 读取这些文件;它绝不重写它们。

### 信任

```
<代理目录>/trust.json   { "<绝对规范化路径>": true|false }
```

- 键排序、2 空格缩进、结尾换行 —— 与 Pi 的写入器逐字节兼容。
- 查找走**最近祖先**:对 `/a/b` 的决定覆盖 `/a/b/c`。
- Pi 的锁文件是 `<file>.lock` **作为一个目录**(用 `mkdir` 创建)。`ProjectTrustService` 镜像这一点,并在 15 秒后恢复过期锁。
- 需要信任的资源:`.pi/settings.json`、`.pi/extensions`、`.pi/skills`、`.pi/prompts`、`.pi/themes`、`.pi/SYSTEM.md`、`.pi/APPEND_SYSTEM.md`、项目的 `.agents/skills`。
- 截至撰写时,这台机器上 `~/.pi/agent/trust.json` **并不存在**,且冒烟测试断言 PiCode 绝不把它作为副作用创建出来。
- 由于 PiCode *确实*会写这一个文件(仅在用户显式决定之后),代理目录必须是 Pi 的真实目录 —— 见上文 `run-paths.sh`。

### Git(「变更」窗格使用)

- `git -C <path> status --porcelain=v1 -z`:`<XY> <path>\0`;对于重命名,**下一个** NUL 分隔的记号是源路径。
- `git -C <path> diff --numstat -z`:`<added>\t<deleted>\t<path>\0`。
- 以 `/usr/bin/git` 加 `-C` 调用,绝不经 shell。

---

## 8. 你还会再次踩到的环境陷阱(已修复 —— 不要回归)

`pi` 以 Node 脚本形式发布(`#!/usr/bin/env node`)。在真实机器上有两件事会破坏发现机制:

1. **另一个同名程序遮蔽了它。** 在这台机器上 `/opt/homebrew/bin/pi` 是一个 2023 年的 Python 脚本,它会以 `ModuleNotFoundError: No module named 'pi'` 失败,而它在登录 shell 的 PATH 上**排在最前**。因此 `command -v pi` 返回的是错误的程序。
2. **一个旧 `node` 遮蔽了正确的那个。** 这里的 `/usr/local/bin/node` 是 Node 18.16.0,而 Pi 需要现代的 Node;当 `/usr/local/bin` 排在 nvm bin 目录之前时,`pi --version` 会在 Pi 的包内部死掉。

后果,两者都已实现:

- `PiDiscoveryService` 通过运行 `pi --version` **验证**每个候选,只返回可用的安装。它先试登录 shell 的命中项,再试静态候选列表,然后试每个 `~/.nvm/versions/node/*/bin/pi`(最新优先)。失败信息会记录登录 shell 命中项被拒的原因。
- `PiDiscoveryService.launchEnvironment(executable:shellPath:)` 返回的 PATH **以可执行文件自身所在目录开头**,然后是移除了该条目的登录 shell PATH。发现(`--version`)与应用的 RPC 启动(`PiSessionController`,以及冒烟测试)都经过它,因此 `pi` 始终在它安装时所配的 Node 下运行。

如果在新机器上发现失败,请打印 `.missing(searched:shellPath:detail:)` 载荷 —— 它列出了尝试过的每条路径以及登录 shell 命中项失败的原因。`SetupViews.swift` 会把同样的信息呈现给用户。

---

- **用 `open(path, 'w').write(...)` 写文件会先截断它。** 如果写入随后抛错 —— 本应是字符串的地方给了元组就够了 —— 文件会留在 **0 字节**,而 `git status` 只把它显示为「已修改」。这已经让本文件付出过一次恢复的代价。请写入临时路径再 `os.replace()`,或在写入前断言替换已匹配,并在事后检查行数。

## 9. RPC 协议说明

分帧:每行一个 JSON 对象,**仅 LF**;CRLF 通过剥离末尾 CR 来容忍。`JSONLDecoder` 绝不把 U+2028/U+2029 当作分隔符,并且只在整条记录可用之后才解码 UTF-8(多字节安全)。记录上限为 32 MiB。

关联:每个请求都发送 `id`;响应会回显它。`PiRPCClient` 维护 `pending[id] → continuation` 加一个超时工作项(`defaultTimeout = 60s`)。`sendAwaitingResponse(_:timeout:)` 是冒烟测试用来探查线格式的原始路径;应用使用类型化的 `send(_:)`。

响应失败会抛出 `PiRPCError.commandFailed(command:message:)`,控制器把它变成对话记录中可见的错误。

已实现的命令(`RPCCommand`,名称已对照 `docs/rpc.md` **以及**已安装的包验证):`get_state`、`get_messages`、`get_available_models`、`get_available_thinking_levels`、`get_commands`、`get_session_stats`、`get_entries(since:)`、`get_tree`、`get_fork_messages`、`get_last_assistant_text`、`set_model`、`cycle_model`、`set_thinking_level`、`cycle_thinking_level`、`set_steering_mode`、`set_follow_up_mode`、`set_auto_compaction`、`set_auto_retry`、`set_session_name`、`prompt`、`steer`、`follow_up`、`abort`、`abort_retry`、`abort_bash`、`clear_queue`、`new_session(parentSession:)`、`switch_session(path:)`、`fork(entryId:)`、`clone`、`compact(customInstructions:)`、`export_html(outputPath:)`、`bash(command:)`。

花过时间才学到的注意事项:

- 流式输出期间,`prompt` **必须**携带 `streamingBehavior`(`steer`/`followUp`),否则 Pi 返回错误。PiCode 把排队的发送改为走 `steer`/`follow_up`。
- 缺省的可选项必须保持**缺省**,而不是 `null`(`compact`、`new_session`、`export_html`、`get_entries`)。冒烟测试锁定了这一点。
- Pi 在某些地方会静默忽略未知字段与未知*值* —— 这就是那些线格式断言存在的原因。

事件(`PiEvent`,`Models/PiEvent.swift`):`agent_start`、`agent_end`、`agent_settled`、`turn_start`、`turn_end`、`message_start`、`message_update`、`message_end`、`bash_execution_update`、`tool_execution_start/update/end`、`queue_update`、`compaction_start/end`、`auto_retry_start/end`、`summarization_retry_*`、`extension_error`、`extension_ui_request`,以及必须保留而不是丢弃的 `unknown(type:)`。记录日志时用 `typeName`;没有 `name` 属性。

`message_update` 携带增量;**`message_end.message` 才是权威。** 实时部分内容由 `message_start` 加增量组装,并在 `agent_settled` 时对账。

### 扩展界面

> **已端到端验证**,由 `./Tools/SmokeTest/run-extension.sh` 对照运行中的 `pi` 与一个一次性扩展完成。它暴露了两个真实缺陷 —— 在触碰扩展路径之前请先读这两条:
>
> 1. **`timeout` 的单位是毫秒。** 它是线格式上唯一以毫秒计的时长,而 `Format.duration` 接收秒,因此直接透传会把 1.5 秒的超时打印成「25m 0s」。请使用 `ExtensionUIRequest.timeoutSeconds`,绝不使用原始字段。
> 2. **Pi 会自行解决带超时的对话框却不通知我们。** 客户端没有自己的计时器,因此卡片会在 Pi 已按默认答案继续之后仍留在屏幕上 —— 邀请用户回答一个已不存在的问题。`PiSessionController.scheduleDialogTimeout` 现在镜像该截止时间(提前四分之一秒,因此回答绝不会与 Pi 自己的竞速),并在活动时间线中记录「扩展请求已过期」。这里有意不设「已过期」对话框状态:卡片消失,时间线解释原因。
>
> 另外:**`prompt` 响应只在扩展命令的处理函数返回后才到达**,这可能与它最慢的对话框一样久。因此 `promptTimeout(for:)` 给扩展命令与 `bash` 相同的耐心预算,避免长对话框伪造出「prompt 失败」错误。

- **对话框**(`select`、`confirm`、`input`、`editor`):Pi 会阻塞,直到客户端用携带同一 `id` 的 `extension_ui_response` 作答 —— `select`/`input`/`editor` 用 `value`,`confirm` 用 `confirmed`,或 `cancelled: true`。同一时间只呈现**一个**对话框;其余排队,对话框显示「还有 N 个在等待」。暗淡遮罩有意**不**可点击关闭:扩展的问题是决定,不是提示条。
- **即发即弃**(`notify`、`setStatus`、`setWidget`、`setTitle`、`set_editor_text`):显示(通知 / 状态栏 / 小组件条 / 窗口标题 / 输入区预填)或记入日志,绝不回答。
- **仅限终端界面、在 RPC 模式下退化** —— 以兼容性提示呈现:`custom()` 返回 undefined;`setWorkingMessage`、`setWorkingIndicator`、`setFooter`、`setHeader`、`setEditorComponent`、`setToolsExpanded` 均为空操作;`getEditorText()` 返回 `""`;`getToolsExpanded()` 返回 `false`;`pasteToEditor()` 退化为 `setEditorText()`;`getAllThemes()` 返回 `[]`;`getTheme()` 返回 `undefined`。
- **`navigateTree` 完全无法通过 RPC 使用**(仅 SDK/扩展),而 `/tree` 与 `/trust` 是终端界面命令。因此树检查器是只读的并提供派生/克隆;`/trust` 由 PiCode 自己的信任界面镜像,写入 Pi 的 `trust.json`。

### 读取路径的成本(在本机、v0.85.1 上测量)

Pi 一次只应答一个请求,因此一次慢读不只是卡住发出它的窗格 —— 它会延迟用户的下一条提示词。在一个真实的 5.5 MB 会话上测量,含 787 个条目 / 上下文中 144 条消息:

| 命令 | 成本 | PiCode 如何使用 |
| --- | --- | --- |
| `get_tree` | **约 32 秒** | **从不调用。** 树从条目在本地构建。 |
| `get_entries`(完整) | **约 20 秒**,无缓存 | 每个会话一次,且在 `refreshAll()` 中排在最后,让对话记录先绘制出来。 |
| `get_entries(since: <id>)` | **0.00–0.01 秒** | 每个已结算回合之后以及压缩之后。 |
| `get_messages` | 约 0.25 秒 | 每次刷新。 |
| `get_fork_messages` | 约 0.00 秒 | 与树/派生界面一起。 |
| `get_session_stats` | 约 0.00 秒 | 用量窗格。 |

由此固化进控制器的结论:

- `PiTreeNode.buildTree(from:leafId:)` 按 `parentId` 顺序从条目推导树。它已由 `run-open.sh --small` 在小会话上对照 Pi 自己的 `get_tree` 验证。绝不重新引入 `get_tree` 调用。
- `PiSessionController.refreshEntries()` 把 `lastEntryId` 作为持久游标:每个会话完整读一次,之后永远用 `since:` 追加。若游标被拒(Pi 重启到了另一个会话),则回退到完整读取。`isLoadingEntries` 防止两次并发的完整遍历,并驱动树窗格的进度状态。
- 因此长会话的首次加载需要约 20 秒的*后台*时间。那是 Pi 的成本,不是 PiCode 的缺陷;树窗格会说明这一点,而不是看起来卡住。

---

## 10. 花费代价换来的 API 事实(以免你重新发现)

- **`JSONValue` 除** `null`、`bool`、`number`、`string`、`array`、`object` **之外没有类型化枚举分支**。没有 `.int`/`.double`/`.string(_:)` 分支 —— 使用访问器(`string(_:)`、`int(_:)`、`double(_:)`、`bool(_:)`、`array(_:)`、`object(_:)`、`…Value`、`isNull`、`prettyDescription`),并用 `.number(Double(x))`、`.object([...])` 构造值。
- 解码经由 `JSONCoding.decode(_:)` / `JSONCoding.line(_:)`,它们由**`JSONScanner`**(迭代式、手写)支撑。`JSONDecoder`/`JSONEncoder` 配上 `JSONValue` 在深层嵌套载荷上会**爆栈**:`get_tree` 每个会话条目嵌套一层,一个 145 条目的会话曾在 `_CodingPathNode.path` 内部以 SIGBUS 让冒烟测试崩溃。只为小型类型化存储保留 `Codable` 支持(§5),绝不把 RPC 或会话数据走它。扫描器还让线格式上的键排序具备确定性。
- 扫描器与 `JSONSerialization` 有两处有意不同,都对 Pi 的输出无害且比失败更安全:重复的对象键保留最后一个值,孤立的 UTF-16 代理项变成 U+FFFD 而不是拒收整条记录。
- `get_session_stats` 的总计覆盖**整个会话历史**(每一条分支,包括已被压缩掉的消息),而 `get_state.messageCount` 是**活动分支**。在测试会话上:总计 780 对上下文中 144,用户 23 对 4。请把它们显示为不同的东西;只有 `contextUsage` 描述实时上下文窗口。
- `PiSessionState` 字段:`model`、`thinkingLevel`、`isStreaming`、`isCompacting`、`steeringMode`、`followUpMode`、`sessionFile`、`sessionId`、`sessionName`、`autoCompactionEnabled`、`autoRetryEnabled`、`messageCount`、`pendingMessageCount`。**没有** `error` 字段。
- `FileChange` = `{ id, path, kind, additions, deletions }`,其中 `Kind ∈ {created, modified, deleted, read}`,且**没有 `count`** —— 出现次数是计算出来的。`FileChange.Kind.gitStatus` 映射到 `GitFileChange.Status`。
- `QueueSnapshot` = `{ steering, followUp }`,元素为 `QueuedMessage { id, text }`,带 `isEmpty` / `update(steering:followUp:)`。控制器上的 `clearQueue()` 在本地丢弃它们并告知 Pi。
- `ActivityEntry` = `{ id, kind, title, detail, timestamp, isError }`,其中 `Kind ∈ {…, .extensionRequest, .notify}`。
- `PreferencesStore` 拥有:`appearance`、`sendKey`、`showInspector`、`showSidebar`、`defaultThinkingLevel`、`defaultModelQualifiedID`、`confirmBeforeDeletingSessions`、`notificationsEnabled`、`recordRPCPayloads`、`extraLaunchArguments`、`pinnedProjects`、`pinnedSessions`、`hiddenSessions`、`expandedProjects`、`lastProjectPath`、`reducedMotionOverride`。其他任何东西目前都不持久化 —— 要加就在这里加。`PreferencesStore` **不是**可观察的,因此界面必须重绘的任何东西都要镜像进 `AppState`(`expandedProjects` 在 `AppState.init` 中种入,并在每次切换时写回 —— 它保存的是对话*被显示*的项目,因为用户从未打开过的项目起始是折叠的;`isInspectorVisible` 是较旧的计算属性风格,也是那里可能出现「窗格重绘了吗?」这类缺陷的原因)。
- `AppState.InspectorTab` 是 `String, CaseIterable, Identifiable`,并暴露 `label`/`systemImage`(不是 `title`)。
- `PiDiagnosticsLog.limit` 是 internal,以便「设置」在帮助文本中描述它。
- `SettingsTab`(`general`、`composer`、`sessions`、`providers`、`pi`)是 `TabView` 的选中项;`AppState.openSettings(tab:)` 设置它,而*视图*负责把窗口提到前面(`AppState` 保持不含 AppKit)。`SettingsTab` 就放在 `SettingsView.swift` 中 `TabView` 旁边。
- `WorkspaceLauncher.openTerminal(at:)` 接受一个目录并返回 `URL?`。把它(或任何其他非 `Void` 的东西)直接放进 `Form` `Section` 内 `Button` 的 action 中,会产生一个*虚假的* SwiftUI 错误 —— 「return type of property requires that 'TableHeaderRowContent<…>' conform to 'View'」—— 指向 section 而不是那一行。请先丢弃该值(`_ = …`)并重新编译,再开始重写视图。
- **AppKit 的 Return 家族,实测值**(真实文本视图、真实按键事件;由 `run-composer.sh` 断言):

  | 按键 | 选择器 | `modifierFlags` |
  | --- | --- | --- |
  | Return | `insertNewline:` | 无 |
  | Shift-Return | `insertNewline:` | `.shift` |
  | Option-Return | `insertNewlineIgnoringFieldEditor:` | `.option` |
  | Command-Return | `noop:` | `.command` |

  两个陷阱:Shift-Return *不是* `insertNewlineIgnoringFieldEditor:`(因此只看选择器的分支会发送提示词),而 Command-Return 是 `noop:` —— 一个未声明的选择器(`Selector(("noop:"))`),只看选择器的分支永远匹配不到(因此 Command-Return 发送模式永远无法发送)。请改读 `NSApp.currentEvent?.modifierFlags`。
- **覆盖层不是它所悬浮内容的一部分。** `SessionView` 用 `.overlay(alignment: .bottom)` 绘制输入区,这正是让对话记录保持窗格全高的原因 —— 也意味着输入区*不*继承对话记录的任何布局:不继承它的内缩、不继承它的宽度上限、不继承它的留白。任何必须与行对齐的东西都要手工放进同一列(`ConversationColumn`)。同一种不对称也是 `ConversationView.bottomInset` 存在的原因:覆盖层不预留空间,因此必须*告知*对话记录其上方那个东西有多高,否则最后一行会永远活在它下面。这块空间绘制在 1pt 底部锚点**上方**(一个 `VStack(spacing: 0)`),因为 `scrollTo(anchor: .bottom)` 会把被标识视图的底部与视口对齐:绘制在锚点下方的内边距会被滚过去,因此间隙会在回合自动滚动时恰好消失。锚点保持 1pt,这样「已固定」意味着最底部,而不是一屏的余量。
- **先 `padding` 再 `frame(maxWidth:)`,绝不反过来。** 在 `ConversationColumn` 中,留白在宽度上限*之前*应用,因此宽窗格停在上限 `maxColumnWidth`(780pt,含其留白),窄窗格仍能得到留白。另一种顺序会先把内容限制到 `maxWidth` 再加内边距,这让一切都比它本该匹配的行宽 44pt —— 这个错误在代码里看起来是对的,只有作为测量宽度才可见(`run-composer.sh` 在两个窗格宽度下把输入框与绘制的行对比)。
- **自身没有尺寸的 `NSViewRepresentable` 会被赋予它的最大高度。** `ComposerTextView` 包裹了一个 `NSScrollView`,它不报告固有尺寸,因此 `.frame(minHeight: 26, maxHeight: 220)` 不是编辑器在其中增长的*范围* —— 而是一个恒定的 220pt 框,里面浮着一个 26pt 的编辑器。用户的抱怨(「把它做短一点」)的根因就在这里,而它在代码审查中不可见,因为这个修饰符读起来像一个钳制。修法:实现 `sizeThatFits(_:nsView:context:)`,对容器布局,并返回 `min(max(usedRect.height + insets, height(forLines: 1)), height(forLines: visibleLines))`。`run-composer.sh` 现在在 1/2/3/5 行测量编辑器,因此回归会表现为一个数字,而不是「框看起来又变高了」。
- **不要在 `sizeThatFits` 内部调整文本容器的大小。** 那句看起来显然该写的「确保宽度是最新的」—— `container.containerSize = NSSize(width: proposal.width ?? …, height: .greatestFiniteMagnitude)` —— 会在 SwiftUI 请求尺寸时使布局失效,返回的答案会过期并振荡:实测 1 行和 2 行正确(22pt、40pt),然后 3 行和 5 行又报 **22pt**,于是框在你打字时塌陷。`widthTracksTextView` 已经让容器与视图同宽;别去动它。(隔离出这个问题的探针同时给滚动视图的 frame *与*文本视图的 `usedRect` 加了检测;在 `22pt` 的框里看到 `used 54pt` 才定位到那个过期答案。)
- **SwiftUI 的 `.continuous` 圆角不是圆**(实测,由 `run-composer.sh` 断言):一个圆角矩形顶行的平直跨度比 `width - 2r` 窄,因此像素测量圆角无法反推出半径。对 300pt 的框,经 `WindowPixels.capture(_ view:)` 实测:半径 10 → 内缩 11.0pt,14 → 16.0pt,18 → 21.0pt,22 → 26.0pt,圆角高度 ≈ 半径 + 1.5(`.circular` 在 18 时 → 17.0pt,偏离该直线)。测试夹具用 `1.25 * radius - 1.5` 把测量值换算回去,容差 1.5pt —— **这是针对那条捕获路径标定的**;对同一个框做窗口服务器捕获会读到宽 3.5pt 的结果。
- **材质无法在 `cacheDisplay` 捕获中存活,而双表面捕获没有统一背景。** `WindowPixels` 通过把像素与捕获中最常见的亮度比较来挑选「墨迹」。两种会静默失效的方式:(1)侧栏 `List` 的材质在离屏绘制时是透明的并解析为黑,于是*每个*像素看起来都比背景暗 —— 某个测试夹具把整列读成一条 428pt 的「文本行」;(2)当捕获中同时包含颜色不同的侧栏与详情列时,众数亮度属于覆盖像素更多的那个,另一个表面就变成全墨。两个修法都已应用:在模拟中绘制纯色背景而不是依赖材质(`.scrollContentBackground(.hidden)` + 分栏视图后面的一个 `Color`),并用 `background(in:yRange:)`(被测区域的众数亮度)而不是整幅图来测量墨迹。那次失败看起来像行为缺陷(「点击项目不会把对话带回来」),其实是捕获缺陷。
- **不要拍摄被遮挡的窗口**:`CGWindowListCreateImage` 返回窗口服务器最后一次合成的内容,因此一个落到真实应用之后的测试夹具窗口会捕获出**纯黑** —— 而「输入框填充可见」这样的断言会报告内容缺失,而不是捕获损坏。因此三个视觉测试夹具都改为绘制视图(`WindowPixels.capture(_ view:)`),它不可能被遮挡,还顺便把标题栏与工具栏排除在画面之外。两个后果:输入区圆角标定比窗口捕获读到的窄 3.5pt;捕获的 y 现在从内容视图顶边开始 —— 而投递的鼠标事件坐标从底部开始,因此点击点是 `contentHeight - distanceFromTop`(标题栏在两者中都不存在)。
- **侧栏列表布局,实测**(`run-sidebar-align.sh` / `run-sidebar-click.sh`,macOS 15,`.listStyle(.sidebar)`):
  - 一个 `listRowBackground` 填满**整列** —— 在 140pt 的列中从 0 到 140pt,没有自己的内缩 —— 因此高亮胶囊若不想贴边就必须手工内缩;
  - 并且它填满行的整个**单元格**,包括它自己的内缩与任何内边距:一个给自己加了上下各 12pt 内边距的项目行,出来是 **37.0pt** 高,而对话是 28.0pt,它多出的空气落到了胶囊*内部*,而且内边距还改变了节奏 —— 因此菜单的第二轮改动删除了每一条垂直边距而不是微调某一条(§12)。(同时实测:`listRowInsets(top: 12)` 把胶囊移到约 29pt 且*完全没有间隙*,`listRowInsets(EdgeInsets())` 仍然横跨整列,一个 12pt 的间隔行产生了 28pt 的间隙 —— 见下一项。)
  - 行的内容有 **20pt** 的下限(`.listStyle(.sidebar)` 会忽略 `.defaultMinListRowHeight`:一个 40pt 的间隔行仍产生 48pt 的单元格),因此胶囊高度是 `max(20, content) + 8` —— 这就是为什么 17pt 的内容与 20pt 的内容都是 28.0pt 的胶囊,也是共享装饰的 `rowMinHeight` 依赖的东西;
  - **绘制在饱和填充上的文字返回时带色**:白色叠在纯蓝上落在 (229,229,255),偏离中性色 26 —— 超过 `WindowPixels.isText` 用来把彩色填充排除在墨迹计数之外的 ±24 —— 因此按墨迹统计行的测试夹具会静默漏掉蓝色胶囊下的那一行。它确实如此:画了五行,数出四行。请改为按颜色统计绘制的行;
  - 列表**行**比分区**标题**再多内缩约 2pt,而系统行内缩距侧栏边缘约 19pt,搜索框则在 10pt(因此 `projectIconShift = 9`,再叠加 `projectIconRightShift = 6`);
  - 侧栏列表行有约 27.5pt 的**最小高度**,而行*内边距*并不按它声称的数值增加:12pt 的 `.padding(.top)` 表现为约 9.8pt 的间隔,*并从被填充行下方的间隙中偷走 1.5pt*,这正是 项目→对话 与 对话→对话 差异的全部(26.5 对 28.0)。间隔行(`Color.clear.frame(height:)`)能让节奏精确,但会被 27.5pt 的最小值抬高;`.listRowInsets` 更糟(它偷走了 5.5pt);`.listSectionSpacing` 在 **macOS 上不可用**,因此按*分组*的间距无法直接表达。结论(现已发布):唯一处处精确相等的节奏就是列表自身的节奏,因此没有行在垂直方向给自己加内缩或内边距,也没有分组被分隔;
  - `Color.accentColor` 跟随*窗口的*焦点:macOS 会把非活动窗口的强调色画成灰色,因此强调色着色的行背景在侧栏不是关键视图时会变色。中性的 `Color.primary.opacity(0.08)` 不会 —— 因此 hover 与活动行共用一个灰色,这也说明两者是同一种陈述而不是两种;
  - `Image(systemName: "folder")` 在 `font(size: 15)` 下渲染出 16.5pt 的墨迹,因此固定的 15pt frame 不会把它裁掉;
  - **投递的鼠标事件不总能送达。** 一次运行中连点多次时,偶尔有一次落在空处 —— `run-sidebar-click.sh` 里「先折叠再展开」的那一对就是它显现的地方(期望五行时出现「屏幕上有 3 行」)。这是测试夹具的问题,不是应用的问题:模拟的行是一个切换 `@State` 的 `Button`,送到的点击总会切换它,重跑就通过。由此有两条结论。不要靠静默重试「修」它 —— 重试会掩盖这个测试夹具存在的唯一理由(那一个回归),而在每次点击前加 `makeKeyAndOrderFront` + `NSApp.activate` 让投递变得*更糟*而不是更好(实测:之前 8 次有 7 次干净,之后 4 次点击只有 1 次投递)。并且把孤立的折叠失败读作「重跑我」,而不是结果;§11 第 10 项是解决它的人工检查。
  - 窗口捕获的位图返回时是 **alpha 在前**,因此请通过 `WindowPixels` 读像素,绝不要通过 `NSBitmapImageRep.bitmapData`(§3)。
- **对话记录的折叠身份是 SwiftUI 的事实,不是外观问题。** 对 `TranscriptRows.group(items)` 做 `ForEach` 会以每行的 `id` 为键,而 `@State` —— 包括折叠行的 `isExpanded` —— 会在该 id 变化时被丢弃。因此一个分组的 id 是 `group-<首个条目 id>`,绝不是其内容的哈希:一个流式回合每一两秒就往一次运行里追加调用,而跟随内容的 id 会在用户阅读途中把折叠行重新合上。同样的推理适用于未来任何内容会增长的行。
- **折叠行不总是工具调用。** 一旦 `thinking` 加入折叠,一个对三个类别成立的假设在第四个上不再成立:推理项没有 `toolArguments`,因此它的 `foldedSummary` *按构造*就是空的(`toolInputSummary` 在没有可摘要内容时返回 `""`),而一个身份来自其摘要的折叠行会显示为空白。回放测试夹具的「每个折叠调用都有可标识它的一行」检查也出于同样原因必须收窄到 `item.kind == .toolCall` —— 推理有意由其类别名标识,因为初稿的中间截断片段什么也说明不了。任何遍历分组并假定有工具名、输出或差异统计的东西,都必须先问 `QuietFamily.of(item)`;现在有四个类别,而其中只有三个是工具。
- **空视图仍然要付它所在 `HStack` 的间距。** 当两个计数都是 `nil` 或零时 `DiffStatView` 什么都不画 —— 而每次 `read` 都是如此 —— 但产生它的 `ForEach` 仍参与该行,因此一次读取的行在空无一物前面留出了 6pt 间隙。请守卫*间距*(这里的做法是过滤出真正有数字的变更),而不是相信一个渲染为空的视图会什么都不占。
- **`NavigationSplitView` 解析出的是*紧凑*工具栏,不是统一工具栏。** 侧栏的搜索图标以窗口标题栏行为中心,而那一行在不同工具栏样式下高度不同。通过一个隐藏标题栏的窗口实测:`.unified` 给出 52pt 的带区、红绿灯按钮在 26pt,`.unifiedCompact` 是 38pt 带区、19pt,`.expanded` 是 44pt、30pt。应用的实际窗口测得 18.75pt,即 `.unifiedCompact` —— 这是 `NavigationSplitView` 为自己选择的样式 —— 而 `SidebarAlignTest` 构建的是 `.unified` 窗口,因此与一个应用从未使用过的常量(26)达成了一致。修法包含两半:`SidebarStyle.titlebarRowCenter = 19`,并把测试夹具窗口切换为 `.unifiedCompact`,以便它测量应用实际所处的环境。今后对标题栏行控件的任何测量都必须固定工具栏样式,否则它验证的是错误的窗口。
- 项目以 `PiCode/` 为根使用 `PBXFileSystemSynchronizedRootGroup`,因此 **`PiCode/` 下的新文件会自动加入 target** —— 无需编辑 `project.pbxproj`。添加在 `PiCode/` *之外*的文件(例如 `Tools/SmokeTest/`)会被正确地排除在应用 target 之外。

---

## 11. 接下来做什么(按优先级)

0. **认证仍只解决了一半。** 凭据与第三方服务商现在可以在「设置 → 服务商」中配置(`run-providers.sh`,§7),但 Pi 的*失败*消息仍以光秃秃的错误行显示。Pi 会说类似 `No API key for anthropic/claude-sonnet-4` 与 `Run '/login anthropic' to re-authenticate.` 的话;这些应渲染成一张引导卡片,带一个在 `pi` 处打开终端的按钮,而不是让用户自己去解读的文本。就绪状态已经存在(同一面板里的 `pi auth check --no-refresh`)—— 复用它来撰写卡片文案。绝不调用 `pi auth print-api-key`、`print-bearer-token` 或 `--credentials`。
1. **用真实提示词做端到端运行。** 直到模型调用为止的一切都已验证;真实的 `message_update` 流下游没有任何东西被实际观察过。选一个便宜的模型,在一个临时项目里发一行提示词,并确认:实时助手文本 → 持久行交接且不重复,工具卡片原地更新,`agent_settled` 对账无闪烁,排队的插话/跟进出现,token 用量条移动。预计要在这里修未知事件形态 —— 那正是这次演练的意义。
2. ~~**扩展界面往返。**~~ **已完成** —— `./Tools/SmokeTest/run-extension.sh` 让真实控制器对照一个真实扩展工作:每种对话框、客户端取消、Pi 自身的超时、通知、状态与小组件的设置/清除、标题与输入区预填,以及不受支持的方法路径。它不消耗额度(Pi 在本地运行扩展命令),它发现的两个缺陷已修复(§9)。仍需在图形界面中用眼确认:对话框卡片的层叠、「还有 N 个在等待」的队列计数,以及 Escape 是真正的取消而不是关闭 —— 测试夹具覆盖逻辑,不覆盖像素。
3. ~~**对照规范(`README.md`)审计对话记录行。**~~ **已完成** —— 发现并修复:文件引用是死链(环境动作从未被提供),变更标签无法打开规范所说的差异,回复没有分支操作,运行中的回合不是规范要求的紧凑耗时展开项。用户提示词现在也是后缘气泡。测试夹具未覆盖:向上滚动时流式输出的滚动位置稳定性,以及 bash 日志中的 ANSI 颜色 —— 在第 1 项的实机运行中用眼检查这两者。
4. **信任流程打磨。** `TrustViews` + `ProjectTrustService` 已存在,但完整的人工流程(未受信任项目带 `.pi/settings.json` → 批准 → 重启 → 徽章)还没走通,而且测试之后不该留下 `trust.json`。
5. **负载下的中断/中止路径**:流式输出中途 `abort`,命令运行期间 `abort_bash`,`interrupt()` 与 `abortRetry()` 的对比,以及回合中途的进程死亡(`onExit`)。
6. **会话生命周期**:`new_session`、`switch_session`、`fork`、`clone`、`compact`、`export_html` 都已实现但只被轻度使用。验证每一个都更新 `sessionFile`/`sessionId` 以及侧栏/临时行行为。
7. **辅助功能检查**:键盘焦点可见性、对话记录行与工具卡片上的 VoiceOver 标签、减弱动态效果得到尊重。
8. **向输入区粘贴附件。** `README.md` 承诺可以粘贴图片与文本文件(两处:输入区章节与对齐表),而目前只有文件选择器与拖放。编辑器是普通 `NSTextView`,因此这意味着在子类中覆写 `paste(_:)`/`readSelection(from:)`:剪贴板上的图片变成 `Attachment`,字符串仍保持文本。不要拦截纯文本粘贴 —— `@path` 引用是输入的,不是粘贴的,而一次静默变成附件的粘贴会让人意外。
9. **悬浮输入区,由人工看过一次。** 结构已被断言,但覆盖层从未在屏幕上被看过(这里没有屏幕录制权限,而渲染真实的 `SessionView` 需要活的控制器)。打开一个足够长的会话并滚动,检查:最后一行结束在框上方,更早的行从它*后面*经过并淡出,淡出效果在浅色与深色外观下都与对话记录背景匹配,编辑器从一行增长到两行时框不跳动,框的边缘与上方文本对齐(`run-composer.sh` 从两个窗格宽度测量过,但从未对照真实对话记录行),且它与底边的距离读起来像刻意的边距而不是被裁掉的框。
10. **侧栏,检查的两半。** `run-sidebar-align.sh` 现已重跑并通过(§2),包括搜索图标所在行在 19pt;而*点击*测试夹具仍是「写了但会飘」。菜单的第二轮改动(搜索框下无分隔线、统一行距、文件夹字形内缩 6pt、单一灰色 hover/活动高亮、13pt regular 字型)是在一条「停止运行测试夹具」的明确指令下完成的,因此其中大部分当时未测量。先跑 `./Tools/SmokeTest/run-sidebar-align.sh` 与 `./Tools/SmokeTest/run-sidebar-click.sh` —— 它们现在断言字形落在 `sidebarMargin + projectIconRightShift`、由四个绘制的胶囊得出精确行距(项目→对话 = 对话→对话 = 对话→项目)、文件中没有字重非 `.regular` 的 `.font`、`SidebarRowChrome` 中没有垂直内边距,且恰好剩下一个 `Divider()` —— 并用它们打印的内容替换 §2 中的 ⚠️ 行。然后是人工的那一半,这里的任何测试夹具都看不到:折叠能挺过重启;*项目*行上的灰色高亮看起来是对的(此前它完全没有 —— 只有对话会 hover)且在两种外观下都对;搜索*进行中*做出的折叠读起来像刻意的而不是结果缺失;折叠那个会话已打开的项目不会干扰已打开的会话;13pt 行与 11pt 说明文字放在一起仍读作同一个菜单;以及搜索框自身的填充已足够把它区分开,因为其下的分隔线已经没了。
11. 完成以上任何一项后更新本文件。
12. **折叠行,由人工看过一次。** 折叠*规则*已由 `run-replay.sh` 在此处每个真实会话上证明(见 §2),但没有任何东西绘制过折叠行:没有对应测试夹具,也没有运行过 —— 这些落地在一条「停止验证循环」的明确指令下。打开一个真实会话并检查:一串步骤读作*一条*暗色行而不是一张卡片;点击该行上任意位置都能打开内容(整行是 `.plain` 按钮内的 `.contentShape(Rectangle())`),且在没有折叠箭头的情况下没有任何东西看起来*不*可点击(hover 提亮与提示条就是全部的可供性);单步分组直接打开其内容而多步分组打开列表;`foldedSummary` 中的命令或路径在*中间*截断且保持一行;运行中调用的转圈与耗时在走动;153 个折叠失败中的一个在折叠状态下显示红色 `Failed` 胶囊;嵌套步骤行的差异统计与单步行的输出对齐;以及空状态与长输出路径在两种外观下都仍然合适。还要检查真实运行上的分组标题 —— `Thinking, edited files, run commands` 是生成的,而这些词是这里唯一没有测试能评判的部分:特别是**推理**折叠后与调用放在一起是否读得正确、会不会被误认为一次调用,以及已打开运行内部的 `Thinking` 步骤绘制的是推理文本(可选择、无输出框、菜单上有 `Copy Reasoning`)而不是一张空卡片。这一轮*移除*的一个行为是有意的:`Thinking` 行不再在推理流式到来时自动打开 —— 折叠行显示转圈,文本只差一次点击 —— 因此如果观察推理实时到达值得那份动静,那就是该主动要回来的东西。
13. **压缩行,由人工看过一次。** 磁盘上的 16 个会话中没有可看的压缩行 —— Pi 写了 51 个 `compaction` *条目*,但压缩只有作为来自 `get_messages` 的 `compactionSummary` *消息*才到达对话记录,而这些会话的活动分支都没有(构建器读文件,而压缩条目不带 `message`)。因此新的一行式行(`[图标] 压缩上下文`)未经端到端验证;从消息角色到 `SummaryKind` 的映射由 `run-open.sh` 在第一个恰好带摘要消息的会话上检查(未运行,与本轮其他一切一样),但*没有人见过那一行*。打开一个已压缩的会话并检查:一条暗色行、字形与树检查器对同一事件的字形一致、无框、无摘要文本,且上下文菜单上仍有 `Copy Summary`。
14. **页眉、工作区菜单与右侧面板,由人工看过一次。** 接线已就位,能看到数字的测试夹具也通过,但以下是像素层面的:
    - **只有一个面板按钮亮起。** `ContentHeader` 现在接收 `isInspectorVisible: state.isInspectorVisible && !state.isNotificationsVisible`,因此铃铛与面板开关绝不会同时点亮(活动 = 完整 `.primary`,非活动 = `.primary` 0.55,hover = 完整)。打开通知,再打开一个产物,确认每次都恰好只有一个点亮,且在两种外观下都如此 —— `.primary` 在浅色外观的 `textBackgroundColor` 页眉上接近黑色,那正是设计所要的「白色」。
    - **工作区菜单打开终端面板。** 选择「显示终端」并确认面板出现在对话下方、拖动其上边缘可在 120 到 420pt 之间调整大小、面板自己的 × 能关闭它且该偏好在重启后保留、其上方的对话记录仍能正确滚动(输入区悬浮在*对话*之上,不是面板之上)。选择「在访达中打开」与「在 VS Code 中打开」并确认各自作用于已打开会话的文件夹;未安装 VS Code 时,确认提示条会说明这一点而不是点击毫无反应。
    - **菜单是暗的,只有 hover 让它变白。** 该方块不跟随终端面板的状态;它像非活动面板开关一样停在 0.55 不透明度,hover 时升到完整。在两种外观下确认这一点,尤其是确认修法作用在 `Menu` 上而不是标签内部:一个渲染测试夹具测得,把 `.opacity(0.55)` 加在 `Menu` 上时该方块亮度为 0.53,而把同一修饰符加在标签内的 `Image` 上时为 0.87(与完整无法区分)—— `borderlessButton` 菜单会把标签快照为模板图像。
    - **三个控件之间**有 16pt 间隙(`HStack(spacing: 16)`),铃铛的角标不会跨过间隙搭到邻居上:在固定 15pt 宽度内 `x: 5, y: -5` 处,`3` 与 `99+` 都留下可见间隙,且计数到达不会让工作区菜单位移(在渲染测试夹具中实测:菜单墨迹在 0、3 与 150 条未读时都停在 836–847pt)。若角标或间隙变化,这一行就是重新测量的对象。
    - **侧栏关闭时的内缩。** `ContentHeader.leadingInset` 在侧栏打开时是 14,关闭时是 104,因此文件夹字形避开红绿灯按钮*和*侧栏开关。折叠侧栏并确认字形不在开关下方;104 是开关实测右边缘(约 101pt)再加几个点,也是这里唯一一个靠估算而不是在折叠状态下观察得到的数字(这台机器上不允许按键自动化)。
    - **面板的页眉分隔线比对话的高出一个点**:两者都用 `.padding(.vertical, 15.5)`,同一带区,做了偏移,让两条线不至于读作未对齐。
    - **面板的代码比正文字号小两档。** 命令/读取与编辑差异的下凹凹槽都使用 `Typography.codeBlockCompact`(11pt,对 `baseSize` 13),因此差异凹槽从 12 降到 11。
    - **输入区的模型菜单**不再在 macOS 自己的指示符前绘制手工 `chevron.down`,且模型/推理菜单与发送/停止按钮之间保留 10pt 间隙(`HStack(spacing: 10)`)。

已由测试夹具关闭的事项(保留在此以免有人重新打开):

- ~~重新加载的会话丢失压缩/分支标记~~ —— 已对照一个真实压缩会话验证:`get_messages` 包含该摘要,且恢复后对话记录会渲染压缩行(`run-open.sh`)。
- ~~带超时的扩展对话框在 Pi 已解决后仍滞留~~ —— 由镜像 Pi 的本地截止时间解除,活动时间线说明原因(`run-extension.sh`)。
- ~~1.5 秒的对话框超时显示成「25m 0s」~~ —— 线格式发送毫秒;`ExtensionUIRequest.timeoutSeconds` 只转换一次(`run-extension.sh`)。
- ~~`SessionReplayTest` 的孤立检查是空洞的~~ —— 它现在按 `toolCallId` 把 `toolResult` 消息匹配到调用(3754/3754 全部匹配)。
- ~~深度嵌套的 RPC 载荷让应用崩溃~~ —— 迭代式扫描器在那条路径上取代了 `JSONDecoder`(§10)。
- ~~`get_tree` 在长会话上卡住应用~~ —— 树在本地构建,条目用游标跟随而不是重读(§9)。

---

## 12. 约定

- **布局**:尽量一个文件一个类型;功能文件夹镜像三栏界面。新界面放进匹配的 `Features/` 文件夹。
- **删除会话由表单应答,而不是由表单执行。** 确认就是全部决定:`AppState.delete(session:)` 把会话移出侧栏所绘制的索引,并在主 actor 上解除文件链接,然后在 `Task` 中运行重新扫描,而 `DeleteSessionSheet` 在同一次点击中关闭。在表单消失之前不得 `await` 任何东西 —— 一次重新扫描会遍历 Pi 的整个会话文件夹(在 304 文件的测试夹具上 1617 ms,而测试夹具目录还更大),一个等它的模态会读作卡死。失败进入窗口的横幅(`present(error:)`),因为已经没有表单可以容纳它们,而行会自己回来:重新扫描才是权威,它只丢弃文件系统已不存在的东西。先解除链接再重新扫描,才能阻止其间运行的重新扫描把该行放回来。删除是对 Pi 会话文件的唯一改动,因此这是唯一必须把这件事做对的地方。
- **侧栏行**:项目与其对话是同一等级,因此它们共用 `SidebarStyle.rowFont` —— 13pt、`.regular`,菜单里*任何东西*都不用 medium、semibold 或粗体(这里避免语义化样式,因为它们会连字重一起带上尺寸;`run-sidebar-align.sh` 会 grep 文件里更重的字重)—— 以及主文本颜色。对话不画对话字形,但它确实拥有一个前导标记槽位 —— `projectIconSize` 加 `iconTextSpacing` —— 起点与项目的文件夹字形相同:安静对话时为空,因此标题与项目名对齐;该对话运行时为会话自己的转圈,因此活动指示器与文件夹待在一起而不是待在名称对面。无论哪种情况槽位都被预留,因此对话开始或停止工作时标题从不位移。项目是**行**,绝不是 `Section`:侧栏列表样式会把分区标题变成带展开箭头的可折叠分组,而项目的折叠改为点击该行。行还共享分区标题所没有的前导内缩,这就是缩进不再需要修正的原因 —— 改变侧栏后用 `run-sidebar-align.sh` 测量它。文件夹字形由 `.offset`(`projectIconOffset`)定位而不是内边距,因为只影响绘制的位移会让名称 —— 以及与之对齐的每个对话标题 —— 保持在原处。搜索框下方没有分隔线:它自己的下凹填充就是分隔,这个视图里只剩下一个 `Divider()`(页脚的那个)。一个分组绘制 `SidebarStyle.visibleRowLimit` 行 —— 一个项目的对话,或一个标题下的项目 —— 并把其余放在一个 `ShowMoreRow` 之后,因为侧栏是一份「你去过的地方」的菜单,不是目录列表:列表已经是最新在前,因此一个分组绘制的那十行就是它最近的十行。项目的「显示全部」会被关闭它的折叠遗忘(`SidebarView.list` 把已打开的路径与 `state.expandedProjects` 求交),因此重新打开项目又会显示前十行,而标题的展开状态持续到会话结束,因为标题无法折叠。该控件是一行而不是页脚:相同节奏、相同 hover 胶囊、位于名称列上。行的后缘控件从 `.foregroundStyle(.primary)` 取墨,变暗则来自作为 `.opacity` **应用在控件上**的 `SidebarStyle.actionIdleOpacity` —— 绝不用字面 `NSColor`(它在错误的外观下解析并会在深色侧栏上画成黑色),也绝不在菜单标签内部放修饰符(`borderlessButton` 菜单在快照时会丢弃它,§10)。那次快照也是两个行菜单都把自己标为 `Text(Image(systemName: "ellipsis"))` 而不是 `Image(…)` 的原因:在侧栏 `List` 里,仅有图像的标签从快照返回时为空,因此菜单按钮什么都不画,而文本包裹的形式能画(在渲染实验室中实测:`Image` 标签 0 墨量,`Text(Image)` 满墨量 255,暗态 151)。
- **内容页眉的控件是一行,每个只表达一种状态。** 通知铃铛与右侧面板开关共用 `ContentHeader.controlTint` 且互斥:活动是完整 `.primary`(设计所要的「白色」;不是字面 `.white`,那会在浅色外观的 `textBackgroundColor` 上消失),非活动是 `.primary` 0.55,hover 提到完整。`RootView` 传入 `isInspectorVisible: state.isInspectorVisible && !state.isNotificationsVisible`,因此面板切到产物时铃铛的光会熄灭。三者在同一个 `HStack(spacing: 16)` 中从左到右是:铃铛、工作区菜单、面板开关 —— 两盏状态灯夹着那个不是状态灯的菜单。工作区菜单是 `Menu` 而不是更多三个图标,以便页眉右缘保持为一行按钮而不是一条带;它的方块是唯一*不*取点亮色的控件:它始终是暗的,只有 hover 把它提到完整,因为菜单是一种可供性提示,不是状态灯(其中哪一项开着由该项的标签与面板是否可见地打开来承载)。那份变暗必须是在 `Menu` 自身的 `.opacity(0.55)`;`borderlessButton` 菜单会把标签快照为模板图像并丢弃其内部设置的修饰符,因此给字形着色(甚至给 `Image` 加 `.opacity`)仍会以满墨渲染 —— 实测:加在菜单上亮度 0.53,加在其内部 0.87。铃铛固定 15pt 宽,其角标偏移 `x: 5, y: -5`,因此计数既不能加宽按钮(那会把旁边的菜单顶走)也不能跨过间隙搭到邻居上。
  页眉从 `leadingInset` 开始 —— 侧栏打开时 14pt,关闭时 104pt —— 因为侧栏关闭时内容列会伸到窗口前缘,否则会绘制在红绿灯按钮与侧栏开关之下;104 是相对运行中的窗口测得的(§10)。
- **终端面板是 Pi 的 bash 界面,不是第二个 shell。** 工作区菜单的「显示终端」在对话下方打开 `TerminalPanel`;其主体是 `TerminalPane`,而那里的每条命令都通过 Pi 自己的 `bash` 工具运行,因此用户的命令与代理的命令落在同一份会话历史里。PiCode 不 fork 一个登录 shell 并给它 pty:一个无关的 shell 会待在这份对话记录所关乎的会话之外,而需要真正的交互式终端时,面板本身就提供「在终端中打开」。该面板是会话列的*第三个区域*,不是输入区下方的页脚 —— 输入区仍悬浮在对话之上,其下不添加任何东西(§6)。它的高度是 `AppState.terminalHeight`,每次访问各自调整;其可见性是 `AppState.isTerminalVisible`,持久化为 `showTerminal`,因为窗口布局事实会被记住。它由 `RootView` 的 `detail` 分支绘制在检查器的 `HSplitView` 旁边,因此打开面板从不打扰两侧边栏;且只在会话打开时绘制,因为那些命令属于该会话。
- **检查器的机器文本比正文字号小两档,其页眉比对话的紧半个点。** `ActionCodeBlock` 的朴素形式与其下凹差异凹槽都使用 `Typography.codeBlockCompact`(`baseSize - 2`),因为该面板是对话旁边供瞥一眼的参考,不是第二个阅读栏;编辑差异从 `codeBlock`(12)降下来以匹配。`ArtifactHeader` 与 `NotificationsPanel.header` 使用 `.padding(.vertical, 15.5)`,而 `ContentHeader` 用 16,因此面板的分隔线比对话的高一个点而不是正好落在其上。这些数字要一起改,不要一次改一个。
- **输入区是一个形状、一行**:编辑器、附件标签与控件共用同一个圆角框(`ComposerMetrics.cornerRadius`),其后没有任何东西填充任何区域 —— 输入区区域下方没有条形材质。新控件加在那一行上:如果它是*输入*,放在模型选择器左侧;如果它配置的是*运行*,放在右侧;新增一行属于设计变更,不是增补。那里的每个控件都必须挣得自己的空间:发送按钮兼任停止,而不是挨着另一个按钮坐。
- **输入区的数字放在 `ComposerMetrics`,其宽度放在 `ConversationColumn`**:框的内边距、控件行上方的间隙与 `boxHeight(forEditor:)` 都是视图*使用*、测试夹具*据此预测*的量,因此内边距变化会表现为一个测量数字,而不是相对硬编码期望的静默漂移。框必须留在对话记录的列里;第二个悬浮元素也要放进 `ConversationColumn`,否则它会横贯整个窗格。
- **输入区保持小,保持为覆盖层**:两行,之后滚动;它绘制在对话记录之上,而对话记录被*告知*这一点(`ConversationView.bottomInset`),因为覆盖层不预留空间。输入区*下方*不添加任何东西 —— 那是有意的移除,任何新的会话状态都属于对话记录的系统行或检查器,而不是页脚。若你改变输入区的高度或内边距,也要改 `ComposerHeightKey` 的消费者,并重跑 `run-composer.sh`:框高是对照 `ComposerMetrics.editorMaxHeight` 断言的,不是魔法数字。
- **Return 家族按键由事件决定,绝不由选择器决定**:Shift 表示「增加一行」,Option 表示「排队一条跟进」,发送组合键来自 `PreferencesStore.SendKey`。只看选择器不够(§10)—— 而且因为该映射在 diff 中不可见,`run-composer.sh` 会断言它。
- **侧栏中的垂直节奏**:每一行都在列表自身的节奏上 —— 对话与其上一个对话之下的距离,等于它与所属项目名之下的距离;项目与其上方对话之下的距离,等于对话之间那样。没有任何东西获得额外边距来宣示「这是一个标题」:分隔两个项目的是文件夹字形。边距与行内边距都不是添加呼吸空间的白拿手段 —— 行的内边距会改变该行的节奏*并且*让胶囊变大,因为 `listRowBackground` 填满整个单元格 —— 因此如果这里确实需要间隙,请从*形状*里挖出来(如同 `rowHighlightInset` 在水平方向所做的那样),不要给行加内边距,并用 `run-sidebar-click.sh` 测量它。项目字形除宽度外还获得固定*高度*,这样一个 15pt 的文件夹不会让它的行比文本行更高。
- **行高亮坐在侧栏的水平边距上,且只有一种颜色**:hover 与活动行绘制同一个圆角胶囊(`rowHighlightRadius`),填充 `rowHighlightFill` —— 中性灰,而不是 `accentColor`,因为窗口一旦不是 key,macOS 反正会把它画成灰色,于是强调色着色的背景会在指针下变色,并对 hover 与选中传达不同的意思。胶囊由 `rowHighlightInset`(即 `sidebarMargin`)内缩,因此它的起止与搜索框一致;`listRowBackground` 自身填满整列,所以没有那个内缩它会贴边,而其他所有元素都坐在边距上。两种行都通过同一个 `SidebarRowChrome`(`View.sidebarRow(fill:)`)绘制,这正是项目的胶囊与对话的一样高的原因 —— 一处可改、一处可测:如果你动了 `rowMinHeight`、`rowHighlightInset` 或该装饰,请运行 `run-sidebar-click.sh`,它测量胶囊与它们之间的步距。
- **对话记录折叠四种安静形态,折叠是纯函数**:带卡片的工具调用是默认;只有 `thinking`、`bash`、`edit`/`write` 与 `read` 变成折叠行,清单位于 `QuietFamily.of(_ item:)` —— 一处,连同文案(`label`/`pluralLabel`/`listed(count:)`)与图标。添加第五个类别意味着加一个 case,并接受用户将不再阅读那些行。同一个函数决定成员资格*与*标题,因此两者不可能不一致。*规则*留在 `TranscriptRows.group`:纯函数、仅依赖 Foundation、不含 SwiftUI,因为正是这让 `run-replay.sh` 能在每个真实会话上而非某个例子上证明它。不要把那个判断搬进视图,也不要给分组一个依赖其内容的 id —— 流式回合会重新给该行设键并把它重新合上(§10)。推理不是工具:一个步骤的形态来自 `QuietFamily.of(item)`,绝不只来自 `toolName`(§10)。
- **工具调用的内容在一处绘制**:`ToolCallContent` 渲染参数、文件变更、输出、截断提示、失败句子与结构化结果;`QuietStepContent` 在那与推理步骤的文本之间选择,而卡片与折叠行都只添加各自的页眉。要在那里一次性改变某个工具的呈现。任何用户不该错过的东西都留在展开之外 —— 这就是失败句子属于内容、而运行/失败胶囊在折叠行上的原因 —— 任何新的工具形态行都必须守住这条规则:不要让重要的状态只藏在一次点击之后。
- **折叠行只打开一样东西,其行文说明是什么**:对话记录只有一种方式表达「这下面还有更多」—— 一行暗色文本、覆盖整行的 `.plain` 按钮、提起暗色的 hover,以及说明该动作的提示条(`ToolGroupView`、`ToolActionRow`)。单独的步骤直接打开其内容且不画折叠箭头;多步运行画那一个打开列表的折叠箭头。不要给单个步骤添加展开字形,也不要使用 `DisclosureGroup`:它的折叠箭头落在前导槽位,既重新引入一列箭头,又把该行的图标推得与列中其他所有图标不对齐。*本身就是事实*而不是折叠的系统行 —— 一次压缩、一次重试 —— 是由模型构建的单行(`SummaryKind`),绝不是徽章加一段话。
- **搜索是命令面板,不是侧栏输入框**:侧栏的搜索是一个打开命令面板的标题栏图标(`SidebarView` 的 `onOpenPalette`),因此没有需要在两种外观下都保持清晰的下凹输入框填充。命令面板是一张带自身背景与自身关闭按钮的表单。
- **添加检查器产物**:右侧面板是单一查看器,不是标签栏。给 `AppState.InspectorArtifact` 加一个 case、给 `ArtifactHeader` 加标题、给 `ArtifactContentView` 加主体分支;选中项由对话自身的动作(`openTool`、`openChange`、`openFile`)打开,因此面板绝不自行决定显示什么。
- **添加命令**:加 `RPCCommand` case(在 Pi 的 `docs/rpc.md` *与*已安装的包里核实线格式名称),把它加到 `Tools/SmokeTest/RPCSmokeTest.swift` 的线格式 case 列表,如果用户可调用则加一个 `PaletteCommand` case,然后在 `AppState.run(_:)` 和/或控制器中接线。菜单与快捷键都是免费的,因为它们全部经由 `PaletteCommand` 分发。
- **添加检查器窗格**:加 `AppState.InspectorTab` case(它必须提供 `label` + `systemImage`),然后在 `InspectorPanes.swift` 中加窗格视图,并在 `InspectorView.pane(controller:)` 中加一行。
- **写大型 Swift 文件**:拆分它们。单次 `write` 超过约 200 行会触及输出 token 上限;请用 `bash cat >> … << 'PICODE_APPEND_EOF'` 分块追加。
- **注释**:解释*为什么*(协议怪癖、Pi 语义、macOS 约束),而不是*做什么*。§9/§10 中的协议事实应放在依赖它们的代码旁边的注释里。
- **绝不**留下隐藏兼容性问题的 `TODO`;把它作为兼容性卡片呈现在界面中。
- **绝不**硬编码 Pi 配置目录内的路径。请询问 `PiPaths`(§7)—— Pi 可以被重定位,而 PiCode 必须与之一致。

## 13. 在宣称某事完成之前的评审清单

- [ ] `swiftc -typecheck` 干净(§3 第 1 步)
- [ ] `xcodebuild` → `** BUILD SUCCEEDED **`
- [ ] `./Tools/SmokeTest/run.sh` → `RESULT: all checks passed`
- [ ] `./Tools/SmokeTest/run-json.sh` → `RESULT: all checks passed`
- [ ] `./Tools/SmokeTest/run-replay.sh` → `RESULT: all checks passed`,包括折叠检查。如果你动过 `TranscriptRows`、`QuietFamily`、`ToolCallContent`、`ToolGroupView`、`QuietStepContent` 或 `ToolCallCard`,请读它的 `folding:` 行:`0` 项丢失、`0` 个来自其他工具的折叠行、`0` 个相邻/被拆分的运行段,且 `families` 列表必须加起来等于会话中每个安静步骤 —— `reasoning folds with the steps it belongs to` 检查正是证明最后一项的东西(此处 3190/3190,共 8132 个步骤)。`watched:` 计数大于零意味着磁盘上存在真实的折叠失败 —— 它们需要 `ToolGroupView` 的红色胶囊,因此那是你打开应用时要看的行
- [ ] `./Tools/SmokeTest/run-open.sh --small` → `RESULT: all checks passed`
- [ ] `./Tools/SmokeTest/run-paths.sh` → `RESULT: all checks passed`(仅当你动过 `PiPaths`、信任、会话发现或进程启动)
- [ ] `./Tools/SmokeTest/run-extension.sh` → `RESULT: all checks passed`(仅当你动过扩展界面、对话框或提示词发送路径)
- [ ] `./Tools/SmokeTest/run-providers.sh` → `RESULT: all checks passed`(仅当你动过 `PiProviderService`、设置或 Pi 的配置路径)
- [ ] `./Tools/SmokeTest/run-index.sh` → `RESULT: all checks passed`(仅当你动过会话发现、侧栏或偏好)
- [ ] `./Tools/SmokeTest/run-sidebar-align.sh` → `RESULT: all checks passed`(仅当你动过侧栏布局;需要图形界面会话)
- [ ] `./Tools/SmokeTest/run-sidebar-click.sh` → `RESULT: all checks passed`(仅当你动过侧栏的行或高亮;需要图形界面会话)。它测量胶囊,因此如果你动过 `rowMinHeight`、`rowHighlightInset` 或 `SidebarRowChrome`,请检查项目的胶囊高度仍等于对话的(28.0pt),并且三个步距 —— 项目→对话、对话→对话、对话→项目 —— 仍然一致(各 28.0pt;给自己加垂直内边距的行会破坏第二个数字,而在其胶囊*内部*加内边距会破坏第一个)
- [ ] `./Tools/SmokeTest/run-composer.sh` → `RESULT: all checks passed`(仅当你动过输入区、Return 键、`PreferencesStore.SendKey`、`SessionView` 的底部区域或对话记录的底部内缩;需要图形界面会话)。如果你改变了输入区的高度或内边距,请检查测得的编辑器高度仍是 22/40/40/40pt,框仍与 `ComposerMetrics.boxHeight(forEditor:)` 一致,且框与一条对话记录行在 1300pt 与 500pt 下仍同宽 —— 高度错误意味着某个 `NSViewRepresentable` 又在取它的最大高度,宽度错误意味着内边距与宽度上限被调换了(§10)
- [ ] 应用能启动并稳定运行数秒,没有崩溃报告
- [ ] 用眼打开过折叠行:一串步骤读作一条暗色行,点击它(行上任意位置)能打开,单步分组直接打开其内容而多步分组打开列表,运行中的调用保留其转圈,折叠的失败只在回合进行中保留其红色胶囊,单独的步骤不画折叠箭头而多步运行画那一个打开列表的,打开 `Thinking` 行显示推理文本而不是空卡片,且一次压缩就是一行 `Compact context` 别无其他(§11 第 12–13 项)
- [ ] `git status` 显示 `~/.pi/agent` 中**没有**任何变更(没有 `trust.json`,没有新会话文件,没有被动过的设置)
- [ ] diff 中任何地方都没有 `sh -c` / 带 shell 的 `Process`
- [ ] 新的 RPC 字段名已在 Pi 的 `docs/rpc.md` 中核实
- [ ] 任何新的能力缺口都被标注为兼容性回退,而不是被隐藏
- [ ] 如果有决策、陷阱或下一步发生变化,本文件已更新
