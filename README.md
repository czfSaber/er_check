# er_check —— 应急响应排查助手

单文件、零依赖、离线可跑的主机入侵排查工具。一个 `er_check.py` 搞定 Windows / Linux 主机排查、日志分析、WebShell 查杀与取证导出，结论直接产出可交付的 HTML 报告。

- **单文件**：只有一个 `.py`，无第三方依赖（纯标准库），拷到目标机器就能跑，无外联也能跑
- **只读**：不删除、不修改任何系统对象；处置建议只生成脚本、不执行
- **可交付**：`report.html` / `findings.json` / `summary.txt` + 时间线与产物证据链
- **可自证**：每条「严重」结论必须带 ≥2 条相互独立的证据来源，不足自动降级；数据源不可用、取数截断一律显式写进「数据源与覆盖度」段，不静默

## 快速开始

```bash
python er_check.py                      # 交互菜单（双击 / 直接运行）
python er_check.py web                  # 图形界面（浏览器控制台，实时进度与结论流）

python er_check.py win                  # Windows 主机入侵排查
python er_check.py linux                # Linux 主机入侵排查
python er_check.py linux --root /mnt/collected    # 分析离线采集的分区

python er_check.py weblog --log access.log        # Web 访问日志分析（支持 .gz）
python er_check.py webshell --dir /var/www/html   # WebShell 目录查杀
python er_check.py all                  # 按当前平台执行主机排查
```

退出码：存在「严重/高危」结论时返回 `1`，便于批量巡检与告警联动；参数校验失败返回 `2`。

## 模式

| 模式 | 说明 |
| --- | --- |
| `menu`（默认） | 交互菜单 |
| `web` / `ui` | 本地图形界面（`--port 8765`，占用自动顺延，默认只监听 `127.0.0.1`） |
| `win` | Windows 入侵排查：进程/内存、网络连接、账号与凭据配置、自启动与持久化、计划任务、服务、WMI、IFEO、LSA、安全日志增强（4624/4672/4648/4776/4768/4769/4907/4719/5140/5145/4662/1102）等 |
| `linux` | Linux 入侵排查：进程与 `/proc` 句柄面、网络、账号与 sudoers、SUID、crontab、systemd、SSH 后门面（sshrc / wrapper / AuthorizedKeysFile / ld.so.preload）、包完整性校验等 |
| `weblog` | Web 访问日志分析（SQL 注入 / 扫描 / 爆破 / WebShell 访问 / SSRF 等） |
| `webshell` | WebShell 目录查杀（字节定位 + 编码边界对齐取证据片段） |
| `malware` | 可疑程序画像（签名 / 落地路径 / 命令行 / 网络行为） |
| `all` | 按当前平台跑主机排查 |

档位：默认档 / `--fast`（跳过整面，报告顶部固定警示「结论不完整」）/ `--deep`（一键深挖：同一次内跑 Web 日志、站点查杀、程序画像）。

## 常用参数

```
--out 报告目录        --days 近期文件天数      --threshold 爆破阈值
--ioc-file 情报文件   --rules 自定义规则        --allow 白名单/例外
--hash-db 本地恶意哈希库   --yara / --yara-root   --sigma
--baseline 保存基线   --diff 与基线对比（新增/消除项）
--pkg-verify 包完整性校验（rpm -Va / dpkg -V）   --quiet
--no-builtin-rules 关闭内置规则库   --show-builtin-rules 只读列出规则库与版本
--collect-evidence 目录   导出取证包（逐条 sha256）
--gen-fix 目录            生成处置建议脚本（PowerShell / bash，只生成不执行）
--merge findings.json…    多主机结论合并 → merged.csv + merged.html
--webhook URL / --mail-to 邮箱 --smtp 主机[:端口]   结论通知（可选，失败不阻塞）
--port / --host / --no-browser                      图形界面参数
```

## 产出物

报告目录下：

- `report.html` —— 浏览器直接打开的可交付报告（结论卡 / 处置建议 / 证据折叠 / 覆盖度声明）
- `findings.json` —— 机器可读结论（含 `coverage` 段：跳过面、截断、降级记录）
- `summary.txt` —— 文本摘要
- `timeline.csv` —— 全局时间线
- `manifest.sha256` —— 报告产物证据链

## 判定口径（为什么结论能当证据用）

1. **只读**：不做任何写操作、不结束进程、不改注册表；建议只输出不执行。
2. **严重需双证**：任何「严重」结论随附 ≥2 条相互独立证据来源，不足自动降级为「高危」并写明原因。
3. **持久化归因**：持久化条目与创建事件按 名字/路径 + 时间窗 对齐，输出「条目 ← 创建进程 ← 创建时间」；对不上的显式写「无归因（仅见结果，未见创建过程）」。单侧证据（仅进程侧命令行）只算「疑似」，且读型/审计型命令（`reg query`、`sc query`、`Get-Content` 等）一律不采信。
4. **不静默**：数据源不存在 / 无权限 / 已截断全部声明，并写明影响面与实际覆盖时长；异常统一收敛到单点降级入口并计数。

## 规则来源

内置规则库（银狐族、LockBit / BlackCat(ALPHV) 等勒索家族、Mimikatz / Cobalt Strike / Rclone / AnyDesk·TeamViewer 等工具 TTP）依据公开资料整理；检测思路部分参考《应急响应实战笔记》（[Bypass007/Emergency-Response-Notes](https://github.com/Bypass007/Emergency-Response-Notes)）。规则语法为本项目自研的简单子集（YARA-like / Sigma 子集），不支持聚合、关联与多后端转换。

## 免责声明

本工具用于**已获授权**的应急响应与自查。检测结果需人工复核后再处置；因误用、超授权使用或据此直接操作生产系统造成的后果，作者不承担责任。

## License

MIT，见 [LICENSE](LICENSE)。
