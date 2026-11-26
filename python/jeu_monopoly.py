# -*- coding: utf-8 -*-
"""
Monopoly v0.9 - Python / Tkinter (compatible EduPython)

Nouveautés de la v0.9 :
- Maisons et hôtels : groupe complet, règle de l'égalité, 4 maisons -> hôtel,
  stock de la banque (32 maisons, 12 hôtels) avec enchères en cas de pénurie,
  revente à la banque pour la moitié du prix
- Hypothèques : valeur hypothécaire, levée = valeur + 10 %, pas de loyer,
  pas de construction sur un groupe hypothéqué
- Faillite juste : un joueur qui manque de liquide doit d'abord vendre / hypothéquer
- Échanges entre joueurs (titres, argent, cartes "Libéré de prison")
- 2 à 8 joueurs
- Menu Partie : nouvelle partie, sauvegarde / chargement (JSON), classement
- Écran de fin avec le classement au patrimoine

Versions précédentes : v0.8 (vraies cartes, enchères, titres, plateau classique),
v0.7 (plateau dessiné, animation), v0.6 (règles de base corrigées).

Organisation du code :
- Données (plateau, cartes)
- Logique du jeu (classes Player et Game) : AUCUN appel à Tkinter
- Interface (classe App) : dessin et boutons, elle appelle Game
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
from tkinter import filedialog
import tkinter.font as tkfont
import random
import math
import json

# ==============================
# Constantes de règles
# ==============================
START_MONEY = 1500
GO_SALARY = 200
JAIL_POS = 10
JAIL_FINE = 50
AUCTION_START = 10
BOARD_SIZE = 40
STATIONS = (5, 15, 25, 35)
MAX_HOUSES = 32                # stock de la banque
MAX_HOTELS = 12
MAX_PLAYERS = 8
SAVE_VERSION = 1


# ==============================
# Plateau (40 cases)
# ==============================
def prop(name, short, color, price, rent, house_price):
    return {"name": name, "short": short, "type": "property", "color": color,
            "price": price, "rent": rent, "house_price": house_price,
            "mortgage": price // 2, "owner": None, "houses": 0, "mortgaged": False}


def station(name, short):
    return {"name": name, "short": short, "type": "station", "price": 200,
            "mortgage": 100, "owner": None, "mortgaged": False}


def utility(name, short):
    return {"name": name, "short": short, "type": "utility", "price": 150,
            "mortgage": 75, "owner": None, "mortgaged": False}


def case(name, short, typ, amount=0):
    return {"name": name, "short": short, "type": typ, "amount": amount}


def make_board():
    """Crée un plateau neuf (appelée à chaque nouvelle partie)."""
    return [
        case("Départ", "DÉPART", "start"),
        prop("Boulevard de Belleville", "BOULEVARD\nDE\nBELLEVILLE", "brun", 60, [2, 10, 30, 90, 160, 250], 50),
        case("Caisse de communauté", "CAISSE DE\nCOMMUNAUTÉ", "community"),
        prop("Rue Lecourbe", "RUE\nLECOURBE", "brun", 60, [4, 20, 60, 180, 320, 450], 50),
        case("Impôts sur le revenu", "IMPÔTS SUR\nLE REVENU", "tax", 200),
        station("Gare Montparnasse", "GARE\nMONT-\nPARNASSE"),
        prop("Rue de Vaugirard", "RUE DE\nVAUGIRARD", "bleu_clair", 100, [6, 30, 90, 270, 400, 550], 50),
        case("Chance", "CHANCE", "chance"),
        prop("Rue de Courcelles", "RUE DE\nCOURCELLES", "bleu_clair", 100, [6, 30, 90, 270, 400, 550], 50),
        prop("Avenue de la République", "AVENUE DE\nLA\nRÉPUBLIQUE", "bleu_clair", 120, [8, 40, 100, 300, 450, 600], 50),
        case("Prison / Simple visite", "PRISON", "jail"),
        prop("Boulevard de la Villette", "BOULEVARD\nDE LA\nVILLETTE", "rose", 140, [10, 50, 150, 450, 625, 750], 100),
        utility("Compagnie de distribution d'électricité", "COMPAGNIE\nD'ÉLEC-\nTRICITÉ"),
        prop("Avenue de Neuilly", "AVENUE\nDE\nNEUILLY", "rose", 140, [10, 50, 150, 450, 625, 750], 100),
        prop("Rue de Paradis", "RUE DE\nPARADIS", "rose", 160, [12, 60, 180, 500, 700, 900], 100),
        station("Gare de Lyon", "GARE\nDE LYON"),
        prop("Avenue Mozart", "AVENUE\nMOZART", "orange", 180, [14, 70, 200, 550, 750, 950], 100),
        case("Caisse de communauté", "CAISSE DE\nCOMMUNAUTÉ", "community"),
        prop("Boulevard Saint-Michel", "BOULEVARD\nSAINT-\nMICHEL", "orange", 180, [14, 70, 200, 550, 750, 950], 100),
        prop("Place Pigalle", "PLACE\nPIGALLE", "orange", 200, [16, 80, 220, 600, 800, 1000], 100),
        case("Parc Gratuit", "PARC GRATUIT", "free_parking"),
        prop("Avenue Matignon", "AVENUE\nMATIGNON", "rouge", 220, [18, 90, 250, 700, 875, 1050], 150),
        case("Chance", "CHANCE", "chance"),
        prop("Boulevard Malesherbes", "BOULEVARD\nMALES-\nHERBES", "rouge", 220, [18, 90, 250, 700, 875, 1050], 150),
        prop("Avenue Henri-Martin", "AVENUE\nHENRI-\nMARTIN", "rouge", 240, [20, 100, 300, 750, 925, 1100], 150),
        station("Gare du Nord", "GARE\nDU NORD"),
        prop("Faubourg Saint-Honoré", "FAUBOURG\nSAINT-\nHONORÉ", "jaune", 260, [22, 110, 330, 800, 975, 1150], 150),
        prop("Place de la Bourse", "PLACE DE\nLA BOURSE", "jaune", 260, [22, 110, 330, 800, 975, 1150], 150),
        utility("Compagnie de distribution des eaux", "COMPAGNIE\nDES EAUX"),
        prop("Rue La Fayette", "RUE\nLA FAYETTE", "jaune", 280, [24, 120, 360, 850, 1025, 1200], 150),
        case("Allez en prison", "ALLEZ EN PRISON", "go_to_jail"),
        prop("Avenue de Breteuil", "AVENUE DE\nBRETEUIL", "vert", 300, [26, 130, 390, 900, 1100, 1275], 200),
        prop("Avenue Foch", "AVENUE\nFOCH", "vert", 300, [26, 130, 390, 900, 1100, 1275], 200),
        case("Caisse de communauté", "CAISSE DE\nCOMMUNAUTÉ", "community"),
        prop("Boulevard des Capucines", "BOULEVARD\nDES\nCAPUCINES", "vert", 320, [28, 150, 450, 1000, 1200, 1400], 200),
        station("Gare Saint-Lazare", "GARE\nSAINT-\nLAZARE"),
        case("Chance", "CHANCE", "chance"),
        prop("Avenue des Champs-Élysées", "AVENUE DES\nCHAMPS-\nÉLYSÉES", "bleu_fonce", 350, [35, 175, 500, 1100, 1300, 1500], 200),
        case("Taxe de luxe", "TAXE DE\nLUXE", "tax", 100),
        prop("Rue de la Paix", "RUE DE\nLA PAIX", "bleu_fonce", 400, [50, 200, 600, 1400, 1700, 2000], 200),
    ]


GROUP_COLORS = {
    "brun": "#8B4513", "bleu_clair": "#AAE0FA", "rose": "#D93A96", "orange": "#F7941D",
    "rouge": "#ED1B24", "jaune": "#FEF200", "vert": "#1FB25A", "bleu_fonce": "#0072BB",
}


# ==============================
# Cartes officielles (version française, montants en euros)
# action = (type, valeur)
#   "gain" / "pay"     : montant
#   "goto"             : avance jusqu'à la case (200 € si on passe par Départ)
#   "go_back_to"       : retourne à la case sans passer par Départ
#   "back"             : recule de n cases
#   "nearest_station"  : avance jusqu'à la prochaine gare
#   "jail"             : aller en prison
#   "jail_card"        : carte "Libéré de prison" conservée
#   "repairs"          : (prix par maison, prix par hôtel)
#   "birthday"         : chaque joueur vous donne ce montant
#   "fine_or_chance"   : payer l'amende ou tirer une carte Chance
# ==============================
CHANCE_CARDS = [
    {"text": "Avancez jusqu'à la case Départ.", "action": ("goto", 0)},
    {"text": "Rendez-vous à la Rue de la Paix.", "action": ("goto", 39)},
    {"text": "Rendez-vous à l'Avenue Henri-Martin. Si vous passez par la case Départ, recevez 200 €.", "action": ("goto", 24)},
    {"text": "Avancez au Boulevard de la Villette. Si vous passez par la case Départ, recevez 200 €.", "action": ("goto", 11)},
    {"text": "Avancez jusqu'à la Gare de Lyon. Si vous passez par la case Départ, recevez 200 €.", "action": ("goto", 15)},
    {"text": "Reculez de trois cases.", "action": ("back", 3)},
    {"text": "Allez en prison. Ne passez pas par la case Départ, ne recevez pas 200 €.", "action": ("jail", None)},
    {"text": "Vous êtes libéré de prison. Cette carte peut être conservée.", "action": ("jail_card", None)},
    {"text": "Réparations de voirie : payez 40 € par maison et 115 € par hôtel.", "action": ("repairs", (40, 115))},
    {"text": "Réparations dans vos maisons : payez 25 € par maison et 100 € par hôtel.", "action": ("repairs", (25, 100))},
    {"text": "Amende pour excès de vitesse : 15 €.", "action": ("pay", 15)},
    {"text": "Amende pour ivresse : 20 €.", "action": ("pay", 20)},
    {"text": "Payez pour frais de scolarité : 150 €.", "action": ("pay", 150)},
    {"text": "La banque vous verse un dividende de 50 €.", "action": ("gain", 50)},
    {"text": "Votre immeuble et votre prêt rapportent : recevez 150 €.", "action": ("gain", 150)},
    {"text": "Vous avez gagné le prix de mots croisés : recevez 100 €.", "action": ("gain", 100)},
]

COMMUNITY_CARDS = [
    {"text": "Placez-vous sur la case Départ.", "action": ("goto", 0)},
    {"text": "Retournez à Belleville.", "action": ("go_back_to", 1)},
    {"text": "Allez en prison. Ne passez pas par la case Départ, ne recevez pas 200 €.", "action": ("jail", None)},
    {"text": "Vous êtes libéré de prison. Cette carte peut être conservée.", "action": ("jail_card", None)},
    {"text": "Erreur de la banque en votre faveur : recevez 200 €.", "action": ("gain", 200)},
    {"text": "Recevez votre revenu annuel : 100 €.", "action": ("gain", 100)},
    {"text": "Vous héritez de 100 €.", "action": ("gain", 100)},
    {"text": "La vente de votre stock vous rapporte 50 €.", "action": ("gain", 50)},
    {"text": "Recevez vos intérêts sur l'emprunt à 7 % : 25 €.", "action": ("gain", 25)},
    {"text": "Les contributions vous remboursent 20 €.", "action": ("gain", 20)},
    {"text": "C'est votre anniversaire : chaque joueur vous donne 10 €.", "action": ("birthday", 10)},
    {"text": "Vous avez gagné le deuxième prix de beauté : recevez 10 €.", "action": ("gain", 10)},
    {"text": "Payez votre police d'assurance : 50 €.", "action": ("pay", 50)},
    {"text": "Payez la note du médecin : 50 €.", "action": ("pay", 50)},
    {"text": "Payez une amende de 10 € ou tirez une carte Chance.", "action": ("fine_or_chance", 10)},
    {"text": "Rendez-vous à la gare la plus proche. Si vous passez par la case Départ, recevez 200 €.", "action": ("nearest_station", None)},
]


# ==============================
# Logique du jeu (sans Tkinter)
# ==============================
class Player:
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.position = 0
        self.money = START_MONEY
        self.properties = []   # indices des cases possédées
        self.in_jail = False
        self.jail_turns = 0    # tentatives ratées pour sortir de prison
        self.jail_cards = []   # cartes "Libéré de prison" : (nom du paquet, carte)
        self.active = True     # False = en faillite


def interest(amount):
    """10 % arrondis à l'euro supérieur (intérêts d'hypothèque)."""
    return (amount + 9) // 10


class Game:
    """Toutes les règles. L'interface est passée en paramètre (ui) et doit fournir :
    log(texte), ask(titre, question) -> bool, refresh(), game_over(gagnant).
    Optionnel : pawn_moved(joueur, sens), card_drawn(paquet, texte),
                ask_bid(joueur, objet, meilleur, meilleure_offre, minimum) -> int ou None,
                raise_funds(joueur, montant, créancier) : laisse le joueur vendre/hypothéquer."""

    def __init__(self, players, ui):
        self.board = make_board()
        self.players = players
        self.ui = ui
        self.current = 0
        self.decks = {"chance": list(CHANCE_CARDS), "community": list(COMMUNITY_CARDS)}
        random.shuffle(self.decks["chance"])
        random.shuffle(self.decks["community"])
        self.last_dice = (0, 0)
        self.doubles = 0          # nombre de doubles d'affilée ce tour
        self.has_rolled = False   # True = le joueur ne peut plus relancer ce tour
        self.over = False
        self.houses_left = MAX_HOUSES
        self.hotels_left = MAX_HOTELS
        self.eliminated = []      # joueurs en faillite, dans l'ordre

    # ---------- utilitaires ----------
    @property
    def player(self):
        return self.players[self.current]

    def log(self, text):
        self.ui.log(text)

    def notify(self, event, *args):
        """Prévient l'interface si elle sait gérer cet événement."""
        handler = getattr(self.ui, event, None)
        if handler:
            return handler(*args)
        return None

    def can_roll(self):
        return not self.over and not self.has_rolled

    def can_end_turn(self):
        return not self.over and self.has_rolled

    def has_actions(self, p):
        """Reste-t-il une action utile avant de finir le tour ?
        (construire ou lever une hypothèque ; hypothéquer ou échanger restent toujours possibles
        mais ne bloquent pas la fin de tour automatique)."""
        return any(self.can_build(p, i) or self.can_unmortgage(p, i) for i in p.properties)

    def group(self, color):
        return [i for i, c in enumerate(self.board) if c["type"] == "property" and c["color"] == color]

    # ---------- argent ----------
    def gain(self, p, amount):
        p.money += amount

    def liquidation_value(self, p):
        """Argent que p peut réunir en vendant ses bâtiments et en hypothéquant."""
        total = p.money
        for i in p.properties:
            cell = self.board[i]
            total += cell.get("houses", 0) * cell.get("house_price", 0) // 2
            if not cell["mortgaged"]:
                total += cell["mortgage"]
        return total

    def pay(self, p, amount, creditor=None):
        """p paie amount à creditor (ou à la banque si None).
        S'il n'a pas assez de liquide, il doit d'abord vendre ses bâtiments et hypothéquer.
        Faillite seulement s'il ne peut vraiment pas payer (ou s'il l'a choisi)."""
        if p.money < amount and self.liquidation_value(p) >= amount:
            to = creditor.name if creditor else "la banque"
            self.log(f"{p.name} doit {amount}€ à {to} mais n'a que {p.money}€ : il doit vendre ou hypothéquer.")
            if getattr(self.ui, "raise_funds", None):
                self.ui.raise_funds(p, amount, creditor)
            else:
                self.auto_raise(p, amount)
        if p.active and p.money >= amount:
            p.money -= amount
            if creditor:
                creditor.money += amount
            return True
        if p.active:
            self.bankrupt(p, creditor)
        return False

    def auto_raise(self, p, amount):
        """Réunit automatiquement la somme : vend les bâtiments puis hypothèque les moins chers."""
        while p.money < amount:
            sellable = [i for i in p.properties if self.can_sell_building(p, i)]
            if not sellable:
                break
            self.sell_building(p, max(sellable, key=lambda i: self.board[i]["houses"]))
        for i in sorted(p.properties, key=lambda i: self.board[i]["mortgage"]):
            if p.money >= amount:
                break
            if self.can_mortgage(p, i):
                self.mortgage(p, i)

    def bankrupt(self, p, creditor=None):
        """Faillite officielle : bâtiments revendus à la banque (moitié prix), puis
        - envers un joueur : il reçoit l'argent, les titres (hypothéqués compris, il paie 10 %)
          et les cartes "Libéré de prison" ;
        - envers la banque : hypothèques annulées et titres mis aux enchères."""
        p.active = False
        p.in_jail = False
        self.eliminated.append(p)
        to = creditor.name if creditor else "la banque"
        self.log(f"*** {p.name} fait faillite ! Ses biens vont à {to}. ***")
        for i in p.properties:                       # bâtiments revendus à la banque
            cell = self.board[i]
            if cell.get("houses"):
                p.money += cell["houses"] * cell["house_price"] // 2
                self.return_buildings(cell["houses"])
                cell["houses"] = 0
        lost = list(p.properties)
        p.properties = []
        if creditor:
            creditor.money += p.money
            p.money = 0
            for i in lost:
                cell = self.board[i]
                cell["owner"] = creditor
                creditor.properties.append(i)
            creditor.jail_cards += p.jail_cards
            p.jail_cards = []
            fees = sum(interest(self.board[i]["mortgage"]) for i in lost if self.board[i]["mortgaged"])
            if fees:
                self.log(f"{creditor.name} paie {fees}€ d'intérêts sur les terrains hypothéqués reçus.")
                creditor.money -= min(fees, creditor.money)
        else:
            p.money = 0
            for i in lost:
                self.board[i]["owner"] = None
                self.board[i]["mortgaged"] = False
            for deck_name, card in p.jail_cards:
                self.decks[deck_name].append(card)
            p.jail_cards = []
        self.check_winner()
        if creditor is None and not self.over:
            for i in lost:
                self.auction(i)

    def check_winner(self):
        alive = [p for p in self.players if p.active]
        if len(alive) == 1 and not self.over:
            self.over = True
            self.log(f"=== Victoire de {alive[0].name} ! ===")
            self.ui.game_over(alive[0])

    def finish(self):
        """Arrête la partie maintenant : le classement se fait au patrimoine."""
        if self.over:
            return
        self.over = True
        leader = self.ranking()[0][1]
        self.log(f"=== Partie terminée. {leader.name} a le plus gros patrimoine. ===")
        self.ui.game_over(leader)

    # ---------- patrimoine et classement ----------
    def assets_value(self, p):
        """Valeur des biens : prix des titres (moitié s'ils sont hypothéqués) + prix des bâtiments."""
        total = 0
        for i in p.properties:
            cell = self.board[i]
            total += cell["price"] - (cell["mortgage"] if cell["mortgaged"] else 0)
            total += cell.get("houses", 0) * cell.get("house_price", 0)
        return total

    def ranking(self):
        """Liste de (rang, joueur, argent, biens, total) : joueurs encore en jeu triés par
        patrimoine, puis joueurs éliminés (le dernier éliminé est le mieux classé)."""
        alive = sorted([p for p in self.players if p.active],
                       key=lambda p: p.money + self.assets_value(p), reverse=True)
        rows = []
        for p in alive + list(reversed(self.eliminated)):
            assets = self.assets_value(p)
            rows.append((len(rows) + 1, p, p.money, assets, p.money + assets))
        return rows

    # ---------- tour de jeu ----------
    def roll(self, dice=None):
        """Lance les dés pour le joueur courant. dice=(d1, d2) permet de tester."""
        if not self.can_roll():
            return
        p = self.player
        if p.in_jail:
            self.offer_jail_exit(p)

        d1, d2 = dice if dice else (random.randint(1, 6), random.randint(1, 6))
        self.last_dice = (d1, d2)
        total, double = d1 + d2, d1 == d2
        self.log(f"{p.name} lance {d1} + {d2} = {total}" + (" (double !)" if double else ""))

        if p.in_jail:
            self.has_rolled = True   # en prison : jamais de relance, même sur double
            if double:
                self.log(f"{p.name} sort de prison grâce au double.")
                self.release(p)
                self.move_by(p, total)
            else:
                p.jail_turns += 1
                if p.jail_turns >= 3:
                    self.log(f"3e échec : {p.name} doit payer {JAIL_FINE}€ et sort.")
                    if self.pay(p, JAIL_FINE):
                        self.release(p)
                        self.move_by(p, total)
                else:
                    self.log(f"{p.name} reste en prison (tentative {p.jail_turns}/3).")
        else:
            if double:
                self.doubles += 1
            if self.doubles == 3:
                self.log("Trois doubles d'affilée !")
                self.send_to_jail(p)
                self.has_rolled = True
            else:
                self.has_rolled = not double
                self.move_by(p, total)
                if p.in_jail or not p.active:   # envoyé en prison ou faillite : tour fini
                    self.has_rolled = True
                elif double:
                    self.log(f"{p.name} rejoue.")
        self.ui.refresh()

    def end_turn(self):
        if not self.can_end_turn():
            return
        self.current = (self.current + 1) % len(self.players)
        while not self.players[self.current].active:
            self.current = (self.current + 1) % len(self.players)
        self.doubles = 0
        self.has_rolled = False
        p = self.player
        self.log(f"--- Au tour de {p.name}" + (" (en prison)" if p.in_jail else "") + " ---")
        self.ui.refresh()

    # ---------- déplacements (une seule logique pour dés et cartes) ----------
    def move_by(self, p, steps):
        new_pos = p.position + steps
        p.position = new_pos % BOARD_SIZE
        self.notify("pawn_moved", p, 1)        # en avant
        if new_pos >= BOARD_SIZE:
            self.gain(p, GO_SALARY)
            self.log(f"{p.name} passe par Départ et reçoit {GO_SALARY}€.")
        self.handle_landing(p)

    def move_to(self, p, pos):
        """Avance jusqu'à pos (dans le sens du jeu)."""
        self.move_by(p, (pos - p.position) % BOARD_SIZE)

    def jump_to(self, p, pos):
        """Déplace sans passer par Départ (on recule ou on "retourne")."""
        p.position = pos % BOARD_SIZE
        self.notify("pawn_moved", p, -1)       # en arrière
        self.handle_landing(p)

    # ---------- prison ----------
    def send_to_jail(self, p):
        p.position = JAIL_POS
        p.in_jail = True
        p.jail_turns = 0
        self.doubles = 0
        self.notify("pawn_moved", p, 0)        # téléportation
        self.log(f"{p.name} est envoyé en PRISON !")

    def release(self, p):
        p.in_jail = False
        p.jail_turns = 0

    def offer_jail_exit(self, p):
        """Avant de lancer en prison : utiliser une carte ou payer 50 €."""
        if p.jail_cards and self.ui.ask("Prison", f"{p.name}, utiliser votre carte « Libéré de prison » ?"):
            deck_name, card = p.jail_cards.pop()
            self.decks[deck_name].append(card)
            self.release(p)
            self.log(f"{p.name} utilise sa carte et sort de prison.")
        elif p.money >= JAIL_FINE and self.ui.ask("Prison", f"{p.name}, payer {JAIL_FINE}€ pour sortir de prison ?"):
            self.pay(p, JAIL_FINE)
            self.release(p)
            self.log(f"{p.name} paie {JAIL_FINE}€ et sort de prison.")

    # ---------- arrivée sur une case ----------
    def handle_landing(self, p):
        cell = self.board[p.position]
        t = cell["type"]
        self.log(f"{p.name} arrive sur {cell['name']}.")

        if t in ("property", "station", "utility"):
            owner = cell["owner"]
            if owner is None:
                self.offer_buy(p, p.position)
            elif owner is not p:
                if cell["mortgaged"]:
                    self.log(f"{cell['name']} est hypothéqué : pas de loyer.")
                else:
                    rent = self.compute_rent(p.position)
                    self.log(f"{p.name} paie {rent}€ de loyer à {owner.name}.")
                    self.pay(p, rent, owner)
        elif t == "tax":
            self.log(f"{p.name} paie {cell['amount']}€ de taxe.")
            self.pay(p, cell["amount"])
        elif t in ("chance", "community"):
            self.draw_card(p, t)
        elif t == "go_to_jail":
            self.send_to_jail(p)

    def offer_buy(self, p, idx):
        cell = self.board[idx]
        if p.money >= cell["price"]:
            if self.ui.ask("Achat", f"{p.name}, acheter {cell['name']} pour {cell['price']}€ ?\n"
                                    f"(solde : {p.money}€)\n\nSi vous refusez, la propriété "
                                    f"est mise aux enchères."):
                p.money -= cell["price"]
                cell["owner"] = p
                p.properties.append(idx)
                self.log(f"{p.name} achète {cell['name']}.")
                return
            self.log(f"{p.name} refuse d'acheter {cell['name']}.")
        else:
            self.log(f"{p.name} n'a pas assez d'argent pour acheter {cell['name']}.")
        self.auction(idx)

    # ---------- enchères ----------
    def run_auction(self, item, bidders, start):
        """Enchère générique : chacun surenchérit ou passe, jusqu'à ce qu'il ne reste qu'un joueur.
        item = dict avec "name" et "price" (pour l'affichage). Renvoie (gagnant, prix) ou (None, 0)."""
        ask_bid = getattr(self.ui, "ask_bid", None)
        if ask_bid is None:
            return None, 0
        bidders = list(bidders)
        best, best_bid, k = None, 0, 0
        while bidders and not (len(bidders) == 1 and bidders[0] is best):
            k %= len(bidders)
            b = bidders[k]
            if b is best:
                k += 1
                continue
            need = max(start, best_bid + 1)
            amount = ask_bid(b, item, best, best_bid, need) if b.money >= need else None
            if amount is None or amount < need or amount > b.money:
                bidders.pop(k)
                self.log(f"   {b.name} passe.")
            else:
                best, best_bid = b, amount
                self.log(f"   {b.name} propose {amount}€.")
                k += 1
        return best, best_bid

    def bidders_from_current(self):
        n = len(self.players)
        order = [self.players[(self.current + k) % n] for k in range(n)]
        return [b for b in order if b.active]

    def auction(self, idx):
        """Enchères officielles d'un terrain : tout le monde peut miser, à partir de 10 €."""
        cell = self.board[idx]
        if getattr(self.ui, "ask_bid", None) is None:
            return
        self.log(f"Enchères pour {cell['name']} (départ à {AUCTION_START}€).")
        best, bid = self.run_auction(cell, self.bidders_from_current(), AUCTION_START)
        if best:
            best.money -= bid
            cell["owner"] = best
            best.properties.append(idx)
            self.log(f"{best.name} remporte {cell['name']} pour {bid}€.")
        else:
            self.log(f"Personne n'enchérit : {cell['name']} reste à la banque.")

    # ---------- loyers ----------
    def owns_group(self, p, color):
        return all(self.board[i]["owner"] is p for i in self.group(color))

    def group_count(self, p, color):
        """(nombre possédé par p, taille du groupe)"""
        g = self.group(color)
        return sum(1 for i in g if self.board[i]["owner"] is p), len(g)

    def count_owned(self, p, typ):
        return sum(1 for c in self.board if c["type"] == typ and c["owner"] is p)

    def compute_rent(self, idx):
        cell = self.board[idx]
        owner = cell["owner"]
        if cell.get("mortgaged"):
            return 0
        if cell["type"] == "property":
            if cell["houses"] > 0:
                return cell["rent"][cell["houses"]]
            base = cell["rent"][0]
            return base * 2 if self.owns_group(owner, cell["color"]) else base
        if cell["type"] == "station":
            return 25 * 2 ** (self.count_owned(owner, "station") - 1)   # 25, 50, 100, 200
        if cell["type"] == "utility":
            factor = 4 if self.count_owned(owner, "utility") == 1 else 10
            return factor * sum(self.last_dice)
        return 0

    # ---------- maisons et hôtels ----------
    def build_block_reason(self, p, idx, check_money=True, check_stock=True):
        """Pourquoi p ne peut pas construire sur idx (None = il peut)."""
        cell = self.board[idx]
        if cell["type"] != "property" or cell["owner"] is not p:
            return "Ce terrain ne vous appartient pas."
        if not self.owns_group(p, cell["color"]):
            return "Il faut posséder tout le groupe de couleur."
        grp = self.group(cell["color"])
        if any(self.board[i]["mortgaged"] for i in grp):
            return "Un terrain du groupe est hypothéqué."
        if cell["houses"] >= 5:
            return "Il y a déjà un hôtel."
        if cell["houses"] > min(self.board[i]["houses"] for i in grp):
            return "Construisez d'abord sur les autres terrains du groupe (règle de l'égalité)."
        if check_stock:
            if cell["houses"] == 4 and self.hotels_left == 0:
                return "La banque n'a plus d'hôtel."
            if cell["houses"] < 4 and self.houses_left == 0:
                return "La banque n'a plus de maison."
        if check_money and p.money < cell["house_price"]:
            return "Pas assez d'argent."
        return None

    def can_build(self, p, idx):
        return self.build_block_reason(p, idx) is None

    def wants_building(self, p, hotel):
        """p peut-il construire ce type de bâtiment quelque part ? (pour détecter une pénurie)"""
        return any(self.can_build(p, i) and (self.board[i]["houses"] == 4) == hotel for i in p.properties)

    def request_build(self, p, idx):
        """Construit une maison (ou un hôtel) sur idx. Si plusieurs joueurs veulent les derniers
        bâtiments de la banque (pénurie), ils sont mis aux enchères. Renvoie True si construit."""
        if not self.can_build(p, idx):
            return False
        cell = self.board[idx]
        hotel = cell["houses"] == 4
        stock = self.hotels_left if hotel else self.houses_left
        rivals = [q for q in self.players if q is not p and q.active and self.wants_building(q, hotel)]
        if rivals and stock <= len(rivals):
            what = "hôtel" if hotel else "maison"
            self.log(f"Pénurie : il reste {stock} {what}(s) pour {len(rivals) + 1} joueurs. Enchères !")
            winner, price = self.run_auction({"name": f"1 {what} (pénurie)", "price": cell["house_price"]},
                                             [p] + rivals, cell["house_price"])
            if winner is None:
                return False
            if winner is not p:
                idx = next(i for i in sorted(winner.properties)
                           if self.build_block_reason(winner, i, check_money=False) is None
                           and (self.board[i]["houses"] == 4) == hotel)
            self.build(winner, idx, price)
            return winner is p
        self.build(p, idx, cell["house_price"])
        return True

    def build(self, p, idx, price):
        cell = self.board[idx]
        p.money -= price
        if cell["houses"] == 4:          # 4 maisons -> 1 hôtel, les maisons retournent à la banque
            self.hotels_left -= 1
            self.houses_left += 4
            cell["houses"] = 5
            self.log(f"{p.name} construit un hôtel sur {cell['name']} ({price}€).")
        else:
            self.houses_left -= 1
            cell["houses"] += 1
            self.log(f"{p.name} construit une maison sur {cell['name']} ({price}€).")

    def can_sell_building(self, p, idx):
        cell = self.board[idx]
        if cell["type"] != "property" or cell["owner"] is not p or cell["houses"] == 0:
            return False
        # règle de l'égalité : on vend d'abord sur le terrain le plus construit
        return cell["houses"] == max(self.board[i]["houses"] for i in self.group(cell["color"]))

    def sell_building(self, p, idx):
        """Revend un bâtiment à la banque pour la moitié de son prix."""
        if not self.can_sell_building(p, idx):
            return False
        cell = self.board[idx]
        half = cell["house_price"] // 2
        if cell["houses"] == 5:
            # l'hôtel redevient 4 maisons... si la banque en a assez
            back = min(4, self.houses_left)
            self.hotels_left += 1
            self.houses_left -= back
            levels = 5 - back
            cell["houses"] = back
            p.money += half * levels
            self.log(f"{p.name} revend l'hôtel de {cell['name']} (+{half * levels}€)"
                     + (f", il reste {back} maison(s)." if back else "."))
        else:
            cell["houses"] -= 1
            self.houses_left += 1
            p.money += half
            self.log(f"{p.name} revend une maison de {cell['name']} (+{half}€).")
        return True

    def return_buildings(self, houses):
        if houses == 5:
            self.hotels_left += 1
        else:
            self.houses_left += houses

    # ---------- hypothèques ----------
    def can_mortgage(self, p, idx):
        cell = self.board[idx]
        if cell.get("owner") is not p or cell["mortgaged"]:
            return False
        if cell["type"] == "property":   # il faut d'abord vendre les bâtiments du groupe
            return all(self.board[i]["houses"] == 0 for i in self.group(cell["color"]))
        return True

    def mortgage(self, p, idx):
        if not self.can_mortgage(p, idx):
            return False
        cell = self.board[idx]
        cell["mortgaged"] = True
        p.money += cell["mortgage"]
        self.log(f"{p.name} hypothèque {cell['name']} (+{cell['mortgage']}€).")
        return True

    def unmortgage_cost(self, idx):
        m = self.board[idx]["mortgage"]
        return m + interest(m)

    def can_unmortgage(self, p, idx):
        cell = self.board[idx]
        return cell.get("owner") is p and cell["mortgaged"] and p.money >= self.unmortgage_cost(idx)

    def unmortgage(self, p, idx):
        if not self.can_unmortgage(p, idx):
            return False
        cost = self.unmortgage_cost(idx)
        p.money -= cost
        self.board[idx]["mortgaged"] = False
        self.log(f"{p.name} lève l'hypothèque de {self.board[idx]['name']} (-{cost}€).")
        return True

    # ---------- échanges ----------
    def tradeable(self, p, idx):
        """Un titre s'échange seulement s'il n'y a aucun bâtiment sur son groupe."""
        cell = self.board[idx]
        if cell.get("owner") is not p:
            return False
        if cell["type"] == "property":
            return all(self.board[i]["houses"] == 0 for i in self.group(cell["color"]))
        return True

    def validate_trade(self, a, b, a_props, b_props, a_money, b_money, a_cards, b_cards):
        """Renvoie un message d'erreur, ou None si l'échange est possible.
        a_cards / b_cards = indices dans la liste jail_cards de chaque joueur."""
        if a is b or not a.active or not b.active:
            return "Partenaire invalide."
        if not (a_props or b_props or a_money or b_money or a_cards or b_cards):
            return "L'échange est vide."
        if a_money < 0 or b_money < 0:
            return "Les montants doivent être positifs."
        for p, props in ((a, a_props), (b, b_props)):
            for i in props:
                if not self.tradeable(p, i):
                    return f"{self.board[i]['name']} ne peut pas être échangé (vendez d'abord les bâtiments du groupe)."
        for p, cards in ((a, a_cards), (b, b_cards)):
            if any(c < 0 or c >= len(p.jail_cards) for c in cards):
                return "Carte invalide."
        # celui qui reçoit un terrain hypothéqué paie 10 % d'intérêts tout de suite
        fees_a = sum(interest(self.board[i]["mortgage"]) for i in b_props if self.board[i]["mortgaged"])
        fees_b = sum(interest(self.board[i]["mortgage"]) for i in a_props if self.board[i]["mortgaged"])
        if a.money < a_money + fees_a:
            return f"{a.name} n'a pas assez d'argent (intérêts d'hypothèque compris : {fees_a}€)."
        if b.money < b_money + fees_b:
            return f"{b.name} n'a pas assez d'argent (intérêts d'hypothèque compris : {fees_b}€)."
        return None

    def trade(self, a, b, a_props, b_props, a_money, b_money, a_cards=(), b_cards=()):
        err = self.validate_trade(a, b, a_props, b_props, a_money, b_money, a_cards, b_cards)
        if err:
            return err
        a.money += b_money - a_money
        b.money += a_money - b_money
        for giver, taker, props in ((a, b, a_props), (b, a, b_props)):
            for i in props:
                cell = self.board[i]
                giver.properties.remove(i)
                taker.properties.append(i)
                cell["owner"] = taker
                if cell["mortgaged"]:
                    fee = interest(cell["mortgage"])
                    taker.money -= fee
                    self.log(f"{taker.name} paie {fee}€ d'intérêts sur {cell['name']} (hypothéqué).")
        moved_a = [a.jail_cards[c] for c in a_cards]
        moved_b = [b.jail_cards[c] for c in b_cards]
        a.jail_cards = [c for k, c in enumerate(a.jail_cards) if k not in a_cards] + moved_b
        b.jail_cards = [c for k, c in enumerate(b.jail_cards) if k not in b_cards] + moved_a
        self.log(f"Échange entre {a.name} et {b.name} effectué.")
        return None

    # ---------- cartes ----------
    def draw_card(self, p, deck_name):
        deck = self.decks[deck_name]
        card = deck.pop(0)
        title = "Chance" if deck_name == "chance" else "Caisse de communauté"
        self.log(f"{title} : {card['text']}")
        self.notify("card_drawn", deck_name, card["text"])
        kind, value = card["action"]
        if kind == "jail_card":
            p.jail_cards.append((deck_name, card))   # la carte quitte le paquet
            return
        deck.append(card)                            # remise sous le paquet
        if kind == "gain":
            self.gain(p, value)
        elif kind == "pay":
            self.pay(p, value)
        elif kind == "goto":
            self.move_to(p, value)
        elif kind == "go_back_to":
            self.jump_to(p, value)
        elif kind == "back":
            self.jump_to(p, p.position - value)
        elif kind == "nearest_station":
            nxt = min([s for s in STATIONS if s > p.position] or [STATIONS[0]])
            self.move_to(p, nxt)
        elif kind == "jail":
            self.send_to_jail(p)
        elif kind == "repairs":
            per_house, per_hotel = value
            houses = sum(self.board[i].get("houses", 0) for i in p.properties
                         if self.board[i].get("houses", 0) < 5)
            hotels = sum(1 for i in p.properties if self.board[i].get("houses", 0) == 5)
            total = houses * per_house + hotels * per_hotel
            self.log(f"{p.name} a {houses} maison(s) et {hotels} hôtel(s) : {total}€ à payer.")
            if total:
                self.pay(p, total)
        elif kind == "birthday":
            for other in self.players:
                if other is not p and other.active:
                    self.pay(other, value, p)
        elif kind == "fine_or_chance":
            if self.ui.ask("Caisse de communauté",
                           f"{p.name} : payer l'amende de {value}€ ?\n(Non = tirer une carte Chance)"):
                self.pay(p, value)
            else:
                self.draw_card(p, "chance")

    # ---------- sauvegarde ----------
    def to_dict(self):
        idx = {p: k for k, p in enumerate(self.players)}
        return {
            "version": SAVE_VERSION,
            "players": [{"name": p.name, "color": p.color, "position": p.position, "money": p.money,
                         "in_jail": p.in_jail, "jail_turns": p.jail_turns, "active": p.active,
                         "jail_cards": [[d, c["text"]] for d, c in p.jail_cards]} for p in self.players],
            "board": [{"owner": idx[c["owner"]] if c.get("owner") else None,
                       "houses": c.get("houses", 0), "mortgaged": c.get("mortgaged", False)}
                      if "price" in c else None for c in self.board],
            "decks": {name: [c["text"] for c in deck] for name, deck in self.decks.items()},
            "current": self.current, "doubles": self.doubles, "has_rolled": self.has_rolled,
            "last_dice": list(self.last_dice), "over": self.over,
            "houses_left": self.houses_left, "hotels_left": self.hotels_left,
            "eliminated": [idx[p] for p in self.eliminated],
        }

    @staticmethod
    def players_from_dict(data):
        players = []
        for d in data["players"]:
            p = Player(d["name"], d["color"])
            p.position, p.money = d["position"], d["money"]
            p.in_jail, p.jail_turns, p.active = d["in_jail"], d["jail_turns"], d["active"]
            players.append(p)
        return players

    def load_dict(self, data):
        """Restaure l'état (les joueurs viennent de players_from_dict)."""
        if data.get("version") != SAVE_VERSION:
            raise ValueError("Version de sauvegarde inconnue.")
        by_text = {"chance": {c["text"]: c for c in CHANCE_CARDS},
                   "community": {c["text"]: c for c in COMMUNITY_CARDS}}
        for p, d in zip(self.players, data["players"]):
            p.jail_cards = [(deck, by_text[deck][text]) for deck, text in d["jail_cards"]]
            p.properties = []
        for i, d in enumerate(data["board"]):
            if d is None:
                continue
            cell = self.board[i]
            cell["owner"] = self.players[d["owner"]] if d["owner"] is not None else None
            cell["mortgaged"] = d["mortgaged"]
            if "houses" in cell:
                cell["houses"] = d["houses"]
            if cell["owner"]:
                cell["owner"].properties.append(i)
        self.decks = {name: [by_text[name][t] for t in texts] for name, texts in data["decks"].items()}
        self.current, self.doubles = data["current"], data["doubles"]
        self.has_rolled, self.over = data["has_rolled"], data["over"]
        self.last_dice = tuple(data["last_dice"])
        self.houses_left, self.hotels_left = data["houses_left"], data["hotels_left"]
        self.eliminated = [self.players[k] for k in data["eliminated"]]


