#!/usr/bin/env python3

"""
Connect4 Game with AI
Created by: Your Name, 2024
"""

import tkinter as tk
from tkinter import font, ttk
import random
import math
import copy
import os

# Configuration
AI_THINKING_LEVELS = {
    "Beginner": 400,
    "Intermediate": 2500, 
    "Hard": 5000
}
CURRENT_LEVEL = "Intermediate"  # Default level

# Directions for win checking (horizontal, vertical, diagonal up, diagonal down)
DIRECTION_X = [0, 1, 1, 1]
DIRECTION_Y = [1, 0, 1, -1]

# Audio files path references (not used by default)
ENABLE_AUDIO = False
AUDIO_FILES = {
    "piece_placed": os.path.join('audio', 'place.wav'),
    "victory": os.path.join('audio', 'victory.wav'),
    "defeat": os.path.join('audio', 'defeat.wav')
}

def play_audio(audio_file):
    """Play audio effect (placeholder)"""
    # Functionality disabled by default
    pass


class GameState:
    """Represents the current state of the Connect4 game board"""
    
    def __init__(self, grid=None, previous_move=None):
        if grid is None:
            # Create empty 6x7 grid
            self.grid = [[0 for _ in range(7)] for _ in range(6)]
            self.previous_move = [None, None]
        else:
            self.grid = grid
            self.previous_move = previous_move if previous_move else [None, None]
    
    def place_piece(self, column, player_value):
        """Place a piece in the specified column if possible
        
        Args:
            column: Column index (0-6) where to drop the piece
            player_value: Value of the player (1 for AI, -1 for human)
            
        Returns:
            Row index where piece was placed, or -1 if invalid move
        """
        # Check if the move is valid
        if column < 0 or column > 6 or self.grid[0][column] != 0:
            return -1
        
        # Find the lowest empty position in the column
        for row in range(5, -1, -1):
            if self.grid[row][column] == 0:
                self.grid[row][column] = player_value
                self.previous_move = [row, column]
                return row
        return -1
    
    def is_game_over(self):
        """Check if the game has ended (board is full)"""
        # Game is over if top row is full
        for col in range(7):
            if self.grid[0][col] == 0:
                return False
        return True
    
    def get_valid_moves(self):
        """Return list of columns where a piece can be placed"""
        valid_moves = []
        for col in range(7):
            if self.grid[0][col] == 0:
                valid_moves.append(col)
        return valid_moves
    
    def simulate_random_move(self, player_value):
        """Generate a new state by making a random valid move"""
        new_state = copy.deepcopy(self)
        valid_moves = new_state.get_valid_moves()
        
        if valid_moves:
            selected_column = random.choice(valid_moves)
            for row in range(5, -1, -1):
                if new_state.grid[row][selected_column] == 0:
                    new_state.grid[row][selected_column] = player_value
                    new_state.previous_move = [row, selected_column]
                    break
                    
        return new_state
    
    def check_winner(self):
        """Check if there's a winner in the current state
        
        Returns:
            1 if AI won, -1 if human won, 0 if no winner yet
        """
        row, col = self.previous_move
        
        # If no moves have been made yet, return 0
        if row is None:
            return 0
            
        # Check in all 4 directions from the last move
        for direction in range(4):
            ai_count = 0
            human_count = 0
            
            # Look at 7 positions in each direction (-3 to +3 from current position)
            for offset in range(-3, 4):
                # Calculate position to check
                check_row = row + offset * DIRECTION_X[direction]
                check_col = col + offset * DIRECTION_Y[direction]
                
                # Skip positions outside the board
                if not (0 <= check_row < 6 and 0 <= check_col < 7):
                    continue
                
                # Count consecutive pieces
                cell_value = self.grid[check_row][check_col]
                if cell_value == -1:  # Human
                    ai_count = 0  # Reset AI counter
                    human_count += 1
                elif cell_value == 1:  # AI
                    human_count = 0  # Reset human counter
                    ai_count += 1
                else:  # Empty
                    human_count = 0
                    ai_count = 0
                
                # Check for 4 in a row
                if human_count >= 4:
                    return -1
                if ai_count >= 4:
                    return 1
                    
        return 0  # No winner yet


