from typing import Optional
from enum import IntEnum
from random import randint
from time import sleep
from copy import deepcopy, copy
from operator import itemgetter
from collections import deque
from tkinter import *

class Player(IntEnum):
    X = 0
    O = 1

Board = list[list[Optional[Player]]]

chars: dict[Optional[Player], str] = {
    Player.X: "X",
    Player.O: "O",
    None: " "
}

def filled_equal(x: list):
    # Returns if a list is filled with equal elements != None
    for item in x:
        if item is None: return False
        if item != x[0]: return False
    return True

# Info about the game
class GameContext:
    def __init__(self):
        self.moves = 0
        self.board: Board = [[None for _ in range(3)] for _ in range(3)]
        self.turn = Player.O

    def possible_moves(self) -> tuple[tuple[int, int]]:
        return tuple(((i, j) for i in range(3) for j in range(3) if self.board[i][j] is None))

    def update(self, row, col):
        self.moves += 1
        self.board[row][col] = self.turn
        self.turn = Player(1 - self.turn)

    def is_game_over(self) -> tuple[bool, Optional[Player]]:
        # Checks if a game is over
        # Also returns the winning player or None if it's a draw
        for row in self.board:
            if filled_equal(row): return (True, row[0])
        cols = list(map(list, zip(*self.board)))
        for col in cols:
            if filled_equal(col): return (True, col[0])
        diag1 = [self.board[i][i] for i in range(3)]
        diag2 = [self.board[2-i][i] for i in range(3)]
        if filled_equal(diag1): return (True, diag1[0])
        if filled_equal(diag2): return (True, diag2[0])
        if self.moves == 9: return (True, None)
        return (False, None)

# Bot
class Bot:
    def __init__(self, p: Player):
        self.player = p

    def predict_move(self, curr_ctx: GameContext) -> tuple[int, int]:
        pass

# A bot that plays random moves
class RandomBot(Bot):
    def predict_move(self, ctx: GameContext) -> tuple[int, int]:
        row = randint(0, 2)
        col = randint(0, 2)
        if ctx.board[row][col] is None: return (row, col)
        else: return self.predict_move(ctx)

class MinimaxBot(Bot):
    def __init__(self, p, max_depth):
        super().__init__(p)
        self.max_depth = max_depth

    def minimax(self, curr_ctx: GameContext, depth: int):
        # Following pseudocode in https://www.neverstopbuilding.com/blog/minimax
        over, winner = curr_ctx.is_game_over()
        if over:
            if winner == self.player: return 10
            elif winner == Player(1 - self.player): return -10
            elif winner is None: return 0
        
        moves = curr_ctx.possible_moves()
        scores = []
        for move in moves:
            new_ctx = deepcopy(curr_ctx)
            new_ctx.update(*move)
            scores.append(self.minimax(new_ctx, depth-1))
        
        if curr_ctx.turn == self.player:
            score, move = max(zip(scores, moves), key=itemgetter(0))
            # print(f"Move {chosen_move} has a score of {score}")
        else:
            score, _ = min(zip(scores, moves), key=itemgetter(0))
            # print(f"Move {chosen_move} has a score of {score}")
        if depth == self.max_depth: self.move = move
        return score
    
    def predict_move(self, curr_ctx):
        self.minimax(curr_ctx, self.max_depth)
        return self.move