# ==============================
# Interface Tkinter
# ==============================
CORNER = 90                       # taille d'un coin (pixels)
SIDE = 56                         # largeur d'une case de côté
MARGIN = 8
BOARD_PX = 2 * CORNER + 9 * SIDE + 2 * MARGIN
INNER_A = MARGIN + CORNER         # début de la zone centrale
INNER_B = MARGIN + CORNER + 9 * SIDE   # fin de la zone centrale
EDGE = INNER_B + CORNER           # bord extérieur bas / droit
MID = (INNER_A + INNER_B) / 2     # centre du plateau
BAND = 17                         # épaisseur de la bande de couleur
JAIL_STRIP = 34                   # largeur de la bande "Simple visite"
PRICE_V = 80                      # position du prix dans une case
PAWN_V = 62                       # centre de la zone des pions dans une case (51 à 74)
# places des pions dans les coins (x, y depuis le coin haut-gauche de la case), les 4 premières
# forment un groupe ; trouvées en analysant le dessin pour éviter textes et images
CORNER_SLOTS_4 = {0: [(75, 59), (75, 75), (61, 51), (75, 43)],                 # jusqu'à 4 joueurs
                  10: [(23, 65), (12, 77), (11, 54), (36, 75)],
                  20: [(75, 22), (75, 75), (22, 75), (18, 14)],
                  30: [(26, 21), (75, 18), (75, 75), (14, 75)]}
