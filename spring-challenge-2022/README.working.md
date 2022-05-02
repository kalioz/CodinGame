# Challenge

URL : https://www.codingame.com/ide/challenge/spring-challenge-2022

# mana
- all heroes should attack
- more monsters hit, more mana
- spells cost 10 mana
- it's better to farm mana outside base (for global score)

# todo
- [x] target best place to hit most mobs
- [ ] make offensif hero follow ennemies heroes inside base
- [x] use of shield
- [x] reduce amout of mobs sent to ennemy base to reduce his mana - better quality, less quantity
- modify strategy in game :
    - at start : 2 roamers (finds mobs to get mana), 1 defender (able to quickly protect base - go inside base if an ennemy is spotted
                coming )
    - after ammassing some mana (like 100 / 200) - switch
        - if an ennemy is offensive, 2 defender one attacker
            - defenders can cast WIND and CONTROL
            - ATTACKER can cast WIND and SHIELD
        - if an ennemy is defensive (3 def), 2 attackers one defender (that will basically only cast WIND near base)
            - defender can cast WIND
            - attackers can cast WIND + SHIELD as a combo (shield activates after the turn) + CONTROL

- [ ] affect a defender to follow attacker's hero, by staying as close as possible to him in order to be able to launch counterspells

## offensive playthrough
# todo limit mana use (no use if mana < 3 SPELLS and castle is in dire danger)
- if hero is not near ennemy base, go to it
- else if hero finds a mob threatening the ennemy's base (life > distance) and we have enough mana for an attack (at least 3 spells, 1 shield and 2 opposite wind):
  - if the mob isn't shielded, shield the mob
  - if there are ennemies heroes that can be winded, do it (check if it's needed for the mob to reach base)
  - if there aren't, follow the mob without hitting it
- else if in_ennemy_base and can_see_opponent_hero:
  - follow opponent_hero
- else if find a mob not threatening castle
  - if mob can be pushed into castle and is worth it (life > distance), do it
  - else just attack the mob keeping max distance
