# Spring Challenge 2021

link to the challenge: https://www.codingame.com/contests/spring-challenge-2021

The goal of this challenge was to grow a forest and complete the most trees, while competing with an opponent on cells for their richness.

This document aims to present how I tried to solve this problem and create the best ~~murder~~planting-bot; Some (or many !) of the ways I went into this may be weird, illogical or simply wrong, it isn't meant to explain how to do it best, just why i did it like that. :D  

## How I Dit It

### Architecture : OOP is Love, OOP is Life

I used three classes to hold the entire game : 
- Forest, contains all trees, cells, and basically all "globals"
- Tree
- Cell

I used the "Forest" class as a way to ease development : functions didn't need to have _all_ variables passed as variables, and globals could be attached to an easily modified object.<br>
This is not best practice for real use-case, but it reduce the time to develop basic functions while keeping the code clean.

### Logical Functionnality

The challenge required to have a lot of trees completed, which required sun points (SP) to grow and complete. I tried to make my strategy revolve around generating SP and trying to prevent the other player from generating SP.

#### Functions

My seeds had bonus points when their placement meant they would cast a shadow on the opponent's tree way more than on mine, when they would not be affected by any tree or when they had access to high richness cells. My strategy was badly configured, as I did not succeed in battling the gold bot in sun points generation; It was too agressive (too much importance on preventing the opponent from gaining SP), which reduced my gains in the long term (win in score until round {end}-6, then get wrecked by the opponent's advantage on SP).

My growth function tried to assess how much the new shadow would impact the existing trees, to prevent growing a tree that would shadow mine in the next turns. It worked pretty well, but at times would prevent trees from growing full size due to a bad placement of thoses trees.

My "complete" function tried to complete trees only if we were lacking in score or if the tree's shade would have a major impact on my other trees. Sized-3 trees cost a lot of SP to produce and generate only 3 SP, I couldn't just cut them at the first hint of a problem : Trees that would produce SP next round were nearly never completed to have those sweet points.

All those functions worked with a scoring system, meaning that each potential candidate was assigned a score, and the highest score was chosen for the action.<br>
My algorithm took into account up to 6 days in the future to calculate potential; However one of its deficiency was that it did not take into account any of the action it should take in the N+1 turn, which _may_ have improved its efficiency, with a significant complexity cost.

#### Function order

I first tried to use the "complete" > "grow" > "seed" order, as completed trees increase the cost of the grow function, and size-0 trees increase the cost of the seed function.<br>
It worked pretty well, but I found that the "seed if none exists" > "complete" > "grow" > "seed" worked better, as we would have priority on the best cells compared to the opponent.

What i didn't do and maybe should have done was calculate all the actions that would be taken for a given turn and then sort them by importance; this would have allowed for a better algorithm as risky or punishing upgrades could be done last, while doing the safest options early.

## Results

This algorithm finished 756th on 6867 players, in gold league. I had my up and downs in the challenge (top 80 in the first days), but it was pretty fun to try and find the ways to improve productivity and what strategies were worth exploring.

In the future, I'll certainly use the [brutaltester](https://github.com/dreignier/cg-brutaltester) tool, which allow finetuning constant modifiers way faster than using the codingame platform (nearly all of my points calculators use hand-tuned modifiers).
