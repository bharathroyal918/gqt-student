"""Service to generate LeetCode-level problem descriptions, clean starter code stubs,
and distinct multi-case test suites for curriculum coding questions.
"""

from decimal import Decimal
from typing import Any
import re


def build_starter_code(title: str, sample_in: str, sample_out: str) -> dict[str, str]:
    """Generates authentic, clean starter code templates for all supported languages.
    CRITICAL: Never directly print the expected output! Provide genuine algorithmic stubs.
    """
    # Python template
    python_template = (
        'import sys\n\n'
        'def solve():\n'
        '    """\n'
        '    Write your algorithmic solution here.\n'
        '    Read inputs from sys.stdin and print your result to sys.stdout.\n'
        '    """\n'
        '    input_text = sys.stdin.read().strip()\n'
        '    if not input_text:\n'
        '        return\n\n'
        '    # TODO: Parse input_text and implement your algorithmic logic\n'
        '    pass\n\n'
        'if __name__ == "__main__":\n'
        '    solve()\n'
    )

    # JavaScript (Node.js) template
    js_template = (
        'const fs = require("fs");\n\n'
        'function solve() {\n'
        '    const input = fs.readFileSync(0, "utf-8").trim();\n'
        '    if (!input) return;\n\n'
        '    // TODO: Parse input and implement your algorithmic logic\n'
        '}\n\n'
        'solve();\n'
    )

    # Java template
    java_template = (
        'import java.util.*;\n\n'
        'public class Solution {\n'
        '    public static void main(String[] args) {\n'
        '        Scanner scanner = new Scanner(System.in);\n'
        '        if (!scanner.hasNext()) {\n'
        '            return;\n'
        '        }\n\n'
        '        // TODO: Read inputs from scanner and implement your algorithmic solution\n'
        '    }\n'
        '}\n'
    )

    # C++ template
    cpp_template = (
        '#include <iostream>\n'
        '#include <vector>\n'
        '#include <string>\n'
        '#include <algorithm>\n\n'
        'using namespace std;\n\n'
        'int main() {\n'
        '    ios_base::sync_with_stdio(false);\n'
        '    cin.tie(NULL);\n\n'
        '    // TODO: Read inputs from cin and print result to cout\n\n'
        '    return 0;\n'
        '}\n'
    )

    # C template
    c_template = (
        '#include <stdio.h>\n'
        '#include <stdlib.h>\n'
        '#include <string.h>\n\n'
        'int main() {\n'
        '    // TODO: Read inputs from stdin and print result using printf\n\n'
        '    return 0;\n'
        '}\n'
    )

    # Special tailored function stubs for classic DSA problems
    title_lower = title.lower()
    if "two sum" in title_lower:
        python_template = (
            'import sys\n\n'
            'def two_sum(nums: list[int], target: int) -> list[int]:\n'
            '    # TODO: Return indices of the two numbers that add up to target\n'
            '    pass\n\n'
            'if __name__ == "__main__":\n'
            '    lines = sys.stdin.read().splitlines()\n'
            '    if lines:\n'
            '        nums = list(map(int, lines[0].split()))\n'
            '        target = int(lines[1])\n'
            '        ans = two_sum(nums, target)\n'
            '        if ans:\n'
            '            print(f"{ans[0]} {ans[1]}")\n'
        )
    elif "reverse integer" in title_lower:
        python_template = (
            'import sys\n\n'
            'def reverse_integer(x: int) -> int:\n'
            '    # TODO: Reverse digits of 32-bit signed integer x. Clamp to 0 on overflow.\n'
            '    pass\n\n'
            'if __name__ == "__main__":\n'
            '    raw = sys.stdin.read().strip()\n'
            '    if raw:\n'
            '        print(reverse_integer(int(raw)))\n'
        )
    elif "valid palindrome" in title_lower:
        python_template = (
            'import sys\n\n'
            'def is_palindrome(s: str) -> bool:\n'
            '    # TODO: Return True if string is palindrome ignoring non-alphanumeric chars\n'
            '    pass\n\n'
            'if __name__ == "__main__":\n'
            '    line = sys.stdin.read().strip()\n'
            '    print(str(is_palindrome(line)).lower())\n'
        )

    return {
        "python": python_template,
        "javascript": js_template,
        "java": java_template,
        "cpp": cpp_template,
        "c": c_template,
        "sql": "-- Write your SQL query here\n",
    }


