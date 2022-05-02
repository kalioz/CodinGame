import sys, math, statistics, random

BASE_AGGRO_DIST = 5000
BASE_DAMAGED_DIST = 300
SPELL_WIND_MOVE = 2200
SPELL_WIND_RADIUS = 1280
SPELL_CONTROL_RANGE = 2200
SPELL_SHIELD_RANGE = 2200

HERO_MOVE_SPEED = 800
HERO_DAMAGE = 2
HERO_DAMAGE_RADIUS = 800

MONSTER_MOVE_SPEED = 400

SPELL_COST_MANA = 10

VISION_HERO = 2200
VISION_BASE = 6000

IDLE_POSITIONS = None
CURRENT_ENTITIES = []

def debug(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr, flush=True)

def isInsideCircle(circle_x, circle_y, radius, x, y):
    # Compare radius of circle
    # with distance of its center
    # from given point
    return ((x - circle_x) * (x - circle_x) + (y - circle_y) * (y - circle_y) <= radius * radius)

class Point:
    def __init__(self, x, y):
        self.x = int(x)
        self.y = int(y)

    def outside_boundaries(self):
        return not (self.x > MAP_MIN.x and self.y > MAP_MIN.y and self.x < MAP_MAX.x and self.y < MAP_MAX.y)

    def distance(self, x, y=None):
        if y is None and isinstance(x, Point):
            return self.distance_point(x)
        return math.dist([self.x, self.y], [x, y])

    def near(self, point, max_allowed_distance):
        # check if the distance between self and point is below the max_allowed_distance
        return self.distance_point(point) < max_allowed_distance

    def distance_point(self, point):
        return self.distance(point.x, point.y)

    def calculate_position_circle(self, radius, radians):
        # calculate the position of another point if it were on a circle of radius at a degree of radians
        return self + Point(radius * math.cos(radians), radius * math.sin(radians))

    def calculate_position_circle_nearest(self, radius, point):
        """calculate the position in the circle of radius R and of center self so that it is the closest to point."""
        radians = math.atan2(point.y - self.y, point.x - self.x)
        return self.calculate_position_circle(radius, radians)

    def __eq__(self, other):
        if (isinstance(other, Point)):
            return self.x == other.x and self.y == other.y
        return False

    def __repr__(self):
        return f'Point(x: {self.x}, y: {self.y})'

    def __add__(self, point):
        return Point(self.x + point.x, self.y + point.y)

    def __sub__(self, point):
        return Point(self.x - point.x, self.y - point.y)

    def __truediv__(self, other):
        if isinstance(other, float) or isinstance(other, int):
            return Point(self.x / other, self.y / other)
        else:
            raise TypeError(f'Cannot multiply a Point with {type(other)}')


    def __mul__(self, other):
        if isinstance(other, float) or isinstance(other, int):
            return Point(self.x * other, self.y * other)
        else:
            raise TypeError(f'Cannot multiply a Point with {type(other)}')

    __rmul__ = __mul__


MAP_MIN = Point(0,0)
MAP_MAX = Point(17630, 9000)

