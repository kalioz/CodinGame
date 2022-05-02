# How to start a new game

This is a guide as to how the code for a new game should be created.
This is a guide for developping with Python.

## Version control

I highly encourage using some kind of version control to develop your code, like git. while the code needs to be copied/paste to the CodinGame, it is always useful to commit your code when something is working so that you have a way to go back if anything goes wrong in your future developments.

## First "working" code

When you start a challenge, read the challenge in full before starting developping. There usually is a git repo given that contains the barebones of a working code in all languages, that will be more advanced than the default one given in the editor. It is highly useful for the inputs.

## Your code

Here are a few recommendations I have for the code while you're in the heat of the challenge :

Your code should use the following structure :

```
CONSTANT_X = "value"

function myFunction

class Person

function init_input # all "init" inputs should be parsed here
function loop_input # all "loop" inputs should be parsed here

CONSTANT_DEPENDING_FROM_CLASS = Person("x")

x, y, z = init_input
while True:
    xx, yy, zz = loop_input
    if xx == yy;
      myFunction(xx, yy, zz)
    else
      myFunction2(xx, yy, zz)
```

- use global constants for every value given in the game (e.g. HERO_SPEED, HERO_ATTACK_DAMAGE) - this will simplify your comprehension of your code when using those values
- use functions for parsing the inputs, and for acting on them - you can keep some logic on the main loop, but keep it simple !
- use classes to store information related to the input loop
  - if one of your object's classes has an id, use mechanisms to be able to track the same object across different turns instead of simply recreating it each turn
  - use class inheritance if it is possible - this will allow you to better organize your code.
- avoid if possible using undefined constants to affect your action - finding out which constant works best manually is just not worth it (I'm talking about `if player.distance > 0.8 * MAX_DISTANCE_ALLOWED` - the 0.8 doesn't refer to any logic value, and is just a "magic" number.)
  - if you want to use magic numbers, you'll need to test them in mass before submitting your code - know this IS possible ! cf [brutaltester](https://github.com/dreignier/cg-brutaltester), I didn't test it yet as I find that logic code is working better than magic numbers.
