# -*- coding: utf-8 -*-
"""
Monopoly (moteur pour le navigateur) - exécuté par Pyodide.

Les règles (plateau, cartes, classes Player et Game) sont celles de Monopoly v0.9
(voir python/jeu_monopoly.py), sans Tkinter.

Dans la version Tkinter, le jeu s'arrête pour poser une question (acheter ? enchérir ?
vendre pour payer ?). Dans le navigateur, on ne peut pas bloquer : l'interface appelle
api(...), et si une décision est nécessaire le moteur renvoie une "attente" (pending).
Quand le joueur répond, l'action est rejouée depuis la sauvegarde de départ avec la liste
des réponses déjà données (les dés sont fixés une fois pour toutes, donc le rejeu est exact).
"""

import random
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
# Couche web : décisions du joueur sans blocage
# ==============================
class Attente(Exception):
    """Levée quand le jeu a besoin d'une réponse du joueur."""

    def __init__(self, info):
        super().__init__(info.get("type"))
        self.info = info


class WebUI:
    """Interface passée à Game. Répond avec les réponses déjà connues, sinon lève Attente."""

    def __init__(self):
        self.logs = []
        self.answers = []
        self.k = 0
        self.last_card = {"chance": "", "community": ""}
        self.winner = None

    # -- appelées par Game --
    def log(self, text):
        self.logs.append(text)

    def next_answer(self, info):
        if self.k < len(self.answers):
            a = self.answers[self.k]
            self.k += 1
            return a
        raise Attente(info)

    def ask(self, title, question):
        return bool(self.next_answer({"type": "ask", "title": title, "question": question}))

    def ask_bid(self, player, item, best, best_bid, minimum):
        a = self.next_answer({"type": "bid", "player": player.name, "item": item["name"], "price": item["price"],
                              "best": best.name if best else None, "best_bid": best_bid,
                              "minimum": minimum, "money": player.money})
        return a if isinstance(a, int) and not isinstance(a, bool) else None

    def raise_funds(self, player, amount, creditor):
        game = WEB["game"]
        while True:
            a = self.next_answer({"type": "funds", "player": player.name, "amount": amount,
                                  "creditor": creditor.name if creditor else None})
            kind = a[0] if isinstance(a, list) else a
            if kind == "sell":
                game.sell_building(player, a[1])
            elif kind == "mortgage":
                game.mortgage(player, a[1])
            else:                      # "pay" ou "bankrupt" : on rend la main à Game.pay
                return

    def refresh(self):
        pass

    def game_over(self, winner):
        self.winner = winner.name

    def card_drawn(self, deck_name, text):
        self.last_card[deck_name] = text


WEB = {"game": None, "ui": None, "pending": None, "history": []}


def _new_game(names):
    ui = WebUI()
    players = [Player(n, PLAYER_COLORS[i]) for i, n in enumerate(names)]
    game = Game(players, ui)
    ui.log("Nouvelle partie ! " + players[0].name + " commence.")
    WEB.update(game=game, ui=ui, pending=None)


PLAYER_COLORS = ["#d7261e", "#1e6fd0", "#1fa35a", "#8e3fb5", "#e67e22", "#00897b", "#6d4c41", "#222222"]


def _snapshot():
    g, ui = WEB["game"], WEB["ui"]
    return {"game": g.to_dict(), "last_card": dict(ui.last_card), "logs": len(ui.logs), "winner": ui.winner}


def _restore(snap):
    g, ui = WEB["game"], WEB["ui"]
    players = Game.players_from_dict(snap["game"])
    ng = Game(players, ui)
    ng.load_dict(snap["game"])
    WEB["game"] = ng
    ui.last_card = dict(snap["last_card"])
    del ui.logs[snap["logs"]:]
    ui.winner = snap["winner"]


def _run(action, args, answers, snap, dice=None):
    """Exécute une action avec les réponses connues. Renvoie True si terminée, False si en attente."""
    ui = WEB["ui"]
    ui.answers, ui.k = answers, 0
    g = WEB["game"]
    try:
        if action == "roll":
            g.roll(tuple(dice))
        elif action == "build":
            g.request_build(g.player, args[0])
        elif action == "trade":
            a, b = g.players[args["a"]], g.players[args["b"]]
            err = g.trade(a, b, args["a_props"], args["b_props"], args["a_money"], args["b_money"],
                          args["a_cards"], args["b_cards"])
            WEB["error"] = err
        WEB["pending"] = None
        return True
    except Attente as w:
        # on garde l'état à ce stade pour l'affichage ; il sera rejoué depuis snap à la réponse suivante
        WEB["pending"] = {"action": action, "args": args, "answers": answers, "snap": snap,
                          "dice": dice, "info": w.info}
        return False


def _start(action, args=None, dice=None):
    WEB["error"] = None
    snap = _snapshot()
    _run(action, args, [], snap, dice)


def _static():
    g = WEB["game"]
    rows = []
    for i, c in enumerate(g.board if g else make_board()):
        r = {"i": i, "name": c["name"], "short": c["short"], "type": c["type"]}
        if c["type"] == "property":
            r.update(color=c["color"], hex=GROUP_COLORS[c["color"]], price=c["price"], rent=c["rent"],
                     house_price=c["house_price"], mortgage=c["mortgage"])
        elif c["type"] in ("station", "utility"):
            r.update(price=c["price"], mortgage=c["mortgage"])
        elif c["type"] == "tax":
            r.update(amount=c["amount"])
        rows.append(r)
    return rows


