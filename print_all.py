import math
import time
from collections import deque


def brute_force_with_eval(existing_expr: str, length_limit: int, target: int) -> set[str]:
    if len(existing_expr) > length_limit:
        return set()
    if eval(existing_expr) == target:
        one_extentions = brute_force_with_eval(existing_expr + "*1", length_limit, target)
        return {existing_expr}.union(one_extentions)
    results = set()
    for op in {"+1", "+2", "+3", "+5", "*1", "*2", "*3", "*5"}:
        results = results.union(brute_force_with_eval(existing_expr + op, length_limit, target))
    return results


def brute_force_with_eval_entry(length_limit: int, target: int) -> set[str]:
    l = set
    for i in {"1", "2", "3", "5"}:
        l = l.union(brute_force_with_eval(i, length_limit, target))
    return l


def brute_force_with_record_keeping(existing_expr: str, last_term_value: int, expr_value: int, length_limit: int, target: int) -> set[str]:
    if len(existing_expr) > length_limit or expr_value > target:
        return set()
    if expr_value == target:
        one_extentions = brute_force_with_record_keeping(existing_expr + "*1", last_term_value, expr_value, length_limit, target)
        return {existing_expr}.union(one_extentions)
    results = set()
    for operator in {"+", "*"}:
        operands = {"1": 1, "2": 2, "x": 3, "y": 5}
        for operand in operands:
            if operator == "+":
                new_last_term_val = operands[operand]
                new_expr_val = expr_value + operands[operand]
            else:
                new_last_term_val = last_term_value * operands[operand]
                new_expr_val = new_last_term_val - last_term_value + expr_value
            results = results.union(
                brute_force_with_record_keeping(existing_expr + operator + operand, new_last_term_val, new_expr_val, length_limit, target)
            )
    return results


def brute_force_with_record_keeping_entry(length_limit: int, target: int) -> set[str]:
    l = set
    values = {"x": 3, "y": 5}
    for i in {"1", "2", "x", "y"}:
        i_value = int(i) if i in {"1", "2"} else values[i]
        l = l.union(brute_force_with_record_keeping(i, i_value, i_value, length_limit, target))
    l = {expr.replace("+", " + ").replace("*", " * ") for expr in l}
    return l


def bfs_with_memoization(length_limit: int, target: int) -> set[str]:
    q = deque()
    for i in {("1", 1, 1), ("2", 2, 2), ("x", 3, 3), ("y", 5, 5)}:
        q.appendleft(i)
    cache = {
        1: {1: {("1", 1, 1)}},
        2: {1: {("2", 2, 2)}},
        3: {1: {("x", 3, 3)}},
        5: {1: {("y", 5, 5)}}
    }
    values = {"x": 3, "y": 5}

    def add_to_cache_and_q(cache: dict, q: deque, expr: str, value: int, last_term_value: int):
        if value not in cache:
            cache[value] = {}
        if len(expr) not in cache[value]:
            cache[value][len(expr)] = set()
        cache[value][len(expr)].add((expr, value, last_term_value))
        q.appendleft((expr, value, last_term_value))

    def extend_expr_by_mul(cache: dict, q: deque, expr: str, value: int, last_term_value: int, operand: str):
        operand_val = int(operand) if operand in {"1", "2"} else values[operand]
        mul = expr + "*" + operand
        mul_new_last_term_val = last_term_value * operand_val
        mul_new_val = value + (mul_new_last_term_val - last_term_value)
        add_to_cache_and_q(cache, q, mul, mul_new_val, mul_new_last_term_val)

    half_point = math.floor(length_limit / 2.0)
    while len(q) != 0:
        expr, value, last_term_val = q.pop()
        if len(expr) > length_limit or value > target:
            continue
        if len(expr) < half_point:
            for operand in {"1", "2", "x", "y"}:
                plus = expr + "+" + operand
                operand_val = int(operand) if operand in {"1", "2"} else values[operand]
                plus_new_val = value + operand_val
                plus_new_last_term_val = operand_val
                add_to_cache_and_q(cache, q, plus, plus_new_val, plus_new_last_term_val)

                extend_expr_by_mul(cache, q, expr, value, last_term_val, operand)
        else:
            length_left = length_limit - len(expr)
            value_left = target - value
            if value_left > 0 and value_left in cache:
                cached_exprs = cache[value_left]
                for possible_length in range(1, length_left):
                    if possible_length not in cached_exprs:
                        continue
                    cached_expr_set = cached_exprs[possible_length]
                    for cached_expr_tuple in cached_expr_set:
                        cached_expr, cached_value, cached_last_term_value = cached_expr_tuple
                        new_expr = expr + "+" + cached_expr
                        new_val = value + cached_value
                        new_last_term_val = cached_last_term_value
                        add_to_cache_and_q(cache, q, new_expr, new_val, new_last_term_val)
            for operand in {"1", "2", "x", "y"}:
                extend_expr_by_mul(cache, q, expr, value, last_term_val, operand)
    if target not in cache:
        return set()
    else:
        overall_set = set()
        for length, s in cache[target].items():
            if length > length_limit:
                continue
            for expr_tuple in s:
                overall_set.add(expr_tuple[0])
        return {expr.replace("+", " + ").replace("*", " * ") for expr in overall_set}


if __name__ == '__main__':
    t = time.process_time()
    results = bfs_with_memoization(7, 12)
    elapsed_time = time.process_time() - t
    print(f"Time used: {elapsed_time}")
    print(results)
    print(len(results))