class MCTSNode:
    """Monte Carlo Tree Search node representing a game state"""
    
    def __init__(self, state, parent=None):
        self.state = state
        self.parent = parent
        self.children = []
        self.moves = []  # Moves that lead to each child
        self.visits = 1
        self.score = 0.0
        
    def add_child(self, state, move):
        """Add a child node with the given state and move"""
        child = MCTSNode(state, self)
        self.children.append(child)
        self.moves.append(move)
        return child
        
    def update_stats(self, result):
        """Update node statistics after simulation"""
        self.score += result
        self.visits += 1
        
    def is_fully_expanded(self):
        """Check if all possible moves from this state have been explored"""
        return len(self.children) == len(self.state.get_valid_moves())


class AIPlayer:
    """Monte Carlo Tree Search implementation for Connect4 AI"""
    
    @staticmethod
    def find_best_move(game_state, max_iterations, exploration_weight=2.0):
        """Find the best move using Monte Carlo Tree Search
        
        Args:
            game_state: Current game state
            max_iterations: Number of MCTS iterations
            exploration_weight: Controls exploration vs exploitation balance
            
        Returns:
            Best move found
        """
        # Create root node with current game state
        root = MCTSNode(game_state)
        
        # Run MCTS for the specified number of iterations
        for _ in range(max_iterations):
            # Selection and expansion
            selected_node, player_turn = AIPlayer._select_node(root, 1, exploration_weight)
            
            # Simulation
            result = AIPlayer._simulate_game(selected_node.state, player_turn)
            
            # Backpropagation
            AIPlayer._backpropagate(selected_node, result, player_turn)
        
        # Select best move from root
        best_child = AIPlayer._select_best_child(root, 0)
        
        # Debug info - show expected values of each move
        child_values = [(c.score / c.visits) for c in root.children]
        print(f"Move values: {child_values}")
        
        return best_child
    
    @staticmethod
    def _select_node(node, player_turn, exploration_weight):
        """Select a node to expand using UCB1 formula"""
        current = node
        current_player = player_turn
        
        # Continue selection until we find a non-terminal node that's not fully expanded
        # or we reach a terminal state
        while (not current.state.is_game_over() and 
               current.state.check_winner() == 0):
            
            if not current.is_fully_expanded():
                return AIPlayer._expand_node(current, current_player), -current_player
            else:
                current = AIPlayer._select_best_child(current, exploration_weight)
                current_player *= -1  # Switch player
                
        return current, current_player
    
    @staticmethod
    def _expand_node(node, player_turn):
        """Add a new child node by trying an unexplored move"""
        # Get unexplored moves
        tried_moves = node.moves
        possible_moves = node.state.get_valid_moves()
        
        # Find a move that hasn't been tried yet
        for move in possible_moves:
            if move not in tried_moves:
                # Create new state by applying this move
                new_state = copy.deepcopy(node.state)
                row = -1
                
                # Find row where piece will land
                for r in range(5, -1, -1):
                    if new_state.grid[r][move] == 0:
                        row = r
                        break
                
                # Apply move
                if row != -1:
                    new_state.grid[row][move] = player_turn
                    new_state.previous_move = [row, move]
                    
                # Add child node
                return node.add_child(new_state, move)
    
    @staticmethod
    def _select_best_child(node, exploration_weight):
        """Select best child using UCB1 formula"""
        best_score = float('-inf')
        best_children = []
        
        for child in node.children:
            # UCB1 formula: exploitation + exploration
            exploitation = child.score / child.visits
            exploration = exploration_weight * math.sqrt(
                math.log(2.0 * node.visits) / child.visits
            )
            
            # Total score
            ucb_score = exploitation + exploration
            
            # Track best score and children with that score
            if ucb_score > best_score:
                best_children = [child]
                best_score = ucb_score
            elif ucb_score == best_score:
                best_children.append(child)
        
        # Return random choice among best children
        return random.choice(best_children)
    
    @staticmethod
    def _simulate_game(state, player_turn):
        """Simulate a random game from the current state"""
        # Create a copy of the state
        sim_state = copy.deepcopy(state)
        current_player = player_turn
        
        # Play until game over or winner found
        while not sim_state.is_game_over() and sim_state.check_winner() == 0:
            sim_state = sim_state.simulate_random_move(current_player)
            current_player *= -1  # Switch player
            
        # Return result
        return sim_state.check_winner()
    
    @staticmethod
    def _backpropagate(node, result, player_turn):
        """Update statistics for all nodes in the path"""
        current = node
        current_player = player_turn
        
        while current is not None:
            current.visits += 1
            # Negate result based on player perspective
            current.score -= current_player * result
            current = current.parent
            current_player *= -1  # Switch player


