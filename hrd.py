import argparse
import sys
import copy
import heapq
import uuid

#====================================================================================

char_single = '2'
char_empty = '.'

class Piece:
    """
    This represents a piece on the Hua Rong Dao puzzle.
    """

    def __init__(self, is_2_by_2, is_single, coord_x, coord_y, orientation, uid=None):
        """
        :param is_2_by_2: True if the piece is a 2x2 piece and False otherwise.
        :type is_2_by_2: bool
        :param is_single: True if this piece is a 1x1 piece and False otherwise.
        :type is_single: bool
        :param coord_x: The x coordinate of the top left corner of the piece.
        :type coord_x: int
        :param coord_y: The y coordinate of the top left corner of the piece.
        :type coord_y: int
        :param orientation: The orientation of the piece (one of 'h' or 'v') 
            if the piece is a 1x2 piece. Otherwise, this is None
        :type orientation: str
        """

        self.is_2_by_2 = is_2_by_2
        self.is_single = is_single
        self.coord_x = coord_x
        self.coord_y = coord_y
        self.orientation = orientation
        if uid:
            self.uid = uid
        else:
            self.uid = uuid.uuid4()

    def set_coords(self, coord_x, coord_y):
        """
        Move the piece to the new coordinates. 

        :param coord: The new coordinates after moving.
        :type coord: int
        """

        self.coord_x = coord_x
        self.coord_y = coord_y

    def __repr__(self):
        return '{} {} {} {} {}'.format(self.is_2_by_2, self.is_single, \
            self.coord_x, self.coord_y, self.orientation)

class Board:
    """
    Board class for setting up the playing board.
    """

    def __init__(self, height, pieces, goal_board_dict = None):
        """
        :param pieces: The list of Pieces
        :type pieces: List[Piece]
        """

        self.width = 4
        self.height = height
        self.pieces = pieces
        self.goal_board_dict = goal_board_dict

        # self.grid is a 2-d (size * size) array automatically generated
        # using the information on the pieces when a board is being created.
        # A grid contains the symbol for representing the pieces on the board.
        self.grid = []
        self.update_grid()

    # customized eq for object comparison.
    def __eq__(self, other):
        if isinstance(other, Board):
            return self.grid == other.grid
        return False
    
    def __str__(self):
        string = ""
        for arr in self.grid:
            string += str(arr)
        return string

    def copy_board(self, new_key, old):
        pieces = {}
        for piece_key in self.pieces:
            piece = self.pieces[piece_key]
            pieces[piece_key] = Piece(piece.is_2_by_2, piece.is_single, piece.coord_x, piece.coord_y, piece.orientation, piece.uid)
        
        board = Board(self.height, pieces, self.goal_board_dict)
        board.pieces[new_key] = board.pieces.pop(old)
        pieces[new_key].set_coords(new_key[0], new_key[1])
        board.update_grid()
        return board

    def update_grid(self):
        """
        Called in __init__ to set up a 2-d grid based on the piece location information.

        """
        self.grid = [['.'] * self.width for _ in range(self.height)]
        for piece in list(self.pieces.values()):
            if piece.is_2_by_2:
                self.grid[piece.coord_y][piece.coord_x] = '1'
                self.grid[piece.coord_y][piece.coord_x + 1] = '1'
                self.grid[piece.coord_y + 1][piece.coord_x] = '1'
                self.grid[piece.coord_y + 1][piece.coord_x + 1] = '1'
            elif piece.is_single:
                self.grid[piece.coord_y][piece.coord_x] = char_single
            else:
                if piece.orientation == 'h':
                    self.grid[piece.coord_y][piece.coord_x] = '<'
                    self.grid[piece.coord_y][piece.coord_x + 1] = '>'
                elif piece.orientation == 'v':
                    self.grid[piece.coord_y][piece.coord_x] = '^'
                    self.grid[piece.coord_y + 1][piece.coord_x] = 'v'
      
    def display(self):
        """
        Print out the current board.

        """
        for i, line in enumerate(self.grid):
            for ch in line:
                print(ch, end='')
            print()
        