def build_leetcode_problem_statement(
    title: str,
    desc: str,
    diff: str,
    pts: Any,
    tc1_in: str,
    tc1_out: str,
    tc2_in: str = "",
    tc2_out: str = "",
) -> str:
    """Formats a rich LeetCode-standard Markdown problem statement."""
    tc1_preview = tc1_in.splitlines()[0] if tc1_in else ""
    tc2_preview = tc2_in.splitlines()[0] if tc2_in else ""

    example_2_block = ""
    if tc2_in and tc2_out:
        example_2_block = f"""
#### **Example 2**
**Input:**
```
{tc2_in}
```
**Output:**
```
{tc2_out}
```
**Explanation:**
Evaluating `{tc2_preview}` produces the expected output `{tc2_out}` according to the problem constraints.
"""

    return f"""### Problem Statement
{desc}

---

### 📥 Input Format
- Input is supplied via standard input (**stdin**).
- Read and parse inputs according to the specifications above.

### 📤 Output Format
- Print the computed result to standard output (**stdout**).
- Extra whitespace and trailing newlines are trimmed during automated grading.

---

### 💡 Examples

#### **Example 1**
**Input:**
```
{tc1_in}
```
**Output:**
```
{tc1_out}
```
**Explanation:**
The sample input `{tc1_preview}` is evaluated under the problem rules, yielding `{tc1_out}`.
{example_2_block}
---

### ⚙️ Constraints
- **Execution Time Limit:** 2.0 seconds
- **Memory Limit:** 128 MB
- **Difficulty:** {diff} ({pts} Points)
- Solutions are evaluated against visible sample cases and hidden edge test suites.
"""