class Entity:
    # class wide variable
    ## tracks the entities across turns
    __entities = {}

    def __new__(cls, id, *args, **kwargs):
        # creates or get the existing entity from the tracked list
        if id in Entity.__entities:
            return Entity.__entities[id]
        out = object.__new__(cls)
        Entity.__entities[id] = out
        return out

    def __init__(self, id, type, x, y, shieldLife, isControlled, health, vx, vy, near_base, threat_for):
        self.id = id
        self.type = type # 0 monster, 1 myHero, 2 ennemyHero
        self.position = Point(x, y)
        self.shieldLife = shieldLife
        self.isControlled = isControlled
        # the below is only valid for monsters
        self.health = health
        self.deplacement = Point(vx, vy)
        self.near_base = near_base # 1 if targets a base, else 0
        self.threat_for = threat_for # 1 if it's my base, 2 if it's ennemy base. only active if near_base is.

        self.last_seen = TURN_ID

        self.future_position = self.position + self.deplacement # future position, modified by wind spell

        # the below is custom, for my heroes
        if not hasattr(self, 'idle_position'):
            # use this if/else to prevent overwriting old data.
            self.idle_position = None # position where the hero should go and wait if he goes too far from the castle.

        if not hasattr(self, 'has_already_been_controlled'):
            # use this if/else to prevent overwriting old data.
            self.has_already_been_controlled = bool(self.isControlled) # position where the hero should go and wait if he goes too far from the castle.
        else:
            self.has_already_been_controlled |= bool(self.isControlled)
        self.can_do_action = True
        self.label = ""
        self.hero_type = "defensive" # Can be "offensive", "defensive" or "middle"
        self.hero_index = -1

    def distance(self, other):
        if isinstance(other, Point):
            return self.position.distance_point(other)
        elif isinstance(other, Entity):
            return self.position.distance_point(other.position)
        else:
            raise Exception("Not handled")

    def rounds_to_reach(self, mob, point_of_interest = None, max_range = None):
        """calculate the number of rounds needed to reach a mob"""
        if max_range is None:
            max_range = HERO_DAMAGE_RADIUS - 1
        number_of_turns = 0
        mob_position = mob.position
        max_rounds = 30
        while self.position.distance_point(mob_position) > number_of_turns * HERO_MOVE_SPEED + max_range:
            number_of_turns+=1
            if number_of_turns > max_rounds:
                break
            if number_of_turns > 1: # don't count the first turn as we would arrive near the mob anyway
                mob_position = mob_position + mob.deplacement

        return number_of_turns

    def calculate_intercept(self, mob, point_of_interest = None, max_range = None):
        """calculate the best path to intercept a mob
            mob: entity to intercept
            point_of_interest: if set, will output coordinates that are more near this point. this allow for quicker withdrawal / intercept.
        """
        if max_range is None:
            max_range = HERO_DAMAGE_RADIUS - 1
        number_of_turns = 0
        mob_position = mob.position
        while self.position.distance(mob_position) > number_of_turns * HERO_MOVE_SPEED + max_range:
            number_of_turns+=1
            if number_of_turns > 1: # don't count the first turn as we would arrive near the mob anyway
                mob_position = mob_position + mob.deplacement

        # calculate points in a line between the mob and the player
        possible_points = [
            mob_position.calculate_position_circle_nearest(max_range * i / 10, self.position) for i in range(11)
        ]

        if point_of_interest is not None:
            # calculate points in a line between the mob and the point of interest
            possible_points+= [
                mob_position.calculate_position_circle_nearest(max_range * i / 10, self.position) for i in range(11)
            ]
        else:
            point_of_interest = self

        if number_of_turns == 0:
            # if we're already at hitting distance : find a better place
            number_of_turns = 1
        possible_points = [p for p in possible_points if self.position.distance(p) <= number_of_turns * HERO_MOVE_SPEED]

        if len(possible_points) == 0:
            # shouldn't be possible / edge case
            possible_points = [ mob_position ]

        return min(possible_points, key=lambda p: point_of_interest.distance(p))

    def near(self, other, max_allowed_distance):
        if isinstance(other, Point):
            return self.position.near(other, max_allowed_distance)
        elif isinstance(other, Entity):
            return self.position.near(other.position, max_allowed_distance)
        elif isinstance(other, list):
            return all(self.near(i, max_allowed_distance) for i in other)
        else:
            raise Exception("type not handled", other)

    def next_position(self, n=1):
        # computes the next position according to the vector. can be done n times
        return self.position + self.deplacement * n

    def findBestAttackPoint(self, entityList, priority_entity = None, attack_range=None, deplacement_range=None):
        """Find the best point to attack the biggest number of passed entities
            entityList: the list of entities succeptible to an attack
            priority_entity: if set, this entity WILL be included in the attack.
            attack_range: the max range the point outputted should be from the targets. defaults to HERO_DAMAGE_RADIUS
            deplacement_range: if set, the max range the point should be from the self.

            returns a (Point, number_of_victims), or None if no point was found.
        """

        if attack_range is None:
            attack_range = HERO_DAMAGE_RADIUS

        in_range_mobs = entityList
        if deplacement_range is not None:
            in_range_mobs = [ mob for mob in entityList if self.near(mob, deplacement_range + attack_range)]

        if len(in_range_mobs) == 0:
            return None

        # find all mobs that can be grouped together 2 per 2
        mobs_near_anothers = {} # {mob_1: [mob_2, mob_3]}
        for i in range(len(in_range_mobs)):
            for j in range(i + 1, len(in_range_mobs)):
                if in_range_mobs[i].near(in_range_mobs[j], 2 * attack_range - 1): # use 2 * attack_range as you can be in the middle to attack them
                    if in_range_mobs[i] not in mobs_near_anothers:
                        mobs_near_anothers[in_range_mobs[i]] = [ in_range_mobs[i], in_range_mobs[j] ]
                    else:
                        mobs_near_anothers[in_range_mobs[i]].append(in_range_mobs[j])
                    if in_range_mobs[j] not in mobs_near_anothers:
                        mobs_near_anothers[in_range_mobs[j]] = [ in_range_mobs[j], in_range_mobs[i] ]
                    else:
                        mobs_near_anothers[in_range_mobs[j]].append(in_range_mobs[i])


        # check the highest group of mobs we can get
        best_point = None
        best_point_number_of_mobs_reached = 0

        for key in mobs_near_anothers:
            mobs = mobs_near_anothers[key]
            while len(mobs) >= best_point_number_of_mobs_reached and (priority_entity is None or priority_entity in mobs):
                # find center of group
                # if not every member is at reach from center of group, remove farthest member
                # retry until exhaustion
                center_of_group = Point(statistics.mean([mob.position.x for mob in mobs]), statistics.mean([mob.position.y for mob in mobs]))

                distances = list(mob.position.distance(center_of_group) for mob in mobs)
                max_distance = max(distances)
                if max_distance > attack_range:
                    farthest = distances.index(max_distance)
                    if farthest == 0:
                        # don't remove first key as it's the "primary" mob
                        farthest = distances.index(sorted(distances)[-2])
                    del mobs[farthest]
                elif deplacement_range is None or (best_point is None or self.distance(best_point) < deplacement_range):
                    best_point = center_of_group
                    best_point_number_of_mobs_reached = len(mobs)
                    break
                else:
                    # middle point is too far - not handled for now, just remove this lot from the possible options
                    break

        if best_point is None:
            # should'nt happend, but hey
            return None

        return (best_point, best_point_number_of_mobs_reached)

    def findNearMe(self, entityList, max_allowed_distance=None, max_allowed_distance_point=None):
        # find the near entities
        #   max_allowed_distance : max distance allowed for entities to be considered valid
        #   max_allowed_distance_point : point used to calculate the max allowed distance. defaults to ME
        return self.findNear(entityList, self.position, max_allowed_distance, max_allowed_distance_point)

    def findNear(self, entityList, point, max_allowed_distance=None, max_allowed_distance_point=None):
        # find the near entities
        #   max_allowed_distance : max distance allowed for entities to be considered valid
        #   max_allowed_distance_point : point used to calculate the max allowed distance. defaults to point
        if max_allowed_distance is not None:
            if max_allowed_distance_point is None:
                max_allowed_distance_point = point
            entityList = [ entity for entity in entityList if entity.position.near(max_allowed_distance_point, max_allowed_distance) ]
        return entityList

    def findNearestMe(self, entityList, max_allowed_distance=None, max_allowed_distance_point=None):
        # find the nearest entity
        #   max_allowed_distance : max distance allowed for entities to be considered valid
        #   max_allowed_distance_point : point used to calculate the max allowed distance. defaults to ME
        return self.findNearestPoint(entityList, self.position, max_allowed_distance, max_allowed_distance_point=max_allowed_distance_point)

    def findNearestPoint(self, entityList, point, max_allowed_distance=None, max_allowed_distance_point=None):
        # find the nearest entity
        #   max_allowed_distance : max distance allowed for entities to be considered valid
        #   max_allowed_distance_point : point used to calculate the max allowed distance. defaults to point
        entities = self.findNear(entityList, point, max_allowed_distance, max_allowed_distance_point)
        if len(entities) == 0:
            return None
        return min(entities,
                     key= lambda x: x.position.distance_point(point))

    def is_threat_to_castle(self, my_heroes, ennemy_heroes ):
        """Check if the current mob entity can be killed before reaching the castle"""
        turns_to_reach_castle = math.ceil((self.position.distance_point(MY_PLAYER.base) - BASE_DAMAGED_DIST) / MONSTER_MOVE_SPEED)

        turns_to_reach_mob = min(hero.rounds_to_reach(self) for hero in my_heroes)

        # TODO calculate with multiple allies
        return turns_to_reach_castle < turns_to_reach_mob + self.health / HERO_DAMAGE

    def can_cast_spell_wind(self, entities):
        """Check if casting the wind spell now is feasible, meaning it would affect at least one of the entities"""
        return self.can_do_action and MY_PLAYER.mana >= SPELL_COST_MANA and any(self.near(entity, SPELL_WIND_RADIUS) and entity.shieldLife == 0 for entity in entities)

    def find_affected_spell_wind(self, entities):
        return list(entity for entity in entities if  self.near(entity, SPELL_WIND_RADIUS) and entity.shieldLife == 0 )

    def action_move(self, x, y):
        if not self.can_do_action:
            raise Exception("Trying to cast second action")
        self.can_do_action = False
        print(f'MOVE {int(x)} {int(y)} {self.label}')

    def action_move_to_entity(self, target, point_of_interest=None, max_range=None):
        """Move to the entity. if the point of interest and the range is set, try to move towards the target while keeping close to the point of interest.
            If the entity is a mob, will move to an intersection point instead of directly to it.
        """
        if target.type != 0:
            self.action_move(target.position.x, target.position.y)
        else:
            target_future_position = self.calculate_intercept(target, point_of_interest, max_range)
            self.action_move(target_future_position.x, target_future_position.y)

    def check_or_update_idle_position(self):
        if self.idle_position not in IDLE_POSITIONS[self.hero_type]:
            # get a random new idle position in the good set
            self.idle_position = random.choice(IDLE_POSITIONS[self.hero_type])
        if self.position == self.idle_position:
            # find a new idle position
            current_position_index = IDLE_POSITIONS[self.hero_type].index(self.idle_position)
            self.idle_position = IDLE_POSITIONS[self.hero_type][(current_position_index + 1)%len(IDLE_POSITIONS[self.hero_type])]


    def action_move_to_idle(self):
        """move the hero to its idle position. if its idle position is already maintained, force a change of its idle position."""
        self.check_or_update_idle_position()
        self.label+= " idle"
        self.action_move(self.idle_position.x, self.idle_position.y)

    def action_spell(self):
        if not self.can_do_action:
            raise Exception("Trying to cast second action")
        self.can_do_action = False
        # decrement mana cost for each spell cast
        MY_PLAYER.mana-=SPELL_COST_MANA

    def action_spell_wind(self, x, y):
        self.action_spell()
        move = Point(0, 0).calculate_position_circle_nearest(SPELL_WIND_MOVE, Point(x, y))
        for entity in CURRENT_ENTITIES:
            if entity.near(self, SPELL_WIND_RADIUS):
                entity.future_position+=move

        print(f'SPELL WIND {int(x)} {int(y)} {self.label}')

    def can_cast_spell_shield(self, entity):
        return self.can_do_action and MY_PLAYER.mana >= SPELL_COST_MANA and \
                entity.shieldLife == 0 and self.near(entity, max_allowed_distance=SPELL_SHIELD_RANGE-1)

    def action_spell_shield(self, entity):
        self.action_spell()
        entity.shieldLife = 16
        print(f'SPELL SHIELD {entity.id}')

    def can_cast_spell_control(self, entity):
        return self.can_do_action and MY_PLAYER.mana >= SPELL_COST_MANA and \
                entity.shieldLife == 0 and self.near(entity, max_allowed_distance=SPELL_CONTROL_RANGE-1)

    def action_spell_control(self, entity, point):
        self.action_spell()
        print(f'SPELL CONTROL {entity.id} {point.x} {point.y}')


