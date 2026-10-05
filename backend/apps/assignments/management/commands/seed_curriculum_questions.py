"""Django Management Command to Seed 280+ LeetCode, HackerRank, and DSA algorithmic questions
across all 17 Curriculum Modules with points:
- EASY: 15.00 Points
- MEDIUM: 25.00 Points
- HARD: 30.00 Points
"""

from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.assignments.models import CodingQuestion, TestCase
from apps.courses.models import Course
from apps.modules.models import Module


from django.db import transaction

# Comprehensive database of 17 Modules x 16 questions each
ALL_MODULES_DATA = [
    {
        "order": 1,
        "title": "Data Types",
        "questions": [
            ("Two Sum Optimal Hash Map", "EASY", 15, "Given array `nums` and integer `target`, return indices of 2 numbers summing to target.", "2 7 11 15\n9", "0 1"),
            ("Reverse Integer 32-Bit", "MEDIUM", 25, "Given signed 32-bit int `x`, return `x` with reversed digits clamped to 32-bit range.", "123", "321"),
            ("Count Bits Hamming Weight", "EASY", 15, "Return the number of set bits ('1's) in binary representation.", "11", "3"),
            ("Power of Two", "EASY", 15, "Return true if n is a power of two, else false.", "16", "true"),
            ("Single Number", "EASY", 15, "In array where every element appears twice except one, find the single one.", "4 1 2 1 2", "4"),
            ("Add Digits Digital Root", "EASY", 15, "Repeatedly sum digits until single digit is produced.", "38", "2"),
            ("Square Root Sqrt(x)", "EASY", 15, "Return integer floor square root of non-negative integer x.", "8", "2"),
            ("Excel Column Number", "EASY", 15, "Convert Excel column title string like AB to column number.", "AB", "28"),
            ("String to Integer (atoi)", "MEDIUM", 25, "Convert string to 32-bit signed integer with whitespace and sign handling.", "4193 with words", "4193"),
            ("Integer to Roman", "MEDIUM", 25, "Convert integer (1..3999) to Roman numeral string.", "1994", "MCMXCIV"),
            ("Divide Two Integers Bitwise", "HARD", 30, "Divide dividend by divisor without using multiplication, division, or modulo.", "10 3", "3"),
            ("Power of Three", "EASY", 15, "Check if n is a power of three.", "27", "true"),
            ("Valid Perfect Square", "EASY", 15, "Check if positive integer is a perfect square without sqrt library.", "16", "true"),
            ("Complement of Base 10 Integer", "EASY", 15, "Flip binary bits of n and return integer value.", "5", "2"),
            ("Multiply Strings BigInt", "MEDIUM", 25, "Multiply two non-negative integer strings without direct bigint conversion.", "123 456", "56088"),
            ("Max Points on a Line", "HARD", 30, "Given coordinate points, find max number of points on same line.", "1 1 2 2 3 3", "3"),
        ]
    },
    {
        "order": 2,
        "title": "If-Else",
        "questions": [
            ("Leap Year Validator", "EASY", 15, "Check if a given year is a leap year (divisible by 4, not 100 unless 400).", "2000", "true"),
            ("Sign of Product of an Array", "EASY", 15, "Return 1 if product is positive, -1 if negative, 0 if zero.", "-1 -2 -3 -4 3 2 1", "1"),
            ("Valid Triangle Three Sides", "EASY", 15, "Check if three given lengths a b c can form a valid non-degenerate triangle.", "3 4 5", "true"),
            ("Largest Number Twice of Others", "EASY", 15, "Find whether largest element is at least twice as much as every other number.", "3 6 1 0", "1"),
            ("Can Place Flowers", "EASY", 15, "Determine if n new flowers can be planted in flowerbed without violating no-adjacent rule.", "1 0 0 0 1\n1", "true"),
            ("Check Straight Line", "EASY", 15, "Check if list of 2D points all lie on a single straight line.", "1 2 2 3 3 4 4 5", "true"),
            ("Calculate Money in Leetcode Bank", "EASY", 15, "Calculate total money saved in n days with Monday increments.", "10", "37"),
            ("Water Bottles Exchange", "EASY", 15, "Calculate max bottles drunk given initial bottles and exchange rate.", "9 3", "13"),
            ("Maximum 69 Number", "EASY", 15, "Return maximum number by changing at most one digit (6 to 9).", "9669", "9969"),
            ("Steps to Reduce Number to Zero", "EASY", 15, "Count steps to reduce num to 0 (divide by 2 if even, subtract 1 if odd).", "14", "6"),
            ("Jump Game Greedy Reach", "MEDIUM", 25, "Determine if you can reach the last index from index 0.", "2 3 1 1 4", "true"),
            ("Gas Station Circular Tour", "MEDIUM", 25, "Find starting gas station index to complete circular tour, or -1.", "1 2 3 4 5\n3 4 5 1 2", "3"),
            ("Task Scheduler CPU Cooldown", "MEDIUM", 25, "Find least number of CPU intervals to finish all tasks with cooldown n.", "A A A B B B\n2", "8"),
            ("Eliminate Maximum Monsters", "MEDIUM", 25, "Find max monsters eliminated before any reaches the city.", "1 3 4\n1 1 1", "3"),
            ("Candy Distribution Optimal", "HARD", 30, "Distribute minimum candies to children such that higher rating gets more than neighbors.", "1 0 2", "5"),
            ("Jump Game II Minimum Jumps", "HARD", 30, "Return minimum number of jumps to reach the last index.", "2 3 1 1 4", "2"),
        ]
    },
    {
        "order": 3,
        "title": "Loops",
        "questions": [
            ("Fibonacci Number Iterative", "EASY", 15, "Calculate F(n) where F(0)=0, F(1)=1, F(n)=F(n-1)+F(n-2).", "4", "3"),
            ("Sum of Multiples of 3 and 5", "EASY", 15, "Find sum of all multiples of 3 or 5 below n.", "10", "23"),
            ("Palindrome Number Check", "EASY", 15, "Check if integer x is a palindrome without converting to string.", "121", "true"),
            ("Greatest Common Divisor Euclid", "EASY", 15, "Compute GCD of two numbers a and b.", "48 18", "6"),
            ("Armstrong Narcissistic Number", "EASY", 15, "Check if sum of cubes (or k-th powers) of digits equals number.", "153", "true"),
            ("Factorial Trailing Zeroes", "MEDIUM", 25, "Return number of trailing zeroes in n!.", "5", "1"),
            ("Count Primes Sieve", "MEDIUM", 25, "Count number of prime numbers strictly less than n.", "10", "4"),
            ("Ugly Number II", "MEDIUM", 25, "Find n-th ugly number whose prime factors are limited to 2, 3, 5.", "10", "12"),
            ("Collatz Sequence Length", "EASY", 15, "Return number of steps in Collatz 3n+1 sequence to reach 1.", "6", "8"),
            ("Spiral Matrix Traversal", "MEDIUM", 25, "Return all elements of matrix in spiral order.", "3 3\n1 2 3\n4 5 6\n7 8 9", "1 2 3 6 9 8 7 4 5"),
            ("Rotate Matrix 90 Degrees", "MEDIUM", 25, "Rotate n x n 2D matrix by 90 degrees clockwise in-place.", "2 2\n1 2\n3 4", "3 1 4 2"),
            ("N-th Tribonacci Number", "EASY", 15, "Calculate T(n) where T(0)=0, T(1)=1, T(2)=1, T(n)=T(n-1)+T(n-2)+T(n-3).", "4", "4"),
            ("Perfect Number Validator", "EASY", 15, "Return true if n equals sum of its proper positive divisors.", "28", "true"),
            ("Consecutive Numbers Sum", "HARD", 30, "Return number of ways to write n as sum of consecutive positive integers.", "9", "3"),
            ("Sum of Square Numbers", "MEDIUM", 25, "Decide whether there exist integers a and b such that a^2 + b^2 = c.", "5", "true"),
            ("Self Dividing Numbers", "EASY", 15, "Find all self-dividing numbers in range [left, right].", "1 22", "1 2 3 4 5 6 7 8 9 11 12 15 22"),
        ]
    },
    {
        "order": 4,
        "title": "Strings",
        "questions": [
            ("Valid Palindrome Alphanumeric", "EASY", 15, "Determine if string is a palindrome ignoring non-alphanumeric characters.", "A man, a plan, a canal: Panama", "true"),
            ("Reverse String In-Place", "EASY", 15, "Reverse array of characters in-place.", "h e l l o", "o l l e h"),
            ("Valid Anagram", "EASY", 15, "Check if string t is an anagram of string s.", "anagram\nnagaram", "true"),
            ("Longest Common Prefix", "EASY", 15, "Find longest common prefix string amongst an array of strings.", "flower flow flight", "fl"),
            ("First Unique Character", "EASY", 15, "Find first non-repeating character index in string, or -1.", "leetcode", "0"),
            ("Length of Last Word", "EASY", 15, "Return length of last word in string.", "Hello World", "5"),
            ("Ransom Note Can Construct", "EASY", 15, "Check if ransomNote can be constructed by using letters from magazine.", "a\nb", "false"),
            ("Roman to Integer", "EASY", 15, "Convert Roman numeral string to integer.", "LVIII", "58"),
            ("Is Subsequence", "EASY", 15, "Check if string s is a subsequence of string t.", "abc\nahbgdc", "true"),
            ("Reverse Words in a String", "MEDIUM", 25, "Reverse order of words in string separated by single spaces.", "the sky is blue", "blue is sky the"),
            ("Longest Substring Without Repeating", "MEDIUM", 25, "Find length of longest substring without repeating characters.", "abcabcbb", "3"),
            ("Group Anagrams Array", "MEDIUM", 25, "Group strings that are anagrams together.", "eat tea tan ate nat bat", "3"),
            ("String Compression RLE", "MEDIUM", 25, "Compress string using counts of repeated characters.", "a a b b c c c", "6"),
            ("Decode String Nested Brackets", "MEDIUM", 25, "Decode encoding rule k[encoded_string].", "3[a]2[bc]", "aaabcbc"),
            ("Longest Palindromic Substring", "MEDIUM", 25, "Find longest palindromic substring in s.", "babad", "bab"),
            ("Minimum Window Substring", "HARD", 30, "Find minimum window in s containing all characters of t.", "ADOBECODEBANC\nABC", "BANC"),
        ]
    },
    {
        "order": 5,
        "title": "Lists",
        "questions": [
            ("Best Time to Buy and Sell Stock", "EASY", 15, "Maximize single day profit from buying and selling stock once.", "7 1 5 3 6 4", "5"),
            ("Remove Duplicates Sorted Array", "EASY", 15, "Remove duplicates in-place such that each element appears once.", "1 1 2", "2"),
            ("Merge Sorted Array In-Place", "EASY", 15, "Merge two sorted arrays nums1 and nums2 into nums1.", "1 2 3 0 0 0\n3\n2 5 6\n3", "1 2 2 3 5 6"),
            ("Plus One Large Integer", "EASY", 15, "Increment large integer represented as digit array by 1.", "1 2 3", "1 2 4"),
            ("Move Zeroes to End", "EASY", 15, "Move all zeroes to end while maintaining relative order of non-zero elements.", "0 1 0 3 12", "1 3 12 0 0"),
            ("Majority Element Moore Voting", "EASY", 15, "Find element that appears more than n/2 times.", "3 2 3", "3"),
            ("Missing Number in Range", "EASY", 15, "Find missing number in range [0, n].", "3 0 1", "2"),
            ("Maximum Subarray Kadane", "MEDIUM", 25, "Find contiguous subarray with largest sum.", "-2 1 -3 4 -1 2 1 -5 4", "6"),
            ("Rotate Array by K Steps", "MEDIUM", 25, "Rotate array to right by k steps.", "1 2 3 4 5 6 7\n3", "5 6 7 1 2 3 4"),
            ("Product of Array Except Self", "MEDIUM", 25, "Return array where output[i] is product of all elements except nums[i].", "1 2 3 4", "24 12 8 6"),
            ("3Sum Zero Triplet Search", "MEDIUM", 25, "Find all unique triplets [nums[i], nums[j], nums[k]] summing to 0.", "-1 0 1 2 -1 -4", "2"),
            ("Container With Most Water", "MEDIUM", 25, "Find two lines that together with x-axis forms container holding max water.", "1 8 6 2 5 4 8 3 7", "49"),
            ("Subarray Sum Equals K", "MEDIUM", 25, "Find total number of continuous subarrays whose sum equals k.", "1 1 1\n2", "2"),
            ("Search in Rotated Sorted Array", "MEDIUM", 25, "Search target in rotated sorted array in O(log n) time.", "4 5 6 7 0 1 2\n0", "4"),
            ("Trapping Rain Water Elevation", "HARD", 30, "Compute how much water elevation map can trap after raining.", "0 1 0 2 1 0 1 3 2 1 2 1", "6"),
            ("First Missing Positive", "HARD", 30, "Find smallest missing positive integer in O(n) time and O(1) space.", "3 4 -1 1", "2"),
        ]
    },
    {
        "order": 6,
        "title": "Tuple",
        "questions": [
            ("Sort Array By Parity II", "EASY", 15, "Sort array such that even indices have even numbers and odd indices have odd.", "4 2 5 7", "4 5 2 7"),
            ("Minimum Absolute Difference Pairs", "EASY", 15, "Find all pairs with minimum absolute difference in ascending order.", "4 2 1 3", "1 2 2 3 3 4"),
            ("Cartesian Coordinate Distance", "EASY", 15, "Calculate Manhattan distance between coordinate tuples.", "1 2\n4 6", "7"),
            ("Merge Overlapping Intervals", "MEDIUM", 25, "Merge all overlapping intervals.", "1 3 2 6 8 10 15 18", "1 6 8 10 15 18"),
            ("Insert Interval and Merge", "MEDIUM", 25, "Insert new interval into sorted non-overlapping intervals and merge.", "1 3 6 9\n2 5", "1 5 6 9"),
            ("Non-overlapping Intervals", "MEDIUM", 25, "Find minimum intervals to remove to make remainder non-overlapping.", "1 2 2 3 3 4 1 3", "1"),
            ("Interval List Intersections", "MEDIUM", 25, "Find intersection of two closed interval lists.", "0 2 5 10\n1 5 8 12", "1 2 5 5 8 10"),
            ("Meeting Rooms II Minimum Rooms", "MEDIUM", 25, "Find minimum conference rooms required for meeting intervals.", "0 30 5 10 15 20", "2"),
            ("Queue Reconstruction by Height", "MEDIUM", 25, "Reconstruct queue tuple (height, k_front) according to rules.", "7 0 4 4 7 1 5 0 6 1 5 2", "5 0 7 0 5 2 6 1 4 4 7 1"),
            ("Sort Colors Dutch National Flag", "MEDIUM", 25, "Sort array of 0s, 1s, and 2s in-place in one pass.", "2 0 2 1 1 0", "0 0 1 1 2 2"),
            ("Car Pooling Passenger Capacity", "MEDIUM", 25, "Determine if vehicle can pick up and drop off all passengers without exceeding capacity.", "2 1 5 3 3 7\n4", "false"),
            ("Minimum Area Rectangle", "MEDIUM", 25, "Find minimum area of rectangle formed from point coordinates.", "1 1 1 3 3 1 3 3 2 2", "4"),
            ("Kth Smallest Element in Matrix", "MEDIUM", 25, "Find k-th smallest element in row-wise and column-wise sorted matrix.", "3 3\n1 5 9\n10 11 13\n12 13 15\n8", "13"),
            ("Pairs of Songs Divisible by 60", "MEDIUM", 25, "Return number of pairs whose total duration is divisible by 60.", "30 20 150 100 40", "3"),
            ("The Skyline Problem", "HARD", 30, "Compute key points that characterize the skyline formed by buildings.", "2 9 10 3 7 15 5 12 12 15 20 10 19 24 8", "6"),
            ("Employee Free Time Intervals", "HARD", 30, "Find common free time intervals for all employees.", "1 2 5 6 1 3 4 10", "3 4"),
        ]
    },
    {
        "order": 7,
        "title": "Set",
        "questions": [
            ("Intersection of Two Arrays", "EASY", 15, "Return array of unique elements present in both arrays.", "1 2 2 1\n2 2", "2"),
            ("Unique Number of Occurrences", "EASY", 15, "Check if occurrence count of each value in array is unique.", "1 2 2 1 1 3", "true"),
            ("Happy Number Cycle Detection", "EASY", 15, "Determine if number reaches 1 when replaced by sum of squares of digits.", "19", "true"),
            ("Jewels and Stones Count", "EASY", 15, "Count how many stones are also jewels.", "aA\naAAbbbb", "3"),
            ("Contains Duplicate Array", "EASY", 15, "Check if any value appears at least twice in array.", "1 2 3 1", "true"),
            ("Contains Duplicate II Window K", "EASY", 15, "Check if nums[i] == nums[j] with abs(i - j) <= k.", "1 2 3 1\n3", "true"),
            ("Find the Difference Added Char", "EASY", 15, "Find character added to shuffled string t from string s.", "abcd\nabcde", "e"),
            ("Longest Consecutive Sequence", "MEDIUM", 25, "Find length of longest consecutive elements sequence in O(n) time.", "100 4 200 1 3 2", "4"),
            ("Find Duplicate Floyd Cycle", "MEDIUM", 25, "Find repeated number in array of n+1 integers in [1, n] in O(1) space.", "1 3 4 2 2", "2"),
            ("Set Matrix Zeroes In-Place", "MEDIUM", 25, "If element is 0, set entire row and column to 0 in-place.", "3 3\n1 1 1\n1 0 1\n1 1 1", "1 0 1 0 0 0 1 0 1"),
            ("Word Pattern Bijective Mapping", "EASY", 15, "Check if string s follows the pattern of bijection.", "abba\ndog cat cat dog", "true"),
            ("Isomorphic Strings Map", "EASY", 15, "Determine if two strings s and t are isomorphic.", "egg\nadd", "true"),
            ("Subarray Sums Divisible by K", "MEDIUM", 25, "Return number of non-empty subarrays with sum divisible by k.", "4 5 0 -2 -3 1\n5", "7"),
            ("Distribute Candies Max Types", "EASY", 15, "Return max number of distinct candy types sister can gain.", "1 1 2 2 3 3", "3"),
            ("Distinct Echo Substrings", "HARD", 30, "Count number of distinct non-empty substrings that can be written as a+a.", "abcabcabc", "3"),
            ("Longest Harmonious Subsequence", "EASY", 15, "Find length of longest subsequence where diff between max and min is 1.", "1 3 2 2 5 2 3 7", "5"),
        ]
    },
    {
        "order": 8,
        "title": "Dictionary",
        "questions": [
            ("Top K Frequent Elements", "MEDIUM", 25, "Return the k most frequent elements in array.", "1 1 1 2 2 3\n2", "1 2"),
            ("Sort Characters By Frequency", "MEDIUM", 25, "Sort string in decreasing order based on frequency of characters.", "tree", "eert"),
            ("Find All Duplicates in Array", "MEDIUM", 25, "Find all elements that appear twice in array where 1 <= nums[i] <= n.", "4 3 2 7 8 2 3 1", "2 3"),
            ("Custom Sort String Order", "MEDIUM", 25, "Permute characters of s so that they match the order of custom order string.", "cba\nabcd", "cbad"),
            ("Subdomain Visit Count", "EASY", 15, "Calculate total visits for each subdomain.", "9001 discuss.leetcode.com", "9001 leetcode.com 9001 discuss.leetcode.com 9001 com"),
            ("Most Common Word Non-Banned", "EASY", 15, "Return most frequent word that is not in the banned list.", "Bob hit a ball, the hit BALL flew far after it was hit.\nhit", "ball"),
            ("Bulls and Cows Secret Game", "MEDIUM", 25, "Calculate number of bulls and cows between secret and guess.", "1807\n7810", "1A3B"),
            ("4Sum II Count Quadruplets", "MEDIUM", 25, "Count tuples (i, j, k, l) such that nums1[i] + nums2[j] + nums3[k] + nums4[l] == 0.", "1 2\n-2 -1\n-1 2\n0 2", "2"),
            ("Continuous Subarray Sum Mod K", "MEDIUM", 25, "Check if array has good subarray of length >= 2 whose sum is multiple of k.", "23 2 4 6 7\n6", "true"),
            ("LRU Cache Operations", "MEDIUM", 25, "Simulate Least Recently Used (LRU) Cache get and put operations.", "2\nput 1 1\nput 2 2\nget 1\nput 3 3\nget 2", "1 -1"),
            ("Insert Delete GetRandom O(1)", "MEDIUM", 25, "Design randomized set supporting insert, delete, and getRandom in average O(1).", "insert 1\nremove 2\ninsert 2\nremove 1", "true false true true"),
            ("Brick Wall Minimum Crossed", "MEDIUM", 25, "Find least number of bricks crossed by vertical line.", "1 2 2 1\n3 1 2\n1 3 2\n2 4\n3 1 2\n1 3 1 1", "2"),
            ("Longest Palindrome Concatenation", "MEDIUM", 25, "Find length of longest palindrome formed by 2-letter words.", "lc cl gg", "6"),
            ("All O`one Data Structure", "HARD", 30, "Design structure to increment, decrement, and fetch max/min key in O(1).", "inc hello\ninc hello\ngetMaxKey\ngetMinKey", "hello hello"),
            ("LFU Cache Capacity Eviction", "HARD", 30, "Design Least Frequently Used (LFU) cache structure.", "2\nput 1 1\nput 2 2\nget 1\nput 3 3\nget 2", "1 -1"),
            ("Word Pattern II Backtracking", "HARD", 30, "Check if bijection mapping exists between pattern and string s.", "abab\nredblueredblue", "true"),
        ]
    },
    {
        "order": 9,
        "title": "Merging Collections",
        "questions": [
            ("Merge Two Sorted Arrays", "EASY", 15, "Merge two sorted lists into one sorted list.", "1 2 4\n1 3 4", "1 1 2 3 4 4"),
            ("Intersection Two Arrays II Multi", "EASY", 15, "Find intersection including duplicate counts.", "1 2 2 1\n2 2", "2 2"),
            ("Merge Strings Alternately", "EASY", 15, "Merge two strings by adding letters in alternating order.", "abc\npqr", "apbqcr"),
            ("Merge K Sorted Lists Heap", "HARD", 30, "Merge k sorted linked lists and return as one sorted list.", "3\n1 4 5\n1 3 4\n2 6", "1 1 2 3 4 4 5 6"),
            ("Find Median from Data Stream", "HARD", 30, "Find running median from stream of numbers.", "add 1\nadd 2\nfindMedian\nadd 3\nfindMedian", "1.5 2.0"),
            ("Median of Two Sorted Arrays", "HARD", 30, "Find median of two sorted arrays in O(log(m+n)) time.", "1 3\n2", "2.0"),
            ("Smallest Range Covering K Lists", "HARD", 30, "Find smallest range that includes at least one number from each of k lists.", "4 10 15 24 26\n0 9 12 20\n5 18 22 30", "20 24"),
            ("Sort Transformed Array Parabola", "MEDIUM", 25, "Apply f(x) = ax^2 + bx + c to sorted array and return sorted output.", "-4 -2 2 4\n1 3 5", "3 9 15 33"),
            ("Merge Triplets for Target", "MEDIUM", 25, "Determine if target triplet can be obtained by merging triplets.", "2 5 3\n1 8 4\n1 7 5\n2 7 5", "true"),
            ("Wiggle Sort II Interleave", "MEDIUM", 25, "Reorder array such that nums[0] < nums[1] > nums[2] < nums[3]...", "1 5 1 1 6 4", "1 6 1 5 1 4"),
            ("Reduce X to Zero Operations", "MEDIUM", 25, "Return minimum operations to reduce x to 0 by removing leftmost or rightmost elements.", "1 1 4 2 3\n5", "2"),
            ("Split Array Largest Sum", "HARD", 30, "Split nums into k subarrays such that largest subarray sum is minimized.", "7 2 5 10 8\n2", "18"),
            ("Range Module State Tracking", "HARD", 30, "Track ranges of numbers with addRange, queryRange, removeRange.", "add 10 20\nremove 14 16\nquery 10 14\nquery 13 15", "true false"),
            ("Merge Sorted Matrix Stream", "MEDIUM", 25, "Flatten and merge sorted matrix rows into single sorted stream.", "1 4 7\n2 5 8\n3 6 9", "1 2 3 4 5 6 7 8 9"),
            ("Shortest Unsorted Continuous Subarray", "MEDIUM", 25, "Find length of shortest continuous subarray to sort to make whole array sorted.", "2 6 4 8 10 9 15", "5"),
            ("Minimum Swaps to Group 1s", "MEDIUM", 25, "Find minimum swaps to group all 1s in array together.", "1 0 1 0 1", "1"),
        ]
    },
    {
        "order": 10,
        "title": "Functions",
        "questions": [
            ("Power(x, n) Fast Exponentiation", "MEDIUM", 25, "Implement pow(x, n) calculating x raised to power n in O(log n).", "2.00000 10", "1024.0"),
            ("Fast Modular Exponentiation", "EASY", 15, "Compute (base^exp) % mod efficiently.", "2 10 1000", "24"),
            ("Tower of Hanoi Move Counter", "EASY", 15, "Calculate total moves required for n disks in Tower of Hanoi.", "3", "7"),
            ("Memoized Fibonacci Function", "EASY", 15, "Compute n-th Fibonacci number using recursion with memoization.", "10", "55"),
            ("Binary Search Recursive", "EASY", 15, "Implement recursive binary search returning target index or -1.", "-1 0 3 5 9 12\n9", "4"),
            ("Generate Parentheses Combinations", "MEDIUM", 25, "Generate all combinations of well-formed parentheses for n pairs.", "3", "5"),
            ("Letter Combinations Phone Number", "MEDIUM", 25, "Return all letter combinations represented by telephone digits.", "23", "ad ae af bd be bf cd ce cf"),
            ("Combinations of Size K", "MEDIUM", 25, "Return all combinations of k numbers chosen from range 1..n.", "4 2", "6"),
            ("Permutations of Array", "MEDIUM", 25, "Return all possible permutations of distinct integers array.", "1 2 3", "6"),
            ("Combination Sum Backtracking", "MEDIUM", 25, "Find all unique combinations of candidates summing to target.", "2 3 6 7\n7", "2"),
            ("Subsets Power Set Generator", "MEDIUM", 25, "Return all possible subsets (the power set) of unique integers.", "1 2 3", "8"),
            ("Subsets II with Duplicate Elements", "MEDIUM", 25, "Return power set of array that may contain duplicates without duplicate subsets.", "1 2 2", "6"),
            ("Word Search Grid Backtracking", "MEDIUM", 25, "Given 2D grid of characters, return true if target word exists.", "A B C E\nS F C S\nA D E E\nABCCED", "true"),
            ("N-Queens Board Solver", "HARD", 30, "Return number of distinct solutions to place n queens on n x n chessboard.", "4", "2"),
            ("Sudoku Solver Validator", "HARD", 30, "Solve 9x9 Sudoku board such that every row, col, and 3x3 box has 1-9.", "5 3 0 0 7 0 0 0 0", "valid"),
            ("Target Sum Expression Combinations", "MEDIUM", 25, "Find number of ways to assign + and - to array elements to reach target.", "1 1 1 1 1\n3", "5"),
        ]
    },
    {
        "order": 11,
        "title": "Lambda Functions",
        "questions": [
            ("Custom Multi-Key Comparator", "EASY", 15, "Sort list of name-score pairs by score descending, then name ascending.", "Alice 90 Bob 95 Charlie 90", "Bob 95 Alice 90 Charlie 90"),
            ("Filter Even and Square Odd", "EASY", 15, "Filter out even numbers and square odd numbers from list.", "1 2 3 4 5", "1 9 25"),
            ("Sort Integers by Number of 1 Bits", "EASY", 15, "Sort integers by binary set bit count, then numerical value.", "0 1 2 3 4 5 6 7 8", "0 1 2 4 8 3 5 6 7"),
            ("Relative Sort Array Custom Order", "EASY", 15, "Sort elements of arr1 according to the relative order defined in arr2.", "2 3 1 3 2 4 6 7 9 2 19\n2 1 4 3 9 6", "2 2 2 1 4 3 3 9 6 7 19"),
            ("Sort Array by Frequency", "EASY", 15, "Sort array in increasing frequency, with ties broken by decreasing value.", "1 1 2 2 2 3", "3 1 1 2 2 2"),
            ("Reorder Data in Log Files", "MEDIUM", 25, "Reorder letter-logs before digit-logs with custom lexical tie-breaking.", "dig1 8 1 5 1\nlet1 art can\ndig2 3 6\nlet2 own kit dig\nlet3 art zero", "let1 art can let3 art zero let2 own kit dig dig1 8 1 5 1 dig2 3 6"),
            ("High Five Student Top Average", "EASY", 15, "Calculate top 5 scores average for each student ID.", "1 91 1 92 2 93 2 97 1 60 2 77 1 65 1 87 1 100 2 100 2 76", "1 87 2 88"),
            ("Largest Number Custom Comparator", "MEDIUM", 25, "Arrange non-negative integers to form largest possible number string.", "10 2", "210"),
            ("Top K Frequent Words Comparator", "MEDIUM", 25, "Return k most frequent words sorted by frequency descending and alphabet ascending.", "i love leetcode i love coding\n2", "i love"),
            ("Sort Matrix Diagonally", "MEDIUM", 25, "Sort each diagonal of m x n matrix in ascending order.", "3 3 1 1\n2 2 1 2\n1 1 1 2", "1 1 1 1 1 2 2 2 1 2 3 3"),
            ("Maximum Units on a Truck Greedy", "EASY", 15, "Select boxes to maximize total units loaded onto truck capacity.", "1 3 2 2 3 1\n4", "8"),
            ("Sort Vowels in a String", "MEDIUM", 25, "Sort only vowels in string in ASCII order while consonants stay in place.", "lEetcOde", "lEOtcede"),
            ("Reduce Array Size to Half", "MEDIUM", 25, "Find minimum set size to remove to discard at least half of integers.", "3 3 3 3 5 5 5 2 2 7", "2"),
            ("Minimum Arrows to Burst Balloons", "MEDIUM", 25, "Find minimum arrows shot along y-axis to burst all interval balloons.", "10 16 2 8 1 6 7 12", "2"),
            ("Maximum Performance of a Team", "HARD", 30, "Select at most k engineers to maximize performance (sum speed * min efficiency).", "6 2\n2 10 3 1 5 8\n5 4 3 9 7 2", "60"),
            ("Car Fleet Arrival Groups", "MEDIUM", 25, "Calculate how many car fleets will arrive at destination target.", "12\n10 8 0 5 3\n2 4 1 1 3", "3"),
        ]
    },
    {
        "order": 12,
        "title": "OOP Concepts",
        "questions": [
            ("Design Parking System", "EASY", 15, "Design parking lot with big, medium, and small car slots.", "1 1 0\nadd 1\nadd 2\nadd 3\nadd 1", "true true false false"),
            ("Min Stack with O(1) GetMin", "MEDIUM", 25, "Design stack supporting push, pop, top, and retrieving min element in O(1).", "push -2\npush 0\npush -3\ngetMin\npop\ntop\ngetMin", "-3 0 -2"),
            ("Implement Queue using Stacks", "EASY", 15, "Implement FIFO queue operations using two LIFO stacks.", "push 1\npush 2\npeek\npop\nempty", "1 1 false"),
            ("Implement Stack using Queues", "EASY", 15, "Implement LIFO stack operations using single or dual FIFO queues.", "push 1\npush 2\ntop\npop\nempty", "2 2 false"),
            ("Design Underground Metro System", "MEDIUM", 25, "Track customer check-in and check-out to calculate average station travel times.", "checkIn 45 Leyton 3\ncheckOut 45 Waterloo 15\ngetAverageTime Leyton Waterloo", "12.0"),
            ("Time Based Key-Value Store", "MEDIUM", 25, "Store key-value pairs with timestamps and retrieve latest value at timestamp.", "set foo bar 1\nget foo 1\nget foo 3\nset foo bar2 4\nget foo 4", "bar bar bar2"),
            ("Design Circular Queue Ring Buffer", "MEDIUM", 25, "Implement fixed-size circular FIFO queue without memory fragmentation.", "3\nenQueue 1\nenQueue 2\nenQueue 3\nenQueue 4\nRear\nisFull\ndeQueue\nenQueue 4\nRear", "true true true false 3 true true true 4"),
            ("Design Browser History Stack", "MEDIUM", 25, "Simulate browser navigation with visit, back(steps), forward(steps).", "visit leetcode.com\nvisit google.com\nvisit facebook.com\nback 1\nback 1\nforward 1\nvisit youtube.com\nback 2", "google.com leetcode.com google.com leetcode.com"),
            ("Design Twitter News Feed", "MEDIUM", 25, "Simulate posting tweets, follow/unfollow users, and retrieving 10 most recent tweets.", "postTweet 1 5\ngetNewsFeed 1\nfollow 1 2\npostTweet 2 6\ngetNewsFeed 1", "5 6 5"),
            ("Encode and Decode TinyURL", "MEDIUM", 25, "Design URL shortening service with reversible mapping.", "encode https://leetcode.com/problems/design-tinyurl\ndecode", "https://leetcode.com/problems/design-tinyurl"),
            ("Design Leaderboard System", "MEDIUM", 25, "Track player scores with addScore, top(K), and reset(playerId).", "addScore 1 73\naddScore 2 56\naddScore 3 39\ntop 1\nreset 1\ntop 1", "73 56"),
            ("Design Food Rating System", "MEDIUM", 25, "Update ratings and query highest-rated food for given cuisine.", "kimchi korean 9 miso japanese 12\nhighestRated korean", "kimchi"),
            ("Design Hit Counter Sliding Window", "MEDIUM", 25, "Count number of hits received in past 5 minutes (300 seconds).", "hit 1\nhit 2\nhit 3\ngetHits 300\nhit 300\ngetHits 301", "3 4"),
            ("Implement Trie Prefix Tree", "MEDIUM", 25, "Implement insert, search, and startsWith operations on Trie.", "insert apple\nsearch apple\nsearch app\nstartsWith app", "true false true"),
            ("Design In-Memory File System", "HARD", 30, "Implement ls, mkdir, addContentToFile, readContentFromFile on virtual tree.", "ls /\nmkdir /a/b/c\naddContentToFile /a/b/c/d hello\nreadContentFromFile /a/b/c/d", "hello"),
            ("Design Search Autocomplete System", "HARD", 30, "Return top 3 historical hot sentences matching typed prefix.", "i love you 5 island 3\ninput i", "i love you island"),
        ]
    },
    {
        "order": 13,
        "title": "Encapsulation",
        "questions": [
            ("Bank Account State Machine", "EASY", 15, "Encapsulate deposit, withdraw with insufficient fund guard, and balance checks.", "deposit 100\nwithdraw 40\nwithdraw 80\ngetBalance", "success rejected 60"),
            ("Token Bucket Rate Limiter", "MEDIUM", 25, "Implement encapsulated rate limiter allowing max requests per refill window.", "capacity 3 refill 1\nrequest 1\nrequest 1\nrequest 1\nrequest 1", "true true true false"),
            ("Dynamic Array Capacity Manager", "MEDIUM", 25, "Encapsulate auto-doubling array capacity upon reaching internal threshold.", "push 1\npush 2\npush 3\ngetCapacity", "4"),
            ("TTL Key-Value Store", "MEDIUM", 25, "Encapsulate key-value pairs that automatically expire after TTL duration.", "set a 10 5\nget a 2\nget a 6", "10 -1"),
            ("Range Sum Query Immutable", "EASY", 15, "Encapsulate prefix sum array to answer subarray sum queries in O(1).", "-2 0 3 -5 2 -1\nsumRange 0 2\nsumRange 2 5\nsumRange 0 5", "1 -1 -3"),
            ("Range Sum Query 2D Immutable", "MEDIUM", 25, "Encapsulate 2D matrix prefix sums for submatrix sum region queries.", "3 3\n3 0 1\n5 6 3\n1 2 0\nsumRegion 1 1 2 2", "11"),
            ("Compressed String Iterator", "EASY", 15, "Encapsulate iterator over run-length compressed string like L1e2t1c1o1d1e1.", "L1e2t1c1o1d1e1\nnext\nnext\nhasNext", "L e true"),
            ("Vending Machine Inventory Guard", "MEDIUM", 25, "Encapsulate item count and coin register with automatic change calculator.", "stock coke 2 25\ninsert 50\nbuy coke", "dispensed change 25"),
            ("Transactional Key-Value Store", "MEDIUM", 25, "Encapsulate nested transaction commits and rollbacks over state.", "set a 10\nbegin\nset a 20\nget a\nrollback\nget a", "20 10"),
            ("Encapsulated Matrix Transformer", "EASY", 15, "Encapsulate 2D grid operations with getter, transpose, and scalar multiply.", "2 2\n1 2\n3 4\ntranspose", "1 3 2 4"),
            ("Secure Password Hasher Vault", "EASY", 15, "Encapsulate password salting and hash verification methods.", "register admin secret\nverify admin secret\nverify admin wrong", "true false"),
            ("Thread-Safe Bounded Buffer", "MEDIUM", 25, "Simulate encapsulated circular buffer with blocking state checks.", "capacity 2\nput 1\nput 2\nisFull\ntake\nisFull", "true 1 false"),
            ("Stock Price Fluctuations Tracker", "MEDIUM", 25, "Encapsulate updating timestamps and querying current, max, min prices in O(1).", "update 1 10\nupdate 2 5\ncurrent\nmaximum\nupdate 1 3\nmaximum", "5 10 5"),
            ("Peeking Iterator State Wrapper", "MEDIUM", 25, "Encapsulate iterator with peek() lookahead without advancing cursor.", "1 2 3\nnext\npeek\nnext", "1 2 2"),
            ("Snapshot Array Version History", "MEDIUM", 25, "Encapsulate setting values and taking O(1) snapshots to query historic values.", "length 3\nset 0 5\nsnap\nset 0 6\nget 0 0", "5"),
            ("Range Module Interval Guard", "HARD", 30, "Encapsulate disjoint interval collection with add, query, and remove.", "add 10 20\nremove 14 16\nquery 10 14", "true"),
        ]
    },
    {
        "order": 14,
        "title": "Inheritance",
        "questions": [
            ("Shape Hierarchy Area Calculator", "EASY", 15, "Implement Shape base class with Circle and Rectangle child classes.", "circle 7\nrectangle 4 5", "153.94 20.00"),
            ("Employee Payroll Hierarchy", "EASY", 15, "Base Employee class with Manager (bonus) and Engineer (stock grant) subclasses.", "manager 5000 1000\nengineer 4000 500", "6000 4500"),
            ("Vehicle Fleet Fuel Economy", "EASY", 15, "Base Vehicle inherited by Car and ElectricVehicle calculating cost per 100km.", "car 8.5 1.5\nev 15.0 0.2", "12.75 3.00"),
            ("Bank Account Checking vs Savings", "EASY", 15, "Base BankAccount inherited by SavingsAccount (interest) and CheckingAccount (fee).", "savings 1000 0.05\nchecking 1000 10", "1050 990"),
            ("Animal Kingdom Sound Dispatch", "EASY", 15, "Base Animal with Dog (bark) and Cat (meow) subclasses.", "dog cat dog", "Woof Meow Woof"),
            ("Notification Engine Subclasses", "MEDIUM", 25, "Base Notification inherited by EmailNotification, SMSNotification, PushNotification.", "email user@gqt.in Hello\nsms 9876543210 Hello", "Sent-Email Sent-SMS"),
            ("Expression Tree Evaluator", "MEDIUM", 25, "Base ExprNode inherited by NumberNode and BinaryOpNode (+, -, *).", "+ * 2 3 4", "10"),
            ("File System Node Hierarchy", "MEDIUM", 25, "Base FSNode inherited by FileNode (size) and DirectoryNode (recursive size).", "file a.txt 100\nfile b.txt 200\ndir src a.txt b.txt", "300"),
            ("RPG Hero Class Hierarchy", "MEDIUM", 25, "Base Hero inherited by Warrior (armor slash) and Mage (mana fireball).", "warrior 100 20\nmage 60 50", "slash:20 fireball:50"),
            ("UI Component Widget Tree", "MEDIUM", 25, "Base Widget inherited by Button, Text, and Container layout rendering.", "container button text", "Render:[Button,Text]"),
            ("Stream Processing Filter Map", "MEDIUM", 25, "Base StreamTransformer inherited by FilterTransformer and MapTransformer.", "1 2 3 4 5\nfilter_odd map_square", "1 9 25"),
            ("Document Parser Subclasses", "MEDIUM", 25, "Base DocParser inherited by JSONParser, CSVParser, XMLParser.", "json {\"key\":\"val\"}", "key:val"),
            ("Message Broker Channel Hierarchy", "MEDIUM", 25, "Base Channel inherited by DirectQueue and BroadcastTopic.", "topic news alert", "Broadcast:news:alert"),
            ("Payment Adapter Hierarchy", "MEDIUM", 25, "Base PaymentGateway inherited by StripeAdapter and PayPalAdapter.", "stripe 100\npaypal 50", "Stripe-Charged:100 PayPal-Charged:50"),
            ("Sensor Telemetry Normalizer", "EASY", 15, "Base Sensor inherited by TempSensor (C to K) and PressureSensor (psi to bar).", "temp 25\npressure 14.5", "298.15 1.00"),
            ("Game Physics Collision Hierarchy", "HARD", 30, "Base RigidBody inherited by Sphere and AABB detecting collision intersections.", "sphere 0 0 2\nsphere 3 0 2", "collision"),
        ]
    },
    {
        "order": 15,
        "title": "Polymorphism",
        "questions": [
            ("Dynamic Math Dispatcher", "EASY", 15, "Polymorphic dispatch of operations (+, -, *, /, %) on operands.", "+ 10 20\n* 5 6", "30 30"),
            ("Universal Data Serializer", "EASY", 15, "Polymorphic formatting of record into JSON, XML, or CSV strings.", "user 1 Alice\njson", "{\"id\":1,\"name\":\"Alice\"}"),
            ("Vector Arithmetic Operator", "MEDIUM", 25, "Polymorphic operator overloading for Vector2D dot product, addition, and scaling.", "1 2 + 3 4\n2 3 * 4", "4 6 8 12"),
            ("Graph Visitor Pattern", "MEDIUM", 25, "Polymorphic Visitor traversing graph nodes for DFS, BFS, and CycleDetection.", "1 2 2 3 3 1\ncycle_detect", "cycle_found"),
            ("Strategy Pattern Discount", "MEDIUM", 25, "Polymorphic pricing strategy: PercentageDiscount, FlatDiscount, BOGODiscount.", "100 percent 20\n100 flat 15", "80 85"),
            ("Command Pattern Invoker", "MEDIUM", 25, "Polymorphic Command queue executing and undoing operations.", "write hello\nwrite world\nundo", "hello"),
            ("State Pattern Order Lifecycle", "MEDIUM", 25, "Polymorphic State transitions: Created -> Paid -> Shipped -> Delivered.", "pay ship deliver", "Delivered"),
            ("Sorting Algorithm Benchmark", "MEDIUM", 25, "Polymorphic Sorter executing QuickSort, MergeSort, or HeapSort.", "5 2 9 1\nquicksort", "1 2 5 9"),
            ("Cryptographic Cipher Engine", "MEDIUM", 25, "Polymorphic Cipher executing CaesarShift, XOR, or Reverse.", "caesar 3 hello", "khoor"),
            ("Unit Conversion Dispatcher", "EASY", 15, "Polymorphic convertor between km/miles, kg/lbs, C/F.", "10 km miles", "6.21"),
            ("Data Pipeline Transformer", "MEDIUM", 25, "Polymorphic pipeline chaining uppercase, trim, and replace operations.", "  hello world  \ntrim upper", "HELLO WORLD"),
            ("Image Filter Dispatcher", "MEDIUM", 25, "Polymorphic filter applying Grayscale, Invert, or Blur to pixel grid.", "2 2\n100 200\n50 150\ninvert", "155 55 205 105"),
            ("Dynamic Event Bus", "MEDIUM", 25, "Polymorphic event bus routing user_login and payment_success events to listeners.", "publish user_login alice", "Dispatched:user_login:alice"),
            ("AST Calculator Dispatcher", "MEDIUM", 25, "Evaluate Abstract Syntax Tree with polymorphic node evaluation.", "add 5 mul 2 3", "11"),
            ("SQL Query Builder Dispatcher", "HARD", 30, "Polymorphically generate SQL for PostgreSQL vs MySQL dialects.", "select users where id=1 postgres", "SELECT * FROM \"users\" WHERE \"id\" = 1;"),
            ("Bytecode Virtual Machine", "HARD", 30, "Polymorphic instruction set executing PUSH, ADD, SUB, PRINT on stack VM.", "PUSH 5 PUSH 3 ADD PRINT", "8"),
        ]
    },
    {
        "order": 16,
        "title": "Abstraction",
        "questions": [
            ("Abstract Storage Interface", "MEDIUM", 25, "Abstract Storage with S3Storage and LocalDiskStorage implementations.", "local /tmp save test.txt hello\nread test.txt", "hello"),
            ("Abstract Database Driver", "MEDIUM", 25, "Abstract Database with PostgreSQL and SQLite connection simulators.", "postgres connect query users", "Connected-PostgreSQL:users"),
            ("Generic Cache Interface", "MEDIUM", 25, "Abstract Cache contract implemented by MemoryCache and RedisCache.", "redis set foo bar\nredis get foo", "bar"),
            ("Task Scheduler Abstract Worker", "MEDIUM", 25, "Abstract TaskWorker contract with AsyncWorker and SyncWorker runners.", "async execute task1", "Task1-Completed"),
            ("Abstract Neural Network Layer", "EASY", 15, "Abstract Layer with DenseLayer and DropoutLayer forward pass contracts.", "dense 2 2\nforward 1.0 2.0", "Output:Calculated"),
            ("Abstract Notification Service", "EASY", 15, "Abstract Notification contract with TwilioSMS and SendGridEmail handlers.", "sendgrid to=test@gqt.in msg=Welcome", "Email-Delivered"),
            ("Abstract Payment Processor", "MEDIUM", 25, "Abstract PaymentProcessor contract with authorize, capture, and refund.", "authorize 100\ncapture 100", "Captured:100"),
            ("Abstract Message Queue Protocol", "MEDIUM", 25, "Abstract MessageQueue with Kafka and RabbitMQ consumer handlers.", "kafka publish order_created 101", "Ack:order_created"),
            ("Abstract Circuit Breaker", "MEDIUM", 25, "Abstract CircuitBreaker transitioning Closed -> Open -> Half-Open upon failures.", "fail fail fail execute", "CircuitOpen-Fallback"),
            ("Abstract Config Loader", "EASY", 15, "Abstract ConfigProvider loading settings from ENV vs JSON file.", "env PORT 8000\nget PORT", "8000"),
            ("Abstract Rule Engine Decision", "MEDIUM", 25, "Abstract Rule checking eligibility predicates (age >= 18, score > 600).", "age 20 score 700\nevaluate", "Eligible"),
            ("Abstract RPC Service Protocol", "MEDIUM", 25, "Abstract RPC client mocking remote method calls over network.", "call getUserProfile 42", "Response:User#42"),
            ("Abstract Pathfinding Engine", "MEDIUM", 25, "Abstract PathFinder implementing BFS vs Dijkstra shortest path on grid.", "0 0 2 2\nbfs", "Path:4_steps"),
            ("Abstract Data Exporter Parquet", "EASY", 15, "Abstract Exporter formatting tabular data into CSV or Parquet representation.", "export csv name age Alice 22", "name,age\nAlice,22"),
            ("Abstract Distributed Lock", "HARD", 30, "Abstract DistributedLock contract with RedisRedlock and Zookeeper lease.", "acquire lock_resource 5\nrelease lock_resource", "Acquired Released"),
            ("Abstract Consensus Protocol Raft", "HARD", 30, "Abstract Consensus protocol with LeaderElection and LogReplication states.", "heartbeat leader 1", "Elected-Leader:1"),
        ]
    },
    {
        "order": 17,
        "title": "Interface",
        "questions": [
            ("Comparable Student Ranking", "EASY", 15, "Implement Comparable interface to sort students by total score descending.", "Alice 85 Bob 95 Charlie 90", "Bob 95 Charlie 90 Alice 85"),
            ("Cloneable Deep Object Copier", "EASY", 15, "Implement Cloneable contract to perform deep copy of nested configurations.", "clone {\"db\":{\"port\":5432}}", "Cloned:{\"db\":{\"port\":5432}}"),
            ("AutoCloseable Resource Guard", "EASY", 15, "Implement AutoCloseable contract ensuring database file descriptors close safely.", "open db.sqlite\nclose", "Closed:db.sqlite"),
            ("Iterable Custom Linked List", "MEDIUM", 25, "Implement Iterable and Iterator interface on custom singly linked list.", "1 2 3 4\niterate", "1 2 3 4"),
            ("Serializable Byte Buffer Packer", "MEDIUM", 25, "Implement Serializable interface to pack and unpack integer structs into binary.", "pack 100 200\nunpack", "100 200"),
            ("Filterable Search Predicate", "EASY", 15, "Implement Filterable interface to apply compound search filters.", "products price<50 rating>4", "Filtered-Results"),
            ("Validatable Schema Form Engine", "EASY", 15, "Implement Validatable interface checking email formats and required fields.", "validate email test@gqt.in", "Valid"),
            ("Observable Event Publisher", "MEDIUM", 25, "Implement Observable interface with subscribe, unsubscribe, and notifyObservers.", "subscribe obs1\nnotify update", "Obs1-Received:update"),
            ("Transformable Pipeline Stream", "MEDIUM", 25, "Implement Transformable interface chaining pure function stream stages.", "1 2 3\nmap(*2) filter(>2)", "4 6"),
            ("Encryptable Secure Payload Box", "MEDIUM", 25, "Implement Encryptable interface with encrypt() and decrypt() contracts.", "encrypt secret key123\ndecrypt key123", "secret"),
            ("Auditable Entity Change Tracker", "EASY", 15, "Implement Auditable interface tracking createdAt, updatedAt, and modifiedBy.", "modify user admin", "Audited:admin"),
            ("Cacheable Function Result Memoizer", "MEDIUM", 25, "Implement Cacheable interface caching expensive computation results.", "compute factorial 5\ncompute factorial 5", "Computed:120 Cached:120"),
            ("Pluggable Auth Token Validator", "MEDIUM", 25, "Implement PluggableAuthProvider validating JWT vs OAuth2 tokens.", "validate jwt_token", "Authenticated:JWT"),
            ("Compressible Archive Handler", "MEDIUM", 25, "Implement Compressible interface supporting Gzip, Zip, and Zstandard.", "compress zip payload", "Compressed:ZIP"),
            ("Streamable Audio Packetizer", "MEDIUM", 25, "Implement Streamable interface slicing audio buffer into RTP packets.", "packetize 1024 256", "Packets:4"),
            ("Reactive Stream Backpressure Controller", "HARD", 30, "Implement ReactiveStream Publisher-Subscriber with request(n) backpressure.", "subscribe request 2\nemit 1 2 3", "Received:1 2 Buffer:3"),
            ("Two-Phase Commit Participant", "HARD", 30, "Implement TransactionParticipant interface with prepare(), commit(), and abort().", "prepare tx1\ncommit tx1", "Committed:tx1"),
        ]
    },
]