# GUI Components

class GameHeader(tk.Frame):
    """Header panel with game title and status"""
    
    def __init__(self, master=None):
        super().__init__(master)
        self.configure(
            bg="#f5f5f5", 
            padx=15, 
            pady=15, 
            bd=1, 
            relief=tk.GROOVE
        )
        
        # Game title
        title_font = font.Font(family="Arial", size=40, weight="bold")
        self.title_label = tk.Label(
            self, 
            text="Connect4 AI", 
            font=title_font,
            bg="#f5f5f5", 
            fg="#2c3e50"
        )
        self.title_label.pack(pady=(0, 10))
        
        # Decorative separator
        separator = tk.Frame(self, height=2, bg="#3498db")
        separator.pack(fill=tk.X, pady=8)
        
        # Status message
        status_font = font.Font(family="Arial", size=14, weight="bold")
        self.status_label = tk.Label(
            self, 
            text="Your turn", 
            font=status_font,
            bg="#f5f5f5", 
            fg="#e74c3c"
        )
        self.status_label.pack(pady=5)


class GameControls(tk.Frame):
    """Control panel with game options and buttons"""
    
    def __init__(self, master=None, restart_callback=None, exit_callback=None):
        super().__init__(master)
        self.configure(bg="white")
        self.restart_callback = restart_callback
        self.exit_callback = exit_callback
        
        # Simple frame with a border
        content_frame = tk.Frame(
            self, 
            bg="white", 
            bd=1, 
            relief=tk.GROOVE, 
            padx=10,
            pady=10
        )
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a simple two-row layout
        # First row: difficulty selector
        level_frame = tk.Frame(content_frame, bg="white", height=30)
        level_frame.pack(fill=tk.X, pady=5)
        level_frame.pack_propagate(False)  # Prevent shrinking
        
        difficulty_label = tk.Label(
            level_frame, 
            text="AI Level:", 
            bg="white",
            font=font.Font(family="Arial", size=10, weight="bold")
        )
        difficulty_label.pack(side=tk.LEFT, padx=5)
        
        self.difficulty_var = tk.StringVar(value=CURRENT_LEVEL)
        
        # Make the dropdown more prominent
        difficulty_selector = ttk.Combobox(
            level_frame,
            values=list(AI_THINKING_LEVELS.keys()),
            textvariable=self.difficulty_var,
            state="readonly",
            width=12,
            font=font.Font(family="Arial", size=10)
        )
        difficulty_selector.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        difficulty_selector.bind("<<ComboboxSelected>>", self.change_difficulty)
        
        # Second row: buttons side by side
        button_frame = tk.Frame(content_frame, bg="white", height=30)
        button_frame.pack(fill=tk.X, pady=5)
        button_frame.pack_propagate(False)  # Prevent shrinking
        
        # Use direct restart function instead of callback to avoid issues
        restart_button = ttk.Button(
            button_frame, 
            text="New Game", 
            command=self.restart_game_direct,
            style="Bold.TButton"
        )
        restart_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        exit_button = ttk.Button(
            button_frame, 
            text="Exit Game", 
            command=self.exit_game
        )
        exit_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
    
    def restart_game_direct(self):
        """Restart game directly without using callback to avoid layout issues"""
        global header, game_board, board_frame
        header.title_label.config(text="Connect4 AI")
        header.status_label.config(text="Your turn", fg="#e74c3c")
        
        # Replace the game board directly
        game_board.destroy()
        game_board = GameBoard(board_frame)
        game_board.pack(fill=tk.BOTH, expand=True)
    
    def restart_game(self):
        """Call the restart callback"""
        if self.restart_callback:
            self.restart_callback()
    
    def exit_game(self):
        """Call the exit callback"""
        if self.exit_callback:
            self.exit_callback()

    def change_difficulty(self, event=None):
        """Update difficulty level"""
        global CURRENT_LEVEL, header
        CURRENT_LEVEL = self.difficulty_var.get()
        header.status_label.config(text=f"Level set to {CURRENT_LEVEL}")
        # Reset status message after delay
        header.after(1500, lambda: header.status_label.config(text="Your turn"))


