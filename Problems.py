"""Content bank.

Every item is a dict:
    prompt      - what the player sees
    answers     - list of accepted answers (lowercased, keyword match for text)
    difficulty  - 1 easy, 2 medium, 3 hard
    explain     - shown after the item, win or lose
    kind        - 'exact' (string/number match) or 'keyword' (any answer appears)
    options     - optional list, turns the item into multiple choice
"""

SEQUENCES = [
    {"prompt": "2, 4, 8, 16, ?", "answers": ["32"], "difficulty": 1,
     "explain": "Each term doubles."},
    {"prompt": "1, 1, 2, 3, 5, 8, ?", "answers": ["13"], "difficulty": 1,
     "explain": "Fibonacci: each term is the sum of the two before it."},
    {"prompt": "3, 6, 11, 18, 27, ?", "answers": ["38"], "difficulty": 2,
     "explain": "Gaps grow by 2: +3, +5, +7, +9, +11."},
    {"prompt": "2, 3, 5, 7, 11, 13, ?", "answers": ["17"], "difficulty": 1,
     "explain": "Consecutive prime numbers."},
    {"prompt": "81, 64, 49, 36, ?", "answers": ["25"], "difficulty": 2,
     "explain": "Squares counting down: 9,8,7,6,5."},
    {"prompt": "1, 4, 9, 61, 52, ?", "answers": ["63"], "difficulty": 3,
     "explain": "Squares 1,4,9,16,25,36 with the digits reversed."},
    {"prompt": "7, 14, 12, 24, 22, 44, ?", "answers": ["42"], "difficulty": 3,
     "explain": "Alternately double, then subtract 2."},
    {"prompt": "B, D, G, K, ?", "answers": ["p"], "difficulty": 3,
     "explain": "Letter gaps grow: +2, +3, +4, +5 -> B D G K P."},
]

LOGIC = [
    {"prompt": "All roses fade. Some fading things are red. Must some roses be red?",
     "options": ["Yes", "No", "Cannot be determined"], "answers": ["no", "b", "2"],
     "difficulty": 2,
     "explain": "The red fading things need not be roses. Overlap is not implication."},
    {"prompt": "A bat and a ball cost 110 rupees together. The bat costs 100 more "
               "than the ball. What does the ball cost (in rupees)?",
     "answers": ["5"], "difficulty": 2,
     "explain": "Ball 5, bat 105. The fast answer 10 makes the gap only 90."},
    {"prompt": "If it rains, the match is cancelled. The match was cancelled. "
               "Did it rain?",
     "options": ["Yes", "No", "Cannot be determined"], "answers": ["cannot be determined", "c", "3"],
     "difficulty": 1,
     "explain": "Affirming the consequent. Cancellation has other possible causes."},
    {"prompt": "5 machines make 5 widgets in 5 minutes. How many minutes for "
               "100 machines to make 100 widgets?",
     "answers": ["5"], "difficulty": 2,
     "explain": "One machine takes 5 minutes per widget, and they work in parallel."},
    {"prompt": "A lily patch doubles daily and covers the lake on day 48. "
               "On which day is it half covered?",
     "answers": ["47"], "difficulty": 2,
     "explain": "Work backwards: one doubling before full is half."},
    {"prompt": "Every card has a letter on one side and a number on the other. "
               "Rule: if a card shows A, its other side is 3. Cards on the table: "
               "A, B, 3, 4. Which two must you turn to test the rule?",
     "options": ["A and 3", "A and 4", "B and 3", "A and B"],
     "answers": ["a and 4", "b", "2"], "difficulty": 3,
     "explain": "Wason selection task: test A, and test 4 for a hidden A. "
                "Turning 3 can never falsify the rule."},
    {"prompt": "Three switches outside a sealed room control one bulb inside. "
               "You may enter once. Minimum number of switch flips needed?",
     "options": ["1", "2", "3"], "answers": ["2", "b"], "difficulty": 3,
     "explain": "Turn one on for a while then off, turn a second on, enter: "
                "lit, warm-and-dark, cold-and-dark identify all three."},
]

MEMORY = [
    {"payload": "7 2 9 4", "difficulty": 1, "explain": "Four digits, forward recall."},
    {"payload": "4 8 1 6 3", "difficulty": 1, "explain": "Five digits, forward recall."},
    {"payload": "9 3 7 1 5 2", "difficulty": 2, "explain": "Six digits. Chunk them in pairs."},
    {"payload": "2 6 4 9 8 3 7", "difficulty": 2, "explain": "Seven digits - around the classic span limit."},
    {"payload": "5 1 8 2 7 4 9 3", "difficulty": 3, "explain": "Eight digits. Chunking is now mandatory."},
    {"payload": "KITE OVEN RAIL MUG", "difficulty": 2, "explain": "Four words. A quick image linking them helps."},
    {"payload": "LAMP TIGER BRICK VIOLET NEST", "difficulty": 3, "explain": "Five words - build one absurd scene."},
]

