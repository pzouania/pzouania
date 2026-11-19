# Portfolio — Pierre Zouania

Site statique (HTML / CSS / JS), sans dépendance ni étape de build.

## Mettre en ligne avec GitHub Pages

1. Crée un dépôt sur GitHub. Pour une adresse du type `https://pzouania.github.io`, nomme-le exactement `pzouania.github.io`.
2. Envoie-y ces fichiers :
   ```bash
   git init
   git add .
   git commit -m "Premier commit du portfolio"
   git branch -M main
   git remote add origin https://github.com/pzouania/pzouania.github.io.git
   git push -u origin main
   ```
3. Sur GitHub : **Settings → Pages → Build and deployment → Source : Deploy from a branch**, branche `main`, dossier `/ (root)`.
4. Après une minute environ, le site est en ligne.

## À personnaliser

- `index.html` : textes et projets.
- `style.css` : couleurs dans le bloc `:root` en haut du fichier.
- Pour ajouter un projet : duplique un bloc `<article class="card project">`.