class GameDisc:
    """Represents a single disc in the game board"""
    
    def __init__(self, x, y, canvas, color="white"):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.color = color
        
        # Create shadow for 3D effect
        self.shadow = canvas.create_oval(
            x + 13, y + 13, 
            x + 64, y + 64,
            fill="#999999", 
            outline=""
        )
        
        # Create the disc
        self.disc = canvas.create_oval(
            x + 10, y + 10, 
            x + 61, y + 61,
            fill=color, 
            outline="#333"
        )
    
    def change_color(self, color):
        """Update the disc color"""
        self.canvas.itemconfigure(self.disc, fill=color)
        self.color = color


class GameBoard(tk.Canvas):
    """Visual representation of the Connect4 board"""
    
    def __init__(self, master=None):
        super().__init__(master)
        self.configure(
            width=500, 
            height=400, 
            bg="#2980b9", 
            bd=2, 
            relief=tk.RIDGE
        )
        
        # Add decorative border
        self.border = self.create_rectangle(
            5, 5, 495, 395, 
            outline="#1a5276", 
            width=3, 
            fill=""
        )
        
        # Game state initialization
        self.discs = []
        self.game_ended = False
        self.game_state = GameState()
        self.previous_state = None
        
        # Create visual grid of discs
        self.create_disc_grid()
        
        # Bind click event
        self.bind("<Button-1>", self.handle_click)
        
        # Bind resize event
        self.bind("<Configure>", self.on_canvas_resize)
    
    def create_disc_grid(self):
        """Create the grid of discs with current canvas dimensions"""
        # Clear existing discs if any
        if self.discs:
            for row in self.discs:
                for disc in row:
                    self.delete(disc.shadow)
                    self.delete(disc.disc)
        
        self.discs = []
        width = self.winfo_width() or 500
        height = self.winfo_height() or 400
        
        cell_width = width // 7
        cell_height = height // 6
        
        # Create visual grid of discs
        for row in range(6):
            disc_row = []
            for col in range(7):
                x_pos = col * cell_width
                y_pos = row * cell_height
                disc_row.append(GameDisc(x_pos, y_pos, self))
            self.discs.append(disc_row)
        
        # Update border
        self.coords(
            self.border,
            5, 5, width-5, height-5
        )
    
    def on_canvas_resize(self, event):
        """Handle canvas resize events"""
        # Update border
        width = event.width
        height = event.height
        self.coords(
            self.border,
            5, 5, width-5, height-5
        )
        
        # For major size changes, recreate the disc grid
        if abs(width - getattr(self, 'last_width', 0)) > 50 or abs(height - getattr(self, 'last_height', 0)) > 50:
            self.create_disc_grid()
            self.refresh_board() # Refresh colors
            self.last_width = width
            self.last_height = height
    
    def handle_click(self, event):
        """Handle player click on the board"""
        # Save current state for undo
        self.previous_state = copy.deepcopy(self.game_state)
        
        # Process human move
        if not self.game_ended:
            # Convert click position to column based on current width
            width = self.winfo_width()
            col = min(6, max(0, int(event.x / (width / 7))))
            
            # Try to place piece
            row = -1
            for r in range(5, -1, -1):
                if self.game_state.grid[r][col] == 0:
                    row = r
                    break
            
            # Invalid move
            if row == -1:
                return
            
            # Update game state and visual board
            self.refresh_board(row, col, -1)
            self.game_state.previous_move = [row, col]
            
            # Play sound
            if ENABLE_AUDIO:
                play_audio(AUDIO_FILES["piece_placed"])
            
            # Update status
            header.status_label.config(text="AI Turn")
            
            # Check for win or draw
            result = self.game_state.check_winner()
            if result == -1:  # Human won
                header.status_label.config(text="You won!")
                self.game_ended = True
                self.highlight_winning_sequence()
                if ENABLE_AUDIO:
                    play_audio(AUDIO_FILES["victory"])
            elif result == 1:  # AI won (shouldn't happen here)
                header.status_label.config(text="You lost!")
                self.game_ended = True
                self.highlight_winning_sequence()
                if ENABLE_AUDIO:
                    play_audio(AUDIO_FILES["defeat"])
            elif self.game_state.is_game_over():  # Draw
                header.status_label.config(text="Draw")
                self.game_ended = True
        
        self.update()
        
        # AI turn
        if not self.game_ended:
            # Calculate and make AI move
            self.calculate_ai_move()
            
            # Play sound
            if ENABLE_AUDIO:
                play_audio(AUDIO_FILES["piece_placed"])
            
            # Update status
            header.status_label.config(text="Your turn")
            
            # Check for win or draw
            result = self.game_state.check_winner()
            if result == 1:  # AI won
                header.status_label.config(text="You lost!")
                self.game_ended = True
                self.highlight_winning_sequence()
                if ENABLE_AUDIO:
                    play_audio(AUDIO_FILES["defeat"])
            elif result == -1:  # Human won (shouldn't happen here)
                header.status_label.config(text="You won!")
                self.game_ended = True
                self.highlight_winning_sequence()
                if ENABLE_AUDIO:
                    play_audio(AUDIO_FILES["victory"])
            elif self.game_state.is_game_over():  # Draw
                header.status_label.config(text="Draw")
                self.game_ended = True
        
        self.update()
    
    def calculate_ai_move(self):
        """Have the AI calculate its next move"""
        global CURRENT_LEVEL
        # Get number of iterations based on difficulty
        iterations = AI_THINKING_LEVELS[CURRENT_LEVEL]
        
        # Create root node with current game state
        root_node = MCTSNode(self.game_state)
        
        # Find best move
        best_move = AIPlayer.find_best_move(self.game_state, iterations)
        
        # Update game state
        self.game_state = copy.deepcopy(best_move.state)
        
        # Update visual board
        self.refresh_board()
    
    def refresh_board(self, row=None, col=None, value=None, new_state=None):
        """Update the visual board to match the game state
        
        Can update the whole board or just a specific disc
        """
        if row is None:
            # Full board update
            if new_state:
                self.game_state = copy.deepcopy(new_state)
            
            # Update all discs
            for r in range(6):
                for c in range(7):
                    self.refresh_board(r, c)
        elif value is None:
            # Update single disc color based on game state
            if self.game_state.grid[row][col] == -1:  # Human
                self.discs[row][col].change_color("#f1c40f")  # Yellow
            elif self.game_state.grid[row][col] == 1:  # AI
                self.discs[row][col].change_color("#e74c3c")  # Red
            else:  # Empty
                self.discs[row][col].change_color("#ecf0f1")  # White
        else:
            # Update both game state and visual display for a single disc
            self.game_state.grid[row][col] = value
            self.refresh_board(row, col)
    
    def highlight_winning_sequence(self):
        """Highlight the four discs that form a winning sequence"""
        row, col = self.game_state.previous_move
        if row is None:
            return
        
        player = self.game_state.grid[row][col]
        
        # Check in each direction
        for direction in range(4):
            count = 0
            winning_positions = []
            
            # Check 7 positions in each direction
            for offset in range(-3, 4):
                check_row = row + offset * DIRECTION_X[direction]
                check_col = col + offset * DIRECTION_Y[direction]
                
                # Skip positions outside the board
                if not (0 <= check_row < 6 and 0 <= check_col < 7):
                    continue
                
                # Check if cell matches the player
                if self.game_state.grid[check_row][check_col] == player:
                    count += 1
                    winning_positions.append((check_row, check_col))
                else:
                    count = 0
                    winning_positions = []
                
                # If 4 consecutive discs found
                if count >= 4:
                    # Highlight last 4 positions
                    for pos in winning_positions[-4:]:
                        r, c = pos
                        highlight_color = "#c9e156" if player == -1 else "#ff6b6b"
                        self.discs[r][c].change_color(highlight_color)
                    return
    
    def undo_move(self):
        """Undo the last move pair (human + AI)"""
        if self.previous_state:
            self.game_ended = False
            header.status_label.config(text="Your turn")
            self.refresh_board(new_state=self.previous_state)
            self.update()


