# -*- coding: utf-8 -*-
"""
Jeu de l'oie - Version serpentin rectangulaire
- Plateau rectangulaire en serpentin (cases 1 à 63)
- Cases colorées et numérotées
- Cases spéciales avec emoji et couleurs dédiées
- Pions ronds avec initiales (décalage si plusieurs joueurs)
- 2 dés
- Règles classiques + variante du puits (2 joueurs)
- Mode test : taper "test" à la demande du nombre de joueurs
"""

import tkinter as tk
from tkinter import simpledialog, messagebox
import random

# ---------- Configuration ----------
BOARD_SIZE = 63
ROWS, COLS = 9, 7        # 9 lignes × 7 colonnes = 63 cases
CELL_SIZE = 70
CANVAS_WIDTH = COLS * CELL_SIZE + 40
CANVAS_HEIGHT = ROWS * CELL_SIZE + 40
PLAYER_COLORS = ["#e53935", "#1e88e5", "#43a047", "#fb8c00"]

# Cases spéciales
GOOSE_SQUARES = {5, 9, 14, 18, 23, 27, 32, 36, 41, 45, 50, 54}
BRIDGE, BRIDGE_TO = 6, 12
INN = 19
WELL = 31
LABYRINTH, LABYRINTH_TO = 42, 39
PRISON = 52
DEATH = 58

SPECIAL_STYLES = {
    BRIDGE: ("🌉", "#7ec8e3"),
    INN: ("🏠", "#eec79a"),
    WELL: ("🕳", "#87ceeb"),
    LABYRINTH: ("🌀", "#d19be6"),
    PRISON: ("🏰", "#bdbdbd"),
    DEATH: ("💀", "#f08080"),
    BOARD_SIZE: ("🏆", "#ffd700"),
}
for sq in GOOSE_SQUARES:
    SPECIAL_STYLES[sq] = ("🦢", "#c7f0c7")

# ---------- Logique ----------
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
    def __init__(self, players, gui_callback=None, test_mode=False):
        self.players = players
        self.current = 0
        self.gui_callback = gui_callback
        self.history = []
        self.winner = None
        self.test_mode = test_mode
        self.forced_dice = None

    def log(self, text):
        self.history.append(text)

    def next_player_index(self):
        return (self.current + 1) % len(self.players)

    def roll_and_move(self):
        if self.winner:
            return
        p = self.players[self.current]

        if p.skip > 0:
            p.skip -= 1
            if p.stuck_well and len(self.players) == 2 and p.skip == 0:
                p.stuck_well = False
                self.log(f"🪣 {p.name} sort du puits après 1 tour (variante 2 joueurs).")
            self.current = self.next_player_index()
            self.log(f"⏸️ {p.name} doit passer son tour.")
            if self.gui_callback:
                self.gui_callback()
            return

        if p.stuck_well:
            self.current = self.next_player_index()
            self.log(f"🪣 {p.name} est bloqué dans le puits et ne peut pas jouer.")
            if self.gui_callback:
                self.gui_callback()
            return

        if self.test_mode and self.forced_dice:
            d1, d2 = self.forced_dice
            self.log(f"🎲 (TEST) {p.name} force les dés : {d1} et {d2} → total {d1 + d2}.")
            self.forced_dice = None
        else:
            d1, d2 = random.randint(1, 6), random.randint(1, 6)
            self.log(f"🎲 {p.name} lance les dés : {d1} et {d2} → total {d1 + d2}.")
        total = d1 + d2

        if p.first_roll and total == 9 and sorted([d1, d2]) == [3, 6]:
            p.pos = 26
            p.first_roll = False
            self.log(f"🚀 {p.name} fait 6+3 au départ → va en 26.")
            self.check_win()
            if self.gui_callback:
                self.gui_callback()
            self.current = self.next_player_index()
            return
        p.first_roll = False

        newpos = p.pos + total
        if newpos > BOARD_SIZE:
            surplus = newpos - BOARD_SIZE
            newpos = BOARD_SIZE - surplus
            self.log(f"↩️ {p.name} dépasse 63 → rebondit en {newpos}.")
        self.log(f"{p.name} avance de {p.pos} à {newpos}.")
        p.pos = newpos

        replay = False

        if p.pos == DEATH:
            p.pos = 0
            p.skip = 0
            p.stuck_well = False
            self.log(f"💀 {p.name} tombe sur la Mort → retourne au départ !")
        elif p.pos == BRIDGE:
            p.pos = BRIDGE_TO
            self.log(f"🌉 {p.name} traverse le Pont → va à {BRIDGE_TO}.")
        elif p.pos == LABYRINTH:
            p.pos = LABYRINTH_TO
            self.log(f"🌀 {p.name} recule à {LABYRINTH_TO} (Labyrinthe).")
        elif p.pos == INN:
            p.skip += 1
            self.log(f"🏠 {p.name} s'arrête à l'Auberge ({INN}) : perd 1 tour.")
        elif p.pos == PRISON:
            p.skip += 3
            self.log(f"🏰 {p.name} va en Prison ({PRISON}) : perd 3 tours.")
        elif p.pos == WELL:
            if len(self.players) == 2:
                p.stuck_well = True
                p.skip = 1
                self.log(f"🕳️ {p.name} tombe dans le Puits ({WELL}) : bloqué 1 tour (variante 2 joueurs).")
            else:
                freed = False
                for other in self.players:
                    if other is not p and other.stuck_well and other.pos == WELL:
                        other.stuck_well = False
                        other.pos = 0
                        freed = True
                        self.log(f"🪣 {p.name} libère {other.name} (qui retourne au départ).")
                p.stuck_well = True
                if not freed:
                    self.log(f"🪣 {p.name} tombe dans le Puits et reste bloqué.")
        elif p.pos in GOOSE_SQUARES:
            self.log(f"🦢 {p.name} tombe sur une Oie ({p.pos}) → rejoue !")
            replay = True

        for other in self.players:
            if other is not p and other.pos == p.pos:
                if not (p.pos == WELL and other.stuck_well):
                    other.pos = 0
                    other.skip = 0
                    other.stuck_well = False
                    self.log(f"⚔️ {p.name} chasse {other.name} au départ.")

        self.check_win()

        if self.winner:
            if self.gui_callback:
                self.gui_callback()
            return

        if replay:
            self.log(f"➡️ {p.name} rejoue immédiatement !")
            if self.gui_callback:
                self.gui_callback()
            return
        else:
            self.current = self.next_player_index()
            if self.gui_callback:
                self.gui_callback()
            return

    def check_win(self):
        for pl in self.players:
            if pl.at_goal():
                self.winner = pl
                self.log(f"🏆 {pl.name} a gagné la partie !")
                return True
        return False

