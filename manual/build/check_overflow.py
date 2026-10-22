# -*- coding: utf-8 -*-
"""校验：把成品 HTML 载入无头浏览器，逐页测量内容是否溢出（被 overflow:hidden 裁掉）。"""
import os, re, subprocess, json, html

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SRC = os.path.join(OUT, "应急响应人工排查手册_v1.0.html")

JS = """
window.addEventListener('load', function(){
  var bad=[], pages=document.querySelectorAll('.sheet');
  pages.forEach(function(p,i){
    var c=p.querySelector('.content');
    if(!c) return;
    var over = c.scrollHeight - c.clientHeight;
    if(over > 1) bad.push({p:i+1, over:Math.round(over), sh:c.scrollHeight, ch:c.clientHeight});
  });
  document.body.innerHTML='<pre id="OUT">'+JSON.stringify({pages:pages.length, bad:bad})+'</pre>';
});
"""

doc = open(SRC, encoding="utf-8").read()
doc = doc.replace("</body>", "<script>%s</script></body>" % JS)
p = os.path.join(HERE, "_check.html")
open(p, "w", encoding="utf-8").write(doc)

r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=12000",
                    "--dump-dom", "file:///" + p.replace("\\", "/")],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
m = re.search(r'(?s)<pre id="OUT">(.*?)</pre>', r.stdout)
if not m:
    raise SystemExit("check failed: " + r.stderr[-800:])
d = json.loads(html.unescape(m.group(1)))
print("pages:", d["pages"], "overflow pages:", len(d["bad"]))
for b in d["bad"]:
    print("  page %d  over=%dpx  (scroll %d / client %d)" % (b["p"], b["over"], b["sh"], b["ch"]))
