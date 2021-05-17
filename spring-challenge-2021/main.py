import sys
import math
import itertools

from dataclasses import dataclass

def debug(*args):
  print(*args, file=sys.stderr)

class Forest:
  def __init__(self):
    number_of_cells = int(input())  # 37
    self.cells = [Cell(input().split()) for i in range(number_of_cells)]
    self._calculate_cell_neighbors()

    self.day_max = 23
    self.day = 0

    self.nutrients = 0

    self.sun = 0
    self.score = 0

    self.opp_sun = 0
    self.opp_score = 0
    self.opp_is_waiting = False

    self.trees = []
    self.tree_by_cell_id = {}
    self.trees_mine = []
    self.trees_mine_active = []
    self.trees_opp = []
    self.trees_mine_by_size = {i:[] for i in range(0,4)}
    self.trees_opp_by_size = {i:[] for i in range(0,4)}

    self.max_seeds = 1 # maximum number of seeds
    self.max_level_3 = 7 # maximum number of size:3 tree
    self.min_level_3 = 0 # minimum number of size:3 tree (before the last day)
    self.max_trees = 9 # maximum number of trees allowed - the map can have 8 trees without having shadows, more and we would start having problems.
    self.producer_trees_number = 2 # number of trees that should NOT be impacted by a single shadow

  def read_inputs_loop(self):
    self.day = int(input())  # the game lasts 24 days: 0-5
    self.nutrients = int(input())  # the base score you gain from the next COMPLETE action
    # sun: your sun points
    # score: your current score
    self.sun, self.score = [int(i) for i in input().split()]
    inputs = input().split()
    
    self.opp_sun = int(inputs[0])  # opponent's sun points
    self.opp_score = int(inputs[1])  # opponent's score
    self.opp_is_waiting = inputs[2] != "0"  # whether your opponent is asleep until the next day
    
    number_of_trees = int(input())  # the current amount of trees
    self.trees = [Tree(self.cells, input().split()) for i in range(number_of_trees)]

    number_of_possible_moves = int(input())
    possible_moves = [input() for i in range(number_of_possible_moves)]

    # post input treatment
    self._calculate_trees()
  
  def _calculate_trees(self):
    self.tree_by_cell_id = {}
    self.trees_mine = []
    self.trees_mine_active = []
    self.trees_opp = []
    self.trees_mine_by_size = {i:[] for i in range(0,4)}
    self.trees_opp_by_size = {i:[] for i in range(0,4)}
    for tree in self.trees: # single loop to improve performance
      self.tree_by_cell_id[tree.cell.index] = tree
      if tree.is_mine:
        self.trees_mine.append(tree)
        self.trees_mine_by_size[tree.size].append(tree)
        if not tree.is_dormant:
          self.trees_mine_active.append(tree)
      else:
        self.trees_opp.append(tree)
        self.trees_opp_by_size[tree.size].append(tree)
    
    # calculate shadow ratio for each one of my trees
    for tree in self.trees_mine:
      tree.shadow_ratio = self.cell_ratio_shadow(tree.cell, self.day)

  def _calculate_cell_neighbors(self):
    # change cells id to cells pointer
    for cell in self.cells:
      cell.neighbors = [self.cells[i] if i != -1 else None for i in cell.neighbors_id ]
    
    # calculate cells distance
    for cell in self.cells:
      neighbors = self.__calculate_cell_neighbors_recursive(cell)
      cell.neighbors_by_size = {i:[self.cells[cell_j] for cell_j in neighbors if neighbors[cell_j] == i] for i in range(1,4)}
      if len(cell.neighbors_by_size[1])>6 or len(cell.neighbors_by_size[2])>12 or len(cell.neighbors_by_size[3])>18:
        debug("ERROR calculate cell neighbors", cell, cell.neighbors_by_size)

  def __calculate_cell_neighbors_recursive(self, cell, output = None, distance=1, max_distance=3):
    """recursively calculate the distance. return {case_id: distance}"""
    if max_distance - distance < 0:
      return output

    if output is None:
      output = {}
      output[cell.index] = 0

    for cell_n in cell.neighbors:
      if cell_n is None:
        continue
      if cell_n.index not in output or output[cell_n.index] > distance:
        output[cell_n.index] = distance
        if distance + 1 <= max_distance:
            self.__calculate_cell_neighbors_recursive(cell_n, output, distance +1, max_distance)
    
    return output

  def grow_cost(self, size):
    if size+1 not in self.trees_mine_by_size:
      debug("grow_cost", size+1, self.trees_mine_by_size)
    return size ** 2 + size + 1 + len(self.trees_mine_by_size[size+1])
  
  def seed_cost(self):
    return len(self.trees_mine_by_size[0])

  def get_cases_shadow(self, case, day, size=3, reverse=False):
    """Get the cases impacted by a shadow cast by the `case` at `day` if a tree of `size` where on it.
    reverse = calculate the cases that will cast a shadow on this case. 
    """
    output = []
    current_case = case
    day_mod = (day + 3 * reverse)%6
    for _ in range(size):
      if current_case.neighbors[day_mod] is None:
        break
      else:
        output.append(current_case.neighbors[day_mod])
        current_case = current_case.neighbors[day_mod]
    return output

  def is_shadowed(self, case, day, exclude_shadows_from_cells_id=[]):
    """Verify if a given cell is shadowed on a given day
      You can exclude some cells from the shadow detector by ading their index to the exclude_shadows_from_cells_id variable.
    """
    shadows = self.get_cases_shadow(case, day, size = 3, reverse = True)
    i = 0
    for case in shadows:
      i+=1
      if case.index in exclude_shadows_from_cells_id: # do not include this variable in the shadows detection
        continue
      if case.index in self.tree_by_cell_id:
        tree = self.tree_by_cell_id[case.index]
        if tree.size >= i:
          return True
    return False
  
  def cell_ratio_shadow(self, cell, day):
    """return the ratio risk of being shadowed on this cell for the next 6 days."""
    output=0
    for delta_day in range(1, 7):
      cases = self.get_cases_shadow(cell, day + delta_day, size = 3, reverse = True)
      for index, case in enumerate(cases):
        if case.index in self.tree_by_cell_id:
          tree = self.tree_by_cell_id[case.index]
          if tree.size + delta_day - (tree.is_dormant) > index:
            output+=1/6
            break
            # TODO best delimitation of different cases by distance ? 
    
    return output

  def impact_shadow(self, case, day, size=3):
    """return the impact of the shadow on a given day. positive number means it will impact more the ennemy than us.
    output can be :
    - size:1 = from -1 to +0.75.
    - size:2 = from -2 to +1.5.
    - size:3 = from -3 to +2.25.
    """
    output = 0
    cases_impacted = self.get_cases_shadow(case, day, size)
    for case in cases_impacted:
      if case.index in self.tree_by_cell_id:
        tree = self.tree_by_cell_id[case.index]
        output+= -(tree.size+1)/4 if tree.is_mine else tree.size / 4 # more impact if this is our tree as the shadow would go both ways
    
    return output
  
  def impact_shadow_seed(self, case, day):
    """return the impact of the expected shadow of a seed planted on a given day. positive number means it will impact more the ennemy than us. it will try to favor our positions.
    output = float
      - no_shadows : 4.51
    """
    output = 0
    # direct future
    for i in range(3):# calculate first for when the tree will grow
      impact = self.impact_tree_sun_points(case, size=i+1, day=day+2+i )
      output+= (impact[0]-impact[1] * 0.5) * (3-i)/3
    
    # long-time future
    for i in range(3):
      impact = self.impact_tree_sun_points(case, size=3, day=day+5+i )
      output+= (impact[0]-impact[1] * 0.5) / (4+i) # no_shadows: 3/4, 3/5, 1/2 
    
    return output

  def impact_growth_tree_on_sun(self, tree, day, delta_day=3):
    """calculate the impact growing a tree on a given day will have on sun production for delta_days.
    return two integers, (our_difference, opponent_difference)
    """
    if tree.size == 3:
      return (None, None)

    our_diff = 0
    opp_diff = 0

    for i in range(1, delta_day+1):
      # === if not shadowed, the tree will produce one more sun ===
      if not self.is_shadowed(tree.cell, day+i):
        our_diff+=1
      
      # === verify the impact of growing this tree on other trees ===
      cases_impacted_shadow = self.get_cases_shadow(tree.cell, day+i, size=tree.size+1)
      if len(cases_impacted_shadow) < tree.size or len(cases_impacted_shadow) == 0: # when we get to the edge
        continue
      else:
        if cases_impacted_shadow[-1].index in self.tree_by_cell_id: # a new tree is impacted
          impact_ratio = 1
          # === check if a shadow is already cast on the tree ===
          for index, case in enumerate(cases_impacted_shadow[:-1]):
            if case.index in self.tree_by_cell_id and self.tree_by_cell_id[case.index].size >= tree.size-(index+1): # a shadow is already being cast
              impact_ratio = 0.5
              break
          impacted_tree = self.tree_by_cell_id[cases_impacted_shadow[-1].index]
          if impacted_tree.is_mine:
            our_diff-=impacted_tree.size * impact_ratio
          else:
            opp_diff-=impacted_tree.size * impact_ratio
    
    return (our_diff, opp_diff)

  def impact_growth_tree_on_seedable_surfaces(self, tree):
    """return a number indicating if the new surfaces seedables are worth it
      number is between 0 and 1.
    """
    if tree.size > 2:
      return 0 
    output = 0
    length = len(tree.cell.neighbors_by_size[tree.size + 1])
    for cell in tree.cell.neighbors_by_size[tree.size + 1]:
      if cell not in self.tree_by_cell_id:
        output+= cell.richness / ( 3 * length )

    return output

  def impact_tree_sun_points(self, cell, size, day):
    """return the number of sun points a given tree will have on the day, for our points and the opponent's points.
    It will also calculate lost potential on shadowed trees that wouldn't be shadowed if this tree wasn't here.
    """
    our_sun_diff=0
    opp_sun_diff=0

    # if the tree is not shadowed
    if not self.is_shadowed(cell, day):
      our_sun_diff+=size

    # calculate my shadow impact
    cases_shadowed = self.get_cases_shadow(cell, day, size=size)
    for i, case in enumerate(cases_shadowed):
      if case.index in self.tree_by_cell_id:
        if not self.is_shadowed(case, day, exclude_shadows_from_cells_id=[cell.index]): # if the case is only shadowed by this case
          tree_case = self.tree_by_cell_id[case.index]
          if tree_case.is_mine:
            our_sun_diff-=tree_case.size
          else:
            opp_sun_diff-=tree_case.size
    
    return (our_sun_diff, opp_sun_diff)

  def _case_get_seed_value(self, case, tree, prefer_unshadowed = False):
    """get the value of the case
    return flaot: 
    """
    # value : richness + shadow impact + is_shadowed + near higher cases
    # in current configuration, ombrage > richness > neighbors
    if case.richness == 0:
      return None
    if self.score < self.opp_score or self.day > 15:
      value = 3 * (case.richness-1)  # 0, 3, 6
    else:
      value = case.richness  # 1, 2, 3

    shadow_impact = self.impact_shadow_seed(case, self.day) # +4.51 in no_shadow cases
    value+= shadow_impact

    if prefer_unshadowed and shadow_impact >= 3: # +4.51 for no shadows at all
      value+= 2 * shadow_impact
    
    # check if the case is near a case with high richness
    for neigh in case.neighbors:
      if neigh != None:
        value+=max(neigh.richness-1, 0)/(2*6) # can add a max of +1, this is just to differentiate some cases

        # check who are ou rdirect neighbors, try to avoid having any ? 
        if neigh.index in self.tree_by_cell_id:
          tree_neigh = self.tree_by_cell_id[neigh.index]
          if tree_neigh.is_mine:
            value-=(tree_neigh.size + 1 ) / 6
          else:
            value+=tree_neigh.size / 6
    
    # and finally, add a modificator on the tree casting the seed
    if tree.size != 3 and not self.is_shadowed(tree.cell, self.day+1) and self.impact_growth_tree_on_sun(tree, self.day+1)[0] > 0: # if this tree could be grown this turn : little malus
      value-=tree.size*(tree.cell.richness / 3)
    elif self.is_shadowed(tree.cell, self.day+1): # if this tree could be completed this turn
      value-=tree.get_score(nutrients=0)

    return value

  def find_case_to_seed(self, prefer_unshadowed = False):
    """find the case and tree that can be seeded"""
    # calculate using this formula :
    # if a tree on a N richness cell can seed a N+1 richness cell, grant +2 interest by richness difference
    # if the seed can in the next 3 turns grow and cast shadow on opponents tree, grant +2 interest by impacted tree
    # if the seed can in the next 3 turns grow and cast shadow on my tree, grant +1 interest by tree (still useful to seed here as it would prevent the opponent from doing so)
    # if a tree on a N richness cell can seed a N-1 richness cell, grant -0.5 interest by reichness difference
    seed_to_plant = (None, None, 3.15) #(tree, cell_to_seed, interest) - interest starts at 3 to prevent bad placements
    for tree in self.trees_mine_active:
      neighbors = list(itertools.chain.from_iterable(tree.cell.neighbors_by_size[i] for i in range(1, tree.size+1)))
      for cell in neighbors:
        if cell.richness != 0 and cell.index not in self.tree_by_cell_id:
          cell_value = self._case_get_seed_value(cell, tree, prefer_unshadowed)
          if cell_value > seed_to_plant[2]:
            seed_to_plant = (tree, cell, cell_value)
    debug("cell selected to plant", seed_to_plant)
    return seed_to_plant[0:2]
    
  def find_tree_to_grow(self, min_size = 0, prefer_unshadowed_tree = False):
    """find the best tree to grow"""
    output = None
    best = -9999
    prioritize_3 = len(self.trees_mine_by_size[3]) < self.min_level_3 # TODO this is what makes us lose 50 sunpoints
    for tree in self.trees_mine_active:
      if tree.size >= 3 or tree.size < min_size:
        continue
      
      grow_cost = self.grow_cost(tree.size)

      if grow_cost > self.sun:
        continue
      
      # === impact on sun production for the next 3 days ===
      our_sun_diff, opp_sun_diff = self.impact_growth_tree_on_sun(tree, self.day, 3)
      sun_opportunity = our_sun_diff - opp_sun_diff*0.5 - grow_cost

      # === impact on new seedable cells ===
      impact_availables_terrains = self.impact_growth_tree_on_seedable_surfaces(tree)

      if self.day < 3: # first 3 day : grow and conquer
        opportunity = tree.cell.richness + sun_opportunity + 2 * impact_availables_terrains
      else:
        if prioritize_3:
          opportunity = tree.cell.richness * (tree.size + 1) ** 2 + sun_opportunity + 2 * impact_availables_terrains
        else:
          opportunity = tree.cell.richness**2 * (tree.size + 1) + sun_opportunity**2 + 2 * impact_availables_terrains

      # === grow rendering tree ===
      if prefer_unshadowed_tree:
        bonus=10
        for i in range(6):
          if self.is_shadowed(tree.cell, i):
            bonus = 0
            break
        opportunity+=bonus
      
      # === no negative impact in the next 3 turns on our trees + no shadow - double the impact of the selected tree
      if our_sun_diff >= 2:
          opportunity+=our_sun_diff
      if self.is_shadowed(tree.cell, self.day+1):
        # don't grow a tree that won't render anything next turn
        opportunity -= grow_cost

      if opportunity > best:
        best = opportunity
        output = tree

    return output
  
  def find_tree_to_complete(self):
    if len(self.trees_mine_by_size[3]) == 0:
      return None

    cut_last_turns = self.day_max - self.day < 5
    cut_needed_for_score = self.score + self.nutrients <= self.opp_score # only cut for score if we're at risk of getting fucked 
    # TODO add a opponent_is_waiting ?

    if not cut_last_turns: # not the last turn
      if len(self.trees_mine) - len(self.trees_mine_by_size[0]) < 3: # prevent cutting the last 3 tree
        return None
    
      if len(self.trees_mine_by_size[3]) <= self.min_level_3 and not cut_needed_for_score : # keep at least min_level_3 fully grown trees
        return None # commented because this seems to reduce our winning ability

    output = None
    best = 0 # cutting a tree should add worth to our score
    for tree in self.trees_mine_by_size[3]:
      if tree.is_dormant: # dormant trees cannot be completed
        continue
      
      # score gained from cutting this tree
      score = tree.get_score(self.nutrients)

      sun_points_difference_next_days = [self.impact_tree_sun_points(tree.cell, tree.size, self.day+i) for i in range(1,4)]# [(out_sun_diff, opp_sun_diff),...] - positive means gain at the next turn by the tree BEING there.
      sun_points_gain_next_days = [-i[0]+i[1]*0.9 for i in sun_points_difference_next_days]# if positive, this means we gain more sun points in the next day by cutting this tree than the opponent.

      opportunity = -1
      if cut_last_turns and score > 0: # last day - only score matters
        opportunity = score
      elif cut_needed_for_score and score > 0:
        if (self.score >= self.opp_score or self.opp_is_waiting) and sun_points_gain_next_days[0] < 0: # the tree still have utility and we don't absolutely need to cut it this round
          continue
        else:
          opportunity = score + sun_points_gain_next_days[0] * 6
      else:
        if sun_points_gain_next_days[0] <= 0 and self.score >= self.opp_score: # cutting this tree does not really help us " TODO also add self.opp_is_waiting"
          continue
        else:
          opportunity = score / 6 + sun_points_gain_next_days[0] + sun_points_gain_next_days[1]*2/3 + sun_points_gain_next_days[2] / 3

      if opportunity > best:
        best = opportunity
        output = tree

    return output

  def allow_plant_seed(self):
    """return True/False if we should allow the IA to plant a seed"""
    day_delay = self.day_max - self.day

    if self.seed_cost() > self.sun: # not enough sun points to seed
      return False

    if day_delay == 0: # last day
      if self.sun % 3 >= self.seed_cost(): # if there are some sun points leftovers that won't be converted to score point
        if len(self.trees_mine_by_size[3]) == 0 or self.sun < 4: # if those sun points can't be used to complete a tree
          return True
      return False
    
    if self.day < 2: # first days : never useful to plant
      return False

    if len(self.trees_mine) >= self.max_trees: # we already have enough trees
      return False # TODO check if all _growing_ trees are asleep, it might be useful to bypass this limit if needeed
    
    if len(self.trees_mine_by_size[0]) >= self.max_seeds: # we already have enough seeds
      return False # TODO check if all _growing_ trees are asleep, it might be useful to bypass this limit if needeed

    # all good
    return True
  
  def allow_complete_trees(self):
    """determine if we should try to complete a tree now or not. note this does NOT force a tree to be cut down."""

    if self.day <= 6: # don't cut trees too early game
      return False
    
    if self.sun < 4: # not enough points to complete a tree
      return False
    
    if self.day_max - self.day <= 5: # complete trees in a harsher way in the last turns
      return True

    if self.score > self.opp_score + self.nutrients: # if we already have a much better score than the adversary
      return False
    
    if len(self.trees_mine_by_size[3]) < self.min_level_3: # If we don't have enough level 3 trees
      return False
    
    # enough points to afford it
    # score is worse or equal to opponent
    # we have enough size-3 trees
    return True


    should_complete_tree = self.day > 10 and (self.score <= self.opp_score or len(self.trees_mine_by_size[3]) > self.min_level_3 or day_delay < 1)

  def calculate_action(self):
    """determine what is the best action to take"""
    # if day < 5 : grow,  don't cut anything, try to plant seed
    # if day >= 5 : always keep an edge on the score, try to maintain self.max_size_3 fully grown trees
    # if max_days - day <= 3 : stop to plant seeds
    # if max_days - day <= 2 : stop to grow seeds
    # if max_days - day <= 1 : stop to grow level 1
    # if max_days - day == 0 : only complete trees

    day_delay = self.day_max - self.day
    minimum_size_grow = 3 - day_delay
    can_plant_seed = self.allow_plant_seed()

    trees_mine_unshadowed = [tree for tree in self.trees_mine if tree.shadow_ratio == 0]

    # Modify priority if we don't have trees that are unshadowed
    should_seed_unshadowed_tree = False
    should_grow_unshadowed_tree = False
    if day_delay > 5 and len(trees_mine_unshadowed) < self.producer_trees_number:
      should_seed_unshadowed_tree = day_delay > 5
    elif len([tree for tree in trees_mine_unshadowed if tree.size == 3]) < self.producer_trees_number:
      should_grow_unshadowed_tree = True
    
    # if we should TRY to complete trees
    should_complete_tree = self.allow_complete_trees()

    # ========= day 0 - no actions =========
    if self.day == 0:
      return "WAIT"

    # ========= try to complete tree first ========
    if should_complete_tree:
      tree_to_complete = self.find_tree_to_complete()
      if tree_to_complete is not None:
        return f"COMPLETE {tree_to_complete.cell.index}"
    
    # ========= if # of seeds planted is 0 and we can plant one - plant before growing ====
    if can_plant_seed and self.seed_cost() == 0:
      seed_to_plant = self.find_case_to_seed(should_seed_unshadowed_tree)
      if seed_to_plant[0] is not None:
        return f"SEED {seed_to_plant[0].cell.index} {seed_to_plant[1].index}"

    # ========= try to find a tree to grow =========
    tree_to_grow = self.find_tree_to_grow(minimum_size_grow) # TODO add should_grow_unshadowed_tree
    if tree_to_grow is not None:
      return f"GROW {tree_to_grow.cell.index}"
    
    # ========= find a seed to seed =======
    if can_plant_seed:
      seed_to_plant = self.find_case_to_seed(should_seed_unshadowed_tree)
      if seed_to_plant[0] is not None:
        return f"SEED {seed_to_plant[0].cell.index} {seed_to_plant[1].index}"

    # ========= no actions could be found - stop round =======
    return "WAIT"