CORNER_SLOTS_8 = {0: [(64, 58), (64, 46), (75, 51), (75, 63), (75, 75), (53, 53), (45, 62), (75, 39)],
                  10: [(20, 57), (9, 52), (10, 64), (16, 75), (26, 68), (36, 75), (41, 64), (26, 20)],
                  20: [(76, 34), (75, 22), (67, 13), (18, 14), (13, 67), (22, 75), (34, 76), (75, 75)],
                  30: [(26, 21), (15, 26), (16, 14), (75, 18), (75, 63), (75, 75), (64, 70), (14, 75)]}
# en prison (depuis le coin haut-gauche du carré orange de 56 x 56)
JAIL_SLOTS = [(8, 8), (21, 8), (8, 21), (48, 48), (35, 48), (48, 35), (27, 6), (50, 29)]
AUTO_END_DELAY = 1500             # délai avant la fin de tour automatique (ms)

FONT = "Arial"
BOARD_BG = "#D2E8D4"              # vert du plateau classique
DARK_GROUPS = ("brun", "rose", "rouge", "vert", "bleu_fonce")   # texte blanc sur l'en-tête
CHANCE_COLORS = {7: "#D6338A", 22: "#1E88C8", 36: "#E8730C"}    # "?" de couleur différente


def cell_rect(pos):
    """Rectangle (x1, y1, x2, y2) de la case pos.
    Départ en bas à droite, Prison en bas à gauche,
    Parc Gratuit en haut à gauche, Allez en prison en haut à droite."""
    if pos == 0:
        return INNER_B, INNER_B, EDGE, EDGE
    if pos < 10:                                  # rangée du bas, de droite à gauche
        x1 = INNER_B - pos * SIDE
        return x1, INNER_B, x1 + SIDE, EDGE
    if pos == 10:
        return MARGIN, INNER_B, INNER_A, EDGE
    if pos < 20:                                  # colonne de gauche, de bas en haut
        y1 = INNER_B - (pos - 10) * SIDE
        return MARGIN, y1, INNER_A, y1 + SIDE
    if pos == 20:
        return MARGIN, MARGIN, INNER_A, INNER_A
    if pos < 30:                                  # rangée du haut, de gauche à droite
        x1 = INNER_A + (pos - 21) * SIDE
        return x1, MARGIN, x1 + SIDE, INNER_A
    if pos == 30:
        return INNER_B, MARGIN, EDGE, INNER_A
    y1 = INNER_A + (pos - 31) * SIDE              # colonne de droite, de haut en bas
    return INNER_B, y1, EDGE, y1 + SIDE


