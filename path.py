# @Author: Manuel Zubieta
# @Version: 0.1.0
# 
# A demonstration of the A* Pathfinding Algorithm using Python 2.6 and PyGame

import sys, pygame, math, heapq
from pygame.locals import *

# Adjust the size of the board and the cells
cell_size = 50
num_cells = 20


cells = {}      # Dictionary of Cells where a tuple (immutable set) of (x,y) coordinates is used as keys

for x in range(num_cells):
    for y in range(num_cells):
        cells[(x,y)]= { 'state':None,   # None, Wall, Goal, Start Are the possible states. None is walkable 
                        'f_score':None, # f() = g() + h() This is used to determine next cell to process
                        'h_score':None, # The heuristic score, We use straight-line distance: sqrt((x1-x0)^2 + (y1-y0)^2)
                        'g_score':None, # The cost to arrive to this cell, from the start cell
                        'parent':None}  # In order to walk the found path, keep track of how we arrived to each cell

# Colors
black = (0,0,0)             # Wall Cells
gray = (112, 128, 144)      # Default Cells
bright_green = (0, 204, 102) # Start Cell
red = (255, 44, 0)          # Goal Cell
orange = (255, 175, 0)      # Open Cells
blue = (0, 124, 204)        # Closed Cells
white = (250,250,250)       # Not used, yet

# PyGame stuff to set up the window
pygame.init()
size = width, height = (cell_size*num_cells)+2, (cell_size*num_cells)+2
screen = pygame.display.set_mode(size)
pygame.display.set_caption = ('Pathfinder')


start_placed = goal_placed = needs_refresh = step_started = False
last_wall = None
start = None
goal = None

# A* variables
# Python's built-in heapq module uses a plain ol' list as it's underlying data structure. Actually,
# heapq is just a set of functions that can be called on a list. Such as:
# 
#     heapify(list)
#     heappop(list)
#     heappush(list,item)
# 
# So open_list is the list that we'll use to store the f_scores of all the opened cells. The cell with the lowest
# f_score is of our highest priority, so when we call heapify(open_list) this will order the list so that the lowest
# score is the first element.

open_list = []      # our priority queue of opened cells' f_scores

# There's an issue with this, as you may have noticed. We're only keeping track of the f_scores of all the opened cells
# in open_list. When we retreive the lowest f_score, how do we know which cell is this? pq_dict is a ditionary for our
# priority queue. 

# When we pop the highest priority f_score out of open_list, we use this as a key to retreive the actual cell
# identifier from pq_dict

pq_dict = {}   
             
closed_list = {}    # A dictionary of closed cells

# This allows for the dynamic changing of the chosen heuristic
heuristic = 'crow' # Could be 'manhattan' or 'crow' anything else is assumed to be 'zero'

# Function to reduce repeated PyGame code to refresh the board

def showBoard(screen, board):
    screen.blit(board, (0,0))
    pygame.display.flip()


# Function to Draw the initial board.

def initBoard(board):
    background = pygame.Surface(board.get_size())
    background = background.convert()
    background.fill (gray)
    
    # Draw Grid lines
    for i in range(0,(cell_size*num_cells)+1)[::cell_size]:
        pygame.draw.line(background, black, (i, 0), (i, cell_size*num_cells), 2)
        pygame.draw.line(background, black, (0, i), (cell_size*num_cells, i), 2)
    return background


# Function in attempt to beautify my code, nothing more.

def calc_f(node):
    cells[node]['f_score'] = cells[node]['h_score'] + cells[node]['g_score']


# Calculate the heuristic score, straight line distance between two points:
# You'll notice I multiply by 10. This is because of how I keep track of the g_score, which you'll see later
# but I'll explain now:
#
# To simplify the calculations of the g_score, if we move in an orthoganal direction, we consider the cost
# of this move to be 10, and not 1. We do this because of the cost of a diagonal move. Typically this would
# be the squareroot of 2 = 1.4142..
#
# To decrease the number of essentially useless computations, we round this to 1.4...and why deal with decimals?
# So we multiply that by 10 to get a cost of 14 to move diagonal and 10 to move orthoganal.

def calc_h(node):
    global heuristic
    x1, y1 = goal
    x0, y0 = node
    if heuristic == 'manhattan':
        cells[node]['h_score'] = (abs(x1-x0)+abs(y1-y0))*10#
    elif heuristic == 'crow':
        cells[node]['h_score'] = math.sqrt( (x1-x0)**2 + (y1-y0)**2 )*10
    else:
        cells[node]['h_score'] = 0


