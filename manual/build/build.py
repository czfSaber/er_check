# -*- coding: utf-8 -*-
"""构建《应急响应人工排查手册》：
   1) 生成测量页 -> 调 Chrome 量出每个内容块高度
   2) 按 A4 可用高度装箱分页（标题与正文保持同页、表格不拦腰断）
   3) 生成目录（页码由装箱结果反算，迭代至稳定）
   4) 导出最终 HTML + pagemap.json（供 PDF 书签使用）
"""
import html
import json
import os
import re
import subprocess
import sys

import data_win
import data_linux
import data_ch0_4 as D04
import data_ch5_7 as D57
import sources

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.dirname(HERE)
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

TITLE = "应急响应人工排查手册"
VER = "v1.0"
DATE = "2026-10"

PAGE_H = 957.0          # 内容区可用高度（px @96dpi），实测校准值
L0_H, L1_H, TOC_CAP = 8.0, 5.0, 222.0   # 目录行高（mm）与每页容量（mm）

CSS = open(os.path.join(HERE, "style.css"), encoding="utf-8").read()

# ---------------------------------------------------------------- 工具

def esc(s):
    return html.escape(str(s), quote=False)


def md(s):
    """转义 + 极简行内标记（**粗体**、`代码`）"""
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`([^`]+?)`", r"<code>\1</code>", s)
    return s


def cell(s):
    """表格单元格：tag span 保留为 HTML，其余走 md()"""
    s = str(s)
    if s.startswith('<span class="tag'):
        return s
    return md(s)


def tag_of(level):
    m = {"严重": "s4", "高危": "s3", "中危": "s2", "低危": "s1", "提示": "s0"}
    return '<span class="tag %s">%s</span>' % (m.get(level, "s0"), level)


def src_html(s):
    """来源列：脚本（附函数名与关键行）/ 经验"""
    if not s:
        return '<span class="none">—</span>'
    if s == "E":
        return '<span class="srcx"><b>经验</b></span>'
    if s.startswith("S|"):
        f, ln = s[2:].split("|", 1)
        fn = esc(f).replace("_", "_<wbr>")   # 只在下划线处换行，避免函数名被拦腰截断
        return '<span class="srcx"><b>脚本</b><i>%s()</i><em>L%s</em></span>' % (fn, esc(ln))
    return esc(s)


def pre_html(text, lang=""):
    body = esc(text)
    body = re.sub(r"(^|\n)(\s*(?:#|::|//).*)", lambda m: m.group(1) + '<span class="cmt">' + m.group(2) + "</span>", body)
    lbl = '<span class="lbl">%s</span><br>' % lang if lang else ""
    return lbl + body


# ---------------------------------------------------------------- 块构造

def B(t, **kw):
    d = dict(t=t)
    d.update(kw)
    return d


def item_blocks(it, chap_plat, script_map):
    """一个检查项 -> 五个块（标题 / 目的 / 命令 / 样例 / 异常 / 误报 / 证据）"""
    out = []
    func = script_map.get(it["no"], "")
    out.append(B("sec", no=it["no"], title=it["t"], prio=it["prio"],
                 meta="对应脚本：%s()　·　优先级 %s　·　五段式：目的 / 命令 / 样例 / 判据 / 证据" % (func, it["prio"]),
                 keep=True))
    out.append(B("part", em="①", h="检查目的", p=it["purpose"]))

    # 命令按语言分组
    groups, cur, curlang = [], [], None
    for c in it["cmds"]:
        lang, cmd = c.split("|", 1)
        if lang != curlang:
            if cur:
                groups.append((curlang, cur))
            cur, curlang = [], lang
        cur.append(cmd)
    if cur:
        groups.append((curlang, cur))
    out.append(B("part", em="②", h="执行命令", pre=[(l, "\n".join(v)) for l, v in groups],
                 note="以上命令均为只读；【需管理员/root】项见各命令前的权限标注。" if chap_plat == "win" else "以上命令均为只读；标 [root] 的需 sudo 或 root 身份。"))
    out.append(B("part", em="③", h="正常样例", sample=it["sample"], cap="（输出已截断，仅示意形态）"))
    out.append(B("part", em="④", h="异常特征", abns=it["abns"],
                 note=None if it.get("note") else None))
    if it.get("note4"):
        out.append(B("note", x=it["note4"], tight=True))
    if it.get("fp"):
        out.append(B("fp", h="▸ 如何排除误报", items=it["fp"]))
    out.append(B("part", em="⑤", h="证据留存", p=it["ev"]))
    return out


def chapter_open(ch):
    no = ch["no"]
    kicker = ("APPENDIX " + no) if no in ("A", "B") else ("CHAPTER " + no)
    plat = ch.get("plat", "通用")
    return B("chopen", chap=ch, kicker=kicker, plat=plat, newpage=True)


def blocks_from_spec(spec):
    """第 0/3/4/5/6/7 章与附录：把 blocks 规格转成渲染块"""
    out = []
    for b in spec:
        t = b["t"]
        if t == "h2":
            out.append(B("h2", x=b["x"], sub=b.get("sub", ""), keep=True))
        elif t == "p":
            out.append(B("p", x=b["x"]))
        elif t == "pre":
            out.append(B("pre", x=b["x"], cap=b.get("cap", "")))
        elif t == "note":
            out.append(B("note", x=b["x"]))
        elif t == "warn":
            out.append(B("warn", x=b["x"]))
        elif t == "rules":
            out.append(B("rules", items=b["x"]))
        elif t == "table":
            out.append(B("table", head=b["head"], rows=b["rows"], w=b.get("w"), cls=b.get("cls", "t"),
                         blank=b.get("blank", False), cap=b.get("cap", "")))
        elif t == "card":
            out.append(B("card", title=b["title"], items=b["items"]))
        elif t == "cards2":
            out.append(B("cards2", cols=[[B("card", title=c["title"], items=c["items"]) for c in col]
                                         for col in b["cols"]]))
        else:
            raise ValueError("unknown block " + t)
    return out


# ---------------------------------------------------------------- 章节装配

SCRIPT_MAP_WIN = {
    "1.1": "win_env_info", "1.2": "win_accounts", "1.3": "win_autoruns", "1.4": "win_tasks",
    "1.5": "win_services", "1.6": "win_process_net", "1.7": "win_files", "1.8": "win_logs",
    "1.9": "win_logs_advanced", "1.10": "win_security_advanced", "1.11": "win_wmi_subscription",
    "1.12": "win_hijack_points", "1.13": "win_bits", "1.14": "win_av_status",
    "1.15": "win_credentials_config", "1.16": "win_network_config", "1.17": "win_shares",
    "1.18": "win_process_anomaly", "1.19": "win_malware_dossier", "1.20": "win_drivers_certs_firewall",
    "1.21": "win_priv_esc", "1.22": "win_hijack_advanced", "1.23": "win_net_config",
    "1.24": "win_proc_deep", "1.25": "r10_baseline_step(win)", "1.26": "r11_custom_checks",
    "1.27": "r13_rules_checks", "1.28": "win_active_setup", "1.29": "win_ps_profiles",
    "1.30": "win_office_addins", "1.31": "win_persist_attribution", "1.32": "win_weblog_step",
    "1.33": "win_webshell_step",
}
SCRIPT_MAP_LINUX = {
    "2.1": "linux_env_info", "2.2": "linux_accounts", "2.3": "linux_history", "2.4": "linux_cron",
    "2.5": "linux_autoruns", "2.6": "linux_backdoors", "2.7": "linux_net_proc", "2.8": "linux_files",
    "2.9": "linux_logs", "2.10": "linux_hidden_procs", "2.11": "linux_kernel_modules",
    "2.12": "linux_capabilities", "2.13": "linux_ssh_surface", "2.14": "linux_injection_points",
    "2.15": "linux_sched_jobs", "2.16": "linux_web_layer", "2.17": "linux_malware_families",
    "2.18": "linux_lateral_and_tools", "2.19": "linux_log_integrity", "2.20": "linux_audit_logs",
    "2.21": "linux_pkg_verify", "2.22": "linux_container_env", "2.23": "linux_app_logs",
    "2.24": "linux_net_config", "2.25": "linux_persistence", "2.26": "linux_proc_deep",
    "2.27": "r10_baseline_step(linux)", "2.28": "r11_custom_checks", "2.29": "r13_rules_checks",
    "2.30": "r12_container_k8s", "2.31": "linux_weblog_step", "2.32": "linux_webshell_step",
}


def build_chapters():
    # 来源列：脚本 / 经验（按节对齐写入 abns 第三段）
    sources.apply(data_win.ITEMS)
    sources.apply(data_linux.ITEMS)
    chaps = []
    # 第 0 章
    c0 = dict(no="0", title=D04.CH0["title"], plat="通用", lead=D04.CH0["lead"])
    chaps.append((c0, [chapter_open(c0)] + blocks_from_spec(D04.CH0["blocks"])))

    # 第 1 章
    c1 = dict(no="1", title="Windows 主机排查", plat="Windows",
              lead="本章 33 个检查项与 er_check.py 的 WIN_STEPS 一一对应、顺序一致。每一项按五段式执行，做完立即填表 1-1。")
    bl = [chapter_open(c1)]
    for it in data_win.ITEMS:
        bl += item_blocks(it, "win", SCRIPT_MAP_WIN)
    bl += summary_blocks("1", "第 1 章检查结果汇总", [("%s　%s" % (i["no"], i["t"])) for i in data_win.ITEMS])
    chaps.append((c1, bl))

    # 第 2 章
    c2 = dict(no="2", title="Linux 主机排查", plat="Linux",
              lead="本章 32 个检查项与 er_check.py 的 LINUX_STEPS 一一对应、顺序一致。标 [root] 的命令需 root 或 sudo。")
    bl = [chapter_open(c2)]
    for it in data_linux.ITEMS:
        bl += item_blocks(it, "linux", SCRIPT_MAP_LINUX)
    bl += summary_blocks("2", "第 2 章检查结果汇总", [("%s　%s" % (i["no"], i["t"])) for i in data_linux.ITEMS])
    chaps.append((c2, bl))

    for spec in (D04.CH3, D04.CH4, D57.CH5, D57.CH6, D57.CH7):
        c = dict(no=spec["no"], title=spec["title"], plat=spec.get("plat", "通用"), lead=spec["lead"])
        chaps.append((c, [chapter_open(c)] + blocks_from_spec(spec["blocks"])))

    for spec in (D57.APPX_A, D57.APPX_B):
        c = dict(no=spec["no"], title=spec["title"], plat=spec.get("plat", "通用"), lead=spec["lead"])
        chaps.append((c, [chapter_open(c)] + blocks_from_spec(spec["blocks"])))
    return chaps


def summary_blocks(chapno, title, names):
    """章末汇总表：拆成两块（18 行 + 其余），避免跨页拦腰断开"""
    out = [B("h1sec", x="表 %s-1　%s" % (chapno, title),
             meta="共 %d 行 ｜ 每检查完一项立即填写，不要事后回忆" % len(names), keep=True)]
    chunk = 18
    for idx in range(0, len(names), chunk):
        part = names[idx:idx + chunk]
        out.append(B("sumtable", rows=part, start=idx + 1, cont=(idx > 0),
                     total=len(names), chapno=chapno))
    return out


# ---------------------------------------------------------------- 渲染

def render_block(b, ctx):
    t = b["t"]
    if t == "chopen":
        ch = b["chap"]
        no = ch["no"]
        nofmt = ("附录 " + no) if no in ("A", "B") else ("第 %s 章" % no)
        titfmt = ch["title"]
        return ('<div class="blk chopen"><div class="kicker">%s</div>'
                '<h1><span class="no">%s</span>%s</h1>'
                '<div class="lead"><span class="plat">%s</span>%s</div></div>'
                % (esc(b["kicker"] + "　/　" + ch.get("plat", "通用")), esc(nofmt), esc(titfmt),
                   esc(ch.get("plat", "通用")), md(ch["lead"])))
    if t == "sec":
        return ('<div class="blk"><h1 class="sec"><span class="row"><span class="no">%s</span>'
                '<span class="ttl">%s</span><span class="prio">%s</span></span>'
                '<span class="meta">%s</span></h1>'
                '<div class="checks"><span><i class="box"></i>已检查</span>'
                '<span><i class="box"></i>正常</span><span><i class="box"></i>异常</span>'
                '<span style="color:#666">结果与证据填入表 %s-1</span></div></div>'
                % (esc(b["no"]), esc(b["title"]), esc(b["prio"]), esc(b["meta"]), b["no"].split(".")[0]))
    if t == "part":
        h = '<h2><em>%s</em>%s</h2>' % (esc(b["em"]), esc(b["h"]))
        body = ""
        if b.get("p"):
            body = "<p>%s</p>" % md(b["p"])
        if b.get("pre"):
            body += "".join('<pre>%s</pre>' % pre_html(txt, l) for l, txt in b["pre"])
        if b.get("sample"):
            body += '<pre>%s</pre>' % pre_html(b["sample"])
            body += '<div class="note">%s</div>' % esc(b["cap"])
        if b.get("abns"):
            rows = []
            for x in b["abns"]:
                parts = x.split("|", 2)
                lvl, desc = parts[0], parts[1]
                src = parts[2] if len(parts) > 2 else ""
                rows.append('<tr><td>%s</td><td class="lv">%s</td><td class="src">%s</td></tr>'
                            % (md(desc), tag_of(lvl), src_html(src)))
            body += ('<table class="t abn"><thead><tr><th>看到什么（命中即按右侧级别记录）</th>'
                     '<th class="lv">级别</th><th class="src">来源</th></tr></thead><tbody>%s</tbody></table>' % "".join(rows))
        return '<div class="blk part">%s%s</div>' % (h, body)
    if t == "fp":
        lis = "".join("<li>%s</li>" % md(x) for x in b["items"])
        return '<div class="blk fp"><h3>%s</h3><ul>%s</ul></div>' % (esc(b["h"]), lis)
    if t == "h2":
        sub = '　<span style="font-weight:400;font-size:8pt;color:#666">%s</span>' % esc(b["sub"]) if b.get("sub") else ""
        return '<div class="blk h2b"><h2>%s%s</h2></div>' % (md(b["x"]), sub)
    if t == "p":
        return '<div class="blk"><p>%s</p></div>' % md(b["x"])
    if t == "pre":
        cap = '<div class="cap">%s</div>' % md(b["cap"]) if b.get("cap") else ""
        return '<div class="blk">%s<pre>%s</pre></div>' % (cap, pre_html(b["x"]))
    if t == "note":
        return '<div class="blk note">%s</div>' % md(b["x"])
    if t == "warn":
        return '<div class="blk warn">%s</div>' % md(b["x"])
    if t == "rules":
        rows = "".join('<div class="rule"><b>%s</b><span>%s</span></div>' % (esc(a), md(bb)) for a, bb in b["items"])
        return '<div class="blk rules">%s</div>' % rows
    if t == "table":
        return '<div class="blk">%s</div>' % table_html(b)
    if t == "sumtable":
        return '<div class="blk">%s</div>' % sumtable_html(b)
    if t == "h1sec":
        return ('<div class="blk"><h1 class="sec"><span class="row"><span class="ttl">%s</span></span>'
                '<span class="meta">%s</span></h1></div>' % (esc(b["x"]), esc(b["meta"])))
    if t == "card":
        lis = "".join('<div class="crow"><span class="cl">%s</span><code>%s</code></div>' % (esc(k), esc(v)) for k, v in b["items"])
        return '<div class="blk card"><h3>%s</h3>%s</div>' % (esc(b["title"]), lis)
    if t == "cards2":
        cols = "".join('<div class="col">%s</div>' % "".join(render_block(x, ctx) for x in col) for col in b["cols"])
        return '<div class="blk"><div class="twocol">%s</div></div>' % cols
    raise ValueError(t)


def table_html(b):
    ws = b.get("w") or []
    colg = ""
    if ws:
        colg = "<colgroup>%s</colgroup>" % "".join('<col style="width:%s">' % w for w in ws)
    head = "".join("<th>%s</th>" % cell(h) for h in b["head"])
    rows = []
    for i, r in enumerate(b["rows"]):
        cls = ' class="alt"' if i % 2 == 1 else ""
        tds = "".join('<td>%s</td>' % ("" if str(c) == "" else cell(c)) for c in r)
        rows.append("<tr%s>%s</tr>" % (cls, tds))
    return ('<table class="%s">%s<thead><tr>%s</tr></thead><tbody>%s</tbody></table>'
            % (b["cls"], colg, head, "".join(rows)))


def sumtable_html(b):
    head = ('<thead><tr><th style="width:8mm">#</th><th>检查项</th>'
            '<th style="width:27mm">结果</th><th style="width:42mm">证据位置</th><th style="width:30mm">备注</th></tr></thead>')
    rows = []
    for i, name in enumerate(b["rows"]):
        n = b["start"] + i
        cls = ' class="alt"' if i % 2 == 1 else ""
        rows.append('<tr%s><td class="idx">%d</td><td class="n">%s</td>'
                    '<td class="r">☐正常 ☐异常</td><td class="e"></td><td></td></tr>'
                    % (cls, n, esc(name)))
    cont = '<div class="cap">（续）第 %s 页起为第 %d–%d 行，共 %d 行</div>' % (
        b["start"], b["start"], b["start"] + len(b["rows"]) - 1, b["total"]) if b["cont"] else ""
    return cont + '<table class="sum">%s<tbody>%s</tbody></table>' % (head, "".join(rows))


# ---------------------------------------------------------------- 测量

def measure(blocks):
    parts = ['<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><style>%s</style></head><body>'
             '<div id="measure">' % CSS]
    for i, b in enumerate(blocks):
        parts.append('<div class="blk" data-bid="%d">%s</div>' % (i, render_block(b, None)))
    parts.append("</div><script>%s</script></body></html>" % MEASURE_JS)
    path = os.path.join(HERE, "_measure.html")
    open(path, "w", encoding="utf-8").write("".join(parts))
    out = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                          "--virtual-time-budget=8000", "--dump-dom", "file:///" + path.replace("\\", "/")],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    m = re.search(r'(?s)<pre id="OUT">(.*?)</pre>', out.stdout)
    if not m:
        raise SystemExit("测量失败，未拿到高度数据。stderr:\n" + out.stderr[-2000:])
    data = json.loads(html.unescape(m.group(1)))
    return [d["h"] for d in data]


MEASURE_JS = """
window.addEventListener('load', function(){
  var out=[];
  document.querySelectorAll('#measure > .blk').forEach(function(el){
    out.push({id: el.dataset.bid, h: Math.ceil(el.getBoundingClientRect().height * 100) / 100});
  });
  document.body.innerHTML='<pre id="OUT">'+JSON.stringify(out)+'</pre>';
});
"""


# ---------------------------------------------------------------- 装箱

def pack(blocks, heights):
    """返回 [(blocks...), ...] 每页的块索引列表"""
    pages, cur, used = [], [], 0.0
    i, n = 0, len(blocks)
    while i < n:
        b = blocks[i]
        h = heights[i]

        # 章首强制换页
        if b.get("newpage") and cur:
            pages.append(cur); cur, used = [], 0.0

        # keep：与下一块同页（下一块高度不足以单独成页时才合并）
        if b.get("keep") and i + 1 < n:
            h2 = heights[i + 1]
            if h + h2 <= PAGE_H * 0.98:
                if used + h + h2 > PAGE_H and cur:
                    pages.append(cur); cur, used = [], 0.0
                cur += [i, i + 1]; used += h + h2
                i += 2
                continue

        if used + h > PAGE_H and cur:
            pages.append(cur); cur, used = [], 0.0
        cur.append(i); used += h
        i += 1
    if cur:
        pages.append(cur)
    return pages


# ---------------------------------------------------------------- 目录

def toc_entries(chaps, page_of_anchor):
    ents = []
    for ch, blocks in chaps:
        no = ch["no"]
        label = ("附录 %s　%s" % (no, ch["title"])) if no in ("A", "B") else ("第 %s 章　%s" % (no, ch["title"]))
        ents.append(("l0", label, page_of_anchor.get("ch" + no, 0)))
        for b in blocks:
            if b["t"] == "sec":
                ents.append(("l1", "%s　%s" % (b["no"], b["title"]), page_of_anchor.get("b" + b["no"], 0)))
            elif b["t"] == "h1sec":
                ents.append(("l1", b["x"], page_of_anchor.get("h" + b["x"], 0)))
            elif b["t"] == "h2":
                ents.append(("l1", re.sub(r"\s+", " ", b["x"]), page_of_anchor.get("h" + b["x"], 0)))
    return ents


def toc_pages(ents):
    """按固定行高把目录条目分页，返回 (pages_of_rows, total_pages)"""
    cap = TOC_CAP
    out, cur, used = [], [], 0.0
    for kind, label, pg in ents:
        h = L0_H if kind == "l0" else L1_H
        if used + h > cap and cur:
            out.append(cur); cur, used = [], 0.0
        cur.append((kind, label, pg))
        used += h
    if cur:
        out.append(cur)
    return out


# ---------------------------------------------------------------- 主流程

def build():
    chaps = build_chapters()
    # 展开为单一 block 列表，并记录每章/每节所属
    all_blocks, owner = [], []
    for ch, blocks in chaps:
        for b in blocks:
            all_blocks.append(b)
            owner.append(ch["no"])

    heights = measure(all_blocks)
    pages = pack(all_blocks, heights)

    # 计算锚点页码（正文内部相对页序，从 1 开始）
    anchor = {}
    for pi, idxs in enumerate(pages, start=1):
        for bi in idxs:
            b = all_blocks[bi]
            if b["t"] == "chopen":
                anchor["ch" + b["chap"]["no"]] = pi
            elif b["t"] == "sec":
                anchor.setdefault("b" + b["no"], pi)
            elif b["t"] == "h1sec":
                anchor.setdefault("h" + b["x"], pi)
            elif b["t"] == "h2":
                anchor.setdefault("h" + b["x"], pi)

    # 迭代目录页数，直到稳定
    L = 3
    for _ in range(6):
        ents = toc_entries(chaps, {k: v + 1 + L for k, v in anchor.items()})
        tp = toc_pages(ents)
        if len(tp) == L:
            break
        L = len(tp)

    body_pages = len(pages)
    total = 1 + L + body_pages

    # ---- 封面
    cover = ('<section class="sheet odd cover-sheet">'
             '<div class="tab"><i class="c">手册</i></div>'
             '<div class="content"><div class="cover">'
             '<div class="top">INCIDENT RESPONSE　/　OFFLINE MANUAL</div>'
             '<div class="mid">'
             '<div class="t1">应急响应<br>人工排查手册</div>'
             '<div class="t2">Windows　·　Linux　·　Web 日志　·　WebShell</div>'
             '<div class="rule"></div>'
             '<div class="one">一句话用法：拿一台不能联网、不能插盘的主机，翻到对应章，照着命令逐条敲，把输出填进本章末尾的汇总表，最后用第 7 章收敛结论。</div>'
             '<div class="spec">'
             '<div><b>适用平台</b>Windows Server 2008R2–2022<br>主流 Linux 发行版</div>'
             '<div><b>版本</b>%s（%s）</div>'
             '<div><b>覆盖范围</b>65 个检查项<br>Windows 33 / Linux 32</div>'
             '<div><b>对应脚本</b>er_check.py 1.0</div>'
             '</div></div>'
             '<div class="bot">'
             '本手册全部命令均为只读，不删除、不修改、不结束进程、不重启。<br>'
             '唯一的写操作集中在第 7.5 节，且标注「取证之后再操作」。<br>'
             '不含二维码、网址、外链字体，可在完全离线的打印环境使用。<br>'
             '来源列中的 Lxxxx 行号对应当前版本脚本的快照；脚本升级后请以函数名为准，行号仅作辅助定位。'
             '</div></div></div></section>' % (VER, DATE))

    # ---- 目录
    toc_html = []
    for pi, rows in enumerate(toc_pages(toc_entries(chaps, {k: v + 1 + L for k, v in anchor.items()})), start=1):
        items = []
        for kind, label, pg in rows:
            items.append('<div class="row %s"><span class="tx">%s</span><span class="dot"></span>'
                         '<span class="pg">%s</span></div>' % (kind, esc(label), pg if pg else "—"))
        head = ('<div class="toc"><h1>目　录</h1><div class="sub">共 %d 页 ｜ 页码为正文实际页码 ｜ 章节号与脚本检查顺序一致</div>%s</div>'
                % (total, "".join(items)))
        if pi == 1:
            head = ('<div class="toc"><h1>目　录</h1><div class="sub">共 %d 页 ｜ 页码为正文实际页码 ｜ 章节号与脚本检查顺序一致</div>%s</div>'
                    % (total, "".join(items)))
        else:
            head = '<div class="toc"><div class="sub" style="margin-bottom:3mm">目　录（续）</div>%s</div>' % "".join(items)
        toc_html.append(head)

    # ---- 正文页
    chap_plat = {c["no"]: c.get("plat", "通用") for c, _ in chaps}
    chap_title = {c["no"]: c["title"] for c, _ in chaps}
    out = [cover]
    abs_page = 1
    for i, tp in enumerate(toc_html):
        abs_page += 1
        odd = abs_page % 2 == 1
        out.append('<section class="sheet %s"><div class="tab"><i class="c">目录</i></div>'
                   '<div class="ph"><span><b>%s</b>　%s　只读版</span><span>目录</span></div>'
                   '<div class="content">%s</div>'
                   '<div class="pf"><span class="l">%s　·　现场手工排查</span><span class="r">— %d —</span></div>'
                   '</section>' % ("odd" if odd else "even", TITLE, VER, tp, "er_check 1.0", abs_page))

    tab_top = {"0": 34, "1": 44, "2": 82, "3": 120, "4": 158, "5": 196, "6": 34, "7": 72, "A": 110, "B": 148}
    tab_cls = {"1": "w", "2": "l"}
    for pi, idxs in enumerate(pages, start=1):
        abs_page += 1
        odd = abs_page % 2 == 1
        chno = owner[idxs[0]]
        plat = chap_plat[chno]
        cl = tab_cls.get(chno, "c")
        tablabel = ("附录" + chno) if chno in ("A", "B") else ("第 %s 章" % chno)
        bl = "".join(render_block(all_blocks[bi], None) for bi in idxs)
        out.append('<section class="sheet %s"><div class="tab"><i class="%s" style="top:%dmm">%s</i></div>'
                   '<div class="annot"><span>批　注</span></div>'
                   '<div class="ph"><span><b>%s</b>　%s　只读版</span><span>%s</span></div>'
                   '<div class="content">%s</div>'
                   '<div class="pf"><span class="l">er_check 1.0　·　%s　·　现场手工排查</span>'
                   '<span class="r">— %d —</span></div></section>'
                   % ("odd" if odd else "even", cl, tab_top.get(chno, 34), esc(tablabel),
                      TITLE, VER, esc(("%s %s" % (("附录" if chno in ("A", "B") else "第 " + chno + " 章"), chap_title[chno]))),
                      bl, plat, abs_page))

    doc = ('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
           '<title>%s %s</title><style>%s</style></head><body>%s</body></html>'
           % (TITLE, VER, CSS, "".join(out)))

    html_path = os.path.join(OUT_DIR, "应急响应人工排查手册_%s.html" % VER)
    open(html_path, "w", encoding="utf-8").write(doc)

    pagemap = dict(total=total, toc_pages=L, body_pages=body_pages,
                   chapters={c["no"]: {"title": c["title"], "page": anchor.get("ch" + c["no"], 0) + 1 + L}
                             for c, _ in chaps},
                   sections=[{"no": b["no"], "title": b["title"], "page": anchor.get("b" + b["no"], 0) + 1 + L}
                             for b in all_blocks if b["t"] == "sec"],
                   h2=[{"title": b["x"], "page": anchor.get("h" + b["x"], 0) + 1 + L}
                       for b in all_blocks if b["t"] == "h2"],
                   tables=[{"title": b["x"], "page": anchor.get("h" + b["x"], 0) + 1 + L}
                           for b in all_blocks if b["t"] == "h1sec"],
                   heights=heights)
    json.dump(pagemap, open(os.path.join(HERE, "pagemap.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print("pages total=%d (cover 1 + toc %d + body %d)" % (total, L, body_pages))
    print("max block height=%.0f  min page fill=%.0f%%" % (
        max(heights),
        100.0 * min(sum(heights[i] for i in p) for p in pages) / PAGE_H))
    over = [(i, h) for i, h in enumerate(heights) if h > PAGE_H]
    if over:
        print("!! blocks taller than one page:", over)
    print("html ->", html_path)


if __name__ == "__main__":
    build()
