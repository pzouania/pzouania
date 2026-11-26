// Page « Jouer » : charge Pyodide (Python dans le navigateur) et affiche les jeux.
// La logique des jeux est en Python (python/web/*.py) ; ce fichier ne fait que dessiner et relayer les clics.

const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/";
const statut = document.getElementById("statut");
let pyodide = null;
let chargementPyodide = null;
const modulesCharges = {};
const jeuxInitialises = {};

function dire(texte, erreur = false) {
  statut.textContent = texte;
  statut.classList.toggle("erreur", erreur);
}

function el(tag, classe, texte) {
  const e = document.createElement(tag);
  if (classe) e.className = classe;
  if (texte !== undefined) e.textContent = texte;
  return e;
}

// ---------- Pont JavaScript <-> Python ----------
function chargerPyodide() {
  if (!chargementPyodide) {
    chargementPyodide = new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = PYODIDE_URL + "pyodide.js";
      s.onload = async () => {
        try { resolve(await loadPyodide({ indexURL: PYODIDE_URL })); }
        catch (e) { reject(e); }
      };
      s.onerror = () => reject(new Error("Impossible de télécharger Pyodide (connexion internet requise)."));
      document.head.appendChild(s);
    });
    chargementPyodide.catch(() => { chargementPyodide = null; });
  }
  return chargementPyodide;
}

async function chargerModule(nom) {
  pyodide = await chargerPyodide();
  if (modulesCharges[nom]) return;
  const reponse = await fetch(`python/web/${nom}.py`);
  if (!reponse.ok) throw new Error(`Fichier python/web/${nom}.py introuvable.`);
  pyodide.FS.writeFile(`/home/pyodide/${nom}.py`, await reponse.text());
  pyodide.runPython(
    "import sys, importlib\n" +
    "if '/home/pyodide' not in sys.path: sys.path.insert(0, '/home/pyodide')\n" +
    "importlib.invalidate_caches()"
  );
  pyodide.runPython(`import ${nom}`);
  modulesCharges[nom] = true;
}

function appel(nom, methode, args = []) {
  const code =
    `import json, ${nom}\n` +
    `json.dumps(${nom}.api(${JSON.stringify(methode)}, json.loads(${JSON.stringify(JSON.stringify(args))})))`;
  return JSON.parse(pyodide.runPython(code));
}

// ---------- Dames ----------
function initDames(racine) {
  racine.innerHTML = "";
  const zone = el("div", "zone");
  const plateau = el("div", "plateau");
  const grille = el("div", "grille8");
  plateau.appendChild(grille);
  const panneau = el("div", "panneau");
  const msg = el("p", "msg");
  const aide = el("p", "aide", "Cliquez sur un de vos pions, puis sur une case marquée. La prise est obligatoire.");
  const nouveau = el("button", "btn", "Nouvelle partie");
  nouveau.type = "button";
  panneau.append(msg, aide, nouveau);
  zone.append(plateau, panneau);
  racine.appendChild(zone);

  const cases = [];
  for (let i = 0; i < 8; i++) {
    for (let j = 0; j < 8; j++) {
      const b = el("button", "sq " + ((i + j) % 2 === 0 ? "l" : "d"));
      b.type = "button";
      b.setAttribute("aria-label", `Ligne ${i + 1}, colonne ${j + 1}`);
      b.addEventListener("click", () => dessiner(appel("dames", "clic", [i, j])));
      grille.appendChild(b);
      cases.push(b);
    }
  }

  function dessiner(etat) {
    const coups = new Set(etat.coups.map((c) => c.join(",")));
    for (let i = 0; i < 8; i++) {
      for (let j = 0; j < 8; j++) {
        const b = cases[i * 8 + j];
        const p = etat.plateau[i][j];
        b.className = "sq " + ((i + j) % 2 === 0 ? "l" : "d");
        if (etat.selection && etat.selection[0] === i && etat.selection[1] === j) b.classList.add("sel");
        if (coups.has(`${i},${j}`)) b.classList.add("cible");
        b.textContent = "";
        if (p !== ".") {
          const pion = el("span", "pion " + (p === p.toUpperCase() ? "b" : "n") + (p === "D" || p === "d" ? " dame" : ""));
          b.appendChild(pion);
        }
      }
    }
    msg.textContent = etat.message;
    msg.classList.toggle("fin", !!etat.fin);
  }

  nouveau.addEventListener("click", () => dessiner(appel("dames", "reset")));
  dessiner(appel("dames", "reset"));
}