class Cell:
  def __init__(self, args):
    self.index = int(args[0])
    self.richness = int(args[1])
    self.neighbors_id = list(map(int, args[2:8]))
    self.neighbors = [None] * 6
    self.neighbors_by_size = {i:[] for i in range(3)} # used to have all neighbors in range(1->3)
  
  def __repr__(self):
    return f"Cell {self.index}"

class Tree:
  def __init__(self, cells, args):
    self.cell_index = int(args[0])
    self.cell = cells[self.cell_index]
    self.size = int(args[1])
    self.is_mine = args[2] != '0'
    self.is_dormant = args[3] != '0'

    self.shadow_ratio = -1
    
  def get_score(self, nutrients: int):
    return nutrients + 2 * (self.cell.richness - 1)
    
  def grow_cost(self, forest):
    return self.size ** 2 + self.size +1 + len(forest.trees_mine_by_size[self.size+1])
  
  def __repr__(self):
    return f"Tree - size {self.size} - is_mine : {self.is_mine} - dormant : {self.is_dormant} - cell_index : {self.cell_index} / {self.cell.index}]"



# ============================ main code ================================
FOREST = Forest()

# game loop
while True:
    # get all inputs
    FOREST.read_inputs_loop()
    
    action = FOREST.calculate_action()

    print(action)

# was 323