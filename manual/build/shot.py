# -*- coding: utf-8 -*-
"""从成品 HTML 中抽出指定页，单独渲染成一张 PNG，用于目检排版。"""
import os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SRC = os.path.join(OUT, "应急响应人工排查手册_v1.0.html")

doc = open(SRC, encoding="utf-8").read()
head = doc[:doc.index("</head>")]
secs = re.findall(r'(?s)<section class="sheet.*?</section>', doc)
print("sections", len(secs))

extra = ("<style>body{background:#fff!important}.sheet{margin:0!important;box-shadow:none!important;"
         "page-break-after:auto!important}</style>")

for n in [int(x) for x in sys.argv[1:]]:
    p = os.path.join(HERE, "_view.html")
    open(p, "w", encoding="utf-8").write(head + extra + "</head><body>" + secs[n - 1] + "</body></html>")
    png = os.path.join(OUT, "_p%d.png" % n)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--window-size=794,1123", "--virtual-time-budget=3000",
                    "--screenshot=" + png, "file:///" + p.replace("\\", "/")],
                   capture_output=True)
    print("shot", n, os.path.getsize(png))