class Hero(Entity):
    def __init__(self, *args, **kwargs):
        super(Hero, self).__init__(*args, **kwargs)

        if not hasattr(self, 'protected_mobs'):
            # use this if/else to prevent overwriting old data.
            self.protected_mobs = [] # mob under guard by this hero

class Monster(Entity):
    def __init__(self, *args, **kwargs):
        super(Monster, self).__init__(*args, **kwargs)

    def will_reach_castle(self, base):
        """check if a mob will reach the given base"""
        mob_pos = self.position
        max_rounds = 40
        i=0
        while True:
            i+=1
            if mob_pos.outside_boundaries():
                return False

            if mob_pos.near(base, BASE_AGGRO_DIST):
                return True

            mob_pos+=self.deplacement
            if i >= max_rounds:
                debug("reached max rounds")
                return False


    def castle_attack_viability(self, base, heroes, offending_player, defending_player):
        """determine the viability of an attack on the base, if the heroes decided to go all out on this mob"""
        turns_to_reach_castle = math.ceil((self.distance(base) - BASE_DAMAGED_DIST) / MONSTER_MOVE_SPEED) # note: considers the mob is in a direct collision course with the castle.

        # todo calculate time for each hero to join
        time_for_each_hero_to_join = []
        life_of_mob_reaching_castle = self.health
        for hero in heroes:
            hero_pos = hero.position
            mob_pos = self.position
            turns_to_reach = 0
            # simulate each turn
            mob_deplacement=self.deplacement
            while not hero_pos.near(mob_pos, HERO_DAMAGE_RADIUS): # assume the mob will be under shield : no spells
                turns_to_reach+=1
                mob_pos+=mob_deplacement # TODO we NEED to account for the case where the mob isn't going to the base
                hero_pos=hero_pos.calculate_position_circle_nearest(HERO_MOVE_SPEED, mob_pos)
                if mob_pos.near(base, BASE_AGGRO_DIST):
                    mob_deplacement = mob_pos.calculate_position_circle_nearest(MONSTER_MOVE_SPEED, base) - mob_pos

                if turns_to_reach > turns_to_reach_castle + 1: # mob already hits castle
                    break

            time_for_each_hero_to_join.append(turns_to_reach)
            life_of_mob_reaching_castle-= HERO_DAMAGE*(turns_to_reach_castle - turns_to_reach)

        viability = 2 - turns_to_reach_castle / 10

        if self.shieldLife > turns_to_reach_castle :
            viability+=0.5

        if self.isControlled == 1:
            viability-=2

        if life_of_mob_reaching_castle > 0:
            viability+=1

        if (len(time_for_each_hero_to_join) == 0 or min(time_for_each_hero_to_join) > 3) and offending_player.mana >= 2 * SPELL_COST_MANA: # I can cast wind, follow suit and cast shield
            viability+=1

        if defending_player.mana < 2 * SPELL_COST_MANA: # ennemy can't adequately defend
            viability+=0.5

        if offending_player.mana < 3 * SPELL_COST_MANA and turns_to_reach_castle > 7: # I can't properly defend the mob once he's attacked and he's not near enough the castle
            viability-=0.5

        return viability




