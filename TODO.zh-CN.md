这是 PiCode 的任务清单。任务完成后,请把它移到「已完成」部分。

待办任务:

(无)

已完成:

1. 页眉:
- 铃铛与右侧导航图标只有一个处于激活状态(而非两者同时),它们之间加 6px 间隙;激活时颜色设为白色
- 左侧菜单关闭时,为内容左侧设置内边距,避免红绿灯按钮/切换菜单按钮覆盖内容
  — `ContentHeader`(`isSidebarVisible`、`leadingInset` 14/104、`HStack(spacing: 6)`,激活态为完整 `.primary`);`RootView` 传入 `isInspectorVisible && !isNotificationsVisible`。

2. 右侧菜单:
- 把(代码的)内容字号调小两档
- 页眉高度减少 1px
  — `ActionCodeBlock` 的差异区现为 `Typography.codeBlockCompact`(11,即 `baseSize - 2`;命令/读取本来就是这个值);`ArtifactHeader` / `NotificationsPanel.header` 用 `.padding(.vertical, 15.5)`。

3. 左侧菜单:
- 让红绿灯按钮 / 切换菜单按钮 / 搜索按钮图标水平居中对齐
- 只为正在运行的对话会话显示活动指示器;目前看起来所有会话都显示为运行中
  — 根因是窗口用了 `.unifiedCompact`(红绿灯中心 19pt)而不是 `.unified`(26pt):`SidebarStyle.titlebarRowCenter = 19`,代理程序窗口切换为 `.unifiedCompact`(在实机构建上实测 18.8pt 对 19.0pt)。`AppState.isRunning` 现在向带键的控制器询问某个由路径支撑的会话,而不是回落到当前活动会话。

4. 文本对话区:
- 最大高度自动调整
- 最小(起始)为 2 行文本,最大 6 行,超过 6 行则滚动
- 去掉模型名前的第一个折叠箭头
- 增加按钮之间的间距(模型名 / 推理强度 与 发送按钮)
  — 最小 2 行 / 最大 6 行加滚动原本就已就位;移除了 `modelThinkingMenu` 中手绘的 `chevron.down`;模型/推理菜单与发送/停止现在位于 `HStack(spacing: 10)`。

5. 输入框悬浮在对话记录之上,但任务处理期间底部间距有时会消失 —— 始终保持相同的底部间距
  — 预留空间原本是 `LazyVStack` 上的 `padding(.bottom, 8 + bottomInset)`,即位于 1pt 底部锚点*之下*,因此 `scrollTo(anchor: .bottom)` 会把锚点的底部对齐到视口,并在自动滚动期间把该内边距滚出视野(短对话记录能看出来,长的看不出来)。现在这块空间位于锚点*之上*,放在一个 `VStack(spacing: 0)` 中 —— 锚点仍保持 1pt,因此「固定到底部」依然指最底部 —— 并且 `ConversationView` 会在 `bottomInset` 随输入区增长而变化时重新滚动。输入框也去掉了顶部内边距(`ComposerMetrics.boxTopPadding` 9 → 0),因此两行的提示词就是一个两行的输入框。

6. 左侧菜单中,当某个对话会话正在运行时,活动指示器应位于会话名开头(与项目图标对齐)
  — `SessionRow` 的转圈从后缘移到预留的前导槽位,该槽位按文件夹字形自身的 11pt 标记、在同一 `projectIconOffset` 处绘制;每个对话都保留该槽位(空闲时为空),因此对话开始或停止工作时标题从不位移。`run-sidebar-align.sh` 检查该槽位的接线,对齐测试夹具也同步到新的行结构。

7. 操作项:
- 去掉分组标签中的步骤数量
- 把(标签之后的)字号调小两档,例如命令 / 文件名等
- 去掉时长与右侧栏图标
  — `ToolGroupView` 的页眉不再绘制 `"\(steps.count) steps"` 摘要(改由运行的那一行列出各类别),页眉与 `ToolActionRow` 中的摘要现在用 `Typography.codeBlockCompact`(11,即 `baseSize - 2`)而不是 `Typography.code`。运行中的计时时钟与每步时长已移除,hover 时的 `sidebar.right` 字形也已移除,因此一个步骤行就只剩它的字形、标签、摘要与差异统计。

