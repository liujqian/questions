from __future__ import annotations
from typing import Callable


def exec_query(query: str, tables: dict[str, list[dict]], use_tree_parser: bool = False) -> list[dict]:
    cols, table_name, pred = parse_query(query, use_tree_parser)
    table = tables[table_name]
    selected = [{col: row[col] for col in cols} for row in table if pred(**row)]
    return selected


def parse_query(query: str, use_tree_parser: bool) -> (list[str], str, Callable[..., bool]):
    query = query.replace("\t", " ").strip()
    split_where = query.split("where")
    if len(split_where) != 2:
        raise ValueError("The number of 'where' in the query is invalid.")
    predicate_str = split_where[-1].strip()
    predicate_toks = tokenize_predicate(predicate_str)
    if not use_tree_parser:
        predicate_func = instantiate_predicates(predicate_toks)
    else:
        predicate_func = get_tree_predicate_instantiater(predicate_toks)
    split_from = split_where[0].split("from")
    table_name = split_from[-1].strip()
    col_list = list(map(lambda col_name: col_name.strip(), split_from[0].strip().removeprefix("select").strip().split(",")))
    return col_list, table_name, predicate_func


def tokenize_predicate(predicate: str) -> list[str]:
    raw_tokens = predicate.split(" ")
    processed_predicate_toks = []
    for tok in raw_tokens:
        tok = tok.strip()
        if len(tok) == 0:
            continue
        if "=" in tok and len(tok) != 1:  # Try to handle the case where there is no space between symbols and "="
            sub_tokens = tok.split("=")
            if len(sub_tokens) != 2:
                raise ValueError("Invalid predicate: " + predicate)
            if sub_tokens[0] == "":
                sub_tokens[0] = "="
            elif sub_tokens[-1] == "":
                sub_tokens[-1] = '='
            else:
                sub_tokens = [sub_tokens[0], "=", sub_tokens[-1]]
            processed_predicate_toks.extend(sub_tokens)

        else:
            processed_predicate_toks.append(tok)
    return processed_predicate_toks


########################################################################################################################
# Implementation of the predicate parser 1:
# Find all the locations of the "and" and "or" operators and evaluate the intervals between the operators hierarchically.
########################################################################################################################
def instantiate_predicates(tokens: list[str]) -> Callable[..., bool]:
    or_indices = [i for i, token in enumerate(tokens) if token == "or"]
    or_intervals = slice_list(tokens, or_indices)
    predicates = list(map(parse_or_interval, or_intervals))

    def pass_any(**kwargs) -> bool:
        return any([pred(**kwargs) for pred in predicates])

    return pass_any


def parse_or_interval(tokens: list[str]) -> Callable[..., bool]:
    and_indices = [i for i, token in enumerate(tokens) if token == "and"]
    and_intervals = slice_list(tokens, and_indices)
    predicates = list(map(parse_simple_predicate, and_intervals))

    def pass_all(**kwargs) -> bool:
        return all([pred(**kwargs) for pred in predicates])

    return pass_all


def slice_list(l: list, cuts: list[int]) -> list[list]:
    start_idx = 0
    intervals = []
    for idx in cuts:
        intervals.append((start_idx, idx))
        start_idx = idx + 1
    intervals.append((start_idx, len(l)))
    slices = [l[start:end] for start, end in intervals]
    return slices


def parse_simple_predicate(tokens: list[str]) -> Callable[..., bool]:
    if len(tokens) < 3:
        raise ValueError(f"Invalid simple predicate received for parsing: {tokens}")
    if len(tokens) > 3 and tokens[0:-3] != ["not"] * len(tokens[0:-3]):
        raise ValueError(f"Invalid simple predicate received for parsing: {tokens}")

    has_not = len(tokens) > 3 and (len(tokens) - 3) % 2
    compare_col = check_token_type(tokens[-1]) == "symbol"
    if not compare_col:
        value_type = check_token_type(tokens[-1])
        if value_type == "int":
            compare_target = int(tokens[-1])
        elif value_type == "float":
            compare_target = float(tokens[-1])
        else:
            compare_target = tokens[-1][1:-1]
    else:
        compare_target = tokens[-1]

    def simple_predicate(**kwargs) -> bool:
        arg1 = tokens[-3]
        arg2 = compare_target
        if compare_col and arg2 not in kwargs:
            raise ValueError("Invalid comparison")
        if has_not:
            if check_token_type(arg1) != "symbol" or arg1 not in kwargs:
                raise ValueError("Invalid comparison")
            return kwargs[arg1] != kwargs[arg2] if compare_col else kwargs[arg1] != arg2
        else:
            if check_token_type(arg1) != "symbol" or arg1 not in kwargs:
                raise ValueError("Invalid comparison")
            return kwargs[arg1] == kwargs[arg2] if compare_col else kwargs[arg1] == arg2

    return simple_predicate


def check_token_type(token: str) -> str:
    if token[0] == token[-1] == "'" or token[0] == token[-1] == '"':
        return "string"
    if is_int(token):
        return "int"
    if is_float(token):
        return "float"
    return "symbol"


def is_int(token: str) -> bool:
    try:
        int(token)
        return True
    except:
        return False


def is_float(token: str) -> bool:
    try:
        float(token)
        return True
    except:
        return False