class State:
    """
    State class wrapping a Board with some extra current state information.
    Note that State and Board are different. Board has the locations of the pieces. 
    State has a Board and some extra information that is relevant to the search: 
    heuristic function, f value, current depth and parent.
    """

    def __init__(self, board, hfn=0, f=0, depth=0, parent=None):
        """
        :param board: The board of the state.
        :type board: Board
        :param hfn: The heuristic function.
        :type hfn: Optional[Heuristic]
        :param f: The f value of current state.
        :type f: int
        :param depth: The depth of current state in the search tree.
        :type depth: int
        :param parent: The parent of current state.
        :type parent: Optional[State]
        """
        self.board = board
        self.hfn = hfn
        self.f = f
        self.depth = depth
        self.parent = parent
    
    def __lt__(self, other):
        return self.f < other.f    

    def generate_successors(self):
        new_states = []
        
        for piece in self.board.pieces.values():
            new_keys = []
            new_key = None
            x = piece.coord_x
            y = piece.coord_y

            if piece.is_2_by_2:
                if (x - 1) >= 0:
                    if (self.board.grid[y][x - 1] == char_empty) and (self.board.grid[y + 1][x - 1] == char_empty):
                        new_keys.append((x - 1, y))
                
                if (y - 1) >= 0:
                    if (self.board.grid[y - 1][x] == char_empty) and (self.board.grid[y - 1][x + 1] == char_empty):
                        new_keys.append((x, y - 1))
                
                if (x + 2) < self.board.width:
                    if (self.board.grid[y][x + 2] == char_empty) and (self.board.grid[y + 1][x + 2] == char_empty):
                        new_keys.append((x + 1, y))
                        
                if (y + 2) < self.board.height:
                    if (self.board.grid[y + 2][x] == char_empty) and (self.board.grid[y + 2][x + 1] == char_empty):
                        new_keys.append((x, y + 1))
                        
            elif piece.is_single:
                if (x - 1) >= 0:
                    if (self.board.grid[y][x - 1] == char_empty):
                        new_keys.append((x - 1, y))
                
                if (y - 1) >= 0:
                    if (self.board.grid[y - 1][x] == char_empty):
                        new_keys.append((x, y - 1))
                        
                if (x + 1) < self.board.width:
                    if (self.board.grid[y][x + 1] == char_empty):
                        new_keys.append((x + 1, y))
                
                if (y + 1) < self.board.height:
                    if (self.board.grid[y + 1][x] == char_empty):
                        new_keys.append((x, y + 1))
            
            elif piece.orientation == 'h':
                if (x - 1) >= 0:
                    if (self.board.grid[y][x - 1] == char_empty):
                        new_keys.append((x - 1, y))
            
                if (y - 1) >= 0:
                    if (self.board.grid[y - 1][x] == char_empty) and (self.board.grid[y - 1][x + 1] == char_empty):
                        new_keys.append((x, y - 1))
            
                if (x + 2) < self.board.width:
                    if (self.board.grid[y][x + 2] == char_empty):
                        new_keys.append((x + 1, y))
            
                if (y + 1) < self.board.height:
                    if (self.board.grid[y + 1][x] == char_empty) and (self.board.grid[y + 1][x + 1] == char_empty):
                        new_keys.append((x, y + 1))
            
            else:
                if (x - 1) >= 0:
                    if (self.board.grid[y][x - 1] == char_empty) and (self.board.grid[y + 1][x - 1] == char_empty):
                        new_keys.append((x - 1, y)) 
            
                if (y - 1) >= 0:
                    if (self.board.grid[y - 1][x] == char_empty):
                        new_keys.append((x, y - 1))
            
                if (x + 1) < self.board.width:
                    if (self.board.grid[y][x + 1] == char_empty) and (self.board.grid[y + 1][x + 1] == char_empty):
                        new_keys.append((x + 1, y))
            
                if (y + 2) < self.board.height:
                    if (self.board.grid[y + 2][x] == char_empty):
                        new_keys.append((x, y + 1))
                    
            for new_key in new_keys:
                goal_piece = self.board.goal_board_dict[piece.uid]
                old_man_dist = abs(x - goal_piece.coord_x) + abs(y - goal_piece.coord_y)
                new_man_dist = abs(new_key[0] - goal_piece.coord_x) + abs(new_key[1] - goal_piece.coord_y)
                board = self.board.copy_board(new_key, (x, y))
                new_states.append(State(board, (self.hfn - old_man_dist) + new_man_dist, self.f, self.depth + 1, self))

        return new_states