8. 内容中的行内代码,字号调小一档
  — `MarkdownInline.attributed` 现在把 `.code` 片段设为 `Typography.codeBlock`(12,即 `baseSize - 1`)而不是 `Typography.code`(13),因此行内代码与其所在句子的对比关系,与围栏代码块一致。这是构建行内片段的唯一位置,因此段落、标题、列表项、引用与表格单元格都会跟随。9. 内容页眉:在通知铃铛旁加一个工作区菜单
  — `ContentHeader` 现在在通知铃铛与检查器开关之间绘制一个 `Menu`(`equal.square`),包含「显示/隐藏终端」、「在访达中打开」与「在 VS Code 中打开」。该方块始终处于变暗状态,仅 hover 时取满色 —— 菜单是一种可供性提示,不是状态灯 —— 而终端的状态由「显示/隐藏」标签与下方打开的面板承载;变暗是应用在 `Menu` 自身的 `.opacity(0.55)`,因为 `borderlessButton` 菜单会丢弃其标签内部设置的修饰符。当 `AppState.isTerminalVisible` 为真(持久化为 `showTerminal`)时,`RootView` 在对话下方渲染 `TerminalPanel`;该面板是 Pi 自带的 bash 界面(`TerminalPane`),不是登录 shell,可通过拖动其上边缘调整大小。命令面板的 `toggleTerminal` 与新增的 `openInVSCode` 都经由 `RootView.perform` 路由。该行是 `HStack(spacing: 16)`,铃铛固定 15pt 宽,其角标偏移 `x: 5`,因此计数既不会挤过间隙,也不会让旁边的菜单位移。

10. 左侧菜单:
- 不显示代理程序
- 项目 / 对话会话的操作:只在 hover 时显示(否则隐藏且不占空间)
  — `SessionRow` 不再在标题旁绘制代理程序说明;对话恢复时所用的运行时仍是该行自身的字段,而 `AppState.open(session:)` 早已解释了那个适配器无法恢复已保存会话的代理程序,因此去掉标签并未丢失用户需要的信息。两种行的后缘控件原本就只在 hover 时绘制,但每一行都永久预留了它们的宽度,导致安静状态下的标题距行后缘还差一个(对话)或两个(项目)按钮的宽度:现在 `ProjectRow` 的预留为 `isHovering ? SidebarStyle.topBarButtonSize * 2 : 0`,`SessionRow` 为 `isHovering ? SidebarStyle.topBarButtonSize : 0`,因此安静行的标题与置顶图标一直延伸到行自身的后缘,按钮只在其可见期间占用空间。

11. 左侧菜单:
- 项目 / 对话行上的 hover 操作应保持暗淡,当控件本身被 hover 时变白
- 为对话会话添加垃圾桶(或归档)操作
- 三点下拉菜单中的每一项都必须有图标
  — 两种行的后缘控件现在从 `.foregroundStyle(.primary)` 取色,变暗则通过应用在控件自身的 `.opacity` 使用 `SidebarStyle.actionIdleOpacity`(0.55):`borderlessButton` 菜单会把标签快照为模板图像,而这些字形此前用的字面 `NSColor` 在错误的外观下解析,这正是它们在深色侧栏上显示为黑色的原因(实机构建实测:暗态 151-159,满态 248-255,背景分别为 33/49)。对话行现在在菜单旁带有一个垃圾桶按钮,接到与菜单项自身相同的确认路径(`sessionPendingDeletion` + `.deleteSession`,除非该偏好关闭,否则会弹出确认表单),对于磁盘上没有任何内容的对话则完全不绘制;该行只在其可见期间预留两个按钮的宽度。两个下拉菜单的每一项原本都带 `Label(_:systemImage:)`;真正不可见的是*菜单按钮*本身 —— 侧栏 `List` 绘制 `borderlessButton` 菜单时会快照其标签,而仅有图像的标签在那里返回空,因此省略号现在是 `Text(Image(systemName: "ellipsis"))`(渲染实验:图像标签为 0 墨量,而文本包裹的版本能绘制)。

