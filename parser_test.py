import unittest

import parser


class TestParse(unittest.TestCase):
    def test_tokenize_predicate(self):
        predicate_str = "a = b and b = 2"
        tokens = parser.tokenize_predicate(predicate_str)
        self.assertEquals(['a', '=', 'b', 'and', 'b', '=', '2'], tokens)
        predicate_str = "a=1 and b =c"
        tokens = parser.tokenize_predicate(predicate_str)
        self.assertEquals(['a', '=', '1', 'and', 'b', '=', 'c'], tokens)
        predicate_str = "a= 1 or b = c"
        tokens = parser.tokenize_predicate(predicate_str)
        self.assertEquals(['a', '=', '1', 'or', 'b', '=', 'c'], tokens)
        predicate_str = "not a= 1 or not b = c"
        tokens = parser.tokenize_predicate(predicate_str)
        self.assertEquals(["not", 'a', '=', '1', 'or', "not", 'b', '=', 'c'], tokens)

    def test_parse_table_and_column_names(self):
        for use_tree_parser in {True, False}:
            query = "select a from t where b = 100"
            cols, table, predicate = parser.parse_query(query, use_tree_parser)
            self.assertEquals(["a"], cols)
            self.assertEquals("t", table)
            self.assertEquals(True, predicate(b=100))
            self.assertEquals(False, predicate(b=110))
            query = "select a,b, c from t where not b = 100 and c = 1 or a = 2"
            cols, table, predicate = parser.parse_query(query, use_tree_parser)
            self.assertEquals(["a", "b", "c"], cols)
            self.assertEquals("t", table)
            self.assertEquals(True, predicate(b=100, a=2, c=1))
            self.assertEquals(False, predicate(b=110, c=2, a=3))
            query = "select a , b, c from t where not b = 100 and c = 1 or a = 2"
            cols, table, predicate = parser.parse_query(query, use_tree_parser)
            self.assertEquals(["a", "b", "c"], cols)
            self.assertEquals("t", table)
            self.assertEquals(True, predicate(b=100, a=2, c=1))
            self.assertEquals(False, predicate(b=110, c=2, a=3))

    def test_instantiate_predicates(self):
        for pred_instantiaters in {parser.instantiate_predicates, parser.get_tree_predicate_instantiater}:
            predicate_str = "a = b and b = 2"
            tokens = parser.tokenize_predicate(predicate_str)
            pred = pred_instantiaters(tokens)
            self.assertEquals(True, pred(a=2, b=2))
            self.assertEquals(False, pred(a=1, b=2))
            self.assertEquals(True, pred(a=2, b=2, c=4))
            self.assertEquals(False, pred(a=1, b=2, c=9))
            predicate_str = "a = b and b = 2 or a = 1"
            tokens = parser.tokenize_predicate(predicate_str)
            pred = pred_instantiaters(tokens)
            self.assertEquals(True, pred(a=1, b=2, c=9))
            self.assertEquals(True, pred(a=2, b=2, c=9))
            self.assertEquals(False, pred(a=3, b=2, c=9))
            predicate_str = "a = b and b = 2 and a = 1"
            tokens = parser.tokenize_predicate(predicate_str)
            pred = pred_instantiaters(tokens)
            self.assertEquals(False, pred(a=1, b=2, c=9))
            self.assertEquals(False, pred(a=2, b=2, c=9))
            predicate_str = "a = b and not b = 2 or a = 1"
            tokens = parser.tokenize_predicate(predicate_str)
            pred = pred_instantiaters(tokens)
            self.assertEquals(False, pred(a=2, b=2, c=9))
            self.assertEquals(True, pred(a=3, b=3, c=9))
            self.assertEquals(True, pred(a=1, b=2, c=9))
            predicate_str = "not a = b and not a = 3 and c = 4 or c = 10 or a = 11 and not b = 19 or not c = 100"
            tokens = parser.tokenize_predicate(predicate_str)
            pred = pred_instantiaters(tokens)
            self.assertEquals(False, pred(a=2, b=2, c=100))
            self.assertEquals(True, pred(a=11, b=2, c=100))
            self.assertEquals(True, pred(a=11, b=19, c=4))
            predicate_str = "not a = 1 or not b = 2 or c = 0"
            tokens = parser.tokenize_predicate(predicate_str)
            pred = pred_instantiaters(tokens)
            self.assertEquals(False, pred(a=1, b=2, c=4))
            self.assertEquals(True, pred(a=2, b=2, c=4))
            self.assertEquals(True, pred(a=1, b=9, c=4))
            self.assertEquals(True, pred(a=3, b=4, c=4))
            self.assertEquals(True, pred(a=1, b=2, c=0))
            predicate_str = "not a = 1 and b = c and c = 7"
            tokens = parser.tokenize_predicate(predicate_str)
            pred = pred_instantiaters(tokens)
            self.assertEquals(True, pred(a=2, b=7, c=7))
            self.assertEquals(False, pred(a=1, b=7, c=7))
            predicate_str = "not not a = 1"
            tokens = parser.tokenize_predicate(predicate_str)
            pred = pred_instantiaters(tokens)
            self.assertEquals(True, pred(a=1, b=7, c=7))
            self.assertEquals(False, pred(a=2, b=7, c=7))
            predicate_str = "not not a = 1 and not not not b = 2"
            tokens = parser.tokenize_predicate(predicate_str)
            pred = pred_instantiaters(tokens)
            self.assertEquals(True, pred(a=1, b=7, c=7))
            self.assertEquals(False, pred(a=1, b=2, c=7))
            self.assertEquals(False, pred(a=2, b=3, c=7))

            predicate = "a = 1 and b = 2".split(" ")
            pred = pred_instantiaters(predicate)
            self.assertEquals(True, pred(a=1, b=2))
            self.assertEquals(False, pred(a=2, b=2))
            self.assertEquals(False, pred(a=1, b=4))
            self.assertEquals(False, pred(a=4, b=4))

            predicate = "a = 1 or b = 2".split(" ")
            pred = pred_instantiaters(predicate)
            self.assertEquals(True, pred(a=1, b=2))
            self.assertEquals(True, pred(a=2, b=2))
            self.assertEquals(True, pred(a=1, b=4))
            self.assertEquals(False, pred(a=4, b=4))

            predicate = "a = 1 or b = 2 and c = 3".split(" ")
            pred = pred_instantiaters(predicate)
            self.assertEquals(True, pred(a=1, b=3, c=4))
            self.assertEquals(True, pred(a=2, b=2, c=3))
            self.assertEquals(True, pred(a=1, b=2, c=3))
            self.assertEquals(False, pred(a=4, b=4, c=4))

            predicate = "a = 1 or b = 2 and c = 3 or c = 4".split(" ")
            pred = pred_instantiaters(predicate)
            self.assertEquals(True, pred(a=0, b=0, c=4))
            self.assertEquals(True, pred(a=1, b=0, c=0))
            self.assertEquals(True, pred(a=9, b=2, c=3))
            self.assertEquals(False, pred(a=4, b=4, c=5))
            self.assertEquals(True, pred(a=1, b=2, c=3))
            self.assertEquals(True, pred(a=1, b=0, c=4))

            predicate = "a = 1 and b = 2 or c = 3 and a = 4".split(" ")
            pred = pred_instantiaters(predicate)
            self.assertEquals(True, pred(a=1, b=2, c=4))
            self.assertEquals(True, pred(a=4, b=0, c=3))
            self.assertEquals(True, pred(a=4, b=2, c=3))
            self.assertEquals(False, pred(a=1, b=3, c=5))
            self.assertEquals(False, pred(a=4, b=2, c=5))
            self.assertEquals(False, pred(a=4, b=3, c=5))

    def test_exec_query(self):
        tables = {
            "students": [
                {
                    "name": "Amy",
                    "age": 12,
                    "gender": "female"
                },
                {
                    "name": "Bob",
                    "age": 15,
                    "gender": "male"
                },
                {
                    "name": "Cindy",
                    "age": 15,
                    "gender": "female"
                },
                {
                    "name": "Danny",
                    "age": 12,
                    "gender": "female"
                },
                {
                    "name": "Eric",
                    "age": 15,
                    "gender": "male"
                },
                {
                    "name": "Amy",
                    "age": 15,
                    "gender": "female"
                }
            ],
            "shirts": [
                {
                    "color": "orange",
                    "size": "L",
                    "price": 10
                },
                {
                    "color": "red",
                    "size": "S",
                    "price": 10
                },
                {
                    "color": "orange",
                    "size": "M",
                    "price": 12
                },
                {
                    "color": "black",
                    "size": "S",
                    "price": 11
                }
            ]
        }
        for use_tree_parser in {True, False}:
            query = "select name from students where gender = 'male'"
            results = parser.exec_query(query, tables, use_tree_parser)
            self.assertEquals([{'name': 'Bob'}, {'name': 'Eric'}], results)
            query = "select age, gender from students where name = 'Amy'"
            results = parser.exec_query(query, tables, use_tree_parser)
            self.assertEquals([{'age': 12, "gender": 'female'}, {'age': 15, "gender": 'female'}], results)
            query = "select age , gender from students where name = 'Amy' or name = 'Danny'"
            results = parser.exec_query(query, tables, use_tree_parser)
            self.assertEquals([{'age': 12, "gender": 'female'}, {'age': 12, "gender": 'female'}, {'age': 15, "gender": 'female'}], results)
            query = "select age , gender from students where name = 'Amy' and age =  110 or name = 'Danny' and not gender = 'female'"
            results = parser.exec_query(query, tables, use_tree_parser)
            self.assertEquals([], results)
            query = "select color, size, price from shirts where not color = 'orange' or not price = 12"
            results = parser.exec_query(query, tables, use_tree_parser)
            self.assertEquals([
                {
                    "color": "orange",
                    "size": "L",
                    "price": 10
                },
                {
                    "color": "red",
                    "size": "S",
                    "price": 10
                },
                {
                    "color": "black",
                    "size": "S",
                    "price": 11
                }
            ], results)
            query = "select price from shirts where not not color = 'orange' and not not not price =12"
            results = parser.exec_query(query, tables, use_tree_parser)
            self.assertEquals([
                {
                    "price": 10
                },
            ], results)


if __name__ == '__main__':
    unittest.main()
