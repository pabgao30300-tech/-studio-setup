// Casa Mar Studio — bureaux 80 m². Modèle 3D complet (three.js), partagé par la visite interactive,
// les rendus haute définition et le plan 2D coté (même source de vérité : LAYOUT ci-dessous).
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { SVGLoader } from 'three/addons/loaders/SVGLoader.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/addons/postprocessing/GTAOPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

/* =====================================================================================
   PROGRAMME — mètres. Intérieur 10,00 × 8,00 = 80 m², hauteur sous plafond 3,00.
   x : ouest → est · z : nord (rue, entrée) → sud (grande façade vitrée, jardin)
   ===================================================================================== */
export const LAYOUT = {
  W: 10, D: 8, H: 3,
  zones: [
    { id: 'salon', name: 'Entrée & salon', x0: 0, z0: 0, x1: 3.4, z1: 4.4, color: '#E8B04A' },
    { id: 'cuisine', name: 'Kitchenette & café', x0: 3.4, z0: 0, x1: 6.6, z1: 2.6, color: '#F4A195' },
    { id: 'circ', name: 'Circulation', x0: 3.4, z0: 2.6, x1: 6.6, z1: 4.6, color: '#cfc9bf', extra: { x0: 0, z0: 4.4, x1: 3.4, z1: 4.6 } },
    { id: 'open', name: 'Open space · 6 postes', x0: 0, z0: 4.6, x1: 6.6, z1: 8, color: '#7BB1DD' },
    { id: 'reunion', name: 'Salle de réunion', x0: 6.6, z0: 0, x1: 10, z1: 3.8, color: '#0B0F1E' },
    { id: 'alcove', name: 'Alcôve casiers & repro', x0: 6.6, z0: 3.8, x1: 10, z1: 4.8, color: '#9a8f7e' },
    { id: 'direction', name: 'Bureau de direction', x0: 6.6, z0: 4.8, x1: 10, z1: 8, color: '#E4A479' },
  ],
};
export const area = z => +(((z.x1 - z.x0) * (z.z1 - z.z0)) + (z.extra ? (z.extra.x1 - z.extra.x0) * (z.extra.z1 - z.extra.z0) : 0)).toFixed(2);

const C = { navy: '#0B0F1E', orange: '#E8B04A', blue: '#7BB1DD', cream: '#FFFEF1', red: '#D9203D', pink: '#F4A195', peach: '#E4A479' };

/* ---------------- aléatoire déterministe ---------------- */
let seed = 11;
const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
const rr = (a, b) => a + (b - a) * rnd();

/* ---------------- textures procédurales ---------------- */
function canvasTex(size, draw, { repeat = [1, 1], srgb = true } = {}) {
  const c = document.createElement('canvas'); c.width = c.height = size;
  const x = c.getContext('2d'); draw(x, size);
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(...repeat); t.anisotropy = 8;
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
function grain(x, s, amp) {
  const d = x.getImageData(0, 0, s, s), p = d.data;
  for (let i = 0; i < p.length; i += 4) { const n = (rnd() - .5) * amp; p[i] += n; p[i + 1] += n; p[i + 2] += n; }
  x.putImageData(d, 0, 0);
}
const TEX = {};
function makeTextures() {
  seed = 3;
  TEX.concrete = canvasTex(1024, (x, s) => {             // béton ciré : nuages doux + passes de lisseuse
    x.fillStyle = '#cfc8bd'; x.fillRect(0, 0, s, s);
    for (let i = 0; i < 900; i++) {
      const r = rr(30, 160), cx = rnd() * s, cy = rnd() * s, l = rnd() > .5;
      const g = x.createRadialGradient(cx, cy, 0, cx, cy, r);
      g.addColorStop(0, l ? 'rgba(236,230,220,.10)' : 'rgba(160,150,138,.09)'); g.addColorStop(1, 'rgba(0,0,0,0)');
      x.fillStyle = g; x.fillRect(cx - r, cy - r, r * 2, r * 2);
    }
    x.globalAlpha = .05;
    for (let i = 0; i < 140; i++) { x.strokeStyle = rnd() > .5 ? '#fff' : '#8d8478'; x.lineWidth = rr(4, 18); x.beginPath();
      const cx = rnd() * s, cy = rnd() * s, r = rr(60, 220); x.arc(cx, cy, r, rr(0, 6), rr(0, 6) + 1.2); x.stroke(); }
    x.globalAlpha = 1; grain(x, s, 10);
  }, { repeat: [3, 2.4] });
  TEX.oak = canvasTex(1024, (x, s) => {                  // chêne : veinage
    const g = x.createLinearGradient(0, 0, s, 0); g.addColorStop(0, '#c49a6c'); g.addColorStop(.5, '#cfa678'); g.addColorStop(1, '#c39668');
    x.fillStyle = g; x.fillRect(0, 0, s, s);
    for (let i = 0; i < 220; i++) {
      x.strokeStyle = `rgba(${rnd() > .5 ? '120,80,45' : '150,105,65'},${rr(.05, .22)})`; x.lineWidth = rr(.6, 3.2);
      x.beginPath(); let px = rnd() * s; x.moveTo(px, 0);
      for (let y = 0; y <= s; y += 32) { px += rr(-4, 4) + Math.sin(y / 90 + i) * 1.2; x.lineTo(px, y); } x.stroke();
    }
    grain(x, s, 8);
  });
  TEX.plaster = canvasTex(512, (x, s) => { x.fillStyle = '#efebe3'; x.fillRect(0, 0, s, s); grain(x, s, 7); }, { repeat: [3, 2] });
  TEX.tiles = canvasTex(1024, (x, s) => {                // zellige orange, émail irrégulier
    const n = 8, c = s / n; x.fillStyle = '#efe7d8'; x.fillRect(0, 0, s, s);
    for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
      const h = 36 + rr(-4, 4), l = 58 + rr(-8, 6);
      const g = x.createLinearGradient(i * c, j * c, i * c + c, j * c + c);
      g.addColorStop(0, `hsl(${h},74%,${l + 6}%)`); g.addColorStop(1, `hsl(${h - 3},70%,${l - 6}%)`);
      x.fillStyle = g; x.fillRect(i * c + 3, j * c + 3, c - 6, c - 6);
    }
    grain(x, s, 6);
  }, { repeat: [3, 1] });
  TEX.fabric = canvasTex(256, (x, s) => { x.fillStyle = '#808080'; x.fillRect(0, 0, s, s);
    for (let i = 0; i < 5000; i++) { x.fillStyle = `rgba(${rnd() > .5 ? 255 : 0},${rnd() > .5 ? 255 : 0},${rnd() > .5 ? 255 : 0},.05)`; x.fillRect(rnd() * s, rnd() * s, 2, 2); }
    grain(x, s, 40); }, { repeat: [4, 4], srgb: false });
  TEX.rug = canvasTex(1024, (x, s) => {                  // tapis : les vagues Casa Mar
    x.fillStyle = '#efe6d2'; x.fillRect(0, 0, s, s);
    x.strokeStyle = C.navy; x.lineWidth = 26; x.strokeRect(40, 40, s - 80, s - 80);
    const cols = [C.blue, C.orange, C.blue];
    cols.forEach((col, k) => { x.strokeStyle = col; x.lineWidth = 34; x.lineCap = 'round'; x.beginPath();
      for (let px = 140; px <= s - 140; px += 8) { const y = s * (.36 + k * .14) + Math.sin(px / 52) * 34; px === 140 ? x.moveTo(px, y) : x.lineTo(px, y); } x.stroke(); });
    grain(x, s, 18);
  });
  TEX.travertine = canvasTex(512, (x, s) => { x.fillStyle = '#ddd0b8'; x.fillRect(0, 0, s, s);
    for (let i = 0; i < 90; i++) { x.fillStyle = `rgba(170,150,120,${rr(.05, .2)})`; x.fillRect(0, rnd() * s, s, rr(1, 4)); }
    for (let i = 0; i < 260; i++) { x.fillStyle = 'rgba(150,130,100,.25)'; x.beginPath(); x.ellipse(rnd() * s, rnd() * s, rr(1, 5), rr(.5, 1.5), 0, 0, 7); x.fill(); }
    grain(x, s, 8); });
  TEX.screen = canvasTex(512, (x, s) => {                // écrans : visuels Casa Mar
    x.fillStyle = C.navy; x.fillRect(0, 0, s, s);
    x.fillStyle = C.orange; x.beginPath(); x.arc(s * .5, s * .55, s * .26, 0, 7); x.fill();
    x.fillStyle = C.navy; for (let i = 0; i < 5; i++) x.fillRect(0, s * .6 + i * s * .06, s, s * .018 + i * 2);
    x.strokeStyle = C.blue; x.lineWidth = 10; x.beginPath(); for (let px = 0; px <= s; px += 6) { const y = s * .88 + Math.sin(px / 24) * 10; px ? x.lineTo(px, y) : x.moveTo(px, y); } x.stroke();
  });
  TEX.sunFilm = canvasTex(1024, (x, s) => {              // vitrophanie de la salle de réunion : soleil rayé
    x.clearRect(0, 0, s, s); x.fillStyle = 'rgba(232,176,74,.82)'; x.beginPath(); x.arc(s / 2, s / 2, s * .45, 0, 7); x.fill();
    x.globalCompositeOperation = 'destination-out'; for (let i = 0; i < 7; i++) x.fillRect(0, s * .55 + i * s * .065, s, 10 + i * 4);
  }, { });
  TEX.poster = canvasTex(512, (x, s) => {                // affiche du salon
    x.fillStyle = '#efe6d2'; x.fillRect(0, 0, s, s);
    x.fillStyle = C.orange; x.beginPath(); x.arc(s / 2, s * .42, s * .3, 0, 7); x.fill();
    x.fillStyle = '#efe6d2'; for (let i = 0; i < 6; i++) x.fillRect(0, s * .48 + i * s * .045, s, 6 + i * 2);
    x.fillStyle = C.navy; x.font = `${s * .1}px Kokoschka, sans-serif`; x.textAlign = 'center'; x.fillText('CASA MAR', s / 2, s * .9);
  });
  TEX.wavePrint = canvasTex(512, (x, s) => {
    x.fillStyle = C.navy; x.fillRect(0, 0, s, s); x.lineCap = 'round';
    [C.orange, C.blue, C.cream].forEach((c, k) => { x.strokeStyle = c; x.lineWidth = 18; x.beginPath();
      for (let px = 60; px <= s - 60; px += 6) { const y = s * (.35 + k * .15) + Math.sin(px / 28) * 22; px === 60 ? x.moveTo(px, y) : x.lineTo(px, y); } x.stroke(); });
  });
  TEX.cork = canvasTex(512, (x, s) => { x.fillStyle = '#b98c5c'; x.fillRect(0, 0, s, s);
    for (let i = 0; i < 9000; i++) { x.fillStyle = `rgba(${rnd() > .5 ? '90,55,25' : '230,200,160'},.25)`; x.fillRect(rnd() * s, rnd() * s, rr(1, 3), rr(1, 3)); } });
  TEX.deck = canvasTex(512, (x, s) => { for (let i = 0; i < 8; i++) { x.fillStyle = `hsl(28,${rr(25, 35)}%,${rr(38, 46)}%)`; x.fillRect(0, i * s / 8, s, s / 8 - 4); x.fillStyle = '#3b2b1d'; x.fillRect(0, (i + 1) * s / 8 - 4, s, 4); } grain(x, s, 12); }, { repeat: [8, 2] });
}