# Technically, I need to change the way I've represented the board. I only realized that after coding this up
# I did this given a square 2D grid of equal sizes. I really only did this by habbit. It SHOULD be more graph-like
# Where each cell has its adjacency matrix...my baaaaad. 
#
# Anyways, this is a helper function to check if a given coord is on the board

def onBoard(node):
    x, y = node
    return x >= 0 and x < num_cells and y >= 0 and y < num_cells


# Return a list of adjacent orthoganal walkable cells 

def orthoganals(current):
    x, y = current
    
    N = x-1, y
    E = x, y+1
    S = x+1, y
    W = x, y-1
    
    directions = [N, E, S, W]
    return [x for x in directions if onBoard(x) and cells[x]['state'] != 'Wall' and not x in closed_list]


# Check if diag is blocked by a wall, making it unwalkable from current

def blocked_diagnol(current,diag):
    x, y = current
    
    N = x-1, y
    E = x, y+1
    S = x+1, y
    W = x, y-1
    NE = x-1, y+1
    SE = x+1, y+1
    SW = x+1, y-1
    NW = x-1, y-1
    
    if diag == NE:
        return cells[N]['state'] == 'Wall' or cells[E]['state'] == 'Wall'
    elif diag == SE:
        return cells[S]['state'] == 'Wall' or cells[E]['state'] == 'Wall'
    elif diag == SW:
        return cells[S]['state'] == 'Wall' or cells[W]['state'] == 'Wall'
    elif diag == NW:
        return cells[N]['state'] == 'Wall' or cells[W]['state'] == 'Wall'
    else:
        return False # Technically, you've done goofed if you arrive here.


# Return a list of adjacent diagonal walkable cells

def diagonals(current):
    x, y = current
    
    NE = x-1, y+1
    SE = x+1, y+1
    SW = x+1, y-1
    NW = x-1, y-1
    
    directions = [NE, SE, SW, NW]
    return [x for x in directions if onBoard(x) and cells[x]['state'] != 'Wall' and not x in closed_list and not blocked_diagnol(current,x)]


# Update a child node with information from parent, such as g_score and the parent's coords

def update_child(parent, child, cost_to_travel):
    cells[child]['g_score'] = cells[parent]['g_score'] + cost_to_travel
    cells[child]['parent'] = parent


# Display the shortest path found

def unwind_path(coord, slow):
    if cells[coord]['parent'] != None:
        left, top = coord
        left = (left*cell_size)+2
        top = (top*cell_size)+2
        r = pygame.Rect(left, top, cell_size-2, cell_size-2)
        pygame.draw.rect(board, white, r, 0)
        if slow:
            showBoard(screen, board)
        unwind_path(cells[coord]['parent'], slow)


# Recursive function to process the current node, which is the node with the smallest f_score from the list of open nodes

def processNode(coord, slow, step):
    global goal, open_list, closed_list, pq_dict, board, screen, needs_refresh
    if coord == goal:
        print "Cost %d\n" % cells[goal]['g_score']
        unwind_path(cells[goal]['parent'], slow)
        needs_refresh = True
        return
        
    # l will be a list of walkable adjacents that we've found a new shortest path to
    l = [] 
    
    # Check all of the diagnols for walkable cells, that we've found a new shortest path to
    for x in diagonals(coord):
        # If x hasn't been visited before
        if cells[x]['g_score'] == None:
            update_child(coord, x, cost_to_travel=14)
            l.append(x)
        # Else if we've found a faster route to x
        elif cells[x]['g_score'] > cells[coord]['g_score'] + 14:
            update_child(coord, x, cost_to_travel=14)
            l.append(x)
    
    for x in orthoganals(coord):
        # If x hasn't been visited before
        if cells[x]['g_score'] == None:
            update_child(coord, x, cost_to_travel=10)
            l.append(x)
        # Else if we've found a faster route to x
        elif cells[x]['g_score'] > cells[coord]['g_score'] + 10:
            update_child(coord, x, cost_to_travel=10)
            l.append(x)
    
    for x in l:
        if x != goal:
            left, top = x
            left = (left*cell_size)+2
            top = (top*cell_size)+2
            r = pygame.Rect(left, top, cell_size-2, cell_size-2)
            pygame.draw.rect(board, orange, r, 0)
            if slow:
                showBoard(screen, board)
        # If we found a shorter path to x
        # Then we remove the old f_score from the heap and dictionary
        if cells[x]['f_score'] in pq_dict:
            if len(pq_dict[cells[x]['f_score']]) > 1:
                pq_dict[cells[x]['f_score']].remove(x)
            else:
                pq_dict.pop(cells[x]['f_score'])
            open_list.remove(cells[x]['f_score'])
        # Update x with the new f and h score (technically don't need to do h if already calculated)
        calc_h(x)
        calc_f(x)
        # Add f to heap and dictionary
        open_list.append(cells[x]['f_score'])
        if cells[x]['f_score'] in pq_dict:
            pq_dict[cells[x]['f_score']].append(x)
        else:
            pq_dict[cells[x]['f_score']] = [x]
    
    heapq.heapify(open_list)
    
    if not step:
        if len(open_list) == 0:
            print 'NO POSSIBLE PATH!'
            return
        f = heapq.heappop(open_list)
        if len(pq_dict[f]) > 1:
            node = pq_dict[f].pop()
        else:
            node = pq_dict.pop(f)[0]
        
        heapq.heapify(open_list)
        closed_list[node]=True
    
        if node != goal:
            left, top = node
            left = (left*cell_size)+2
            top = (top*cell_size)+2
            r = pygame.Rect(left, top, cell_size-2, cell_size-2)
            pygame.draw.rect(board, blue, r, 0)
            if slow:
                showBoard(screen, board)
    
        processNode(node, slow, step)