class Player:
    def __init__(self, base) -> None:
        self.health = None
        self.mana = None
        self.base = base

        self.base_is_top_left = base.distance_point(MAP_MIN) < base.distance_point(MAP_MAX) # True if the base is the one on the top left corner.

        self.ennemies_near_base = False

    def check_if_ennemies_near_base(self, opp_heroes):
        self.ennemies_near_base = any(hero.near(self.base,VISION_BASE) for hero in opp_heroes)

    def update(self, health, mana):
        self.health = health
        self.mana = mana

    def find_threatening_castle(self, entityList):
        CASTLE_AGGRO_RANGE=5000
        return list(filter(lambda entity: entity.next_position().distance_point(self.base) <= CASTLE_AGGRO_RANGE,
        entityList))

TYPE_MONSTER = 0
TYPE_MY_HERO = 1
TYPE_OP_HERO = 2

# base_x,base_y: The corner of the map representing your base
BASE = Point(*[int(i) for i in input().split()])

MY_PLAYER = Player(BASE)
ENNEMI_PLAYER = Player(MAP_MAX - BASE)

heroes_per_player = int(input())

OFFENSIVE_IDLE_POSITIONS = [
    ENNEMI_PLAYER.base.calculate_position_circle(BASE_AGGRO_DIST + VISION_HERO/2,
     math.pi * ((MY_PLAYER.base_is_top_left) + 1 / 4 + i / 12 )) for i in range(-2, 3)
]