def read_from_file(filename):
    """
    Load initial board from a given file.

    :param filename: The name of the given file.
    :type filename: str
    :return: A loaded board
    :rtype: Board
    """
    goal_board_dict = {}
    puzzle_file = open(filename, "r")
    singles = []
    vert = []
    hori = []
    double = None

    line_index = 0
    pieces = {}
    final_pieces = {}
    final = False
    found_2by2 = False
    finalfound_2by2 = False
    height_ = 0

    for line in puzzle_file:
        height_ += 1
        if line == '\n':
            if not final:
                height_ = 0
                final = True
                line_index = 0
            continue
        if not final: #initial board
            for x, ch in enumerate(line):
                if ch == '^': # found vertical piece
                    piece = Piece(False, False, x, line_index, 'v')
                    pieces[(x, line_index)] = piece
                    vert.append(piece)
                elif ch == '<': # found horizontal piece
                    piece = Piece(False, False, x, line_index, 'h')
                    pieces[(x, line_index)] = piece
                    hori.append(piece)
                elif ch == char_single:
                    piece = Piece(False, True, x, line_index, None)
                    pieces[(x, line_index)] = piece
                    singles.append(piece)                
                elif ch == '1':
                    if found_2by2 == False:
                        piece = Piece(True, False, x, line_index, None)
                        pieces[(x, line_index)] = piece
                        double = piece
                        found_2by2 = True

        else: #goal board
            for x, ch in enumerate(line):
                if ch == '^': # found vertical piece
                    uid = vert.pop(find_min_index(vert, x, line_index)).uid
                    piece = Piece(False, False, x, line_index, 'v', uid)
                    final_pieces[(x, line_index)] = piece
                    goal_board_dict[uid] = piece
                elif ch == '<': # found horizontal piece
                    uid = hori.pop(find_min_index(hori, x, line_index)).uid
                    piece = Piece(False, False, x, line_index, 'h', uid)
                    final_pieces[(x, line_index)] = piece
                    goal_board_dict[uid] = piece                    
                elif ch == char_single:
                    uid = singles.pop(find_min_index(singles, x, line_index)).uid
                    piece = Piece(False, True, x, line_index, None, uid)
                    final_pieces[(x, line_index)] = piece 
                    goal_board_dict[uid] = piece
                elif ch == '1':
                    if finalfound_2by2 == False:
                        piece = Piece(True, False, x, line_index, None, double.uid)
                        final_pieces[(x, line_index)] = piece
                        goal_board_dict[double.uid] = piece
                        finalfound_2by2 = True
        line_index += 1
        
    puzzle_file.close()
    board = Board(height_, pieces, goal_board_dict)
    goal_board = Board(height_, final_pieces)
    return board, goal_board

def find_min_index(arr, x, y):
    min_i = 0
    min_dist = float('inf')
    for i in range(len(arr)):
        piece = arr[i]
        new_dist = (abs(x - piece.coord_x) + abs(y - piece.coord_y))
        if new_dist < min_dist:
            min_dist = new_dist
            min_i = i
    return min_i


def grid_to_string(grid):
    string = ""
    for i, line in enumerate(grid):
        for ch in line:
            string += ch
        string += "\n"
    return string

def init_manhattan_distance(board, goal_board):
    total = 0
    
    for piece in board.pieces.values():
        for goal_piece in goal_board.pieces.values():
            if piece.uid == goal_piece.uid:
                total += abs(goal_piece.coord_x - piece.coord_x) + abs(goal_piece.coord_y - piece.coord_y)
                
    return total

def astar(initial, goal_board):
    heap_lst = []
    heapq.heappush(heap_lst, (initial.f, initial))
    
    visited = set()
    
    while heap_lst:
        curr_f, curr = heapq.heappop(heap_lst)
        
        if str(curr.board) not in visited:
            visited.add(str(curr.board))
            
            if curr.board == goal_board:
                return curr            
            
            successors = curr.generate_successors()
            for state in successors:
                if str(state.board) not in visited:
                    state.f = state.depth + state.hfn
                    heapq.heappush(heap_lst, (state.f, state))
    return None
                    

def dfs(initial, goal_board):
    stack = [initial]
    visited = set()

    while stack:
        curr = stack.pop()
        if str(curr.board) not in visited:
            visited.add(str(curr.board))

            if curr.board == goal_board:
                return curr
            
            successors = curr.generate_successors()
            for state in successors:
                if str(state.board) not in visited:
                    stack.append(state)
    return None
    

def output_solution(board, goal_board, algo, output_file):
    states = []
    original_stdout = sys.stdout

    if algo == 'dfs':
        initial = State(board)
        state = dfs(initial, goal_board)
    else:
        man_dist = init_manhattan_distance(board, goal_board)
        initial = State(board, man_dist, man_dist, 0)
        state = astar(initial, goal_board)
        
    
    with open(output_file, 'w') as sys.stdout:
        if state:
            while state:
                states.append(state)
                state = state.parent
            
            states = states[::-1]
            
            for state in states:
                    state.board.display()
                    print("")    
        else:
            print("No solution")
    
    sys.stdout = original_stdout
    
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inputfile",
        type=str,
        required=True,
        help="The input file that contains the puzzles."
    )
    parser.add_argument(
        "--outputfile",
        type=str,
        required=True,
        help="The output file that contains the solution."
    )
    parser.add_argument(
        "--algo",
        type=str,
        required=True,
        choices=['astar', 'dfs'],
        help="The searching algorithm."
    )
    args = parser.parse_args()

    # read the board from the file
    board, goal_board = read_from_file(args.inputfile)
    output_solution(board, goal_board, args.algo, args.outputfile)