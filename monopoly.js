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
  const plateau = el("div", "mono-plateau");
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

  // ---------- plateau ----------
  function placer(i) {
    if (i === 0) return [11, 11];
    if (i < 10) return [11, 11 - i];
    if (i === 10) return [11, 1];
    if (i < 20) return [11 - (i - 10), 1];
    if (i === 20) return [1, 1];
    if (i < 30) return [1, 1 + (i - 20)];
    if (i === 30) return [1, 11];
    return [1 + (i - 30), 11];
  }
  const casesDom = [];
  function construirePlateau() {
    plateau.innerHTML = "";
    casesDom.length = 0;
    ST.forEach((c) => {
      const [ligne, col] = placer(c.i);
      const d = el("div", `mono-case t-${c.type}${c.i % 10 === 0 ? " coin" : ""}`);
      d.style.gridRow = ligne; d.style.gridColumn = col;
      d.tabIndex = 0;
      d.setAttribute("role", "button");
      d.setAttribute("aria-label", c.name);
      if (c.type === "property") {
        const b = el("div", "bande"); b.style.background = c.hex; d.appendChild(b);
      }
      const nom = el("div", "nom", c.short.replace(/\n/g, " "));
      d.appendChild(nom);
      const bas = el("div", "bas");
      if (c.price) bas.textContent = eur(c.price);
      else if (c.type === "tax") bas.textContent = eur(c.amount);
      else if (c.type === "chance") { nom.textContent = "CHANCE"; bas.textContent = "?"; bas.classList.add("grand"); }
      else if (c.type === "community") { bas.textContent = "▣"; bas.classList.add("grand"); }
      else if (c.type === "station") bas.insertAdjacentText("afterbegin", "▤ " + eur(c.price));
      d.appendChild(bas);
      const pions = el("div", "pions"); d.appendChild(pions);
      const prop = el("div", "proprio"); d.appendChild(prop);
      d.addEventListener("mouseenter", () => { survol = c.i; dessinerCarte(); });
      d.addEventListener("focus", () => { survol = c.i; dessinerCarte(); });
      d.addEventListener("click", () => { survol = c.i; dessinerCarte(); });
      plateau.appendChild(d);
      casesDom.push(d);
    });
    const centre = el("div", "mono-centre");
    centre.innerHTML = '<div class="logo-m">MONOPOLY</div><div class="des" id="mono-des"></div>' +
      '<div class="paquets"><div class="paquet caisse"><b>Caisse de communauté</b><span id="mono-cc">—</span></div>' +
      '<div class="paquet chance"><b>Chance</b><span id="mono-ch">—</span></div></div>' +
      '<p class="aide petite">Survolez une case ou un titre pour voir sa carte.</p>';
    plateau.appendChild(centre);
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

    casesDom.forEach((d, i) => {
      const cs = S.cells[i], c = ST[i];
      d.classList.toggle("courant", !S.over && cur.position === i);
      d.classList.toggle("hyp", !!(cs && cs.mortgaged));
      d.classList.toggle("sel", survol === i);
      const prop = d.querySelector(".proprio");
      prop.style.background = cs && cs.owner !== null ? S.players[cs.owner].color : "transparent";
      const bande = d.querySelector(".bande");
      if (bande) {
        bande.innerHTML = "";
        if (cs && cs.houses) {
          if (cs.houses === 5) bande.appendChild(el("i", "hotel"));
          else for (let k = 0; k < cs.houses; k++) bande.appendChild(el("i", "maison"));
        }
      }
      const pions = d.querySelector(".pions");
      pions.innerHTML = "";
      S.players.forEach((p) => {
        if (p.active && p.position === i) {
          const e = el("span", "pion", p.name[0].toUpperCase());
          e.style.background = p.color;
          e.title = p.name + (p.in_jail ? " (en prison)" : "");
          if (p.in_jail) e.classList.add("prison");
          pions.appendChild(e);
        }
      });
    });
    const des = document.getElementById("mono-des");
    des.textContent = `${DES[S.dice[0]] || ""} ${DES[S.dice[1]] || ""}`;
    document.getElementById("mono-cc").textContent = S.last_card.community || "(aucune carte tirée)";
    document.getElementById("mono-ch").textContent = S.last_card.chance || "(aucune carte tirée)";

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
        j.addEventListener("mouseenter", () => { survol = i; dessinerCarte(); });
        j.addEventListener("click", () => { survol = i; dessinerCarte(); });
        chips.appendChild(j);
      });
      if (!p.properties.length && p.active) chips.appendChild(el("span", "aucun", "aucun titre"));
      l.append(nom, val, chips);
      joueurs.appendChild(l);
    });

    journal.innerHTML = "";
    S.log.slice(-60).forEach((t) => journal.appendChild(el("li", null, t)));
    journal.scrollTop = journal.scrollHeight;
    dessinerCarte();
  }

  function dessinerCarte() {
    carte.innerHTML = "";
    if (survol === null || !ST.length) { carte.hidden = true; return; }
    carte.hidden = false;
    casesDom.forEach((d, i) => d.classList.toggle("sel", i === survol));
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
  function maj(res) {
    if (res.statique) { ST = res.statique; construirePlateau(); }
    if (res.etat) { S = res.etat; }
    clearTimeout(minuteur);
    dessiner();
    if (modale && modale.dataset.type === "biens") listeBiens(null);
    else if (S && S.pending && S.pending.type === "funds") listeBiens(S.pending);
    else gererAttente();
    programmerFin();
    if (S && S.over && !classementMontre) { classementMontre = true; ouvrirClassement(true); }
    if (S && !S.over) classementMontre = false;
    return res;
  }
  function agir(methode, args = []) {
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