/* ---------------- matériaux ---------------- */
const M = {};
function makeMaterials() {
  const std = (o) => new THREE.MeshStandardMaterial(Object.assign({ envMapIntensity: .42 }, o));
  M.concrete = std({ map: TEX.concrete, roughness: .5, metalness: 0 });
  M.plaster = std({ map: TEX.plaster, roughness: .95 });
  M.ceiling = std({ color: '#e9e5dd', roughness: .95 });
  M.navy = std({ color: C.navy, roughness: .85 });
  M.oak = std({ map: TEX.oak, roughness: .55 });
  M.oakDark = std({ map: TEX.oak, color: '#9c7a5a', roughness: .6 });
  M.steel = std({ color: '#1b1c20', roughness: .38, metalness: .85 });
  M.alu = std({ color: '#c9c9c6', roughness: .28, metalness: .9 });
  M.brass = std({ color: C.orange, roughness: .32, metalness: .65 });
  M.glass = new THREE.MeshPhysicalMaterial({ color: '#e7f0f2', transparent: true, opacity: .14, roughness: .02, metalness: 0, envMapIntensity: 1.2, side: THREE.DoubleSide, depthWrite: false });
  M.film = new THREE.MeshStandardMaterial({ map: TEX.sunFilm, transparent: true, roughness: .4, side: THREE.DoubleSide, depthWrite: false });
  const fab = (c) => std({ color: c, roughness: .96, bumpMap: TEX.fabric, bumpScale: .6 });
  M.orange = fab(C.orange); M.blue = fab(C.blue); M.navyFab = fab('#1c2340'); M.boucle = fab('#ece4d3'); M.greyFab = fab('#8a8780');
  M.tiles = std({ map: TEX.tiles, roughness: .22 });
  M.counter = std({ map: TEX.concrete, color: '#a39b90', roughness: .45 });
  M.travertine = std({ map: TEX.travertine, roughness: .5 });
  M.rug = std({ map: TEX.rug, roughness: 1 });
  M.black = std({ color: '#141416', roughness: .5 });
  M.white = std({ color: '#f3f1ec', roughness: .5 });
  M.screen = new THREE.MeshStandardMaterial({ map: TEX.screen, emissive: '#ffffff', emissiveMap: TEX.screen, emissiveIntensity: .7, roughness: .2 });
  M.poster = std({ map: TEX.poster, roughness: .8 });
  M.wavePrint = std({ map: TEX.wavePrint, roughness: .8 });
  M.cork = std({ map: TEX.cork, roughness: 1 });
  M.leaf = std({ color: '#3d6b45', roughness: .7, side: THREE.DoubleSide });
  M.leaf2 = std({ color: '#557d4c', roughness: .7, side: THREE.DoubleSide });
  M.ceramic = std({ color: '#efe9de', roughness: .35 });
  M.terracotta = std({ color: '#b86b45', roughness: .8 });
  M.lightOn = new THREE.MeshStandardMaterial({ color: '#fff6e0', emissive: '#ffe7b8', emissiveIntensity: 0, roughness: .4 });
  M.deck = std({ map: TEX.deck, roughness: .8 });
  M.ground = std({ color: '#b8b2a2', roughness: 1 });
  M.grass = std({ color: '#7e9a64', roughness: 1 });
  M.facade = std({ color: '#ddd5c6', roughness: .9 });
}

