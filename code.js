/* Visionneuse de code Python : coloration maison, plan, copie, lien vers une ligne */
(function () {
  "use strict";
  var FICHIERS = [
    { id: "dames",  titre: "Jeu de dames",  sous: "Tkinter", chemin: "python/jeu_de_dames.py",  jeu: "dames",  desc: "Version d'origine, avec l'interface Tkinter (20/02/2025 – 30/05/2025)." },
    { id: "oie",    titre: "Jeu de l'oie",  sous: "Tkinter", chemin: "python/jeu_de_l_oie.py",  jeu: "oie",    desc: "Version d'origine, avec l'interface Tkinter (20/02/2025 – 30/05/2025)." },
    { id: "echecs", titre: "Jeu d'échecs",  sous: "Tkinter", chemin: "python/jeu_d_echecs.py",  jeu: "echecs", desc: "Version d'origine, avec l'interface Tkinter (20/02/2025 – 30/05/2025)." },
    { id: "dames-web",  titre: "Dames",  sous: "moteur web",  chemin: "python/web/dames.py",  jeu: "dames",  desc: "Moteur de règles sans interface, exécuté dans le navigateur par Pyodide." },
    { id: "oie-web",    titre: "Oie",    sous: "moteur web",  chemin: "python/web/oie.py",    jeu: "oie",    desc: "Moteur de règles sans interface, exécuté dans le navigateur par Pyodide." },
    { id: "echecs-web", titre: "Échecs", sous: "moteur web",  chemin: "python/web/echecs.py", jeu: "echecs", desc: "Moteur de règles sans interface, exécuté dans le navigateur par Pyodide." }
  ];
  var MOTS = "False None True and as assert async await break class continue def del elif else except finally for from global if import in is lambda nonlocal not or pass raise return try while with yield match case".split(" ");
  var INTEGRES = "print len range int str float list dict set tuple bool self cls super isinstance enumerate zip map filter sorted sum min max abs round open input type any all reversed iter next repr format divmod".split(" ");
  var K = {}, B = {}; MOTS.forEach(function (m) { K[m] = 1; }); INTEGRES.forEach(function (m) { B[m] = 1; });
  var RE = /("""[\s\S]*?"""|'''[\s\S]*?''')|((?:[rRbBfFuU]{1,2})?(?:"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*'))|(#[^\n]*)|(@[A-Za-z_][\w.]*)|(\b\d[\d_]*\.?\d*(?:[eE][+-]?\d+)?\b)|([A-Za-z_]\w*)|(\n)|([^\S\n]+)|([\s\S])/g;

  function esc(s) { return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }

  function colorier(src) {
    var lignes = [[]], m, apresDef = false;
    function pousser(type, txt) {
      var parts = txt.split("\n");
      for (var i = 0; i < parts.length; i++) {
        if (i > 0) lignes.push([]);
        if (parts[i] !== "") lignes[lignes.length - 1].push(type ? '<span class="' + type + '">' + esc(parts[i]) + "</span>" : esc(parts[i]));
      }
    }
    RE.lastIndex = 0;
    while ((m = RE.exec(src))) {
      if (m[1]) { pousser("s", m[1]); apresDef = false; }
      else if (m[2]) { pousser("s", m[2]); apresDef = false; }
      else if (m[3]) pousser("c", m[3]);
      else if (m[4]) pousser("a", m[4]);
      else if (m[5]) { pousser("d", m[5]); apresDef = false; }
      else if (m[6]) {
        var w = m[6];
        if (apresDef) { pousser("f", w); apresDef = false; }
        else if (K[w]) { pousser("k", w); apresDef = (w === "def" || w === "class"); }
        else if (B[w]) pousser("b", w);
        else pousser("", w);
      }
      else if (m[7]) pousser("", "\n");
      else pousser("", m[0] || m[8] || m[9]);
    }
    return lignes.map(function (l) { return l.join(""); });
  }

  var $ = function (id) { return document.getElementById(id); };
  var zone = $("zone-code"), plan = $("plan"), tabs = $("fichiers"), courant = null, texte = "", cache = {};
  var taille = 13;
  try { taille = parseInt(localStorage.getItem("codeTaille"), 10) || 13; } catch (e) {}
  zone.style.setProperty("--taille", taille + "px");

  FICHIERS.forEach(function (f) {
    var b = document.createElement("button");
    b.className = "tab"; b.type = "button"; b.setAttribute("role", "tab"); b.dataset.id = f.id;
    b.innerHTML = esc(f.titre) + "<small>" + esc(f.sous) + "</small>";
    b.addEventListener("click", function () { ouvrir(f.id, true); });
    tabs.appendChild(b);
  });

  function idDepuisAdresse() {
    var h = (location.hash || "").replace("#", "").split("-L")[0].split(":")[0];
    return FICHIERS.some(function (f) { return f.id === h; }) ? h : "dames";
  }
  function ligneDepuisAdresse() { var m = /[:-]L(\d+)$/.exec(location.hash || ""); return m ? +m[1] : 0; }

  function ouvrir(id, majAdresse) {
    var f = FICHIERS.filter(function (x) { return x.id === id; })[0] || FICHIERS[0];
    courant = f;
    Array.prototype.forEach.call(tabs.children, function (b) { b.setAttribute("aria-selected", b.dataset.id === f.id ? "true" : "false"); });
    $("ide-path").textContent = f.chemin;
    $("b-dl").href = f.chemin; $("b-dl").setAttribute("download", f.chemin.split("/").pop());
    $("b-jouer").href = "jouer.html#" + f.jeu;
    $("desc").textContent = f.desc;
    if (majAdresse) history.replaceState(null, "", "#" + f.id);
    if (cache[f.chemin]) return afficher(cache[f.chemin]);
    zone.innerHTML = '<p class="vide">Chargement…</p>'; plan.innerHTML = "";
    fetch(f.chemin).then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); })
      .then(function (t) { cache[f.chemin] = t; if (courant === f) afficher(t); })
      .catch(function () { zone.innerHTML = '<p class="vide">Impossible de charger ce fichier. <a class="link" href="' + f.chemin + '">Ouvrir le fichier brut →</a></p>'; });
  }

  function afficher(t) {
    texte = t.replace(/\r\n?/g, "\n").replace(/\n$/, "");
    var lg = colorier(texte), h = '<div class="code-lignes">';
    for (var i = 0; i < lg.length; i++) h += '<div class="ln" id="L' + (i + 1) + '"><span class="n" data-l="' + (i + 1) + '">' + (i + 1) + '</span><span class="t">' + (lg[i] || " ") + "</span></div>";
    zone.innerHTML = h + "</div>";
    $("ide-meta").textContent = lg.length + " lignes · " + Math.max(1, Math.round(new Blob([texte]).size / 102.4) / 10) + " Ko";
    construirePlan(texte.split("\n"));
    var l = ligneDepuisAdresse(); if (l) aller(l);
  }

  function construirePlan(lignes) {
    plan.innerHTML = "";
    lignes.forEach(function (ln, i) {
      var m = /^(\s*)(class|def)\s+([A-Za-z_]\w*)/.exec(ln);
      if (!m) return;
      var li = document.createElement("li"), b = document.createElement("button");
      b.type = "button"; b.title = "Ligne " + (i + 1);
      b.className = m[2] === "class" ? "classe" : (m[1].length ? "meth" : "");
      b.textContent = (m[2] === "class" ? "class " : "def ") + m[3];
      b.addEventListener("click", function () { aller(i + 1); });
      li.appendChild(b); plan.appendChild(li);
    });
    if (!plan.children.length) plan.innerHTML = '<li><button type="button" disabled>(aucune fonction)</button></li>';
  }

  function aller(n) {
    var ancien = zone.querySelector(".cible"); if (ancien) ancien.classList.remove("cible");
    var el = $("L" + n); if (!el) return;
    el.classList.add("cible");
    zone.scrollTop = Math.max(0, el.offsetTop - 60);
    if (courant) history.replaceState(null, "", "#" + courant.id + "-L" + n);
  }

  zone.addEventListener("click", function (e) { var n = e.target.closest && e.target.closest(".n"); if (n) aller(+n.dataset.l); });

  $("b-copier").addEventListener("click", function () {
    var b = this;
    function ok() { b.textContent = "Copié ✓"; setTimeout(function () { b.textContent = "Copier"; }, 1500); }
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(texte).then(ok, function () { b.textContent = "Échec"; });
    else { var ta = document.createElement("textarea"); ta.value = texte; document.body.appendChild(ta); ta.select(); try { document.execCommand("copy"); ok(); } catch (x) {} ta.remove(); }
  });
  function changeTaille(d) {
    taille = Math.min(20, Math.max(10, taille + d)); zone.style.setProperty("--taille", taille + "px");
    try { localStorage.setItem("codeTaille", taille); } catch (e) {}
  }
  $("b-plus").addEventListener("click", function () { changeTaille(1); });
  $("b-moins").addEventListener("click", function () { changeTaille(-1); });
  $("b-wrap").addEventListener("click", function () {
    var on = zone.classList.toggle("wrap"); this.setAttribute("aria-pressed", on ? "true" : "false");
  });
  window.addEventListener("hashchange", function () { var id = idDepuisAdresse(); if (!courant || id !== courant.id) ouvrir(id, false); else { var l = ligneDepuisAdresse(); if (l) aller(l); } });

  ouvrir(idDepuisAdresse(), false);
})();
