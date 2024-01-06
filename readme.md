# Attempts to the Problems
## Question 1
Please refer to the `print_all.py` file for my implementation of the problem. If my understanding of the problem is correct, the problem can be 
simplied as "finding all arithmetic expressions with only addition and multiplication operations and integers in the set of {1, 2, 3, 5}, 
of at most L characters that evaluate to N." I consider operators taking lengths as well though the solution should be basically the same if operators don't count
into the length of expressions.

I have three implementations to the problem. The first one is to use recursion to enumerate all possible arithmetic expressions no longer than L and
evaluate them with the `eval` function of Python. Then I keep the ones that evaluate to N. I use this as a quick implementation to test out my other 
implementations. Please see the `brute_force_with_eval_entry` function for the details.

The second implementation uses brute-force recursion as well but I keep track of the values of the expressions and the values of the last term (value of the
expression after the last plus sign). I also try to use early stop when the existing expression is already larger than N. Please see the `brute_force_with_record_keeping_entry`
for details.

The time complexity of the brute-force solution is roughly O(4^L). To improve the complexity is not easy. I try to remember all the evaluations of expressions
generated in a breadth first search and after the search level has a length higher than half of the length limit, I can get all the previously 
generated expressions and try to add them to the existing expression to get the target value. The complexity is still exponential but in my experiments, this 
method can save time in the order of ten or more when the length limit is long. Please see the `bfs_with_memoization` function for more details.

## Question 2
Please refer to the `proof_correctness_binary_search.ipynb` file.

## Question 3
Please refer to the `parser.py` and `parser_test.py` for the implementation and unit tests.
First of all, the given grammar for Predicate P is ambiguous as the grammar does not dictate the precedence of the "and," "or," and "not" operators. 
I assume that when evaluating a predicate, the "not" operator takes the highest precedence, the "and" operator has a lower precedence than the "not" operator 
, and the "or" operator has the lowest precedence. Also, given the production rule of Predicate P not including parenthesis, 
I just assume this grammar does not use parenthesis to elevate the precedence of operators.

Because of the simplicity and the ambiguity of the requirement, I did not try to implement a complete parser for the overall SQL grammar. 
Instead, the high-level idea is to use pattern matching to parse everything except the Predicate and the Column names. 
Column names are easy as comas separate them. 

For the Predicate, I tried two ways of parsing. For the first way of parsing it, I divide the overall Predicate into segments separated by
"or" operators. Then, I divide each segment by "and" to get simple predicates. For each simple Predicate, 
I count the number of "not" shown to see if it is negated. For each simple Predicate, 
I generate a function that takes column names and their values as arguments and returns a boolean value indicating if the Predicate is satisfied. 
I use logical and operation to evaluate the result of each segment and use logical or operation to evaluate the overall Predicate. Please refer to the `instantiate_predicates`
function in `parser.py` for this implementation.

For the second way of parsing it, I first rewrite the grammar to take precedence into consideration and remove left recursion and common prefixes.
The rewritten grammar is given in the comment at the top of the `SimplePredicate` class in `parser.py`. Then, I build a parse tree from a list of tokens
of the Predicate. When evaluating the Predicate, I traverse the parse tree. The entry to this implementation is the `get_tree_predicate_instantiater` function in
`parser.py`.

Regardless of the way of parsing, the overall entry to the implementation is the `exec_query` function `parser.py`. I use a dictionary to represent a
row of tables where the keys of such dictionaries are the names of the columns and the values are values of the cells of the tables. A table is then a list
of such dictionaries. The `tables` parameter of the function is a dictionary of such "tables" keyed by table names. The `use_tree_parser` parameter indicates
if the recursive descent parsing method is used. The function returns a list of dictionaries representing the rows meeting the requirements specified by the Predicate.

For both methods, I did not attempt to write a complete lexer and instead used white space as a token separator to save some tedious work.
