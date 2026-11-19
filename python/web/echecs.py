"""Moteur du jeu d'échecs pour le site web.

Reprend la logique de Jeu_d_Echec.py (sans Tkinter). La page web appelle
api(methode, args) et reçoit l'état en JSON.

Par rapport à la version Tkinter, quelques cas limites sont corrigés :
- le roque exige que le roi et la tour n'aient pas bougé, que le roi ne soit
  pas en échec et ne traverse pas une case attaquée ;
- un roi n'est plus considéré comme "attaquant" deux cases plus loin ;
- la fin du tour après une promotion est gérée (échec, mat, pat) ;
- la nulle par répétition (3 fois la même position) est détectée.
"""

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
        if y_start == y_end and plateau[x_end][y_end] == '.':
            if dx == 1:
                return x_end == x_start + direction
            elif dx == 2:
                interm_x = x_start + direction
                return (x_start == (6 if couleur else 1)) and plateau[interm_x][y_start] == '.' and x_end == x_start + 2 * direction
            else:
                return False
        if dx == 1 and dy == 1 and dest_piece != '.' and (dest_piece.isupper() != couleur):
            return x_end == x_start + direction
        if dx == 1 and dy == 1 and dest_piece == '.' and en_passant_target is not None:
            if (x_end, y_end) == en_passant_target:
                return x_end == x_start + direction
        return False

    if piece.lower() == 'n':  # Cavalier
        return (dx, dy) in [(2, 1), (1, 2)]

    if piece.lower() == 'b':  # Fou
        return dx == dy and chemin_libre(plateau, start, end)

    if piece.lower() == 'r':  # Tour
        return (x_start == x_end or y_start == y_end) and chemin_libre(plateau, start, end)

    if piece.lower() == 'q':  # Reine
        return (dx == dy or x_start == x_end or y_start == y_end) and chemin_libre(plateau, start, end)

    if piece.lower() == 'k':  # Roi
        if max(dx, dy) == 1:
            return dest_piece == '.' or dest_piece.isupper() != couleur
        # roque : roi sur sa case de départ, tour en place, cases libres
        if dx == 0 and dy == 2 and dest_piece == '.':
            if x_start != (7 if couleur else 0) or y_start != 4:
                return False
            tour = 'R' if couleur else 'r'
            if y_end > y_start:
                return (plateau[x_start][7] == tour and plateau[x_start][5] == '.'
                        and plateau[x_start][6] == '.')
            return (plateau[x_start][0] == tour and plateau[x_start][1] == '.'
                    and plateau[x_start][2] == '.' and plateau[x_start][3] == '.')
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
            if mouvement_valide(plateau, (i, j), roi_pos, en_passant_target):
                return True
    return False