# Main App Functions

def restart_game():
    """Reset the game to initial state"""
    global header, game_board, board_frame
    header.title_label.config(text="Connect4 AI")
    header.status_label.config(text="Your turn", fg="#e74c3c")
    
    # Replace the game board
    game_board.destroy()
    game_board = GameBoard(board_frame)
    game_board.pack(fill=tk.BOTH, expand=True)

def exit_game():
    """Close the application"""
    root.destroy()

# Application Entry Point
if __name__ == "__main__":
    # Create main window
    root = tk.Tk()
    root.geometry("550x600")
    root.title("Connect4 AI")
    root.configure(bg="#e0e0e0")
    # Set minimum size to ensure controls are visible
    root.minsize(450, 550)  # Increased minimum size
    
    # Create a simpler, more reliable layout with vertical weights
    main_frame = tk.Frame(root, bg="#e0e0e0")
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Create 3 row layout with fixed heights for header and controls
    main_frame.rowconfigure(0, weight=0, minsize=100)  # Fixed header height
    main_frame.rowconfigure(1, weight=1)  # Game board can expand
    main_frame.rowconfigure(2, weight=0, minsize=120)  # Fixed controls height
    main_frame.columnconfigure(0, weight=1)  # Single column can expand
    
    # Header at the top (fixed height)
    header = GameHeader(main_frame)
    header.grid(row=0, column=0, sticky="ew", pady=5)
    
    # Game board in the middle (expandable)
    board_frame = tk.Frame(main_frame, bg="#e0e0e0")
    board_frame.grid(row=1, column=0, sticky="nsew", pady=5)
    
    game_board = GameBoard(board_frame)
    game_board.pack(fill=tk.BOTH, expand=True)
    
    # Controls at the bottom (fixed height to ensure visibility)
    controls_frame = tk.Frame(main_frame, bg="#e0e0e0")
    controls_frame.grid(row=2, column=0, sticky="ew", pady=5)
    
    controls = GameControls(controls_frame, restart_game, exit_game)
    controls.pack(fill=tk.X)
    
    # Status bar at the very bottom
    status_bar = tk.Frame(main_frame, bg="#d0d0d0", height=24, bd=1, relief=tk.SUNKEN)
    status_bar.grid(row=3, column=0, sticky="ew")
    
    status_label = tk.Label(
        status_bar, 
        text="© 2024", 
        bg="#d0d0d0", 
        fg="#666666", 
        font=font.Font(family="Arial", size=8)
    )
    status_label.pack(side=tk.RIGHT, padx=8, pady=4)
    
    # Add a resize handler to update the game board when window size changes
    def on_resize(event):
        # Only handle main window resize events
        if event.widget == root:
            # Update after a small delay to avoid excessive updates
            root.after(100, update_board_size)
    
    def update_board_size():
        width = board_frame.winfo_width()
        height = board_frame.winfo_height() 
        
        # Only update if dimensions are valid
        if width > 100 and height > 100:
            # Configure game board size
            game_board.configure(width=width, height=height)
            
            # Recalculate disc positions and sizes
            cell_width = width // 7
            cell_height = height // 6
            
            # Recreate all discs with new positions
            for row in range(6):
                for col in range(7):
                    disc = game_board.discs[row][col]
                    
                    # Calculate new position and size
                    x_pos = col * cell_width
                    y_pos = row * cell_height
                    radius = min(cell_width, cell_height) // 2 - 5
                    
                    # Update shadow position and size
                    game_board.coords(
                        disc.shadow,
                        x_pos + 3 + (cell_width - 2*radius) // 2,
                        y_pos + 3 + (cell_height - 2*radius) // 2,
                        x_pos + 3 + (cell_width + 2*radius) // 2,
                        y_pos + 3 + (cell_height + 2*radius) // 2
                    )
                    
                    # Update disc position and size
                    game_board.coords(
                        disc.disc,
                        x_pos + (cell_width - 2*radius) // 2,
                        y_pos + (cell_height - 2*radius) // 2,
                        x_pos + (cell_width + 2*radius) // 2,
                        y_pos + (cell_height + 2*radius) // 2
                    )
    
    # Bind resize event
    root.bind("<Configure>", on_resize)
    
    # Start application
    root.mainloop() 