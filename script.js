// Année du footer
document.getElementById("year").textContent = new Date().getFullYear();

// Thème sombre / clair (sombre par défaut, choix mémorisé si possible)
const root = document.documentElement;
const toggle = document.getElementById("theme-toggle");
const metaTheme = document.querySelector('meta[name="theme-color"]');
function appliquerTheme(theme) {
  root.dataset.theme = theme;
  toggle.innerHTML = theme === "light"
    ? '☾<span class="tlabel"> Sombre</span>'
    : '☀<span class="tlabel"> Clair</span>';
  toggle.setAttribute("aria-label", theme === "light" ? "Passer en thème sombre" : "Passer en thème clair");
  if (metaTheme) metaTheme.content = theme === "light" ? "#f2f2f3" : "#0b0b0d";
}
appliquerTheme(root.dataset.theme === "light" ? "light" : "dark");
toggle.addEventListener("click", () => {
  const next = root.dataset.theme === "light" ? "dark" : "light";
  appliquerTheme(next);
  try { localStorage.setItem("theme", next); } catch (e) {}
});

// Apparition douce des sections au scroll
const items = document.querySelectorAll("section h2, .card, .hero > *, .timeline li");
items.forEach((el) => el.classList.add("reveal"));
const io = new IntersectionObserver((entries) => {
  entries.forEach((e) => {
    if (e.isIntersecting) {
      e.target.classList.add("visible");
      io.unobserve(e.target);
    }
  });
}, { threshold: 0.12 });
items.forEach((el) => io.observe(el));

// Dates des projets : format jj/mm/aaaa, durée calculée en direct
const p2 = (n) => String(n).padStart(2, "0");
const fmt = (d) => `${p2(d.getDate())}/${p2(d.getMonth() + 1)}/${d.getFullYear()}`;
const plur = (n, mot) => `${n} ${mot}${n > 1 && mot !== "mois" ? "s" : ""}`;

function duree(a, b) {
  let mois = (b.getFullYear() - a.getFullYear()) * 12 + (b.getMonth() - a.getMonth());
  let jours = b.getDate() - a.getDate();
  if (jours < 0) {
    mois -= 1;
    jours += new Date(b.getFullYear(), b.getMonth(), 0).getDate();
  }
  const parts = [];
  const ans = Math.floor(mois / 12);
  if (ans) parts.push(plur(ans, "an"));
  if (mois % 12) parts.push(`${mois % 12} mois`);
  if (jours || !parts.length) parts.push(plur(jours, "jour"));
  return parts.join(" et ");
}

const JOUR = 24 * 3600 * 1000;
function fin_de(el) {
  const fini = !!el.dataset.end;
  const b = fini ? new Date(el.dataset.end + "T00:00:00") : new Date();
  b.setHours(0, 0, 0, 0);
  return { b, fini };
}

function majDates() {
  document.querySelectorAll(".date[data-start]").forEach((el) => {
    const a = new Date(el.dataset.start + "T00:00:00");
    const { b, fini } = fin_de(el);
    // Sans date de fin : on affiche la date d'aujourd'hui
    const fin = fini ? fmt(b) : `${fmt(b)} (aujourd'hui)`;
    const dansPeriodes = !!el.closest(".periodes");   // plusieurs périodes : une seule durée, additionnée
    el.textContent = `${fmt(a)} → ${fin}` + (dansPeriodes ? "" : ` · ${duree(a, b)}`);
  });
  // Projets en plusieurs périodes : durée totale = somme des durées de chaque période
  document.querySelectorAll(".periodes").forEach((bloc) => {
    let total = 0, debut = null;
    bloc.querySelectorAll(".date[data-start]").forEach((el) => {
      const a = new Date(el.dataset.start + "T00:00:00");
      total += Math.round((fin_de(el).b - a) / JOUR);
      if (!debut || a < debut) debut = a;
    });
    let t = bloc.querySelector(".total");
    if (!t) { t = document.createElement("span"); t.className = "date total"; bloc.appendChild(t); }
    const fin = new Date(debut.getFullYear(), debut.getMonth(), debut.getDate() + total);
    t.textContent = `Durée totale : ${duree(debut, fin)}`;
  });
}
majDates();
setInterval(majDates, 60 * 1000); // se met à jour si la page reste ouverte après minuit
