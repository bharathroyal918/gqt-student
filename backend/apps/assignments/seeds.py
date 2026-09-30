"""Seed initial production-grade coding challenges with starter codes and test cases."""

from decimal import Decimal
from typing import List

from apps.assignments.models import CodingQuestion, TestCase
from apps.courses.models import Course
from apps.modules.models import Module
from apps.modules.services import StudentModuleService


SEED_QUESTIONS = [
    {
        "module_order": 1,  # Data Types
        "title": "Two Sum Optimal Hash Map",
        "slug": "two-sum-optimal-hash-map",
        "difficulty": CodingQuestion.DifficultyChoices.EASY,
        "points": Decimal("50.00"),
        "time_limit_seconds": Decimal("2.00"),
        "memory_limit_mb": 128,
        "problem_statement": """### Problem Statement
Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`.
You may assume that each input would have exactly one solution, and you may not use the same element twice.

### Input Format
- First line contains space-separated integers representing `nums`.
- Second line contains a single integer `target`.

### Output Format
- Return a space-separated pair of 0-based indices `[i, j]` with `i < j`.

### Constraints
- $2 \\le nums.length \\le 10^4$
- $-10^9 \\le nums[i] \\le 10^9$
- $-10^9 \\le target \\le 10^9$
- Exactly one valid answer exists.

### Examples
**Example 1:**
- Input:
```
2 7 11 15
9
```
- Output: `0 1`
""",
        "allowed_languages": ["python", "java", "c", "cpp", "javascript"],
        "starter_code": {
            "python": "def two_sum(nums: list[int], target: int) -> list[int]:\n    # Write your optimal O(N) solution here\n    seen = {}\n    for i, n in enumerate(nums):\n        diff = target - n\n        if diff in seen:\n            return [seen[diff], i]\n        seen[n] = i\n    return []\n\nif __name__ == '__main__':\n    import sys\n    lines = sys.stdin.read().splitlines()\n    if lines:\n        nums = list(map(int, lines[0].split()))\n        target = int(lines[1])\n        res = two_sum(nums, target)\n        print(' '.join(map(str, res)))",
            "javascript": "function twoSum(nums, target) {\n    const map = new Map();\n    for (let i = 0; i < nums.length; i++) {\n        const complement = target - nums[i];\n        if (map.has(complement)) return [map.get(complement), i];\n        map.set(nums[i], i);\n    }\n    return [];\n}\n\nconst fs = require('fs');\nconst input = fs.readFileSync('/dev/stdin', 'utf-8').trim().split('\\n');\nif (input.length >= 2) {\n    const nums = input[0].trim().split(/\\s+/).map(Number);\n    const target = Number(input[1]);\n    console.log(twoSum(nums, target).join(' '));\n}",
            "java": "import java.util.*;\n\npublic class Solution {\n    public static int[] twoSum(int[] nums, int target) {\n        Map<Integer, Integer> map = new HashMap<>();\n        for (int i = 0; i < nums.length; i++) {\n            int comp = target - nums[i];\n            if (map.containsKey(comp)) return new int[]{map.get(comp), i};\n            map.put(nums[i], i);\n        }\n        return new int[]{};\n    }\n\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNextLine()) {\n            String[] parts = sc.nextLine().trim().split(\"\\\\s+\");\n            int[] nums = new int[parts.length];\n            for (int i = 0; i < parts.length; i++) nums[i] = Integer.parseInt(parts[i]);\n            int target = sc.nextInt();\n            int[] res = twoSum(nums, target);\n            System.out.println(res[0] + \" \" + res[1]);\n        }\n    }\n}",
            "cpp": "#include <iostream>\n#include <vector>\n#include <unordered_map>\n#include <sstream>\nusing namespace std;\n\nvector<int> twoSum(vector<int>& nums, int target) {\n    unordered_map<int, int> seen;\n    for (int i = 0; i < nums.size(); i++) {\n        int comp = target - nums[i];\n        if (seen.count(comp)) return {seen[comp], i};\n        seen[nums[i]] = i;\n    }\n    return {};\n}\n\nint main() {\n    string line;\n    if (getline(cin, line)) {\n        stringstream ss(line);\n        int val, target;\n        vector<int> nums;\n        while (ss >> val) nums.push_back(val);\n        cin >> target;\n        auto res = twoSum(nums, target);\n        cout << res[0] << \" \" << res[1] << endl;\n    }\n    return 0;\n}",
            "c": "#include <stdio.h>\n#include <stdlib.h>\n\nint main() {\n    int nums[10000];\n    int n = 0, target;\n    while (scanf(\"%d\", &nums[n]) == 1) {\n        char c = getchar();\n        n++;\n        if (c == '\\n' || c == EOF) break;\n    }\n    if (scanf(\"%d\", &target) == 1) {\n        for (int i = 0; i < n; i++) {\n            for (int j = i + 1; j < n; j++) {\n                if (nums[i] + nums[j] == target) {\n                    printf(\"%d %d\\n\", i, j);\n                    return 0;\n                }\n            }\n        }\n    }\n    return 0;\n}",
        },
        "test_cases": [
            {"input": "2 7 11 15\n9", "output": "0 1", "is_visible": True, "order": 1},
            {"input": "3 2 4\n6", "output": "1 2", "is_visible": True, "order": 2},
            {"input": "3 3\n6", "output": "0 1", "is_visible": False, "order": 3},
            {"input": "100 200 500 800\n700", "output": "1 2", "is_visible": False, "order": 4},
        ],
    },
    {
        "module_order": 4,  # Strings
        "title": "Valid Palindrome with Alphanumeric Normalization",
        "slug": "valid-palindrome-alphanumeric",
        "difficulty": CodingQuestion.DifficultyChoices.EASY,
        "points": Decimal("50.00"),
        "time_limit_seconds": Decimal("2.00"),
        "memory_limit_mb": 128,
        "problem_statement": """### Problem Statement
A phrase is a palindrome if, after converting all uppercase letters into lowercase letters and removing all non-alphanumeric characters, it reads the same forward and backward.

Given a string `s`, return `true` if it is a palindrome, or `false` otherwise.

### Input Format
- A single string line containing `s`.

### Output Format
- Print `true` or `false`.

### Constraints
- $1 \\le s.length \\le 2 \\times 10^5$
- `s` consists only of printable ASCII characters.

### Examples
- Input: `A man, a plan, a canal: Panama`
- Output: `true`
""",
        "allowed_languages": ["python", "java", "c", "cpp", "javascript"],
        "starter_code": {
            "python": "def is_palindrome(s: str) -> bool:\n    clean = [c.lower() for c in s if c.isalnum()]\n    return clean == clean[::-1]\n\nif __name__ == '__main__':\n    import sys\n    line = sys.stdin.read().strip()\n    print(str(is_palindrome(line)).lower())",
            "javascript": "function isPalindrome(s) {\n    const clean = s.toLowerCase().replace(/[^a-z0-9]/g, '');\n    return clean === clean.split('').reverse().join('');\n}\nconst fs = require('fs');\nconst input = fs.readFileSync('/dev/stdin', 'utf-8').trim();\nconsole.log(isPalindrome(input));",
            "java": "import java.util.*;\npublic class Solution {\n    public static boolean isPalindrome(String s) {\n        String clean = s.replaceAll(\"[^a-zA-Z0-9]\", \"\").toLowerCase();\n        return clean.equals(new StringBuilder(clean).reverse().toString());\n    }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNextLine()) System.out.println(isPalindrome(sc.nextLine()));\n    }\n}",
            "cpp": "#include <iostream>\n#include <string>\n#include <cctype>\nusing namespace std;\nbool isPalindrome(string s) {\n    string clean = \"\";\n    for (char c : s) if (isalnum(c)) clean += tolower(c);\n    int l = 0, r = clean.length() - 1;\n    while (l < r) if (clean[l++] != clean[r--]) return false;\n    return true;\n}\nint main() {\n    string s;\n    if (getline(cin, s)) cout << (isPalindrome(s) ? \"true\" : \"false\") << endl;\n    return 0;\n}",
            "c": "#include <stdio.h>\n#include <string.h>\n#include <ctype.h>\nint main() {\n    char s[200000];\n    if (fgets(s, sizeof(s), stdin)) {\n        int l = 0, r = strlen(s) - 1;\n        while (l < r) {\n            while (l < r && !isalnum(s[l])) l++;\n            while (l < r && !isalnum(s[r])) r--;\n            if (tolower(s[l]) != tolower(s[r])) { printf(\"false\\n\"); return 0; }\n            l++; r--;\n        }\n        printf(\"true\\n\");\n    }\n    return 0;\n}",
        },
        "test_cases": [
            {"input": "A man, a plan, a canal: Panama", "output": "true", "is_visible": True, "order": 1},
            {"input": "race a car", "output": "false", "is_visible": True, "order": 2},
            {"input": " ", "output": "true", "is_visible": False, "order": 3},
            {"input": "0P", "output": "false", "is_visible": False, "order": 4},
        ],
    },
    {
        "module_order": 5,  # Lists
        "title": "Valid Parentheses Stack Evaluation",
        "slug": "valid-parentheses-stack",
        "difficulty": CodingQuestion.DifficultyChoices.MEDIUM,
        "points": Decimal("75.00"),
        "time_limit_seconds": Decimal("2.00"),
        "memory_limit_mb": 128,
        "problem_statement": """### Problem Statement
Given a string `s` containing just the characters `'('`, `')'`, `'{'`, `'}'`, `'['` and `']'`, determine if the input string is valid.

An input string is valid if:
1. Open brackets must be closed by the same type of brackets.
2. Open brackets must be closed in the correct order.
3. Every close bracket has a corresponding open bracket of the same type.

### Input Format
- A single string `s`.

### Output Format
- Print `true` or `false`.

### Constraints
- $1 \\le s.length \\le 10^4$
- `s` consists of parentheses only `'()[]{}'`.

### Examples
- Input: `()[]{}`
- Output: `true`
- Input: `(]`
- Output: `false`
""",
        "allowed_languages": ["python", "java", "c", "cpp", "javascript"],
        "starter_code": {
            "python": "def is_valid(s: str) -> bool:\n    stack = []\n    mapping = {')': '(', '}': '{', ']': '['}\n    for char in s:\n        if char in mapping:\n            top = stack.pop() if stack else '#'\n            if mapping[char] != top:\n                return False\n        else:\n            stack.append(char)\n    return not stack\n\nif __name__ == '__main__':\n    import sys\n    s = sys.stdin.read().strip()\n    print(str(is_valid(s)).lower())",
            "javascript": "function isValid(s) {\n    const stack = [];\n    const map = { ')': '(', '}': '{', ']': '[' };\n    for (const char of s) {\n        if (map[char]) {\n            if (stack.pop() !== map[char]) return false;\n        } else {\n            stack.push(char);\n        }\n    }\n    return stack.length === 0;\n}\nconst fs = require('fs');\nconsole.log(isValid(fs.readFileSync('/dev/stdin', 'utf-8').trim()));",
            "java": "import java.util.*;\npublic class Solution {\n    public static boolean isValid(String s) {\n        Deque<Character> stack = new ArrayDeque<>();\n        for (char c : s.toCharArray()) {\n            if (c == '(') stack.push(')');\n            else if (c == '{') stack.push('}');\n            else if (c == '[') stack.push(']');\n            else if (stack.isEmpty() || stack.pop() != c) return false;\n        }\n        return stack.isEmpty();\n    }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNext()) System.out.println(isValid(sc.next()));\n    }\n}",
            "cpp": "#include <iostream>\n#include <stack>\n#include <string>\nusing namespace std;\nbool isValid(string s) {\n    stack<char> st;\n    for (char c : s) {\n        if (c == '(' || c == '{' || c == '[') st.push(c);\n        else {\n            if (st.empty()) return false;\n            if (c == ')' && st.top() != '(') return false;\n            if (c == '}' && st.top() != '{') return false;\n            if (c == ']' && st.top() != '[') return false;\n            st.pop();\n        }\n    }\n    return st.empty();\n}\nint main() {\n    string s;\n    if (cin >> s) cout << (isValid(s) ? \"true\" : \"false\") << endl;\n    return 0;\n}",
            "c": "#include <stdio.h>\n#include <string.h>\n#include <stdbool.h>\nint main() {\n    char s[10005], stack[10005];\n    int top = 0;\n    if (scanf(\"%s\", s) == 1) {\n        for (int i = 0; s[i]; i++) {\n            if (s[i] == '(' || s[i] == '{' || s[i] == '[') stack[top++] = s[i];\n            else {\n                if (top == 0) { printf(\"false\\n\"); return 0; }\n                char prev = stack[--top];\n                if (s[i] == ')' && prev != '(') { printf(\"false\\n\"); return 0; }\n                if (s[i] == '}' && prev != '{') { printf(\"false\\n\"); return 0; }\n                if (s[i] == ']' && prev != '[') { printf(\"false\\n\"); return 0; }\n            }\n        }\n        printf(\"%s\\n\", top == 0 ? \"true\" : \"false\");\n    }\n    return 0;\n}",
        },
        "test_cases": [
            {"input": "()[]{}", "output": "true", "is_visible": True, "order": 1},
            {"input": "(]", "output": "false", "is_visible": True, "order": 2},
            {"input": "([{}])", "output": "true", "is_visible": False, "order": 3},
            {"input": "[(])", "output": "false", "is_visible": False, "order": 4},
        ],
    },
]