MIDDLE_IDLE_POSITIONS = []
for i in range(-1,2):
    for j in range(-1,2):
        MIDDLE_IDLE_POSITIONS.append(Point(MAP_MAX.x * (2 + i) / 4, MAP_MAX.y* (2 + j) / 4))

DEFENSIVE_IDLE_POSITIONS = [
    MY_PLAYER.base.calculate_position_circle(BASE_AGGRO_DIST * 1.2,
     math.pi * ((not MY_PLAYER.base_is_top_left) + 1 / 4 + i / 12 )) for i in range(-2, 3)
]

IDLE_POSITIONS = {
    "offensive" : OFFENSIVE_IDLE_POSITIONS,
    "defensive" : DEFENSIVE_IDLE_POSITIONS,
    "middle" : MIDDLE_IDLE_POSITIONS
}

debug(IDLE_POSITIONS)

def input_loop():
    MY_PLAYER.update(*[int(j) for j in input().split()])
    ENNEMI_PLAYER.update(*[int(j) for j in input().split()])
    entity_count = int(input())  # Amount of heros and monsters you can see

    monsters = []
    my_heroes = []
    opp_heroes = []
    for i in range(entity_count):
        _id, _type, x, y, shield_life, isControlled, health, vx, vy, near_base, threat_for = [int(j) for j in input().split()]

        _class = Entity
        if _type == TYPE_MONSTER:
            _class = Monster
        else:
            _class = Hero

        entity = _class(
            _id,            # _id: Unique identifier
            _type,          # _type: 0=monster, 1=your hero, 2=opponent hero
            x, y,           # x,y: Position of this entity
            shield_life,    # shield_life: Ignore for this league; Count down until shield spell fades
            isControlled,  # isControlled: Ignore for this league; Equals 1 when this entity is under a control spell
            health,         # health: Remaining health of this monster
            vx, vy,         # vx,vy: Trajectory of this monster
            near_base,      # near_base: 0=monster with no target yet, 1=monster targeting a base
            threat_for      # threat_for: Given this monster's trajectory, is it a threat to 1=your base, 2=your opponent's base, 0=neither
        )

        if _type == TYPE_MONSTER:
            monsters.append(entity)
        elif _type == TYPE_MY_HERO:
            my_heroes.append(entity)
        elif _type == TYPE_OP_HERO:
            opp_heroes.append(entity)

    my_heroes[0].hero_index = 0
    my_heroes[1].hero_index = 1
    my_heroes[2].hero_index = 2

    return (monsters, my_heroes, opp_heroes)

