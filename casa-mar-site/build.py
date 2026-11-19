"""Assemble index.html from template.html by inlining the traced logo paths."""
import re, os
here = os.path.dirname(os.path.abspath(__file__))
t = open(os.path.join(here, "template.html")).read()
for key, f in [("ICON", "logo-icon"), ("H", "logo-h"), ("V", "logo-v")]:
    svg = open(os.path.join(here, "assets", f + ".svg")).read()
    t = t.replace("{{" + key + "_VB}}", re.search(r'viewBox="([^"]+)"', svg).group(1))
    t = t.replace("{{" + key + "_D}}", re.search(r' d="([^"]+)"', svg).group(1))
open(os.path.join(here, "index.html"), "w").write(t)
print("index.html", len(t))