def cell_frame(pos):
    """Repère local d'une case de côté (pas un coin), comme sur le vrai plateau :
    le haut des lettres pointe toujours vers le centre.
    Renvoie (to_xy, angle) : to_xy(u, v) donne les pixels d'un point défini par
    u = position dans le sens de lecture (0..SIDE) et v = distance au bord intérieur (0..CORNER)."""
    x1, y1, x2, y2 = cell_rect(pos)
    if pos < 10:
        return (lambda u, v: (x1 + u, y1 + v)), 0
    if pos < 20:
        return (lambda u, v: (x2 - v, y1 + u)), -90
    if pos < 30:
        return (lambda u, v: (x2 - u, y2 - v)), 180
    return (lambda u, v: (x1 + v, y2 - u)), 90


def rotate(points, cx, cy, angle):
    """Tourne des points (dx, dy) relatifs au centre de 'angle' degrés
    (sens inverse des aiguilles d'une montre, comme le texte Tkinter) et les place en (cx, cy)."""
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for dx, dy in points:
        out += [cx + dx * ca + dy * sa, cy - dx * sa + dy * ca]
    return out


def find_cell(x, y):
    for i in range(BOARD_SIZE):
        x1, y1, x2, y2 = cell_rect(i)
        if x1 <= x < x2 and y1 <= y < y2:
            return i
    return None