# Class that contains all game and GUI contexts
class Application:
    def __init__(self, master=None):
        # Create window context
        self.tk = Tk()
        self.tk.title("Tic-tac-toe")
        
        # Manages if the main loop should finish
        self.quit = False
        def quit():
            self.quit = True
        self.tk.protocol("WM_DELETE_WINDOW", quit)
        
        # Window and board geometry
        self.window_height = 600
        self.board_size = 500 # Square
        self.cell_size = self.board_size/3
        self.tk.geometry(f"{self.board_size}x{self.window_height}")

        # Reset game button
        self.reset_button = Button(self.tk, text="Reset game", command=self.reset_game)
        self.reset_button.pack()
        self.tk.update() # Must update tk before getting the width of element
        self.reset_button.place(x=self.board_size/2 - self.reset_button.winfo_width()/2, y=self.board_size + 60)

        # Text area
        self.text_area = Label(self.tk, text="Tic-tac-toe!")
        self.text_area.pack()
        self.text_area.config(font=("Courier", 200))
        self.tk.update()
        self.text_area.place(x=self.board_size/2 - self.text_area.winfo_width()/2, y=self.board_size + 30)
        
        # Keep track of the elements drawn in canvas other than board lines
        self.drawn_ids = []
        
        # Draw board lines
        self.canvas = Canvas(master=self.tk, width=self.board_size, height=self.board_size)
        self.canvas.create_line(self.board_size/3, 0, self.board_size/3, self.board_size, width=8)
        self.canvas.create_line(self.board_size*2/3, 0, self.board_size*2/3, self.board_size, width=8)
        self.canvas.create_line(0, self.board_size/3, self.board_size, self.board_size/3, width=8)
        self.canvas.create_line(0, self.board_size*2/3, self.board_size, self.board_size*2/3, width=8)

        # Initialize game context
        self.reset_game()

        # Handler for mouse events
        def mouse_callback(event):
            col = int(event.x // self.cell_size)
            row = int(event.y // self.cell_size)
            if row not in range(3) or col not in range(3): return
            if self.accept_user_input and self.ctx.board[row][col] is None:
                # Valid mouse events will update the game context
                self.update_canvas(row, col)
                self.ctx.update(row, col)

                if self.ctx.is_game_over()[0]:
                    # Check if game has ended to freeze the game context
                    self.accept_user_input = False
                    winning_player = self.ctx.is_game_over()[1]
                    message = "Draw!" if winning_player is None else f"{chars[winning_player]} wins!"
                    self.text_area.config(text=message)
                else:
                    # Bot move
                    row, col = self.bot.predict_move(self.ctx)
                    
                    # Update game context after bot move
                    self.update_canvas(row, col)
                    self.ctx.update(row, col)
                    if self.ctx.is_game_over()[0]:
                        self.accept_user_input = False
                        winning_player = self.ctx.is_game_over()[1]
                        message = "Draw!" if winning_player is None else f"{chars[winning_player]} wins!"
                        self.text_area.config(text=message)
        
        # Set mouse event callback to our handler
        self.canvas.bind("<Button-1>", mouse_callback)

        # Must do this for some reason
        self.canvas.pack()


    def reset_game(self):
        # TODO: at each game reset, user might choose player or pick at random
        # Resets GUI and game contexts
        self.ctx = GameContext()
        for id in self.drawn_ids:
            self.canvas.delete(id)
        self.drawn_ids = []

        # Instantiate bot
        self.user_player = Player(randint(0, 1))
        self.bot = MinimaxBot(Player(1 - self.user_player), max_depth=8)
        if self.user_player == Player.X:
            row = randint(0, 2)
            col = randint(0, 2)
            self.update_canvas(row, col)
            self.ctx.update(row, col)
        self.accept_user_input = True
        self.text_area.config(text="Tic-tac-toe!")
    
    def update_canvas(self, row, col):
        # Update GUI context by drawing new elements into the canvas
        pad = 0.1*self.cell_size
        if self.ctx.turn == Player.O:
            self.drawn_ids.append(
                self.canvas.create_oval(col*self.cell_size + pad, row*self.cell_size + pad, (col+1)*self.cell_size - pad, (row+1)*self.cell_size - pad, width=8)
            )
        elif self.ctx.turn == Player.X:
            self.drawn_ids.append(
                self.canvas.create_line(col*self.cell_size + pad, row*self.cell_size + pad, (col+1)*self.cell_size - pad, (row+1)*self.cell_size - pad, width=8)
            )
            self.drawn_ids.append(
                self.canvas.create_line(col*self.cell_size + pad, (row+1)*self.cell_size - pad, (col+1)*self.cell_size - pad, row*self.cell_size + pad, width=8)
            )


def main():
    app = Application()
    while True:
        # Update window context
        app.tk.update()
        app.tk.update_idletasks()
        
        # Check if user closed window
        if app.quit:
            break
    
if __name__ == "__main__":
    main()