"""
Coding round problems for the live code-execution feature.
Each problem includes test cases (stdin -> expected stdout) so submitted
code can be judged for actual correctness via Judge0, not just eyeballed.

These are original write-ups of classic, widely-taught algorithm concepts
(arrays, strings, hashmaps, recursion, sorting) - not copied from any
specific platform's problem bank. Candidate code reads from stdin and
prints to stdout, which keeps judging language-agnostic and simple.

'topic' is used to match problems to a candidate's JD/skill_gaps, the
same way the Q&A question bank does.
"""

CODING_PROBLEMS = [
    # --- Difficulty 1: fundamentals ---
    {
        "id": "cp_reverse_string",
        "title": "Reverse a String",
        "topic": "strings",
        "difficulty": 1,
        "description": "Read a single line of text and print it reversed.",
        "test_cases": [
            {"stdin": "hello\n", "expected_stdout": "olleh"},
            {"stdin": "virexa\n", "expected_stdout": "axeriv"},
        ],
    },
    {
        "id": "cp_fizzbuzz",
        "title": "FizzBuzz",
        "topic": "basics",
        "difficulty": 1,
        "description": (
            "Read an integer n. Print numbers 1 to n, one per line. For multiples of "
            "3 print 'Fizz', for multiples of 5 print 'Buzz', for multiples of both "
            "print 'FizzBuzz'."
        ),
        "test_cases": [
            {"stdin": "5\n", "expected_stdout": "1\n2\nFizz\n4\nBuzz"},
            {"stdin": "15\n", "expected_stdout": "1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n13\n14\nFizzBuzz"},
        ],
    },
    {
        "id": "cp_sum_array",
        "title": "Sum of an Array",
        "topic": "arrays",
        "difficulty": 1,
        "description": "Read a line of space-separated integers and print their sum.",
        "test_cases": [
            {"stdin": "1 2 3 4 5\n", "expected_stdout": "15"},
            {"stdin": "-1 -2 3\n", "expected_stdout": "0"},
        ],
    },
    {
        "id": "cp_count_vowels",
        "title": "Count Vowels",
        "topic": "strings",
        "difficulty": 1,
        "description": "Read a line of text and print the number of vowels (a, e, i, o, u - case-insensitive) in it.",
        "test_cases": [
            {"stdin": "Interview\n", "expected_stdout": "4"},
            {"stdin": "xyz\n", "expected_stdout": "0"},
        ],
    },

    # --- Difficulty 2: common interview basics ---
    {
        "id": "cp_is_palindrome",
        "title": "Palindrome Check",
        "topic": "strings",
        "difficulty": 2,
        "description": "Read a single word and print 'Yes' if it's a palindrome, 'No' otherwise.",
        "test_cases": [
            {"stdin": "racecar\n", "expected_stdout": "Yes"},
            {"stdin": "hello\n", "expected_stdout": "No"},
            {"stdin": "level\n", "expected_stdout": "Yes"},
        ],
    },
    {
        "id": "cp_find_max",
        "title": "Find the Maximum",
        "topic": "arrays",
        "difficulty": 2,
        "description": "Read a line of space-separated integers and print the largest one, without using a built-in max function.",
        "test_cases": [
            {"stdin": "3 7 2 9 4\n", "expected_stdout": "9"},
            {"stdin": "-5 -1 -10\n", "expected_stdout": "-1"},
        ],
    },
    {
        "id": "cp_count_frequency",
        "title": "Character Frequency Count",
        "topic": "hashmaps",
        "difficulty": 2,
        "description": (
            "Read a word and print each distinct character with its count, one per "
            "line, in the order each character first appears. Format: 'char count'."
        ),
        "test_cases": [
            {"stdin": "aabbc\n", "expected_stdout": "a 2\nb 2\nc 1"},
            {"stdin": "xyz\n", "expected_stdout": "x 1\ny 1\nz 1"},
        ],
    },
    {
        "id": "cp_remove_duplicates",
        "title": "Remove Duplicates from a List",
        "topic": "arrays",
        "difficulty": 2,
        "description": (
            "Read a line of space-separated integers and print the list with "
            "duplicates removed, keeping the first occurrence order, space-separated."
        ),
        "test_cases": [
            {"stdin": "1 2 2 3 1 4\n", "expected_stdout": "1 2 3 4"},
            {"stdin": "5 5 5\n", "expected_stdout": "5"},
        ],
    },
    {
        "id": "cp_factorial",
        "title": "Factorial (Recursive)",
        "topic": "recursion",
        "difficulty": 2,
        "description": "Read an integer n and print n! (factorial), computed using recursion.",
        "test_cases": [
            {"stdin": "5\n", "expected_stdout": "120"},
            {"stdin": "0\n", "expected_stdout": "1"},
        ],
    },

    # --- Difficulty 3: intermediate ---
    {
        "id": "cp_two_sum",
        "title": "Two Sum",
        "topic": "hashmaps",
        "difficulty": 3,
        "description": (
            "Given a line of space-separated integers followed by a target value on "
            "the next line, print the 0-based indices of the two numbers that add up "
            "to the target, space-separated. Example input:\n"
            "2 7 11 15\n9\n"
            "Expected output: 0 1"
        ),
        "test_cases": [
            {"stdin": "2 7 11 15\n9\n", "expected_stdout": "0 1"},
            {"stdin": "3 2 4\n6\n", "expected_stdout": "1 2"},
            {"stdin": "3 3\n6\n", "expected_stdout": "0 1"},
        ],
    },
    {
        "id": "cp_first_non_repeating",
        "title": "First Non-Repeating Character",
        "topic": "hashmaps",
        "difficulty": 3,
        "description": (
            "Read a single word and print the first character that does not repeat "
            "anywhere else in the word. If every character repeats, print -1."
        ),
        "test_cases": [
            {"stdin": "swiss\n", "expected_stdout": "w"},
            {"stdin": "aabbcc\n", "expected_stdout": "-1"},
            {"stdin": "hello\n", "expected_stdout": "h"},
        ],
    },
    {
        "id": "cp_binary_search",
        "title": "Binary Search",
        "topic": "searching",
        "difficulty": 3,
        "description": (
            "Read a line of sorted, space-separated integers, then a target value on "
            "the next line. Print the 0-based index of the target using binary "
            "search, or -1 if not found."
        ),
        "test_cases": [
            {"stdin": "1 3 5 7 9 11\n7\n", "expected_stdout": "3"},
            {"stdin": "2 4 6 8\n5\n", "expected_stdout": "-1"},
        ],
    },
    {
        "id": "cp_valid_parentheses",
        "title": "Valid Parentheses",
        "topic": "stacks",
        "difficulty": 3,
        "description": (
            "Read a line containing only the characters ( ) { } [ ]. Print 'Valid' "
            "if every bracket is properly opened and closed in the right order, "
            "'Invalid' otherwise."
        ),
        "test_cases": [
            {"stdin": "({[]})\n", "expected_stdout": "Valid"},
            {"stdin": "({[})\n", "expected_stdout": "Invalid"},
            {"stdin": "(()\n", "expected_stdout": "Invalid"},
        ],
    },
    {
        "id": "cp_bubble_sort",
        "title": "Sort an Array (implement your own sort)",
        "topic": "sorting",
        "difficulty": 3,
        "description": (
            "Read a line of space-separated integers and print them sorted in "
            "ascending order. Implement the sorting yourself rather than calling a "
            "built-in sort function."
        ),
        "test_cases": [
            {"stdin": "5 2 8 1 9\n", "expected_stdout": "1 2 5 8 9"},
            {"stdin": "3 3 1\n", "expected_stdout": "1 3 3"},
        ],
    },

    # --- Difficulty 4: harder / more design-oriented ---
    {
        "id": "cp_max_subarray",
        "title": "Maximum Subarray Sum",
        "topic": "arrays",
        "difficulty": 4,
        "description": (
            "Given a line of space-separated integers (positive and negative), print "
            "the maximum possible sum of any contiguous subarray."
        ),
        "test_cases": [
            {"stdin": "-2 1 -3 4 -1 2 1 -5 4\n", "expected_stdout": "6"},
            {"stdin": "1 2 3 4\n", "expected_stdout": "10"},
            {"stdin": "-1 -2 -3\n", "expected_stdout": "-1"},
        ],
    },
    {
        "id": "cp_anagram_groups",
        "title": "Group Anagrams",
        "topic": "hashmaps",
        "difficulty": 4,
        "description": (
            "Read a line of space-separated words. Print groups of anagrams, one "
            "group per line, words space-separated within a group, groups in order "
            "of each group's first appearance, words within a group in original order."
        ),
        "test_cases": [
            {"stdin": "eat tea tan ate nat bat\n", "expected_stdout": "eat tea ate\ntan nat\nbat"},
        ],
    },
    {
        "id": "cp_fibonacci_memo",
        "title": "Fibonacci with Memoization",
        "topic": "recursion",
        "difficulty": 4,
        "description": (
            "Read an integer n and print the nth Fibonacci number (0-indexed: "
            "fib(0)=0, fib(1)=1). Use memoization so it runs efficiently even for "
            "larger n (e.g. n=35 should return quickly)."
        ),
        "test_cases": [
            {"stdin": "10\n", "expected_stdout": "55"},
            {"stdin": "20\n", "expected_stdout": "6765"},
        ],
    },

    # --- Difficulty 5: hardest ---
    {
        "id": "cp_longest_substring",
        "title": "Longest Substring Without Repeating Characters",
        "topic": "sliding-window",
        "difficulty": 5,
        "description": (
            "Read a single word and print the length of the longest substring "
            "without any repeating characters."
        ),
        "test_cases": [
            {"stdin": "abcabcbb\n", "expected_stdout": "3"},
            {"stdin": "bbbbb\n", "expected_stdout": "1"},
            {"stdin": "pwwkew\n", "expected_stdout": "3"},
        ],
    },
]


