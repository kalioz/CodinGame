# Spring Challenge 2022

link to the challenge : https://www.codingame.com/contests/spring-challenge-2022

The goal of this challenge is to control 3 heroes and to protect your base against monsters. the monsters spawn randomly, the players gain mana by having their heroes attack the monster, and the mana allow the heroes to push / control / protect themselves or other monsters / heroes.

## How I did it
### Architecture

Like always, I want for an OOP approach. For this game, I learned about some concepts in Python :
- the class function `__new__`: surcharging this function allowed me to avoid recreating already existing objects. in hindsight the code I created would have had issues with memory in the long term, but that did not impact any of my plays.
- the `filter` function - although I learned after that list comprehension is faster anyways, ho well :)

I created 4 classes for this game :
- Point : a class containing (x,y) coordinates, and multiples functions associated to it
- Entity : a class containing all informations related to the entities. in hindsight, it should have herited from Point as I recreated all functions anyway
- Hero(Entity) : a class containing all informations & functions related to the hero
- Monster(Entity) : a class containing all informations & functions related to the Monster

the Hero and Monster class are under-utilized as I only created them in the final steps of the game, when the Entity class became too bloated to be comprehensible.

### Logical functionality

For the challenge I quickly found out that the defense was more important than the offense, and so affected two heroes to it : one hero was defender 100%, while the other one was defender only if an ennemy hero was coming near our base; else he was just farming wild mana.
I think this allowed me to quickly rise ranks as this allowed me to have a functional defense against user who used or didn't use any attack strategies.
Defenders mainly used the push spell to repell ennemies from the base, by calculating if the ennemies would be killed before they became dangerous or not. that is why a single hero could defend the base if no attacker was nearby.

The last hero was sent to attack, meaning he pushed monsters towards the ennemy base and tried to divert the defenders from the mob. not gonna lie, he was not functionning half as good as I wanted him to be, but I didn't have the time to make him better :'(
The attacking hero was supposed to use the control spell to divert defenders and wind spell to accelerate the deplacement of the mobs - however, he never seemed to follow through an attack (meaning he pushed the mobs towards the ennemies, and then... just kinda went for another mob) - which greatly reduced his efficacity, while being a big mana consumption source.

## Results

I finished in gold league, ranked 730th / 7 705. As always, the challenge was fun to solve and find ways to outsmart opponents, but I find it difficult to develop without having any access to debugging tools - you need to produce working code without tests if you don't want to lose time, and avoid using WHILE loops as if they are badly defined you will need to parse all your program to find out why it is not outputting text in the alloted time.

I had ideas to produce a better bot, but not the time to implement it - all in all I'm glad I did a better score than last year with less time to develop my solution.