#####################################
# Implementation of the predicate parser 2:
# First rewrite the grammar as follows:
# Predicate :== AndExpression SubOrExpression
# SubOrExpression :== "or" AndExpression SubOrExpression | eps
# AndExpression: NegatablePredicate SubAndExpression
# SubAndExpression: "and" NegatablePredicate SubAndExpression |eps
# NegatablePredicate: SimplePredicate | "not" NegatablePredicate
# SimplePredicate: a = v | a = a
# Then use recursive descent parsing to get a parse tree. Evaluate predicates by traversing the parse tree.
#####################################
class SimplePredicate:
    def __init__(self, a1: str, v1: str | float | int | None, a2: str | None):
        assert v1 is not None or a2 is not None, "Cannot have 'None' as a comparison target."
        assert v1 is None or a2 is None, "Can only have comparison target!"
        self.a1 = a1
        self.v1 = v1
        self.a2 = a2

    @staticmethod
    def parse(tokens: list[str]) -> SimplePredicate:
        assert len(tokens) >= 3, "A simple predicate must be made of 3 tokens or more."
        col_name = tokens[0]
        assert check_token_type(col_name) == "symbol", "Invalid simple predicate given."
        del tokens[0]

        assert tokens[0] == '=', "The second character of a simple predicate must be '='!"
        del tokens[0]

        target = tokens[0]
        del tokens[0]

        if check_token_type(target) == "symbol":
            return SimplePredicate(col_name, None, target)
        elif check_token_type(target) == "int":
            return SimplePredicate(col_name, int(target), None)
        elif check_token_type(target) == 'float':
            return SimplePredicate(col_name, float(target), None)
        else:
            return SimplePredicate(col_name, target[1:-1], None)

    def evaluate(self, **kargs) -> bool:
        if self.a2 is not None:
            return kargs[self.a1] == kargs[self.a2]
        else:
            return kargs[self.a1] == self.v1


class NegatablePredicate:
    def __init__(self, num_not: int, simple_predicate: SimplePredicate):
        self.num_not = num_not
        self.simple_predicate = simple_predicate

    @staticmethod
    def parse(tokens: list[str]) -> NegatablePredicate:
        assert len(tokens) >= 3, "A simple predicate must be made of 3 tokens or more."
        not_count = 0
        while tokens[0] == "not":
            not_count += 1
            del tokens[0]
        return NegatablePredicate(not_count, SimplePredicate.parse(tokens))

    def evaluate(self, **kargs) -> bool:
        result = self.simple_predicate.evaluate(**kargs)
        if self.num_not % 2:
            return not result
        else:
            return result


class SubAndExpression:
    def __init__(self, predicate: NegatablePredicate | None, sub_and_expr: SubAndExpression | None):
        self.predicate = predicate
        self.sub_and_expr = sub_and_expr

    def is_empty(self):
        return self.predicate is None

    @staticmethod
    def parse(tokens: list[str]) -> SubAndExpression:
        if len(tokens) > 1 and tokens[0] == 'and':
            del tokens[0]
            negatable_pred = NegatablePredicate.parse(tokens)
            sub_and_expr = SubAndExpression.parse(tokens)
            return SubAndExpression(negatable_pred, sub_and_expr)
        else:
            return SubAndExpression(None, None)

    def evaluate(self, **kargs) -> bool:
        if self.is_empty():
            return True
        else:
            return self.predicate.evaluate(**kargs) and self.sub_and_expr.evaluate(**kargs)


class AndExpression:
    def __init__(self, predicate: NegatablePredicate, sub_and_expr: SubAndExpression):
        self.predicate = predicate
        self.sub_and_expr = sub_and_expr

    @staticmethod
    def parse(tokens: list[str]) -> AndExpression:
        negatable_pred = NegatablePredicate.parse(tokens)
        sub_and_expr = SubAndExpression.parse(tokens)
        return AndExpression(negatable_pred, sub_and_expr)

    def evaluate(self, **kargs) -> bool:
        return self.predicate.evaluate(**kargs) and self.sub_and_expr.evaluate(**kargs)


class SubOrExpression:
    def __init__(self, and_expr: AndExpression | None, sub_or_expr: SubOrExpression | None):
        self.and_expr = and_expr
        self.sub_or_expr = sub_or_expr

    def is_empty(self):
        return self.and_expr is None

    @staticmethod
    def parse(tokens: list[str]) -> SubOrExpression:
        if len(tokens) > 1 and tokens[0] == 'or':
            del tokens[0]
            and_expr = AndExpression.parse(tokens)
            sub_or_expr = SubOrExpression.parse(tokens)
            return SubOrExpression(and_expr, sub_or_expr)
        else:
            return SubOrExpression(None, None)

    def evaluate(self, **kargs) -> bool:
        if self.is_empty():
            return False
        else:
            return self.and_expr.evaluate(**kargs) or self.sub_or_expr.evaluate(**kargs)


class Predicate:
    def __init__(self, and_expr: AndExpression, sub_or_expr: SubOrExpression):
        self.and_expr = and_expr
        self.sub_or_expr = sub_or_expr

    @staticmethod
    def parse(tokens: list[str]) -> Predicate:
        and_expr = AndExpression.parse(tokens)
        sub_or_expr = SubOrExpression.parse(tokens)
        return Predicate(and_expr, sub_or_expr)

    def evaluate(self, **kargs) -> bool:
        return self.and_expr.evaluate(**kargs) or self.sub_or_expr.evaluate(**kargs)


def get_tree_predicate_instantiater(tokens: list[str]) -> Callable:
    return Predicate.parse(tokens).evaluate
