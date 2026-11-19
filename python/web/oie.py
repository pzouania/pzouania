"""Moteur du jeu de l'oie pour le site web.

Reprend la logique de Jeu_de_l_oie.py (sans Tkinter, journal sans emoji).
La page web appelle api(methode, args) et reçoit l'état en JSON.
"""

import random

BOARD_SIZE = 63
PLAYER_COLORS = ["#e53935", "#1e88e5", "#43a047", "#fb8c00"]

GOOSE_SQUARES = {5, 9, 14, 18, 23, 27, 32, 36, 41, 45, 50, 54}
BRIDGE, BRIDGE_TO = 6, 12
INN = 19
WELL = 31
LABYRINTH, LABYRINTH_TO = 42, 39
PRISON = 52
DEATH = 58


class Player:
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.pos = 0
        self.skip = 0
        self.stuck_well = False
        self.first_roll = True

    def at_goal(self):
        return self.pos == BOARD_SIZE


class GooseGame:
    def __init__(self, players):
        self.players = players
        self.current = 0
        self.history = []
        self.winner = None
        self.last_dice = None

    def log(self, text):
        self.history.append(text)

    def next_player_index(self):
        return (self.current + 1) % len(self.players)

    def roll_and_move(self, forced_dice=None):
        if self.winner:
            return
        p = self.players[self.current]
        self.last_dice = None

        if p.skip > 0:
            p.skip -= 1
            if p.stuck_well and len(self.players) == 2 and p.skip == 0:
                p.stuck_well = False
                self.log(f"{p.name} sort du puits après 1 tour (variante 2 joueurs).")
            self.current = self.next_player_index()
            self.log(f"{p.name} doit passer son tour.")
            return

        if p.stuck_well:
            self.current = self.next_player_index()
            self.log(f"{p.name} est bloqué dans le puits et ne peut pas jouer.")
            return

        if forced_dice:
            d1, d2 = forced_dice
        else:
            d1, d2 = random.randint(1, 6), random.randint(1, 6)
        self.last_dice = (d1, d2)
        total = d1 + d2
        self.log(f"{p.name} lance les dés : {d1} et {d2}, total {total}.")

        if p.first_roll and total == 9 and sorted([d1, d2]) == [3, 6]:
            p.pos = 26
            p.first_roll = False
            self.log(f"{p.name} fait 6+3 au départ : va en 26.")
            self.check_win()
            self.current = self.next_player_index()
            return
        p.first_roll = False

        newpos = p.pos + total
        if newpos > BOARD_SIZE:
            surplus = newpos - BOARD_SIZE
            newpos = BOARD_SIZE - surplus
            self.log(f"{p.name} dépasse 63 et rebondit en {newpos}.")
        self.log(f"{p.name} avance de {p.pos} à {newpos}.")
        p.pos = newpos

        replay = False

        if p.pos == DEATH:
            p.pos = 0
            p.skip = 0
            p.stuck_well = False
            self.log(f"{p.name} tombe sur la Mort : retour au départ !")
        elif p.pos == BRIDGE:
            p.pos = BRIDGE_TO
            self.log(f"{p.name} traverse le Pont et va à {BRIDGE_TO}.")
        elif p.pos == LABYRINTH:
            p.pos = LABYRINTH_TO
            self.log(f"{p.name} recule à {LABYRINTH_TO} (Labyrinthe).")
        elif p.pos == INN:
            p.skip += 1
            self.log(f"{p.name} s'arrête à l'Auberge ({INN}) : perd 1 tour.")
        elif p.pos == PRISON:
            p.skip += 3
            self.log(f"{p.name} va en Prison ({PRISON}) : perd 3 tours.")
        elif p.pos == WELL:
            if len(self.players) == 2:
                p.stuck_well = True
                p.skip = 1
                self.log(f"{p.name} tombe dans le Puits ({WELL}) : bloqué 1 tour (variante 2 joueurs).")
            else:
                freed = False
                for other in self.players:
                    if other is not p and other.stuck_well and other.pos == WELL:
                        other.stuck_well = False
                        other.pos = 0
                        freed = True
                        self.log(f"{p.name} libère {other.name} (qui retourne au départ).")
                p.stuck_well = True
                if not freed:
                    self.log(f"{p.name} tombe dans le Puits et reste bloqué.")
        elif p.pos in GOOSE_SQUARES:
            self.log(f"{p.name} tombe sur une Oie ({p.pos}) : rejoue !")
            replay = True

        for other in self.players:
            if other is not p and other.pos == p.pos:
                if not (p.pos == WELL and other.stuck_well):
                    other.pos = 0
                    other.skip = 0
                    other.stuck_well = False
                    self.log(f"{p.name} chasse {other.name} au départ.")

        self.check_win()

        if self.winner:
            return

        if replay:
            self.log(f"{p.name} rejoue immédiatement !")
        else:
            self.current = self.next_player_index()

    def check_win(self):
        for pl in self.players:
            if pl.at_goal():
                self.winner = pl
                self.log(f"{pl.name} a gagné la partie !")
                return True
        return False

    def etat(self):
        return {
            "joueurs": [
                {"nom": p.name, "couleur": p.color, "pos": p.pos,
                 "passe": p.skip, "puits": p.stuck_well}
                for p in self.players
            ],
            "courant": self.current,
            "gagnant": self.winner.name if self.winner else None,
            "des": list(self.last_dice) if self.last_dice else None,
            "journal": self.history[-80:],
        }


_jeu = None


def api(methode, args):
    global _jeu
    if methode == "creer":
        noms = [str(n).strip() or f"Joueur {i + 1}" for i, n in enumerate(args[0])][:4]
        _jeu = GooseGame([Player(n, PLAYER_COLORS[i]) for i, n in enumerate(noms)])
    elif methode == "lancer" and _jeu is not None:
        forces = args[0] if args else None
        _jeu.roll_and_move(tuple(forces) if forces else None)
    return _jeu.etat() if _jeu else None