class App:
    def __init__(self, root, players, state=None):
        """Crée une partie. state = dictionnaire de sauvegarde (pour reprendre une partie)."""
        self.root = root
        root.title("Monopoly v0.9")
        self.frame = tk.Frame(root)          # tout le jeu est dans ce cadre (détruit pour une nouvelle partie)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.build_menu()

        self.canvas = tk.Canvas(self.frame, width=BOARD_PX, height=BOARD_PX, bg="white",
                                highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, padx=5, pady=5)

        side = tk.Frame(self.frame)
        side.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.lbl_turn = tk.Label(side, font=(FONT, 14, "bold"))
        self.lbl_turn.pack(anchor="w")

        btns = tk.Frame(side)
        btns.pack(anchor="w", pady=(4, 0))
        self.btn_roll = tk.Button(btns, text="Lancer les dés", width=13, command=self.on_roll)
        self.btn_roll.pack(side=tk.LEFT, padx=(0, 4))
        self.btn_end = tk.Button(btns, text="Fin du tour", width=13, command=self.on_end)
        self.btn_end.pack(side=tk.LEFT)
        btns2 = tk.Frame(side)
        btns2.pack(anchor="w", pady=(4, 0))
        self.btn_manage = tk.Button(btns2, text="Gérer mes biens", width=13, command=self.on_manage)
        self.btn_manage.pack(side=tk.LEFT, padx=(0, 4))
        self.btn_trade = tk.Button(btns2, text="Échanger", width=13, command=self.on_trade)
        self.btn_trade.pack(side=tk.LEFT)

        self.auto_var = tk.BooleanVar(value=True)
        tk.Checkbutton(side, text="Fin de tour automatique", variable=self.auto_var,
                       command=self.on_auto_toggle).pack(anchor="w")
        self.lbl_auto = tk.Label(side, text="", fg="#777777", font=(FONT, 8, "italic"),
                                 wraplength=370, justify="left")
        self.lbl_auto.pack(anchor="w")
        self.lbl_bank = tk.Label(side, text="", fg="#555555", font=(FONT, 8))
        self.lbl_bank.pack(anchor="w")
        tk.Label(side, text="Survolez une case ou un titre pour voir sa carte.", fg="#4A6B50",
                 font=(FONT, 8, "italic")).pack(anchor="w")

        # un bloc par joueur : nom/argent + ses titres de propriété
        self.player_labels, self.chip_canvases = [], []
        compact = len(players) > 4
        for p in players:
            lbl = tk.Label(side, anchor="w", justify="left", font=(FONT, 9 if compact else 10, "bold"), fg=p.color)
            lbl.pack(anchor="w", fill=tk.X, pady=(2 if compact else 5, 0))
            chips = tk.Canvas(side, width=372, height=20 if compact else 24, highlightthickness=0)
            chips.pack(anchor="w")
            self.player_labels.append(lbl)
            self.chip_canvases.append(chips)

        log_frame = tk.Frame(side)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(6, 0))
        scroll = tk.Scrollbar(log_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text = tk.Text(log_frame, width=50, height=6 if compact else 10, font=("Consolas", 9),
                                yscrollcommand=scroll.set, state="disabled")
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=self.log_text.yview)

        self.shown = {p: p.position for p in players}   # position affichée (animation)
        self.last_card = {"chance": "", "community": ""}
        self.hover = None                                 # case dont on montre le titre
        self.auto_job = None                              # fin de tour programmée
        self.icon_tags = None                             # tag ajouté aux icônes dessinées
        self.font_cache = {}                              # polices mesurées (retour à la ligne)
        self.icon_k = 1                                   # échelle des icônes (réduites dans les cases)

        self.game = Game(players, self)
        if state:
            self.game.load_dict(state)
        self.draw_board()
        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<Leave>", lambda e: self.hide_deed())
        if state:
            self.log(f"Partie chargée. Au tour de {self.game.player.name}.")
        else:
            self.log("Nouvelle partie ! " + players[0].name + " commence.")
        self.refresh()
        if state:
            self.schedule_auto_end()

    # ==============================
    # Menu "Partie" : nouvelle partie, sauvegarde, chargement, classement
    # ==============================
    def build_menu(self):
        bar = tk.Menu(self.root)
        m = tk.Menu(bar, tearoff=0)
        m.add_command(label="Nouvelle partie", command=self.on_new_game)
        m.add_separator()
        m.add_command(label="Sauvegarder...", command=self.on_save)
        m.add_command(label="Charger...", command=self.on_load)
        m.add_separator()
        m.add_command(label="Classement", command=lambda: RankingWindow(self, final=False))
        m.add_command(label="Terminer la partie", command=self.on_finish)
        m.add_separator()
        m.add_command(label="Quitter", command=self.root.destroy)
        bar.add_cascade(label="Partie", menu=m)
        self.root.config(menu=bar)

    def close(self):
        """Détruit cette partie (avant d'en lancer ou d'en charger une autre)."""
        self.cancel_auto_end()
        self.frame.destroy()

    def on_new_game(self):
        if not self.game.over and not messagebox.askyesno("Nouvelle partie", "Abandonner la partie en cours ?"):
            return
        players = ask_players(self.root)
        if players:
            self.close()
            App(self.root, players)

    def on_save(self):
        path = filedialog.asksaveasfilename(title="Sauvegarder la partie", defaultextension=".json",
                                            filetypes=[("Partie Monopoly", "*.json")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.game.to_dict(), f, ensure_ascii=False, indent=1)
            self.log(f"Partie sauvegardée dans {path}")
        except OSError as e:
            messagebox.showerror("Sauvegarde", f"Impossible d'écrire le fichier :\n{e}")

    def on_load(self):
        path = filedialog.askopenfilename(title="Charger une partie",
                                          filetypes=[("Partie Monopoly", "*.json")])
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            players = Game.players_from_dict(data)
        except (OSError, ValueError, KeyError) as e:
            messagebox.showerror("Chargement", f"Fichier invalide :\n{e}")
            return
        self.close()
        App(self.root, players, state=data)

    def on_finish(self):
        if not self.game.over and messagebox.askyesno(
                "Terminer la partie", "Arrêter maintenant et classer les joueurs selon leur patrimoine ?"):
            self.game.finish()

    # ==============================
    # Méthodes appelées par Game
    # ==============================
    def log(self, text):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def ask(self, title, question):
        return messagebox.askyesno(title, question)

    def ask_bid(self, player, item, best, best_bid, minimum):
        current = f"Meilleure offre : {best_bid}€ ({best.name})" if best else "Aucune offre pour l'instant"
        return simpledialog.askinteger(
            "Enchères", f"{item['name']} (prix : {item['price']}€)\n{current}\n\n"
                        f"{player.name}, votre enchère ? (minimum {minimum}€, solde {player.money}€)\n"
                        f"Annuler = passer",
            minvalue=minimum, maxvalue=player.money, parent=self.root)

    def raise_funds(self, player, amount, creditor):
        """Le joueur doit réunir la somme : fenêtre modale pour vendre / hypothéquer."""
        self.refresh()
        ManageWindow(self, player, debt=(amount, creditor))

    def game_over(self, winner):
        self.cancel_auto_end()
        self.refresh()
        RankingWindow(self, final=True)

    def card_drawn(self, deck_name, text):
        self.last_card[deck_name] = text
        self.draw_dynamic()

    def pawn_moved(self, p, direction=1):
        """Déplace le pion case par case (direction 1 = avance, -1 = recule, 0 = saut direct)."""
        target, cur = p.position, self.shown[p]
        if direction == 0:
            steps = 0
        elif direction > 0:
            steps = (target - cur) % BOARD_SIZE
        else:
            steps = (cur - target) % BOARD_SIZE
        delay = 90 if steps <= 12 else 35                # les longs trajets vont plus vite
        try:
            for _ in range(steps):
                cur = (cur + direction) % BOARD_SIZE
                self.shown[p] = cur
                self.draw_dynamic()
                self.root.update()
                self.root.after(delay)
            self.shown[p] = target
            self.draw_dynamic()
            self.root.update()
        except tk.TclError:                              # fenêtre fermée pendant l'animation
            pass

    def refresh(self):
        g = self.game
        p = g.player
        for pl in g.players:
            self.shown[pl] = pl.position
        self.lbl_turn.config(text="Partie terminée" if g.over else f"Tour de {p.name}",
                             fg="black" if g.over else p.color)
        self.btn_roll.config(state=tk.NORMAL if g.can_roll() else tk.DISABLED)
        self.btn_end.config(state=tk.NORMAL if g.can_end_turn() else tk.DISABLED)
        busy = tk.DISABLED if g.over else tk.NORMAL
        self.btn_manage.config(state=busy)
        self.btn_trade.config(state=busy)
        self.lbl_bank.config(text=f"Banque : {g.houses_left} maison(s), {g.hotels_left} hôtel(s) disponibles")

        for pl, lbl, chips in zip(g.players, self.player_labels, self.chip_canvases):
            if not pl.active:
                txt = f"{pl.name} : faillite"
            else:
                txt = f"{pl.name} : {pl.money}€  (patrimoine {pl.money + g.assets_value(pl)}€)"
                if pl.in_jail:
                    txt += "  - en prison"
                if pl.jail_cards:
                    txt += f"  - {len(pl.jail_cards)} carte(s) prison"
            lbl.config(text=("> " if pl is p and not g.over else "   ") + txt)
            self.draw_chips(chips, pl)

        self.draw_dynamic()

    # ==============================
    # Fin de tour automatique
    # ==============================
    def schedule_auto_end(self):
        self.cancel_auto_end()
        g = self.game
        if not g.can_end_turn():
            return
        if g.has_actions(g.player):
            self.lbl_auto.config(text="Vous pouvez encore construire ou lever une hypothèque "
                                      "(« Gérer mes biens »), puis cliquez sur « Fin du tour ».")
        elif self.auto_var.get():
            self.lbl_auto.config(text="Plus d'action possible : fin du tour automatique...")
            self.auto_job = self.root.after(AUTO_END_DELAY, self.auto_end)

    def cancel_auto_end(self):
        if self.auto_job:
            self.root.after_cancel(self.auto_job)
            self.auto_job = None
        self.lbl_auto.config(text="")

    def auto_end(self):
        self.auto_job = None
        self.lbl_auto.config(text="")
        self.game.end_turn()

    def on_auto_toggle(self):
        if self.auto_var.get():
            self.schedule_auto_end()
        else:
            self.cancel_auto_end()

    # ---------- boutons ----------
    def on_roll(self):
        self.btn_roll.config(state=tk.DISABLED)   # évite les doubles clics pendant l'animation
        self.btn_end.config(state=tk.DISABLED)
        self.game.roll()
        self.refresh()
        self.schedule_auto_end()

    def on_end(self):
        self.cancel_auto_end()
        self.game.end_turn()

    def on_manage(self):
        self.cancel_auto_end()
        ManageWindow(self, self.game.player)

    def on_trade(self):
        if len([p for p in self.game.players if p.active]) < 2:
            return
        self.cancel_auto_end()
        TradeWindow(self, self.game.player)

    def after_action(self):
        """Après une fenêtre (gestion, échange) : on redessine et on réévalue la fin de tour."""
        self.refresh()
        self.schedule_auto_end()

    # ==============================
    # Petits outils de dessin
    # ==============================
    # ---------- texte ----------
    # Les tailles sont converties en PIXELS (taille négative pour Tkinter) : le rendu est
    # le même quel que soit le réglage d'échelle de Windows.
    def font(self, size, bold=False):
        px = max(6, round(size * 1.33))
        return (FONT, -px, "bold") if bold else (FONT, -px)

    def measure(self, txt, size, bold=False):
        """Largeur en pixels de la plus longue ligne de txt."""
        key = (size, bold)
        if key not in self.font_cache:
            f = self.font(size, bold)
            self.font_cache[key] = tkfont.Font(root=self.root, family=f[0], size=f[1],
                                               weight="bold" if bold else "normal")
        return max(self.font_cache[key].measure(line) for line in txt.split("\n"))

    def wrap(self, txt, size, bold, max_px):
        """Coupe le texte en lignes de max_px pixels, sans jamais couper un mot."""
        lines = []
        for para in txt.split("\n"):
            cur = ""
            for word in para.split(" "):
                test = (cur + " " + word).strip()
                if cur and self.measure(test, size, bold) > max_px:
                    lines.append(cur)
                    cur = word
                else:
                    cur = test
            lines.append(cur)
        return "\n".join(lines)

    def text(self, xy, txt, size=7, bold=False, angle=0, width=None, fill="black", tags=None,
             fit=None, **kw):
        """Écrit un texte.
        width = largeur max : retour à la ligne entre les mots (jamais au milieu d'un mot).
        fit   = largeur max : réduit la taille jusqu'à ce que chaque ligne rentre.
        Un texte tourné de plusieurs lignes est écrit ligne par ligne (Tkinter les place mal sinon)."""
        if width:
            txt = self.wrap(txt, size, bold, width)
        if fit:
            while size > 4.6 and self.measure(txt, size, bold) > fit:
                size -= 0.25
        opts = {"font": self.font(size, bold), "fill": fill, "justify": "center"}
        if tags:
            opts["tags"] = tags
        opts.update(kw)
        angle %= 360
        lines = txt.split("\n")
        if angle == 0 or len(lines) == 1:
            if angle:
                opts["angle"] = angle
            return self.canvas.create_text(xy[0], xy[1], text=txt, **opts)
        line_h = round(size * 1.33 * 1.2)
        item = None
        for k, line in enumerate(lines):
            x, y = rotate([(0, (k - (len(lines) - 1) / 2) * line_h)], xy[0], xy[1], angle)
            item = self.canvas.create_text(x, y, text=line, angle=angle, **opts)
        return item

    def poly(self, pts, cx, cy, angle, canvas=None, **kw):
        if self.icon_tags and "tags" not in kw:
            kw["tags"] = self.icon_tags
        k = self.icon_k
        pts = [(x * k, y * k) for x, y in pts]
        return (canvas or self.canvas).create_polygon(rotate(pts, cx, cy, angle), **kw)

    def rot_rect(self, cx, cy, w, h, angle, **kw):
        """Rectangle de taille w x h centré en (cx, cy) et tourné."""
        return self.poly([(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)],
                         cx, cy, angle, **kw)

    def circle(self, cx, cy, r, canvas=None, **kw):
        if self.icon_tags and "tags" not in kw:
            kw["tags"] = self.icon_tags
        r *= self.icon_k
        return (canvas or self.canvas).create_oval(cx - r, cy - r, cx + r, cy + r, **kw)

    def at_rot(self, cx, cy, angle, dx, dy):
        """Point (dx, dy) d'un repère tourné, centré en (cx, cy)."""
        x, y = rotate([(dx * self.icon_k, dy * self.icon_k)], cx, cy, angle)
        return x, y

    # ==============================
    # Plateau fixe (dessiné une seule fois)
    # ==============================
    def draw_board(self):
        c = self.canvas
        c.create_rectangle(MARGIN, MARGIN, EDGE, EDGE, fill=BOARD_BG, outline="black", width=2)
        for i, cell in enumerate(self.game.board):
            x1, y1, x2, y2 = cell_rect(i)
            c.create_rectangle(x1, y1, x2, y2, fill=BOARD_BG, outline="black")
            if i % 10 == 0:
                self.draw_corner(i)
            else:
                self.draw_side_cell(i, cell)
        c.create_rectangle(INNER_A, INNER_A, INNER_B, INNER_B, outline="black", width=2)
        self.draw_center()

    def draw_side_cell(self, i, cell):
        """Disposition d'une case (v = distance au bord intérieur, 0..90) :
            0-17  bande de couleur      18-50  nom (et icône)
           51-74  ZONE DES PIONS (vide) 75-85  prix        86-90  bande du propriétaire"""
        c = self.canvas
        to, angle = cell_frame(i)
        t = cell["type"]
        w = SIDE - 4
        mid_u = SIDE / 2
        price_v = PRICE_V

        def name(top, txt, size=6.5, bold=False, max_bottom=50):
            """Nom collé en haut : centre calculé d'après le nombre de lignes."""
            n = txt.count("\n") + 1
            line_h = size * 1.33 * 1.2
            while top + n * line_h > max_bottom and size > 4.6:   # trop haut : on réduit
                size -= 0.25
                line_h = size * 1.33 * 1.2
            self.text(to(mid_u, top + n * line_h / 2), txt, size, bold, angle, fit=w)

        def icon(draw, v, k):
            self.icon_k = k
            draw(*to(mid_u, v), angle)
            self.icon_k = 1

        if t == "property":
            pts = [to(0, 0), to(SIDE, 0), to(SIDE, BAND), to(0, BAND)]
            c.create_polygon([k for p in pts for k in p], fill=GROUP_COLORS[cell["color"]], outline="black")
            name(BAND + 2, cell["short"])
            self.text(to(mid_u, price_v), f"{cell['price']} €", 6, False, angle)
        elif t == "station":
            name(3, cell["short"], max_bottom=30)
            icon(self.icon_train, 40, 0.72)
            self.text(to(mid_u, price_v), "200 €", 6, False, angle)
        elif t == "utility":
            name(3, cell["short"], max_bottom=30)
            icon(self.icon_faucet if "eaux" in cell["name"] else self.icon_bulb, 41, 0.62)
            self.text(to(mid_u, price_v), "150 €", 6, False, angle)
        elif t == "chance":
            self.text(to(mid_u, 9), "CHANCE", 6, False, angle)
            self.text(to(mid_u, 33), "?", 21, True, angle, fill=CHANCE_COLORS.get(i, "#E8730C"))
        elif t == "community":
            name(3, cell["short"], max_bottom=24)
            icon(self.icon_chest, 37, 0.8)
        elif t == "tax":
            name(3, cell["short"], 7 if cell["amount"] == 100 else 6.5, cell["amount"] == 100, max_bottom=28)
            icon(self.icon_ring if cell["amount"] == 100 else self.icon_diamond, 39, 0.75)
            self.text(to(mid_u, price_v), f"PAYEZ {cell['amount']} €", 6, False, angle, fit=w)

    def draw_corner(self, i):
        c = self.canvas
        x1, y1, x2, y2 = cell_rect(i)
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        if i == 0:                        # Départ : texte en diagonale + flèche rouge
            a = 45
            bx, by = cx - 6, cy - 14                  # bloc en haut à gauche : le bas à droite reste aux pions
            self.text(self.at_rot(bx - 2, by + 2, a, 0, -15), "RECEVEZ 200 €\nCHAQUE FOIS QUE\nVOUS PASSEZ ICI",
                      5, False, a, fit=42)
            self.text(self.at_rot(bx, by, a, 0, 7), "DÉPART", 12, True, a, fit=64)
            c.create_polygon(x1 + 6, y2 - 11, x1 + 20, y2 - 19, x1 + 20, y2 - 14, x1 + 56, y2 - 14,
                             x1 + 56, y2 - 8, x1 + 20, y2 - 8, x1 + 20, y2 - 3,
                             fill="#D7261E", outline="black")
        elif i == JAIL_POS:               # Prison : carré orange + bande "Simple visite"
            jx1, jy2 = x1 + JAIL_STRIP, y2 - JAIL_STRIP
            c.create_rectangle(jx1, y1, x2, jy2, fill="#F7941D", outline="black", width=2)
            for k in range(1, 5):
                bx = jx1 + k * (x2 - jx1) / 5
                c.create_line(bx, y1 + 3, bx, jy2 - 3, width=2, fill="#5A3A1A")
            jcx, jcy = (jx1 + x2) / 2, (y1 + jy2) / 2
            c.create_polygon(rotate([(-32, -8), (32, -8), (32, 8), (-32, 8)], jcx, jcy, 45),
                             fill="white", outline="black")
            self.text((jcx, jcy), "EN PRISON", 7, True, 45, fit=56)
            # textes poussés aux bouts de la bande : l'angle en bas à gauche reste aux visiteurs
            self.text((x1 + JAIL_STRIP / 2, y1 + 26), "SIMPLE", 6.5, True, 90)
            self.text((x2 - 24, y2 - JAIL_STRIP / 2), "VISITE", 6.5, True)
        elif i == 20:                     # Parc Gratuit : diagonale tournée vers le centre
            a = -135
            self.text(self.at_rot(cx, cy, a, 0, -24), "PARC", 10, True, a)
            self.icon_car(cx, cy, a)
            self.text(self.at_rot(cx, cy, a, 0, 21), "GRATUIT", 9, True, a)
        elif i == 30:                     # Allez en prison
            a = 135
            self.text(self.at_rot(cx, cy, a, 0, -25), "ALLEZ EN", 9, True, a)
            self.icon_police(cx, cy, a)
            self.text(self.at_rot(cx, cy, a, 0, 22), "PRISON", 9, True, a)

    def draw_center(self):
        c = self.canvas
        # paquets de cartes inclinés : Caisse en haut à gauche, Chance en bas à droite
        # (les décors restent à plus de PAWN_LANE pixels du bord : cette bande est réservée aux pions)
        self.decks_pos = {"community": (MID - 132, MID - 132), "chance": (MID + 132, MID + 132)}
        dcx, dcy = self.decks_pos["community"]
        self.rot_rect(dcx, dcy, 150, 92, 45, fill="#BFE3F5", outline="#1E88C8", width=3)
        self.text(self.at_rot(dcx, dcy, 45, 0, -34), "CAISSE DE COMMUNAUTÉ", 8, True, 45, fill="#0B5E8E", fit=132)
        self.icon_chest(*self.at_rot(dcx, dcy, 45, -54, 22), 45, small=True)
        dcx, dcy = self.decks_pos["chance"]
        self.rot_rect(dcx, dcy, 150, 92, 45, fill="#F9B66A", outline="#C25E00", width=3)
        self.text(self.at_rot(dcx, dcy, 45, 0, -34), "CHANCE", 8, True, 45, fill="#8A3F00")
        self.text(self.at_rot(dcx, dcy, 45, -58, 24), "?", 15, True, 45, fill="white")
        # logo en diagonale
        self.rot_rect(MID, MID, 370, 72, 45, fill="#D7261E", outline="black", width=2)
        self.rot_rect(MID, MID, 356, 58, 45, fill="", outline="white", width=2)
        self.text((MID, MID), "MONOPOLY", 32, True, 45, fill="white")

    # ==============================
    # Icônes (dessinées dans un repère droit, puis tournées)
    # ==============================
    def icon_train(self, cx, cy, angle):
        self.poly([(-16, -3), (5, -3), (5, -12), (14, -12), (14, -3), (17, -3), (17, 7), (-16, 7)],
                  cx, cy, angle, fill="#222222", outline="black")
        self.poly([(-13, -10), (-7, -10), (-7, -3), (-13, -3)], cx, cy, angle, fill="#222222")
        for dx in (-10, 0, 11):
            self.circle(*self.at_rot(cx, cy, angle, dx, 9), 4, fill="#222222", outline="#888888")

    def icon_bulb(self, cx, cy, angle):
        self.circle(*self.at_rot(cx, cy, angle, 0, -4), 10, fill="#FEF200", outline="black")
        self.poly([(-5, 5), (5, 5), (5, 13), (-5, 13)], cx, cy, angle, fill="#999999", outline="black")
        for dx, dy in ((-15, -12), (15, -12), (0, -19), (-17, -2), (17, -2)):   # rayons
            x0, y0 = self.at_rot(cx, cy, angle, dx * 0.8, dy * 0.8)
            x1, y1 = self.at_rot(cx, cy, angle, dx, dy)
            self.canvas.create_line(x0, y0, x1, y1, width=1, tags=self.icon_tags or "")

    def icon_faucet(self, cx, cy, angle):
        self.poly([(-16, -6), (6, -6), (6, 1), (-16, 1)], cx, cy, angle, fill="#CFCFCF", outline="black")
        self.poly([(0, 1), (7, 1), (7, 9), (0, 9)], cx, cy, angle, fill="#CFCFCF", outline="black")
        self.poly([(-3, -6), (-3, -12), (1, -12), (1, -6)], cx, cy, angle, fill="#CFCFCF", outline="black")
        self.poly([(-9, -12), (7, -12), (7, -15), (-9, -15)], cx, cy, angle, fill="#CFCFCF", outline="black")
        self.poly([(3.5, 11), (6, 15), (3.5, 17), (1, 15)], cx, cy, angle, fill="#3BA3E0", outline="#1E6FA0")

    def icon_chest(self, cx, cy, angle, small=False):
        k = 0.8 if small else 1
        pts_body = [(-14, -2), (14, -2), (14, 11), (-14, 11)]
        pts_lid = [(-14, -2), (-14, -8), (-8, -13), (8, -13), (14, -8), (14, -2)]
        self.poly([(x * k, y * k) for x, y in pts_body], cx, cy, angle, fill="#3BA3E0", outline="black")
        self.poly([(x * k, y * k) for x, y in pts_lid], cx, cy, angle, fill="#7CC6EF", outline="black")
        self.poly([(x * k, y * k) for x, y in [(-3, -4), (3, -4), (3, 3), (-3, 3)]], cx, cy, angle,
                  fill="#FEF200", outline="black")

    def icon_diamond(self, cx, cy, angle):
        self.poly([(0, -7), (7, 0), (0, 7), (-7, 0)], cx, cy, angle, fill="", outline="black", width=2)
        self.poly([(0, -3), (3, 0), (0, 3), (-3, 0)], cx, cy, angle, fill="black")

    def icon_ring(self, cx, cy, angle):
        rx, ry = self.at_rot(cx, cy, angle, 0, 3)
        self.circle(rx, ry, 11, fill="", outline="#C9A227", width=4)
        self.poly([(-6, -9), (-3, -14), (3, -14), (6, -9), (0, -4)], cx, cy, angle,
                  fill="#BFE9F5", outline="#0072BB")

    def icon_car(self, cx, cy, angle):
        body = [(-24, 6), (-24, -2), (-12, -4), (-6, -12), (10, -12), (16, -4), (24, -2), (24, 6)]
        self.poly(body, cx, cy, angle, fill="#D7261E", outline="black")
        self.poly([(-4, -10), (8, -10), (12, -4), (-8, -4)], cx, cy, angle, fill="#BFE9F5", outline="black")
        for dx in (-13, 13):
            self.circle(*self.at_rot(cx, cy, angle, dx, 7), 5, fill="#222222", outline="black")

    def icon_police(self, cx, cy, angle):
        self.circle(*self.at_rot(cx, cy, angle, 0, 4), 11, fill="#F5CBA7", outline="black")      # visage
        self.poly([(-14, -4), (14, -4), (10, -16), (-10, -16)], cx, cy, angle,
                  fill="#1F3A93", outline="black")                                              # képi
        self.poly([(-16, -5), (16, -5), (16, -2), (-16, -2)], cx, cy, angle, fill="#111111")     # visière
        self.circle(*self.at_rot(cx, cy, angle, 0, -11), 2, fill="#FEF200", outline="")         # insigne
        for dx in (-4, 4):
            self.circle(*self.at_rot(cx, cy, angle, dx, 3), 1.5, fill="black")                  # yeux

    # ==============================
    # Dessin dynamique (tag "dyn") : propriétaires, maisons, pions, dés, cartes
    # ==============================
    def draw_dynamic(self):
        c = self.canvas
        g = self.game
        c.delete("dyn")

        for i, cell in enumerate(g.board):
            if i % 10 == 0:
                continue
            to, angle = cell_frame(i)
            owner = cell.get("owner")
            if owner:   # bande de la couleur du propriétaire, côté extérieur
                pts = [to(0, CORNER - 4), to(SIDE, CORNER - 4), to(SIDE, CORNER), to(0, CORNER)]
                c.create_polygon([k for p in pts for k in p], fill=owner.color, outline="black", tags="dyn")
            if cell.get("houses"):
                self.draw_houses(i, cell["houses"])
            if cell.get("mortgaged"):   # terrain hypothéqué : croix rouge + mention
                x1, y1, x2, y2 = cell_rect(i)
                c.create_line(x1 + 3, y1 + 3, x2 - 3, y2 - 3, fill="#C0392B", width=2, tags="dyn")
                c.create_line(x2 - 3, y1 + 3, x1 + 3, y2 - 3, fill="#C0392B", width=2, tags="dyn")

        cur = g.player
        if not g.over:   # case du joueur actif encadrée
            x1, y1, x2, y2 = cell_rect(self.shown[cur])
            c.create_rectangle(x1 + 1, y1 + 1, x2 - 1, y2 - 1, outline=cur.color, width=3, tags="dyn")

        initials = [pl.name[:1].upper() for pl in g.players]
        if len(set(initials)) < len(initials):   # deux noms avec la même initiale : on numérote
            initials = [str(k + 1) for k in range(len(g.players))]
        for k, p in enumerate(g.players):   # pions
            if p.active:
                x, y = self.pawn_xy(p, k)
                r = (7 if p is cur else 6) if len(g.players) <= 4 else (6 if p is cur else 5)
                self.circle(x, y, r, fill=p.color, outline="white", width=2, tags="dyn")
                self.text((x, y), initials[k], 7, True, fill="white", tags="dyn")

        for name, (dx, dy) in self.decks_pos.items():   # dernières cartes tirées
            txt = self.last_card[name] or "(aucune carte tirée)"
            self.text(self.at_rot(dx, dy, 45, 4, 8), txt, 8.5, False, 45, width=118, tags="dyn",
                      fill="black" if self.last_card[name] else "#555555")

        # dés (en haut à droite du centre) et joueur actif (en bas à gauche)
        d1, d2 = g.last_dice
        self.draw_die(MID + 200, MID - 148, d1)   # l'un au-dessus de l'autre, hors des bandes des pions
        self.draw_die(MID + 200, MID - 104, d2)
        if g.over:
            winner = [p for p in g.players if p.active][0]
            self.text((MID - 125, MID + 195), f"Victoire de\n{winner.name} !", 12, True, fit=100, tags="dyn")
        else:
            self.text((MID - 125, MID + 195), f"Tour de\n{cur.name}", 12, True, fill=cur.color, fit=100, tags="dyn")

        if self.hover is not None:
            self.draw_info(self.hover)

    def draw_die(self, cx, cy, value):
        s = 18
        self.canvas.create_rectangle(cx - s, cy - s, cx + s, cy + s, fill="white",
                                     outline="black", width=2, tags="dyn")
        pips = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)],
                4: [(-1, -1), (1, -1), (-1, 1), (1, 1)],
                5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)],
                6: [(-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)]}
        for px, py in pips.get(value, []):
            self.circle(cx + px * 10, cy + py * 10, 3.5, fill="black", tags="dyn")

    def draw_houses(self, i, n):
        to, angle = cell_frame(i)
        if n >= 5:   # hôtel
            self.poly([(-12, -5), (12, -5), (12, 5), (-12, 5)], *to(SIDE / 2, BAND / 2), angle,
                      fill="#D0021B", outline="black", tags="dyn")
            return
        for k in range(n):
            self.poly([(-5, 6), (-5, -1), (0, -6), (5, -1), (5, 6)], *to(7 + k * 14, BAND / 2), angle,
                      fill="#2E8B37", outline="black", tags="dyn")

    def pawn_xy(self, p, k):
        """Position du pion du k-ième joueur, DANS sa case, sans recouvrir textes ni icônes :
        - case d'un côté : zone réservée au milieu de la case (entre le nom et le prix) ;
        - coin : places libres repérées autour des dessins (CORNER_SLOTS) ;
        - en prison : derrière les barreaux, dans les triangles libres de part et d'autre de "EN PRISON"."""
        pos = self.shown[p]
        many = len(self.game.players) > 4
        x1, y1, x2, y2 = cell_rect(pos)
        if pos == JAIL_POS and p.in_jail:
            sx, sy = JAIL_SLOTS[k]
            return x1 + JAIL_STRIP + sx, y1 + sy
        if pos % 10 == 0:
            sx, sy = (CORNER_SLOTS_8 if many else CORNER_SLOTS_4)[pos][k]
            return x1 + sx, y1 + sy
        to, angle = cell_frame(pos)
        if many:   # 2 rangées de 4
            return to(9.5 + (k % 4) * 12.3, PAWN_V - 6 + (k // 4) * 12)
        return to(9.5 + k * 12.3, PAWN_V)

    # ==============================
    # Titres de propriété des joueurs (panneau de droite)
    # ==============================
    def draw_chips(self, chips, player):
        chips.delete("all")
        for k, idx in enumerate(sorted(player.properties)):
            cell = self.game.board[idx]
            x = 2 + k * 13
            if cell["type"] == "property":
                fill, label = GROUP_COLORS[cell["color"]], str(cell["houses"]) if cell["houses"] else ""
                if cell["houses"] == 5:
                    label = "H"
            elif cell["type"] == "station":
                fill, label = "#222222", "G"
            else:
                fill, label = "#E8E8E8", "C"
            tag = f"chip{idx}"
            h = int(chips.cget("height")) - 2
            chips.create_rectangle(x, 2, x + 11, h, fill=fill, outline="black", tags=tag)
            if label:
                fg = "white" if cell.get("color") in DARK_GROUPS or cell["type"] == "station" else "black"
                chips.create_text(x + 6, (h + 2) / 2, text=label, font=(FONT, 7, "bold"), fill=fg, tags=tag)
            if cell["mortgaged"]:   # titre retourné (hypothéqué)
                chips.create_rectangle(x, 2, x + 11, h, fill="white", outline="#C0392B", width=2, tags=tag)
                chips.create_line(x, 2, x + 11, h, fill="#C0392B", width=2, tags=tag)
            chips.tag_bind(tag, "<Enter>", lambda e, i=idx: self.show_deed(i))
            chips.tag_bind(tag, "<Leave>", lambda e: self.hide_deed())
        if not player.properties:
            chips.create_text(4, int(chips.cget("height")) / 2, text="aucun titre", anchor="w", font=(FONT, 8, "italic"), fill="#999999")

    # ==============================
    # Titre de propriété (carte affichée au centre)
    # ==============================
    def on_motion(self, event):
        i = find_cell(event.x, event.y)
        if i != self.hover:
            if i is None:
                self.hide_deed()
            else:
                self.show_deed(i)

    def show_deed(self, i):
        self.hover = i
        self.draw_info(i)

    def hide_deed(self):
        self.hover = None
        self.canvas.delete("info")

    def deed_content(self, i):
        """Contenu du titre : (en-tête, lignes, état).
        lignes : ("row", gauche, droite, actif) / ("sep",) / ("note", texte, actif)"""
        g = self.game
        cell = g.board[i]
        t = cell["type"]
        owner = cell.get("owner")
        lines, status = [], []

        if t == "property":
            r, houses = cell["rent"], cell["houses"]
            group_full = owner is not None and g.owns_group(owner, cell["color"])
            active = None
            if owner:
                active = houses if houses else ("group" if group_full else 0)
            lines = [("row", "LOYER Terrain nu", f"{r[0]} €", active == 0),
                     ("row", "Avec 1 Maison", f"{r[1]} €", active == 1),
                     ("row", "Avec 2 Maisons", f"{r[2]} €", active == 2),
                     ("row", "Avec 3 Maisons", f"{r[3]} €", active == 3),
                     ("row", "Avec 4 Maisons", f"{r[4]} €", active == 4),
                     ("row", "Avec HÔTEL", f"{r[5]} €", active == 5),
                     ("sep",),
                     ("row", "Prix des Maisons", f"{cell['house_price']} € chacune", False),
                     ("row", "Prix d'un Hôtel", f"{cell['house_price']} € + 4 maisons", False),
                     ("row", "Valeur hypothécaire", f"{cell['mortgage']} €", False),
                     ("sep",),
                     ("note", "Si un joueur possède TOUS les terrains\nd'un groupe de couleur, le loyer des\n"
                              "terrains nus de ce groupe est doublé.", active == "group")]
            if owner:
                n, total = g.group_count(owner, cell["color"])
                status.append((f"Groupe : {n}/{total} terrain(s) à {owner.name}", "black"))
            header = ("title", GROUP_COLORS[cell["color"]],
                      "white" if cell["color"] in DARK_GROUPS else "black")
        elif t == "station":
            n = g.count_owned(owner, "station") if owner else 0
            lines = [("row", "LOYER", "25 €", n == 1),
                     ("row", "Si 2 gares sont possédées", "50 €", n == 2),
                     ("row", "Si 3 gares sont possédées", "100 €", n == 3),
                     ("row", "Si 4 gares sont possédées", "200 €", n == 4),
                     ("sep",),
                     ("row", "Valeur hypothécaire", "100 €", False)]
            if owner:
                status.append((f"{owner.name} possède {n} gare(s)", "black"))
            header = ("icon", "station")
        elif t == "utility":
            n = g.count_owned(owner, "utility") if owner else 0
            lines = [("note", "Si l'on possède UNE carte de compagnie,\nle loyer est 4 fois le montant\n"
                              "indiqué par les dés.", n == 1),
                     ("note", "Si l'on possède les DEUX cartes de\ncompagnie, le loyer est 10 fois le\n"
                              "montant indiqué par les dés.", n == 2),
                     ("sep",),
                     ("row", "Valeur hypothécaire", "75 €", False)]
            header = ("icon", "eaux" if "eaux" in cell["name"] else "elec")
        else:
            desc = {
                "start": "Recevez 200 € chaque fois que vous\npassez ou vous arrêtez sur la\ncase Départ.",
                "jail": "Simple visite : rien ne se passe.\n\nEn prison : 3 tentatives pour faire\nun double, "
                        "ou payez 50 € avant de\nlancer, ou utilisez une carte\n« Libéré de prison ».\n"
                        "Au 3e échec, payez 50 € et avancez.\nEn prison, on touche ses loyers.",
                "free_parking": "Case de repos : rien ne se passe.\n(Aucun argent à gagner ici,\nselon "
                                "les règles officielles.)",
                "go_to_jail": "Allez directement en prison, sans\npasser par la case Départ ni\nrecevoir 200 €.",
                "chance": "Tirez une carte Chance et suivez\nses instructions.",
                "community": "Tirez une carte Caisse de\ncommunauté et suivez ses\ninstructions.",
                "tax": f"Payez {cell.get('amount', 0)} € à la banque.",
            }[t]
            lines = [("note", desc, False)]
            header = ("plain",)

        if t in ("property", "station", "utility"):
            if owner and cell["mortgaged"]:
                status.insert(0, (f"Propriétaire : {owner.name}", owner.color))
                status.append((f"HYPOTHÉQUÉ - lever : {self.game.unmortgage_cost(i)} €", "#C0392B"))
                status.append(("Loyer actuel : 0 €", "black"))
            elif owner:
                status.insert(0, (f"Propriétaire : {owner.name}", owner.color))
                if t == "utility":
                    status.append((f"Loyer actuel : {4 if n == 1 else 10} × les dés", "black"))
                else:
                    status.append((f"Loyer actuel : {g.compute_rent(i)} €", "black"))
            else:
                status.append((f"À vendre : {cell['price']} €", "#2E8B37"))
        return header, lines, status

    def draw_info(self, i):
        c = self.canvas
        cell = self.game.board[i]
        owner = cell.get("owner")
        header, lines, status = self.deed_content(i)
        c.delete("info")
        tag = "info"
        w = 240
        head_h = 56 if header[0] != "icon" else 64
        if header[0] == "plain":
            head_h = 40
        body_h = 0
        for ln in lines:
            if ln[0] == "row":
                body_h += 17
            elif ln[0] == "sep":
                body_h += 9
            else:
                body_h += (ln[1].count("\n") + 1) * 12 + 8
        status_h = len(status) * 16 + 12 if status else 0
        h = 10 + head_h + 10 + body_h + 6 + status_h + 8
        x1, y1 = MID - w / 2, MID - h / 2
        x2, y2 = x1 + w, y1 + h

        c.create_rectangle(x1 + 5, y1 + 5, x2 + 5, y2 + 5, fill="#6E8E73", outline="", tags=tag)   # ombre
        c.create_rectangle(x1, y1, x2, y2, fill="white", outline="black", width=2, tags=tag)
        c.create_rectangle(x1 + 5, y1 + 5, x2 - 5, y2 - 5 - status_h, outline="#444444", tags=tag)

        # en-tête
        hy1, hy2 = y1 + 10, y1 + 10 + head_h
        if header[0] == "title":
            _, fill, fg = header
            c.create_rectangle(x1 + 10, hy1, x2 - 10, hy2, fill=fill, outline="black", tags=tag)
            self.text((MID, hy1 + 13), "TITRE DE PROPRIÉTÉ", 7, False, fill=fg, tags=tag)
            self.text((MID, hy1 + 36), cell["name"].upper(), 10, True, width=w - 30, fill=fg, tags=tag)
        elif header[0] == "icon":
            ix, iy = MID, hy1 + 18
            self.icon_tags = tag   # les formes de l'icône appartiennent à la carte
            {"station": self.icon_train, "eaux": self.icon_faucet, "elec": self.icon_bulb}[header[1]](ix, iy, 0)
            self.icon_tags = None
            self.text((MID, hy1 + 50), cell["name"].upper(), 9, True, width=w - 30, tags=tag)
        else:
            self.text((MID, hy1 + head_h / 2), cell["name"].upper(), 11, True, width=w - 30, tags=tag)

        # lignes
        y = hy2 + 10
        hl = owner.color if owner else "black"
        for ln in lines:
            if ln[0] == "sep":
                c.create_line(x1 + 16, y + 3, x2 - 16, y + 3, fill="#AAAAAA", tags=tag)
                y += 9
            elif ln[0] == "row":
                _, left, right, active = ln
                active = active and not cell.get("mortgaged")   # hypothéqué : aucun loyer en cours
                if active:
                    c.create_rectangle(x1 + 10, y - 1, x2 - 10, y + 15, fill="#FFF3B0", outline="", tags=tag)
                col = hl if active else "black"
                self.text((x1 + 16, y + 7), left, 8, active, anchor="w", justify="left", fill=col, tags=tag)
                self.text((x2 - 16, y + 7), right, 8, active, anchor="e", justify="right", fill=col, tags=tag)
                y += 17
            else:
                _, txt, active = ln
                active = active and not cell.get("mortgaged")
                nb = txt.count("\n") + 1
                if active:
                    c.create_rectangle(x1 + 10, y, x2 - 10, y + nb * 12 + 4, fill="#FFF3B0", outline="", tags=tag)
                self.text((MID, y + 2 + nb * 6), txt, 7 if header[0] != "plain" else 8, active,
                          fill=hl if active else "#333333", tags=tag)
                y += nb * 12 + 8

        # état actuel (propriétaire, groupe, loyer)
        if status:
            sy = y2 - status_h
            c.create_rectangle(x1 + 2, sy, x2 - 2, y2 - 2, fill="#EEF3EE", outline="", tags=tag)
            for k, (txt, col) in enumerate(status):
                self.text((MID, sy + 12 + k * 16), txt, 8, k == 0, fill=col, tags=tag)
        c.tag_raise("info")


# ==============================
# Fenêtre "Gérer mes biens" (aussi utilisée quand un joueur doit réunir une somme)
# ==============================
class ManageWindow:
    def __init__(self, app, player, debt=None):
        """debt = (montant, créancier) : le joueur doit réunir cette somme avant de fermer."""
        self.app, self.game, self.player, self.debt = app, app.game, player, debt
        self.top = tk.Toplevel(app.root)
        self.top.title(f"Biens de {player.name}")
        self.top.transient(app.root)
        self.top.resizable(False, False)
        self.body = tk.Frame(self.top, padx=10, pady=8)
        self.body.pack(fill=tk.BOTH, expand=True)
        self.build()
        self.top.grab_set()                         # fenêtre modale
        if debt:
            self.top.protocol("WM_DELETE_WINDOW", lambda: None)   # on doit payer ou faire faillite
            app.root.wait_window(self.top)          # le jeu attend la décision
        else:
            self.top.protocol("WM_DELETE_WINDOW", self.close)

    def build(self):
        for w in self.body.winfo_children():
            w.destroy()
        g, p = self.game, self.player
        tk.Label(self.body, text=f"{p.name} - {p.money}€", font=(FONT, 13, "bold"), fg=p.color).grid(
            row=0, column=0, columnspan=6, sticky="w")
        tk.Label(self.body, text=f"Banque : {g.houses_left} maison(s), {g.hotels_left} hôtel(s)",
                 fg="#555555").grid(row=1, column=0, columnspan=6, sticky="w")
        if self.debt:
            amount, creditor = self.debt
            to = creditor.name if creditor else "la banque"
            tk.Label(self.body, text=f"Vous devez {amount}€ à {to}. Vendez des bâtiments ou hypothéquez "
                                     f"des terrains pour réunir la somme.",
                     fg="#C0392B", font=(FONT, 10, "bold"), wraplength=520, justify="left").grid(
                row=2, column=0, columnspan=6, sticky="w", pady=(4, 6))

        row = 3
        if not p.properties:
            tk.Label(self.body, text="Aucun titre de propriété.", fg="#777777").grid(row=row, column=0, sticky="w")
        for idx in sorted(p.properties):
            cell = g.board[idx]
            color = GROUP_COLORS.get(cell.get("color"), "#222222" if cell["type"] == "station" else "#DDDDDD")
            tk.Label(self.body, bg=color, width=2).grid(row=row, column=0, padx=(0, 6), pady=1, sticky="ns")
            tk.Label(self.body, text=cell["name"], anchor="w", width=30).grid(row=row, column=1, sticky="w")
            if cell["mortgaged"]:
                state = "hypothéqué"
            elif cell.get("houses") == 5:
                state = "hôtel"
            elif cell.get("houses"):
                state = f"{cell['houses']} maison(s)"
            else:
                state = ""
            tk.Label(self.body, text=state, width=11, anchor="w",
                     fg="#C0392B" if cell["mortgaged"] else "black").grid(row=row, column=2, sticky="w")

            if cell["type"] == "property":
                hp = cell["house_price"]
                label = f"+ Hôtel ({hp}€)" if cell["houses"] == 4 else f"+ Maison ({hp}€)"
                ok = g.can_build(p, idx) and not self.debt
                b = tk.Button(self.body, text=label, width=15, state=tk.NORMAL if ok else tk.DISABLED,
                              command=lambda i=idx: self.do(self.game.request_build, i))
                b.grid(row=row, column=3, padx=2)
                ok = g.can_sell_building(p, idx)
                tk.Button(self.body, text=f"Vendre (+{hp // 2}€)", width=12,
                          state=tk.NORMAL if ok else tk.DISABLED,
                          command=lambda i=idx: self.do(self.game.sell_building, i)).grid(row=row, column=4, padx=2)
            if cell["mortgaged"]:
                cost = g.unmortgage_cost(idx)
                ok = g.can_unmortgage(p, idx) and not self.debt
                tk.Button(self.body, text=f"Lever (-{cost}€)", width=15, state=tk.NORMAL if ok else tk.DISABLED,
                          command=lambda i=idx: self.do(self.game.unmortgage, i)).grid(row=row, column=5, padx=2)
            else:
                ok = g.can_mortgage(p, idx)
                tk.Button(self.body, text=f"Hypothéquer (+{cell['mortgage']}€)", width=15,
                          state=tk.NORMAL if ok else tk.DISABLED,
                          command=lambda i=idx: self.do(self.game.mortgage, i)).grid(row=row, column=5, padx=2)
            row += 1

        tk.Label(self.body, text="Règles : on construit sur un groupe complet, de façon égale ; on hypothèque "
                                 "après avoir vendu les bâtiments du groupe ; lever coûte la valeur + 10 %.",
                 fg="#777777", font=(FONT, 8), wraplength=560, justify="left").grid(
            row=row, column=0, columnspan=6, sticky="w", pady=(8, 4))
        row += 1
        bottom = tk.Frame(self.body)
        bottom.grid(row=row, column=0, columnspan=6, sticky="e", pady=(4, 0))
        if self.debt:
            amount, _ = self.debt
            tk.Button(bottom, text=f"Payer {amount}€", width=14,
                      state=tk.NORMAL if p.money >= amount else tk.DISABLED,
                      command=self.close).pack(side=tk.LEFT, padx=4)
            tk.Button(bottom, text="Déclarer faillite", width=14, fg="#C0392B",
                      command=self.give_up).pack(side=tk.LEFT, padx=4)
        else:
            tk.Button(bottom, text="Fermer", width=12, command=self.close).pack(side=tk.LEFT)

    def do(self, action, idx):
        action(self.player, idx)
        self.app.refresh()
        self.build()

    def give_up(self):
        if messagebox.askyesno("Faillite", f"{self.player.name}, déclarer faillite ?", parent=self.top):
            self.close()   # sans assez d'argent, Game.pay déclenche la faillite

    def close(self):
        self.top.grab_release()
        self.top.destroy()
        if not self.debt:
            self.app.after_action()


# ==============================
# Fenêtre "Échanger"
# ==============================
class TradeWindow:
    def __init__(self, app, player):
        self.app, self.game, self.a = app, app.game, player
        self.others = [p for p in self.game.players if p.active and p is not player]
        self.top = tk.Toplevel(app.root)
        self.top.title("Échange")
        self.top.transient(app.root)
        self.top.resizable(False, False)
        self.top.protocol("WM_DELETE_WINDOW", self.close)

        head = tk.Frame(self.top, padx=10, pady=8)
        head.pack(fill=tk.X)
        tk.Label(head, text=f"{player.name} propose un échange à :", font=(FONT, 11, "bold")).pack(side=tk.LEFT)
        self.partner_var = tk.StringVar(value=self.others[0].name)
        tk.OptionMenu(head, self.partner_var, *[p.name for p in self.others],
                      command=lambda _: self.build_columns()).pack(side=tk.LEFT, padx=6)

        self.cols = tk.Frame(self.top, padx=10)
        self.cols.pack(fill=tk.BOTH)
        tk.Label(self.top, text="Seuls les titres sans bâtiment sur leur groupe peuvent être échangés. "
                                "Celui qui reçoit un terrain hypothéqué paie 10 % d'intérêts.",
                 fg="#777777", font=(FONT, 8), wraplength=520, justify="left").pack(padx=10, pady=(6, 0), anchor="w")
        bottom = tk.Frame(self.top, pady=8)
        bottom.pack()
        tk.Button(bottom, text="Proposer l'échange", width=18, command=self.propose).pack(side=tk.LEFT, padx=4)
        tk.Button(bottom, text="Annuler", width=10, command=self.close).pack(side=tk.LEFT, padx=4)
        self.build_columns()
        self.top.grab_set()

    @property
    def b(self):
        return next(p for p in self.others if p.name == self.partner_var.get())

    def build_columns(self):
        for w in self.cols.winfo_children():
            w.destroy()
        self.sides = {}
        for col, p in enumerate((self.a, self.b)):
            frame = tk.LabelFrame(self.cols, text=f" {p.name} donne ({p.money}€) ", fg=p.color,
                                  font=(FONT, 10, "bold"), padx=6, pady=4)
            frame.grid(row=0, column=col, sticky="n", padx=4)
            props, cards = {}, {}
            for idx in sorted(p.properties):
                cell = self.game.board[idx]
                var = tk.IntVar()
                txt = cell["name"] + (" (hyp.)" if cell["mortgaged"] else "")
                cb = tk.Checkbutton(frame, text=txt, variable=var, anchor="w",
                                    state=tk.NORMAL if self.game.tradeable(p, idx) else tk.DISABLED)
                cb.pack(anchor="w")
                props[idx] = var
            for k, (deck, card) in enumerate(p.jail_cards):
                var = tk.IntVar()
                tk.Checkbutton(frame, text="Carte « Libéré de prison »", variable=var).pack(anchor="w")
                cards[k] = var
            if not p.properties and not p.jail_cards:
                tk.Label(frame, text="(aucun titre)", fg="#999999").pack(anchor="w")
            line = tk.Frame(frame)
            line.pack(anchor="w", pady=(4, 0))
            tk.Label(line, text="Argent : ").pack(side=tk.LEFT)
            money = tk.Entry(line, width=8)
            money.insert(0, "0")
            money.pack(side=tk.LEFT)
            tk.Label(line, text="€").pack(side=tk.LEFT)
            self.sides[p] = (props, cards, money)

    def collect(self, p):
        props, cards, money = self.sides[p]
        chosen = [i for i, v in props.items() if v.get()]
        chosen_cards = [k for k, v in cards.items() if v.get()]
        try:
            amount = int(money.get().strip() or 0)
        except ValueError:
            amount = -1
        return chosen, chosen_cards, amount

    def describe(self, props, cards, money):
        items = [self.game.board[i]["name"] for i in props]
        items += ["carte « Libéré de prison »"] * len(cards)
        if money:
            items.append(f"{money}€")
        return ", ".join(items) if items else "rien"

    def propose(self):
        a, b = self.a, self.b
        pa, ca, ma = self.collect(a)
        pb, cb, mb = self.collect(b)
        err = self.game.validate_trade(a, b, pa, pb, ma, mb, ca, cb)
        if err:
            messagebox.showerror("Échange impossible", err, parent=self.top)
            return
        recap = (f"{a.name} donne : {self.describe(pa, ca, ma)}\n"
                 f"{b.name} donne : {self.describe(pb, cb, mb)}")
        if messagebox.askyesno("Échange", f"{b.name}, acceptez-vous cet échange ?\n\n{recap}", parent=self.top):
            self.game.trade(a, b, pa, pb, ma, mb, ca, cb)
            self.close()
        else:
            self.app.log(f"{b.name} refuse l'échange proposé par {a.name}.")

    def close(self):
        self.top.grab_release()
        self.top.destroy()
        self.app.after_action()


# ==============================
# Classement (patrimoine = argent + valeur des biens)
# ==============================
class RankingWindow:
    def __init__(self, app, final):
        g = app.game
        top = tk.Toplevel(app.root)
        top.title("Fin de partie" if final else "Classement")
        top.transient(app.root)
        top.resizable(False, False)
        body = tk.Frame(top, padx=14, pady=10)
        body.pack()
        rows = g.ranking()
        if final:
            tk.Label(body, text=f"{rows[0][1].name} gagne le Monopoly !", font=(FONT, 16, "bold"),
                     fg=rows[0][1].color).grid(row=0, column=0, columnspan=6, pady=(0, 8))
        heads = ("Rang", "Joueur", "Argent", "Biens", "Patrimoine", "")
        for c, h in enumerate(heads):
            tk.Label(body, text=h, font=(FONT, 10, "bold")).grid(row=1, column=c, padx=8, sticky="w")
        for r, (rank, p, money, assets, total) in enumerate(rows, start=2):
            status = "faillite" if not p.active else ""
            values = (f"{rank}.", p.name, f"{money}€", f"{assets}€", f"{total}€", status)
            for c, v in enumerate(values):
                tk.Label(body, text=v, fg=p.color if c == 1 else ("#C0392B" if c == 5 else "black"),
                         font=(FONT, 10, "bold" if rank == 1 else "normal")).grid(row=r, column=c, padx=8, sticky="w")
        tk.Label(body, text="Biens = prix des titres (moins l'hypothèque) + prix des bâtiments.",
                 fg="#777777", font=(FONT, 8)).grid(row=len(rows) + 2, column=0, columnspan=6, pady=(8, 0), sticky="w")
        btns = tk.Frame(body)
        btns.grid(row=len(rows) + 3, column=0, columnspan=6, pady=(10, 0))
        if final:
            tk.Button(btns, text="Nouvelle partie", width=14,
                      command=lambda: (top.destroy(), app.on_new_game())).pack(side=tk.LEFT, padx=4)
        tk.Button(btns, text="Fermer", width=10, command=top.destroy).pack(side=tk.LEFT, padx=4)


# ==============================
# Lancement
# ==============================
PLAYER_COLORS = ["red", "blue", "green", "purple", "#E67E22", "#00897B", "#6D4C41", "#222222"]


def ask_players(root):
    """Demande le nombre et le nom des joueurs. Renvoie une liste de Player ou None."""
    nb = simpledialog.askinteger("Monopoly", f"Combien de joueurs ? (2-{MAX_PLAYERS})",
                                 minvalue=2, maxvalue=MAX_PLAYERS, parent=root)
    if not nb:
        return None
    players = []
    for i in range(nb):
        name = simpledialog.askstring("Nom du joueur", f"Nom du joueur {i + 1} :", parent=root)
        players.append(Player(name.strip() if name and name.strip() else f"Joueur {i + 1}", PLAYER_COLORS[i]))
    return players


def start_game():
    root = tk.Tk()
    root.withdraw()   # cache la fenêtre pendant les questions
    if messagebox.askyesno("Monopoly", "Charger une partie sauvegardée ?\n(Non = nouvelle partie)", parent=root):
        path = filedialog.askopenfilename(title="Charger une partie", filetypes=[("Partie Monopoly", "*.json")])
        if path:
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                players = Game.players_from_dict(data)
                root.deiconify()
                App(root, players, state=data)
                root.mainloop()
                return
            except (OSError, ValueError, KeyError) as e:
                messagebox.showerror("Chargement", f"Fichier invalide, nouvelle partie.\n{e}", parent=root)
    players = ask_players(root)
    if not players:
        root.destroy()
        return
    root.deiconify()
    App(root, players)
    root.mainloop()


if __name__ == "__main__":
    start_game()
