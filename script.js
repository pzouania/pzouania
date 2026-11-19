// Année du footer
document.getElementById("year").textContent = new Date().getFullYear();

// Thème clair / sombre (mémorisé si possible)
const root = document.documentElement;
try {
  const saved = localStorage.getItem("theme");
  if (saved) root.dataset.theme = saved;
} catch (e) {}

document.getElementById("theme-toggle").addEventListener("click", () => {
  const next = root.dataset.theme === "light" ? "dark" : "light";
  root.dataset.theme = next;
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

function majDates() {
  document.querySelectorAll(".date[data-start]").forEach((el) => {
    const a = new Date(el.dataset.start + "T00:00:00");
    const fini = !!el.dataset.end;
    const b = fini ? new Date(el.dataset.end + "T00:00:00") : new Date();
    b.setHours(0, 0, 0, 0);
    // Sans date de fin : on affiche la date d'aujourd'hui
    const fin = fini ? fmt(b) : `${fmt(b)} (aujourd'hui)`;
    el.textContent = `${fmt(a)} → ${fin} · ${duree(a, b)}`;
  });
}
majDates();
setInterval(majDates, 60 * 1000); // se met à jour si la page reste ouverte après minuit
