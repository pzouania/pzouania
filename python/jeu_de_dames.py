import tkinter as tk
from tkinter import messagebox

# Symboles des pièces
PIECES = {
    'p': '⛂',  # pion noir
    'P': '⛀',  # pion blanc
    'd': '⛃',  # dame noire
    'D': '⛁',  # dame blanche
}

# Plateau initial
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
        xm, ym = x + dx//2, y + dy//2
        if est_dans_plateau(x2, y2) and plateau[x2][y2] == '.':
            if plateau[xm][ym] != '.' and plateau[xm][ym].isupper() != piece.isupper():
                coups.append((x2, y2))
    return coups

def captures_dame(plateau, x, y):
    piece = plateau[x][y]
    coups = []
    directions = [(-1,-1), (-1,1), (1,-1), (1,1)]
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

    if piece in ('P','p'):
        if capture_seulement:
            return captures_pion(plateau, x, y)
        dx = -1 if piece=='P' else 1
        for dy in [-1,1]:
            nx, ny = x+dx, y+dy
            if est_dans_plateau(nx, ny) and plateau[nx][ny]=='.':
                coups.append((nx, ny))
        coups.extend(captures_pion(plateau,x,y))
    else:
        if capture_seulement:
            return captures_dame(plateau, x, y)
        directions = [(-1,-1), (-1,1), (1,-1), (1,1)]
        for dx, dy in directions:
            nx, ny = x+dx, y+dy
            while est_dans_plateau(nx, ny) and plateau[nx][ny]=='.':
                coups.append((nx, ny))
                nx += dx
                ny += dy
        coups.extend(captures_dame(plateau,x,y))
    return coups

def toutes_captures_obligatoires(plateau, joueur_blanc):
    captures = []
    for i in range(8):
        for j in range(8):
            piece = plateau[i][j]
            if piece=='.' or piece.isupper()!=joueur_blanc:
                continue
            c = coups_possibles_piece(plateau,i,j,capture_seulement=True)
            if c:
                captures.append(((i,j), c))
    return captures

def deplacer(plateau, start, end):
    x1, y1 = start
    x2, y2 = end
    piece = plateau[x1][y1]
    plateau[x2][y2] = piece
    plateau[x1][y1] = '.'

    # capture
    if abs(x2-x1)>=2:
        dx = (x2-x1)//abs(x2-x1)
        dy = (y2-y1)//abs(y2-y1)
        nx, ny = x1+dx, y1+dy
        while (nx, ny)!=(x2,y2):
            if plateau[nx][ny]!='.':
                plateau[nx][ny]='.'
                break
            nx+=dx
            ny+=dy

    # promotion
    if piece=='P' and x2==0:
        plateau[x2][y2]='D'
    elif piece=='p' and x2==7:
        plateau[x2][y2]='d'

def joueur_peut_jouer(plateau, joueur_blanc):
    for i in range(8):
        for j in range(8):
            piece=plateau[i][j]
            if piece=='.' or piece.isupper()!=joueur_blanc:
                continue
            if coups_possibles_piece(plateau,i,j):
                return True
    return False

class Dames(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Jeu de dames")
        self.geometry("600x650")
        self.resizable(False, False)

        self.plateau = [ligne.copy() for ligne in plateau_initial]
        self.tour_blanc = True
        self.selection = None
        self.cases = []
        self.coups_possibles = []
        self.multi_capture = None
        self.partie_terminee = False

        self.message = tk.Label(self, text="Tour des Blancs", font=("Arial", 14))
        self.message.pack(pady=10)

        frame = tk.Frame(self)
        frame.pack()

        for i in range(8):
            frame.grid_rowconfigure(i, minsize=60)
            frame.grid_columnconfigure(i, minsize=60)

        for i in range(8):
            ligne=[]
            for j in range(8):
                couleur_bg = "#EEEED2" if (i+j)%2==0 else "#769656"
                btn = tk.Button(frame, text=PIECES.get(self.plateau[i][j],' '), font=("Arial",24),
                                bg=couleur_bg,
                                command=lambda x=i,y=j:self.clic_case(x,y))
                btn.grid(row=i,column=j,sticky="nsew")
                ligne.append(btn)
            self.cases.append(ligne)
        self.bouton_quitter=tk.Button(self,text="Quitter",command=self.destroy)
        self.bouton_quitter.pack(pady=10)
        self.maj_affichage()

    def maj_affichage(self):
        if self.partie_terminee:
            return
        for i in range(8):
            for j in range(8):
                couleur_bg = "#EEEED2" if (i+j)%2==0 else "#769656"
                if (i,j) in self.coups_possibles:
                    couleur_bg="#77DD77"
                self.cases[i][j].config(bg=couleur_bg,text=PIECES.get(self.plateau[i][j],' '))
        joueur = "Blancs" if self.tour_blanc else "Noirs"
        if self.multi_capture:
            joueur += " (capture multiple)"
        self.message.config(text=f"Tour des {joueur}")

    def fin_partie(self):
        blancs = any(p.isupper() for ligne in self.plateau for p in ligne)
        noirs = any(p.islower() for ligne in self.plateau for p in ligne)
        if not blancs:
            messagebox.showinfo("Fin de partie","Les Noirs gagnent !")
            self.partie_terminee=True
            self.destroy()
            return
        elif not noirs:
            messagebox.showinfo("Fin de partie","Les Blancs gagnent !")
            self.partie_terminee=True
            self.destroy()
            return
        elif not joueur_peut_jouer(self.plateau,self.tour_blanc):
            gagnant = "Noirs" if self.tour_blanc else "Blancs"
            messagebox.showinfo("Fin de partie",f"{gagnant} gagnent (adversaire bloqué) !")
            self.partie_terminee=True
            self.destroy()
            return

    def clic_case(self,x,y):
        if self.partie_terminee:
            return
        captures_obligatoires = toutes_captures_obligatoires(self.plateau,self.tour_blanc)
        if self.selection is None:
            piece=self.plateau[x][y]
            if piece=='.' or piece.isupper()!=self.tour_blanc:
                return
            self.selection=(x,y)
            self.coups_possibles=coups_possibles_piece(self.plateau,x,y)
            if captures_obligatoires:
                for p in captures_obligatoires:
                    if p[0]==(x,y):
                        self.coups_possibles = p[1]
                        break
                else:
                    self.coups_possibles=[]
            self.maj_affichage()
        else:
            x1,y1 = self.selection
            if (x,y) in self.coups_possibles:
                capture = abs(x-x1)>=2
                deplacer(self.plateau,(x1,y1),(x,y))
                if capture:
                    new_captures = coups_possibles_piece(self.plateau,x,y,capture_seulement=True)
                    if new_captures:
                        self.selection=(x,y)
                        self.coups_possibles=new_captures
                        self.multi_capture=(x,y)
                    else:
                        self.selection=None
                        self.multi_capture=None
                        self.tour_blanc = not self.tour_blanc
                        self.coups_possibles=[]
                        self.fin_partie()
                else:
                    self.selection=None
                    self.multi_capture=None
                    self.tour_blanc = not self.tour_blanc
                    self.coups_possibles=[]
                    self.fin_partie()
            else:
                self.selection=None
                self.coups_possibles=[]
            self.maj_affichage()

if __name__=="__main__":
    app=Dames()
    app.mainloop()