// ---------- Échecs ----------
const GLYPHES = { k: "♚", q: "♛", r: "♜", b: "♝", n: "♞", p: "♟" };
const glyphe = (p) => GLYPHES[p.toLowerCase()] + "︎";

function initEchecs(racine) {
  racine.innerHTML = "";
  const zone = el("div", "zone");
  const wrap = el("div", "echecs-wrap");
  const rangs = el("div", "rangs");
  const fichiers = el("div", "fichiers");
  for (let i = 0; i < 8; i++) rangs.appendChild(el("span", "", String(8 - i)));
  for (const f of "abcdefgh") fichiers.appendChild(el("span", "", f));
  const plateau = el("div", "plateau");
  const grille = el("div", "grille8");
  plateau.appendChild(grille);
  wrap.append(rangs, plateau, fichiers);

  const panneau = el("div", "panneau");
  const msg = el("p", "msg");
  const promo = el("div", "promo");
  promo.hidden = true;
  const aide = el("p", "aide", "Cliquez sur une pièce, puis sur une case marquée. Roque, prise en passant et promotion sont gérés.");
  const nouveau = el("button", "btn", "Nouvelle partie");
  nouveau.type = "button";
  panneau.append(msg, promo, aide, nouveau);
  zone.append(wrap, panneau);
  racine.appendChild(zone);

  const cases = [];
  for (let i = 0; i < 8; i++) {
    for (let j = 0; j < 8; j++) {
      const b = el("button", "sq " + ((i + j) % 2 === 0 ? "l" : "d"));
      b.type = "button";
      b.setAttribute("aria-label", `${"abcdefgh"[j]}${8 - i}`);
      b.addEventListener("click", () => dessiner(appel("echecs", "clic", [i, j])));
      grille.appendChild(b);
      cases.push(b);
    }
  }

  function dessiner(etat) {
    const coups = new Set(etat.coups.map((c) => c.join(",")));
    const dernier = new Set((etat.dernier || []).map((c) => c.join(",")));
    for (let i = 0; i < 8; i++) {
      for (let j = 0; j < 8; j++) {
        const b = cases[i * 8 + j];
        const p = etat.plateau[i][j];
        const cle = `${i},${j}`;
        b.className = "sq " + ((i + j) % 2 === 0 ? "l" : "d");
        if (dernier.has(cle)) b.classList.add("dernier");
        if (etat.selection && etat.selection[0] === i && etat.selection[1] === j) b.classList.add("sel");
        if (coups.has(cle)) { b.classList.add("cible"); if (p !== ".") b.classList.add("occupe"); }
        if (etat.roi_en_echec && etat.roi_en_echec[0] === i && etat.roi_en_echec[1] === j) b.classList.add("echec");
        b.textContent = "";
        if (p !== ".") {
          const s = el("span", "piece " + (p === p.toUpperCase() ? "w" : "k"), glyphe(p));
          b.appendChild(s);
        }
      }
    }
    msg.textContent = etat.message;
    msg.classList.toggle("fin", !!etat.fin);
    promo.hidden = !etat.promotion;
    if (etat.promotion) {
      promo.innerHTML = "";
      for (const lettre of "QRBN") {
        const l = etat.tour_blanc ? lettre : lettre.toLowerCase();
        const b = el("button", "", glyphe(l));
        b.type = "button";
        b.setAttribute("aria-label", { Q: "Reine", R: "Tour", B: "Fou", N: "Cavalier" }[lettre]);
        const s = b.firstChild;
        b.innerHTML = "";
        b.appendChild(el("span", "piece " + (etat.tour_blanc ? "w" : "k"), s.textContent));
        b.addEventListener("click", () => dessiner(appel("echecs", "promouvoir", [l])));
        promo.appendChild(b);
      }
    }
  }

  nouveau.addEventListener("click", () => dessiner(appel("echecs", "reset")));
  dessiner(appel("echecs", "reset"));
}