def seed_coding_questions():
    """Idempotently seeds coding questions across curriculum modules."""
    course, _ = Course.objects.get_or_create(
        slug="python-mastery-track",
        defaults={
            "title": "Python & Algorithms Track",
            "description": "Master algorithmic thinking, standard libraries, and high-performance computing.",
            "is_published": True,
        },
    )
    modules = StudentModuleService.ensure_default_curriculum(course)
    mod_map = {m.order_index: m for m in modules}

    for item in SEED_QUESTIONS:
        mod = mod_map.get(item["module_order"])
        if not mod:
            continue

        question, _ = CodingQuestion.objects.get_or_create(
            module=mod,
            slug=item["slug"],
            defaults={
                "title": item["title"],
                "difficulty": item["difficulty"],
                "points": item["points"],
                "time_limit_seconds": item["time_limit_seconds"],
                "memory_limit_mb": item["memory_limit_mb"],
                "problem_statement": item["problem_statement"],
                "allowed_languages": item["allowed_languages"],
                "starter_code": item["starter_code"],
                "order": 1,
                "is_active": True,
            },
        )

        for tc in item["test_cases"]:
            TestCase.objects.get_or_create(
                question=question,
                order=tc["order"],
                defaults={
                    "input_data": tc["input"],
                    "expected_output": tc["output"],
                    "is_visible": tc["is_visible"],
                    "weight": Decimal("1.00"),
                },
            )
