import { CurriculumTopic } from "../types/curriculum";

export const SEQUENTIAL_CURRICULUM_TOPICS: CurriculumTopic[] = [
  { orderIndex: 1, title: "Data Types", slug: "data-types", description: "Primitive types, numbers, booleans, casting, and memory representation." },
  { orderIndex: 2, title: "If-Else", slug: "if-else", description: "Conditional logic, nested branches, and boolean evaluation." },
  { orderIndex: 3, title: "Loops", slug: "loops", description: "For loops, while loops, loop control statements (break, continue), and nested loops." },
  { orderIndex: 4, title: "Strings", slug: "strings", description: "String manipulation, slicing, immutability, pattern matching, and string formatting." },
  { orderIndex: 5, title: "Lists", slug: "lists", description: "Dynamic arrays, indexing, slicing, comprehensions, and linear search algorithms." },
  { orderIndex: 6, title: "Tuple", slug: "tuple", description: "Immutable sequences, tuple unpacking, and performance considerations." },
  { orderIndex: 7, title: "Set", slug: "set", description: "Unique collections, hash table fundamentals, union, intersection, and difference operations." },
  { orderIndex: 8, title: "Dictionary", slug: "dictionary", description: "Key-value hash maps, hashing mechanisms, dictionary traversal, and frequency mapping." },
  { orderIndex: 9, title: "Merging Collections", slug: "merging-collections", description: "Combining sequences, chaining iterables, unpacking operators, and collision resolution." },
  { orderIndex: 10, title: "Functions", slug: "functions", description: "Scope, stack frames, positional/keyword arguments, recursion, and return signatures." },
  { orderIndex: 11, title: "Lambda Functions", slug: "lambda-functions", description: "Anonymous functions, functional primitives (map, filter, reduce), and closures." },
  { orderIndex: 12, title: "OOP Concepts", slug: "oop-concepts", description: "Object-oriented paradigm, classes, instances, constructors, and self/this references." },
  { orderIndex: 13, title: "Encapsulation", slug: "encapsulation", description: "Data hiding, access specifiers (private/protected/public), and getter/setter invariants." },
  { orderIndex: 14, title: "Inheritance", slug: "inheritance", description: "Class hierarchies, single/multiple inheritance, super calls, and Method Resolution Order (MRO)." },
  { orderIndex: 15, title: "Polymorphism", slug: "polymorphism", description: "Method overriding, operator overloading, and runtime vs compile-time polymorphism." },
  { orderIndex: 16, title: "Abstraction", slug: "abstraction", description: "Abstract Base Classes (ABCs), interface enforcement, and contract-driven design." },
  { orderIndex: 17, title: "Interface", slug: "interface", description: "Strict protocol definitions, multiple interface implementation, and decoupling architecture." },
];
