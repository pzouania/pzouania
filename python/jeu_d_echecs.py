# Jeu d'Echec amélioré (correction prise en passant)
# - Coordonnées autour de l'échiquier (A-H en haut/bas, 8-1 à gauche/droite)
# - Fenêtre redimensionnable + bouton plein écran (cases adaptatives)
# - Prise en passant (corrigée)
# - Nulle par répétition (3 occurrences identiques -> partie nulle)
#
# Sauvegarde et lance avec Python 3 (Tkinter requis).

import tkinter as tk
from tkinter import messagebox

PIECES = {
    'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚', 'p': '♟',
    'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔', 'P': '♙',
}

PROMOTION_CHOIX = {
    'Reine': ('Q', 'q'),
    'Tour': ('R', 'r'),
    'Fou': ('B', 'b'),
    'Cavalier': ('N', 'n')
}

plateau_initial = [
    ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
    ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
    ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
]

def est_dans_plateau(x, y):
    return 0 <= x < 8 and 0 <= y < 8

def chemin_libre(plateau, start, end):
    x_start, y_start = start
    x_end, y_end = end
    dx = 1 if x_end > x_start else -1 if x_end < x_start else 0
    dy = 1 if y_end > y_start else -1 if y_end < y_start else 0
    x, y = x_start + dx, y_start + dy
    while (x, y) != (x_end, y_end):
        if plateau[x][y] != '.':
            return False
        x += dx
        y += dy
    return True

def mouvement_valide(plateau, start, end, en_passant_target=None):
    x_start, y_start = start
    x_end, y_end = end
    if not est_dans_plateau(x_start, y_start) or not est_dans_plateau(x_end, y_end):
        return False

    piece = plateau[x_start][y_start]
    if piece == '.':
        return False

    couleur = piece.isupper()
    dest_piece = plateau[x_end][y_end]
    if dest_piece != '.' and (dest_piece.isupper() == couleur):
        return False

    dx, dy = abs(x_end - x_start), abs(y_end - y_start)

    if piece.lower() == 'p':  # Pion
        direction = -1 if couleur else 1
        # mouvement vertical
        if y_start == y_end and plateau[x_end][y_end] == '.':
            if dx == 1:
                return x_end == x_start + direction
            elif dx == 2:
                interm_x = x_start + direction
                return (x_start == (6 if couleur else 1)) and plateau[interm_x][y_start] == '.' and x_end == x_start + 2 * direction
            else:
                return False
        # capture normale
        if dx == 1 and dy == 1 and dest_piece != '.' and (dest_piece.isupper() != couleur):
            return x_end == x_start + direction
        # prise en passant : destination vide mais correspond à la cible en_passant_target
        if dx == 1 and dy == 1 and dest_piece == '.' and en_passant_target is not None:
            if (x_end, y_end) == en_passant_target:
                return x_end == x_start + direction
        return False

    if piece.lower() == 'n':  # Cavalier
        return (dx, dy) in [(2, 1), (1, 2)]

    if piece.lower() == 'b':  # Fou
        if dx == dy:
            return chemin_libre(plateau, start, end)
        else:
            return False

    if piece.lower() == 'r':  # Tour
        if x_start == x_end or y_start == y_end:
            return chemin_libre(plateau, start, end)
        else:
            return False

    if piece.lower() == 'q':  # Reine
        if dx == dy or x_start == x_end or y_start == y_end:
            return chemin_libre(plateau, start, end)
        else:
            return False

    if piece.lower() == 'k':  # Roi
        if max(dx, dy) == 1:
            return dest_piece == '.' or dest_piece.isupper() != couleur
        # roque
        if dx == 0 and dy == 2:
            if y_end > y_start:
                if plateau[x_start][y_start+1] != '.' or plateau[x_start][y_start+2] != '.':
                    return False
            else:
                if plateau[x_start][y_start-1] != '.' or plateau[x_start][y_start-2] != '.' or plateau[x_start][y_start-3] != '.':
                    return False
            return True
        return False

    return False

def trouver_roi(plateau, couleur_blanc):
    roi = 'K' if couleur_blanc else 'k'
    for i in range(8):
        for j in range(8):
            if plateau[i][j] == roi:
                return (i, j)
    return None

def est_en_echec(plateau, couleur_blanc, en_passant_target=None):
    roi_pos = trouver_roi(plateau, couleur_blanc)
    if roi_pos is None:
        return True
    for i in range(8):
        for j in range(8):
            piece = plateau[i][j]
            if piece == '.' or piece.isupper() == couleur_blanc:
                continue
            # si une pièce adverse peut bouger sur la position du roi (en prenant en compte en_passant_target)
            if mouvement_valide(plateau, (i, j), roi_pos, en_passant_target):
                return True
    return False