def defensive_hero_action(hero, monsters, my_heroes, opp_heroes, global_inputs):
    hero.label = f"def"
    monsters_threatening_my_castle = global_inputs['monsters_threatening_my_castle']
    monsters_future_threaten_my_castle = global_inputs['monsters_future_threaten_my_castle']
    max_allowed_distance = 1.5 * BASE_AGGRO_DIST
    # defensive heroes
    if len(monsters_threatening_my_castle) > 0:
        # if a monster is threatening our castle, aggro it

        # if i've already been controlled and an ennemy hero is in the castle range > cast shield on myself
        if hero.has_already_been_controlled and MY_PLAYER.check_if_ennemies_near_base(opp_heroes) and hero.can_cast_spell_shield(hero):
            hero.action_spell_shield(hero)
            return

        if hero.can_cast_spell_wind(monsters_threatening_my_castle) and not global_inputs['defensive_wind_spell_used']:
            monsters_affected = hero.find_affected_spell_wind(monsters_threatening_my_castle)

            if any(monster.is_threat_to_castle(my_heroes, opp_heroes) for monster in monsters_affected):
                # if i'm already near the monster
                # and he's a real threat to the castle (
                #   will reach it before I can kill it ||
                #   there's an ennemy player besides)
                # and i can cast wind
                outside_point_circle = 2 * hero.position - MY_PLAYER.base
                hero.action_spell_wind(outside_point_circle.x, outside_point_circle.y)
                global_inputs['defensive_wind_spell_used'] = True

        if hero.can_do_action:
            # monsters are threatening the castle but I can't / won't cast wind
            target = hero.findNearestPoint(monsters_threatening_my_castle, MY_PLAYER.base)
            point_to_attack = hero.findBestAttackPoint(monsters, priority_entity = target)
            if point_to_attack is not None:
                hero.action_move(point_to_attack[0].x, point_to_attack[0].y)

    else:
        # else find a monster to hit, while staying near the castle (< 1.5 times the max distance) - privilege those that will aggro the castle
        if len(monsters_future_threaten_my_castle) != 0:
            nearest_danger_mob = hero.findNearestMe(monsters_future_threaten_my_castle, max_allowed_distance = max_allowed_distance, max_allowed_distance_point = MY_PLAYER.base)
            point_to_attack = hero.findBestAttackPoint(monsters, priority_entity = nearest_danger_mob)
            if point_to_attack is None:
                target = nearest_danger_mob
            else:
                hero.action_move(point_to_attack[0].x, point_to_attack[0].y)
        else:
            monsters_near = [mob for mob in monsters if mob.near(MY_PLAYER.base, max_allowed_distance)]
            point_to_attack = hero.findBestAttackPoint(monsters_near, deplacement_range=HERO_MOVE_SPEED)
            if point_to_attack is None:
                target = hero.findNearestMe(monsters_near, max_allowed_distance = max_allowed_distance, max_allowed_distance_point = MY_PLAYER.base)
            else:
                hero.action_move(point_to_attack[0].x, point_to_attack[0].y)


    if hero.can_do_action:
        if target is None:
            # defaults to defensive position
            hero.action_move_to_idle()
        else:
            hero.action_move_to_entity(target)


def offensive_hero_action(hero, monsters, my_heroes, opp_heroes):
    # offensive hero
    hero.label = "off"
    max_allowed_distance_base = VISION_BASE * 2
    # if not < 2 times the max distance from the ennemy castle, move towards idle position
    if not hero.position.near(ENNEMI_PLAYER.base, max_allowed_distance_base):
        hero.action_move_to_idle()
    else:
        # else find mob that is only near my vision
        near_mobs = hero.findNearMe(monsters, max_allowed_distance = max_allowed_distance_base, max_allowed_distance_point=ENNEMI_PLAYER.base)
        # TODO : ignore mobs that are already on the attack path but outside the castle
        # filter to remove those actually attacking their castle
        near_mobs = list(filter( lambda mob: mob.near_base == 0 and mob.position.near(ENNEMI_PLAYER.base, max_allowed_distance_base), near_mobs))
        if len(near_mobs) > 0:
            # find mobs near the ennemy castle that do not have aggro yet
            mobs_near_ennemy_castle = list(filter(
                lambda mob: mob.position.near(ENNEMI_PLAYER.base, BASE_AGGRO_DIST + 3 * SPELL_WIND_MOVE),
                near_mobs))

            if len(mobs_near_ennemy_castle) > 0 and any(mob.health > 6 * HERO_DAMAGE and not mob.threat_for == 2 for mob in mobs_near_ennemy_castle):
                if hero.can_cast_spell_wind(mobs_near_ennemy_castle):
                    # if mob found and within wind spell toward castle
                    hero.action_spell_wind(ENNEMI_PLAYER.base.x, ENNEMI_PLAYER.base.y)
                    # TODO: add follow through (continue to push mob towards ennemy lines)
                else:
                    # else get into position
                    # hero.findNearestMe(near_mobs, max_allowed_distance = 2 * BASE_AGGRO_DIST, max_allowed_distance_point = ENNEMI_PLAYER.base)
                    # TODO move towards the actual closest mob
                    hero.action_move_to_entity( mobs_near_ennemy_castle[0] )
            else:
                # no mobs currently pushable : attack nearest mob
                hero.action_move_to_entity( near_mobs[0] )
        else:
            # get into IDLE position
            hero.action_move_to_idle()