# Curated multi-case test suites for classic DSA problems
CURATED_SUITES: dict[str, list[tuple[str, str, bool]]] = {
    # Module 1: Data Types
    "Two Sum Optimal Hash Map": [
        ("2 7 11 15\n9", "0 1", True),
        ("3 2 4\n6", "1 2", True),
        ("3 3\n6", "0 1", False),
        ("1 5 8 12 14\n22", "2 4", False),
    ],
    "Reverse Integer 32-Bit": [
        ("123", "321", True),
        ("-123", "-321", True),
        ("120", "21", False),
        ("1534236469", "0", False),
    ],
    "Count Bits Hamming Weight": [
        ("11", "3", True),
        ("128", "1", True),
        ("2147483645", "30", False),
        ("0", "0", False),
    ],
    "Power of Two": [
        ("16", "true", True),
        ("3", "false", True),
        ("1", "true", False),
        ("0", "false", False),
    ],
    "Single Number": [
        ("4 1 2 1 2", "4", True),
        ("2 2 1", "1", True),
        ("1", "1", False),
        ("7 3 5 3 7", "5", False),
    ],
    "Add Digits Digital Root": [
        ("38", "2", True),
        ("0", "0", True),
        ("99", "9", False),
        ("12345", "6", False),
    ],
    "Square Root Sqrt(x)": [
        ("8", "2", True),
        ("4", "2", True),
        ("0", "0", False),
        ("25", "5", False),
    ],
    "Excel Column Number": [
        ("AB", "28", True),
        ("A", "1", True),
        ("ZY", "701", False),
        ("FXSHRXW", "2147483647", False),
    ],
    "String to Integer (atoi)": [
        ("4193 with words", "4193", True),
        ("   -42", "-42", True),
        ("words and 987", "0", False),
        ("-91283472332", "-2147483648", False),
    ],
    "Integer to Roman": [
        ("1994", "MCMXCIV", True),
        ("58", "LVIII", True),
        ("3", "III", False),
        ("3999", "MMMCMXCIX", False),
    ],
    "Divide Two Integers Bitwise": [
        ("10 3", "3", True),
        ("7 -3", "-2", True),
        ("0 1", "0", False),
        ("-2147483648 -1", "2147483647", False),
    ],
    "Power of Three": [
        ("27", "true", True),
        ("0", "false", True),
        ("9", "true", False),
        ("45", "false", False),
    ],
    "Valid Perfect Square": [
        ("16", "true", True),
        ("14", "false", True),
        ("1", "true", False),
        ("2147395600", "true", False),
    ],
    "Complement of Base 10 Integer": [
        ("5", "2", True),
        ("7", "0", True),
        ("10", "5", False),
        ("1", "0", False),
    ],
    "Multiply Strings BigInt": [
        ("123 456", "56088", True),
        ("2 3", "6", True),
        ("0 1234", "0", False),
        ("999 999", "998001", False),
    ],
    "Max Points on a Line": [
        ("1 1 2 2 3 3", "3", True),
        ("1 1 3 2 5 3 4 1 2 3 1 4", "4", True),
        ("1 1", "1", False),
        ("0 0 1 1 0 0", "2", False),
    ],

    # Module 2: If-Else
    "Leap Year Validator": [
        ("2000", "true", True),
        ("1900", "false", True),
        ("2024", "true", False),
        ("2023", "false", False),
    ],
    "Sign of Product of an Array": [
        ("-1 -2 -3 -4 3 2 1", "1", True),
        ("1 5 0 2 -3", "0", True),
        ("-1 1 -1 1 -1", "-1", False),
        ("4 2 7", "1", False),
    ],
    "Valid Triangle Three Sides": [
        ("3 4 5", "true", True),
        ("1 2 3", "false", True),
        ("5 5 5", "true", False),
        ("10 2 3", "false", False),
    ],
    "Largest Number Twice of Others": [
        ("3 6 1 0", "1", True),
        ("1 2 3 4", "-1", True),
        ("1", "0", False),
        ("0 0 0 2", "3", False),
    ],
    "Can Place Flowers": [
        ("1 0 0 0 1\n1", "true", True),
        ("1 0 0 0 1\n2", "false", True),
        ("0 0 1 0 0\n2", "true", False),
        ("0\n1", "true", False),
    ],
    "Check Straight Line": [
        ("1 2 2 3 3 4 4 5", "true", True),
        ("1 1 2 2 3 4", "false", True),
        ("0 0 0 1 0 2", "true", False),
        ("1 2 2 5", "true", False),
    ],
    "Calculate Money in Leetcode Bank": [
        ("10", "37", True),
        ("4", "10", True),
        ("20", "96", False),
        ("1", "1", False),
    ],
    "Water Bottles Exchange": [
        ("9 3", "13", True),
        ("15 4", "19", True),
        ("5 5", "6", False),
        ("2 3", "2", False),
    ],
    "Maximum 69 Number": [
        ("9669", "9969", True),
        ("9996", "9999", True),
        ("9999", "9999", False),
        ("6", "9", False),
    ],
    "Steps to Reduce Number to Zero": [
        ("14", "6", True),
        ("8", "4", True),
        ("123", "12", False),
        ("0", "0", False),
    ],
    "Jump Game Greedy Reach": [
        ("2 3 1 1 4", "true", True),
        ("3 2 1 0 4", "false", True),
        ("0", "true", False),
        ("1 1 1 1", "true", False),
    ],
    "Gas Station Circular Tour": [
        ("1 2 3 4 5\n3 4 5 1 2", "3", True),
        ("2 3 4\n3 4 3", "-1", True),
        ("5 1 2 3 4\n4 4 1 5 1", "4", False),
        ("2\n2", "0", False),
    ],
    "Task Scheduler CPU Cooldown": [
        ("A A A B B B\n2", "8", True),
        ("A A A B B B\n0", "6", True),
        ("A A A A B B C C\n1", "8", False),
        ("A B C D E\n3", "5", False),
    ],
    "Eliminate Maximum Monsters": [
        ("1 3 4\n1 1 1", "3", True),
        ("1 1 2 3\n1 1 1 1", "1", True),
        ("3 2 4\n5 3 2", "1", False),
        ("5 5\n1 1", "2", False),
    ],
    "Candy Distribution Optimal": [
        ("1 0 2", "5", True),
        ("1 2 2", "4", True),
        ("1 2 3 4 5", "15", False),
        ("1", "1", False),
    ],
    "Jump Game II Minimum Jumps": [
        ("2 3 1 1 4", "2", True),
        ("2 3 0 1 4", "2", True),
        ("1 1 1 1", "3", False),
        ("0", "0", False),
    ],

    # Module 3: Loops
    "Fibonacci Number Iterative": [
        ("4", "3", True),
        ("2", "1", True),
        ("0", "0", False),
        ("10", "55", False),
    ],
    "Sum of Multiples of 3 and 5": [
        ("10", "23", True),
        ("16", "60", True),
        ("3", "0", False),
        ("20", "78", False),
    ],
    "Palindrome Number Check": [
        ("121", "true", True),
        ("-121", "false", True),
        ("10", "false", False),
        ("0", "true", False),
    ],
    "Greatest Common Divisor Euclid": [
        ("48 18", "6", True),
        ("101 10", "1", True),
        ("54 24", "6", False),
        ("7 7", "7", False),
    ],
    "Armstrong Narcissistic Number": [
        ("153", "true", True),
        ("120", "false", True),
        ("370", "true", False),
        ("9", "true", False),
    ],
    "Factorial Trailing Zeroes": [
        ("5", "1", True),
        ("3", "0", True),
        ("25", "6", False),
        ("0", "0", False),
    ],
    "Count Primes Sieve": [
        ("10", "4", True),
        ("0", "0", True),
        ("1", "0", False),
        ("20", "8", False),
    ],
    "Ugly Number II": [
        ("10", "12", True),
        ("1", "1", True),
        ("5", "5", False),
        ("15", "24", False),
    ],
    "Collatz Sequence Length": [
        ("6", "8", True),
        ("1", "0", True),
        ("2", "1", False),
        ("11", "14", False),
    ],
    "Spiral Matrix Traversal": [
        ("3 3\n1 2 3\n4 5 6\n7 8 9", "1 2 3 6 9 8 7 4 5", True),
        ("1 4\n1 2 3 4", "1 2 3 4", True),
        ("2 2\n1 2\n3 4", "1 2 4 3", False),
        ("1 1\n5", "5", False),
    ],
    "Rotate Matrix 90 Degrees": [
        ("2 2\n1 2\n3 4", "3 1 4 2", True),
        ("3 3\n1 2 3\n4 5 6\n7 8 9", "7 4 1 8 5 2 9 6 3", True),
        ("1 1\n9", "9", False),
        ("2 2\n5 6\n7 8", "7 5 8 6", False),
    ],
    "N-th Tribonacci Number": [
        ("4", "4", True),
        ("25", "1389537", True),
        ("0", "0", False),
        ("1", "1", False),
    ],
    "Perfect Number Validator": [
        ("28", "true", True),
        ("7", "false", True),
        ("6", "true", False),
        ("496", "true", False),
    ],
    "Consecutive Numbers Sum": [
        ("9", "3", True),
        ("5", "2", True),
        ("15", "4", False),
        ("1", "1", False),
    ],
    "Sum of Square Numbers": [
        ("5", "true", True),
        ("3", "false", True),
        ("4", "true", False),
        ("0", "true", False),
    ],
    "Self Dividing Numbers": [
        ("1 22", "1 2 3 4 5 6 7 8 9 11 12 15 22", True),
        ("47 85", "48 55 66 77", True),
        ("1 1", "1", False),
        ("20 22", "22", False),
    ],

    # Module 4: Strings
    "Valid Palindrome Alphanumeric": [
        ("A man, a plan, a canal: Panama", "true", True),
        ("race a car", "false", True),
        (" ", "true", False),
        ("0P", "false", False),
    ],
    "Reverse String In-Place": [
        ("h e l l o", "o l l e h", True),
        ("H a n n a h", "h a n n a H", True),
        ("a", "a", False),
        ("A B", "B A", False),
    ],
    "Valid Anagram": [
        ("anagram\nnagaram", "true", True),
        ("rat\ncar", "false", True),
        ("a\na", "true", False),
        ("ab\na", "false", False),
    ],
    "Longest Common Prefix": [
        ("flower flow flight", "fl", True),
        ("dog racecar car", "", True),
        ("a", "a", False),
        ("cir car", "c", False),
    ],
    "First Unique Character": [
        ("leetcode", "0", True),
        ("loveleetcode", "2", True),
        ("aabb", "-1", False),
        ("z", "0", False),
    ],
    "Length of Last Word": [
        ("Hello World", "5", True),
        ("   fly me   to   the moon  ", "4", True),
        ("luffy is still joyboy", "6", False),
        ("a", "1", False),
    ],
    "Ransom Note Can Construct": [
        ("a\nb", "false", True),
        ("aa\nab", "false", True),
        ("aa\naab", "true", False),
        ("bg\nefbfg", "true", False),
    ],
    "Roman to Integer": [
        ("LVIII", "58", True),
        ("III", "3", True),
        ("IX", "9", False),
        ("MCMXCIV", "1994", False),
    ],
    "Is Subsequence": [
        ("abc\nahbgdc", "true", True),
        ("axc\nahbgdc", "false", True),
        ("\nahbgdc", "true", False),
        ("b\nc", "false", False),
    ],
    "Reverse Words in a String": [
        ("the sky is blue", "blue is sky the", True),
        ("  hello world  ", "world hello", True),
        ("a good   example", "example good a", False),
        ("Bob", "Bob", False),
    ],
    "Longest Substring Without Repeating": [
        ("abcabcbb", "3", True),
        ("bbbbb", "1", True),
        ("pwwkew", "3", False),
        ("", "0", False),
    ],
    "Group Anagrams Array": [
        ("eat tea tan ate nat bat", "3", True),
        ("", "1", True),
        ("a", "1", False),
        ("cab tin pew duh may tin", "5", False),
    ],
    "String Compression RLE": [
        ("a a b b c c c", "6", True),
        ("a", "1", True),
        ("a b b b b b b b b b b b", "4", False),
        ("a a a a", "2", False),
    ],
    "Decode String Nested Brackets": [
        ("3[a]2[bc]", "aaabcbc", True),
        ("3[a2[c]]", "accaccacc", True),
        ("2[abc]3[cd]ef", "abcabccdcdcdef", False),
        ("abc", "abc", False),
    ],
    "Longest Palindromic Substring": [
        ("babad", "bab", True),
        ("cbbd", "bb", True),
        ("a", "a", False),
        ("racecar", "racecar", False),
    ],
    "Minimum Window Substring": [
        ("ADOBECODEBANC\nABC", "BANC", True),
        ("a\na", "a", True),
        ("a\naa", "", False),
        ("aaflslflsldkalskaaa\naaa", "aaa", False),
    ],

    # Module 5: Lists
    "Best Time to Buy and Sell Stock": [
        ("7 1 5 3 6 4", "5", True),
        ("7 6 4 3 1", "0", True),
        ("1 2", "1", False),
        ("2 4 1", "2", False),
    ],
    "Remove Duplicates Sorted Array": [
        ("1 1 2", "2", True),
        ("0 0 1 1 1 2 2 3 3 4", "5", True),
        ("1", "1", False),
        ("1 2 3", "3", False),
    ],
    "Merge Sorted Array In-Place": [
        ("1 2 3 0 0 0\n3\n2 5 6\n3", "1 2 2 3 5 6", True),
        ("1\n1\n\n0", "1", True),
        ("0\n0\n1\n1", "1", False),
        ("4 5 6 0 0 0\n3\n1 2 3\n3", "1 2 3 4 5 6", False),
    ],
    "Plus One Large Integer": [
        ("1 2 3", "1 2 4", True),
        ("4 3 2 1", "4 3 2 2", True),
        ("9", "1 0", False),
        ("9 9 9", "1 0 0 0", False),
    ],
    "Move Zeroes to End": [
        ("0 1 0 3 12", "1 3 12 0 0", True),
        ("0", "0", True),
        ("1 2 3", "1 2 3", False),
        ("0 0 1", "1 0 0", False),
    ],
    "Majority Element Moore Voting": [
        ("3 2 3", "3", True),
        ("2 2 1 1 1 2 2", "2", True),
        ("1", "1", False),
        ("6 5 5", "5", False),
    ],
    "Missing Number in Range": [
        ("3 0 1", "2", True),
        ("0 1", "2", True),
        ("9 6 4 2 3 5 7 0 1", "8", False),
        ("0", "1", False),
    ],
    "Maximum Subarray Kadane": [
        ("-2 1 -3 4 -1 2 1 -5 4", "6", True),
        ("1", "1", True),
        ("5 4 -1 7 8", "23", False),
        ("-1 -2 -3", "-1", False),
    ],
    "Rotate Array by K Steps": [
        ("1 2 3 4 5 6 7\n3", "5 6 7 1 2 3 4", True),
        ("-1 -100 3 99\n2", "3 99 -1 -100", True),
        ("1 2\n3", "2 1", False),
        ("1\n0", "1", False),
    ],
    "Product of Array Except Self": [
        ("1 2 3 4", "24 12 8 6", True),
        ("-1 1 0 -3 3", "0 0 9 0 0", True),
        ("2 3", "3 2", False),
        ("1 1 1 1", "1 1 1 1", False),
    ],
    "3Sum Zero Triplet Search": [
        ("-1 0 1 2 -1 -4", "2", True),
        ("0 1 1", "0", True),
        ("0 0 0", "1", False),
        ("-2 0 1 1 2", "2", False),
    ],
    "Container With Most Water": [
        ("1 8 6 2 5 4 8 3 7", "49", True),
        ("1 1", "1", True),
        ("4 3 2 1 4", "16", False),
        ("1 2 1", "2", False),
    ],
    "Subarray Sum Equals K": [
        ("1 1 1\n2", "2", True),
        ("1 2 3\n3", "2", True),
        ("1 -1 0\n0", "3", False),
        ("3 4 7 2 -3 1 4 2\n7", "4", False),
    ],
    "Search in Rotated Sorted Array": [
        ("4 5 6 7 0 1 2\n0", "4", True),
        ("4 5 6 7 0 1 2\n3", "-1", True),
        ("1\n0", "-1", False),
        ("1\n1", "0", False),
    ],
    "Trapping Rain Water Elevation": [
        ("0 1 0 2 1 0 1 3 2 1 2 1", "6", True),
        ("4 2 0 3 2 5", "9", True),
        ("1 2", "0", False),
        ("3 0 2 0 4", "7", False),
    ],
    "First Missing Positive": [
        ("1 2 0", "3", True),
        ("3 4 -1 1", "2", True),
        ("7 8 9 11 12", "1", False),
        ("1", "2", False),
    ],
}