# Maps a candidate's likely required skills/keywords to relevant coding
# topics above - crude keyword matching, but effective enough to bias
# problem selection toward a candidate's actual JD without needing a
# full search index for a list this small.
SKILL_TO_TOPICS = {
    "python": ["basics", "strings", "arrays", "hashmaps"],
    "java": ["arrays", "hashmaps", "recursion", "stacks"],
    "data": ["arrays", "hashmaps"],
    "data analysis": ["arrays", "hashmaps"],
    "sql": ["hashmaps"],
    "algorithm": ["recursion", "sorting", "searching", "sliding-window"],
    "dsa": ["recursion", "sorting", "searching", "sliding-window", "stacks"],
    "software": ["recursion", "sorting", "searching", "stacks", "hashmaps"],
    "backend": ["hashmaps", "stacks", "recursion"],
}


def _relevant_topics(profile: dict) -> set[str]:
    keywords = [k.lower() for k in profile.get("skill_gaps", []) + profile.get("required_skills", [])]
    topics = set()
    for kw in keywords:
        for skill_key, mapped_topics in SKILL_TO_TOPICS.items():
            if skill_key in kw:
                topics.update(mapped_topics)
    return topics


def pick_problem(profile: dict, difficulty: int, excluded_ids: list[str]) -> dict | None:
    """
    Picks the best-matching unattempted coding problem for this candidate:
    prefers a topic relevant to their JD/skill_gaps, then the closest
    difficulty match. Falls back to any unattempted problem if no topic
    match is found. Returns None only if every problem has been attempted.
    """
    candidates = [p for p in CODING_PROBLEMS if p["id"] not in excluded_ids]
    if not candidates:
        return None

    relevant = _relevant_topics(profile)
    preferred = [p for p in candidates if p["topic"] in relevant] or candidates

    # closest difficulty match among the preferred set
    preferred.sort(key=lambda p: abs(p["difficulty"] - difficulty))
    return preferred[0]