def offensive_hero_action_v2(hero, monsters, my_heroes, opp_heroes):
    # offensive hero
    hero.label = "off"
    max_allowed_distance_base = VISION_BASE * 2
    monsters_near_ennemy_castle = [mob for mob in monsters if mob.near(ENNEMI_PLAYER.base, max_allowed_distance_base)]
    monsters_threatening_ennemy_castle = [mob for mob in monsters_near_ennemy_castle if mob.threat_for == 2]

    # if not < 2 times the max distance from the ennemy castle, move towards idle position
    if not hero.position.near(ENNEMI_PLAYER.base, max_allowed_distance_base):
        hero.action_move_to_idle()
    else:
        # if i've already been controlled, check if i need to recast my shield
        if hero.has_already_been_controlled and hero.shieldLife == 0 and hero.near(opp_heroes, SPELL_CONTROL_RANGE):
            if MY_PLAYER.mana > 5 * SPELL_COST_MANA:
                hero.action_spell_shield(hero)
                return

        # check if any protected mob is still alive
        for mob in hero.protected_mobs:
            if mob.last_seen > TURN_ID - 3:# mob not seen for more than 3 turns - consider it dead
                hero.protected_mobs.remove(mob)
                continue

            if not mob.will_reach_castle(ENNEMI_PLAYER.base): # mob will not reach castle, remove it from the priviledge list
                hero.protected_mobs.remove(mob)
                continue

        if len(hero.protected_mobs) == 0 and len(monsters_threatening_ennemy_castle) > 0:
            # find a monster to protect
                attack_viabilities = [
                    mob.castle_attack_viability(ENNEMI_PLAYER.base, opp_heroes, MY_PLAYER, ENNEMI_PLAYER) for mob in monsters_threatening_ennemy_castle
                ]

                best_viability = monsters_threatening_ennemy_castle[attack_viabilities.index(max(attack_viabilities))]
                hero.protected_mobs.append(best_viability)
        debug("protected_mobs : ", hero.protected_mobs)
        if len(hero.protected_mobs) > 0:
            protected_mob = hero.protected_mobs[0]
            mob_position = protected_mob.position if protected_mob.last_seen == TURN_ID \
                else protected_mob.future_position + (TURN_ID - protected_mob.last_seen - 1) * protected_mob.deplacement
            debug("protect mobd")
            if protected_mob.shieldLife == 0 and \
                    hero.can_cast_spell_shield(protected_mob) and \
                    ENNEMI_PLAYER.mana > SPELL_COST_MANA and \
                    protected_mob.near(opp_heroes, SPELL_CONTROL_RANGE): # mob could be controlled
                debug("cast shield")
                # cast a shield over the mob if he risks being controlled
                hero.action_spell_shield(protected_mob)
            else:
                # if within range and unshielded, cast spell wind to make it go faster
                if hero.can_cast_spell_wind([protected_mob]):
                    debug("cast wind")
                    hero.action_spell_wind(ENNEMI_PLAYER.base.x, ENNEMI_PLAYER.base.y)
                elif protected_mob.shieldLife > 0 \
                     and protected_mob.shieldLife < 16 \
                     and hero.can_cast_spell_wind(opp_heroes): # mob is shielded, search for opponents to throw outside their ring
                    hero.action_spell_wind(MY_PLAYER.base.x, MY_PLAYER.base.y)
                else: # run to catch up with mob
                    non_aggro_point = mob_position.calculate_position_circle_nearest(HERO_DAMAGE_RADIUS + 1, hero.position)
                    hero.action_move(non_aggro_point.x, non_aggro_point.y)

        else: # find a mob either to aggro or go to idle position
            # find a mob to protect
            if len(monsters_near_ennemy_castle) > 0:
                # find nearest mob
                point_to_attack = hero.findBestAttackPoint(monsters)
                nearestMob = hero.findNearestMe(monsters_near_ennemy_castle, max_allowed_distance=SPELL_CONTROL_RANGE)
                if nearestMob is not None and MY_PLAYER.mana > 5 * SPELL_COST_MANA:
                    # use control instead of wind to reduce the amount of mana the defenders can get for killing the mob
                    hero.action_spell_control(nearestMob, ENNEMI_PLAYER.base)
                elif point_to_attack is not None:
                    hero.action_move(point_to_attack[0].x, point_to_attack[0].y)
                else:
                    hero.action_move_to_idle()

            else:
                # go to IDLE position
                hero.action_move_to_idle()


def middle_hero_action(hero, monsters, my_heroes, opp_heroes):
    # hero that roam in the middle to gain points
    # he shouldn't go too far from our side in order to be able to fall back and defend.

    hero.label = "middle"

    # if monsters can be currently attacked : do it
    monsters_near = [mob for mob in monsters if hero.near(mob, HERO_MOVE_SPEED + HERO_DAMAGE_RADIUS)]
    target_move = None
    if len(monsters_near) > 0:
        point_to_attack = hero.findBestAttackPoint(monsters)
        if point_to_attack is None:
            target = hero.findNearestMe(monsters_near, max_allowed_distance = 2 * BASE_AGGRO_DIST, max_allowed_distance_point = MY_PLAYER.base)
            if target is not None:
                target_move = target.position
        else:
            target_move = point_to_attack[0]
    else:
        target = hero.findNearestMe(monsters)
        if target is not None:
            hero.action_move_to_entity(target)
            return

    if target_move is not None:
        hero.action_move(target_move.x, target_move.y)
    else:
        hero.action_move_to_idle()
    # else
    #   if on idle_position, order a change of idle position
    #   go to idle_position