# Interference items: the answer fights the obvious reading.
FOCUS = [
    {"prompt": "How many LETTERS are in the word below?\n\n        SEVEN",
     "answers": ["5"], "difficulty": 1,
     "explain": "SEVEN has 5 letters. The number named is a distractor."},
    {"prompt": "How many LETTERS are in the word below?\n\n        THREE",
     "answers": ["5"], "difficulty": 1, "explain": "THREE has 5 letters."},
    {"prompt": "Count the words, not the numbers:\n\n        NINE NINE NINE",
     "answers": ["3"], "difficulty": 1, "explain": "Three words."},
    {"prompt": "How many letters in total?\n\n        ONE TWO SIX",
     "answers": ["9"], "difficulty": 2, "explain": "3 + 3 + 3 = 9 letters."},
    {"prompt": "Which is larger: the NUMBER OF LETTERS in TWELVE, or the "
               "NUMBER OF LETTERS in FOUR? Answer with the word.",
     "answers": ["twelve"], "difficulty": 2, "explain": "TWELVE has 6 letters, FOUR has 4."},
    {"prompt": "Read only the capitalised letters, ignore the rest:\n\n"
               "        aBcDeF gHi -> how many capitals?",
     "answers": ["4"], "difficulty": 2, "explain": "B, D, F, H = 4."},
    {"prompt": "In the string below, how many times does '3' appear?\n\n"
               "        1 3 8 3 3 9 3 2 5 3",
     "answers": ["5"], "difficulty": 3, "explain": "Positions 2, 4, 5, 7, 10 - five threes."},
]

LATERAL = [
    {"prompt": "A man pushes his car to a hotel and immediately loses all his money. "
               "What is going on? (one word)",
     "answers": ["monopoly", "board game", "game"], "kind": "keyword", "difficulty": 2,
     "explain": "He is playing Monopoly. The frame, not the facts, was the puzzle."},
    {"prompt": "What can travel around the world while staying in one corner?",
     "answers": ["stamp", "postage"], "kind": "keyword", "difficulty": 2,
     "explain": "A postage stamp."},
    {"prompt": "Two people are born the same minute to the same mother, same day, "
               "but are not twins. How? (one word)",
     "answers": ["triplet", "triplets", "quadruplet", "quadruplets"], "kind": "keyword",
     "difficulty": 2, "explain": "They are part of triplets or more."},
    {"prompt": "The more of it you take, the more you leave behind. What is it?",
     "answers": ["footstep", "footsteps", "steps", "step"], "kind": "keyword",
     "difficulty": 1, "explain": "Footsteps."},
    {"prompt": "A woman shoots her husband, holds him under water for five minutes, "
               "then they enjoy dinner together. How? (one word)",
     "answers": ["photograph", "photo", "photographer", "camera", "film"], "kind": "keyword",
     "difficulty": 3, "explain": "She photographed him and developed the print."},
    {"prompt": "Which word becomes shorter when you add two letters to it?",
     "answers": ["short"], "kind": "keyword", "difficulty": 2, "explain": "short -> shorter."},
]

NUMERIC = [
    {"prompt": "17 + 28 - 9 = ?", "answers": ["36"], "difficulty": 1, "explain": "45 - 9 = 36."},
    {"prompt": "14 x 6 = ?", "answers": ["84"], "difficulty": 1, "explain": "14 x 6 = 84."},
    {"prompt": "A shirt is 40% off, then 10% off the new price. "
               "Total discount off the original (percent)?",
     "answers": ["46"], "difficulty": 3, "explain": "0.6 x 0.9 = 0.54, so 46% off - not 50%."},
    {"prompt": "(24 / 4) x 7 - 13 = ?", "answers": ["29"], "difficulty": 2, "explain": "6 x 7 = 42, 42 - 13 = 29."},
    {"prompt": "A train covers 180 km in 2.5 hours. Speed in km/h?",
     "answers": ["72"], "difficulty": 2, "explain": "180 / 2.5 = 72."},
    {"prompt": "What is 15% of 260?", "answers": ["39"], "difficulty": 2,
     "explain": "10% = 26, 5% = 13, total 39."},
    {"prompt": "Sum of all numbers from 1 to 20?", "answers": ["210"], "difficulty": 3,
     "explain": "20 x 21 / 2 = 210."},
]

DISTRACTORS = [
    "[ another player just passed your score ]",
    "[ ping ] someone is waiting on your answer...",
    "[ the clock is halved on this round ]",
    "[ 3 players are watching this item ]",
    "[ your streak is on the line ]",
    "[ this item is worth double - do not miss ]",
]
