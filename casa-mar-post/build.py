"""Assemble index.html : injecte le logo vectorisé du site dans le gabarit."""
import re, os
here = os.path.dirname(os.path.abspath(__file__))
t = open(os.path.join(here, "template.html")).read()
svg = open(os.path.join(here, "..", "casa-mar-site", "assets", "logo-icon.svg")).read()
t = t.replace("{{ICON_VB}}", re.search(r'viewBox="([^"]+)"', svg).group(1)).replace("{{ICON_D}}", re.search(r' d="([^"]+)"', svg).group(1))
open(os.path.join(here, "index.html"), "w").write(t); print("index.html", len(t))
