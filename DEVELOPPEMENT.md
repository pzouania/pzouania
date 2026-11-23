# Notes de développement

Documentation technique du site (ce fichier n'est pas affiché sur le profil GitHub).

## Technologies

HTML, CSS et JavaScript, sans framework ni étape de build. Polices : Space Grotesk et JetBrains Mono (Google Fonts). Les jeux tournent avec [Pyodide](https://pyodide.org) (Python dans le navigateur). Hébergement : GitHub Pages.

## Structure

```
index.html        page d'accueil du portfolio
jouer.html        page des jeux jouables en ligne
code.html         visionneuse du code Python (coloration, plan, copie)
style.css         styles et palette (variables en haut du fichier)
jouer.css         styles des plateaux
script.js         thème, animations, calcul des durées
jouer.js          interface des jeux et chargement de Pyodide
code.css / code.js  style et script de la visionneuse de code
logo.png          logo PZ (aussi utilisé comme icône d'onglet)
photo.jpg         portrait affiché dans la section À propos (fond détouré, 800 x 1000)
cv/               CV au format PDF
python/           code d'origine des trois jeux (Tkinter)
python/web/       moteurs Python utilisés par la page Jouer
```

## Modifier le site

- **Textes et projets** : modifier `index.html`. Pour ajouter un projet, dupliquer un bloc `<article class="card project">`.
- **Dates des projets** : renseigner `data-start="AAAA-MM-JJ"` et, si le projet est terminé, `data-end="AAAA-MM-JJ"`. L'affichage `jj/mm/aaaa` et la durée sont calculés par `script.js`. Sans date de fin, la date du jour est utilisée.
- **Couleurs** : variables `:root` au début de `style.css`, thème clair dans `:root[data-theme="light"]`.
- **CV** : remplacer `cv/CV_Pierre_Zouania.pdf` en gardant le même nom de fichier.

## Les jeux en ligne

Chaque jeu a un moteur Python dans `python/web/` (même logique que les fichiers Tkinter, sans l'interface) exposant une fonction `api(methode, args)` qui renvoie l'état en JSON. La page `jouer.html` charge Pyodide depuis un CDN, importe le moteur choisi et dessine le plateau en HTML.

Pour tester en local, servir le site (`python -m http.server`, puis `http://localhost:8000/jouer.html`) : en ouvrant le fichier directement, le navigateur bloque la lecture des fichiers Python.

## Mise en ligne avec GitHub Pages

1. Créer un dépôt public nommé `pzouania.github.io`.
2. Y envoyer le contenu du dossier (**Add file → Upload files**), avec `index.html` à la racine, puis **Commit changes**.
3. Dans **Settings → Pages**, choisir **Deploy from a branch**, la branche `main` et le dossier `/ (root)`.
4. Le site est disponible après une à deux minutes.