// ---------- Jeu de l'oie ----------
const OIES = [5, 9, 14, 18, 23, 27, 32, 36, 41, 45, 50, 54];
const SPECIALES = {
  6: ["PONT", "#7ec8e3", "Pont : va à la case 12"],
  19: ["AUBERGE", "#eec79a", "Auberge : perd 1 tour"],
  31: ["PUITS", "#87ceeb", "Puits"],
  42: ["LABYR.", "#d19be6", "Labyrinthe : recule à la case 39"],
  52: ["PRISON", "#bdbdbd", "Prison : perd 3 tours"],
  58: ["MORT", "#f08080", "Mort : retour au départ"],
  63: ["ARRIVÉE", "#ffd700", "Arrivée"],
};
for (const n of OIES) SPECIALES[n] = ["OIE", "#c7f0c7", "Oie : on rejoue"];

function initiales(nom) {
  return nom.split(/\s+/).filter(Boolean).slice(0, 2).map((m) => m[0]).join("").toUpperCase() || "?";
}

function pionJoueur(j) {
  const p = el("span", "pj", initiales(j.nom));
  p.style.background = j.couleur;
  p.title = j.nom;
  return p;
}

function initOie(racine) {
  racine.innerHTML = "";
  afficherSetup();

  function afficherSetup() {
    racine.innerHTML = "";
    const f = el("form", "setup");
    const lblN = el("label", "", "Nombre de joueurs");
    const sel = el("select");
    for (const n of [2, 3, 4]) sel.appendChild(new Option(String(n), String(n)));
    lblN.appendChild(sel);
    const champs = el("div");
    champs.style.display = "grid";
    champs.style.gap = "1rem";
    function majChamps() {
      champs.innerHTML = "";
      for (let i = 0; i < Number(sel.value); i++) {
        const l = el("label", "", `Nom du joueur ${i + 1}`);
        const inp = el("input");
        inp.type = "text";
        inp.maxLength = 18;
        inp.value = `Joueur ${i + 1}`;
        l.appendChild(inp);
        champs.appendChild(l);
      }
    }
    sel.addEventListener("change", majChamps);
    majChamps();
    const ok = el("button", "btn primary", "Commencer la partie");
    ok.type = "submit";
    f.append(lblN, champs, ok);
    f.addEventListener("submit", (e) => {
      e.preventDefault();
      const noms = [...champs.querySelectorAll("input")].map((i) => i.value);
      demarrer(appel("oie", "creer", [noms]));
    });
    racine.appendChild(f);
  }

  function demarrer(etatInitial) {
    racine.innerHTML = "";
    const zone = el("div", "oie-zone");
    const gauche = el("div", "oie-gauche");
    const plateau = el("div", "oie-plateau");
    const depart = el("div", "depart");
    depart.append(el("span", "lib", "Départ"));
    const pionsDepart = el("div", "pions");
    depart.appendChild(pionsDepart);

    // Cases en serpentin : 9 lignes x 7 colonnes, la case 1 en bas à gauche.
    const pionsCases = {};
    for (let n = 1; n <= 63; n++) {
      const ligne = Math.floor((n - 1) / 7);
      const col = (n - 1) % 7;
      const c = el("div", "case");
      c.style.gridRow = String(9 - ligne);
      c.style.gridColumn = String((ligne % 2 === 0 ? col : 6 - col) + 1);
      c.appendChild(el("span", "num", String(n)));
      const spec = SPECIALES[n];
      if (spec) {
        c.classList.add("spec");
        c.style.setProperty("--teinte", spec[1]);
        c.title = spec[2];
        c.appendChild(el("span", "lib", spec[0]));
      } else {
        c.appendChild(el("span", "lib", ""));
      }
      const pions = el("div", "pions");
      c.appendChild(pions);
      pionsCases[n] = pions;
      plateau.appendChild(c);
    }
    gauche.append(plateau, depart);

    const droite = el("div", "panneau");
    const msg = el("p", "msg");
    const liste = el("ul", "joueurs");
    const des = el("div", "des");
    const lancer = el("button", "btn primary", "Lancer les dés");
    lancer.type = "button";
    const journal = el("ol", "journal");
    const nouveau = el("button", "btn", "Nouvelle partie");
    nouveau.type = "button";
    droite.append(msg, liste, des, lancer, journal, nouveau);
    zone.append(gauche, droite);
    racine.appendChild(zone);

    function dessiner(etat) {
      pionsDepart.innerHTML = "";
      for (const k of Object.keys(pionsCases)) pionsCases[k].innerHTML = "";
      liste.innerHTML = "";
      etat.joueurs.forEach((j, i) => {
        (j.pos === 0 ? pionsDepart : pionsCases[j.pos]).appendChild(pionJoueur(j));
        const li = el("li", i === etat.courant && !etat.gagnant ? "courant" : "");
        const pt = el("span", "pt");
        pt.style.background = j.couleur;
        const nom = el("span", "", `${j.nom} : case ${j.pos}`);
        const e = [];
        if (j.passe > 0) e.push(`passe ${j.passe} tour${j.passe > 1 ? "s" : ""}`);
        if (j.puits) e.push("au puits");
        li.append(pt, nom, el("span", "etat", e.join(" · ")));
        liste.appendChild(li);
      });
      des.innerHTML = "";
      if (etat.des) {
        des.append(el("span", "de", String(etat.des[0])), el("span", "de", String(etat.des[1])),
          el("span", "total", `Total ${etat.des[0] + etat.des[1]}`));
      }
      journal.innerHTML = "";
      for (const l of etat.journal) journal.appendChild(el("li", "", l));
      journal.scrollTop = journal.scrollHeight;
      if (etat.gagnant) {
        msg.textContent = `${etat.gagnant} a gagné la partie !`;
        msg.classList.add("fin");
        lancer.disabled = true;
      } else {
        msg.textContent = `Tour de ${etat.joueurs[etat.courant].nom}`;
        msg.classList.remove("fin");
        lancer.disabled = false;
      }
    }

    lancer.addEventListener("click", () => dessiner(appel("oie", "lancer")));
    nouveau.addEventListener("click", afficherSetup);
    dessiner(etatInitial);
  }
}

