"""
ClearPath Offline Explanation Bank Builder and Validator.

Compiles and validates the multimodal offline explanation bank (data/explanations.json)
for 100% offline uptime and instant fallback.

NOTE: Per architecture specifications, this file MUST NOT import the `groq` package.
Only backend/app/llm/gateway.py may import `groq`.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DATA_DIR = ROOT_DIR / "backend" / "data"
ROOT_DATA_DIR = ROOT_DIR / "data"

# Comprehensive Curated Offline Explanation Bank
OFFLINE_BANK_DATA: Dict[str, Any] = {
    "c1_fraction_basics": {
        "visual": {
            "level_1": {
                "explanation": "Picture a circle cut into 4 equal slices like a personal pizza. If 1 slice is colored orange and 3 slices are white, the orange portion is 1/4. The bottom number 4 tells us how many total equal slices make the complete pie, and the top number 1 counts the orange slice.",
                "check_question": "In the fraction 1/4, what does the bottom number 4 tell us?",
                "visual_description": "A circle divided into 4 equal quarters, with 1 quarter colored bright orange and 3 quarters plain white."
            },
            "level_2": {
                "explanation": "Think of a rectangular chocolate bar split cleanly into 5 equal square blocks. Eating 3 blocks means you ate 3/5 of the bar. The denominator 5 defines the size of the whole bar, while the numerator 3 counts the blocks consumed.",
                "check_question": "If you eat 4 blocks out of 5, what fraction of the bar have you eaten?",
                "visual_description": "A horizontal rectangle divided into 5 equal blocks in a row. 3 blocks are filled with chocolate brown, 2 blocks are unshaded."
            },
            "level_3": {
                "explanation": "On a number line from 0 to 1, mark 8 equal tick marks. Each interval has length 1/8. Landing on 5/8 means counting 5 iterations of the unit fraction 1/8 starting from 0. Fractions are numbers that measure precise positions between whole numbers.",
                "check_question": "How many unit fractions of 1/8 must you combine to reach 5/8?",
                "visual_description": "A horizontal number line from 0 to 1 with 8 evenly spaced ticks. An arrow jumps from 0 across 5 segments to point directly at 5/8."
            }
        },
        "analogy": {
            "level_1": {
                "explanation": "Imagine an egg carton designed to hold 6 eggs. If 2 eggs are sitting in the carton, you have 2 out of 6 eggs (2/6). The carton's total capacity is the bottom number, and the eggs present are the top number.",
                "check_question": "What does the bottom number tell you in the egg carton comparison?",
                "visual_description": "A 6-slot egg carton with 2 eggs resting in the first two slots and 4 empty slots."
            },
            "level_2": {
                "explanation": "Think of your phone battery meter divided into 4 equal charging bars. If 3 bars are glowing green, your phone is at 3/4 battery. The 4 represents a 100% full charge, and the 3 represents your remaining power.",
                "check_question": "Why is the total capacity of 4 bars placed on the bottom?",
                "visual_description": "A mobile battery icon partitioned into 4 vertical segments, with the first 3 segments glowing neon green."
            },
            "level_3": {
                "explanation": "Think of a sports squad where 7 out of 10 players are on the field. The full squad roster of 10 is the foundation whole, while the 7 active players form the subset being evaluated.",
                "check_question": "If 1 more player joins the field from the bench, what is the new active fraction?",
                "visual_description": "A team roster board showing 10 numbered slots, with 7 highlighted as 'Active On Field' and 3 as 'Bench'."
            }
        },
        "worked": {
            "level_1": {
                "explanation": "Step 1: Count all the equal parts in the whole shape (that's your bottom number, the denominator).\\nStep 2: Count how many parts are shaded or selected (that's your top number, the numerator).\\nStep 3: Write numerator over denominator: parts counted / total parts.",
                "check_question": "Where do you write the total number of parts?",
                "visual_description": "A two-tier box diagram: Top box labeled 'Parts You Count (Numerator)' over Bottom box labeled 'Total Equal Parts (Denominator)'."
            },
            "level_2": {
                "explanation": "Step 1: Confirm all pieces are identical in size.\\nStep 2: Count total pieces = 6 (Denominator = 6).\\nStep 3: Count colored pieces = 4 (Numerator = 4).\\nStep 4: Combine into 4/6, read as 'four-sixths'.",
                "check_question": "In the fraction 4/6, what is the numerator?",
                "visual_description": "A diagram pointing an arrow to 4 with the label 'Numerator' and an arrow to 6 with the label 'Denominator'."
            },
            "level_3": {
                "explanation": "Step 1: Identify the reference unit whole [0, 1].\\nStep 2: Partition into N equal sub-units of size 1/N.\\nStep 3: Accumulate k sub-units to form k/N.\\nStep 4: Verify whether k < N (proper fraction), k = N (whole 1), or k > N (improper fraction).",
                "check_question": "If a whole is cut into 10 parts and you take 7, what is the fraction?",
                "visual_description": "A detailed breakdown diagram showing unit interval, partition size 1/N, and accumulated sum k/N."
            }
        },
        "step_by_step": {
            "level_1": {
                "explanation": "Step 1: Look at the top number (numerator). It tells you how many pieces you are counting.\\nStep 2: Look at the bottom number (denominator). It tells you how many equal pieces make up the complete whole.",
                "check_question": "Does the denominator represent the parts you have or the whole?",
                "visual_description": "Diagram with an arrow pointing to top 'Numerator = Parts' and bottom 'Denominator = Whole'."
            },
            "level_2": {
                "explanation": "Step 1: Confirm all pieces are identical in size.\\nStep 2: Count total pieces = 6 (Denominator = 6).\\nStep 3: Count colored pieces = 4 (Numerator = 4).\\nStep 4: Combine into 4/6, read as 'four-sixths'.",
                "check_question": "In the fraction 4/6, what is the numerator?",
                "visual_description": "A diagram pointing an arrow to 4 with the label 'Numerator' and an arrow to 6 with the label 'Denominator'."
            },
            "level_3": {
                "explanation": "Step 1: Identify the reference unit whole [0, 1].\\nStep 2: Partition into N equal sub-units of size 1/N.\\nStep 3: Accumulate k sub-units to form k/N.\\nStep 4: Verify whether k < N (proper fraction), k = N (whole 1), or k > N (improper fraction).",
                "check_question": "If a whole is cut into 10 parts and you take 7, what is the fraction?",
                "visual_description": "A detailed breakdown diagram showing unit interval, partition size 1/N, and accumulated sum k/N."
            }
        },
        "simple_language": {
            "level_1": {
                "explanation": "A fraction is just a part of something. The top number counts how many slices you have. The bottom number counts how many slices the whole cake was cut into.",
                "check_question": "What is the bottom number called?",
                "visual_description": "A slice of cake pulled out of a whole cake."
            },
            "level_2": {
                "explanation": "Fractions help us talk about amounts smaller than 1. If you split a cookie in half, each piece is 1/2. You have 1 piece, but it takes 2 pieces to make the whole cookie.",
                "check_question": "How many halves make a whole cookie?",
                "visual_description": "A round cookie split into two equal halves with a small gap in between."
            },
            "level_3": {
                "explanation": "Whenever you don't have a whole number of items, fractions give an exact measurement. The denominator sets the scale (how small each piece is) and the numerator counts how many of those pieces you hold.",
                "check_question": "If you have 5 eighths of an inch, how many 1/8 pieces do you have?",
                "visual_description": "A ruler highlighting the difference between whole inches and fractional sixteenth ticks."
            }
        }
    },
    "c2_equal_parts": {
        "visual": {
            "level_1": {
                "explanation": "Look at two pizzas. Pizza A is cut with messy, crooked lines into uneven pieces. Pizza B is cut with straight, symmetrical lines into 4 identical quarters. A fraction can ONLY describe Pizza B because fractions strictly require equal parts!",
                "check_question": "Can you use standard fractions if the pieces are different sizes?",
                "visual_description": "Two circular pizzas: one divided unevenly with jagged slices; one divided cleanly with 4 identical quadrant slices."
            },
            "level_2": {
                "explanation": "Look at a square divided into 4 pieces. If one piece is huge and three pieces are tiny, each piece is NOT 1/4. To be 1/4, every piece must cover the exact same surface area.",
                "check_question": "Why must pieces have the exact same area to be called fourths?",
                "visual_description": "A square with 4 identical quadrant squares next to a square with one giant triangle and tiny corners."
            },
            "level_3": {
                "explanation": "Area conservation in partitioning: Even if pieces have different geometric shapes (like triangles and rectangles), they represent equal fractions only if their calculated areas are strictly identical.",
                "check_question": "Can two differently shaped pieces both represent 1/4 of the same whole?",
                "visual_description": "A square partitioned into two triangles and two rectangles, each verified with equal computed area of 4 cm²."
            }
        },
        "analogy": {
            "level_1": {
                "explanation": "Think of sharing cake with your best friend. If you cut the cake so you get a huge slice and your friend gets a tiny crumb, that is unfair! Fractions are completely fair: every piece must be the exact same size.",
                "check_question": "If you give someone a tiny crumb and keep the rest, is that a fair half?",
                "visual_description": "Two plates: one holding almost an entire cake and the other holding a small crumb, next to an unequal balance symbol."
            },
            "level_2": {
                "explanation": "Imagine splitting rent evenly between roommates. If one person gets a master bedroom with a jacuzzi and the other gets a closet, splitting 50/50 isn't equal! Equal fractions require equal portions.",
                "check_question": "Why is equal sharing like equal partitioning?",
                "visual_description": "A floor plan comparing two identical symmetrical bedrooms."
            },
            "level_3": {
                "explanation": "Like calibrated weights on a laboratory balance scale: each 100g weight must have the exact same mass. If one weight is heavier, the entire measurement system loses integrity.",
                "check_question": "What happens to the fraction definition if one partition is larger than the others?",
                "visual_description": "A balance scale with two equal weights resting in level equilibrium."
            }
        },
        "worked": {
            "level_1": {
                "explanation": "Step 1: Look at the whole object.\\nStep 2: Check each dividing line.\\nStep 3: Confirm that every slice has the exact same area or volume. If yes, it represents a valid fraction.",
                "check_question": "What is the key rule for partitioning a whole into fractions?",
                "visual_description": "A ruler checking equal width across three bar segments."
            },
            "level_2": {
                "explanation": "Step 1: Count total sections.\\nStep 2: Compare width, height, or surface area of each section.\\nStep 3: If every section matches, name the fraction as 1/total (e.g. 1/3 for 3 equal sections).",
                "check_question": "If a rectangle is split into 3 sections of different widths, can you call each section 1/3?",
                "visual_description": "A ruler measuring equal 2 cm intervals across a 6 cm bar."
            },
            "level_3": {
                "explanation": "Step 1: Calculate total area A.\\nStep 2: Measure individual piece areas A_1, A_2, ..., A_n.\\nStep 3: Verify A_i = A / n for all pieces.\\nStep 4: Only when variance is zero can each piece be mathematically designated as 1/n.",
                "check_question": "If total area is 12 and there are 4 equal pieces, what is the area of each?",
                "visual_description": "Mathematical table showing area calculations summing to total area with zero variance."
            }
        },
        "step_by_step": {
            "level_1": {
                "explanation": "Step 1: Inspect the whole object.\\nStep 2: Check each dividing line.\\nStep 3: Confirm that every slice has the exact same area or volume. If yes, it represents a valid fraction.",
                "check_question": "What is the key rule for partitioning a whole into fractions?",
                "visual_description": "A ruler checking equal width across three bar segments."
            },
            "level_2": {
                "explanation": "Step 1: Count total sections.\\nStep 2: Compare width, height, or surface area of each section.\\nStep 3: If every section matches, name the fraction as 1/total (e.g. 1/3 for 3 equal sections).",
                "check_question": "If a rectangle is split into 3 sections of different widths, can you call each section 1/3?",
                "visual_description": "A ruler measuring equal 2 cm intervals across a 6 cm bar."
            },
            "level_3": {
                "explanation": "Step 1: Calculate total area A.\\nStep 2: Measure individual piece areas A_1, A_2, ..., A_n.\\nStep 3: Verify A_i = A / n for all pieces.\\nStep 4: Only when variance is zero can each piece be mathematically designated as 1/n.",
                "check_question": "If total area is 12 and there are 4 equal pieces, what is the area of each?",
                "visual_description": "Mathematical table showing area calculations summing to total area with zero variance."
            }
        },
        "simple_language": {
            "level_1": {
                "explanation": "In fractions, 'fair is fair'. All pieces must be the exact same size. If one piece is bigger than the rest, it is not an equal fraction.",
                "check_question": "Do fraction pieces have to be the exact same size?",
                "visual_description": "Equal balance scales weighing two pieces of cake."
            },
            "level_2": {
                "explanation": "You can only use fraction names like 'thirds' or 'fourths' if every piece is equal. Cutting something into 4 pieces doesn't make fourths unless all 4 pieces are identical.",
                "check_question": "Does cutting an apple into 3 random chunks make true thirds?",
                "visual_description": "An apple cut into 3 identical wedges."
            },
            "level_3": {
                "explanation": "The whole idea of fractions relies on equal parts. The denominator only has meaning when every single division represents the exact same quantity.",
                "check_question": "Why does the denominator depend on parts being equal?",
                "visual_description": "A grid illustrating that equal units create a consistent measurement grid."
            }
        }
    },
    "c3_fraction_as_division": {
        "visual": {
            "level_1": {
                "explanation": "Picture 3 pizzas shared by 4 friends. If you slice each of the 3 pizzas into 4 quarters, there are 12 quarters total. When distributed equally, each friend takes 3 quarters (3/4 of a pizza).",
                "check_question": "How much pizza does each friend get?",
                "visual_description": "Draw 3 circles (pizzas). Cut each into 4 equal slices (quarters). Give 1 slice from each pizza to each friend, giving 3 slices out of 4 to each person."
            },
            "level_2": {
                "explanation": "Imagine 3 identical rectangular candy bars. Divide each candy bar into 4 equal blocks. Each friend gets one block from each candy bar. Since there are 3 candy bars, each friend holds 3 fourth-blocks: exactly 3/4 of a whole bar.",
                "check_question": "If you had 2 candy bars shared among 3 friends, what fraction would each get?",
                "visual_description": "Draw 3 long rectangles side by side. Draw lines splitting each into 4 segments. Color in one segment per rectangle in blue: 3 blocks out of 4-unit whole."
            },
            "level_3": {
                "explanation": "On a number line spanning [0, 3], divide the entire length into 4 equal segments. Each segment has length 3/4 (0.75). The fraction bar directly represents the algebraic division operator: a/b is identical to a ÷ b.",
                "check_question": "What is the length of each segment when the interval [0, 5] is divided into 2 equal parts?",
                "visual_description": "A continuous number line from 0 to 3 divided into 4 equal intervals of length 3/4."
            }
        },
        "analogy": {
            "level_1": {
                "explanation": "Think of a fraction like a recipe shared among cooks. The numerator is what you have on the kitchen counter (3 items), and the denominator is the number of plates you must fill evenly (4 plates). Each plate receives 3/4 of an item.",
                "check_question": "In this kitchen analogy, what does the denominator represent?",
                "visual_description": "Imagine 3 pies lined up, with arrows pointing into 4 empty banquet plates."
            },
            "level_2": {
                "explanation": "Think of a music band splitting cash earnings after a gig. If the band earned $300 and has 4 members, each gets $300 ÷ 4 = $75. Similarly, if they share 3 gold coins, each gets 3/4 of a coin.",
                "check_question": "What mathematical operation does the fraction line '/' represent?",
                "visual_description": "A fraction bar acting like a seesaw with total items on top and receivers balanced on the bottom."
            },
            "level_3": {
                "explanation": "Think of an industrial pump delivering 3 liters of liquid into 4 test cylinders simultaneously. The fill height in each cylinder is exactly 3/4 liters.",
                "check_question": "If 6 liters are poured equally into 8 containers, what fraction is in each container?",
                "visual_description": "A primary fluid reservoir feeding evenly into 4 graduated beakers."
            }
        },
        "worked": {
            "level_1": {
                "explanation": "Step 1: Identify what is being shared (the items). That is 3, which becomes the numerator (top).\\nStep 2: Identify who or what is dividing the items (the recipients). That is 4, which becomes the denominator (bottom).\\nStep 3: Write it as a fraction: 3/4.",
                "check_question": "What is the numerator in 3/4?",
                "visual_description": "A vertical layout highlighting 'Items (3)' -> numerator over 'People (4)' -> denominator."
            },
            "level_2": {
                "explanation": "Step 1: State the division problem: a ÷ b.\\nStep 2: Write dividend 'a' as numerator.\\nStep 3: Write divisor 'b' as denominator.\\nStep 4: Understand that 3 ÷ 4 = 3/4.",
                "check_question": "How do you write 5 divided by 8 as a fraction?",
                "visual_description": "An arrow transforming 3 ÷ 4 directly into the fraction 3/4."
            },
            "level_3": {
                "explanation": "Step 1: Set up quotient equation: q = a / b.\\nStep 2: Recognize that for any integers a and b (b != 0), a/b is the exact value that satisfies q * b = a.\\nStep 3: Verify: (3/4) * 4 = 3.",
                "check_question": "What do you get when you multiply 3/4 by 4?",
                "visual_description": "Algebraic proof showing division definition and verification through multiplication."
            }
        },
        "step_by_step": {
            "level_1": {
                "explanation": "Step 1: Identify what is being shared (the items). That is 3, which becomes the numerator (top).\\nStep 2: Identify who or what is dividing the items (the recipients). That is 4, which becomes the denominator (bottom).\\nStep 3: Write it as a fraction: 3/4.",
                "check_question": "What is the numerator in 3/4?",
                "visual_description": "A vertical layout highlighting 'Items (3)' -> numerator over 'People (4)' -> denominator."
            },
            "level_2": {
                "explanation": "Step 1: State the division problem: a ÷ b.\\nStep 2: Write dividend 'a' as numerator.\\nStep 3: Write divisor 'b' as denominator.\\nStep 4: Understand that 3 ÷ 4 = 3/4.",
                "check_question": "How do you write 5 divided by 8 as a fraction?",
                "visual_description": "An arrow transforming 3 ÷ 4 directly into the fraction 3/4."
            },
            "level_3": {
                "explanation": "Step 1: Set up quotient equation: q = a / b.\\nStep 2: Recognize that for any integers a and b (b != 0), a/b is the exact value that satisfies q * b = a.\\nStep 3: Verify: (3/4) * 4 = 3.",
                "check_question": "What do you get when you multiply 3/4 by 4?",
                "visual_description": "Algebraic proof showing division definition and verification through multiplication."
            }
        },
        "simple_language": {
            "level_1": {
                "explanation": "When you have 3 things and 4 people, no one gets a whole thing. Everyone gets a fraction: 3 divided by 4, written simply as 3/4.",
                "check_question": "Can everyone get a whole pizza if there are only 3 pizzas for 4 people?",
                "visual_description": "3 pizzas grouped together, with a small caption showing each person gets 3 out of 4 slices."
            },
            "level_2": {
                "explanation": "The fraction line is just another way to write a division sign. 3/4 literally means 3 divided by 4.",
                "check_question": "What sign does the middle line in a fraction stand for?",
                "visual_description": "A division sign ÷ transforming into a fraction bar."
            },
            "level_3": {
                "explanation": "Whenever division doesn't give a whole number, fractions give the exact answer without needing messy rounded decimals.",
                "check_question": "Why is 1/3 more exact than writing 0.333?",
                "visual_description": "Comparison showing exact 1/3 vs rounded 0.33."
            }
        }
    },
    "c4_equivalent_fractions": {
        "visual": {
            "level_1": {
                "explanation": "Look at two chocolate bars of the same size. Bar A is cut into 2 halves, and you take 1 piece (1/2). Bar B is cut into 4 quarters, and you take 2 pieces (2/4). Notice that both amounts cover the exact same area!",
                "check_question": "Is 2/4 greater than, less than, or equal to 1/2?",
                "visual_description": "Two identical bars side-by-side: Top bar has 1/2 shaded; bottom bar has 2/4 shaded. Both shaded lengths are identical."
            },
            "level_2": {
                "explanation": "Imagine cutting a pizza into 4 slices and taking 2 slices (2/4). Now imagine cutting those slices again so there are 8 slices total and you have 4 (4/8). You still have the same amount of pizza: 1/2 = 2/4 = 4/8.",
                "check_question": "Does cutting pizza into smaller slices give you more food?",
                "visual_description": "Three circles with the right half shaded: 1 slice out of 2, 2 out of 4, and 4 out of 8."
            },
            "level_3": {
                "explanation": "Multiplying both numerator and denominator by the same number k is the same as multiplying by k/k = 1. Since multiplying by 1 never changes value, 1/2 * (2/2) = 2/4.",
                "check_question": "What is the value of 2/2?",
                "visual_description": "A fraction 1/2 multiplied by a giant number 1 shaped like (2/2) resulting in 2/4."
            }
        },
        "analogy": {
            "level_1": {
                "explanation": "Think of currency: one $1 bill has the exact same value as two 50-cent coins or four 25-cent quarters. They look different, but their value is identical.",
                "check_question": "How many fourths equal one half?",
                "visual_description": "A 1-dollar bill shown as equal to two half-dollar coins."
            },
            "level_2": {
                "explanation": "Think of having a favorite nickname. Whether someone calls you by your full name or your nickname, you are still the exact same person. 1/2 and 2/4 are different names for the same number.",
                "check_question": "Are 1/2 and 2/4 different amounts or different names for the same amount?",
                "visual_description": "Two name tags with '1/2' and '2/4' attached to the same friendly character."
            },
            "level_3": {
                "explanation": "Think of scaling an image resolution: whether an image is 100x100 or 200x200, its aspect ratio (proportions) remains identical.",
                "check_question": "Why does multiplying width and height by 2 keep an image shape the same?",
                "visual_description": "Two screens of different resolutions displaying identical aspect ratios."
            }
        },
        "worked": {
            "level_1": {
                "explanation": "Step 1: Check what you multiply or divide the bottom number by.\\nStep 2: Multiply or divide the top number by the exact same value.\\nStep 3: If 1/2 becomes ?/4, 2 × 2 = 4, so 1 × 2 = 2. The equivalent fraction is 2/4.",
                "check_question": "What must you do to the top number if you multiply the bottom number by 3?",
                "visual_description": "1/2 with ×2 on top and ×2 on bottom leading to 2/4."
            },
            "level_2": {
                "explanation": "Step 1: To find an equivalent fraction for 3/5 with denominator 15, divide 15 by 5 = 3.\\nStep 2: Multiply numerator 3 by 3 = 9.\\nStep 3: Write 9/15. Therefore, 3/5 = 9/15.",
                "check_question": "What is the equivalent fraction for 2/3 with denominator 12?",
                "visual_description": "Step-by-step arrows showing 5 × 3 = 15 and 3 × 3 = 9."
            },
            "level_3": {
                "explanation": "Step 1: To simplify 12/16 to simplest terms, find greatest common factor: GCD(12, 16) = 4.\\nStep 2: Divide numerator by 4: 12 ÷ 4 = 3.\\nStep 3: Divide denominator by 4: 16 ÷ 4 = 4.\\nStep 4: Result is 3/4.",
                "check_question": "What is 8/10 in simplest form?",
                "visual_description": "Division arrows showing top and bottom divided by GCD 4 to yield 3/4."
            }
        },
        "step_by_step": {
            "level_1": {
                "explanation": "Step 1: Check what you multiply or divide the bottom number by.\\nStep 2: Multiply or divide the top number by the exact same value.\\nStep 3: If 1/2 becomes ?/4, 2 × 2 = 4, so 1 × 2 = 2. The equivalent fraction is 2/4.",
                "check_question": "What must you do to the top number if you multiply the bottom number by 3?",
                "visual_description": "1/2 with ×2 on top and ×2 on bottom leading to 2/4."
            },
            "level_2": {
                "explanation": "Step 1: To find an equivalent fraction for 3/5 with denominator 15, divide 15 by 5 = 3.\\nStep 2: Multiply numerator 3 by 3 = 9.\\nStep 3: Write 9/15. Therefore, 3/5 = 9/15.",
                "check_question": "What is the equivalent fraction for 2/3 with denominator 12?",
                "visual_description": "Step-by-step arrows showing 5 × 3 = 15 and 3 × 3 = 9."
            },
            "level_3": {
                "explanation": "Step 1: To simplify 12/16 to simplest terms, find greatest common factor: GCD(12, 16) = 4.\\nStep 2: Divide numerator by 4: 12 ÷ 4 = 3.\\nStep 3: Divide denominator by 4: 16 ÷ 4 = 4.\\nStep 4: Result is 3/4.",
                "check_question": "What is 8/10 in simplest form?",
                "visual_description": "Division arrows showing top and bottom divided by GCD 4 to yield 3/4."
            }
        },
        "simple_language": {
            "level_1": {
                "explanation": "Equivalent fractions are different ways of naming the exact same amount. Cutting a pizza into smaller slices doesn't give you more pizza!",
                "check_question": "Does cutting pizza into more slices increase the total food you have?",
                "visual_description": "Two pizzas of same size, one cut into 2 slices, one cut into 4 slices."
            },
            "level_2": {
                "explanation": "Whatever you do to the top number, you must also do to the bottom number. Double the top? Double the bottom. The fraction stays equal.",
                "check_question": "If you multiply the top number by 5, what must you do to the bottom number?",
                "visual_description": "A scale remaining in balance when both sides are doubled."
            },
            "level_3": {
                "explanation": "Two fractions are equivalent if they land on the exact same spot on the number line.",
                "check_question": "Where do 1/2 and 2/4 land on a number line?",
                "visual_description": "A number line showing 1/2 and 2/4 aligned at the exact same point."
            }
        }
    },
    "c5_comparing_fractions": {
        "visual": {
            "level_1": {
                "explanation": "Imagine two identical measuring cups. Cup A is filled to 2/5 and Cup B is filled to 3/5. Because both cups have fifths as their marking, Cup B with 3 parts is noticeably higher than Cup A with 2 parts (3/5 > 2/5).",
                "check_question": "Between 2/5 and 3/5, which cup has more liquid?",
                "visual_description": "Two graduated cylinders with 5 tick marks. One filled to mark 2, other filled to mark 3."
            },
            "level_2": {
                "explanation": "Compare 1/2 and 1/4. Look at the circle slices: cutting a pizza into 4 slices makes each slice smaller than cutting into 2 slices! So 1/2 is bigger than 1/4.",
                "check_question": "Is 1/3 bigger or smaller than 1/6?",
                "visual_description": "Two pizzas: one with 1/2 shaded (large slice), one with 1/4 shaded (smaller slice)."
            },
            "level_3": {
                "explanation": "To compare 2/3 and 3/4, find a common denominator: twelfths. 2/3 = 8/12 and 3/4 = 9/12. Since 9/12 > 8/12, 3/4 is greater than 2/3.",
                "check_question": "Which is greater: 2/3 or 3/4?",
                "visual_description": "A number line graduated in twelfths showing 8/12 (2/3) to the left of 9/12 (3/4)."
            }
        },
        "analogy": {
            "level_1": {
                "explanation": "Imagine two runners on a 5-mile track. Runner A completed 2 miles (2/5) while Runner B completed 3 miles (3/5). Runner B is further along the track.",
                "check_question": "Why is 3/5 greater than 2/5?",
                "visual_description": "A 5-mile road with two runners at milestone 2 and 3."
            },
            "level_2": {
                "explanation": "Would you rather share 1 pizza with 2 people or 1 pizza with 8 people? When sharing with 2 people, your share is much larger! A bigger bottom number means smaller shares.",
                "check_question": "If the numerator is 1, does a bigger denominator mean a bigger or smaller piece?",
                "visual_description": "A pizza shared between 2 friends versus a pizza shared between 8 friends."
            },
            "level_3": {
                "explanation": "Think of comparing two fuel gauges: Gauge A shows 5 out of 8 gallons remaining, Gauge B shows 3 out of 4 gallons. Standardizing to eighths (6/8) makes the comparison instant.",
                "check_question": "How many eighths is 3/4?",
                "visual_description": "Two car dashboard fuel gauges showing 5/8 vs 6/8."
            }
        },
        "worked": {
            "level_1": {
                "explanation": "Step 1: Look at the denominators. Are they the same? Yes, both are 5.\\nStep 2: Since pieces are identical in size, compare numerators: 3 > 2.\\nStep 3: Conclude that 3/5 > 2/5.",
                "check_question": "When denominators are equal, which fraction is larger?",
                "visual_description": "Comparing numerators 2 vs 3 over equal denominators 5."
            },
            "level_2": {
                "explanation": "Step 1: When numerators are the same (like 1/3 vs 1/5), compare denominators.\\nStep 2: Remember: smaller denominator means bigger pieces.\\nStep 3: Since 3 < 5, each third is bigger than each fifth: 1/3 > 1/5.",
                "check_question": "Which fraction is bigger: 1/4 or 1/10?",
                "visual_description": "A comparison chart showing inverse relation between denominator and piece size."
            },
            "level_3": {
                "explanation": "Step 1: To compare a/b and c/d with different denominators, cross-multiply: compare a × d with b × c.\\nStep 2: For 3/5 and 4/7: 3 × 7 = 21 and 5 × 4 = 20.\\nStep 3: Since 21 > 20, 3/5 > 4/7.",
                "check_question": "Using cross-multiplication, is 2/3 greater than 3/5?",
                "visual_description": "A cross-multiplication diagram showing diagonal arrows: 3×7=21 on left and 5×4=20 on right."
            }
        },
        "step_by_step": {
            "level_1": {
                "explanation": "Step 1: Look at the denominators. Are they the same? Yes, both are 5.\\nStep 2: Since pieces are identical in size, compare numerators: 3 > 2.\\nStep 3: Conclude that 3/5 > 2/5.",
                "check_question": "When denominators are equal, which fraction is larger?",
                "visual_description": "Comparing numerators 2 vs 3 over equal denominators 5."
            },
            "level_2": {
                "explanation": "Step 1: When numerators are the same (like 1/3 vs 1/5), compare denominators.\\nStep 2: Remember: smaller denominator means bigger pieces.\\nStep 3: Since 3 < 5, each third is bigger than each fifth: 1/3 > 1/5.",
                "check_question": "Which fraction is bigger: 1/4 or 1/10?",
                "visual_description": "A comparison chart showing inverse relation between denominator and piece size."
            },
            "level_3": {
                "explanation": "Step 1: To compare a/b and c/d with different denominators, cross-multiply: compare a × d with b × c.\\nStep 2: For 3/5 and 4/7: 3 × 7 = 21 and 5 × 4 = 20.\\nStep 3: Since 21 > 20, 3/5 > 4/7.",
                "check_question": "Using cross-multiplication, is 2/3 greater than 3/5?",
                "visual_description": "A cross-multiplication diagram showing diagonal arrows: 3×7=21 on left and 5×4=20 on right."
            }
        },
        "simple_language": {
            "level_1": {
                "explanation": "When two fractions have the same bottom number, the slices are the same size. Having 3 slices is always more than having 2 slices!",
                "check_question": "Which is more: 3 slices or 2 slices of the same size?",
                "visual_description": "3 slices on a plate vs 2 slices on another plate."
            },
            "level_2": {
                "explanation": "If you cut a pie into 100 slices, each slice is microscopic! If you cut it into 2 slices, each slice is huge. Bigger bottom number = smaller slices.",
                "check_question": "Which slice is bigger: 1/2 of a pie or 1/100 of a pie?",
                "visual_description": "A huge half slice compared with a tiny sliver."
            },
            "level_3": {
                "explanation": "To compare tricky fractions, change them into matching slice sizes (common denominators) first, then just look at the top numbers.",
                "check_question": "What must match before you can add fraction numerators?",
                "visual_description": "Two unequal fractions being converted to matching denominators side by side."
            }
        }
    },
    "c6_adding_fractions": {
        "visual": {
            "level_1": {
                "explanation": "Imagine a 6-slice pizza. You eat 1 slice (1/6) and your friend eats 3 slices (3/6). Together you ate 1 + 3 = 4 slices out of the 6 total slices (4/6). Notice the denominator stays 6 because the slice sizes never changed!",
                "check_question": "Why didn't the denominator change to 12 when adding 1/6 + 3/6?",
                "visual_description": "A pizza with 6 slices: 1 shaded blue, 3 shaded green, 2 unshaded."
            },
            "level_2": {
                "explanation": "Look at a ruler marked in eighths. Moving forward 2 eighths (2/8) and then another 3 eighths (3/8) lands you at 5 eighths (5/8). You add the steps (2 + 3 = 5), not the unit size.",
                "check_question": "What is 2/8 + 3/8?",
                "visual_description": "A ruler with two jump arrows: 0 to 2/8, then 2/8 to 5/8."
            },
            "level_3": {
                "explanation": "When adding unlike fractions like 1/2 + 1/4, you cannot add directly because slices differ in size. Split the 1/2 slice into two 1/4 slices (2/4). Now add: 2/4 + 1/4 = 3/4.",
                "check_question": "Why must denominators match before adding fractions?",
                "visual_description": "A circle diagram showing 1/2 converted into 2/4 slices before combining with 1/4."
            }
        },
        "analogy": {
            "level_1": {
                "explanation": "Think of adding items: 1 cat + 3 cats = 4 cats. You don't get '4 double-cats'. In 1/6 + 3/6, 'sixths' is just the name of the item: 1 sixth + 3 sixths = 4 sixths.",
                "check_question": "What is the common item name when adding 1/6 and 3/6?",
                "visual_description": "Baskets with sixths labeled like unit items being combined into a larger basket."
            },
            "level_2": {
                "explanation": "Like counting currency: one 5-dollar bill plus two 5-dollar bills equals three 5-dollar bills ($15). The denomination ($5 bill) stays the same; only the count increases.",
                "check_question": "Why does the denomination stay the same when counting bills?",
                "visual_description": "Banknotes of the same denomination being grouped together."
            },
            "level_3": {
                "explanation": "Like combining liquids in chemistry: pouring 200 mL and 300 mL into a 1000 mL beaker gives 500 mL out of 1000 mL. The total beaker capacity (1000 mL) remains constant.",
                "check_question": "In the beaker example, what represents the denominator?",
                "visual_description": "Two smaller beakers pouring into a 1000 mL measuring flask."
            }
        },
        "worked": {
            "level_1": {
                "explanation": "Step 1: Check that denominators are identical (both 6).\\nStep 2: Add numerators only: 1 + 3 = 4.\\nStep 3: Keep the denominator: 4/6.\\nStep 4: Reduce to lowest terms if possible: 4/6 = 2/3.",
                "check_question": "Do you add the bottom numbers when adding fractions?",
                "visual_description": "Fraction addition equation showing numerators adding and denominator staying constant."
            },
            "level_2": {
                "explanation": "Step 1: Check denominators: In 2/10 + 3/10, both are 10.\\nStep 2: Add numerators: 2 + 3 = 5.\\nStep 3: Keep denominator: 5/10.\\nStep 4: Simplify by dividing top and bottom by 5: 5/10 = 1/2.",
                "check_question": "What is 2/10 + 3/10 in simplest form?",
                "visual_description": "Step-by-step arithmetic: 2/10 + 3/10 = 5/10 = 1/2."
            },
            "level_3": {
                "explanation": "Step 1: Given 1/3 + 1/6, find common denominator: LCM(3, 6) = 6.\\nStep 2: Convert 1/3: multiply top and bottom by 2 -> 2/6.\\nStep 3: Add converted fractions: 2/6 + 1/6 = 3/6.\\nStep 4: Simplify: 3/6 = 1/2.",
                "check_question": "What is the common denominator for 1/3 and 1/6?",
                "visual_description": "Four-step diagram showing conversion of 1/3 to 2/6 followed by addition and simplification."
            }
        },
        "step_by_step": {
            "level_1": {
                "explanation": "Step 1: Check that denominators are identical (both 6).\\nStep 2: Add numerators only: 1 + 3 = 4.\\nStep 3: Keep the denominator: 4/6.\\nStep 4: Reduce to lowest terms by dividing by 2: 2/3.",
                "check_question": "What is 4/6 divided by 2/2?",
                "visual_description": "Fraction addition equation showing numerators adding and denominator staying constant."
            },
            "level_2": {
                "explanation": "Step 1: Check denominators: In 2/10 + 3/10, both are 10.\\nStep 2: Add numerators: 2 + 3 = 5.\\nStep 3: Keep denominator: 5/10.\\nStep 4: Simplify by dividing top and bottom by 5: 5/10 = 1/2.",
                "check_question": "What is 2/10 + 3/10 in simplest form?",
                "visual_description": "Step-by-step arithmetic: 2/10 + 3/10 = 5/10 = 1/2."
            },
            "level_3": {
                "explanation": "Step 1: Given 1/3 + 1/6, find common denominator: LCM(3, 6) = 6.\\nStep 2: Convert 1/3: multiply top and bottom by 2 -> 2/6.\\nStep 3: Add converted fractions: 2/6 + 1/6 = 3/6.\\nStep 4: Simplify: 3/6 = 1/2.",
                "check_question": "What is the common denominator for 1/3 and 1/6?",
                "visual_description": "Four-step diagram showing conversion of 1/3 to 2/6 followed by addition and simplification."
            }
        },
        "simple_language": {
            "level_1": {
                "explanation": "When adding fractions with the same bottom number, only add the top numbers. Keep the bottom number the same!",
                "check_question": "Do you add the bottom numbers when adding fractions?",
                "visual_description": "Equation highlighting top numbers with a plus sign, bottom number with an arrow straight across."
            },
            "level_2": {
                "explanation": "Never add the bottom numbers! If you have 1 fourth of a pie and get 2 more fourths, you have 3 fourths, not 3 eighths.",
                "check_question": "What is 1/4 + 2/4?",
                "visual_description": "Pie wedges combining into 3/4."
            },
            "level_3": {
                "explanation": "You can only add fractions if their slice sizes match. If bottom numbers are different, change them to matching slices first, then add the tops.",
                "check_question": "What must match before you can add fraction numerators?",
                "visual_description": "Two unequal puzzle pieces being sliced so they fit together."
            }
        }
    }
}


def validate_bank(bank: Dict[str, Any], concepts_path: Path) -> List[str]:
    """
    Validates that every concept in concepts.json has complete multimodal coverage
    and valid schema structures {explanation, check_question, visual_description}.
    """
    errors: List[str] = []
    if not concepts_path.exists():
        errors.append(f"Concepts file not found at {concepts_path}")
        return errors

    with open(concepts_path, "r", encoding="utf-8") as f:
        concepts = json.load(f)

    required_styles = ["visual", "analogy", "worked"]
    required_levels = ["level_1", "level_2", "level_3"]
    required_keys = ["explanation", "check_question", "visual_description"]

    for c in concepts:
        cid = c["id"]
        if cid not in bank:
            errors.append(f"Missing concept in offline bank: {cid}")
            continue

        c_data = bank[cid]
        for style in required_styles:
            if style not in c_data:
                errors.append(f"Concept {cid} missing required style: {style}")
                continue
            for lvl in required_levels:
                if lvl not in c_data[style]:
                    errors.append(f"Concept {cid} style {style} missing level: {lvl}")
                    continue
                entry = c_data[style][lvl]
                for key in required_keys:
                    if key not in entry or not isinstance(entry[key], str) or not entry[key].strip():
                        errors.append(f"Concept {cid} style {style} {lvl} invalid/empty key: {key}")

    return errors


def build_bank() -> Dict[str, Any]:
    """
    Validates and writes explanations.json to both backend/data and data directories.
    """
    print("Building and validating ClearPath offline explanation bank...")

    concepts_file = BACKEND_DATA_DIR / "concepts.json"
    if not concepts_file.exists():
        concepts_file = ROOT_DATA_DIR / "concepts.json"

    errors = validate_bank(OFFLINE_BANK_DATA, concepts_file)
    if errors:
        print(f"Validation FAILED with {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        raise ValueError(f"Offline bank validation failed: {errors[0]}")

    # Ensure target directories exist
    BACKEND_DATA_DIR.mkdir(parents=True, exist_ok=True)
    ROOT_DATA_DIR.mkdir(parents=True, exist_ok=True)

    backend_out = BACKEND_DATA_DIR / "explanations.json"
    root_out = ROOT_DATA_DIR / "explanations.json"

    formatted_json = json.dumps(OFFLINE_BANK_DATA, indent=2, ensure_ascii=False)

    with open(backend_out, "w", encoding="utf-8") as f:
        f.write(formatted_json)

    with open(root_out, "w", encoding="utf-8") as f:
        f.write(formatted_json)

    print(f"Successfully verified and saved offline explanation bank:")
    print(f"  -> {backend_out}")
    print(f"  -> {root_out}")
    print(f"Total concepts covered: {len(OFFLINE_BANK_DATA)}")
    return OFFLINE_BANK_DATA


if __name__ == "__main__":
    build_bank()

