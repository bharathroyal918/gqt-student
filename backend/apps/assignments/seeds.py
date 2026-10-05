"""Seed initial production-grade coding challenges with starter codes and test cases."""

from decimal import Decimal
from typing import List, Dict, Any
from django.utils.text import slugify

from apps.assignments.models import CodingQuestion, TestCase
from apps.courses.models import Course
from apps.modules.models import Module


MODULE_TOPIC_QUESTIONS: Dict[int, List[Dict[str, Any]]] = {
    1: [  # Data Types
        {
            "title": "Two Sum Optimal Hash Map",
            "slug": "two-sum-optimal-hash-map",
            "difficulty": CodingQuestion.DifficultyChoices.EASY,
            "points": Decimal("15.00"),
            "problem": "Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`.\n\n### Input Format\n- First line: space-separated integers `nums`.\n- Second line: integer `target`.\n\n### Output Format\n- Space-separated 0-based indices `i j`.\n\n### Examples\nInput:\n```\n2 7 11 15\n9\n```\nOutput: `0 1`",
            "starter_code": {
                "python": "def two_sum(nums: list[int], target: int) -> list[int]:\n    seen = {}\n    for i, n in enumerate(nums):\n        diff = target - n\n        if diff in seen:\n            return [seen[diff], i]\n        seen[n] = i\n    return []\n\nif __name__ == '__main__':\n    import sys\n    lines = sys.stdin.read().splitlines()\n    if lines:\n        nums = list(map(int, lines[0].split()))\n        target = int(lines[1])\n        print(' '.join(map(str, two_sum(nums, target))))",
                "javascript": "function twoSum(nums, target) {\n    const map = new Map();\n    for (let i = 0; i < nums.length; i++) {\n        const diff = target - nums[i];\n        if (map.has(diff)) return [map.get(diff), i];\n        map.set(nums[i], i);\n    }\n    return [];\n}\nconst fs = require('fs');\nconst lines = fs.readFileSync(0, 'utf-8').trim().split('\\n');\nif (lines.length >= 2) {\n    const nums = lines[0].trim().split(/\\s+/).map(Number);\n    const target = Number(lines[1]);\n    console.log(twoSum(nums, target).join(' '));\n}",
                "java": "import java.util.*;\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNextLine()) {\n            String[] parts = sc.nextLine().trim().split(\"\\\\s+\");\n            int[] nums = new int[parts.length];\n            for (int i = 0; i < parts.length; i++) nums[i] = Integer.parseInt(parts[i]);\n            int target = sc.nextInt();\n            Map<Integer, Integer> map = new HashMap<>();\n            for (int i = 0; i < nums.length; i++) {\n                int diff = target - nums[i];\n                if (map.containsKey(diff)) {\n                    System.out.println(map.get(diff) + \" \" + i);\n                    return;\n                }\n                map.put(nums[i], i);\n            }\n        }\n    }\n}",
                "cpp": "#include <iostream>\n#include <vector>\n#include <unordered_map>\n#include <sstream>\nusing namespace std;\nint main() {\n    string line; if (getline(cin, line)) {\n        stringstream ss(line); int val, target;\n        vector<int> nums; while (ss >> val) nums.push_back(val);\n        cin >> target;\n        unordered_map<int, int> seen;\n        for (int i = 0; i < nums.size(); i++) {\n            int diff = target - nums[i];\n            if (seen.count(diff)) { cout << seen[diff] << \" \" << i << endl; return 0; }\n            seen[nums[i]] = i;\n        }\n    }\n    return 0;\n}",
                "c": "#include <stdio.h>\nint main() {\n    int nums[1000], n = 0, target;\n    while (scanf(\"%d\", &nums[n]) == 1) { n++; if (getchar() == '\\n') break; }\n    if (scanf(\"%d\", &target) == 1) {\n        for (int i = 0; i < n; i++) {\n            for (int j = i + 1; j < n; j++) {\n                if (nums[i] + nums[j] == target) { printf(\"%d %d\\n\", i, j); return 0; }\n            }\n        }\n    }\n    return 0;\n}"
            },
            "test_cases": [
                {"input": "2 7 11 15\n9", "output": "0 1", "is_visible": True, "order": 1},
                {"input": "3 2 4\n6", "output": "1 2", "is_visible": True, "order": 2},
                {"input": "3 3\n6", "output": "0 1", "is_visible": False, "order": 3},
                {"input": "1 5 9 12\n14", "output": "1 2", "is_visible": False, "order": 4},
            ]
        },
        {
            "title": "Reverse Integer 32-Bit",
            "slug": "reverse-integer-32-bit",
            "difficulty": CodingQuestion.DifficultyChoices.MEDIUM,
            "points": Decimal("25.00"),
            "problem": "Given a signed 32-bit integer `x`, return `x` with its digits reversed. If reversing `x` causes the value to go outside $[-2^{31}, 2^{31} - 1]$, return `0`.\n\n### Input Format\n- A single integer `x`.\n\n### Output Format\n- Reversed integer or `0`.",
            "starter_code": {
                "python": "def reverse(x: int) -> int:\n    sign = -1 if x < 0 else 1\n    rev = int(str(abs(x))[::-1]) * sign\n    return rev if -2**31 <= rev <= 2**31 - 1 else 0\n\nif __name__ == '__main__':\n    import sys\n    val = sys.stdin.read().strip()\n    if val:\n        print(reverse(int(val)))",
                "javascript": "function reverse(x) {\n    const sign = x < 0 ? -1 : 1;\n    const rev = parseInt(Math.abs(x).toString().split('').reverse().join('')) * sign;\n    if (rev < -(2**31) || rev > 2**31 - 1) return 0;\n    return rev;\n}\nconst fs = require('fs');\nconst line = fs.readFileSync(0, 'utf-8').trim();\nif (line) console.log(reverse(Number(line)));",
                "java": "import java.util.*;\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNextInt()) {\n            int x = sc.nextInt();\n            long rev = 0;\n            while (x != 0) {\n                rev = rev * 10 + (x % 10);\n                x /= 10;\n            }\n            if (rev < Integer.MIN_VALUE || rev > Integer.MAX_VALUE) System.out.println(0);\n            else System.out.println((int)rev);\n        }\n    }\n}",
                "cpp": "#include <iostream>\n#include <climits>\nusing namespace std;\nint main() {\n    int x; if (cin >> x) {\n        long rev = 0;\n        while (x != 0) { rev = rev * 10 + (x % 10); x /= 10; }\n        if (rev < INT_MIN || rev > INT_MAX) cout << 0 << endl;\n        else cout << rev << endl;\n    }\n    return 0;\n}",
                "c": "#include <stdio.h>\n#include <limits.h>\nint main() {\n    int x; if (scanf(\"%d\", &x) == 1) {\n        long long rev = 0;\n        while (x != 0) { rev = rev * 10 + (x % 10); x /= 10; }\n        if (rev < INT_MIN || rev > INT_MAX) printf(\"0\\n\");\n        else printf(\"%lld\\n\", rev);\n    }\n    return 0;\n}"
            },
            "test_cases": [
                {"input": "123", "output": "321", "is_visible": True, "order": 1},
                {"input": "-123", "output": "-321", "is_visible": True, "order": 2},
                {"input": "120", "output": "21", "is_visible": False, "order": 3},
                {"input": "1534236469", "output": "0", "is_visible": False, "order": 4},
            ]
        },
        {
            "title": "Count Bits Hamming Weight",
            "slug": "count-bits-hamming-weight",
            "difficulty": CodingQuestion.DifficultyChoices.EASY,
            "points": Decimal("15.00"),
            "problem": "Write a function that takes the binary representation of a positive integer and returns the number of set bits (1s) it has.\n\n### Input Format\n- A single positive integer `n`.\n\n### Output Format\n- Number of set bits.",
            "starter_code": {
                "python": "def hammingWeight(n: int) -> int:\n    return bin(n).count('1')\n\nif __name__ == '__main__':\n    import sys\n    inp = sys.stdin.read().strip()\n    if inp:\n        print(hammingWeight(int(inp)))",
                "javascript": "const fs = require('fs');\nconst n = Number(fs.readFileSync(0, 'utf-8').trim());\nconsole.log((n >>> 0).toString(2).replace(/0/g, '').length);",
                "java": "import java.util.*;\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNextLong()) {\n            long n = sc.nextLong();\n            System.out.println(Long.bitCount(n));\n        }\n    }\n}",
                "cpp": "#include <iostream>\nusing namespace std;\nint main() {\n    unsigned int n; if (cin >> n) cout << __builtin_popcount(n) << endl;\n    return 0;\n}",
                "c": "#include <stdio.h>\nint main() {\n    unsigned int n; if (scanf(\"%u\", &n) == 1) {\n        int cnt = 0;\n        while (n) { cnt += (n & 1); n >>= 1; }\n        printf(\"%d\\n\", cnt);\n    }\n    return 0;\n}"
            },
            "test_cases": [
                {"input": "11", "output": "3", "is_visible": True, "order": 1},
                {"input": "128", "output": "1", "is_visible": True, "order": 2},
                {"input": "2147483645", "output": "30", "is_visible": False, "order": 3},
            ]
        },
        {
            "title": "Power of Two Checker",
            "slug": "power-of-two-checker",
            "difficulty": CodingQuestion.DifficultyChoices.EASY,
            "points": Decimal("15.00"),
            "problem": "Given an integer `n`, return `true` if it is a power of two. Otherwise, return `false`.\n\n### Input Format\n- A single integer `n`.\n\n### Output Format\n- `true` or `false`.",
            "starter_code": {
                "python": "def isPowerOfTwo(n: int) -> bool:\n    return n > 0 and (n & (n - 1)) == 0\n\nif __name__ == '__main__':\n    import sys\n    print(str(isPowerOfTwo(int(sys.stdin.read().strip()))).lower())",
                "javascript": "const fs = require('fs');\nconst n = Number(fs.readFileSync(0, 'utf-8').trim());\nconsole.log(n > 0 && (n & (n - 1)) === 0 ? 'true' : 'false');",
                "java": "import java.util.*;\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNextLong()) {\n            long n = sc.nextLong();\n            System.out.println((n > 0 && (n & (n - 1)) == 0) ? \"true\" : \"false\");\n        }\n    }\n}",
                "cpp": "#include <iostream>\nusing namespace std;\nint main() {\n    long long n; if (cin >> n) cout << (n > 0 && (n & (n - 1)) == 0 ? \"true\" : \"false\") << endl;\n    return 0;\n}",
                "c": "#include <stdio.h>\nint main() {\n    long long n; if (scanf(\"%lld\", &n) == 1) {\n        printf(\"%s\\n\", (n > 0 && (n & (n - 1)) == 0) ? \"true\" : \"false\");\n    }\n    return 0;\n}"
            },
            "test_cases": [
                {"input": "1", "output": "true", "is_visible": True, "order": 1},
                {"input": "16", "output": "true", "is_visible": True, "order": 2},
                {"input": "3", "output": "false", "is_visible": True, "order": 3},
                {"input": "1024", "output": "true", "is_visible": False, "order": 4},
            ]
        },
        {
            "title": "Single Number in Pairs",
            "slug": "single-number-in-pairs",
            "difficulty": CodingQuestion.DifficultyChoices.EASY,
            "points": Decimal("15.00"),
            "problem": "Given a non-empty array of integers `nums`, every element appears twice except for one. Find that single one in $O(n)$ time and $O(1)$ extra space.\n\n### Input Format\n- Space-separated integers `nums`.\n\n### Output Format\n- Single integer value.",
            "starter_code": {
                "python": "def singleNumber(nums: list[int]) -> int:\n    res = 0\n    for x in nums: res ^= x\n    return res\n\nif __name__ == '__main__':\n    import sys\n    print(singleNumber(list(map(int, sys.stdin.read().split()))))",
                "javascript": "const fs = require('fs');\nconst nums = fs.readFileSync(0, 'utf-8').trim().split(/\\s+/).map(Number);\nconsole.log(nums.reduce((acc, curr) => acc ^ curr, 0));",
                "java": "import java.util.*;\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int res = 0;\n        while (sc.hasNextInt()) res ^= sc.nextInt();\n        System.out.println(res);\n    }\n}",
                "cpp": "#include <iostream>\nusing namespace std;\nint main() {\n    int val, res = 0;\n    while (cin >> val) res ^= val;\n    cout << res << endl;\n    return 0;\n}",
                "c": "#include <stdio.h>\nint main() {\n    int val, res = 0;\n    while (scanf(\"%d\", &val) == 1) res ^= val;\n    printf(\"%d\\n\", res);\n    return 0;\n}"
            },
            "test_cases": [
                {"input": "2 2 1", "output": "1", "is_visible": True, "order": 1},
                {"input": "4 1 2 1 2", "output": "4", "is_visible": True, "order": 2},
                {"input": "1", "output": "1", "is_visible": False, "order": 3},
                {"input": "7 3 5 3 7", "output": "5", "is_visible": False, "order": 4},
            ]
        },
        {
            "title": "Add Digits Digital Root",
            "slug": "add-digits-digital-root",
            "difficulty": CodingQuestion.DifficultyChoices.EASY,
            "points": Decimal("15.00"),
            "problem": "Given an integer `num`, repeatedly add all its digits until the result has only one digit, and return it in $O(1)$ runtime.\n\n### Input Format\n- A single non-negative integer `num`.\n\n### Output Format\n- Single digit digital root.",
            "starter_code": {
                "python": "def addDigits(num: int) -> int:\n    if num == 0: return 0\n    return 9 if num % 9 == 0 else num % 9\n\nif __name__ == '__main__':\n    import sys\n    print(addDigits(int(sys.stdin.read().strip())))",
                "javascript": "const fs = require('fs');\nconst n = Number(fs.readFileSync(0, 'utf-8').trim());\nconsole.log(n === 0 ? 0 : 1 + (n - 1) % 9);",
                "java": "import java.util.*;\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNextInt()) {\n            int n = sc.nextInt();\n            System.out.println(n == 0 ? 0 : 1 + (n - 1) % 9);\n        }\n    }\n}",
                "cpp": "#include <iostream>\nusing namespace std;\nint main() { int n; if (cin >> n) cout << (n == 0 ? 0 : 1 + (n - 1) % 9) << endl; return 0; }",
                "c": "#include <stdio.h>\nint main() { int n; if (scanf(\"%d\", &n) == 1) printf(\"%d\\n\", n == 0 ? 0 : 1 + (n - 1) % 9); return 0; }"
            },
            "test_cases": [
                {"input": "38", "output": "2", "is_visible": True, "order": 1},
                {"input": "0", "output": "0", "is_visible": True, "order": 2},
                {"input": "199", "output": "1", "is_visible": False, "order": 3},
            ]
        },
        {
            "title": "Integer Square Root Sqrt(x)",
            "slug": "integer-square-root",
            "difficulty": CodingQuestion.DifficultyChoices.EASY,
            "points": Decimal("15.00"),
            "problem": "Given a non-negative integer `x`, return the square root of `x` rounded down to the nearest integer. The returned integer should be non-negative as well.\n\n### Input Format\n- A single non-negative integer `x`.\n\n### Output Format\n- Integer square root.",
            "starter_code": {
                "python": "def mySqrt(x: int) -> int:\n    if x < 2: return x\n    l, r = 1, x // 2\n    while l <= r:\n        mid = (l + r) // 2\n        if mid * mid <= x < (mid + 1) * (mid + 1):\n            return mid\n        elif mid * mid > x:\n            r = mid - 1\n        else:\n            l = mid + 1\n    return r\n\nif __name__ == '__main__':\n    import sys\n    print(mySqrt(int(sys.stdin.read().strip())))",
                "javascript": "const fs = require('fs');\nconst x = Number(fs.readFileSync(0, 'utf-8').trim());\nconsole.log(Math.floor(Math.sqrt(x)));",
                "java": "import java.util.*;\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNextLong()) {\n            long x = sc.nextLong();\n            long r = x;\n            while (r * r > x) r = (r + x / r) / 2;\n            System.out.println(r);\n        }\n    }\n}",
                "cpp": "#include <iostream>\nusing namespace std;\nint main() {\n    long long x; if (cin >> x) {\n        long long r = x;\n        while (r * r > x) r = (r + x / r) / 2;\n        cout << r << endl;\n    }\n    return 0;\n}",
                "c": "#include <stdio.h>\nint main() {\n    long long x; if (scanf(\"%lld\", &x) == 1) {\n        long long r = x;\n        while (r * r > x) r = (r + x / r) / 2;\n        printf(\"%lld\\n\", r);\n    }\n    return 0;\n}"
            },
            "test_cases": [
                {"input": "4", "output": "2", "is_visible": True, "order": 1},
                {"input": "8", "output": "2", "is_visible": True, "order": 2},
                {"input": "16", "output": "4", "is_visible": False, "order": 3},
                {"input": "2147395599", "output": "46339", "is_visible": False, "order": 4},
            ]
        },
        {
            "title": "Excel Sheet Column Number",
            "slug": "excel-sheet-column-number",
            "difficulty": CodingQuestion.DifficultyChoices.EASY,
            "points": Decimal("15.00"),
            "problem": "Given a string `columnTitle` that represents the column title as appears in an Excel sheet, return its corresponding column number.\n\n### Input Format\n- A string `columnTitle` (e.g. `A`, `AB`, `ZY`).\n\n### Output Format\n- Integer column number.",
            "starter_code": {
                "python": "def titleToNumber(columnTitle: str) -> int:\n    res = 0\n    for c in columnTitle.strip():\n        res = res * 26 + (ord(c) - ord('A') + 1)\n    return res\n\nif __name__ == '__main__':\n    import sys\n    print(titleToNumber(sys.stdin.read().strip()))",
                "javascript": "const fs = require('fs');\nconst s = fs.readFileSync(0, 'utf-8').trim();\nlet res = 0;\nfor (let i = 0; i < s.length; i++) res = res * 26 + (s.charCodeAt(i) - 64);\nconsole.log(res);",
                "java": "import java.util.*;\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNext()) {\n            String s = sc.next();\n            int res = 0;\n            for (char c : s.toCharArray()) res = res * 26 + (c - 'A' + 1);\n            System.out.println(res);\n        }\n    }\n}",
                "cpp": "#include <iostream>\n#include <string>\nusing namespace std;\nint main() {\n    string s; if (cin >> s) {\n        long long res = 0;\n        for (char c : s) res = res * 26 + (c - 'A' + 1);\n        cout << res << endl;\n    }\n    return 0;\n}",
                "c": "#include <stdio.h>\nint main() {\n    char s[100]; if (scanf(\"%s\", s) == 1) {\n        long long res = 0;\n        for (int i = 0; s[i]; i++) res = res * 26 + (s[i] - 'A' + 1);\n        printf(\"%lld\\n\", res);\n    }\n    return 0;\n}"
            },
            "test_cases": [
                {"input": "A", "output": "1", "is_visible": True, "order": 1},
                {"input": "AB", "output": "28", "is_visible": True, "order": 2},
                {"input": "ZY", "output": "701", "is_visible": True, "order": 3},
                {"input": "FXSHRXW", "output": "2147483647", "is_visible": False, "order": 4},
            ]
        },
        {
            "title": "String to Integer (atoi)",
            "slug": "string-to-integer-atoi",
            "difficulty": CodingQuestion.DifficultyChoices.MEDIUM,
            "points": Decimal("25.00"),
            "problem": "Implement the `myAtoi(string s)` function, which converts a string to a 32-bit signed integer with whitespace trimming, sign parsing, and 32-bit clamping $[-2^{31}, 2^{31} - 1]$.\n\n### Input Format\n- A line of string `s`.\n\n### Output Format\n- Parsed integer.",
            "starter_code": {
                "python": "def myAtoi(s: str) -> int:\n    s = s.lstrip()\n    if not s: return 0\n    sign = 1\n    if s[0] in ['+', '-']:\n        if s[0] == '-': sign = -1\n        s = s[1:]\n    res = 0\n    for c in s:\n        if not c.isdigit(): break\n        res = res * 10 + int(c)\n    res *= sign\n    return max(-2**31, min(2**31 - 1, res))\n\nif __name__ == '__main__':\n    import sys\n    print(myAtoi(sys.stdin.read().strip()))",
                "javascript": "const fs = require('fs');\nconst s = fs.readFileSync(0, 'utf-8').trim();\nconst parsed = parseInt(s, 10);\nif (isNaN(parsed)) console.log(0);\nelse console.log(Math.max(-(2**31), Math.min(2**31 - 1, parsed)));",
                "java": "import java.util.*;\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNextLine()) {\n            String s = sc.nextLine().trim();\n            if (s.isEmpty()) { System.out.println(0); return; }\n            int i = 0, sign = 1; long res = 0;\n            if (s.charAt(0) == '+' || s.charAt(0) == '-') {\n                if (s.charAt(0) == '-') sign = -1;\n                i++;\n            }\n            while (i < s.length() && Character.isDigit(s.charAt(i))) {\n                res = res * 10 + (s.charAt(i) - '0');\n                if (sign * res > Integer.MAX_VALUE) { System.out.println(Integer.MAX_VALUE); return; }\n                if (sign * res < Integer.MIN_VALUE) { System.out.println(Integer.MIN_VALUE); return; }\n                i++;\n            }\n            System.out.println((int)(sign * res));\n        }\n    }\n}",
                "cpp": "#include <iostream>\n#include <climits>\nusing namespace std;\nint main() {\n    string s; if (getline(cin, s)) {\n        int i = 0; while (i < s.size() && s[i] == ' ') i++;\n        if (i == s.size()) { cout << 0 << endl; return 0; }\n        int sign = 1;\n        if (s[i] == '+' || s[i] == '-') { if (s[i] == '-') sign = -1; i++; }\n        long res = 0;\n        while (i < s.size() && isdigit(s[i])) {\n            res = res * 10 + (s[i] - '0');\n            if (sign * res > INT_MAX) { cout << INT_MAX << endl; return 0; }\n            if (sign * res < INT_MIN) { cout << INT_MIN << endl; return 0; }\n            i++;\n        }\n        cout << sign * res << endl;\n    }\n    return 0;\n}",
                "c": "#include <stdio.h>\n#include <limits.h>\n#include <ctype.h>\nint main() {\n    char s[1000]; if (fgets(s, sizeof(s), stdin)) {\n        int i = 0; while (s[i] == ' ') i++;\n        int sign = 1; if (s[i] == '+' || s[i] == '-') { if (s[i] == '-') sign = -1; i++; }\n        long long res = 0;\n        while (isdigit(s[i])) {\n            res = res * 10 + (s[i] - '0');\n            if (sign * res > INT_MAX) { printf(\"%d\\n\", INT_MAX); return 0; }\n            if (sign * res < INT_MIN) { printf(\"%d\\n\", INT_MIN); return 0; }\n            i++;\n        }\n        printf(\"%lld\\n\", sign * res);\n    }\n    return 0;\n}"
            },
            "test_cases": [
                {"input": "42", "output": "42", "is_visible": True, "order": 1},
                {"input": "   -42", "output": "-42", "is_visible": True, "order": 2},
                {"input": "4193 with words", "output": "4193", "is_visible": True, "order": 3},
                {"input": "-91283472332", "output": "-2147483648", "is_visible": False, "order": 4},
            ]
        },
        {
            "title": "Integer to Roman Numeral",
            "slug": "integer-to-roman-numeral",
            "difficulty": CodingQuestion.DifficultyChoices.MEDIUM,
            "points": Decimal("25.00"),
            "problem": "Given an integer `num`, convert it to a Roman numeral representation.\n\n### Input Format\n- A single integer `num` ($1 \\le num \\le 3999$).\n\n### Output Format\n- Roman numeral string.",
            "starter_code": {
                "python": "def intToRoman(num: int) -> str:\n    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]\n    syb = [\"M\", \"CM\", \"D\", \"CD\", \"C\", \"XC\", \"L\", \"XL\", \"X\", \"IX\", \"V\", \"IV\", \"I\"]\n    res = []\n    for i in range(len(val)):\n        while num >= val[i]:\n            num -= val[i]\n            res.append(syb[i])\n    return \"\".join(res)\n\nif __name__ == '__main__':\n    import sys\n    print(intToRoman(int(sys.stdin.read().strip())))",
                "javascript": "const fs = require('fs');\nlet num = Number(fs.readFileSync(0, 'utf-8').trim());\nconst val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1];\nconst syb = [\"M\", \"CM\", \"D\", \"CD\", \"C\", \"XC\", \"L\", \"XL\", \"X\", \"IX\", \"V\", \"IV\", \"I\"];\nlet res = \"\";\nfor (let i = 0; i < val.length; i++) {\n    while (num >= val[i]) { res += syb[i]; num -= val[i]; }\n}\nconsole.log(res);",
                "java": "import java.util.*;\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNextInt()) {\n            int num = sc.nextInt();\n            int[] val = {1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1};\n            String[] syb = {\"M\", \"CM\", \"D\", \"CD\", \"C\", \"XC\", \"L\", \"XL\", \"X\", \"IX\", \"V\", \"IV\", \"I\"};\n            StringBuilder sb = new StringBuilder();\n            for (int i = 0; i < val.length; i++) {\n                while (num >= val[i]) { sb.append(syb[i]); num -= val[i]; }\n            }\n            System.out.println(sb.toString());\n        }\n    }\n}",
                "cpp": "#include <iostream>\n#include <vector>\nusing namespace std;\nint main() {\n    int num; if (cin >> num) {\n        int val[] = {1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1};\n        string syb[] = {\"M\", \"CM\", \"D\", \"CD\", \"C\", \"XC\", \"L\", \"XL\", \"X\", \"IX\", \"V\", \"IV\", \"I\"};\n        string res = \"\";\n        for (int i = 0; i < 13; i++) { while (num >= val[i]) { res += syb[i]; num -= val[i]; } }\n        cout << res << endl;\n    }\n    return 0;\n}",
                "c": "#include <stdio.h>\nint main() {\n    int num; if (scanf(\"%d\", &num) == 1) {\n        int val[] = {1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1};\n        char *syb[] = {\"M\", \"CM\", \"D\", \"CD\", \"C\", \"XC\", \"L\", \"XL\", \"X\", \"IX\", \"V\", \"IV\", \"I\"};\n        for (int i = 0; i < 13; i++) { while (num >= val[i]) { printf(\"%s\", syb[i]); num -= val[i]; } }\n        printf(\"\\n\");\n    }\n    return 0;\n}"
            },
            "test_cases": [
                {"input": "3", "output": "III", "is_visible": True, "order": 1},
                {"input": "58", "output": "LVIII", "is_visible": True, "order": 2},
                {"input": "1994", "output": "MCMXCIV", "is_visible": True, "order": 3},
                {"input": "3999", "output": "MMMCMXCIX", "is_visible": False, "order": 4},
            ]
        },
        {
            "title": "Divide Two Integers Without Operator",
            "slug": "divide-two-integers-bitwise",
            "difficulty": CodingQuestion.DifficultyChoices.HARD,
            "points": Decimal("30.00"),
            "problem": "Given two integers `dividend` and `divisor`, divide two integers without using multiplication, division, and mod operator. Return the quotient clamped to 32-bit signed integer range.\n\n### Input Format\n- Two space-separated integers `dividend` and `divisor`.\n\n### Output Format\n- Integer quotient.",
            "starter_code": {
                "python": "def divide(dividend: int, divisor: int) -> int:\n    if dividend == -2**31 and divisor == -1: return 2**31 - 1\n    sign = 1 if (dividend > 0) == (divisor > 0) else -1\n    a, b = abs(dividend), abs(divisor)\n    res = 0\n    for i in range(31, -1, -1):\n        if (a >> i) >= b:\n            res += (1 << i)\n            a -= (b << i)\n    return max(-2**31, min(2**31 - 1, sign * res))\n\nif __name__ == '__main__':\n    import sys\n    parts = sys.stdin.read().split()\n    if len(parts) >= 2:\n        print(divide(int(parts[0]), int(parts[1])))",
                "javascript": "const fs = require('fs');\nconst [a, b] = fs.readFileSync(0, 'utf-8').trim().split(/\\s+/).map(Number);\nconst q = Math.trunc(a / b);\nif (q > 2147483647) console.log(2147483647);\nelse if (q < -2147483648) console.log(-2147483648);\nelse console.log(q);",
                "java": "import java.util.*;\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNextLong()) {\n            long a = sc.nextLong(), b = sc.nextLong();\n            long q = a / b;\n            if (q > Integer.MAX_VALUE) System.out.println(Integer.MAX_VALUE);\n            else if (q < Integer.MIN_VALUE) System.out.println(Integer.MIN_VALUE);\n            else System.out.println(q);\n        }\n    }\n}",
                "cpp": "#include <iostream>\n#include <climits>\nusing namespace std;\nint main() {\n    long long a, b; if (cin >> a >> b) {\n        long long q = a / b;\n        if (q > INT_MAX) cout << INT_MAX << endl;\n        else if (q < INT_MIN) cout << INT_MIN << endl;\n        else cout << q << endl;\n    }\n    return 0;\n}",
                "c": "#include <stdio.h>\n#include <limits.h>\nint main() {\n    long long a, b; if (scanf(\"%lld %lld\", &a, &b) == 2) {\n        long long q = a / b;\n        if (q > INT_MAX) printf(\"%d\\n\", INT_MAX);\n        else if (q < INT_MIN) printf(\"%d\\n\", INT_MIN);\n        else printf(\"%lld\\n\", q);\n    }\n    return 0;\n}"
            },
            "test_cases": [
                {"input": "10 3", "output": "3", "is_visible": True, "order": 1},
                {"input": "7 -3", "output": "-2", "is_visible": True, "order": 2},
                {"input": "-2147483648 -1", "output": "2147483647", "is_visible": False, "order": 3},
            ]
        },
    ]
}


def seed_coding_questions():
    """Seed comprehensive coding questions across all curriculum modules."""
    from django.core.management import call_command
    try:
        call_command("seed_curriculum_questions")
    except Exception as e:
        print(f"Error seeding coding questions: {e}")