// ---------- Onglets ----------
const JEUX = {
  dames: { module: "dames", init: initDames },
  oie: { module: "oie", init: initOie },
  echecs: { module: "echecs", init: initEchecs },
  monopoly: { module: "monopoly", init: initMonopoly },
};
const onglets = [...document.querySelectorAll(".tab")];
let enCours = 0;

async function ouvrirJeu(nom) {
  const jeu = JEUX[nom];
  if (!jeu) return;
  const jeton = ++enCours;
  onglets.forEach((t) => t.setAttribute("aria-selected", String(t.dataset.jeu === nom)));
  for (const n of Object.keys(JEUX)) document.getElementById(`jeu-${n}`).hidden = n !== nom;
  history.replaceState(null, "", location.pathname + `#${nom}`);
  const racine = document.getElementById(`jeu-${nom}`);
  if (jeuxInitialises[nom]) { dire(""); return; }
  try {
    dire(pyodide ? "Chargement du jeu…" : "Chargement de Python dans le navigateur (quelques secondes)…");
    await chargerModule(jeu.module);
    jeu.init(racine);
    jeuxInitialises[nom] = true;
    if (jeton === enCours) dire("");
  } catch (e) {
    console.error(e);
    const local = location.protocol === "file:";
    dire(local
      ? "Ouvre le site depuis GitHub Pages ou un serveur local (par exemple python -m http.server) : le navigateur bloque la lecture des fichiers Python en ouverture directe."
      : `Erreur de chargement : ${e.message}`, true);
  }
}

onglets.forEach((t) => t.addEventListener("click", () => ouvrirJeu(t.dataset.jeu)));
function ouvrirDepuisAdresse() {
  const nom = location.hash.replace("#", "");
  if (JEUX[nom]) ouvrirJeu(nom);
}
window.addEventListener("hashchange", ouvrirDepuisAdresse);
ouvrirDepuisAdresse();