/* ---------------- primitives ---------------- */
let G;                                                    // groupe courant
const PLAN = [];                                          // empreintes pour le plan 2D
const SOLIDS = [];                                        // obstacles pour la visite (AABB 2D)
function mesh(geo, mat, x = 0, y = 0, z = 0, parent = G) {
  const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = true; m.receiveShadow = true; parent.add(m); return m;
}
function B(mat, x0, y0, z0, x1, y1, z1, parent = G) {    // boîte entre deux coins
  return mesh(new THREE.BoxGeometry(Math.abs(x1 - x0), Math.abs(y1 - y0), Math.abs(z1 - z0)), mat, (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2, parent);
}
function RB(mat, w, h, d, r, x, y, z, parent = G) { return mesh(new RoundedBoxGeometry(w, h, d, 3, r), mat, x, y, z, parent); }
function cyl(mat, r, h, x, y, z, seg = 24, parent = G, r2 = r) { return mesh(new THREE.CylinderGeometry(r, r2, h, seg), mat, x, y, z, parent); }
function group(x, z, ry = 0, y = 0) { const g = new THREE.Group(); g.position.set(x, y, z); g.rotation.y = ry; G.add(g); return g; }
const fp = (o) => PLAN.push(o);
const solid = (x0, z0, x1, z1) => SOLIDS.push([Math.min(x0, x1), Math.min(z0, z1), Math.max(x0, x1), Math.max(z0, z1)]);

/* ---------------- mobilier ---------------- */
function taskChair(x, z, ry, mat) {
  const g = group(x, z, ry);
  RB(mat, .5, .08, .48, .03, 0, .47, 0, g);
  const back = RB(mat, .46, .52, .06, .03, 0, .8, -.24, g); back.rotation.x = -.12;
  cyl(M.steel, .025, .3, 0, .3, 0, 12, g);
  for (let i = 0; i < 5; i++) { const a = i / 5 * Math.PI * 2; const leg = B(M.steel, -.02, .05, 0, .02, .08, .3, g); leg.rotation.y = a; leg.position.set(Math.sin(a) * .15, .065, Math.cos(a) * .15);
    cyl(M.black, .025, .04, Math.sin(a) * .29, .025, Math.cos(a) * .29, 10, g); }
  [-.24, .24].forEach(s => { B(M.steel, s - .015, .5, -.12, s + .015, .66, -.1, g); RB(M.black, .05, .025, .22, .01, s, .67, -.02, g); });
  fp({ t: 'circle', x, z, r: .3 });
}
function shellChair(x, z, ry, mat) {
  const g = group(x, z, ry);
  RB(mat, .48, .07, .46, .03, 0, .46, 0, g);
  const back = RB(mat, .48, .42, .05, .03, 0, .7, -.22, g); back.rotation.x = -.15;
  [[-.2, -.18], [.2, -.18], [-.2, .18], [.2, .18]].forEach(([a, b]) => { const l = cyl(M.steel, .012, .45, a, .22, b, 8, g); l.rotation.z = a * .2; });
  fp({ t: 'circle', x, z, r: .27 });
}
function stool(x, z) {
  const g = group(x, z); cyl(M.oak, .19, .04, 0, .74, 0, 28, g);
  for (let i = 0; i < 4; i++) { const a = i / 4 * Math.PI * 2 + .78; const l = cyl(M.steel, .012, .74, Math.sin(a) * .14, .37, Math.cos(a) * .14, 8, g); l.rotation.set(Math.cos(a) * .12, 0, -Math.sin(a) * .12); }
  const ring = mesh(new THREE.TorusGeometry(.15, .008, 6, 32), M.steel, 0, .28, 0, g); ring.rotation.x = Math.PI / 2;
  fp({ t: 'circle', x, z, r: .19 });
}
function armchair(x, z, ry, mat) {
  const g = group(x, z, ry);
  RB(mat, .82, .3, .8, .08, 0, .32, 0, g);
  RB(mat, .82, .5, .2, .09, 0, .62, -.31, g);
  RB(mat, .16, .32, .72, .07, -.36, .52, .02, g); RB(mat, .16, .32, .72, .07, .36, .52, .02, g);
  RB(mat, .52, .1, .56, .05, 0, .5, .06, g);
  [[-.33, -.3], [.33, -.3], [-.33, .3], [.33, .3]].forEach(([a, b]) => cyl(M.oak, .022, .17, a, .085, b, 10, g, .016));
  fp({ t: 'rect', x0: x - .42, z0: z - .42, x1: x + .42, z1: z + .42, label: '' });
}
function sofa(x0, z0, len, ry, mat) {                     // canapé le long de son axe x local
  const g = group(x0, z0, ry);
  RB(mat, len, .28, .95, .06, 0, .3, 0, g);
  RB(mat, len, .55, .22, .1, 0, .62, -.37, g);
  RB(mat, .2, .4, .95, .08, -len / 2 + .1, .5, 0, g); RB(mat, .2, .4, .95, .08, len / 2 - .1, .5, 0, g);
  const n = 3, cw = (len - .44) / n;
  for (let i = 0; i < n; i++) { const cx = -len / 2 + .22 + cw * (i + .5);
    RB(mat, cw - .02, .16, .7, .07, cx, .52, .08, g); const p = RB(mat, cw - .06, .42, .16, .08, cx, .72, -.24, g); p.rotation.x = -.18; }
  RB(M.orange, .42, .4, .12, .06, len / 2 - .45, .72, -.17, g).rotation.set(-.2, -.25, .1);
  RB(M.blue, .4, .38, .12, .06, -len / 2 + .45, .72, -.17, g).rotation.set(-.2, .25, -.08);
  [[-len / 2 + .08, -.4], [len / 2 - .08, -.4], [-len / 2 + .08, .4], [len / 2 - .08, .4]].forEach(([a, b]) => B(M.steel, a - .02, 0, b - .02, a + .02, .16, b + .02, g));
}
function monitor(x, z, ry) {
  const g = group(x, z, ry, .76);
  B(M.black, -.3, .12, -.02, .3, .47, 0, g);
  const s = mesh(new THREE.PlaneGeometry(.57, .32), M.screen, 0, .295, .002, g); s.castShadow = false;
  B(M.alu, -.02, 0, -.06, .02, .14, -.03, g); B(M.alu, -.1, 0, -.12, .1, .01, .03, g);
  B(M.alu, -.16, 0, .14, .16, .012, .36, g);              // clavier
}
function laptop(x, z, ry) {
  const g = group(x, z, ry, .76);
  B(M.alu, -.16, 0, -.11, .16, .012, .11, g);
  const lid = new THREE.Group(); lid.position.set(0, .012, -.11); lid.rotation.x = -1.85 + Math.PI / 2; g.add(lid);
  B(M.alu, -.16, 0, 0, .16, .006, .22, lid); const s = mesh(new THREE.PlaneGeometry(.28, .18), M.screen, 0, .007, .11, lid); s.rotation.x = Math.PI / 2; s.rotation.y = Math.PI;
}
function plant(x, z, h = 1.4, potMat = M.ceramic, potR = .22) {
  const g = group(x, z);
  cyl(potMat, potR, potR * 1.6, 0, potR * .8, 0, 28, g, potR * .8);
  cyl(M.black, potR * .92, .02, 0, potR * 1.6, 0, 20, g);
  const leafGeo = new THREE.SphereGeometry(1, 10, 6);
  const n = Math.round(14 + h * 18);
  for (let i = 0; i < n; i++) {
    const k = i / n, a = rnd() * Math.PI * 2, y = potR * 1.6 + .15 + k * (h - .3) + rr(-.05, .05), rad = rr(.08, .28) * (1 - k * .5);
    const l = mesh(leafGeo, rnd() > .5 ? M.leaf : M.leaf2, Math.cos(a) * rad, y, Math.sin(a) * rad, g);
    l.scale.set(.13 * (1 - k * .3), .02, .2 * (1 - k * .3)); l.rotation.set(rr(-.6, .6), a, rr(-.5, .5));
  }
  cyl(M.oakDark, .012, h - .2, 0, potR * 1.6 + (h - .2) / 2, 0, 6, g);
  fp({ t: 'plant', x, z, r: potR + .1 });
}
function books(x0, x1, y, z0, z1, axis = 'x') {           // une rangée de livres
  const cols = ['#efe6d2', C.navy, C.orange, '#c9bfa9', C.blue, '#7a6a55', '#2c2f3a', '#e8dfcc'];
  let p = axis === 'x' ? x0 : z0; const end = axis === 'x' ? x1 : z1;
  while (p < end - .05) {
    const w = rr(.025, .05), h = rr(.2, .3), col = cols[Math.floor(rnd() * cols.length)];
    if (rnd() < .12) { p += rr(.08, .2); continue; }
    const m = new THREE.MeshStandardMaterial({ color: col, roughness: .8 });
    if (axis === 'x') B(m, p, y, z0, p + w, y + h, z1); else B(m, x0, y, p, x1, y + h, p + w);
    p += w + .002;
  }
}
function linearPendant(x0, x1, z, y = 2.25) {
  const LEN = x1 - x0;
  const body = B(M.steel, x0, y, z - .04, x1, y + .06, z + .04);
  const strip = B(M.lightOn, x0 + .02, y - .006, z - .025, x1 - .02, y, z + .025); strip.castShadow = false;
  [x0 + .15, x1 - .15].forEach(cx => { const c = cyl(M.steel, .003, 3 - y - .06, cx, (3 + y + .06) / 2, z, 4); c.castShadow = false; });
  LIGHTS.push({ x: (x0 + x1) / 2, y: y - .1, z, i: 1.2 * LEN, d: 6 });
  return body;
}
function pendantZ(x, z0, z1, y = 2.25) {                  // même suspension, orientée nord-sud
  B(M.steel, x - .04, y, z0, x + .04, y + .06, z1);
  const s = B(M.lightOn, x - .025, y - .006, z0 + .02, x + .025, y, z1 - .02); s.castShadow = false;
  [z0 + .15, z1 - .15].forEach(cz => { const c = cyl(M.steel, .003, 3 - y - .06, x, (3 + y + .06) / 2, cz, 4); c.castShadow = false; });
  LIGHTS.push({ x, y: y - .1, z: (z0 + z1) / 2, i: 1.2 * (z1 - z0), d: 6 });
}
function globe(x, z, y, r = .2) {
  const c = cyl(M.steel, .003, 3 - y - r, x, (3 + y + r) / 2, z, 4); c.castShadow = false;
  const s = mesh(new THREE.SphereGeometry(r, 28, 20), M.lightOn, x, y, z); s.castShadow = false;
  LIGHTS.push({ x, y: y - .05, z, i: 1.4, d: 5 });
}
function cone(x, z, y) {
  const c = cyl(M.steel, .003, 3 - y - .2, x, (3 + y + .2) / 2, z, 4); c.castShadow = false;
  const sh = mesh(new THREE.ConeGeometry(.17, .22, 32, 1, true), new THREE.MeshStandardMaterial({ color: C.orange, roughness: .35, metalness: .4, side: THREE.DoubleSide }), x, y + .08, z);
  const d = mesh(new THREE.CircleGeometry(.15, 24), M.lightOn, x, y - .02, z); d.rotation.x = Math.PI / 2; d.castShadow = false;
  LIGHTS.push({ x, y: y - .1, z, i: 1.1, d: 4 });
}
const LIGHTS = [];

/* ---------------- architecture ---------------- */
const CUT = [];                                           // éléments coupés en vue isométrique
function architecture() {
  const { W, D, H } = LAYOUT;
  // dalle + sol béton ciré
  const floor = mesh(new THREE.PlaneGeometry(W, D), M.concrete, W / 2, 0, D / 2); floor.rotation.x = -Math.PI / 2; floor.castShadow = false;
  B(M.facade, -.25, -.3, -.25, W + .25, -.001, D + .25).castShadow = false;
  // plafond (masquable)
  const ceil = B(M.ceiling, -.2, H, -.2, W + .2, H + .25, D + .2); ceil.name = 'ceiling'; CEIL.push(ceil);
  // poutres béton apparentes
  [3.3, 6.7].forEach(x => { const b = B(M.ceiling, x - .15, H - .35, 0, x + .15, H, D); CEIL.push(b); });

  // mur nord (rue) avec porte d'entrée
  B(M.plaster, -.2, 0, -.2, .6, H, 0); B(M.plaster, 1.6, 0, -.2, W + .2, H, 0); B(M.plaster, .6, 2.4, -.2, 1.6, H, 0);
  solid(-.2, -.2, .6, 0); solid(1.6, -.2, W + .2, 0);
  // porte vitrée cadre acier
  frameRect(.6, 0, -.1, 1.6, 2.4, -.1, 'z');
  const door = B(M.glass, .62, .02, -.11, 1.58, 2.38, -.09); door.castShadow = false;
  B(M.brass, 1.42, .9, -.03, 1.45, 1.6, -.0);              // poignée bâton laiton
  // mur ouest (mitoyen) : coupé en iso
  const west = new THREE.Group(); G.add(west); CUT.push(west);
  B(M.plaster, -.2, 0, 0, 0, H, D, west); solid(-.2, 0, 0, D);
  // mur est avec deux grandes baies
  B(M.plaster, W, 0, -.2, W + .2, H, .5); B(M.plaster, W, 0, 3.3, W + .2, H, 5.0); B(M.plaster, W, 0, 7.5, W + .2, H, D + .2);
  B(M.plaster, W, 2.7, .5, W + .2, H, 3.3); B(M.plaster, W, 2.7, 5.0, W + .2, H, 7.5);
  solid(W, -.2, W + .2, D + .2);
  glazing(W + .1, .5, 3.3, 'x', 3); glazing(W + .1, 5.0, 7.5, 'x', 3);
  // grande façade sud vitrée (coupée en iso)
  const south = new THREE.Group(); G.add(south); CUT.push(south);
  const prev = G; G = south;
  B(M.plaster, -.2, 2.8, D, W + .2, H, D + .2);
  glazingSouth();
  G = prev; solid(-.2, D, W + .2, D + .2);

  // cloisons vitrées réunion / direction
  partitionX(6.6, 0, 3.8, [2.85, 3.75]);
  partitionX(6.6, 4.8, 8, [4.9, 5.8]);
  B(M.plaster, 6.6, 0, 3.8, W, H, 3.9); solid(6.6, 3.8, W, 3.9);
  B(M.plaster, 6.6, 0, 4.7, W, H, 4.8); solid(6.6, 4.7, W, 4.8);
  fp({ t: 'wall', x0: 6.6, z0: 3.8, x1: W, z1: 3.9 }); fp({ t: 'wall', x0: 6.6, z0: 4.7, x1: W, z1: 4.8 });
}
const CEIL = [];
function frameRect(x0, y0, z, x1, y1, _z, axis) {          // cadre acier fin autour d'une ouverture
  const t = .04;
  if (axis === 'z') { B(M.steel, x0, y0, z - .03, x0 + t, y1, z + .03); B(M.steel, x1 - t, y0, z - .03, x1, y1, z + .03); B(M.steel, x0, y1 - t, z - .03, x1, y1, z + .03); }
}
function glazing(x, z0, z1, _a, h) {                       // baie est : vitrage + meneaux
  const g = B(M.glass, x - .01, 0, z0, x + .01, 2.7, z1); g.castShadow = false; g.receiveShadow = false;
  const n = Math.max(1, Math.round((z1 - z0) / 1.3));
  for (let i = 0; i <= n; i++) { const z = z0 + (z1 - z0) * i / n; B(M.steel, x - .03, 0, z - .025, x + .03, 2.7, z + .025); }
  B(M.steel, x - .03, 0, z0, x + .03, .05, z1); B(M.steel, x - .03, 2.65, z0, x + .03, 2.7, z1);
}
function glazingSouth() {
  const { W, D } = LAYOUT, z = D + .08;
  const g = B(M.glass, 0, 0, z - .01, W, 2.8, z + .01); g.castShadow = false; g.receiveShadow = false;
  const n = 6;
  for (let i = 0; i <= n; i++) { const x = W * i / n; B(M.steel, x - .03, 0, z - .04, x + .03, 2.8, z + .04); }
  B(M.steel, 0, 2.2, z - .03, W, 2.24, z + .03);           // imposte
  B(M.steel, 0, 0, z - .04, W, .05, z + .04);
}
function partitionX(x, z0, z1, door) {                     // cloison vitrée toute hauteur, porte coulissante
  const H = LAYOUT.H;
  const segs = [[z0, door[0]], [door[1], z1]];
  segs.forEach(([a, b]) => {
    const g = B(M.glass, x, .02, a, x + .02, H, b); g.castShadow = false; g.receiveShadow = false;
    const n = Math.max(1, Math.round((b - a) / 1.1));
    for (let i = 0; i <= n; i++) { const z = a + (b - a) * i / n; B(M.steel, x - .015, 0, z - .015, x + .035, H, z + .015); }
    solid(x - .03, a, x + .05, b);
    fp({ t: 'glass', x0: x, z0: a, x1: x + .02, z1: b });
  });
  B(M.steel, x - .015, 0, z0, x + .035, .04, z1); B(M.steel, x - .015, 2.35, door[0], x + .035, 2.42, door[1]);
  // porte coulissante vitrée, en position ouverte (glissée devant la partie fixe)
  const g = B(M.glass, x - .07, .03, door[0] - (door[1] - door[0]) + .05, x - .05, 2.34, door[0] + .05); g.castShadow = false;
  B(M.steel, x - .08, 1.0, door[0] + .02, x - .04, 1.3, door[0] + .04);
  fp({ t: 'door', x, z0: door[0], z1: door[1] });
  // bande de vitrophanie (sécurité) aux couleurs de la marque
  const band = B(new THREE.MeshStandardMaterial({ color: C.orange, roughness: .5, transparent: true, opacity: .85 }), x + .021, 1.1, z0 + .02, x + .023, 1.16, door[0] - .02); band.castShadow = false;
}

/* ---------------- les pièces ---------------- */
async function entreeSalon() {
  // la « maison dans la maison » : portique en chêne au profil du logo
  const outer = [[0, 0], [0, 2.15], [1.6, 2.85], [3.2, 2.15], [3.2, 0]];
  const T = .12;
  const shape = new THREE.Shape(); outer.forEach(([x, y], i) => i ? shape.lineTo(x, y) : shape.moveTo(x, y)); shape.closePath();
  const hole = new THREE.Path(); [[T, 0], [T, 2.15 - .04], [1.6, 2.85 - T - .06], [3.2 - T, 2.15 - .04], [3.2 - T, 0]].forEach(([x, y], i) => i ? hole.lineTo(x, y) : hole.moveTo(x, y)); hole.closePath();
  shape.holes.push(hole);
  const frameGeo = new THREE.ExtrudeGeometry(shape, { depth: T, bevelEnabled: false });
  [1.85, 4.25].forEach(z => mesh(frameGeo, M.oak, .1, 0, z));
  // liteaux de toiture : ombres rayées sur le salon
  const slope = Math.hypot(1.6, .7), ang = Math.atan2(.7, 1.6);
  for (let z = 1.97; z < 4.25; z += .16) {
    [-1, 1].forEach(s => { const b = mesh(new THREE.BoxGeometry(slope, .05, .045), M.oak, .1 + 1.6 - s * .8, 2.15 + .35 + .03, z + .02);
      b.rotation.z = s * ang; });
  }
  fp({ t: 'house', x0: .1, z0: 1.85, x1: 3.3, z1: 4.37 });

  // sofa contre le mur ouest, face à l'est
  sofa(.52, 3.1, 2.1, Math.PI / 2, M.boucle); fp({ t: 'rect', x0: .05, z0: 2.05, x1: 1.0, z1: 4.15, label: 'Canapé' });
  // tapis vagues
  const rug = mesh(new THREE.PlaneGeometry(2.3, 2.0), M.rug, 2.05, .006, 3.1); rug.rotation.x = -Math.PI / 2; rug.rotation.z = Math.PI / 2; rug.castShadow = false;
  fp({ t: 'rug', x0: 1.05, z0: 1.95, x1: 3.05, z1: 4.25 });
  // table basse travertin
  cyl(M.travertine, .42, .06, 1.8, .36, 3.1, 48); cyl(M.travertine, .2, .33, 1.8, .165, 3.1, 32);
  fp({ t: 'circle', x: 1.8, z: 3.1, r: .42 });
  cyl(M.ceramic, .09, .14, 1.68, .46, 3.0, 24); B(M.navy, 1.85, .39, 3.15, 2.1, .43, 3.4);            // vase + livres
  B(new THREE.MeshStandardMaterial({ color: C.orange, roughness: .8 }), 1.88, .43, 3.18, 2.07, .45, 3.36);
  // fauteuils orange face au canapé
  armchair(2.82, 2.55, -Math.PI / 2 - .3, M.orange); armchair(2.82, 3.7, -Math.PI / 2 + .3, M.orange);
  // lampadaire arc
  const lamp = group(.35, 4.15);
  cyl(M.steel, .16, .03, 0, .015, 0, 32, lamp); cyl(M.steel, .012, 1.65, 0, .84, 0, 8, lamp);
  const arm = cyl(M.steel, .01, .7, .28, 1.75, -.0, 8, lamp); arm.rotation.z = -1.1;
  mesh(new THREE.SphereGeometry(.16, 24, 16, 0, Math.PI * 2, 0, Math.PI / 2), M.brass, .58, 1.72, 0, lamp).rotation.x = Math.PI;
  LIGHTS.push({ x: .9, y: 1.6, z: 4.15, i: 1, d: 4 });
  globe(1.7, 3.1, 2.05, .24);
  // affiche soleil rayé au-dessus du canapé
  B(M.oak, .0, 1.15, 2.45, .04, 2.05, 3.75); const p = mesh(new THREE.PlaneGeometry(1.24, .84), M.poster, .045, 1.6, 3.1); p.rotation.y = Math.PI / 2;
  plant(.35, 1.65, 1.7, M.terracotta, .24);
  solid(.05, 2.05, 1.0, 4.15); solid(2.4, 2.1, 3.25, 4.1);

  // entrée : vestiaire intégré + banc + logo
  B(M.oak, 1.75, 0, 0, 3.35, 2.6, .45);                   // armoire vestiaire toute hauteur
  for (let x = 1.75; x <= 3.36; x += .4) B(M.steel, x - .004, .05, .451, x + .004, 2.55, .455);
  [2.15, 2.95].forEach(x => B(M.brass, x - .01, 1.0, .455, x + .01, 1.3, .48));
  B(M.oak, .0, .0, .9, .42, .45, 1.65); RB(M.navyFab, .4, .06, .72, .02, .21, .48, 1.27);    // banc d'accueil contre le mur ouest
  fp({ t: 'rect', x0: 1.75, z0: 0, x1: 3.35, z1: .45, label: 'Vestiaire' }); fp({ t: 'rect', x0: 0, z0: .9, x1: .42, z1: 1.65, label: '' });
  solid(1.75, 0, 3.35, .45); solid(0, .9, .42, 1.65);
  // logo Casa Mar en relief laiton sur le mur ouest, vu dès l'entrée
  try {
    const txt = await (await fetch('assets/logo-h.svg')).text();
    const data = new SVGLoader().parse(txt);
    const shapes = data.paths.flatMap(p => SVGLoader.createShapes(p));
    const geo = new THREE.ExtrudeGeometry(shapes, { depth: 30, bevelEnabled: false });
    geo.computeBoundingBox(); const bb = geo.boundingBox, s = 1.15 / (bb.max.x - bb.min.x);
    geo.translate(-(bb.min.x + bb.max.x) / 2, -(bb.min.y + bb.max.y) / 2, 0);
    const logo = new THREE.Mesh(geo, M.brass); logo.scale.set(s, -s, s); logo.rotation.y = Math.PI / 2;
    logo.position.set(.02, 1.75, .75); logo.castShadow = true; G.add(logo);
  } catch (e) { /* logo facultatif */ }
  // lumière de mur rasante sous le logo
  const strip = B(M.lightOn, .02, 2.35, .2, .05, 2.37, 1.6); strip.castShadow = false;
}

function kitchenette() {
  const z1 = .62;
  B(M.navy, 3.45, .1, 0, 5.55, .88, z1);                  // meubles bas laque marine
  B(M.black, 3.45, 0, .05, 5.55, .1, z1 - .05);
  for (let x = 3.45 + .6; x < 5.5; x += .6) B(M.steel, x - .003, .12, z1, x + .003, .86, z1 + .004);
  B(M.counter, 3.42, .88, 0, 5.58, .92, z1 + .02);        // plan béton
  B(M.black, 4.25, .86, .12, 4.75, .921, .48);            // évier
  const tap = cyl(M.brass, .012, .32, 4.5, 1.07, .08, 12); const spout = cyl(M.brass, .01, .18, 4.5, 1.22, .17, 12); spout.rotation.x = Math.PI / 2;
  // machine à café
  B(M.alu, 3.62, .92, .08, 3.98, 1.3, .44); B(M.black, 3.66, 1.0, .44, 3.94, 1.2, .445); cyl(M.black, .04, .03, 3.8, 1.04, .46, 16).rotation.x = Math.PI / 2;
  [3.7, 3.9].forEach(x => cyl(M.ceramic, .04, .09, x, .965, .3, 16));
  // crédence zellige
  B(M.tiles, 3.42, .92, 0, 5.58, 1.55, .015);
  // étagères chêne + vaisselle
  [1.65, 2.05].forEach(y => { B(M.oak, 3.5, y, 0, 5.5, y + .035, .28); });
  for (let i = 0; i < 9; i++) cyl(i % 3 ? M.ceramic : new THREE.MeshStandardMaterial({ color: i % 2 ? C.blue : C.orange, roughness: .4 }), .045, .1, 3.62 + i * .2, 1.735, .14, 16);
  for (let i = 0; i < 6; i++) B(M.ceramic, 3.62 + i * .28, 2.085, .05, 3.62 + i * .28 + .22, 2.12, .25);
  plant(5.2, .18, .5, M.terracotta, .1);
  // colonne : réfrigérateur + four, chêne
  B(M.oak, 5.6, 0, 0, 6.55, 2.6, .65);
  B(M.steel, 5.6, 1.3, .65, 6.55, 1.304, .655); B(M.brass, 5.66, .9, .655, 5.68, 1.2, .68); B(M.brass, 5.66, 1.4, .655, 5.68, 1.7, .68);
  fp({ t: 'rect', x0: 3.42, z0: 0, x1: 6.55, z1: .65, label: 'Plan + colonne' });
  solid(3.42, 0, 6.55, .65);
  // comptoir haut + tabourets
  B(M.oak, 3.9, 1.03, 1.55, 5.9, 1.08, 2.25); B(M.steel, 4.05, 0, 1.85, 4.12, 1.03, 1.95); B(M.steel, 5.68, 0, 1.85, 5.75, 1.03, 1.95);
  B(M.steel, 4.05, 0, 1.6, 4.12, .04, 2.2); B(M.steel, 5.68, 0, 1.6, 5.75, .04, 2.2);
  fp({ t: 'rect', x0: 3.9, z0: 1.55, x1: 5.9, z1: 2.25, label: 'Comptoir café' }); solid(3.9, 1.55, 5.9, 2.25);
  [4.3, 4.9, 5.5].forEach(x => stool(x, 2.6));
  cone(4.4, 1.9, 1.95); cone(5.4, 1.9, 1.95);
  cyl(M.ceramic, .045, .1, 4.6, 1.13, 1.8, 16); cyl(new THREE.MeshStandardMaterial({ color: C.blue, roughness: .4 }), .045, .1, 5.1, 1.13, 1.95, 16);
}

function openSpace() {
  // mur de rangement intégré (ouest), niches ouvertes
  B(M.oak, 0, 0, 4.65, .45, 2.6, 7.95);
  for (let z = 4.65; z < 7.9; z += .65) {
    for (let y = .45; y < 2.5; y += .52) {
      const open = ((z * 7 + y * 3) % 1) > .45;
      if (open) { B(M.oakDark, .2, y, z + .03, .451, y + .46, z + .62); books(.22, .44, y + .01, z + .06, z + .5, 'z'); }
      else { B(M.steel, .451, y + .23, z + .1, .456, y + .25, z + .3); }
    }
  }
  B(M.oakDark, .0, 0, 4.65, .46, .08, 7.95);
  fp({ t: 'rect', x0: 0, z0: 4.65, x1: .45, z1: 7.95, label: 'Rangements' }); solid(0, 4.65, .45, 7.95);
  // grande table commune chêne (6 postes) perpendiculaire à la façade
  const x0 = 2.25, x1 = 3.85, z0 = 5.0, z1 = 7.55;
  B(M.oak, x0, .72, z0, x1, .76, z1);
  [[z0 + .15], [z1 - .15]].forEach(([z]) => { B(M.steel, x0 + .1, 0, z - .025, x0 + .14, .72, z + .025); B(M.steel, x1 - .14, 0, z - .025, x1 - .1, .72, z + .025);
    B(M.steel, x0 + .1, .68, z - .025, x1 - .1, .72, z + .025); });
  B(M.steel, (x0 + x1) / 2 - .01, .76, z0 + .1, (x0 + x1) / 2 + .01, 1.05, z1 - .1);           // séparation feutre
  B(M.blue, (x0 + x1) / 2 - .012, .79, z0 + .2, (x0 + x1) / 2 + .012, 1.08, z1 - .2);
  fp({ t: 'rect', x0, z0, x1, z1, label: 'Table 6 postes' }); solid(x0, z0, x1, z1);
  const zs = [5.42, 6.27, 7.12];
  const mats = [M.orange, M.navyFab, M.blue];
  zs.forEach((z, i) => {
    taskChair(1.72, z, Math.PI / 2 + rr(-.25, .25), mats[i]); taskChair(4.38, z, -Math.PI / 2 + rr(-.25, .25), mats[(i + 1) % 3]);
    if (i !== 1) monitor(x0 + .35, z, Math.PI / 2); else laptop(x0 + .35, z, Math.PI / 2);
    if (i !== 2) monitor(x1 - .35, z, -Math.PI / 2); else laptop(x1 - .35, z, -Math.PI / 2);
    cyl(M.ceramic, .04, .09, x0 + .6, .805, z + .25, 16);
  });
  B(new THREE.MeshStandardMaterial({ color: '#efe6d2', roughness: .9 }), 3.2, .76, 6.5, 3.45, .78, 6.85);   // carnet
  pendantZ(3.05, 5.15, 7.4, 2.15);
  // bafflles acoustiques bois au plafond
  for (let x = .9; x < 6.4; x += .38) { const b = B(M.oak, x - .02, 2.45, 4.9, x + .02, 2.62, 7.8); CEIL.push(b); }
  // mur d'idées mobile + imprimante + plantes
  const board = group(5.55, 5.5, -.35);
  B(M.cork, -.75, .45, -.02, .75, 1.95, .02, board); B(M.steel, -.78, 0, -.03, -.74, 2.0, .03, board); B(M.steel, .74, 0, -.03, .78, 2.0, .03, board);
  const pins = [C.orange, C.blue, '#efe6d2', C.navy, '#efe6d2', C.orange];
  for (let i = 0; i < 9; i++) { const m = new THREE.MeshStandardMaterial({ color: pins[i % pins.length], roughness: .9 }); const w = rr(.2, .34);
    const card = B(m, -.65 + (i % 3) * .45, .6 + Math.floor(i / 3) * .42, .021, -.65 + (i % 3) * .45 + w, .6 + Math.floor(i / 3) * .42 + w * 1.2, .024, board); card.rotation.z = rr(-.06, .06); }
  fp({ t: 'rect', x0: 4.85, z0: 5.2, x1: 6.25, z1: 5.8, label: 'Mur d\'idées' }); solid(4.85, 5.2, 6.25, 5.8);
  plant(6.1, 7.55, 1.9, M.ceramic, .27); plant(1.0, 7.6, 1.2, M.terracotta, .2); plant(5.2, 7.6, .9, M.navy, .18);
  // banquette basse le long de la vitrine (assise informelle)
  B(M.oak, 4.6, 0, 7.45, 5.9, .42, 7.9); RB(M.blue, 1.26, .08, .42, .03, 5.25, .46, 7.67);
  fp({ t: 'rect', x0: 4.6, z0: 7.45, x1: 5.9, z1: 7.9, label: 'Banquette' }); solid(4.6, 7.45, 5.9, 7.9);
}

function reunion() {
  // mur de liteaux chêne (acoustique) côté sud
  B(M.navy, 6.65, 0, 3.75, 10, 3, 3.8);
  for (let x = 6.7; x < 9.98; x += .07) B(M.oak, x, 0, 3.72, x + .04, 2.9, 3.75);
  // écran + crédence basse côté nord
  B(M.oak, 6.8, 0, 0, 9.8, .62, .45);
  const scr = mesh(new THREE.PlaneGeometry(1.6, .92), M.screen, 8.3, 1.45, .03); scr.castShadow = false; B(M.black, 7.48, .97, 0, 9.12, 1.93, .025);
  fp({ t: 'rect', x0: 6.8, z0: 0, x1: 9.8, z1: .45, label: 'Crédence + écran' }); solid(6.8, 0, 9.8, .45);
  books(7.0, 7.9, .62, .08, .32, 'x'); plant(9.5, .25, .55, M.ceramic, .11);
  // grande table chêne 8 personnes
  const x0 = 7.75, x1 = 8.85, z0 = .85, z1 = 3.3;
  B(M.oak, x0, .72, z0, x1, .76, z1);
  [z0 + .45, z1 - .45].forEach(z => { B(M.steel, 8.25, 0, z - .03, 8.35, .72, z + .03); B(M.steel, x0 + .15, 0, z - .03, x1 - .15, .04, z + .03); });
  fp({ t: 'rect', x0, z0, x1, z1, label: 'Table 8 pers.' }); solid(x0, z0, x1, z1);
  [1.25, 2.05, 2.85].forEach(z => { shellChair(7.42, z, Math.PI / 2, M.blue); shellChair(9.18, z, -Math.PI / 2, M.navyFab); });
  shellChair(8.3, .55, 0, M.orange); shellChair(8.3, 3.55, Math.PI, M.orange);
  // bouquet, carafe, carnets
  cyl(M.glass, .05, .24, 8.3, .88, 2.05, 24); plant(8.3, 1.55, .38, M.ceramic, .07);
  // vitrophanie soleil sur la cloison
  const film = mesh(new THREE.PlaneGeometry(1.5, 1.5), M.film, 6.63, 1.35, 1.25); film.rotation.y = Math.PI / 2; film.castShadow = false;
  pendantZ(8.3, 1.05, 3.1, 2.1);
}

function alcove() {
  for (let x = 6.75; x < 9.9; x += .45) { B(M.oak, x, 0, 3.9, x + .44, 2.2, 4.25); B(M.brass, x + .36, 1.0, 4.25, x + .38, 1.25, 4.27); }
  B(M.white, 9.2, .9, 3.92, 9.85, 1.25, 4.24);           // imprimante posée dans une niche
  fp({ t: 'rect', x0: 6.75, z0: 3.9, x1: 9.9, z1: 4.25, label: 'Casiers' }); solid(6.75, 3.9, 9.9, 4.25);
}

function direction() {
  // bureau chêne + retour, face à la cloison vitrée
  B(M.oak, 8.45, .72, 5.6, 9.3, .76, 7.35);
  B(M.oak, 8.47, 0, 5.62, 8.52, .72, 7.33); B(M.oak, 9.23, 0, 5.62, 9.28, .72, 7.33);
  B(M.navy, 8.6, .35, 6.9, 9.25, .72, 7.33);              // caisson
  fp({ t: 'rect', x0: 8.45, z0: 5.6, x1: 9.3, z1: 7.35, label: 'Bureau' }); solid(8.45, 5.6, 9.3, 7.35);
  monitor(8.75, 6.2, -Math.PI / 2); laptop(8.85, 6.95, -Math.PI / 2 + .2);
  taskChair(9.62, 6.45, -Math.PI / 2, M.navyFab);
  // lampe de bureau laiton
  cyl(M.brass, .07, .02, 8.65, .77, 5.8, 20); const st = cyl(M.brass, .008, .42, 8.65, .98, 5.8, 8); mesh(new THREE.ConeGeometry(.09, .12, 24, 1, true), M.brass, 8.7, 1.2, 5.8).rotation.z = .5;
  // coin lecture : fauteuil + guéridon
  armchair(7.35, 7.3, Math.PI * .85, M.orange); cyl(M.travertine, .22, .04, 7.95, .52, 7.55, 32); cyl(M.travertine, .1, .5, 7.95, .25, 7.55, 24);
  // crédence basse + affiche vagues sur le mur nord
  B(M.oak, 6.8, 0, 4.8, 9.85, .7, 5.25); books(7.0, 8.4, .7, 4.86, 5.15, 'x');
  B(M.oak, 7.6, 1.15, 4.8, 8.92, 2.25, 4.83); const wp = mesh(new THREE.PlaneGeometry(1.24, 1.02), M.wavePrint, 8.26, 1.7, 4.835); wp.castShadow = false;
  fp({ t: 'rect', x0: 6.8, z0: 4.8, x1: 9.85, z1: 5.25, label: 'Crédence' }); solid(6.8, 4.8, 9.85, 5.25);
  plant(9.65, 5.55, 1.5, M.terracotta, .22);
  globe(8.0, 6.3, 2.2, .22);
}

function outside() {
  const { W, D } = LAYOUT;
  const deck = mesh(new THREE.PlaneGeometry(W + 4, 3.2), M.deck, W / 2, -.02, D + 1.8); deck.rotation.x = -Math.PI / 2; deck.castShadow = false;
  const gr = mesh(new THREE.PlaneGeometry(200, 200), M.grass, W / 2, -.06, D + 60); gr.rotation.x = -Math.PI / 2; gr.castShadow = false;
  const street = mesh(new THREE.PlaneGeometry(200, 30), M.ground, W / 2, -.05, -15); street.rotation.x = -Math.PI / 2; street.castShadow = false;
  // jardinières + oliviers
  const prevG = G; G = new THREE.Group(); G.name = 'garden'; prevG.add(G);
  [[1.2, 9.8], [5, 9.9], [8.8, 9.8]].forEach(([x, z]) => {
    B(M.facade, x - .7, -.02, z - .3, x + .7, .5, z + .3);
    const t = group(x, z); cyl(M.oakDark, .06, 1.4, 0, 1.1, 0, 10, t);
    for (let i = 0; i < 9; i++) { const s = mesh(new THREE.IcosahedronGeometry(rr(.35, .55), 1), rnd() > .5 ? M.leaf : M.leaf2, rr(-.5, .5), rr(1.7, 2.5), rr(-.4, .4), t); s.scale.y = .7; }
  });
  // haie + arbres au fond du jardin
  B(M.leaf, -8, 0, 15, W + 8, 1.6, 16.2);
  for (let i = 0; i < 9; i++) { const t = group(-6 + i * 2.8 + rr(-.5, .5), 18 + rr(0, 3)); cyl(M.oakDark, .12, 2.5, 0, 1.25, 0, 10, t);
    for (let k = 0; k < 6; k++) mesh(new THREE.IcosahedronGeometry(rr(1, 1.6), 1), rnd() > .5 ? M.leaf : M.leaf2, rr(-1, 1), rr(3, 4.6), rr(-1, 1), t); }
  G = prevG;
  // immeubles voisins côté rue
  [[-14, -10, 6], [-4, -12, 9], [16, -9, 7], [24, 4, 12]].forEach(([x, z, h]) => B(M.facade, x - 4, 0, z - 3, x + 4, h, z + 3));
  // façade extérieure du bâtiment au-dessus (étage)
  B(M.facade, -.25, 3.25, -.25, W + .25, 6.5, D + .25).name = 'upper';
}

/* =====================================================================================
   SCÈNE, LUMIÈRES, CAMÉRAS
   ===================================================================================== */
export async function createOffice(canvas, { quality = 'live', width, height } = {}) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(quality === 'still' ? 1 : Math.min(2, devicePixelRatio || 1));
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.0;
  const W0 = width || canvas.clientWidth, H0 = height || canvas.clientHeight;
  renderer.setSize(W0, H0, !width);
  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(renderer), .04).texture;

  makeTextures(); makeMaterials();
  G = new THREE.Group(); scene.add(G);
  seed = 21;
  architecture(); await entreeSalon(); kitchenette(); openSpace(); reunion(); alcove(); direction(); outside();
  const upper = G.getObjectByName('upper'), garden = G.getObjectByName('garden');

  // lumière du jour
  const hemi = new THREE.HemisphereLight('#dbe8f2', '#cdbfa9', .32); scene.add(hemi);
  const sun = new THREE.DirectionalLight('#fff1dc', 3.2); sun.castShadow = true;
  sun.shadow.mapSize.set(quality === 'still' ? 4096 : 2048, quality === 'still' ? 4096 : 2048);
  Object.assign(sun.shadow.camera, { left: -11, right: 11, top: 11, bottom: -11, near: 1, far: 80 });
  sun.shadow.bias = -.0004; sun.shadow.normalBias = .02; sun.shadow.radius = 3; sun.shadow.camera.updateProjectionMatrix();
  sun.target.position.set(5, 0, 4); scene.add(sun, sun.target);
  // remplissage doux depuis les baies (lumière qui rebondit)
  const bounce = new THREE.DirectionalLight('#fff7ea', .32); bounce.position.set(5, 3, 30); bounce.target.position.set(5, 1, 0); scene.add(bounce, bounce.target);
  // éclairage artificiel
  const pts = LIGHTS.map(l => { const p = new THREE.PointLight('#ffd9a0', 0, l.d, 1.6); p.position.set(l.x, l.y, l.z); p.userData.k = l.i; scene.add(p); return p; });
  const cove = new THREE.PointLight('#ffd49a', 0, 5, 1.6); cove.position.set(.4, 2.3, .9); cove.userData.k = 1.2; scene.add(cove); pts.push(cove);

  // ciel
  const skyC = document.createElement('canvas'); skyC.width = 2; skyC.height = 256; const skyX = skyC.getContext('2d');
  const skyT = new THREE.CanvasTexture(skyC); skyT.colorSpace = THREE.SRGBColorSpace; scene.background = skyT;
  scene.fog = new THREE.Fog('#dfe6ea', 30, 90);

  function setTime(h) {                                   // 8 h → 21 h
    const k = (h - 7) / (20.5 - 7);                       // course du soleil
    const az = THREE.MathUtils.lerp(1.4, -1.5, k);        // azimut : 0 = plein sud ; + = est (matin), - = ouest (soir)
    const el = Math.max(.03, Math.sin(Math.PI * THREE.MathUtils.clamp(k, 0, 1)) * .9);
    const R = 30;
    sun.position.set(5 + Math.sin(az) * Math.cos(el) * R, Math.sin(el) * R, 4 + Math.cos(az) * Math.cos(el) * R);
    const dusk = THREE.MathUtils.clamp((h - 17.5) / 3, 0, 1);
    const night = THREE.MathUtils.clamp((h - 19.5) / 1.3, 0, 1);
    sun.intensity = 4.2 * (1 - night) * (1 - dusk * .4);
    sun.color.set('#fff1dc').lerp(new THREE.Color('#ffb46b'), dusk);
    hemi.intensity = .32 * (1 - night * .8);
    bounce.intensity = .32 * (1 - night);
    const lights = THREE.MathUtils.clamp((h - 17) / 2, 0, 1);
    M.lightOn.emissiveIntensity = .2 + lights * 2.3;
    pts.forEach(p => p.intensity = p.userData.k * lights * 2.2);
    M.screen.emissiveIntensity = .5 + lights * .5;
    renderer.toneMappingExposure = 1.15 - night * .2;
    scene.traverse(m => { if (m.isMesh && m.material && m.material.envMapIntensity !== undefined) {
      if (m.material.userData.env0 === undefined) m.material.userData.env0 = m.material.envMapIntensity;
      m.material.envMapIntensity = m.material.userData.env0 * (1 - night * .88); } });
    const top = new THREE.Color('#8fb7d8').lerp(new THREE.Color('#e9a46a'), dusk * .6).lerp(new THREE.Color('#0B0F1E'), night);
    const hor = new THREE.Color('#f1ede4').lerp(new THREE.Color('#f3c48b'), dusk).lerp(new THREE.Color('#2a2440'), night);
    const g = skyX.createLinearGradient(0, 0, 0, 256); g.addColorStop(0, '#' + top.getHexString()); g.addColorStop(1, '#' + hor.getHexString());
    skyX.fillStyle = g; skyX.fillRect(0, 0, 2, 256); skyT.needsUpdate = true;
    scene.fog.color.copy(hor);
  }
  setTime(15.5);

  // caméras
  const persp = new THREE.PerspectiveCamera(58, W0 / H0, .05, 400);
  const ortho = new THREE.OrthographicCamera(-1, 1, 1, -1, .1, 400);
  let camera = persp;
  const controls = new OrbitControls(persp, canvas); controls.enableDamping = true; controls.target.set(5, .8, 4);
  controls.maxPolarAngle = Math.PI / 2 - .02;
  const VIEWS = {
    iso: { iso: true, pos: [-8.5, 14, 18.5], target: [5, .3, 4.2], zoom: 1 },
    entree: { pos: [1.05, 1.62, .35], target: [3.4, 1.15, 5.2], fov: 64 },
    open: { pos: [.85, 1.5, 4.75], target: [5.2, 1.0, 7.0], fov: 64 },
    reunion: { pos: [9.75, 1.65, .35], target: [7.3, .8, 3.0], fov: 66 },
    detente: { pos: [6.3, 1.6, 4.3], target: [2.2, 1.05, 1.4], fov: 66 },
    direction: { pos: [6.95, 1.6, 5.1], target: [9.4, .95, 7.2], fov: 64 },
  };
  function fitOrtho(aspect) {
    const s = 5.4; ortho.left = -s * aspect; ortho.right = s * aspect; ortho.top = s; ortho.bottom = -s; ortho.updateProjectionMatrix();
  }
  function setCut(on) { CUT.forEach(g => { g.scale.y = on ? .4 : 1; }); CEIL.forEach(c => c.visible = !on); if (upper) upper.visible = !on; if (garden) garden.visible = !on; }
  function setView(name) {
    const v = VIEWS[name]; if (!v) return;
    const aspect = renderer.domElement.width / renderer.domElement.height;
    if (v.iso) { camera = ortho; fitOrtho(aspect); setCut(true); }
    else { camera = persp; persp.fov = v.fov || 58; persp.aspect = aspect; persp.updateProjectionMatrix(); setCut(false); }
    camera.position.set(...v.pos); controls.object = camera; controls.target.set(...v.target); camera.lookAt(...v.target); controls.update();
    passes.render.camera = camera; if (passes.ao) passes.ao.camera = camera;
  }
  function setOrbit(free) { setCut(free); camera = persp; controls.object = persp; passes.render.camera = persp; if (passes.ao) passes.ao.camera = persp; }

  // post-traitement : occlusion ambiante pour les rendus fixes
  const composer = new EffectComposer(renderer);
  const passes = { render: new RenderPass(scene, camera) };
  composer.addPass(passes.render);
  if (quality === 'still') {
    passes.ao = new GTAOPass(scene, camera, W0, H0);
    passes.ao.updateGtaoMaterial({ radius: .5, distanceExponent: 1.2, thickness: 1, scale: 1.1, samples: 16 });
    passes.ao.blendIntensity = .9;
    composer.addPass(passes.ao);
  }
  composer.addPass(new OutputPass());

  function resize(w, h) { renderer.setSize(w, h, false); composer.setSize(w, h); persp.aspect = w / h; persp.updateProjectionMatrix(); if (camera === ortho) fitOrtho(w / h); }

  return {
    THREE, renderer, scene, controls, VIEWS, SOLIDS, PLAN, LAYOUT,
    get camera() { return camera; }, persp,
    setView, setTime, setCut, setOrbit, resize,
    render() { passes.render.camera = camera; if (passes.ao) passes.ao.camera = camera; composer.render(); },
  };
}
