"""Moteur du jeu de dames pour le site web.

Reprend la logique de Jeu_de_Dame.py (sans Tkinter). L'interface est dessinée
par la page web, qui appelle api(methode, args) et reçoit l'état en JSON.
"""

plateau_initial = [
    ['.', 'p', '.', 'p', '.', 'p', '.', 'p'],
    ['p', '.', 'p', '.', 'p', '.', 'p', '.'],
    ['.', 'p', '.', 'p', '.', 'p', '.', 'p'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['P', '.', 'P', '.', 'P', '.', 'P', '.'],
    ['.', 'P', '.', 'P', '.', 'P', '.', 'P'],
    ['P', '.', 'P', '.', 'P', '.', 'P', '.']
]


def est_dans_plateau(x, y):
    return 0 <= x < 8 and 0 <= y < 8


def captures_pion(plateau, x, y):
    piece = plateau[x][y]
    coups = []
    directions = [(-2, -2), (-2, 2)] if piece == 'P' else [(2, -2), (2, 2)]
    for dx, dy in directions:
        x2, y2 = x + dx, y + dy
        xm, ym = x + dx // 2, y + dy // 2
        if est_dans_plateau(x2, y2) and plateau[x2][y2] == '.':
            if plateau[xm][ym] != '.' and plateau[xm][ym].isupper() != piece.isupper():
                coups.append((x2, y2))
    return coups


def captures_dame(plateau, x, y):
    piece = plateau[x][y]
    coups = []
    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        while est_dans_plateau(nx, ny) and plateau[nx][ny] == '.':
            nx += dx
            ny += dy
        if est_dans_plateau(nx, ny) and plateau[nx][ny] != '.' and plateau[nx][ny].isupper() != piece.isupper():
            nx2, ny2 = nx + dx, ny + dy
            while est_dans_plateau(nx2, ny2) and plateau[nx2][ny2] == '.':
                coups.append((nx2, ny2))
                nx2 += dx
                ny2 += dy
    return coups


def coups_possibles_piece(plateau, x, y, capture_seulement=False):
    piece = plateau[x][y]
    coups = []

    if piece in ('P', 'p'):
        if capture_seulement:
            return captures_pion(plateau, x, y)
        dx = -1 if piece == 'P' else 1
        for dy in [-1, 1]:
            nx, ny = x + dx, y + dy
            if est_dans_plateau(nx, ny) and plateau[nx][ny] == '.':
                coups.append((nx, ny))
        coups.extend(captures_pion(plateau, x, y))
    else:
        if capture_seulement:
            return captures_dame(plateau, x, y)
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            while est_dans_plateau(nx, ny) and plateau[nx][ny] == '.':
                coups.append((nx, ny))
                nx += dx
                ny += dy
        coups.extend(captures_dame(plateau, x, y))
    return coups


def toutes_captures_obligatoires(plateau, joueur_blanc):
    captures = []
    for i in range(8):
        for j in range(8):
            piece = plateau[i][j]
            if piece == '.' or piece.isupper() != joueur_blanc:
                continue
            c = coups_possibles_piece(plateau, i, j, capture_seulement=True)
            if c:
                captures.append(((i, j), c))
    return captures


def deplacer(plateau, start, end):
    x1, y1 = start
    x2, y2 = end
    piece = plateau[x1][y1]
    plateau[x2][y2] = piece
    plateau[x1][y1] = '.'

    # capture
    if abs(x2 - x1) >= 2:
        dx = (x2 - x1) // abs(x2 - x1)
        dy = (y2 - y1) // abs(y2 - y1)
        nx, ny = x1 + dx, y1 + dy
        while (nx, ny) != (x2, y2):
            if plateau[nx][ny] != '.':
                plateau[nx][ny] = '.'
                break
            nx += dx
            ny += dy

    # promotion
    if piece == 'P' and x2 == 0:
        plateau[x2][y2] = 'D'
    elif piece == 'p' and x2 == 7:
        plateau[x2][y2] = 'd'


def joueur_peut_jouer(plateau, joueur_blanc):
    for i in range(8):
        for j in range(8):
            piece = plateau[i][j]
            if piece == '.' or piece.isupper() != joueur_blanc:
                continue
            if coups_possibles_piece(plateau, i, j):
                return True
    return False


class Partie:
    """État d'une partie (équivalent de la classe Dames de l'interface Tkinter)."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.plateau = [ligne.copy() for ligne in plateau_initial]
        self.tour_blanc = True
        self.selection = None
        self.coups = []
        self.multi = False
        self.fin = None

    def message(self):
        if self.fin:
            return self.fin
        joueur = "Blancs" if self.tour_blanc else "Noirs"
        if self.multi:
            joueur += " (capture multiple)"
        return f"Tour des {joueur}"

    def verifier_fin(self):
        blancs = any(p.isupper() for ligne in self.plateau for p in ligne)
        noirs = any(p.islower() for ligne in self.plateau for p in ligne)
        if not blancs:
            self.fin = "Fin de partie : les Noirs gagnent !"
        elif not noirs:
            self.fin = "Fin de partie : les Blancs gagnent !"
        elif not joueur_peut_jouer(self.plateau, self.tour_blanc):
            gagnant = "Noirs" if self.tour_blanc else "Blancs"
            self.fin = f"Fin de partie : les {gagnant} gagnent (adversaire bloqué) !"

    def terminer_tour(self):
        self.selection = None
        self.multi = False
        self.coups = []
        self.tour_blanc = not self.tour_blanc
        self.verifier_fin()

    def clic(self, x, y):
        if self.fin:
            return
        captures_obligatoires = toutes_captures_obligatoires(self.plateau, self.tour_blanc)

        if self.selection is None:
            piece = self.plateau[x][y]
            if piece == '.' or piece.isupper() != self.tour_blanc:
                return
            self.selection = (x, y)
            self.coups = coups_possibles_piece(self.plateau, x, y)
            if captures_obligatoires:
                for origine, cibles in captures_obligatoires:
                    if origine == (x, y):
                        self.coups = cibles
                        break
                else:
                    self.coups = []
            return

        x1, y1 = self.selection
        if (x, y) in self.coups:
            piece_avant = self.plateau[x1][y1]
            capture = abs(x - x1) >= 2
            deplacer(self.plateau, (x1, y1), (x, y))
            promue = piece_avant in ('P', 'p') and self.plateau[x][y] in ('D', 'd')
            if capture and not promue:
                nouvelles = coups_possibles_piece(self.plateau, x, y, capture_seulement=True)
                if nouvelles:
                    self.selection = (x, y)
                    self.coups = nouvelles
                    self.multi = True
                    return
            self.terminer_tour()
        elif not self.multi:
            # Hors capture multiple, un clic ailleurs annule la sélection.
            self.selection = None
            self.coups = []

    def etat(self):
        return {
            "plateau": self.plateau,
            "tour_blanc": self.tour_blanc,
            "selection": list(self.selection) if self.selection else None,
            "coups": [list(c) for c in self.coups],
            "multi": self.multi,
            "fin": self.fin,
            "message": self.message(),
        }


_partie = Partie()


def api(methode, args):
    if methode == "reset":
        _partie.reset()
    elif methode == "clic":
        _partie.clic(int(args[0]), int(args[1]))
    return _partie.etat()