# Start the search for the shortest path from start to goal

def findPath(slow, step):
    if start != None and goal != None:
        cells[start]['g_score'] = 0
        calc_h(start)
        calc_f(start)
        
        if step:
            open_list.append(cells[start]['f_score'])
            pq_dict[cells[start]['f_score']] = [start]
            if len(open_list) == 0:
                print 'NO POSSIBLE PATH!'
                return
            f = heapq.heappop(open_list)
            if len(pq_dict[f]) > 1:
                node = pq_dict[f].pop()
            else:
                node = pq_dict.pop(f)[0]
                
            heapq.heapify(open_list)
            closed_list[node]=True
            
            if node != goal and node != start:
                left, top = node
                left = (left*cell_size)+2
                top = (top*cell_size)+2
                r = pygame.Rect(left, top, cell_size-2, cell_size-2)
                pygame.draw.rect(board, blue, r, 0)
                if slow:
                    showBoard(screen, board)
                    
            processNode(node, slow, step)
        else:
            closed_list[start]=True
            processNode(start, slow, step)


# Clean up code a little bit: This function draws a cell at (x,y)        

def draw_cell(x, y, size, color):
    r = pygame.Rect(x, y, size, size)
    pygame.draw.rect(board, color, r, 0)


# Draw that board, Son!
board = initBoard(screen)