# ---------- Interface ----------
class GooseGUI:
    def __init__(self, root):
        self.root = root
        root.title("Jeu de l'oie - Plateau serpentin")
        self.root.resizable(False, False)

        resp = simpledialog.askstring("Joueurs", "Combien de joueurs ? (2-4) ou 'test'", parent=root)
        if resp is None:
            root.destroy()
            return

        resp_clean = resp.strip().lower()
        self.test_mode = (resp_clean == "test")

        players = []
        if self.test_mode:
            players = [Player("Test1", PLAYER_COLORS[0]), Player("Test2", PLAYER_COLORS[1])]
        else:
            try:
                n = int(resp_clean)
            except:
                messagebox.showerror("Erreur", "Entrée invalide.")
                root.destroy()
                return
            if not (2 <= n <= 4):
                messagebox.showerror("Erreur", "Nombre de joueurs doit être entre 2 et 4.")
                root.destroy()
                return
            for i in range(n):
                name = simpledialog.askstring("Nom", f"Nom du joueur {i+1} :", initialvalue=f"Joueur {i+1}", parent=root)
                if not name:
                    name = f"Joueur {i+1}"
                players.append(Player(name, PLAYER_COLORS[i]))

        self.game = GooseGame(players, gui_callback=self.update_gui, test_mode=self.test_mode)

        self.build_ui()
        self.update_gui()

    def build_ui(self):
        top = tk.Frame(self.root)
        top.pack(fill=tk.X, padx=6, pady=6)

        self.roll_btn = tk.Button(top, text="Lancer les dés 🎲", command=self.on_roll)
        self.roll_btn.pack(side=tk.LEFT, padx=6)

        if self.test_mode:
            self.force_btn = tk.Button(top, text="Forcer dés (test)", command=self.force_dice)
            self.force_btn.pack(side=tk.LEFT, padx=6)

        self.info_label = tk.Label(top, text="Bienvenue", font=("Helvetica", 12, "bold"))
        self.info_label.pack(side=tk.LEFT, padx=12)

        self.canvas = tk.Canvas(self.root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="#2e7d32")
        self.canvas.pack(side=tk.LEFT, padx=6, pady=6)

        right = tk.Frame(self.root)
        right.pack(side=tk.LEFT, fill=tk.BOTH, padx=6, pady=6)

        self.dice_label = tk.Label(right, text="—", font=("Helvetica", 14, "bold"))
        self.dice_label.pack(pady=6)

        self.player_labels = []
        for p in self.game.players:
            lbl = tk.Label(right, text=f"{p.name} : case {p.pos}", fg=p.color, anchor="w")
            lbl.pack(fill=tk.X, pady=2)
            self.player_labels.append(lbl)

        self.hist_text = tk.Text(right, width=36, height=30, state=tk.DISABLED, wrap=tk.WORD)
        self.hist_text.pack(fill=tk.BOTH, expand=True)

    def force_dice(self):
        if not self.test_mode:
            return
        d1 = simpledialog.askinteger("Dé 1", "Valeur (1-6)", minvalue=1, maxvalue=6, parent=self.root)
        if d1 is None:
            return
        d2 = simpledialog.askinteger("Dé 2", "Valeur (1-6)", minvalue=1, maxvalue=6, parent=self.root)
        if d2 is None:
            return
        self.game.forced_dice = (d1, d2)
        self.on_roll()

    def draw_board(self):
        self.canvas.delete("all")
        positions = {}

        for row in range(ROWS):
            for col in range(COLS):
                case = row * COLS + col + 1
                if case > BOARD_SIZE:
                    continue
                if row % 2 == 0:
                    x = col * CELL_SIZE + 20
                else:
                    x = (COLS - 1 - col) * CELL_SIZE + 20
                y = (ROWS - 1 - row) * CELL_SIZE + 20
                positions[case] = (x, y)

                x1, y1 = x, y
                x2, y2 = x + CELL_SIZE - 4, y + CELL_SIZE - 4

                if case in SPECIAL_STYLES:
                    emoji, color = SPECIAL_STYLES[case]
                    fill = color
                else:
                    fill = "#fffdf7" if (row + col) % 2 == 0 else "#eef8ff"
                    emoji = ""

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline="black", width=2)
                self.canvas.create_oval(x1+4, y1+4, x1+20, y1+20, fill="white")
                self.canvas.create_text(x1+12, y1+12, text=str(case), font=("Helvetica", 8, "bold"))
                if emoji:
                    self.canvas.create_text((x1+x2)//2, (y1+y2)//2, text=emoji, font=("Helvetica", 16))

        for pos, plist in self.group_players().items():
            if pos == 0:
                continue
            if pos in positions:
                x, y = positions[pos]
                for i, p in enumerate(plist):
                    px = x + 30 + (i*10)
                    py = y + 40 + (i*10)
                    self.canvas.create_oval(px-12, py-12, px+12, py+12, fill=p.color, outline="white", width=2)
                    initials = "".join([w[0] for w in p.name.split()][:2]).upper()
                    self.canvas.create_text(px, py, text=initials, fill="white", font=("Helvetica", 9, "bold"))

    def group_players(self):
        pos_map = {}
        for p in self.game.players:
            pos_map.setdefault(p.pos, []).append(p)
        return pos_map

    def update_gui(self):
        for i, p in enumerate(self.game.players):
            state = ""
            if p.skip > 0:
                state += f" - passe {p.skip} tour(s)"
            if p.stuck_well:
                state += " - au puits"
            self.player_labels[i].config(text=f"{p.name} : case {p.pos}{state}")

        last_dice = "—"
        for line in reversed(self.game.history):
            if "lance les dés" in line or "(TEST)" in line:
                last_dice = line
                break
        self.dice_label.config(text=last_dice)

        self.hist_text.config(state=tk.NORMAL)
        self.hist_text.delete(1.0, tk.END)
        for line in self.game.history[-300:]:
            self.hist_text.insert(tk.END, line + "\n")
        self.hist_text.see(tk.END)
        self.hist_text.config(state=tk.DISABLED)

        if self.game.winner:
            self.info_label.config(text=f"🏆 {self.game.winner.name} a gagné !")
            self.roll_btn.config(state=tk.DISABLED)
            if self.test_mode:
                try: self.force_btn.config(state=tk.DISABLED)
                except: pass
        else:
            cur = self.game.players[self.game.current]
            self.info_label.config(text=f"Tour de {cur.name} 🎲")

        self.draw_board()

    def on_roll(self):
        self.game.roll_and_move()

def main():
    root = tk.Tk()
    GooseGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