12. 左侧菜单:
- 当项目会话超过 10 个时,只显示最近 10 个,并在其下显示一个「显示更多…」文本按钮;点击后显示全部,折叠项目再展开后重新显示前 10 个
- 项目 / 置顶项目同理:最近 10 个项目,然后一个显示更多按钮
  — 一个上限(`SidebarStyle.visibleRowLimit`,10)与一个辅助函数(`SidebarView.capped(_:showingAll:)`)让项目的对话与两个项目标题共用同一条规则:`AppState.sort` 已把列表排为最新在前(置顶在前,随后按 `updatedAt` / `mostRecentActivity`),取前十行,其余隐藏时显示一个 `ShowMoreRow`。项目的展开属于视图状态 —— `expandedChatLists`,一组项目路径 —— 而该 `list` 的 `onChange(of: state.expandedProjects)` 会把它与展开集合求交,因此折叠会遗忘展开状态,重新打开项目时又显示最近十个对话;两个标题没有折叠,因此它们的展开状态(`showsAllProjects`、`showsAllPinnedProjects`)持续到会话结束。`ShowMoreRow` 是一行而不是页脚:相同节奏、相同 hover 胶囊,文本位于名称列(`SidebarStyle.titleIndent`),色调偏暗(实测峰值墨量 157,名称为 223-232),隐藏数量放在其提示条中。

13. 删除对话会话时,它在后台进行而不是冻结界面:
- 确认表单随回答关闭,会话同时离开左侧菜单;文件被解除链接,索引在窗口背后重新扫描
  — `AppState.delete(session:)` 不再是 `async throws`:它从 `projects` 中移除该会话(`dropFromIndex`,由于项目文件夹仍在,项目行保留),并在主 actor 上解除文件链接,然后在 `Task` 中运行 `refreshIndex()`。先解除链接再重新扫描,才能阻止其间运行的重新扫描把该行放回来。`DeleteSessionSheet` 去掉了 `isDeleting`/`error` 状态:它在同一次点击中调用 `state.delete(session:)` 与 `onFinish()`,因此没有「正在删除…」标题需要等待,命令面板中无需确认的路径也直接调用同一方法。失败会进入窗口的横幅(`present(error:)`),该行会在下一次重新扫描时回来 —— 重新扫描才是判断什么仍然存在的权威。在一个 304 文件的测试夹具上实测:按下后 420-476 ms 内表单与行消失(即表单自身的关闭动画),而重新扫描耗时 1617 ms,期间 AX 往返保持在 13 ms;只读文件夹在按下后 12 ms 产生横幅,该行随后恢复。

14. 把「跳到最新」按钮移到顶部居中、输入框上方
  — `ConversationView` 的气泡从带固定 `.padding(16)` 的 `.overlay(alignment: .bottomTrailing)` 改为落在 `.padding(.bottom, bottomInset)` 上的 `.overlay(alignment: .bottom)`:`bottomInset` 正是对话记录为悬浮输入框预留的空间(其高度加 16pt 装饰,由 `SessionView` 传入),因此气泡的下边缘恰好落在输入区的顶部内边距上,并在任何提示词高度下都避开输入框。角落锚点对它来说是错误的位置 —— 窗格后缘位于居中内容列*之外*,因此在宽窗口上气泡会漂离它所滚动到的文本,在窄窗口上又会被输入框的渐变遮住(该覆盖层位于 `ConversationView` 之上)。居中后,滚动代理与 `isPinnedToBottom` 仍留在拥有它们的视图中;气泡的可见性规则与其 `.easeOut(duration: 0.2)` 滚动到 `bottomAnchor` 的行为不变。
