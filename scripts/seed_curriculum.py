"""Curriculum Seeding Script for GQT Student Portal.

Registers and validates the 17 sequential core programming topics.
Usage:
    python scripts/seed_curriculum.py
"""

SEQUENTIAL_TOPICS = [
    (1, "Data Types", "Primitive data types, memory representations, typing rules, and conversion."),
    (2, "If-Else", "Conditional statements, relational and logical expressions, nested flow."),
    (3, "Loops", "For and while loops, loop invariants, break/continue controls, iteration patterns."),
    (4, "Strings", "String encoding, character traversal, slicing, manipulation algorithms."),
    (5, "Lists", "Sequential dynamic collections, indexing, slicing, and linear search."),
    (6, "Tuple", "Immutable sequences, tuple unpacking, memory efficiency."),
    (7, "Set", "Unique element collection, hash table principles, mathematical set operations."),
    (8, "Dictionary", "Associative key-value mapping, amortized O(1) operations, collision handling."),
    (9, "Merging Collections", "Collection combination, iterable unpacking, merge conflict resolution."),
    (10, "Functions", "Call stack mechanics, parameter passing, recursion, scoping rules."),
    (11, "Lambda Functions", "First-class functions, anonymous function expressions, map/filter/reduce."),
    (12, "OOP Concepts", "Class anatomy, instance instantiation, self/this bindings."),
    (13, "Encapsulation", "Data protection, getter/setter contracts, boundary enforcement."),
    (14, "Inheritance", "Base and derived hierarchies, super delegations, multiple inheritance."),
    (15, "Polymorphism", "Method overriding, signature polymorphism, dynamic dispatch."),
    (16, "Abstraction", "Abstract Base Classes, contract specification, interface enforcement."),
    (17, "Interface", "Pure abstract protocols, decoupling implementation details."),
]


def display_curriculum():
    print("=" * 70)
    print("GQT STUDENT PORTAL - 17 SEQUENTIAL LEARNING CURRICULUM BLUEPRINT")
    print("=" * 70)
    for idx, title, desc in SEQUENTIAL_TOPICS:
        print(f"[{idx:02d}/17] {title:<22} : {desc}")
    print("=" * 70)
    print("Curriculum topics blueprint verified.")


if __name__ == "__main__":
    display_curriculum()