def position_key(plateau, tour_blanc, roque_droit_blanc, roque_gauche_blanc, roque_droit_noir, roque_gauche_noir, en_passant_target):
    rows = [''.join(row) for row in plateau]
    board_str = '/'.join(rows)
    side = 'w' if tour_blanc else 'b'
    castling = ''
    if roque_droit_blanc: castling += 'K'
    if roque_gauche_blanc: castling += 'Q'
    if roque_droit_noir: castling += 'k'
    if roque_gauche_noir: castling += 'q'
    if castling == '': castling = '-'
    ep = f"{en_passant_target[0]}{en_passant_target[1]}" if en_passant_target is not None else '-'
    return f"{board_str} {side} {castling} {ep}"

def coups_possibles(plateau, couleur_blanc, roque_droit_blanc, roque_gauche_blanc, roque_droit_noir, roque_gauche_noir, en_passant_target):
    # renvoie True s'il existe au moins un coup légal
    for i in range(8):
        for j in range(8):
            piece = plateau[i][j]
            if piece == '.' or piece.isupper() != couleur_blanc:
                continue
            for x in range(8):
                for y in range(8):
                    if not mouvement_valide(plateau, (i, j), (x, y), en_passant_target):
                        continue
                    # construire copie et appliquer coup (en tenant compte de en passant)
                    copie = [ligne.copy() for ligne in plateau]
                    piece_deplacee = copie[i][j]
                    # prise en passant sur la copie
                    if piece_deplacee.lower() == 'p' and (x, y) == en_passant_target and plateau[x][y] == '.':
                        copie[x][y] = copie[i][j]
                        copie[i][j] = '.'
                        # le pion capturé se trouve à (i, y)
                        copie[i][y] = '.'
                    else:
                        copie[x][y] = copie[i][j]
                        copie[i][j] = '.'
                    # roque : déplacer la tour sur la copie si nécessaire
                    if piece_deplacee.lower() == 'k' and abs(y - j) == 2:
                        if y > j:
                            copie[i][y-1] = copie[i][7]
                            copie[i][7] = '.'
                        else:
                            copie[i][y+1] = copie[i][0]
                            copie[i][0] = '.'
                    # calculer nouvelle cible en_passant (pour la position résultante)
                    if piece_deplacee.lower() == 'p' and abs(x - i) == 2:
                        interm_x = (x + i) // 2
                        new_en_passant = (interm_x, y)
                    else:
                        new_en_passant = None
                    # vérifier si ce coup laisse le roi en échec (utiliser new_en_passant)
                    if not est_en_echec(copie, couleur_blanc, new_en_passant):
                        return True
    return False

class ChoixPromotion(tk.Toplevel):
    def __init__(self, parent, couleur_blanc, callback):
        super().__init__(parent)
        self.title("Promotion du pion")
        self.geometry("450x100")
        self.resizable(False, False)
        self.callback = callback
        self.couleur_blanc = couleur_blanc
        self.selection = None
        self.transient(parent)
        self.grab_set()

        label = tk.Label(self, text="Choisissez la pièce pour la promotion :")
        label.pack(pady=5)

        frame = tk.Frame(self)
        frame.pack()

        for nom, (maj, minusc) in PROMOTION_CHOIX.items():
            piece = maj if couleur_blanc else minusc
            btn = tk.Button(frame, text=PIECES[piece], width=4, font=("Arial", 24),
                            command=lambda p=piece: self.choisir(p))
            btn.pack(side=tk.LEFT, padx=5)

    def choisir(self, piece):
        self.selection = piece
        self.callback(piece)
        self.destroy()

