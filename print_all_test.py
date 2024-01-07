import unittest

import print_all


class TestParse(unittest.TestCase):
    def test_generating_exprs(self):
        for expr_gen in {
            print_all.brute_force_with_record_keeping_entry,
            print_all.bfs_with_memoization
        }:
            self.assertEquals({"1"}, expr_gen(1, 1))
            self.assertEquals({"1", "1 * 1", "1 * 1 * 1", }, expr_gen(5, 1))
            self.assertEquals({"x"}, expr_gen(1, 3))
            self.assertEquals(0, len(expr_gen(1, 4)))
            self.assertEquals(0, len(expr_gen(5, 0)))
            self.assertEquals(0, len(expr_gen(5, 999)))
            self.assertEquals(
                len(print_all.brute_force_with_eval_entry(5, 3)),
                len(expr_gen(5, 3))
            )
            self.assertEquals(
                len(print_all.brute_force_with_eval_entry(9, 24)),
                len(expr_gen(9, 24))
            )