def appliquer_coup(plateau, start, end, en_passant_target):
    """Renvoie (copie du plateau après le coup, nouvelle cible d'en passant)."""
    x1, y1 = start
    x2, y2 = end
    copie = [ligne.copy() for ligne in plateau]
    piece = copie[x1][y1]
    if piece.lower() == 'p' and (x2, y2) == en_passant_target and copie[x2][y2] == '.' and y1 != y2:
        copie[x1][y2] = '.'
    copie[x2][y2] = piece
    copie[x1][y1] = '.'
    if piece.lower() == 'k' and abs(y2 - y1) == 2:
        if y2 > y1:
            copie[x2][y2 - 1] = copie[x2][7]
            copie[x2][7] = '.'
        else:
            copie[x2][y2 + 1] = copie[x2][0]
            copie[x2][0] = '.'
    nouveau_ep = ((x1 + x2) // 2, y1) if piece.lower() == 'p' and abs(x2 - x1) == 2 else None
    return copie, nouveau_ep


def position_key(plateau, tour_blanc, roques, en_passant_target):
    board_str = '/'.join(''.join(row) for row in plateau)
    side = 'w' if tour_blanc else 'b'
    castling = ''.join(c for c in 'KQkq' if roques[c]) or '-'
    ep = f"{en_passant_target[0]}{en_passant_target[1]}" if en_passant_target is not None else '-'
    return f"{board_str} {side} {castling} {ep}"


PROMOTION = {True: 'QRBN', False: 'qrbn'}


class Partie:
    def __init__(self):
        self.reset()

    def reset(self):
        self.plateau = [ligne.copy() for ligne in plateau_initial]
        self.tour_blanc = True
        self.selection = None
        self.coups = []
        self.roques = {'K': True, 'Q': True, 'k': True, 'q': True}
        self.en_passant = None
        self.promotion_case = None
        self.dernier = None
        self.fin = None
        self.echec = False
        self.historique = []
        self.historique.append(self.cle())

    def cle(self):
        return position_key(self.plateau, self.tour_blanc, self.roques, self.en_passant)

    # ----- légalité -----
    def coup_legal(self, start, end):
        x1, y1 = start
        x2, y2 = end
        piece = self.plateau[x1][y1]
        couleur = piece.isupper()
        if not mouvement_valide(self.plateau, start, end, self.en_passant):
            return False
        if piece.lower() == 'k' and abs(y2 - y1) == 2:
            droit = self.roques[('K' if y2 > y1 else 'Q') if couleur else ('k' if y2 > y1 else 'q')]
            if not droit or est_en_echec(self.plateau, couleur, self.en_passant):
                return False
            test = [ligne.copy() for ligne in self.plateau]
            test[x1][y1] = '.'
            test[x1][(y1 + y2) // 2] = piece
            if est_en_echec(test, couleur, None):
                return False
        copie, nouveau_ep = appliquer_coup(self.plateau, start, end, self.en_passant)
        return not est_en_echec(copie, couleur, nouveau_ep)

    def coups_legaux(self, x, y):
        return [(i, j) for i in range(8) for j in range(8) if self.coup_legal((x, y), (i, j))]

    def a_un_coup(self, couleur_blanc):
        for i in range(8):
            for j in range(8):
                piece = self.plateau[i][j]
                if piece == '.' or piece.isupper() != couleur_blanc:
                    continue
                if self.coups_legaux(i, j):
                    return True
        return False

    # ----- déroulement -----
    def clic(self, x, y):
        if self.fin or self.promotion_case:
            return
        piece = self.plateau[x][y]
        if self.selection is None:
            if piece != '.' and piece.isupper() == self.tour_blanc:
                self.selection = (x, y)
                self.coups = self.coups_legaux(x, y)
            return
        if (x, y) == self.selection:
            self.selection, self.coups = None, []
        elif (x, y) in self.coups:
            self.jouer(self.selection, (x, y))
        elif piece != '.' and piece.isupper() == self.tour_blanc:
            self.selection = (x, y)
            self.coups = self.coups_legaux(x, y)
        else:
            self.selection, self.coups = None, []

    def jouer(self, start, end):
        x1, y1 = start
        x2, y2 = end
        piece = self.plateau[x1][y1]
        self.plateau, self.en_passant = appliquer_coup(self.plateau, start, end, self.en_passant)
        self.dernier = [list(start), list(end)]

        if piece == 'K':
            self.roques['K'] = self.roques['Q'] = False
        elif piece == 'k':
            self.roques['k'] = self.roques['q'] = False
        for case, droit in (((7, 0), 'Q'), ((7, 7), 'K'), ((0, 0), 'q'), ((0, 7), 'k')):
            if start == case or end == case:
                self.roques[droit] = False

        self.selection, self.coups = None, []
        if piece.lower() == 'p' and x2 in (0, 7):
            self.promotion_case = (x2, y2)
            return
        self.finir_tour()

    def promouvoir(self, lettre):
        if not self.promotion_case:
            return
        autorisees = PROMOTION[self.tour_blanc]
        if lettre not in autorisees:
            return
        x, y = self.promotion_case
        self.plateau[x][y] = lettre
        self.promotion_case = None
        self.finir_tour()

    def finir_tour(self):
        self.tour_blanc = not self.tour_blanc
        cle = self.cle()
        self.historique.append(cle)
        self.echec = est_en_echec(self.plateau, self.tour_blanc, self.en_passant)
        peut_jouer = self.a_un_coup(self.tour_blanc)
        if not peut_jouer:
            if self.echec:
                gagnant = "Noirs" if self.tour_blanc else "Blancs"
                self.fin = f"Échec et mat : les {gagnant} gagnent !"
            else:
                self.fin = "Pat : partie nulle."
        elif self.historique.count(cle) >= 3:
            self.fin = "Partie nulle par répétition de position."

    def message(self):
        if self.fin:
            return self.fin
        if self.promotion_case:
            return "Choisissez la pièce de promotion."
        joueur = "Blancs" if self.tour_blanc else "Noirs"
        return f"Échec ! Tour des {joueur}" if self.echec else f"Tour des {joueur}"

    def etat(self):
        roi = trouver_roi(self.plateau, self.tour_blanc) if self.echec else None
        return {
            "plateau": self.plateau,
            "tour_blanc": self.tour_blanc,
            "selection": list(self.selection) if self.selection else None,
            "coups": [list(c) for c in self.coups],
            "promotion": self.promotion_case is not None,
            "roi_en_echec": list(roi) if roi else None,
            "dernier": self.dernier,
            "fin": self.fin,
            "message": self.message(),
        }


_partie = Partie()


def api(methode, args):
    if methode == "reset":
        _partie.reset()
    elif methode == "clic":
        _partie.clic(int(args[0]), int(args[1]))
    elif methode == "promouvoir":
        _partie.promouvoir(str(args[0]))
    return _partie.etat()