def _state():
    g, ui = WEB["game"], WEB["ui"]
    cells = []
    for i, c in enumerate(g.board):
        if "price" in c:
            cells.append({"owner": g.players.index(c["owner"]) if c["owner"] else None,
                          "houses": c.get("houses", 0), "mortgaged": c["mortgaged"],
                          "rent": g.compute_rent(i) if c["owner"] else None,
                          "unmortgage": g.unmortgage_cost(i) if c["mortgaged"] else None})
        else:
            cells.append(None)
    players = []
    for k, p in enumerate(g.players):
        players.append({"name": p.name, "color": p.color, "position": p.position, "money": p.money,
                        "properties": sorted(p.properties), "in_jail": p.in_jail, "jail_cards": len(p.jail_cards),
                        "active": p.active, "assets": g.assets_value(p), "k": k})
    pend = WEB["pending"]
    ranking = [{"rank": r, "name": p.name, "color": p.color, "money": m, "assets": a, "total": t, "active": p.active}
               for r, p, m, a, t in g.ranking()]
    return {
        "cells": cells, "players": players, "current": g.current, "dice": list(g.last_dice),
        "can_roll": g.can_roll() and not pend, "can_end": g.can_end_turn() and not pend,
        "has_actions": bool(g.has_actions(g.player)) if not g.over else False,
        "over": g.over, "winner": ui.winner, "houses_left": g.houses_left, "hotels_left": g.hotels_left,
        "last_card": ui.last_card, "log": ui.logs[-200:], "ranking": ranking,
        "pending": pend["info"] if pend else None,
        "error": WEB.get("error"),
        "manage": _manage_info(),
    }


def _manage_info():
    """Pour chaque titre du joueur courant (ou du joueur en dette) : actions possibles."""
    g = WEB["game"]
    pend = WEB["pending"]
    p = g.player
    debt = False
    if pend and pend["info"]["type"] == "funds":
        p = next(q for q in g.players if q.name == pend["info"]["player"])
        debt = True
    out = []
    for i in sorted(p.properties):
        c = g.board[i]
        out.append({"i": i,
                    "build": (not debt) and c["type"] == "property" and g.can_build(p, i),
                    "build_hotel": c["type"] == "property" and c["houses"] == 4,
                    "build_reason": g.build_block_reason(p, i) if c["type"] == "property" else None,
                    "sell": g.can_sell_building(p, i),
                    "mortgage": g.can_mortgage(p, i),
                    "unmortgage": (not debt) and g.can_unmortgage(p, i),
                    "tradeable": g.tradeable(p, i)})
    return {"player": p.name, "money": p.money, "titles": out, "debt": debt}


def api(method, args):
    g = WEB["game"]
    if method == "nouvelle":
        _new_game(args[0] if args and isinstance(args[0], list) else args)
        return {"statique": _static(), "etat": _state()}
    if method == "statique":
        return {"statique": _static()}
    if g is None:
        return {"erreur": "Aucune partie."}
    pend = WEB["pending"]

    if method == "etat":
        pass
    elif method == "repondre":
        if pend:
            pend["answers"] = pend["answers"] + [args[0]]
            _restore(pend["snap"])
            _run(pend["action"], pend["args"], pend["answers"], pend["snap"], pend["dice"])
    elif pend:
        return {"erreur": "Une décision est en attente.", "etat": _state()}
    elif method == "lancer":
        if g.can_roll():
            _start("roll", dice=[random.randint(1, 6), random.randint(1, 6)])
    elif method == "lancer_test":                       # dés imposés (tests)
        if g.can_roll():
            _start("roll", dice=args)
    elif method == "fin_tour":
        g.end_turn()
    elif method == "construire":
        _start("build", [args[0]])
    elif method == "vendre":
        g.sell_building(g.player, args[0])
    elif method == "hypothequer":
        g.mortgage(g.player, args[0])
    elif method == "lever":
        g.unmortgage(g.player, args[0])
    elif method == "valider_echange":
        args = args[0] if isinstance(args, list) else args
        a, b = g.players[args["a"]], g.players[args["b"]]
        err = g.validate_trade(a, b, args["a_props"], args["b_props"], args["a_money"], args["b_money"],
                               args["a_cards"], args["b_cards"])
        return {"erreur": err}
    elif method == "echange":
        _start("trade", args[0] if isinstance(args, list) else args)
    elif method == "terminer":
        g.finish()
    elif method == "sauvegarder":
        return {"donnees": g.to_dict()}
    elif method == "charger":
        data = args[0] if isinstance(args, list) else args
        ui = WebUI()
        players = Game.players_from_dict(data)
        ng = Game(players, ui)
        ng.load_dict(data)
        ui.log(f"Partie chargée. Au tour de {ng.player.name}.")
        WEB.update(game=ng, ui=ui, pending=None)
        return {"statique": _static(), "etat": _state()}
    return {"etat": _state()}