class Echiquier(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Jeu d'échecs")
        self.geometry("700x700")
        self.resizable(True, True)

        self.plateau = [ligne.copy() for ligne in plateau_initial]
        self.tour_blanc = True
        self.selection = None

        self.roque_droit_blanc = True
        self.roque_gauche_blanc = True
        self.roque_droit_noir = True
        self.roque_gauche_noir = True

        # cible d'en passant actuelle (case où le pion attaquant doit atterrir)
        self.en_passant_target = None

        self.historique_positions = []
        self.push_position_history()

        top_frame = tk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.X)

        self.message = tk.Label(top_frame, text="Tour des Blancs", font=("Arial", 14))
        self.message.pack(side=tk.LEFT, padx=10, pady=6)

        self.bouton_fullscreen = tk.Button(top_frame, text="Plein écran", command=self.toggle_fullscreen)
        self.bouton_fullscreen.pack(side=tk.RIGHT, padx=6)
        self.fullscreen = False

        self.bouton_quitter = tk.Button(top_frame, text="Quitter", command=self.destroy)
        self.bouton_quitter.pack(side=tk.RIGHT, padx=6)

        container = tk.Frame(self)
        container.pack(expand=True, fill=tk.BOTH, padx=8, pady=8)

        for r in range(10):
            container.grid_rowconfigure(r, weight=1)
        for c in range(10):
            container.grid_columnconfigure(c, weight=1)

        self.cases = [[None]*8 for _ in range(8)]
        lettres = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

        for j, lettre in enumerate(lettres, start=1):
            lbl_top = tk.Label(container, text=lettre, font=("Arial", 12))
            lbl_top.grid(row=0, column=j, sticky="nsew")
            lbl_bottom = tk.Label(container, text=lettre, font=("Arial", 12))
            lbl_bottom.grid(row=9, column=j, sticky="nsew")

        for i in range(1, 9):
            rang = 9 - i
            lbl_left = tk.Label(container, text=str(rang), font=("Arial", 12))
            lbl_left.grid(row=i, column=0, sticky="nsew")
            lbl_right = tk.Label(container, text=str(rang), font=("Arial", 12))
            lbl_right.grid(row=i, column=9, sticky="nsew")

        for i in range(8):
            for j in range(8):
                couleur_bg = "#F0D9B5" if (i + j) % 2 == 0 else "#B58863"
                btn = tk.Button(container, text=PIECES.get(self.plateau[i][j], ' '),
                                font=("Arial", 24),
                                bg=couleur_bg,
                                command=lambda x=i, y=j: self.clic_case(x, y))
                btn.grid(row=1 + i, column=1 + j, sticky="nsew")
                self.cases[i][j] = btn

        container.bind("<Configure>", self.on_container_configure)
        self.container = container

        self.promotion_en_cours = False
        self.promotion_case = None

        self.maj_affichage()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.attributes("-fullscreen", self.fullscreen)
        self.bouton_fullscreen.config(text="Quitter plein écran" if self.fullscreen else "Plein écran")

    def on_container_configure(self, event):
        width = event.width
        height = event.height
        cell_w = max(10, int(width / 10))
        cell_h = max(10, int(height / 10))
        size = max(8, int(min(cell_w, cell_h) / 2))
        for i in range(8):
            for j in range(8):
                self.cases[i][j].config(font=("Arial", size))
        self.message.config(font=("Arial", max(10, size//2)))

    def reinit_couleurs(self):
        for i in range(8):
            for j in range(8):
                couleur_bg = "#F0D9B5" if (i + j) % 2 == 0 else "#B58863"
                self.cases[i][j].config(bg=couleur_bg)

    def maj_affichage(self):
        self.reinit_couleurs()
        for i in range(8):
            for j in range(8):
                self.cases[i][j]['text'] = PIECES.get(self.plateau[i][j], ' ')
        roi_pos = trouver_roi(self.plateau, self.tour_blanc)
        if roi_pos and est_en_echec(self.plateau, self.tour_blanc, self.en_passant_target):
            x, y = roi_pos
            self.cases[x][y].config(bg='red')
        joueur = "Blancs" if self.tour_blanc else "Noirs"
        self.message.config(text=f"Tour des {joueur}")

    def push_position_history(self):
        key = position_key(self.plateau, self.tour_blanc,
                           self.roque_droit_blanc, self.roque_gauche_blanc,
                           self.roque_droit_noir, self.roque_gauche_noir,
                           self.en_passant_target)
        self.historique_positions.append(key)

    def clic_case(self, x, y):
        if self.promotion_en_cours:
            return

        piece = self.plateau[x][y]

        if self.selection is None:
            if piece == '.' or (piece.isupper() != self.tour_blanc):
                return
            self.selection = (x, y)
            self.cases[x][y].config(bg="yellow")
        else:
            x_sel, y_sel = self.selection
            if (x, y) == (x_sel, y_sel):
                self.cases[x_sel][y_sel].config(bg="#F0D9B5" if (x_sel + y_sel) % 2 == 0 else "#B58863")
                self.selection = None
                return

            # vérification du mouvement (en passant pris en compte via self.en_passant_target)
            if mouvement_valide(self.plateau, (x_sel, y_sel), (x, y), self.en_passant_target):
                copie = [ligne.copy() for ligne in self.plateau]
                piece_deplacee = copie[x_sel][y_sel]

                # simulation prise en passant sur la copie
                if piece_deplacee.lower() == 'p' and (x, y) == self.en_passant_target and copie[x][y] == '.':
                    copie[x][y] = copie[x_sel][y_sel]
                    copie[x_sel][y_sel] = '.'
                    capture_x = x_sel
                    capture_y = y
                    copie[capture_x][capture_y] = '.'
                else:
                    copie[x][y] = copie[x_sel][y_sel]
                    copie[x_sel][y_sel] = '.'

                # simulation roque sur copie
                if piece_deplacee.lower() == 'k' and abs(y - y_sel) == 2:
                    if y > y_sel:
                        copie[x][y-1] = copie[x][7]
                        copie[x][7] = '.'
                    else:
                        copie[x][y+1] = copie[x][0]
                        copie[x][0] = '.'

                # calculer nouvelle cible en_passant pour la position résultante
                if piece_deplacee.lower() == 'p' and abs(x - x_sel) == 2:
                    interm_x = (x + x_sel) // 2
                    new_en_passant = (interm_x, y)
                else:
                    new_en_passant = None

                # vérifier que le coup ne laisse pas le roi en échec (en tenant compte de new_en_passant)
                if est_en_echec(copie, self.tour_blanc, new_en_passant):
                    # coup illégal car roi en échec après
                    return

                # Appliquer le coup sur le vrai plateau (prise en passant gérée)
                if piece_deplacee.lower() == 'p' and (x, y) == self.en_passant_target and self.plateau[x][y] == '.':
                    self.plateau[x][y] = self.plateau[x_sel][y_sel]
                    self.plateau[x_sel][y_sel] = '.'
                    capture_x = x_sel
                    capture_y = y
                    self.plateau[capture_x][capture_y] = '.'
                else:
                    self.plateau[x][y] = self.plateau[x_sel][y_sel]
                    self.plateau[x_sel][y_sel] = '.'

                # si roque, déplacer la tour sur le vrai plateau
                if piece_deplacee.lower() == 'k' and abs(y - y_sel) == 2:
                    if y > y_sel:
                        self.plateau[x][y-1] = self.plateau[x][7]
                        self.plateau[x][7] = '.'
                    else:
                        self.plateau[x][y+1] = self.plateau[x][0]
                        self.plateau[x][0] = '.'

                # Mise à jour droits de roque
                if piece_deplacee.lower() == 'k':
                    if self.tour_blanc:
                        self.roque_droit_blanc = False
                        self.roque_gauche_blanc = False
                    else:
                        self.roque_droit_noir = False
                        self.roque_gauche_noir = False
                elif piece_deplacee.lower() == 'r':
                    if self.tour_blanc:
                        if (x_sel, y_sel) == (7, 0):
                            self.roque_gauche_blanc = False
                        elif (x_sel, y_sel) == (7, 7):
                            self.roque_droit_blanc = False
                    else:
                        if (x_sel, y_sel) == (0, 0):
                            self.roque_gauche_noir = False
                        elif (x_sel, y_sel) == (0, 7):
                            self.roque_droit_noir = False

                # Définir nouvelle cible d'en passant (si pion a avancé de 2 cases)
                if piece_deplacee.lower() == 'p' and abs(x - x_sel) == 2:
                    interm_x = (x + x_sel) // 2
                    self.en_passant_target = (interm_x, y)
                else:
                    self.en_passant_target = None

                # Promotion
                if piece_deplacee.lower() == 'p':
                    if (self.tour_blanc and x == 0) or (not self.tour_blanc and x == 7):
                        self.promotion_en_cours = True
                        self.promotion_case = (x, y)
                        self.selection = None
                        self.maj_affichage()
                        self.choix_promotion()
                        return

                # Fin du tour
                self.tour_blanc = not self.tour_blanc
                self.push_position_history()
                self.selection = None
                self.maj_affichage()

                # Vérifications d'échec/mat/pat
                if est_en_echec(self.plateau, self.tour_blanc, self.en_passant_target):
                    if not coups_possibles(self.plateau, self.tour_blanc,
                                          self.roque_droit_blanc, self.roque_gauche_blanc,
                                          self.roque_droit_noir, self.roque_gauche_noir,
                                          self.en_passant_target):
                        messagebox.showinfo("Échec et Mat", f"Les {'Blancs' if not self.tour_blanc else 'Noirs'} ont gagné !")
                        self.destroy()
                        return
                    else:
                        messagebox.showinfo("Échec", "Échec !")
                else:
                    if not coups_possibles(self.plateau, self.tour_blanc,
                                           self.roque_droit_blanc, self.roque_gauche_blanc,
                                           self.roque_droit_noir, self.roque_gauche_noir,
                                           self.en_passant_target):
                        messagebox.showinfo("Pat", "Partie nulle par pat.")
                        self.destroy()
                        return

            else:
                self.cases[x_sel][y_sel].config(bg="#F0D9B5" if (x_sel + y_sel) % 2 == 0 else "#B58863")
                self.selection = None

    def choix_promotion(self):
        def callback(piece_choisie):
            x, y = self.promotion_case
            self.plateau[x][y] = piece_choisie
            self.promotion_en_cours = False
            self.promotion_case = None
            # Fin du tour après promotion
            self.tour_blanc = not self.tour_blanc

        choix = ChoixPromotion(self, self.tour_blanc, callback)
        choix.wait_window()

if __name__ == "__main__":
    app = Echiquier()
    app.mainloop()
