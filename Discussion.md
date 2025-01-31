## Binary Search Algorithm: Assuming its sorted 

### Overview
Binary search is a highly efficient search algorithm that operates on sorted data by repeatedly dividing the search interval in half. In our log file processing context, it's particularly valuable for quickly locating specific dates within a large (1TB) chronologically ordered log file.

### Basic Principle
1. Start with the entire search range
2. Find the middle element
3. Compare target with middle element
4. Eliminate half of the remaining elements
5. Repeat until target is found or range is empty

--------------------------------
## After failing to implement binary search, I came to know its unsorted data.####
--------------------------------

## Chunk-based Processing:
Reads file in large chunks (100MB) for efficient I/O
Processes each chunk line by line
Handles lines that span chunk boundaries
## Concurrent Processing:
Uses a separate thread for writing output
Main thread focuses on reading and matching
Uses a queue to buffer matches between threads
## Memory Efficient:
Streams data instead of loading entire file
Only keeps matching lines in memory
Uses a bounded queue to prevent memory overflow