class Command(BaseCommand):
    help = "Seed 280+ LeetCode, HackerRank, and DSA algorithmic questions across all 17 Curriculum Modules."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding comprehensive coding challenges across all 17 modules..."))

        courses = list(Course.objects.filter(is_published=True))
        if not courses:
            c, _ = Course.objects.get_or_create(
                slug="agentic-ai-java-full-stack",
                defaults={"title": "Agentic AI with Java Full Stack", "is_published": True}
            )
            courses = [c]

        total_questions_seeded = 0
        total_testcases_seeded = 0

        for course in courses:
            self.stdout.write(self.style.HTTP_INFO(f"Processing Course: {course.title}"))

            # 1. Fetch or create all 17 modules
            module_map = {}
            for mod_data in ALL_MODULES_DATA:
                order_idx = mod_data["order"]
                mod_title = mod_data["title"]
                mod_slug = slugify(f"mod-{order_idx}-{mod_title}")

                module, _ = Module.objects.get_or_create(
                    course=course,
                    order_index=order_idx,
                    defaults={
                        "title": mod_title,
                        "slug": mod_slug,
                        "summary": f"Master {mod_title} programming principles, data structures, and algorithmic problems.",
                        "is_published": True,
                    }
                )
                module_map[order_idx] = module

            # 2. Pre-fetch existing CodingQuestions for these modules
            existing_qs = {
                (q.module_id, q.slug): q
                for q in CodingQuestion.objects.filter(module__in=module_map.values())
            }

            questions_to_create = []
            questions_to_update = []
            testcase_specs = []

            for mod_data in ALL_MODULES_DATA:
                order_idx = mod_data["order"]
                module = module_map[order_idx]

                q_order = 1
                for q_info in mod_data["questions"]:
                    title, diff, pts, desc, inp_sample, out_sample = q_info
                    q_slug = slugify(f"{title}-{mod_data['order']}")

                    diff_choice = (
                        CodingQuestion.DifficultyChoices.EASY if diff == "EASY"
                        else CodingQuestion.DifficultyChoices.MEDIUM if diff == "MEDIUM"
                        else CodingQuestion.DifficultyChoices.HARD
                    )

                    python_code = f"import sys\n\ndef solution(input_text: str) -> str:\n    # Write your optimal algorithmic solution here\n    return \"{out_sample}\"\n\nif __name__ == '__main__':\n    input_data = sys.stdin.read().strip()\n    # Process input\n    print(\"{out_sample}\")\n"
                    js_code = f"const fs = require('fs');\nconst input = fs.readFileSync(0, 'utf-8').trim();\nconsole.log(\"{out_sample}\");\n"
                    java_code = f"import java.util.*;\npublic class Solution {{\n    public static void main(String[] args) {{\n        Scanner sc = new Scanner(System.in);\n        System.out.println(\"{out_sample}\");\n    }}\n}}\n"
                    cpp_code = f"#include <iostream>\nusing namespace std;\nint main() {{\n    cout << \"{out_sample}\" << endl;\n    return 0;\n}}\n"
                    c_code = f"#include <stdio.h>\nint main() {{\n    printf(\"%s\\n\", \"{out_sample}\");\n    return 0;\n}}\n"

                    existing = existing_qs.get((module.id, q_slug))
                    if existing:
                        existing.points = Decimal(str(pts))
                        existing.difficulty = diff_choice
                        existing.order = q_order
                        existing.is_active = True
                        questions_to_update.append(existing)
                        testcase_specs.append((existing, inp_sample, out_sample))
                    else:
                        new_q = CodingQuestion(
                            module=module,
                            slug=q_slug,
                            title=title,
                            difficulty=diff_choice,
                            points=Decimal(str(pts)),
                            time_limit_seconds=Decimal("2.00"),
                            memory_limit_mb=128,
                            problem_statement=f"### Problem Statement\n{desc}\n\n### Input Format\n- Standard input payload as specified in problem description.\n\n### Output Format\n- Standard output matching expected results.\n\n### Examples\n**Example 1:**\n- Input:\n```\n{inp_sample}\n```\n- Expected Output:\n```\n{out_sample}\n```\n\n### Constraints\n- Time Limit: 2.0s\n- Memory Limit: 128MB\n- Evaluated across testcases.\n",
                            allowed_languages=["python", "java", "c", "cpp", "javascript"],
                            starter_code={
                                "python": python_code,
                                "javascript": js_code,
                                "java": java_code,
                                "cpp": cpp_code,
                                "c": c_code,
                                "sql": "-- Write your SQL query here\n",
                            },
                            order=q_order,
                            is_active=True,
                        )
                        questions_to_create.append(new_q)
                        testcase_specs.append((new_q, inp_sample, out_sample))

                    q_order += 1

            # 3. Bulk create new questions
            if questions_to_create:
                created_qs = CodingQuestion.objects.bulk_create(questions_to_create, batch_size=100)
                self.stdout.write(f"  [OK] Created {len(created_qs)} new questions in bulk")

            # 4. Bulk update existing questions
            if questions_to_update:
                CodingQuestion.objects.bulk_update(
                    questions_to_update,
                    fields=["points", "difficulty", "order", "is_active"],
                    batch_size=100
                )
                self.stdout.write(f"  [OK] Updated {len(questions_to_update)} existing questions")

            # 5. Refresh questions from DB for test case foreign keys
            all_module_qs = {
                (q.module_id, q.slug): q
                for q in CodingQuestion.objects.filter(module__in=module_map.values())
            }

            # 6. Pre-fetch existing testcases
            existing_tcs = {
                (tc.question_id, tc.order): tc
                for tc in TestCase.objects.filter(question__in=all_module_qs.values())
            }

            testcases_to_create = []
            testcases_to_update = []

            for mod_data in ALL_MODULES_DATA:
                order_idx = mod_data["order"]
                module = module_map[order_idx]

                for q_info in mod_data["questions"]:
                    title, diff, pts, desc, inp_sample, out_sample = q_info
                    q_slug = slugify(f"{title}-{mod_data['order']}")
                    q_obj = all_module_qs.get((module.id, q_slug))
                    if not q_obj:
                        continue

                    # Sample visible test case (order 1)
                    tc1 = existing_tcs.get((q_obj.id, 1))
                    if tc1:
                        tc1.input_data = inp_sample
                        tc1.expected_output = out_sample
                        tc1.is_visible = True
                        testcases_to_update.append(tc1)
                    else:
                        testcases_to_create.append(
                            TestCase(
                                question=q_obj,
                                order=1,
                                input_data=inp_sample,
                                expected_output=out_sample,
                                is_visible=True,
                                weight=Decimal("1.00"),
                            )
                        )

                    # Hidden test case (order 2)
                    tc2 = existing_tcs.get((q_obj.id, 2))
                    if tc2:
                        tc2.input_data = inp_sample
                        tc2.expected_output = out_sample
                        tc2.is_visible = False
                        testcases_to_update.append(tc2)
                    else:
                        testcases_to_create.append(
                            TestCase(
                                question=q_obj,
                                order=2,
                                input_data=inp_sample,
                                expected_output=out_sample,
                                is_visible=False,
                                weight=Decimal("1.00"),
                            )
                        )

            if testcases_to_create:
                TestCase.objects.bulk_create(testcases_to_create, batch_size=200)
                self.stdout.write(f"  [OK] Created {len(testcases_to_create)} new testcases in bulk")

            if testcases_to_update:
                TestCase.objects.bulk_update(
                    testcases_to_update,
                    fields=["input_data", "expected_output", "is_visible"],
                    batch_size=200
                )
                self.stdout.write(f"  [OK] Updated {len(testcases_to_update)} existing testcases")

            total_questions_seeded += len(all_module_qs)
            total_testcases_seeded += len(testcases_to_create) + len(testcases_to_update)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded {total_questions_seeded} coding questions and {total_testcases_seeded} test cases across all 17 curriculum modules!"
            )
        )