# Event handling beyond this point:
while 1:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit()
        key=pygame.key.get_pressed()
        
        # Define our key events
        left_click, middle_click, right_click = pygame.mouse.get_pressed()
        ctrl = key[pygame.K_LCTRL] or key[pygame.K_RCTRL]
        escape = key[pygame.K_ESCAPE]
        shift = key[pygame.K_LSHIFT]
        enter = key[pygame.K_RETURN]
        delete = key[pygame.K_BACKSPACE]
        right_arrow = key[pygame.K_RIGHT]
        step_through = key[pygame.K_n]
        one = key[pygame.K_1]
        two = key[pygame.K_2]
        three = key[pygame.K_3]
        
        # Find out where the mouse is
        x, y = pygame.mouse.get_pos()
        # Find the top left corner of the cell that the mouse is in
        left = ((x/cell_size)*cell_size)+2
        top = ((y/cell_size)*cell_size)+2
        # Find the x,y index of the 2D Grid that the mouse is in
        x_index = (left-2)/cell_size
        y_index = (top-2)/cell_size
        
        if (x_index, y_index) in cells:
            # Place Start
            if ctrl and left_click and not start_placed and cells[(x_index, y_index)]['state'] != 'Start' and  cells[(x_index, y_index)]['state'] != 'Goal':
                start_placed = True
                cells[(x_index, y_index)]['state']='Start'
                draw_cell(left,top, cell_size-2, bright_green)
                start = (x_index, y_index)
            
            # Remove Start
            elif ctrl and left_click and start_placed and cells[(x_index, y_index)]['state'] == 'Start':
                start_placed = False
                cells[(x_index, y_index)]['state']=None
                r = pygame.Rect(left, top, cell_size-2, cell_size-2)
                pygame.draw.rect(board, gray, r, 0)
                start = None
                
            # Place Goal
            elif ctrl and right_click and not goal_placed and cells[(x_index, y_index)]['state'] != 'Goal' and  cells[(x_index, y_index)]['state'] != 'Start':
                cells[(x_index, y_index)]['state']='Goal'
                goal_placed = True
                r = pygame.Rect(left, top, cell_size-2, cell_size-2)
                pygame.draw.rect(board, red, r, 0)
                goal = (x_index, y_index)
        
            # Remove Goal
            elif ctrl and right_click and goal_placed and cells[(x_index, y_index)]['state'] == 'Goal':
                cells[(x_index, y_index)]['state']=None
                goal_placed = False
                r = pygame.Rect(left, top, cell_size-2, cell_size-2)
                pygame.draw.rect(board, gray, r, 0)
                goal = None
                
            # Place Wall
            elif shift and left_click and cells[(x_index, y_index)]['state'] == None and  last_wall != (x_index, y_index):
                cells[(x_index, y_index)]['state']='Wall'
                r = pygame.Rect(left, top, cell_size-2, cell_size-2)
                pygame.draw.rect(board, black, r, 0)
                last_wall = (x_index, y_index)
        
            # Remove Wall
            elif shift and left_click and cells[(x_index, y_index)]['state'] == 'Wall' and last_wall != (x_index, y_index):
                cells[(x_index, y_index)]['state'] = None
                r = pygame.Rect(left, top, cell_size-2, cell_size-2)
                pygame.draw.rect(board, gray, r, 0)  
                last_wall = (x_index, y_index)     
        
            # Reset Board
            elif escape:
                for cell in cells:
                    for x in cells[cell]:
                        cells[cell][x]=None
                start_placed = goal_placed = False
                board = initBoard(screen)
                start = goal = last_wall = None
                open_list = []
                closed_list = {}
                pq_dict = {}
                needs_refresh = step_started =False
            
            # Soft Reset Board (keep start, goal and walls)
            elif delete:
                i = 0
                for cell in cells:
                    if cells[cell]['state'] != 'Wall' and cells[cell]['state'] != 'Start' and cells[cell]['state'] != 'Goal':
                        i += 1
                        for x in cells[cell]:
                            cells[cell][x] = None
                        left, top = cell
                        left = (left*cell_size)+2
                        top = (top*cell_size)+2
                        r = pygame.Rect(left, top, cell_size-2, cell_size-2)
                        pygame.draw.rect(board, gray, r, 0)
                    elif cells[cell]['state'] == 'Start' or cells[cell]['state'] == 'Goal':
                        for x in cells[cell]:
                            if x != 'state':
                                cells[cell][x] = None
                showBoard(screen, board)
                open_list = []
                closed_list = {}
                pq_dict = {}
                needs_refresh = step_started= False
            
            # Verbose Path Find
            elif enter and not needs_refresh:
                findPath(slow = True, step = False)
                needs_refresh = True
            
            # Instant Path Find
            elif right_arrow and not needs_refresh:
                findPath(slow = False, step = False)
                needs_refresh = True
            
            # Start Step Through Path Find
            elif step_through and not step_started:
                findPath(slow = False, step = True)
                step_started = True
                
            # Continue Step Through Path Find
            elif step_through and step_started and not needs_refresh:
                if len(open_list) == 0:
                    print 'NO POSSIBLE PATH!'
                f = heapq.heappop(open_list)
                if len(pq_dict[f]) > 1:
                    node = pq_dict[f].pop()
                else:
                    node = pq_dict.pop(f)[0]

                heapq.heapify(open_list)
                closed_list[node]=True

                if node != goal and node != start:
                    left, top = node
                    left = (left*cell_size)+2
                    top = (top*cell_size)+2
                    r = pygame.Rect(left, top, cell_size-2, cell_size-2)
                    pygame.draw.rect(board, blue, r, 0)
                processNode(node, slow = False, step = True)
                
            # Change Heuristic to "As the Crow Flies"    
            elif shift and one:
                heuristic = 'crow'
            
            # Change Heuristic to "Manhattan Distance"
            elif shift and two:
                heuristic = 'manhattan'
                
            # Change Heuristic to Neive heuristic assuming h( ) = 0
            elif shift and three:
                heuristic = 'zero'
            showBoard(screen, board)
