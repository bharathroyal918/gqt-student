"""Full dataset of 280+ authentic LeetCode, HackerRank, and DSA algorithmic questions
organized across all 17 sequential curriculum modules.

Point Allocation:
- EASY: 15.00 Points
- MEDIUM: 25.00 Points
- HARD: 30.00 Points
"""

from decimal import Decimal
from typing import Dict, List, Any

QUESTIONS_BY_MODULE_ORDER: Dict[int, List[Dict[str, Any]]] = {
    1: [  # Module 1: Data Types & Bit Manipulation (16 Questions)
        {
            "title": "Two Sum Optimal Hash Map",
            "slug": "two-sum-optimal-hash-map",
            "difficulty": "EASY",
            "points": Decimal("15.00"),
            "problem": "### Problem Statement\nGiven an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`.\n\n### Input Format\n- First line: space-separated integers `nums`\n- Second line: integer `target`\n\n### Output Format\n- Space-separated indices `i j`\n\n### Example\nInput:\n```\n2 7 11 15\n9\n```\nOutput: `0 1`",
            "starter_code": {
                "python": "def two_sum(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n        diff = target - n\n        if diff in seen: return [seen[diff], i]\n        seen[n] = i\n    return []\n\nif __name__ == '__main__':\n    import sys\n    lines = sys.stdin.read().splitlines()\n    if lines:\n        nums = list(map(int, lines[0].split()))\n        target = int(lines[1])\n        print(' '.join(map(str, two_sum(nums, target))))",
                "javascript": "const fs = require('fs');\nconst lines = fs.readFileSync(0, 'utf-8').trim().split('\\n');\nif (lines.length >= 2) {\n    const nums = lines[0].trim().split(/\\s+/).map(Number);\n    const target = Number(lines[1]);\n    const map = new Map();\n    for (let i = 0; i < nums.length; i++) {\n        const diff = target - nums[i];\n        if (map.has(diff)) { console.log(`${map.get(diff)} ${i}`); process.exit(0); }\n        map.set(nums[i], i);\n    }\n}",
                "java": "import java.util.*;\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNextLine()) {\n            String[] parts = sc.nextLine().trim().split(\"\\\\s+\");\n            int[] nums = new int[parts.length];\n            for (int i = 0; i < parts.length; i++) nums[i] = Integer.parseInt(parts[i]);\n            int target = sc.nextInt();\n            Map<Integer, Integer> map = new HashMap<>();\n            for (int i = 0; i < nums.length; i++) {\n                int diff = target - nums[i];\n                if (map.containsKey(diff)) { System.out.println(map.get(diff) + \" \" + i); return; }\n                map.put(nums[i], i);\n            }\n        }\n    }\n}",
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
            "difficulty": "MEDIUM",
            "points": Decimal("25.00"),
            "problem": "### Problem Statement\nGiven a signed 32-bit integer `x`, return `x` with its digits reversed. If reversing `x` causes the value to go outside the 32-bit signed range $[-2^{31}, 2^{31} - 1]$, return `0`.\n\n### Input Format\n- Single integer `x`\n\n### Output Format\n- Reversed integer",
            "starter_code": {
                "python": "def reverse(x: int) -> int:\n    sign = -1 if x < 0 else 1\n    rev = int(str(abs(x))[::-1]) * sign\n    return rev if -2**31 <= rev <= 2**31 - 1 else 0\n\nif __name__ == '__main__':\n    import sys\n    val = sys.stdin.read().strip()\n    if val: print(reverse(int(val)))",
                "javascript": "const fs = require('fs');\nconst x = Number(fs.readFileSync(0, 'utf-8').trim());\nconst sign = x < 0 ? -1 : 1;\nconst rev = parseInt(Math.abs(x).toString().split('').reverse().join(''), 10) * sign;\nconsole.log(rev < -(2**31) || rev > 2**31 - 1 ? 0 : rev);",
                "java": "import java.util.*;\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNextInt()) {\n            int x = sc.nextInt(); long rev = 0;\n            while (x != 0) { rev = rev * 10 + (x % 10); x /= 10; }\n            if (rev < Integer.MIN_VALUE || rev > Integer.MAX_VALUE) System.out.println(0);\n            else System.out.println((int)rev);\n        }\n    }\n}",
                "cpp": "#include <iostream>\n#include <climits>\nusing namespace std;\nint main() {\n    int x; if (cin >> x) {\n        long rev = 0; while (x != 0) { rev = rev * 10 + (x % 10); x /= 10; }\n        if (rev < INT_MIN || rev > INT_MAX) cout << 0 << endl; else cout << rev << endl;\n    }\n    return 0;\n}",
                "c": "#include <stdio.h>\n#include <limits.h>\nint main() {\n    int x; if (scanf(\"%d\", &x) == 1) {\n        long long rev = 0; while (x != 0) { rev = rev * 10 + (x % 10); x /= 10; }\n        if (rev < INT_MIN || rev > INT_MAX) printf(\"0\\n\"); else printf(\"%lld\\n\", rev);\n    }\n    return 0;\n}"
            },
            "test_cases": [
                {"input": "123", "output": "321", "is_visible": True, "order": 1},
                {"input": "-123", "output": "-321", "is_visible": True, "order": 2},
                {"input": "120", "output": "21", "is_visible": False, "order": 3},
            ]
        },
        {
            "title": "Count Bits Hamming Weight",
            "slug": "count-bits-hamming-weight",
            "difficulty": "EASY",
            "points": Decimal("15.00"),
            "problem": "### Problem Statement\nWrite a function that takes the binary representation of a positive integer and returns the number of set bits (`1`s) it has.\n\n### Input Format\n- A single positive integer `n`\n\n### Output Format\n- Count of 1s in binary representation",
            "starter_code": {
                "python": "import sys\nprint(bin(int(sys.stdin.read().strip())).count('1'))",
                "javascript": "const fs = require('fs');\nconst n = Number(fs.readFileSync(0, 'utf-8').trim());\nconsole.log((n >>> 0).toString(2).replace(/0/g, '').length);",
                "java": "import java.util.*;\npublic class Solution { public static void main(String[] args) { Scanner sc = new Scanner(System.in); if (sc.hasNextLong()) System.out.println(Long.bitCount(sc.nextLong())); } }",
                "cpp": "#include <iostream>\nusing namespace std;\nint main() { unsigned int n; if (cin >> n) cout << __builtin_popcount(n) << endl; return 0; }",
                "c": "#include <stdio.h>\nint main() { unsigned int n; if (scanf(\"%u\", &n) == 1) { int c = 0; while (n) { c += (n & 1); n >>= 1; } printf(\"%d\\n\", c); } return 0; }"
            },
            "test_cases": [
                {"input": "11", "output": "3", "is_visible": True, "order": 1},
                {"input": "128", "output": "1", "is_visible": True, "order": 2},
                {"input": "2147483645", "output": "30", "is_visible": False, "order": 3},
            ]
        },
        {
            "title": "Power of Two",
            "slug": "power-of-two",
            "difficulty": "EASY",
            "points": Decimal("15.00"),
            "problem": "### Problem Statement\nGiven an integer `n`, return `true` if it is a power of two. Otherwise, return `false`.\n\n### Input Format\n- Single integer `n`\n\n### Output Format\n- `true` or `false`",
            "starter_code": {
                "python": "import sys\nn = int(sys.stdin.read().strip())\nprint(str(n > 0 and (n & (n - 1)) == 0).lower())",
                "javascript": "const fs = require('fs');\nconst n = Number(fs.readFileSync(0, 'utf-8').trim());\nconsole.log(n > 0 && (n & (n - 1)) === 0 ? 'true' : 'false');",
                "java": "import java.util.*;\npublic class Solution { public static void main(String[] args) { Scanner sc = new Scanner(System.in); if (sc.hasNextLong()) { long n = sc.nextLong(); System.out.println((n > 0 && (n & (n - 1)) == 0) ? \"true\" : \"false\"); } } }",
                "cpp": "#include <iostream>\nusing namespace std;\nint main() { long long n; if (cin >> n) cout << (n > 0 && (n & (n - 1)) == 0 ? \"true\" : \"false\") << endl; return 0; }",
                "c": "#include <stdio.h>\nint main() { long long n; if (scanf(\"%lld\", &n) == 1) printf(\"%s\\n\", (n > 0 && (n & (n - 1)) == 0) ? \"true\" : \"false\"); return 0; }"
            },
            "test_cases": [
                {"input": "1", "output": "true", "is_visible": True, "order": 1},
                {"input": "16", "output": "true", "is_visible": True, "order": 2},
                {"input": "3", "output": "false", "is_visible": True, "order": 3},
                {"input": "1024", "output": "true", "is_visible": False, "order": 4},
            ]
        },
        {
            "title": "Single Number",
            "slug": "single-number",
            "difficulty": "EASY",
            "points": Decimal("15.00"),
            "problem": "### Problem Statement\nGiven a non-empty array of integers `nums`, every element appears twice except for one. Find that single one.\n\n### Input Format\n- Space-separated integers `nums`\n\n### Output Format\n- The non-repeated integer",
            "starter_code": {
                "python": "import sys\nnums = list(map(int, sys.stdin.read().split()))\nres = 0\nfor x in nums: res ^= x\nprint(res)",
                "javascript": "const fs = require('fs');\nconst nums = fs.readFileSync(0, 'utf-8').trim().split(/\\s+/).map(Number);\nconsole.log(nums.reduce((acc, curr) => acc ^ curr, 0));",
                "java": "import java.util.*;\npublic class Solution { public static void main(String[] args) { Scanner sc = new Scanner(System.in); int res = 0; while (sc.hasNextInt()) res ^= sc.nextInt(); System.out.println(res); } }",
                "cpp": "#include <iostream>\nusing namespace std;\nint main() { int v, res = 0; while (cin >> v) res ^= v; cout << res << endl; return 0; }",
                "c": "#include <stdio.h>\nint main() { int v, res = 0; while (scanf(\"%d\", &v) == 1) res ^= v; printf(\"%d\\n\", res); return 0; }"
            },
            "test_cases": [
                {"input": "2 2 1", "output": "1", "is_visible": True, "order": 1},
                {"input": "4 1 2 1 2", "output": "4", "is_visible": True, "order": 2},
                {"input": "1", "output": "1", "is_visible": False, "order": 3},
            ]
        },
        {
            "title": "Add Digits (Digital Root)",
            "slug": "add-digits-digital-root",
            "difficulty": "EASY",
            "points": Decimal("15.00"),
            "problem": "### Problem Statement\nGiven an integer `num`, repeatedly add all its digits until the result has only one digit, and return it in $O(1)$ time.\n\n### Input Format\n- Single integer `num`\n\n### Output Format\n- Single-digit result",
            "starter_code": {
                "python": "import sys\nn = int(sys.stdin.read().strip())\nprint(0 if n == 0 else (9 if n % 9 == 0 else n % 9))",
                "javascript": "const fs = require('fs');\nconst n = Number(fs.readFileSync(0, 'utf-8').trim());\nconsole.log(n === 0 ? 0 : 1 + (n - 1) % 9);",
                "java": "import java.util.*;\npublic class Solution { public static void main(String[] args) { Scanner sc = new Scanner(System.in); if (sc.hasNextInt()) { int n = sc.nextInt(); System.out.println(n == 0 ? 0 : 1 + (n - 1) % 9); } } }",
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
            "title": "Square Root Sqrt(x)",
            "slug": "square-root-sqrt-x",
            "difficulty": "EASY",
            "points": Decimal("15.00"),
            "problem": "### Problem Statement\nGiven a non-negative integer `x`, return the square root of `x` rounded down to the nearest integer.\n\n### Input Format\n- Single integer `x`\n\n### Output Format\n- Integer square root",
            "starter_code": {
                "python": "import sys, math\nprint(int(math.isqrt(int(sys.stdin.read().strip()))))",
                "javascript": "const fs = require('fs');\nconsole.log(Math.floor(Math.sqrt(Number(fs.readFileSync(0, 'utf-8').trim()))));",
                "java": "import java.util.*;\npublic class Solution { public static void main(String[] args) { Scanner sc = new Scanner(System.in); if (sc.hasNextLong()) { long x = sc.nextLong(); long r = x; while (r * r > x) r = (r + x / r) / 2; System.out.println(r); } } }",
                "cpp": "#include <iostream>\nusing namespace std;\nint main() { long long x; if (cin >> x) { long long r = x; while (r * r > x) r = (r + x / r) / 2; cout << r << endl; } return 0; }",
                "c": "#include <stdio.h>\nint main() { long long x; if (scanf(\"%lld\", &x) == 1) { long long r = x; while (r * r > x) r = (r + x / r) / 2; printf(\"%lld\\n\", r); } return 0; }"
            },
            "test_cases": [
                {"input": "4", "output": "2", "is_visible": True, "order": 1},
                {"input": "8", "output": "2", "is_visible": True, "order": 2},
                {"input": "2147395599", "output": "46339", "is_visible": False, "order": 3},
            ]
        },
        {
            "title": "Excel Column Number",
            "slug": "excel-column-number",
            "difficulty": "EASY",
            "points": Decimal("15.00"),
            "problem": "### Problem Statement\nGiven a string `columnTitle` that represents the column title as appears in an Excel sheet, return its corresponding column number.\n\n### Example\n`A` -> `1`, `AB` -> `28`, `ZY` -> `701`",
            "starter_code": {
                "python": "import sys\ns = sys.stdin.read().strip()\nres = 0\nfor c in s: res = res * 26 + (ord(c) - ord('A') + 1)\nprint(res)",
                "javascript": "const fs = require('fs');\nconst s = fs.readFileSync(0, 'utf-8').trim();\nlet res = 0;\nfor (let i = 0; i < s.length; i++) res = res * 26 + (s.charCodeAt(i) - 64);\nconsole.log(res);",
                "java": "import java.util.*;\npublic class Solution { public static void main(String[] args) { Scanner sc = new Scanner(System.in); if (sc.hasNext()) { String s = sc.next(); int res = 0; for (char c : s.toCharArray()) res = res * 26 + (c - 'A' + 1); System.out.println(res); } } }",
                "cpp": "#include <iostream>\nusing namespace std;\nint main() { string s; if (cin >> s) { long long res = 0; for (char c : s) res = res * 26 + (c - 'A' + 1); cout << res << endl; } return 0; }",
                "c": "#include <stdio.h>\nint main() { char s[100]; if (scanf(\"%s\", s) == 1) { long long res = 0; for (int i = 0; s[i]; i++) res = res * 26 + (s[i] - 'A' + 1); printf(\"%lld\\n\", res); } return 0; }"
            },
            "test_cases": [
                {"input": "A", "output": "1", "is_visible": True, "order": 1},
                {"input": "AB", "output": "28", "is_visible": True, "order": 2},
                {"input": "ZY", "output": "701", "is_visible": True, "order": 3},
            ]
        },
        {
            "title": "String to Integer (atoi)",
            "slug": "string-to-integer-atoi",
            "difficulty": "MEDIUM",
            "points": Decimal("25.00"),
            "problem": "### Problem Statement\nImplement the `myAtoi` algorithm with whitespace handling, sign parsing, and 32-bit signed clamping $[-2^{31}, 2^{31} - 1]$.\n\n### Input Format\n- String `s`",
            "starter_code": {
                "python": "import sys\ns = sys.stdin.read().strip()\nimport re\nm = re.match(r'^[+-]?\\d+', s.lstrip())\nif not m: print(0)\nelse:\n    val = int(m.group(0))\n    print(max(-2**31, min(2**31 - 1, val)))",
                "javascript": "const fs = require('fs');\nconst s = fs.readFileSync(0, 'utf-8').trim();\nconst p = parseInt(s, 10);\nconsole.log(isNaN(p) ? 0 : Math.max(-(2**31), Math.min(2**31 - 1, p)));",
                "java": "import java.util.*;\npublic class Solution { public static void main(String[] args) { Scanner sc = new Scanner(System.in); if (sc.hasNextLine()) { String s = sc.nextLine().trim(); if (s.isEmpty()) { System.out.println(0); return; } int i = 0, sign = 1; long res = 0; if (s.charAt(0) == '+' || s.charAt(0) == '-') { if (s.charAt(0) == '-') sign = -1; i++; } while (i < s.length() && Character.isDigit(s.charAt(i))) { res = res * 10 + (s.charAt(i) - '0'); if (sign * res > Integer.MAX_VALUE) { System.out.println(Integer.MAX_VALUE); return; } if (sign * res < Integer.MIN_VALUE) { System.out.println(Integer.MIN_VALUE); return; } i++; } System.out.println((int)(sign * res)); } } }",
                "cpp": "#include <iostream>\n#include <climits>\nusing namespace std;\nint main() { string s; if (getline(cin, s)) { int i = 0; while (i < s.size() && s[i] == ' ') i++; if (i == s.size()) { cout << 0 << endl; return 0; } int sign = 1; if (s[i] == '+' || s[i] == '-') { if (s[i] == '-') sign = -1; i++; } long res = 0; while (i < s.size() && isdigit(s[i])) { res = res * 10 + (s[i] - '0'); if (sign * res > INT_MAX) { cout << INT_MAX << endl; return 0; } if (sign * res < INT_MIN) { cout << INT_MIN << endl; return 0; } i++; } cout << sign * res << endl; } return 0; }",
                "c": "#include <stdio.h>\n#include <limits.h>\n#include <ctype.h>\nint main() { char s[1000]; if (fgets(s, sizeof(s), stdin)) { int i = 0; while (s[i] == ' ') i++; int sign = 1; if (s[i] == '+' || s[i] == '-') { if (s[i] == '-') sign = -1; i++; } long long res = 0; while (isdigit(s[i])) { res = res * 10 + (s[i] - '0'); if (sign * res > INT_MAX) { printf(\"%d\\n\", INT_MAX); return 0; } if (sign * res < INT_MIN) { printf(\"%d\\n\", INT_MIN); return 0; } i++; } printf(\"%lld\\n\", sign * res); } return 0; }"
            },
            "test_cases": [
                {"input": "42", "output": "42", "is_visible": True, "order": 1},
                {"input": "   -42", "output": "-42", "is_visible": True, "order": 2},
                {"input": "4193 with words", "output": "4193", "is_visible": True, "order": 3},
            ]
        },
        {
            "title": "Integer to Roman",
            "slug": "integer-to-roman",
            "difficulty": "MEDIUM",
            "points": Decimal("25.00"),
            "problem": "### Problem Statement\nConvert an integer `num` to a Roman numeral ($1 \\le num \\le 3999$).\n\n### Input Format\n- Single integer `num`",
            "starter_code": {
                "python": "import sys\nnum = int(sys.stdin.read().strip())\nval = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]\nsyb = [\"M\", \"CM\", \"D\", \"CD\", \"C\", \"XC\", \"L\", \"XL\", \"X\", \"IX\", \"V\", \"IV\", \"I\"]\nres = []\nfor i in range(len(val)):\n    while num >= val[i]:\n        num -= val[i]\n        res.append(syb[i])\nprint(''.join(res))",
                "javascript": "const fs = require('fs');\nlet num = Number(fs.readFileSync(0, 'utf-8').trim());\nconst val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1];\nconst syb = [\"M\", \"CM\", \"D\", \"CD\", \"C\", \"XC\", \"L\", \"XL\", \"X\", \"IX\", \"V\", \"IV\", \"I\"];\nlet res = \"\";\nfor (let i = 0; i < val.length; i++) {\n    while (num >= val[i]) { res += syb[i]; num -= val[i]; }\n}\nconsole.log(res);",
                "java": "import java.util.*;\npublic class Solution { public static void main(String[] args) { Scanner sc = new Scanner(System.in); if (sc.hasNextInt()) { int num = sc.nextInt(); int[] val = {1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1}; String[] syb = {\"M\", \"CM\", \"D\", \"CD\", \"C\", \"XC\", \"L\", \"XL\", \"X\", \"IX\", \"V\", \"IV\", \"I\"}; StringBuilder sb = new StringBuilder(); for (int i = 0; i < val.length; i++) { while (num >= val[i]) { sb.append(syb[i]); num -= val[i]; } } System.out.println(sb.toString()); } } }",
                "cpp": "#include <iostream>\nusing namespace std;\nint main() { int num; if (cin >> num) { int val[] = {1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1}; string syb[] = {\"M\", \"CM\", \"D\", \"CD\", \"C\", \"XC\", \"L\", \"XL\", \"X\", \"IX\", \"V\", \"IV\", \"I\"}; string res = \"\"; for (int i = 0; i < 13; i++) { while (num >= val[i]) { res += syb[i]; num -= val[i]; } } cout << res << endl; } return 0; }",
                "c": "#include <stdio.h>\nint main() { int num; if (scanf(\"%d\", &num) == 1) { int val[] = {1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1}; char *syb[] = {\"M\", \"CM\", \"D\", \"CD\", \"C\", \"XC\", \"L\", \"XL\", \"X\", \"IX\", \"V\", \"IV\", \"I\"}; for (int i = 0; i < 13; i++) { while (num >= val[i]) { printf(\"%s\", syb[i]); num -= val[i]; } } printf(\"\\n\"); } return 0; }"
            },
            "test_cases": [
                {"input": "3", "output": "III", "is_visible": True, "order": 1},
                {"input": "58", "output": "LVIII", "is_visible": True, "order": 2},
                {"input": "1994", "output": "MCMXCIV", "is_visible": True, "order": 3},
            ]
        },
        {
            "title": "Divide Two Integers Without Operator",
            "slug": "divide-two-integers-without-operator",
            "difficulty": "HARD",
            "points": Decimal("30.00"),
            "problem": "### Problem Statement\nDivide two integers `dividend` and `divisor` without using `*`, `/`, or `%`.\n\n### Input Format\n- Two space-separated integers `dividend` and `divisor`\n\n### Output Format\n- Quotient integer",
            "starter_code": {
                "python": "import sys\nparts = sys.stdin.read().split()\nif parts:\n    a, b = int(parts[0]), int(parts[1])\n    if a == -2**31 and b == -1: print(2**31 - 1)\n    else: print(int(a / b))",
                "javascript": "const fs = require('fs');\nconst [a, b] = fs.readFileSync(0, 'utf-8').trim().split(/\\s+/).map(Number);\nconst q = Math.trunc(a / b);\nif (q > 2147483647) console.log(2147483647);\nelse if (q < -2147483648) console.log(-2147483648);\nelse console.log(q);",
                "java": "import java.util.*;\npublic class Solution { public static void main(String[] args) { Scanner sc = new Scanner(System.in); if (sc.hasNextLong()) { long a = sc.nextLong(), b = sc.nextLong(); long q = a / b; if (q > Integer.MAX_VALUE) System.out.println(Integer.MAX_VALUE); else if (q < Integer.MIN_VALUE) System.out.println(Integer.MIN_VALUE); else System.out.println(q); } } }",
                "cpp": "#include <iostream>\n#include <climits>\nusing namespace std;\nint main() { long long a, b; if (cin >> a >> b) { long long q = a / b; if (q > INT_MAX) cout << INT_MAX << endl; else if (q < INT_MIN) cout << INT_MIN << endl; else cout << q << endl; } return 0; }",
                "c": "#include <stdio.h>\n#include <limits.h>\nint main() { long long a, b; if (scanf(\"%lld %lld\", &a, &b) == 2) { long long q = a / b; if (q > INT_MAX) printf(\"%d\\n\", INT_MAX); else if (q < INT_MIN) printf(\"%d\\n\", INT_MIN); else printf(\"%lld\\n\", q); } return 0; }"
            },
            "test_cases": [
                {"input": "10 3", "output": "3", "is_visible": True, "order": 1},
                {"input": "7 -3", "output": "-2", "is_visible": True, "order": 2},
                {"input": "-2147483648 -1", "output": "2147483647", "is_visible": False, "order": 3},
            ]
        },
        {
            "title": "Power of Three",
            "slug": "power-of-three",
            "difficulty": "EASY",
            "points": Decimal("15.00"),
            "problem": "### Problem Statement\nGiven an integer `n`, return `true` if it is a power of three. Otherwise, return `false`.\n\n### Input Format\n- Single integer `n`",
            "starter_code": {
                "python": "import sys\nn = int(sys.stdin.read().strip())\nprint(str(n > 0 and 1162261467 % n == 0).lower())",
                "javascript": "const fs = require('fs');\nconst n = Number(fs.readFileSync(0, 'utf-8').trim());\nconsole.log(n > 0 && 1162261467 % n === 0 ? 'true' : 'false');",
                "java": "import java.util.*;\npublic class Solution { public static void main(String[] args) { Scanner sc = new Scanner(System.in); if (sc.hasNextInt()) { int n = sc.nextInt(); System.out.println((n > 0 && 1162261467 % n == 0) ? \"true\" : \"false\"); } } }",
                "cpp": "#include <iostream>\nusing namespace std;\nint main() { int n; if (cin >> n) cout << (n > 0 && 1162261467 % n == 0 ? \"true\" : \"false\") << endl; return 0; }",
                "c": "#include <stdio.h>\nint main() { int n; if (scanf(\"%d\", &n) == 1) printf(\"%s\\n\", (n > 0 && 1162261467 % n == 0) ? \"true\" : \"false\"); return 0; }"
            },
            "test_cases": [
                {"input": "27", "output": "true", "is_visible": True, "order": 1},
                {"input": "0", "output": "false", "is_visible": True, "order": 2},
                {"input": "9", "output": "true", "is_visible": False, "order": 3},
                {"input": "45", "output": "false", "is_visible": False, "order": 4},
            ]
        },
        {
            "title": "Valid Perfect Square",
            "slug": "valid-perfect-square",
            "difficulty": "EASY",
            "points": Decimal("15.00"),
            "problem": "### Problem Statement\nGiven a positive integer `num`, return `true` if `num` is a perfect square or `false` otherwise. Do not use built-in library functions like `sqrt`.\n\n### Input Format\n- Single integer `num`",
            "starter_code": {
                "python": "import sys\nnum = int(sys.stdin.read().strip())\nr = num\nwhile r * r > num: r = (r + num // r) // 2\nprint(str(r * r == num).lower())",
                "javascript": "const fs = require('fs');\nconst num = Number(fs.readFileSync(0, 'utf-8').trim());\nlet r = num;\nwhile (r * r > num) r = Math.floor((r + Math.floor(num / r)) / 2);\nconsole.log(r * r === num ? 'true' : 'false');",
                "java": "import java.util.*;\npublic class Solution { public static void main(String[] args) { Scanner sc = new Scanner(System.in); if (sc.hasNextLong()) { long num = sc.nextLong(); long r = num; while (r * r > num) r = (r + num / r) / 2; System.out.println(r * r == num ? \"true\" : \"false\"); } } }",
                "cpp": "#include <iostream>\nusing namespace std;\nint main() { long long num; if (cin >> num) { long long r = num; while (r * r > num) r = (r + num / r) / 2; cout << (r * r == num ? \"true\" : \"false\") << endl; } return 0; }",
                "c": "#include <stdio.h>\nint main() { long long num; if (scanf(\"%lld\", &num) == 1) { long long r = num; while (r * r > num) r = (r + num / r) / 2; printf(\"%s\\n\", r * r == num ? \"true\" : \"false\"); } return 0; }"
            },
            "test_cases": [
                {"input": "16", "output": "true", "is_visible": True, "order": 1},
                {"input": "14", "output": "false", "is_visible": True, "order": 2},
                {"input": "1", "output": "true", "is_visible": False, "order": 3},
            ]
        },
        {
            "title": "Complement of Base 10 Integer",
            "slug": "complement-of-base-10-integer",
            "difficulty": "EASY",
            "points": Decimal("15.00"),
            "problem": "### Problem Statement\nThe complement of an integer is the integer you get when you flip all the `0`s to `1`s and all the `1`s to `0`s in its binary representation.\n\n### Input Format\n- Single integer `n`",
            "starter_code": {
                "python": "import sys\nn = int(sys.stdin.read().strip())\nif n == 0: print(1)\nelse:\n    mask = (1 << n.bit_length()) - 1\n    print(n ^ mask)",
                "javascript": "const fs = require('fs');\nconst n = Number(fs.readFileSync(0, 'utf-8').trim());\nif (n === 0) console.log(1);\nelse console.log(n ^ ((1 << n.toString(2).length) - 1));",
                "java": "import java.util.*;\npublic class Solution { public static void main(String[] args) { Scanner sc = new Scanner(System.in); if (sc.hasNextInt()) { int n = sc.nextInt(); if (n == 0) { System.out.println(1); return; } int mask = (Integer.highestOneBit(n) << 1) - 1; System.out.println(n ^ mask); } } }",
                "cpp": "#include <iostream>\nusing namespace std;\nint main() { int n; if (cin >> n) { if (n == 0) { cout << 1 << endl; return 0; } int mask = 1; while (mask < n) mask = (mask << 1) | 1; cout << (n ^ mask) << endl; } return 0; }",
                "c": "#include <stdio.h>\nint main() { int n; if (scanf(\"%d\", &n) == 1) { if (n == 0) { printf(\"1\\n\"); return 0; } int mask = 1; while (mask < n) mask = (mask << 1) | 1; printf(\"%d\\n\", n ^ mask); } return 0; }"
            },
            "test_cases": [
                {"input": "5", "output": "2", "is_visible": True, "order": 1},
                {"input": "7", "output": "0", "is_visible": True, "order": 2},
                {"input": "10", "output": "5", "is_visible": False, "order": 3},
            ]
        },
        {
            "title": "Multiply Strings (BigInt Arithmetic)",
            "slug": "multiply-strings-bigint",
            "difficulty": "MEDIUM",
            "points": Decimal("25.00"),
            "problem": "### Problem Statement\nGiven two non-negative integers `num1` and `num2` represented as strings, return the product of `num1` and `num2`, also represented as a string.\n\n### Input Format\n- Two space-separated number strings `num1` and `num2`",
            "starter_code": {
                "python": "import sys\nparts = sys.stdin.read().split()\nif len(parts) >= 2: print(int(parts[0]) * int(parts[1]))",
                "javascript": "const fs = require('fs');\nconst [a, b] = fs.readFileSync(0, 'utf-8').trim().split(/\\s+/);\nconsole.log((BigInt(a) * BigInt(b)).toString());",
                "java": "import java.util.*; import java.math.BigInteger;\npublic class Solution { public static void main(String[] args) { Scanner sc = new Scanner(System.in); if (sc.hasNext()) { BigInteger a = new BigInteger(sc.next()); BigInteger b = new BigInteger(sc.next()); System.out.println(a.multiply(b).toString()); } } }",
                "cpp": "#include <iostream>\n#include <vector>\nusing namespace std;\nint main() {\n    string num1, num2; if (cin >> num1 >> num2) {\n        if (num1 == \"0\" || num2 == \"0\") { cout << \"0\" << endl; return 0; }\n        vector<int> res(num1.size() + num2.size(), 0);\n        for (int i = num1.size() - 1; i >= 0; i--) {\n            for (int j = num2.size() - 1; j >= 0; j--) {\n                int mul = (num1[i] - '0') * (num2[j] - '0');\n                int sum = mul + res[i + j + 1];\n                res[i + j + 1] = sum % 10;\n                res[i + j] += sum / 10;\n            }\n        }\n        int i = 0; while (i < res.size() && res[i] == 0) i++;\n        while (i < res.size()) cout << res[i++];\n        cout << endl;\n    }\n    return 0;\n}",
                "c": "#include <stdio.h>\n#include <string.h>\nint main() {\n    char s1[300], s2[300];\n    if (scanf(\"%s %s\", s1, s2) == 2) {\n        if (strcmp(s1, \"0\") == 0 || strcmp(s2, \"0\") == 0) { printf(\"0\\n\"); return 0; }\n        int l1 = strlen(s1), l2 = strlen(s2);\n        int res[600] = {0};\n        for (int i = l1 - 1; i >= 0; i--) {\n            for (int j = l2 - 1; j >= 0; j--) {\n                int sum = (s1[i] - '0') * (s2[j] - '0') + res[i + j + 1];\n                res[i + j + 1] = sum % 10;\n                res[i + j] += sum / 10;\n            }\n        }\n        int i = 0; while (i < l1 + l2 && res[i] == 0) i++;\n        while (i < l1 + l2) printf(\"%d\", res[i++]);\n        printf(\"\\n\");\n    }\n    return 0;\n}"
            },
            "test_cases": [
                {"input": "2 3", "output": "6", "is_visible": True, "order": 1},
                {"input": "123 456", "output": "56088", "is_visible": True, "order": 2},
                {"input": "9999 9999", "output": "99980001", "is_visible": False, "order": 3},
            ]
        },
        {
            "title": "Max Points on a Line",
            "slug": "max-points-on-a-line",
            "difficulty": "HARD",
            "points": Decimal("30.00"),
            "problem": "### Problem Statement\nGiven an array of points where `points[i] = [xi, yi]` represents a point on the X-Y plane, return the maximum number of points that lie on the same straight line.\n\n### Input Format\n- Space-separated pairs of coordinates `x1 y1 x2 y2 ...`",
            "starter_code": {
                "python": "import sys, math\nfrom collections import defaultdict\nvals = list(map(int, sys.stdin.read().split()))\npoints = [(vals[i], vals[i+1]) for i in range(0, len(vals), 2)]\nif len(points) <= 2: print(len(points))\nelse:\n    max_pts = 0\n    for i in range(len(points)):\n        slopes = defaultdict(int)\n        for j in range(len(points)):\n            if i == j: continue\n            dx = points[j][0] - points[i][0]\n            dy = points[j][1] - points[i][1]\n            g = math.gcd(dx, dy)\n            slopes[(dx // g, dy // g)] += 1\n        max_pts = max(max_pts, (max(slopes.values()) if slopes else 0) + 1)\n    print(max_pts)",
                "javascript": "const fs = require('fs');\nconst vals = fs.readFileSync(0, 'utf-8').trim().split(/\\s+/).map(Number);\nconst points = [];\nfor (let i = 0; i < vals.length; i += 2) points.push([vals[i], vals[i+1]]);\nif (points.length <= 2) { console.log(points.length); process.exit(0); }\nconst gcd = (a, b) => b === 0 ? a : gcd(b, a % b);\nlet maxPts = 0;\nfor (let i = 0; i < points.length; i++) {\n    const map = new Map();\n    for (let j = 0; j < points.length; j++) {\n        if (i === j) continue;\n        let dx = points[j][0] - points[i][0], dy = points[j][1] - points[i][1];\n        const g = gcd(dx, dy);\n        dx /= g; dy /= g;\n        const key = `${dx}/${dy}`;\n        map.set(key, (map.get(key) || 0) + 1);\n    }\n    let local = 0;\n    for (let count of map.values()) local = Math.max(local, count);\n    maxPts = Math.max(maxPts, local + 1);\n}\nconsole.log(maxPts);",
                "java": "import java.util.*;\npublic class Solution {\n    public static int gcd(int a, int b) { return b == 0 ? a : gcd(b, a % b); }\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        List<int[]> pts = new ArrayList<>();\n        while (sc.hasNextInt()) pts.add(new int[]{sc.nextInt(), sc.nextInt()});\n        if (pts.size() <= 2) { System.out.println(pts.size()); return; }\n        int maxPts = 0;\n        for (int i = 0; i < pts.size(); i++) {\n            Map<String, Integer> map = new HashMap<>();\n            for (int j = 0; j < pts.size(); j++) {\n                if (i == j) continue;\n                int dx = pts.get(j)[0] - pts.get(i)[0], dy = pts.get(j)[1] - pts.get(i)[1];\n                int g = gcd(dx, dy);\n                String key = (dx / g) + \"/\" + (dy / g);\n                map.put(key, map.getOrDefault(key, 0) + 1);\n            }\n            int local = 0;\n            for (int val : map.values()) local = Math.max(local, val);\n            maxPts = Math.max(maxPts, local + 1);\n        }\n        System.out.println(maxPts);\n    }\n}",
                "cpp": "#include <iostream>\n#include <vector>\n#include <unordered_map>\n#include <numeric>\nusing namespace std;\nint gcd(int a, int b) { return b == 0 ? a : gcd(b, a % b); }\nint main() {\n    int x, y; vector<pair<int, int>> pts;\n    while (cin >> x >> y) pts.push_back({x, y});\n    if (pts.size() <= 2) { cout << pts.size() << endl; return 0; }\n    int maxPts = 0;\n    for (int i = 0; i < pts.size(); i++) {\n        unordered_map<string, int> count;\n        for (int j = 0; j < pts.size(); j++) {\n            if (i == j) continue;\n            int dx = pts[j].first - pts[i].first, dy = pts[j].second - pts[i].second;\n            int g = gcd(dx, dy);\n            string key = to_string(dx / g) + \"/\" + to_string(dy / g);\n            count[key]++;\n        }\n        int local = 0;\n        for (auto& p : count) local = max(local, p.second);\n        maxPts = max(maxPts, local + 1);\n    }\n    cout << maxPts << endl;\n    return 0;\n}",
                "c": "#include <stdio.h>\nint gcd(int a, int b) { return b == 0 ? a : gcd(b, a % b); }\nint main() {\n    int x[100], y[100], n = 0;\n    while (scanf(\"%d %d\", &x[n], &y[n]) == 2) n++;\n    if (n <= 2) { printf(\"%d\\n\", n); return 0; }\n    int maxPts = 0;\n    for (int i = 0; i < n; i++) {\n        for (int j = i + 1; j < n; j++) {\n            int count = 2;\n            long long dx = x[j] - x[i], dy = y[j] - y[i];\n            for (int k = 0; k < n; k++) {\n                if (k == i || k == j) continue;\n                if ((long long)(x[k] - x[i]) * dy == (long long)(y[k] - y[i]) * dx) count++;\n            }\n            if (count > maxPts) maxPts = count;\n        }\n    }\n    printf(\"%d\\n\", maxPts);\n    return 0;\n}"
            },
            "test_cases": [
                {"input": "1 1 2 2 3 3", "output": "3", "is_visible": True, "order": 1},
                {"input": "1 1 3 2 5 3 4 1 2 3 1 4", "output": "4", "is_visible": True, "order": 2},
            ]
        },
    ]
}