def defensive_hero_counter_attack(hero, monsters, my_heroes, opp_heroes, global_inputs):
    # a defensive hero whose goal is to counter the opponent offensive heroes

    # if an ennemy hero is in my base
    # AND there's a mob in my base
    # AND the ennemy hero can cast something on the mob OR on one of my heroes
    # AND I've alread lost a life / the mob has a lot of life / lots of mob and is really near the castle
    # THEN go to control the attack hero so that it becomes one of my defensors while running away from the circle.

    ennemy_heroes_in_base = [hero for hero in opp_heroes if hero.near(MY_PLAYER.base, BASE_AGGRO_DIST)]
    mobs_in_base = [mob for mob in monsters if mob.near(MY_PLAYER.base, BASE_AGGRO_DIST)]
    if len(ennemy_heroes_in_base) > 0 and \
       len(mobs_in_base) > 0:
        # if there's both ennemy and mobs in base
        biggest_threat = max(ennemy_heroes_in_base, key=lambda hero: ( 1 - hero.distance(MY_PLAYER.base) / BASE_AGGRO_DIST ) - hero.isControlled - hero.shieldLife)
        if not biggest_threat.isControlled and biggest_threat.shieldLife == 0:
            # if the ennemy is not controlled and doesn't have a shield
            nearest_mob_from_him = biggest_threat.findNearestMe(mobs_in_base, max_allowed_distance=SPELL_WIND_RADIUS)
            nearest_hero_from_him = biggest_threat.findNearestMe(my_heroes, max_allowed_distance=SPELL_CONTROL_RANGE)
            if (nearest_mob_from_him is not None and nearest_mob_from_him.shieldLife == 0 and nearest_mob_from_him.near(MY_PLAYER.base, SPELL_WIND_MOVE + 2 * BASE_DAMAGED_DIST)) or \
                (nearest_hero_from_him is not None and nearest_hero_from_him.shieldLife == 0):
                # if he's near a mob and able to make it fly or one of my heroes
                # then control him
                if hero.can_cast_spell_control(biggest_threat) and MY_PLAYER.mana > 5 * SPELL_COST_MANA:
                    hero.action_spell_control(biggest_threat, ENNEMI_PLAYER.base)
                elif MY_PLAYER.mana > 5 * SPELL_COST_MANA:
                    hero.action_move_to_entity(biggest_threat)

    # end of offensive def - go to defensives actions if not action has been taken
    if hero.can_do_action:
        defensive_hero_action(hero, monsters, my_heroes, opp_heroes, global_inputs)



# game loop
TURN_ID=0
CURRENT_ENTITIES = []
while True:
    TURN_ID+=1
    monsters, my_heroes, opp_heroes = input_loop()
    CURRENT_ENTITIES = [*monsters, *my_heroes, *opp_heroes]

    MY_PLAYER.check_if_ennemies_near_base(opp_heroes)

    my_heroes[0].hero_type = "defensive"
    my_heroes[1].hero_type = "middle"
    my_heroes[2].hero_type = "offensive"
    if MY_PLAYER.ennemies_near_base:
        my_heroes[1].hero_type = "defensive_counter"
    if TURN_ID < 30:
        my_heroes[2].hero_type = "middle"

    global_inputs = {}

    # monsters directly threatening my castle
    global_inputs['monsters_threatening_my_castle'] = list(filter(lambda monster: monster.near_base and monster.threat_for == 1, monsters))
    # monsters that will threaten my castle
    global_inputs['monsters_future_threaten_my_castle'] = list(filter(lambda monster: not monster.near_base and monster.threat_for == 1, monsters))

    # limit defensive wind spell to 1 for now - until we can better see where the spells lands
    global_inputs['defensive_wind_spell_used'] = False

    for i in range(heroes_per_player):
        hero = my_heroes[i]
        if hero.hero_type == "middle":
            middle_hero_action(hero, monsters, my_heroes, opp_heroes)
        elif hero.hero_type == "offensive":
            offensive_hero_action_v2(hero, monsters, my_heroes, opp_heroes)
        elif hero.hero_type == "defensive_counter":
            hero.hero_type = "defensive" # needed for other things
            defensive_hero_counter_attack(hero, monsters, my_heroes, opp_heroes, global_inputs)
        else: # fallback to defensive by default
            defensive_hero_action(hero, monsters, my_heroes, opp_heroes, global_inputs)
