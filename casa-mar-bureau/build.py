"""index.html (publication, three.js via jsDelivr) et local.html (rendus hors ligne, node_modules)."""
import os
here = os.path.dirname(os.path.abspath(__file__))
t = open(os.path.join(here, "index.template.html")).read()
cdn = '<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}</script>'
loc = '<script type="importmap">{"imports":{"three":"./node_modules/three/build/three.module.js","three/addons/":"./node_modules/three/examples/jsm/"}}</script>'
open(os.path.join(here, "index.html"), "w").write(t.replace("{{IMPORTMAP}}", cdn))
open(os.path.join(here, "local.html"), "w").write(t.replace("{{IMPORTMAP}}", loc))
print("ok")