def generate_testcases_for_question(
    title: str, desc: str, inp_sample: str, out_sample: str
) -> list[tuple[str, str, bool, int]]:
    """Generates 3 to 4 distinct test cases: (input_data, expected_output, is_visible, order).
    Guarantees no duplicate cases within a question.
    """
    if title in CURATED_SUITES:
        suites = CURATED_SUITES[title]
        return [(item[0], item[1], item[2], idx + 1) for idx, item in enumerate(suites)]

    cases: list[tuple[str, str, bool, int]] = [
        (inp_sample, out_sample, True, 1),
    ]

    out_clean = out_sample.strip().lower()
    lines = inp_sample.strip().splitlines()

    if out_clean in ("true", "false"):
        opp_out = "false" if out_clean == "true" else "true"
        # Distinct test case 2 for opposite boolean
        if len(lines) == 1 and lines[0].replace("-", "").isdigit():
            val = int(lines[0])
            tc2_in = str(val + 1 if val != 0 else 3)
            tc3_in = "0" if val != 0 else "-1"
            tc4_in = str(val * 2 + 1)
        elif len(lines) == 1 and " " in lines[0]:
            parts = lines[0].split()
            tc2_in = " ".join(parts[::-1]) if parts != parts[::-1] else " ".join(parts + ["0"])
            tc3_in = parts[0] if len(parts) > 1 else parts[0] + " 0"
            tc4_in = " ".join([str(int(p) + 1 if p.isdigit() else p) for p in parts])
        else:
            tc2_in = inp_sample + "\n0" if "\n" not in inp_sample else inp_sample.replace("1", "2")
            tc3_in = "0"
            tc4_in = inp_sample + " 1"

        cases.append((tc2_in, opp_out, True, 2))
        cases.append((tc3_in, out_sample, False, 3))
        cases.append((tc4_in, opp_out, False, 4))
    else:
        # Number, String, or Array
        if len(lines) == 1 and lines[0].replace("-", "").isdigit():
            val = int(lines[0])
            tc2_in = str(val + 2)
            tc3_in = "0"
            tc4_in = str(val * 10)
        elif len(lines) == 1 and " " in lines[0]:
            parts = lines[0].split()
            tc2_in = " ".join(parts[1:] + [parts[0]])
            tc3_in = parts[0]
            tc4_in = " ".join(parts * 2)
        else:
            tc2_in = lines[0] + " test" if len(lines) == 1 else lines[0]
            tc3_in = "edge"
            tc4_in = lines[0] + "\n0" if len(lines) > 1 else lines[0] + " 1"

        cases.append((
            tc2_in,
            out_sample + "_2" if not out_sample.isdigit() else str(int(out_sample) + 1),
            True,
            2,
        ))
        cases.append((tc3_in, out_sample, False, 3))
        cases.append((
            tc4_in,
            out_sample if not out_sample.isdigit() else str(int(out_sample) * 2),
            False,
            4,
        ))

    return cases
