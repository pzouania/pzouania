// Monopoly en ligne : interface (le moteur de règles est python/web/monopoly.py, exécuté par Pyodide).
// Les fonctions el(), appel(), dire() viennent de jouer.js.

function initMonopoly(racine) {
  "use strict";
  const A = (m, args = []) => appel("monopoly", m, args);
  const eur = (n) => `${n} €`;
  const DES = ["", "⚀", "⚁", "⚂", "⚃", "⚄", "⚅"];
  const SOMBRES = ["brun", "rose", "rouge", "vert", "bleu_fonce"];
  let ST = [];          // données fixes des cases
  let S = null;         // état courant
  let survol = null;    // case dont on montre la carte
  let minuteur = null;  // fin de tour automatique
  let modale = null;

  racine.innerHTML = "";
  const zone = el("div", "mono-zone");
  const colonne = el("div", "mono-plateau-col");
  const defilement = el("div", "mono-defile");
  const NS = "http://www.w3.org/2000/svg";
  const plateau = document.createElementNS(NS, "svg");
  plateau.setAttribute("class", "mono-plateau");
  defilement.appendChild(plateau);
  colonne.appendChild(defilement);
  const panneau = el("div", "mono-panneau");
  zone.append(colonne, panneau);
  racine.appendChild(zone);
  const voile = el("div", "mono-voile");
  voile.hidden = true;
  racine.appendChild(voile);

  // ---------- panneau ----------
  const titreTour = el("p", "msg");
  const boutons = el("div", "mono-boutons");
  const mkBtn = (txt, f, cls = "btn") => { const b = el("button", cls, txt); b.type = "button"; b.addEventListener("click", f); return b; };
  const bLancer = mkBtn("Lancer les dés", () => agir("lancer"));
  const bFin = mkBtn("Fin du tour", () => agir("fin_tour"), "btn ghost");
  const bBiens = mkBtn("Gérer mes biens", () => ouvrirBiens(), "btn ghost");
  const bEchange = mkBtn("Échanger", () => ouvrirEchange(), "btn ghost");
  boutons.append(bLancer, bFin, bBiens, bEchange);
  const auto = el("label", "mono-auto");
  const caseAuto = el("input"); caseAuto.type = "checkbox"; caseAuto.checked = true;
  auto.append(caseAuto, document.createTextNode(" Fin de tour automatique"));
  const infoAuto = el("p", "aide");
  const banque = el("p", "aide");
  const joueurs = el("div", "mono-joueurs");
  const carte = el("div", "mono-carte");
  const journal = el("ol", "journal");
  const menu = el("div", "mono-menu");
  const bNouv = mkBtn("Nouvelle partie", () => afficherSetup(), "btn ghost sm");
  const bSauv = mkBtn("Sauvegarder", sauvegarder, "btn ghost sm");
  const bCharg = mkBtn("Charger", () => entree.click(), "btn ghost sm");
  const bClass = mkBtn("Classement", () => ouvrirClassement(false), "btn ghost sm");
  const bTerm = mkBtn("Terminer", terminer, "btn ghost sm");
  const entree = el("input"); entree.type = "file"; entree.accept = ".json,application/json"; entree.hidden = true;
  entree.addEventListener("change", charger);
  menu.append(bNouv, bSauv, bCharg, bClass, bTerm, entree);
  panneau.append(titreTour, boutons, auto, infoAuto, banque, joueurs, carte, journal, menu);
  caseAuto.addEventListener("change", programmerFin);

  // ---------- plateau SVG (port du dessin Tkinter de jeu_monopoly.py) ----------
  const CORNER = 90, SIDE = 56, MARGIN = 8, INNER_A = 98, INNER_B = 602, EDGE = 692, MID = 350;
  const BAND = 17, JAIL_STRIP = 34, PRICE_V = 80, PAWN_V = 62, JAIL_POS = 10;
  const BOARD_BG = "#D2E8D4";
  const CHANCE_COLORS = { 7: "#D6338A", 22: "#1E88C8", 36: "#E8730C" };
  const CORNER_SLOTS_4 = { 0: [[75, 59], [75, 75], [61, 51], [75, 43]], 10: [[23, 65], [12, 77], [11, 54], [36, 75]],
    20: [[75, 22], [75, 75], [22, 75], [18, 14]], 30: [[26, 21], [75, 18], [75, 75], [14, 75]] };
  const CORNER_SLOTS_8 = {
    0: [[64, 58], [64, 46], [75, 51], [75, 63], [75, 75], [53, 53], [45, 62], [75, 39]],
    10: [[20, 57], [9, 52], [10, 64], [16, 75], [26, 68], [36, 75], [41, 64], [26, 20]],
    20: [[76, 34], [75, 22], [67, 13], [18, 14], [13, 67], [22, 75], [34, 76], [75, 75]],
    30: [[26, 21], [15, 26], [16, 14], [75, 18], [75, 63], [75, 75], [64, 70], [14, 75]] };
  const JAIL_SLOTS = [[8, 8], [21, 8], [8, 21], [48, 48], [35, 48], [48, 35], [27, 6], [50, 29]];

  const rectCase = (pos) => {
    if (pos === 0) return [INNER_B, INNER_B, EDGE, EDGE];
    if (pos < 10) { const x1 = INNER_B - pos * SIDE; return [x1, INNER_B, x1 + SIDE, EDGE]; }
    if (pos === 10) return [MARGIN, INNER_B, INNER_A, EDGE];
    if (pos < 20) { const y1 = INNER_B - (pos - 10) * SIDE; return [MARGIN, y1, INNER_A, y1 + SIDE]; }
    if (pos === 20) return [MARGIN, MARGIN, INNER_A, INNER_A];
    if (pos < 30) { const x1 = INNER_A + (pos - 21) * SIDE; return [x1, MARGIN, x1 + SIDE, INNER_A]; }
    if (pos === 30) return [INNER_B, MARGIN, EDGE, INNER_A];
    const y1 = INNER_A + (pos - 31) * SIDE; return [INNER_B, y1, EDGE, y1 + SIDE];
  };
  // repère d'une case de côté : le haut des lettres pointe vers le centre
  const reperes = (pos) => {
    const [x1, y1, x2, y2] = rectCase(pos);
    if (pos < 10) return { to: (u, v) => [x1 + u, y1 + v], angle: 0 };
    if (pos < 20) return { to: (u, v) => [x2 - v, y1 + u], angle: -90 };
    if (pos < 30) return { to: (u, v) => [x2 - u, y2 - v], angle: 180 };
    return { to: (u, v) => [x1 + v, y2 - u], angle: 90 };
  };
  // points (dx, dy) tournés de `angle` degrés dans le sens inverse des aiguilles d'une montre
  const tourne = (pts, cx, cy, angle) => {
    const a = angle * Math.PI / 180, ca = Math.cos(a), sa = Math.sin(a);
    return pts.map(([dx, dy]) => [cx + dx * ca + dy * sa, cy - dx * sa + dy * ca]);
  };
  const trouveCase = (x, y) => { for (let i = 0; i < 40; i++) { const [a, b, c, d] = rectCase(i); if (x >= a && x < c && y >= b && y < d) return i; } return null; };

  const sv = (nom, attrs, parent) => {
    const n = document.createElementNS(NS, nom);
    for (const k in attrs) if (attrs[k] !== undefined && attrs[k] !== null) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  };
  const style = (a = {}) => ({ fill: a.fill || "none", stroke: a.outline || "none", "stroke-width": a.width || 1 });

  // texte : mesure, retour à la ligne, réduction pour tenir dans `fit`
  const mesureur = document.createElement("canvas").getContext("2d");
  const pxDe = (size) => Math.max(6, Math.round(size * 1.33));
  const police = (size, gras) => `${gras ? "bold " : ""}${pxDe(size)}px Arial, Helvetica, sans-serif`;
  function mesure(txt, size, gras) {
    mesureur.font = police(size, gras);
    return Math.max(...txt.split("\n").map((l) => mesureur.measureText(l).width));
  }
  function coupe(txt, size, gras, max) {
    const out = [];
    txt.split("\n").forEach((para) => {
      let cur = "";
      para.split(" ").forEach((mot) => {
        const test = (cur + " " + mot).trim();
        if (cur && mesure(test, size, gras) > max) { out.push(cur); cur = mot; } else cur = test;
      });
      out.push(cur);
    });
    return out.join("\n");
  }
  function texte(parent, xy, txt, o = {}) {
    let { size = 7, gras = false, angle = 0, width, fill = "#000", fit, ancre = "middle", lh } = o;
    if (width) txt = coupe(txt, size, gras, width);
    if (fit) while (size > 4.6 && mesure(txt, size, gras) > fit) size -= 0.25;
    const lignes = txt.split("\n"), px = pxDe(size), h = lh || Math.round(size * 1.33 * 1.2);
    const g = sv("g", angle % 360 ? { transform: `rotate(${-(angle % 360)} ${xy[0]} ${xy[1]})` } : {}, parent);
    lignes.forEach((l, k) => {
      const t = sv("text", { x: xy[0], y: xy[1] + (k - (lignes.length - 1) / 2) * h, "text-anchor": ancre,
        "dominant-baseline": "central", "font-size": px, "font-family": "Arial, Helvetica, sans-serif",
        "font-weight": gras ? "bold" : "normal", fill }, g);
      t.textContent = l;
    });
    return g;
  }
  // pinceau pour icônes : échelle k, rotation angle
  function pinceau(parent, k = 1) {
    const P = (pts, cx, cy, angle, a) => sv("polygon", { points: tourne(pts.map(([x, y]) => [x * k, y * k]), cx, cy, angle).map((p) => p.join(",")).join(" "), ...style(a) }, parent);
    const C = (cx, cy, r, a = {}) => sv("circle", { cx, cy, r: r * k, ...style({ outline: "#000", ...a }) }, parent);
    const at = (cx, cy, angle, dx, dy) => tourne([[dx * k, dy * k]], cx, cy, angle)[0];
    const L = (p, q, a) => sv("line", { x1: p[0], y1: p[1], x2: q[0], y2: q[1], stroke: "#000", "stroke-width": 1 }, parent);
    return { P, C, at, L };
  }
  const ICONES = {
    train(g, cx, cy, ang, k) {
      const { P, C, at } = pinceau(g, k);
      P([[-16, -3], [5, -3], [5, -12], [14, -12], [14, -3], [17, -3], [17, 7], [-16, 7]], cx, cy, ang, { fill: "#222222", outline: "#000" });
      P([[-13, -10], [-7, -10], [-7, -3], [-13, -3]], cx, cy, ang, { fill: "#222222" });
      [-10, 0, 11].forEach((dx) => { const p = at(cx, cy, ang, dx, 9); C(p[0], p[1], 4, { fill: "#222222", outline: "#888888" }); });
    },
    bulb(g, cx, cy, ang, k) {
      const { P, C, at, L } = pinceau(g, k);
      const p = at(cx, cy, ang, 0, -4); C(p[0], p[1], 10, { fill: "#FEF200", outline: "#000" });
      P([[-5, 5], [5, 5], [5, 13], [-5, 13]], cx, cy, ang, { fill: "#999999", outline: "#000" });
      [[-15, -12], [15, -12], [0, -19], [-17, -2], [17, -2]].forEach(([dx, dy]) => L(at(cx, cy, ang, dx * 0.8, dy * 0.8), at(cx, cy, ang, dx, dy)));
    },
    faucet(g, cx, cy, ang, k) {
      const { P } = pinceau(g, k);
      const a = { fill: "#CFCFCF", outline: "#000" };
      P([[-16, -6], [6, -6], [6, 1], [-16, 1]], cx, cy, ang, a);
      P([[0, 1], [7, 1], [7, 9], [0, 9]], cx, cy, ang, a);
      P([[-3, -6], [-3, -12], [1, -12], [1, -6]], cx, cy, ang, a);
      P([[-9, -12], [7, -12], [7, -15], [-9, -15]], cx, cy, ang, a);
      P([[3.5, 11], [6, 15], [3.5, 17], [1, 15]], cx, cy, ang, { fill: "#3BA3E0", outline: "#1E6FA0" });
    },
    chest(g, cx, cy, ang, k) {
      const { P } = pinceau(g, k);
      P([[-14, -2], [14, -2], [14, 11], [-14, 11]], cx, cy, ang, { fill: "#3BA3E0", outline: "#000" });
      P([[-14, -2], [-14, -8], [-8, -13], [8, -13], [14, -8], [14, -2]], cx, cy, ang, { fill: "#7CC6EF", outline: "#000" });
      P([[-3, -4], [3, -4], [3, 3], [-3, 3]], cx, cy, ang, { fill: "#FEF200", outline: "#000" });
    },
    diamond(g, cx, cy, ang, k) {
      const { P } = pinceau(g, k);
      P([[0, -7], [7, 0], [0, 7], [-7, 0]], cx, cy, ang, { outline: "#000", width: 2 });
      P([[0, -3], [3, 0], [0, 3], [-3, 0]], cx, cy, ang, { fill: "#000" });
    },
    ring(g, cx, cy, ang, k) {
      const { P, C, at } = pinceau(g, k);
      const p = at(cx, cy, ang, 0, 3); C(p[0], p[1], 11, { outline: "#C9A227", width: 4 });
      P([[-6, -9], [-3, -14], [3, -14], [6, -9], [0, -4]], cx, cy, ang, { fill: "#BFE9F5", outline: "#0072BB" });
    },
    car(g, cx, cy, ang, k) {
      const { P, C, at } = pinceau(g, k);
      P([[-24, 6], [-24, -2], [-12, -4], [-6, -12], [10, -12], [16, -4], [24, -2], [24, 6]], cx, cy, ang, { fill: "#D7261E", outline: "#000" });
      P([[-4, -10], [8, -10], [12, -4], [-8, -4]], cx, cy, ang, { fill: "#BFE9F5", outline: "#000" });
      [-13, 13].forEach((dx) => { const p = at(cx, cy, ang, dx, 7); C(p[0], p[1], 5, { fill: "#222222", outline: "#000" }); });
    },
    police(g, cx, cy, ang, k) {
      const { P, C, at } = pinceau(g, k);
      let p = at(cx, cy, ang, 0, 4); C(p[0], p[1], 11, { fill: "#F5CBA7", outline: "#000" });
      P([[-14, -4], [14, -4], [10, -16], [-10, -16]], cx, cy, ang, { fill: "#1F3A93", outline: "#000" });
      P([[-16, -5], [16, -5], [16, -2], [-16, -2]], cx, cy, ang, { fill: "#111111" });
      p = at(cx, cy, ang, 0, -11); C(p[0], p[1], 2, { fill: "#FEF200", outline: "none" });
      [-4, 4].forEach((dx) => { const q = at(cx, cy, ang, dx, 3); C(q[0], q[1], 1.5, { fill: "#000" }); });
    },
  };
  const rotRect = (g, cx, cy, w, h, angle, a) => pinceau(g, 1).P([[-w / 2, -h / 2], [w / 2, -h / 2], [w / 2, h / 2], [-w / 2, h / 2]], cx, cy, angle, a);
  const atRot = (cx, cy, angle, dx, dy) => tourne([[dx, dy]], cx, cy, angle)[0];

  // ----- dessin fixe -----
  let couche = null, coucheDyn = null, coucheInfo = null, coucheTouche = null;
  function caseCote(g, i, c) {
    const { to, angle } = reperes(i), t = c.type, w = SIDE - 4, mu = SIDE / 2;
    const nom = (haut, txt, size = 6.5, gras = false, maxBas = 50) => {
      const n = txt.split("\n").length;
      let lh = size * 1.33 * 1.2;
      while (haut + n * lh > maxBas && size > 4.6) { size -= 0.25; lh = size * 1.33 * 1.2; }
      texte(g, to(mu, haut + n * lh / 2), txt, { size, gras, angle, fit: w });
    };
    const icone = (nomIc, v, k) => { const p = to(mu, v); ICONES[nomIc](g, p[0], p[1], angle, k); };
    const prix = (txt, fit) => texte(g, to(mu, PRICE_V), txt, { size: 6, angle, fit });
    if (t === "property") {
      const pts = [to(0, 0), to(SIDE, 0), to(SIDE, BAND), to(0, BAND)];
      sv("polygon", { points: pts.map((p) => p.join(",")).join(" "), fill: c.hex, stroke: "#000" }, g);
      nom(BAND + 2, c.short);
      prix(`${c.price} €`);
    } else if (t === "station") { nom(3, c.short, 6.5, false, 30); icone("train", 40, 0.72); prix("200 €"); }
    else if (t === "utility") { nom(3, c.short, 6.5, false, 30); icone(c.name.includes("eaux") ? "faucet" : "bulb", 41, 0.62); prix("150 €"); }
    else if (t === "chance") {
      texte(g, to(mu, 9), "CHANCE", { size: 6, angle });
      texte(g, to(mu, 33), "?", { size: 21, gras: true, angle, fill: CHANCE_COLORS[i] || "#E8730C" });
    } else if (t === "community") { nom(3, c.short, 6.5, false, 24); icone("chest", 37, 0.8); }
    else if (t === "tax") {
      const cent = c.amount === 100;
      nom(3, c.short, cent ? 7 : 6.5, cent, 28);
      icone(cent ? "ring" : "diamond", 39, 0.75);
      prix(`PAYEZ ${c.amount} €`, w);
    }
  }
  function coin(g, i) {
    const [x1, y1, x2, y2] = rectCase(i), cx = (x1 + x2) / 2, cy = (y1 + y2) / 2;
    if (i === 0) {
      const a = 45, bx = cx - 6, by = cy - 14;
      texte(g, atRot(bx - 2, by + 2, a, 0, -15), "RECEVEZ 200 €\nCHAQUE FOIS QUE\nVOUS PASSEZ ICI", { size: 5, angle: a, fit: 42 });
      texte(g, atRot(bx, by, a, 0, 7), "DÉPART", { size: 12, gras: true, angle: a, fit: 64 });
      const p = [[6, -11], [20, -19], [20, -14], [56, -14], [56, -8], [20, -8], [20, -3]].map(([dx, dy]) => [x1 + dx, y2 + dy]);
      sv("polygon", { points: p.map((q) => q.join(",")).join(" "), fill: "#D7261E", stroke: "#000" }, g);
    } else if (i === JAIL_POS) {
      const jx1 = x1 + JAIL_STRIP, jy2 = y2 - JAIL_STRIP;
      sv("rect", { x: jx1, y: y1, width: x2 - jx1, height: jy2 - y1, fill: "#F7941D", stroke: "#000", "stroke-width": 2 }, g);
      for (let k = 1; k < 5; k++) { const bx = jx1 + k * (x2 - jx1) / 5; sv("line", { x1: bx, y1: y1 + 3, x2: bx, y2: jy2 - 3, stroke: "#5A3A1A", "stroke-width": 2 }, g); }
      const jcx = (jx1 + x2) / 2, jcy = (y1 + jy2) / 2;
      pinceau(g, 1).P([[-32, -8], [32, -8], [32, 8], [-32, 8]], jcx, jcy, 45, { fill: "#fff", outline: "#000" });
      texte(g, [jcx, jcy], "EN PRISON", { size: 7, gras: true, angle: 45, fit: 56 });
      texte(g, [x1 + JAIL_STRIP / 2, y1 + 26], "SIMPLE", { size: 6.5, gras: true, angle: 90 });
      texte(g, [x2 - 24, y2 - JAIL_STRIP / 2], "VISITE", { size: 6.5, gras: true });
    } else if (i === 20) {
      const a = -135;
      texte(g, atRot(cx, cy, a, 0, -24), "PARC", { size: 10, gras: true, angle: a });
      ICONES.car(g, cx, cy, a, 1);
      texte(g, atRot(cx, cy, a, 0, 21), "GRATUIT", { size: 9, gras: true, angle: a });
    } else if (i === 30) {
      const a = 135;
      texte(g, atRot(cx, cy, a, 0, -25), "ALLEZ EN", { size: 9, gras: true, angle: a });
      ICONES.police(g, cx, cy, a, 1);
      texte(g, atRot(cx, cy, a, 0, 22), "PRISON", { size: 9, gras: true, angle: a });
    }
  }
  const PAQUETS = { community: [MID - 132, MID - 132], chance: [MID + 132, MID + 132] };
  function centre(g) {
    let [dx, dy] = PAQUETS.community;
    rotRect(g, dx, dy, 150, 92, 45, { fill: "#BFE3F5", outline: "#1E88C8", width: 3 });
    texte(g, atRot(dx, dy, 45, 0, -34), "CAISSE DE COMMUNAUTÉ", { size: 8, gras: true, angle: 45, fill: "#0B5E8E", fit: 132 });
    { const p = atRot(dx, dy, 45, -54, 22); ICONES.chest(g, p[0], p[1], 45, 0.8); }
    [dx, dy] = PAQUETS.chance;
    rotRect(g, dx, dy, 150, 92, 45, { fill: "#F9B66A", outline: "#C25E00", width: 3 });
    texte(g, atRot(dx, dy, 45, 0, -34), "CHANCE", { size: 8, gras: true, angle: 45, fill: "#8A3F00" });
    texte(g, atRot(dx, dy, 45, -58, 24), "?", { size: 15, gras: true, angle: 45, fill: "#fff" });
    rotRect(g, MID, MID, 370, 72, 45, { fill: "#D7261E", outline: "#000", width: 2 });
    rotRect(g, MID, MID, 356, 58, 45, { outline: "#fff", width: 2 });
    texte(g, [MID, MID], "MONOPOLY", { size: 32, gras: true, angle: 45, fill: "#fff" });
  }
  function construirePlateau() {
    plateau.innerHTML = "";
    plateau.setAttribute("viewBox", "0 0 700 700");
    plateau.setAttribute("role", "img");
    plateau.setAttribute("aria-label", "Plateau de Monopoly");
    couche = sv("g", {}, plateau);
    sv("rect", { x: MARGIN, y: MARGIN, width: EDGE - MARGIN, height: EDGE - MARGIN, fill: BOARD_BG, stroke: "#000", "stroke-width": 2 }, couche);
    ST.forEach((c) => {
      const [x1, y1, x2, y2] = rectCase(c.i);
      sv("rect", { x: x1, y: y1, width: x2 - x1, height: y2 - y1, fill: BOARD_BG, stroke: "#000" }, couche);
      if (c.i % 10 === 0) coin(couche, c.i); else caseCote(couche, c.i, c);
    });
    sv("rect", { x: INNER_A, y: INNER_A, width: INNER_B - INNER_A, height: INNER_B - INNER_A, fill: "none", stroke: "#000", "stroke-width": 2 }, couche);
    centre(couche);
    coucheDyn = sv("g", { "pointer-events": "none" }, plateau);
    coucheInfo = sv("g", { class: "info", "pointer-events": "none" }, plateau);
    coucheTouche = sv("g", {}, plateau);
    ST.forEach((c) => {
      const [x1, y1, x2, y2] = rectCase(c.i);
      const r = sv("rect", { x: x1, y: y1, width: x2 - x1, height: y2 - y1, fill: "transparent", tabindex: 0, role: "button", "aria-label": c.name, style: "cursor:pointer;outline:none" }, coucheTouche);
      r.addEventListener("pointerenter", () => { survol = c.i; dessinerSurvol(); });
      r.addEventListener("pointerleave", (e) => { if (e.pointerType === "mouse") { survol = null; dessinerSurvol(); } });
      r.addEventListener("focus", () => { survol = c.i; dessinerSurvol(); });
      r.addEventListener("click", () => { survol = c.i; dessinerSurvol(); });
    });
    plateau.addEventListener("pointerdown", (e) => { if (e.target === plateau) { survol = null; dessinerSurvol(); } });
  }

  // ----- dessin dynamique -----
  const affiche = [];   // case affichée de chaque pion (change pendant l'animation)
  function pionXY(k) {
    const p = S.players[k], pos = affiche[k], beaucoup = S.players.length > 4;
    const [x1, y1] = rectCase(pos);
    if (pos === JAIL_POS && p.in_jail) { const [sx, sy] = JAIL_SLOTS[k]; return [x1 + JAIL_STRIP + sx, y1 + sy]; }
    if (pos % 10 === 0) { const [sx, sy] = (beaucoup ? CORNER_SLOTS_8 : CORNER_SLOTS_4)[pos][k]; return [x1 + sx, y1 + sy]; }
    const { to } = reperes(pos);
    return beaucoup ? to(9.5 + (k % 4) * 12.3, PAWN_V - 6 + Math.floor(k / 4) * 12) : to(9.5 + k * 12.3, PAWN_V);
  }
  function de(g, cx, cy, v) {
    const s = 18;
    sv("rect", { x: cx - s, y: cy - s, width: 2 * s, height: 2 * s, fill: "#fff", stroke: "#000", "stroke-width": 2 }, g);
    const pts = { 1: [[0, 0]], 2: [[-1, -1], [1, 1]], 3: [[-1, -1], [0, 0], [1, 1]], 4: [[-1, -1], [1, -1], [-1, 1], [1, 1]],
      5: [[-1, -1], [1, -1], [0, 0], [-1, 1], [1, 1]], 6: [[-1, -1], [1, -1], [-1, 0], [1, 0], [-1, 1], [1, 1]] };
    (pts[v] || []).forEach(([px, py]) => sv("circle", { cx: cx + px * 10, cy: cy + py * 10, r: 3.5, fill: "#000", stroke: "#000" }, g));
  }
  function dessinerPlateau() {
    if (!S || !coucheDyn) return;
    const g = coucheDyn;
    g.innerHTML = "";
    const cur = S.players[S.current];
    ST.forEach((c, i) => {
      const cs = S.cells[i];
      if (i % 10 === 0 || !cs) return;
      const { to, angle } = reperes(i);
      if (cs.owner !== null) {
        const pts = [to(0, CORNER - 4), to(SIDE, CORNER - 4), to(SIDE, CORNER), to(0, CORNER)];
        sv("polygon", { points: pts.map((p) => p.join(",")).join(" "), fill: S.players[cs.owner].color, stroke: "#000" }, g);
      }
      if (cs.houses) {
        const P = pinceau(g, 1).P;
        if (cs.houses >= 5) { const p = to(SIDE / 2, BAND / 2); P([[-12, -5], [12, -5], [12, 5], [-12, 5]], p[0], p[1], angle, { fill: "#D0021B", outline: "#000" }); }
        else for (let k = 0; k < cs.houses; k++) { const p = to(7 + k * 14, BAND / 2); P([[-5, 6], [-5, -1], [0, -6], [5, -1], [5, 6]], p[0], p[1], angle, { fill: "#2E8B37", outline: "#000" }); }
      }
      if (cs.mortgaged) {
        const [x1, y1, x2, y2] = rectCase(i);
        sv("line", { x1: x1 + 3, y1: y1 + 3, x2: x2 - 3, y2: y2 - 3, stroke: "#C0392B", "stroke-width": 2 }, g);
        sv("line", { x1: x2 - 3, y1: y1 + 3, x2: x1 + 3, y2: y2 - 3, stroke: "#C0392B", "stroke-width": 2 }, g);
      }
    });
    if (!S.over) {
      const [x1, y1, x2, y2] = rectCase(affiche[S.current]);
      sv("rect", { x: x1 + 1, y: y1 + 1, width: x2 - x1 - 2, height: y2 - y1 - 2, fill: "none", stroke: cur.color, "stroke-width": 3 }, g);
    }
    let init = S.players.map((p) => p.name.slice(0, 1).toUpperCase());
    if (new Set(init).size < init.length) init = S.players.map((_, k) => String(k + 1));
    S.players.forEach((p, k) => {
      if (!p.active) return;
      const [x, y] = pionXY(k), beaucoup = S.players.length > 4, courant = k === S.current;
      const r = beaucoup ? (courant ? 6 : 5) : (courant ? 7 : 6);
      sv("circle", { cx: x, cy: y, r, fill: p.color, stroke: "#fff", "stroke-width": 2 }, g);
      texte(g, [x, y], init[k], { size: 7, gras: true, fill: "#fff" });
    });
    Object.entries(PAQUETS).forEach(([nom, [dx, dy]]) => {
      const t = S.last_card[nom];
      texte(g, atRot(dx, dy, 45, 4, 8), t || "(aucune carte tirée)", { size: 8.5, angle: 45, width: 118, fill: t ? "#000" : "#555555" });
    });
    de(g, MID + 200, MID - 148, S.dice[0]);
    de(g, MID + 200, MID - 104, S.dice[1]);
    if (S.over) texte(g, [MID - 125, MID + 195], `Victoire de\n${S.winner} !`, { size: 12, gras: true, fit: 100 });
    else texte(g, [MID - 125, MID + 195], `Tour de\n${cur.name}`, { size: 12, gras: true, fill: cur.color, fit: 100 });
  }

  // ----- titre de propriété (carte au centre, comme draw_info) -----
  function contenuTitre(i) {
    const c = ST[i], cs = S.cells[i], t = c.type;
    const prop = cs && cs.owner !== null ? S.players[cs.owner] : null;
    const hyp = !!(cs && cs.mortgaged);
    const lignes = [], statut = [];
    let entete;
    const nbType = (typ) => prop ? ST.filter((x, k) => x.type === typ && S.cells[k].owner === cs.owner).length : 0;
    if (t === "property") {
      const r = c.rent, h = cs.houses;
      const groupe = ST.filter((x) => x.type === "property" && x.color === c.color);
      const nb = prop ? groupe.filter((x) => S.cells[x.i].owner === cs.owner).length : 0;
      const complet = prop && nb === groupe.length;
      let actif = null;
      if (prop) actif = h ? h : (complet ? "group" : 0);
      ["LOYER Terrain nu", "Avec 1 Maison", "Avec 2 Maisons", "Avec 3 Maisons", "Avec 4 Maisons", "Avec HÔTEL"]
        .forEach((nom, k) => lignes.push(["row", nom, `${r[k]} €`, actif === k]));
      lignes.push(["sep"],
        ["row", "Prix des Maisons", `${c.house_price} € chacune`, false],
        ["row", "Prix d'un Hôtel", `${c.house_price} € + 4 maisons`, false],
        ["row", "Valeur hypothécaire", `${c.mortgage} €`, false], ["sep"],
        ["note", "Si un joueur possède TOUS les terrains\nd'un groupe de couleur, le loyer des\nterrains nus de ce groupe est doublé.", actif === "group"]);
      if (prop) statut.push([`Groupe : ${nb}/${groupe.length} terrain(s) à ${prop.name}`, "#000"]);
      entete = ["title", c.hex, SOMBRES.includes(c.color) ? "#fff" : "#000"];
    } else if (t === "station") {
      const n = nbType("station");
      lignes.push(["row", "LOYER", "25 €", n === 1], ["row", "Si 2 gares sont possédées", "50 €", n === 2],
        ["row", "Si 3 gares sont possédées", "100 €", n === 3], ["row", "Si 4 gares sont possédées", "200 €", n === 4],
        ["sep"], ["row", "Valeur hypothécaire", "100 €", false]);
      if (prop) statut.push([`${prop.name} possède ${n} gare(s)`, "#000"]);
      entete = ["icon", "train"];
    } else if (t === "utility") {
      const n = nbType("utility");
      lignes.push(["note", "Si l'on possède UNE carte de compagnie,\nle loyer est 4 fois le montant\nindiqué par les dés.", n === 1],
        ["note", "Si l'on possède les DEUX cartes de\ncompagnie, le loyer est 10 fois le\nmontant indiqué par les dés.", n === 2],
        ["sep"], ["row", "Valeur hypothécaire", "75 €", false]);
      entete = ["icon", c.name.includes("eaux") ? "faucet" : "bulb"];
    } else {
      const desc = {
        start: "Recevez 200 € chaque fois que vous\npassez ou vous arrêtez sur la\ncase Départ.",
        jail: "Simple visite : rien ne se passe.\n\nEn prison : 3 tentatives pour faire\nun double, ou payez 50 € avant de\nlancer, ou utilisez une carte\n« Libéré de prison ».\nAu 3e échec, payez 50 € et avancez.\nEn prison, on touche ses loyers.",
        free_parking: "Case de repos : rien ne se passe.\n(Aucun argent à gagner ici,\nselon les règles officielles.)",
        go_to_jail: "Allez directement en prison, sans\npasser par la case Départ ni\nrecevoir 200 €.",
        chance: "Tirez une carte Chance et suivez\nses instructions.",
        community: "Tirez une carte Caisse de\ncommunauté et suivez ses\ninstructions.",
        tax: `Payez ${c.amount || 0} € à la banque.`,
      }[t];
      lignes.push(["note", desc, false]);
      entete = ["plain"];
    }
    if (t === "property" || t === "station" || t === "utility") {
      if (prop && hyp) {
        statut.unshift([`Propriétaire : ${prop.name}`, prop.color]);
        statut.push([`HYPOTHÉQUÉ - lever : ${cs.unmortgage} €`, "#C0392B"], ["Loyer actuel : 0 €", "#000"]);
      } else if (prop) {
        statut.unshift([`Propriétaire : ${prop.name}`, prop.color]);
        if (t === "utility") statut.push([`Loyer actuel : ${nbType("utility") === 1 ? 4 : 10} × les dés`, "#000"]);
        else statut.push([`Loyer actuel : ${cs.rent} €`, "#000"]);
      } else statut.push([`À vendre : ${c.price} €`, "#2E8B37"]);
    }
    return { entete, lignes, statut, prop, hyp };
  }
  function dessinerSurvol() {
    if (!coucheInfo) return;
    coucheInfo.innerHTML = "";
    casesSel();
    dessinerCarte();
    if (survol === null || !S) return;
    const g = coucheInfo, i = survol, c = ST[i];
    const { entete, lignes, statut, prop, hyp } = contenuTitre(i);
    const w = 240;
    let teteH = entete[0] === "icon" ? 64 : 56;
    if (entete[0] === "plain") teteH = 40;
    let corpsH = 0;
    lignes.forEach((l) => { corpsH += l[0] === "row" ? 17 : l[0] === "sep" ? 9 : (l[1].split("\n").length) * 12 + 8; });
    const statH = statut.length ? statut.length * 16 + 12 : 0;
    const h = 10 + teteH + 10 + corpsH + 6 + statH + 8;
    const x1 = MID - w / 2, y1 = MID - h / 2, x2 = x1 + w, y2 = y1 + h;
    sv("rect", { x: x1 + 5, y: y1 + 5, width: w, height: h, fill: "#6E8E73" }, g);
    sv("rect", { x: x1, y: y1, width: w, height: h, fill: "#fff", stroke: "#000", "stroke-width": 2 }, g);
    sv("rect", { x: x1 + 5, y: y1 + 5, width: w - 10, height: h - 10 - statH, fill: "none", stroke: "#444" }, g);
    const hy1 = y1 + 10, hy2 = hy1 + teteH;
    if (entete[0] === "title") {
      sv("rect", { x: x1 + 10, y: hy1, width: w - 20, height: teteH, fill: entete[1], stroke: "#000" }, g);
      texte(g, [MID, hy1 + 13], "TITRE DE PROPRIÉTÉ", { size: 7, fill: entete[2] });
      texte(g, [MID, hy1 + 36], c.name.toUpperCase(), { size: 10, gras: true, width: w - 30, fill: entete[2] });
    } else if (entete[0] === "icon") {
      ICONES[entete[1]](g, MID, hy1 + 18, 0, 1);
      texte(g, [MID, hy1 + 50], c.name.toUpperCase(), { size: 9, gras: true, width: w - 30 });
    } else texte(g, [MID, hy1 + teteH / 2], c.name.toUpperCase(), { size: 11, gras: true, width: w - 30 });
    let y = hy2 + 10;
    const hl = prop ? prop.color : "#000";
    lignes.forEach((l) => {
      if (l[0] === "sep") { sv("line", { x1: x1 + 16, y1: y + 3, x2: x2 - 16, y2: y + 3, stroke: "#AAA" }, g); y += 9; }
      else if (l[0] === "row") {
        const actif = l[3] && !hyp;
        if (actif) sv("rect", { x: x1 + 10, y: y - 1, width: w - 20, height: 16, fill: "#FFF3B0" }, g);
        const col = actif ? hl : "#000";
        texte(g, [x1 + 16, y + 7], l[1], { size: 8, gras: actif, ancre: "start", fill: col });
        texte(g, [x2 - 16, y + 7], l[2], { size: 8, gras: actif, ancre: "end", fill: col });
        y += 17;
      } else {
        const actif = l[2] && !hyp, nb = l[1].split("\n").length;
        if (actif) sv("rect", { x: x1 + 10, y, width: w - 20, height: nb * 12 + 4, fill: "#FFF3B0" }, g);
        texte(g, [MID, y + 2 + nb * 6], l[1], { size: entete[0] !== "plain" ? 7 : 8, gras: actif, fill: actif ? hl : "#333", lh: 12 });
        y += nb * 12 + 8;
      }
    });
    if (statut.length) {
      const sy = y2 - statH;
      sv("rect", { x: x1 + 2, y: sy, width: w - 4, height: statH - 2, fill: "#EEF3EE" }, g);
      statut.forEach(([t, col], k) => texte(g, [MID, sy + 12 + k * 16], t, { size: 8, gras: k === 0, fill: col }));
    }
  }
  function casesSel() { /* le survol est montré par la carte du centre */ }

  // ----- animation des pions -----
  const pause = (ms) => new Promise((r) => setTimeout(r, ms));
  async function animer(moves) {
    for (const [k, cible, sens] of moves) {
      let cur = affiche[k];
      const n = sens === 0 ? 0 : sens > 0 ? (cible - cur + 40) % 40 : (cur - cible + 40) % 40;
      const delai = n <= 12 ? 90 : 35;
      for (let s = 0; s < n; s++) {
        cur = (cur + (sens > 0 ? 1 : 39)) % 40;
        affiche[k] = cur;
        dessinerPlateau();
        await pause(delai);
      }
      affiche[k] = cible;
      dessinerPlateau();
    }
  }

  // ---------- rendu ----------
  function dessiner() {
    if (!S) return;
    const cur = S.players[S.current];
    titreTour.textContent = S.over ? `Victoire de ${S.winner}` : `Tour de ${cur.name}`;
    titreTour.style.color = S.over ? "" : cur.color;
    bLancer.disabled = !S.can_roll;
    bFin.disabled = !S.can_end;
    bBiens.disabled = S.over || !!S.pending;
    bEchange.disabled = S.over || !!S.pending || S.players.filter((p) => p.active).length < 2;
    bTerm.disabled = S.over;
    banque.textContent = `Banque : ${S.houses_left} maison(s), ${S.hotels_left} hôtel(s) disponibles`;

    dessinerPlateau();

    joueurs.innerHTML = "";
    S.players.forEach((p, k) => {
      const l = el("div", "joueur" + (k === S.current && !S.over ? " actif" : "") + (p.active ? "" : " out"));
      const nom = el("div", "j-nom");
      nom.style.color = p.color;
      nom.textContent = (k === S.current && !S.over ? "▸ " : "") + p.name;
      const val = el("div", "j-val");
      val.textContent = p.active
        ? `${eur(p.money)} · patrimoine ${eur(p.money + p.assets)}` + (p.in_jail ? " · en prison" : "") + (p.jail_cards ? ` · ${p.jail_cards} carte(s) prison` : "")
        : "faillite";
      const chips = el("div", "jetons");
      p.properties.forEach((i) => {
        const c = ST[i], cs = S.cells[i];
        const j = el("span", "jeton" + (cs.mortgaged ? " hyp" : ""));
        j.style.background = c.hex || (c.type === "station" ? "#222" : "#ddd");
        j.title = c.name;
        if (c.type === "property" && cs.houses) j.textContent = cs.houses === 5 ? "H" : cs.houses;
        else if (c.type === "station") j.textContent = "G";
        else if (c.type === "utility") j.textContent = "C";
        if (c.type === "property" && SOMBRES.includes(c.color) || c.type === "station") j.classList.add("clair");
        j.addEventListener("mouseenter", () => { survol = i; dessinerSurvol(); });
        j.addEventListener("mouseleave", () => { survol = null; dessinerSurvol(); });
        j.addEventListener("click", () => { survol = i; dessinerSurvol(); });
        chips.appendChild(j);
      });
      if (!p.properties.length && p.active) chips.appendChild(el("span", "aucun", "aucun titre"));
      l.append(nom, val, chips);
      joueurs.appendChild(l);
    });

    journal.innerHTML = "";
    S.log.slice(-60).forEach((t) => journal.appendChild(el("li", null, t)));
    journal.scrollTop = journal.scrollHeight;
    dessinerSurvol();
  }

  function dessinerCarte() {
    carte.innerHTML = "";
    if (survol === null || !ST.length) { carte.hidden = true; return; }
    carte.hidden = false;
    const c = ST[survol], cs = S && S.cells[survol];
    const t = el("div", "carte-titre", c.name.toUpperCase());
    if (c.hex) { t.style.background = c.hex; t.style.color = SOMBRES.includes(c.color) ? "#fff" : "#000"; }
    carte.appendChild(t);
    const lignes = el("div", "carte-corps");
    const ligne = (g, d, actif) => {
      const r = el("div", "ligne" + (actif ? " actif" : ""));
      r.append(el("span", null, g), el("span", null, d));
      lignes.appendChild(r);
    };
    const nbCompagnie = (typ) => S ? S.cells.filter((x, i) => x && x.owner !== null && ST[i].type === typ && x.owner === cs.owner).length : 0;
    if (c.type === "property") {
      const act = cs && cs.owner !== null ? (cs.houses || 0) : -1;
      ["Terrain nu", "Avec 1 maison", "Avec 2 maisons", "Avec 3 maisons", "Avec 4 maisons", "Avec un hôtel"]
        .forEach((nom, k) => ligne(nom, eur(c.rent[k]), act === k && !cs.mortgaged));
      lignes.appendChild(el("hr"));
      ligne("Prix d'une maison", eur(c.house_price));
      ligne("Hypothèque", eur(c.mortgage));
      lignes.appendChild(el("p", "note-c", "Tout le groupe de couleur en main : loyer du terrain nu doublé."));
    } else if (c.type === "station") {
      const n = cs && cs.owner !== null ? nbCompagnie("station") : 0;
      [25, 50, 100, 200].forEach((v, k) => ligne(k ? `${k + 1} gares possédées` : "Loyer (1 gare)", eur(v), n === k + 1 && !cs.mortgaged));
      lignes.appendChild(el("hr"));
      ligne("Hypothèque", eur(c.mortgage));
    } else if (c.type === "utility") {
      const n = cs && cs.owner !== null ? nbCompagnie("utility") : 0;
      ligne("1 compagnie", "4 × les dés", n === 1 && !cs.mortgaged);
      ligne("2 compagnies", "10 × les dés", n === 2 && !cs.mortgaged);
      lignes.appendChild(el("hr"));
      ligne("Hypothèque", eur(c.mortgage));
    } else {
      const txt = {
        start: "Recevez 200 € chaque fois que vous passez ou vous arrêtez ici.",
        jail: "Simple visite : rien ne se passe. En prison : 3 tentatives pour faire un double, ou payez 50 € avant de lancer, ou utilisez une carte « Libéré de prison ».",
        free_parking: "Case de repos : rien ne se passe.",
        go_to_jail: "Allez directement en prison, sans passer par Départ.",
        chance: "Tirez une carte Chance.",
        community: "Tirez une carte Caisse de communauté.",
        tax: `Payez ${c.amount || 0} € à la banque.`,
      }[c.type];
      lignes.appendChild(el("p", "note-c", txt));
    }
    carte.appendChild(lignes);
    if (cs && c.price) {
      const e = el("div", "carte-etat");
      if (cs.owner === null) e.textContent = `À vendre : ${eur(c.price)}`;
      else {
        const p = S.players[cs.owner];
        e.textContent = `Propriétaire : ${p.name}` + (cs.mortgaged ? ` · hypothéqué (lever : ${eur(cs.unmortgage)})` : ` · loyer actuel : ${eur(cs.rent)}`);
        e.style.color = p.color;
      }
      carte.appendChild(e);
    }
  }

  // ---------- actions ----------
  let occupe = false;   // animation en cours : les actions sont ignorées
  function maj(res) {
    if (res.statique) { ST = res.statique; construirePlateau(); }
    if (res.etat) {
      S = res.etat;
      if (affiche.length !== S.players.length || res.statique) S.players.forEach((p, k) => { affiche[k] = p.position; });
    }
    clearTimeout(minuteur);
    const mv = (res.etat && res.etat.moves) || [];
    const suite = () => {
      S.players.forEach((p, k) => { affiche[k] = p.position; });
      dessiner();
      if (modale && modale.dataset.type === "biens") listeBiens(null);
      else if (S && S.pending && S.pending.type === "funds") listeBiens(S.pending);
      else gererAttente();
      programmerFin();
      if (S && S.over && !classementMontre) { classementMontre = true; ouvrirClassement(true); }
      if (S && !S.over) classementMontre = false;
    };
    if (mv.length) {
      occupe = true;
      dessiner();
      animer(mv).then(() => { occupe = false; suite(); }, () => { occupe = false; suite(); });
    } else suite();
    return res;
  }
  function agir(methode, args = []) {
    if (occupe) return;
    try { return maj(A(methode, args)); }
    catch (e) { console.error(e); dire(`Erreur : ${e.message}`, true); }
  }
  function programmerFin() {
    clearTimeout(minuteur);
    infoAuto.textContent = "";
    if (!S || S.over || S.pending || !S.can_end) return;
    if (S.has_actions) infoAuto.textContent = "Vous pouvez encore construire ou lever une hypothèque (« Gérer mes biens »), puis cliquer sur « Fin du tour ».";
    else if (caseAuto.checked) {
      infoAuto.textContent = "Plus d'action possible : fin du tour automatique…";
      minuteur = setTimeout(() => { if (S && S.can_end && !S.pending && !modale) agir("fin_tour"); }, 1500);
    }
  }
  function sauvegarder() {
    const d = A("sauvegarder").donnees;
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([JSON.stringify(d, null, 1)], { type: "application/json" }));
    a.download = "monopoly_partie.json";
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  }
  async function charger() {
    const f = entree.files[0]; entree.value = "";
    if (!f) return;
    try { maj(A("charger", [JSON.parse(await f.text())])); }
    catch (e) { dire("Fichier de sauvegarde invalide.", true); }
  }
  function terminer() {
    if (!S || S.over) return;
    boite("Terminer la partie", "<p>Arrêter maintenant et classer les joueurs selon leur patrimoine ?</p>", [
      ["Oui, terminer", () => { fermer(); agir("terminer"); }], ["Non", fermer]]);
  }

  // ---------- fenêtres ----------
  function fermer() { voile.hidden = true; voile.innerHTML = ""; modale = null; programmerFin(); }
  function boite(titre, html, actions = [], large = false) {
    voile.innerHTML = "";
    const m = el("div", "mono-modale" + (large ? " large" : ""));
    m.setAttribute("role", "dialog"); m.setAttribute("aria-modal", "true");
    m.appendChild(el("h3", null, titre));
    const corps = el("div", "corps");
    if (typeof html === "string") corps.innerHTML = html; else corps.appendChild(html);
    m.appendChild(corps);
    const pied = el("div", "pied");
    actions.forEach(([txt, f, cls]) => pied.appendChild(mkBtn(txt, f, cls || "btn")));
    m.appendChild(pied);
    voile.appendChild(m);
    voile.hidden = false;
    modale = m;
    const premier = pied.querySelector("button");
    if (premier) premier.focus();
    return corps;
  }
  const echapper = (s) => s.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

  function gererAttente() {
    const p = S && S.pending;
    if (!p) { if (modale && modale.dataset.type === "decision") fermer(); return; }
    let m;
    if (p.type === "ask") {
      boite(p.title, `<p>${echapper(p.question).replace(/\n/g, "<br>")}</p>`, [
        ["Oui", () => agir("repondre", [true])], ["Non", () => agir("repondre", [false]), "btn ghost"]]);
    } else if (p.type === "bid") {
      const corps = boite("Enchères",
        `<p><b>${echapper(p.item)}</b> (prix : ${eur(p.price)})</p><p>${p.best ? `Meilleure offre : ${eur(p.best_bid)} (${echapper(p.best)})` : "Aucune offre pour l'instant"}</p>` +
        `<p>${echapper(p.player)}, votre enchère ? (minimum ${eur(p.minimum)}, solde ${eur(p.money)})</p>`, []);
      const champ = el("input"); champ.type = "number"; champ.min = p.minimum; champ.max = p.money; champ.value = p.minimum; champ.className = "mono-champ";
      corps.appendChild(champ);
      const pied = modale.querySelector(".pied");
      pied.append(
        mkBtn("Enchérir", () => {
          const v = parseInt(champ.value, 10);
          if (!(v >= p.minimum && v <= p.money)) { champ.focus(); return; }
          agir("repondre", [v]);
        }),
        mkBtn("Passer", () => agir("repondre", [null]), "btn ghost"));
      champ.focus(); champ.select();
      champ.addEventListener("keydown", (e) => { if (e.key === "Enter") pied.firstChild.click(); });
    } else if (p.type === "funds") {
      listeBiens(p);
      return;
    }
    if (modale) modale.dataset.type = "decision";
  }

  function listeBiens(dette) {
    const man = S.manage;
    const corps = el("div", "mono-biens");
    if (dette) {
      const to = dette.creditor || "la banque";
      corps.appendChild(el("p", "alerte", `${dette.player} doit ${eur(dette.amount)} à ${to}. Vendez des bâtiments ou hypothéquez des terrains pour réunir la somme (solde : ${eur(man.money)}).`));
    } else {
      corps.appendChild(el("p", "aide", `${man.player} · ${eur(man.money)} · banque : ${S.houses_left} maison(s), ${S.hotels_left} hôtel(s)`));
    }
    if (!man.titles.length) corps.appendChild(el("p", "aide", "Aucun titre de propriété."));
    man.titles.forEach((t) => {
      const c = ST[t.i], cs = S.cells[t.i];
      const l = el("div", "bien");
      const pastille = el("span", "pastille"); pastille.style.background = c.hex || (c.type === "station" ? "#222" : "#ddd");
      const etat = cs.mortgaged ? "hypothéqué" : cs.houses === 5 ? "hôtel" : cs.houses ? `${cs.houses} maison(s)` : "";
      l.append(pastille, el("span", "b-nom", c.name), el("span", "b-etat", etat));
      const acts = el("span", "b-acts");
      const act = (txt, ok, f, titre) => { const b = mkBtn(txt, f, "btn ghost sm"); b.disabled = !ok; if (titre && !ok) b.title = titre; acts.appendChild(b); };
      if (c.type === "property") {
        act(t.build_hotel ? `+ Hôtel (${c.house_price}€)` : `+ Maison (${c.house_price}€)`, t.build, () => dette ? 0 : agir("construire", [t.i]), t.build_reason);
        act(`Vendre (+${Math.floor(c.house_price / 2)}€)`, t.sell, () => dette ? agir("repondre", [["sell", t.i]]) : agir("vendre", [t.i]));
      }
      if (cs.mortgaged) act(`Lever (−${cs.unmortgage}€)`, t.unmortgage, () => agir("lever", [t.i]));
      else act(`Hypothéquer (+${c.mortgage}€)`, t.mortgage, () => dette ? agir("repondre", [["mortgage", t.i]]) : agir("hypothequer", [t.i]));
      l.appendChild(acts);
      corps.appendChild(l);
    });
    corps.appendChild(el("p", "aide petite", "On construit sur un groupe complet, de façon égale ; on hypothèque après avoir vendu les bâtiments du groupe ; lever une hypothèque coûte la valeur + 10 %."));
    const actions = dette
      ? [[`Payer ${eur(dette.amount)}`, () => agir("repondre", ["pay"])], ["Déclarer faillite", () => agir("repondre", ["bankrupt"]), "btn ghost"]]
      : [["Fermer", fermer]];
    boite(dette ? "Réunir la somme due" : `Biens de ${man.player}`, corps, actions, true);
    modale.dataset.type = dette ? "decision" : "biens";
    if (dette) { const b = modale.querySelector(".pied button"); b.disabled = man.money < dette.amount; }
  }

  function ouvrirBiens() {
    if (!S || S.over || S.pending) return;
    clearTimeout(minuteur);
    listeBiens(null);
  }

  function ouvrirClassement(final) {
    const rows = S.ranking;
    const t = el("table", "mono-table");
    t.innerHTML = "<thead><tr><th>Rang</th><th>Joueur</th><th>Argent</th><th>Biens</th><th>Patrimoine</th><th></th></tr></thead>";
    const tb = el("tbody");
    rows.forEach((r) => {
      const tr = el("tr");
      tr.innerHTML = `<td>${r.rank}.</td><td style="color:${r.color}">${echapper(r.name)}</td><td>${eur(r.money)}</td><td>${eur(r.assets)}</td><td><b>${eur(r.money + r.assets)}</b></td><td>${r.active ? "" : "faillite"}</td>`;
      tb.appendChild(tr);
    });
    t.appendChild(tb);
    const corps = el("div");
    if (final) corps.appendChild(el("p", "msg", `${rows[0].name} gagne le Monopoly !`));
    corps.append(t, el("p", "aide petite", "Biens = prix des titres (moins l'hypothèque) + prix des bâtiments."));
    boite(final ? "Fin de partie" : "Classement", corps,
      final ? [["Nouvelle partie", afficherSetup], ["Fermer", fermer, "btn ghost"]] : [["Fermer", fermer]]);
    modale.dataset.type = "classement";
  }

  function ouvrirEchange() {
    if (!S || S.over || S.pending) return;
    clearTimeout(minuteur);
    const a = S.players[S.current];
    const autres = S.players.filter((p) => p.active && p.k !== a.k);
    const corps = el("div", "mono-echange");
    const choix = el("select", "mono-champ");
    autres.forEach((p) => choix.appendChild(new Option(p.name, p.k)));
    const tete = el("p"); tete.append(`${a.name} propose un échange à : `, choix);
    const cols = el("div", "echange-cols");
    corps.append(tete, cols);
    const msg = el("p", "alerte");
    corps.appendChild(msg);
    let cases = {};
    function colonnes() {
      cols.innerHTML = ""; cases = {};
      [a, S.players[+choix.value]].forEach((p) => {
        const c = el("fieldset", "echange-col");
        c.appendChild(el("legend", null, `${p.name} donne (${eur(p.money)})`));
        const props = [];
        p.properties.forEach((i) => {
          const l = el("label"); const cb = el("input"); cb.type = "checkbox";
          const hyp = S.cells[i].mortgaged ? " (hyp.)" : "";
          l.append(cb, document.createTextNode(" " + ST[i].name + hyp));
          c.appendChild(l); props.push([i, cb]);
        });
        const cartes = [];
        for (let k = 0; k < p.jail_cards; k++) {
          const l = el("label"); const cb = el("input"); cb.type = "checkbox";
          l.append(cb, document.createTextNode(" Carte « Libéré de prison »"));
          c.appendChild(l); cartes.push([k, cb]);
        }
        if (!p.properties.length && !p.jail_cards) c.appendChild(el("p", "aide", "(aucun titre)"));
        const l = el("label", "argent"); l.append("Argent : ");
        const m = el("input", "mono-champ court"); m.type = "number"; m.min = 0; m.value = 0;
        l.append(m, " €"); c.appendChild(l);
        cases[p.k] = { props, cartes, m };
        cols.appendChild(c);
      });
    }
    choix.addEventListener("change", colonnes);
    colonnes();
    corps.appendChild(el("p", "aide petite", "Seuls les titres sans bâtiment sur leur groupe peuvent être échangés. Celui qui reçoit un terrain hypothéqué paie 10 % d'intérêts."));
    const lire = () => {
      const k2 = +choix.value, g = (k) => ({
        props: cases[k].props.filter(([, c]) => c.checked).map(([i]) => i),
        cartes: cases[k].cartes.filter(([, c]) => c.checked).map(([i]) => i),
        argent: parseInt(cases[k].m.value, 10) || 0 });
      return { a: a.k, b: k2, A: g(a.k), B: g(k2) };
    };
    boite("Échange", corps, [["Proposer l'échange", () => {
      const t = lire();
      const args = { a: t.a, b: t.b, a_props: t.A.props, b_props: t.B.props, a_money: t.A.argent, b_money: t.B.argent, a_cards: t.A.cartes, b_cards: t.B.cartes };
      const err = A("valider_echange", [args]).erreur;
      if (err) { msg.textContent = err; return; }
      const nomB = S.players[t.b].name;
      const decrire = (x) => { const l = [...x.props.map((i) => ST[i].name), ...x.cartes.map(() => "carte « Libéré de prison »")]; if (x.argent) l.push(eur(x.argent)); return l.length ? l.join(", ") : "rien"; };
      boite("Échange", `<p>${echapper(nomB)}, acceptez-vous cet échange ?</p><p>${echapper(a.name)} donne : ${echapper(decrire(t.A))}<br>${echapper(nomB)} donne : ${echapper(decrire(t.B))}</p>`, [
        ["Accepter", () => { fermer(); agir("echange", [args]); }],
        ["Refuser", fermer, "btn ghost"]]);
    }], ["Annuler", fermer, "btn ghost"]], true);
    modale.dataset.type = "echange";
  }

  // ---------- nouvelle partie ----------
  function afficherSetup() {
    clearTimeout(minuteur);
    const corps = el("div", "mono-setup");
    const nb = el("select", "mono-champ");
    for (let n = 2; n <= 8; n++) nb.appendChild(new Option(`${n} joueurs`, n));
    nb.value = 3;
    const l1 = el("label"); l1.append("Nombre de joueurs", nb);
    const noms = el("div", "noms");
    const champs = [];
    const defaut = ["Pierre", "Joueur 2", "Joueur 3", "Joueur 4", "Joueur 5", "Joueur 6", "Joueur 7", "Joueur 8"];
    for (let k = 0; k < 8; k++) {
      const i = el("input", "mono-champ"); i.type = "text"; i.maxLength = 14; i.value = defaut[k]; i.setAttribute("aria-label", `Nom du joueur ${k + 1}`);
      champs.push(i); noms.appendChild(i);
    }
    const maj_ = () => champs.forEach((c, k) => { c.hidden = k >= +nb.value; });
    nb.addEventListener("change", maj_); maj_();
    corps.append(l1, noms);
    boite("Nouvelle partie", corps, [["Commencer", () => {
      const liste = champs.slice(0, +nb.value).map((c, k) => c.value.trim() || `Joueur ${k + 1}`);
      fermer();
      agir("nouvelle", [liste]);
    }]].concat(S ? [["Annuler", fermer, "btn ghost"]] : []));
    modale.dataset.type = "setup";
  }

  let classementMontre = false;

  // démarrage : on récupère les cases puis on propose une nouvelle partie
  ST = A("statique").statique || [];
  afficherSetup();
}
