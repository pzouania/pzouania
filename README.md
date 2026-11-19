# Portfolio — Pierre Zouania

Portfolio personnel d'un étudiant en BUT Science des données (IUT Nice Côte d'Azur, Valbonne), futur développeur de jeux vidéo.

Site en ligne : https://pzouania.github.io

## Contenu

- **À propos** et **compétences** : programmation, outils, données, langues (barres de niveau), savoir-être.
- **Projets informatiques**, avec dates et durées calculées automatiquement :
  - Jeux de plateau en Python (dames, oie, échecs), du 20/02/2025 au 30/05/2025.
  - Calendraft V0, du 30/01/2026 au 11/09/2026.
  - Calendraft V1, depuis le 22/09/2026.
- **Parcours** : formation et expériences.
- **Contact** : e-mail, GitHub, LinkedIn et CV téléchargeable.

## Technologies

HTML, CSS et JavaScript, sans framework ni étape de build. Polices : Space Grotesk et JetBrains Mono (Google Fonts). Hébergement : GitHub Pages.

Style : tech monochrome, acier brossé, coins coupés à 45°, traces de circuit, fond très sombre.

## Structure

```
index.html        page unique du site
style.css         styles et palette (variables en haut du fichier)
script.js         animations, année du pied de page, calcul des durées
logo.png          logo PZ (aussi utilisé comme icône d'onglet)
cv/               CV au format PDF
python/           code source des trois jeux Python
```

## Modifier le site

- **Textes et projets** : modifier `index.html`. Pour ajouter un projet, dupliquer un bloc `<article class="card project">`.
- **Dates des projets** : renseigner `data-start="AAAA-MM-JJ"` et, si le projet est terminé, `data-end="AAAA-MM-JJ"`. L'affichage `jj/mm/aaaa` et la durée sont calculés par `script.js`. Sans date de fin, la date du jour est utilisée.
- **Couleurs** : variables `:root` au début de `style.css`.
- **CV** : remplacer `cv/CV_Pierre_Zouania.pdf` en gardant le même nom de fichier.

## Mettre en ligne avec GitHub Pages

1. Créer un dépôt public nommé `pzouania.github.io`.
2. Y envoyer le contenu du dossier (**Add file → Upload files**), avec `index.html` à la racine, puis **Commit changes**.
3. Dans **Settings → Pages**, choisir **Deploy from a branch**, la branche `main` et le dossier `/ (root)`.
4. Le site est disponible après une à deux minutes.

Avec Git en ligne de commande :

```bash
git init
git add .
git commit -m "Portfolio"
git branch -M main
git remote add origin https://github.com/pzouania/pzouania.github.io.git
git push -u origin main
```

## Contact

pzouania@gmail.com · [GitHub](https://github.com/pzouania) · [LinkedIn](https://www.linkedin.com/in/pierre-zouania-0696a0435/)
