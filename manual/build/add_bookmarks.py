# -*- coding: utf-8 -*-
"""给打印好的 PDF 加导航书签（PDF 大纲 / 书签面板），页码取自 pagemap.json。"""
import json, os, re, sys
from pypdf import PdfReader, PdfWriter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
SRC = os.path.join(OUT, "_raw.pdf")
DST = os.path.join(OUT, "应急响应人工排查手册_v1.0.pdf")

pm = json.load(open(os.path.join(HERE, "pagemap.json"), encoding="utf-8"))
chapters = pm["chapters"]
secs = pm["sections"]
h2s = pm["h2"]
tabs = pm["tables"]

# 章节边界（按页码排序）
bounds = sorted([(v["page"], k) for k, v in chapters.items()])
order = [k for _, k in bounds]


def chap_of(page):
    cur = order[0]
    for p, k in bounds:
        if page >= p:
            cur = k
    return cur


groups = {k: [] for k in order}
for s in secs:
    groups[chap_of(s["page"])].append(("sec", s))
for s in h2s:
    groups[chap_of(s["page"])].append(("h2", s))
for s in tabs:
    groups[chap_of(s["page"])].append(("tab", s))

r = PdfReader(SRC)
w = PdfWriter(clone_from=r)

w.add_outline_item("封面", 0)
w.add_outline_item("目录", 1)

for k in order:
    info = chapters[k]
    label = ("附录 %s　%s" % (k, info["title"])) if k in ("A", "B") else ("第 %s 章　%s" % (k, info["title"]))
    parent = w.add_outline_item(label, max(0, info["page"] - 1))
    items = sorted(groups[k], key=lambda x: x[1]["page"])
    for kind, it in items:
        if kind == "sec":
            title = "%s　%s" % (it["no"], it["title"])
        elif kind == "tab":
            title = it["title"]
        else:
            title = re.sub(r"^(\d+\.\d+|[A-B]\.\d+)　?", lambda m: m.group(1) + "　", it["title"])
            title = title.replace("　　", "　")
        w.add_outline_item(title, max(0, it["page"] - 1), parent=parent)

try:
    w.page_mode = "/UseOutlines"
except Exception as e:
    print("page_mode skip:", e)

with open(DST, "wb") as f:
    w.write(f)

print("bookmarks:", len(w.outline), "->", DST)
print("pages:", len(w.pages))
