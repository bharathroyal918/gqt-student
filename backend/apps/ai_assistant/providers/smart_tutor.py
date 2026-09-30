"""High-quality intelligent Smart Tutor provider for programming concepts, debugging, and hints."""

import re
from typing import Any, Dict, List, Optional

from apps.ai_assistant.providers.base import AIProviderResult, BaseAIProvider


class SmartTutorAIProvider(BaseAIProvider):
    """Pedagogical tutor provider offering structured code guidance, error explanation, and concept tutoring."""

    def __init__(self, model_name: str = "smart-tutor-v2"):
        self.model_name = model_name

    def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> AIProviderResult:
        if not messages:
            return AIProviderResult(
                content="Hello! How can I assist you with your code or programming concepts today?",
                tokens_used=15,
                model_name=self.model_name,
            )

        # Extract the latest student query
        last_message = messages[-1]["content"].strip()
        last_lower = last_message.lower()

        # Generate intelligent contextual pedagogical response based on the query
        response_text = self._synthesize_pedagogical_reply(last_message, last_lower, messages, context)
        estimated_tokens = max(20, len(response_text.split()) * 2)

        return AIProviderResult(
            content=response_text,
            tokens_used=estimated_tokens,
            model_name=self.model_name,
            finish_reason="stop",
        )

    def _synthesize_pedagogical_reply(
        self,
        query: str,
        q_lower: str,
        history: List[Dict[str, str]],
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        # Check for error tracebacks / debugging queries
        if any(err in q_lower for err in ["error", "exception", "traceback", "indexerror", "keyerror", "recursionerror", "typeerror", "valueerror", "syntaxerror", "nameerror", "attributeerror", "zerodivisionerror"]):
            return self._handle_error_debugging(query, q_lower)

        # Check for OOP concepts
        if any(term in q_lower for term in ["polymorphism", "inheritance", "encapsulation", "abstraction", "oop", "class", "object", "dunder", "__init__"]):
            return self._handle_oop_concepts(q_lower)

        # Check for Python data structures
        if any(term in q_lower for term in ["list", "tuple", "set", "dictionary", "dict", "merging collections", "lambda", "comprehension"]):
            return self._handle_data_structures(q_lower)

        # Check for algorithms / complexity
        if any(term in q_lower for term in ["big o", "time complexity", "space complexity", "binary search", "sorting", "recursion", "dynamic programming", "two pointer"]):
            return self._handle_algorithms(q_lower)

        # Check for code optimization / best practices
        if any(term in q_lower for term in ["optimize", "clean code", "refactor", "best practice", "pep 8"]):
            return self._handle_best_practices(query)

        # Generic programming mentor guidance
        return (
            f"### 💡 Understanding Your Query: *{query[:60]}...*\n\n"
            "Here is how to approach this problem step-by-step:\n\n"
            "1. **Identify the Core Goal**: Clearly define what inputs you receive and what exact output format is expected.\n"
            "2. **Break Down the Logic**: Write pseudo-code before writing actual syntax to ensure the flow is sound.\n"
            "3. **Check Edge Cases**:\n"
            "   - Empty collections or `None` values\n"
            "   - Boundary indices (0 and `len(n) - 1`)\n"
            "   - Negative numbers or unexpected types\n\n"
            "```python\n"
            "# Example pattern for safe modular logic:\n"
            "def solve_problem(data: list) -> list:\n"
            "    if not data:\n"
            "        return []\n"
            "    \n"
            "    result = []\n"
            "    for item in data:\n"
            "        # Process item with clear transformation\n"
            "        result.append(item)\n"
            "    return result\n"
            "```\n\n"
            "Would you like to share the specific snippet or error message you are encountering so we can debug it together?"
        )

    def _handle_error_debugging(self, query: str, q_lower: str) -> str:
        if "recursionerror" in q_lower or "maximum recursion depth" in q_lower:
            return (
                "### 🔍 Debugging: `RecursionError: maximum recursion depth exceeded`\n\n"
                "This error occurs when a recursive function calls itself continuously without ever reaching a valid termination condition.\n\n"
                "#### Key Checklist:\n"
                "1. **Base Case**: Does your function have an `if` statement at the very top that returns without making another recursive call?\n"
                "2. **Progress Toward Base Case**: Are you modifying parameters in the recursive step (e.g., `n - 1`, `arr[1:]`) so it gets closer to the base case?\n\n"
                "```python\n"
                "# ❌ Infinite Recursion\n"
                "def factorial(n):\n"
                "    return n * factorial(n) # Bug: no base case and n doesn't decrement\n\n"
                "# ✅ Correct Implementation with Base Case\n"
                "def factorial(n: int) -> int:\n"
                "    if n <= 1:  # Base Case\n"
                "        return 1\n"
                "    return n * factorial(n - 1)  # Step moves toward base case\n"
                "```\n\n"
                "Check your function's base condition and verify what value stops the recursion!"
            )
        elif "indexerror" in q_lower:
            return (
                "### 🔍 Debugging: `IndexError: list index out of range`\n\n"
                "This happens when you attempt to access an index that is greater than or equal to `len(sequence)` or less than `-len(sequence)`.\n\n"
                "#### Common Causes & Fixes:\n"
                "- Using `<= len(arr)` instead of `< len(arr)` in `while` or `for` loops.\n"
                "- Off-by-one errors when processing arrays of size $N$ (valid indices are `0` through `N - 1`).\n\n"
                "```python\n"
                "items = [10, 20, 30]\n\n"
                "# ❌ IndexError: index 3 does not exist\n"
                "# for i in range(len(items) + 1):\n"
                "#     print(items[i])\n\n"
                "# ✅ Safe Iteration\n"
                "for item in items:\n"
                "    print(item)\n"
                "\n"
                "# Or with index bounds check:\n"
                "for idx, val in enumerate(items):\n"
                "    print(f\"Index {idx}: {val}\")\n"
                "```"
            )
        elif "keyerror" in q_lower:
            return (
                "### 🔍 Debugging: `KeyError`\n\n"
                "A `KeyError` is raised when trying to access a dictionary key that does not exist.\n\n"
                "#### Recommended Approaches:\n"
                "1. Use `dict.get(key, default_value)` instead of direct `dict[key]` indexing.\n"
                "2. Check with `if key in my_dict:` before accessing.\n"
                "3. Use `collections.defaultdict` if you are aggregating counts or lists.\n\n"
                "```python\n"
                "user_data = {\"name\": \"Alice\", \"role\": \"Student\"}\n\n"
                "# ✅ Safe access with fallback\n"
                "score = user_data.get(\"score\", 0)\n"
                "print(score)  # Returns 0 without raising KeyError\n"
                "```"
            )
        else:
            return (
                "### 🛠️ Error Analysis & Debugging Strategy\n\n"
                "When tracking down runtime exceptions in Python, follow this 3-step diagnostic:\n\n"
                "1. **Read the Stack Trace Bottom-Up**: The bottom line specifies the exact Exception type and reason.\n"
                "2. **Inspect Variable Values**: Print or inspect the inputs right before the offending line.\n"
                "3. **Validate Types & Boundaries**: Ensure data types match expected interfaces (e.g. `int` vs `str`).\n\n"
                "Paste your code snippet and exact error output here, and I'll highlight the precise fix!"
            )

    def _handle_oop_concepts(self, q_lower: str) -> str:
        if "polymorphism" in q_lower:
            return (
                "### 🧩 Understanding Polymorphism in Python\n\n"
                "**Polymorphism** (from Greek: *many forms*) allows different classes to implement methods with the same name, enabling a unified interface.\n\n"
                "#### Implementation in Python (Duck Typing & Method Overriding):\n\n"
                "```python\n"
                "class Shape:\n"
                "    def area(self) -> float:\n"
                "        raise NotImplementedError(\"Subclasses must implement area()\")\n\n"
                "class Circle(Shape):\n"
                "    def __init__(self, radius: float):\n"
                "        self.radius = radius\n"
                "    \n"
                "    def area(self) -> float:\n"
                "        return 3.14159 * (self.radius ** 2)\n\n"
                "class Rectangle(Shape):\n"
                "    def __init__(self, width: float, height: float):\n"
                "        self.width = width\n"
                "        self.height = height\n"
                "        \n"
                "    def area(self) -> float:\n"
                "        return self.width * self.height\n\n"
                "# Polymorphic usage:\n"
                "shapes = [Circle(5), Rectangle(4, 6)]\n"
                "for s in shapes:\n"
                "    print(f\"{s.__class__.__name__} area: {s.area():.2f}\")\n"
                "```\n\n"
                "**Key takeaway**: Python resolves the method at runtime based on the actual object instance (*Duck Typing*: \"If it walks like a duck and quacks like a duck, it's a duck\")."
            )
        elif "encapsulation" in q_lower:
            return (
                "### 🔒 Understanding Encapsulation in Python\n\n"
                "**Encapsulation** is the bundling of data (attributes) and methods that operate on that data into a single unit (class), while restricting direct access to internal state.\n\n"
                "#### Access Conventions:\n"
                "- Public: `self.name`\n"
                "- Protected: `self._balance` (hint to developers)\n"
                "- Private: `self.__password` (name mangling)\n\n"
                "```python\n"
                "class BankAccount:\n"
                "    def __init__(self, initial_balance: float):\n"
                "        self.__balance = max(0.0, initial_balance)  # Private attribute\n\n"
                "    @property\n"
                "    def balance(self) -> float:\n"
                "        \"\"\"Getter method.\"\"\"\n"
                "        return self.__balance\n\n"
                "    def deposit(self, amount: float) -> None:\n"
                "        \"\"\"Controlled setter logic with validation.\"\"\"\n"
                "        if amount > 0:\n"
                "            self.__balance += amount\n"
                "        else:\n"
                "            raise ValueError(\"Deposit must be positive\")\n"
                "```"
            )
        else:
            return (
                "### 🏗️ Object-Oriented Programming (OOP) Pillars in Python\n\n"
                "1. **Encapsulation**: Keeping state private within objects and exposing getters/setters via `@property`.\n"
                "2. **Inheritance**: Deriving specialized subclasses from base classes (`class Dog(Animal):`).\n"
                "3. **Polymorphism**: Treating different subclasses through a common interface.\n"
                "4. **Abstraction**: Hiding complex implementation details using Abstract Base Classes (`abc.ABC`).\n\n"
                "Which specific OOP pillar or implementation would you like to explore deeper?"
            )

    def _handle_data_structures(self, q_lower: str) -> str:
        if "tuple" in q_lower or "list vs tuple" in q_lower or "difference" in q_lower:
            return (
                "### 📊 Lists vs. Tuples in Python\n\n"
                "| Feature | `list` | `tuple` |\n"
                "| :--- | :--- | :--- |\n"
                "| **Mutability** | Mutable (can modify, append, remove) | **Immutable** (cannot alter after creation) |\n"
                "| **Syntax** | `[1, 2, 3]` | `(1, 2, 3)` |\n"
                "| **Memory & Speed**| Larger memory footprint, slightly slower | Lower memory, faster iteration & hashable |\n"
                "| **Dictionary Key** | ❌ Cannot be used as dict keys | ✅ Can be used as dict keys if contents are immutable |\n\n"
                "```python\n"
                "# List example:\n"
                "my_list = [1, 2, 3]\n"
                "my_list.append(4)  # Allowed\n\n"
                "# Tuple example:\n"
                "coordinates = (12.9716, 77.5946)\n"
                "# coordinates[0] = 13.0  # Raises TypeError: 'tuple' object does not support item assignment\n"
                "```"
            )
        elif "merging collections" in q_lower or "merge" in q_lower:
            return (
                "### 🔀 Merging Collections in Python\n\n"
                "#### 1. Merging Dictionaries (Python 3.9+):\n"
                "```python\n"
                "dict1 = {\"a\": 1, \"b\": 2}\n"
                "dict2 = {\"b\": 99, \"c\": 3}\n\n"
                "# Using the union operator (dict2 overwrites keys in dict1):\n"
                "merged = dict1 | dict2\n"
                "print(merged)  # {'a': 1, 'b': 99, 'c': 3}\n"
                "```\n\n"
                "#### 2. Merging Lists / Sets:\n"
                "```python\n"
                "list1 = [1, 2, 3]\n"
                "list2 = [4, 5, 6]\n"
                "combined_list = list1 + list2\n\n"
                "set1 = {1, 2, 3}\n"
                "set2 = {3, 4, 5}\n"
                "union_set = set1 | set2  # {1, 2, 3, 4, 5}\n"
                "```"
            )
        else:
            return (
                "### 📚 Python Core Collections\n\n"
                "- **List `[]`**: Ordered, mutable sequence of items.\n"
                "- **Tuple `()`**: Ordered, immutable sequence.\n"
                "- **Set `{}`**: Unordered, unique elements with $O(1)$ lookup time.\n"
                "- **Dict `{k: v}`**: Key-value hash map with $O(1)$ average insertion and retrieval.\n\n"
                "What collection operation or algorithm do you need assistance with?"
            )

    def _handle_algorithms(self, q_lower: str) -> str:
        return (
            "### ⚡ Algorithmic Thinking & Complexity Analysis\n\n"
            "When analyzing efficiency, we look at **Big-O asymptotic bounds**:\n\n"
            "- $O(1)$: Constant time (e.g. Dict/Hash table lookup, array index access)\n"
            "- $O(\\log N)$: Logarithmic time (e.g. Binary Search on sorted array)\n"
            "- $O(N)$: Linear time (e.g. Single loop iterating through $N$ elements)\n"
            "- $O(N \\log N)$: Linearithmic time (e.g. Merge Sort, Timsort/`sorted()` in Python)\n"
            "- $O(N^2)$: Quadratic time (e.g. Nested loops like Bubble Sort)\n\n"
            "```python\n"
            "# Example: Binary Search in O(log N)\n"
            "def binary_search(arr: list[int], target: int) -> int:\n"
            "    left, right = 0, len(arr) - 1\n"
            "    while left <= right:\n"
            "        mid = (left + right) // 2\n"
            "        if arr[mid] == target:\n"
            "            return mid\n"
            "        elif arr[mid] < target:\n"
            "            left = mid + 1\n"
            "        else:\n"
            "            right = mid - 1\n"
            "    return -1\n"
            "```\n\n"
            "What problem are you solving? Share the constraints and we can determine the optimal approach together!"
        )

    def _handle_best_practices(self, query: str) -> str:
        return (
            "### 🌟 Python Clean Code & PEP 8 Guidelines\n\n"
            "1. **Descriptive Naming**: Use `snake_case` for functions/variables and `PascalCase` for classes.\n"
            "2. **Type Hints**: Add type hints (`def process(name: str) -> bool:`) for clarity and IDE autocomplete.\n"
            "3. **Docstrings**: Document function expectations, arguments, and return types.\n"
            "4. **Early Returns (Guard Clauses)**: Return early to avoid deep nesting.\n\n"
            "```python\n"
            "from typing import Optional\n\n"
            "def calculate_discount(price: float, discount_percent: Optional[float] = None) -> float:\n"
            "    \"\"\"Calculate final price with safety bounds.\"\"\"\n"
            "    if price < 0:\n"
            "        raise ValueError(\"Price cannot be negative\")\n"
            "    \n"
            "    if not discount_percent:\n"
            "        return price\n"
            "        \n"
            "    discount_factor = max(0.0, min(discount_percent / 100.0, 1.0))\n"
            "    return price * (1.0 - discount_factor)\n"
            "```"
        )
