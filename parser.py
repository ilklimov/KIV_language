import errors as e
import tokens as t
import nodes as n
import stack as stack


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.tok_idx = -1
        self.advance()

    def advance(self, ):
        self.tok_idx += 1
        if self.tok_idx < len(self.tokens):
            self.current_tok = self.tokens[self.tok_idx]
        return self.current_tok

    def parse(self):
        res = self.expr()
        if not res.error and self.current_tok.type != t.TT_EOF:
            return res.failure(e.InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '+', '-', '*', '/', '^', '==', '!=', '<', '>', <=', '>=', 'AND' or 'OR'"
            ))
        return res

    ###################################

    def expr(self):
        res = stack.Stack()

        if self.current_tok.matches(t.TT_KEYWORD, 'VAR'):
            res.register_advancement()
            self.advance()

            if self.current_tok.type != t.TT_IDENTIFIER:
                return res.failure(e.InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected identifier"
                ))

            var_name = self.current_tok
            res.register_advancement()
            self.advance()

            if self.current_tok.type != t.TT_EQ:
                return res.failure(e.InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected '='"
                ))

            res.register_advancement()
            self.advance()
            expr = res.register(self.expr())
            if res.error: return res
            return res.success(n.VarAssignNode(var_name, expr))

        node = res.register(self.bin_op(self.comp_expr, ((t.TT_KEYWORD, 'AND'), (t.TT_KEYWORD, 'OR'))))

        if res.error:
            return res.failure(e.InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'VAR', 'IF', 'FOR', 'WHILE', 'FUN', int, float, identifier, '+', '-', '(', '[' or 'NOT'"
            ))

        return res.success(node)

    def comp_expr(self):
        res = stack.Stack()

        if self.current_tok.matches(t.TT_KEYWORD, 'NOT'):
            op_tok = self.current_tok
            res.register_advancement()
            self.advance()

            node = res.register(self.comp_expr())
            if res.error: return res
            return res.success(n.UnaryOpNode(op_tok, node))

        node = res.register(self.bin_op(self.arith_expr, (t.TT_EE, t.TT_NE, t.TT_LT, t.TT_GT, t.TT_LTE, t.TT_GTE)))

        if res.error:
            return res.failure(e.InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected int, float, identifier, '+', '-', '(', '[', 'IF', 'FOR', 'WHILE', 'FUN' or 'NOT'"
            ))

        return res.success(node)

    def arith_expr(self):
        return self.bin_op(self.term, (t.TT_PLUS, t.TT_MINUS))

    def term(self):
        return self.bin_op(self.factor, (t.TT_MUL, t.TT_DIV))

    def factor(self):
        res = stack.Stack()
        tok = self.current_tok

        if tok.type in (t.TT_PLUS, t.TT_MINUS):
            res.register_advancement()
            self.advance()
            factor = res.register(self.factor())
            if res.error: return res
            return res.success(n.UnaryOpNode(tok, factor))

        return self.power()

    def power(self):
        return self.bin_op(self.call, (t.TT_POW,), self.factor)

    def call(self):
        res = stack.Stack()
        atom = res.register(self.atom())
        if res.error: return res

        if self.current_tok.type == t.TT_LPAREN:
            res.register_advancement()
            self.advance()
            arg_nodes = []

            if self.current_tok.type == t.TT_RPAREN:
                res.register_advancement()
                self.advance()
            else:
                arg_nodes.append(res.register(self.expr()))
                if res.error:
                    return res.failure(e.InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        "Expected ')', 'VAR', 'IF', 'FOR', 'WHILE', 'FUN', int, float, identifier, '+', '-', '(', '[' or 'NOT'"
                    ))

                while self.current_tok.type == t.TT_COMMA:
                    res.register_advancement()
                    self.advance()

                    arg_nodes.append(res.register(self.expr()))
                    if res.error: return res

                if self.current_tok.type != t.TT_RPAREN:
                    return res.failure(e.InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        f"Expected ',' or ')'"
                    ))

                res.register_advancement()
                self.advance()
            return res.success(n.CallNode(atom, arg_nodes))
        return res.success(atom)

    def atom(self):
        res = stack.Stack()
        tok = self.current_tok

        if tok.type in (t.TT_INT, t.TT_FLOAT):
            res.register_advancement()
            self.advance()
            return res.success(n.NumberNode(tok))

        elif tok.type == t.TT_STRING:
            res.register_advancement()
            self.advance()
            return res.success(n.StringNode(tok))

        elif tok.type == t.TT_IDENTIFIER:
            res.register_advancement()
            self.advance()
            return res.success(n.VarAccessNode(tok))

        elif tok.type == t.TT_LPAREN:
            res.register_advancement()
            self.advance()
            expr = res.register(self.expr())
            if res.error: return res
            if self.current_tok.type == t.TT_RPAREN:
                res.register_advancement()
                self.advance()
                return res.success(expr)
            else:
                return res.failure(e.InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected ')'"
                ))

        elif tok.type == t.TT_LSQUARE:
            list_expr = res.register(self.list_expr())
            if res.error: return res
            return res.success(list_expr)

        elif tok.matches(t.TT_KEYWORD, 'IF'):
            if_expr = res.register(self.if_expr())
            if res.error: return res
            return res.success(if_expr)

        elif tok.matches(t.TT_KEYWORD, 'FOR'):
            for_expr = res.register(self.for_expr())
            if res.error: return res
            return res.success(for_expr)

        elif tok.matches(t.TT_KEYWORD, 'WHILE'):
            while_expr = res.register(self.while_expr())
            if res.error: return res
            return res.success(while_expr)

        elif tok.matches(t.TT_KEYWORD, 'FUN'):
            func_def = res.register(self.func_def())
            if res.error: return res
            return res.success(func_def)

        return res.failure(e.InvalidSyntaxError(
            tok.pos_start, tok.pos_end,
            "Expected int, float, identifier, '+', '-', '(', '[', IF', 'FOR', 'WHILE', 'FUN'"
        ))

    def list_expr(self):
        res = stack.Stack()
        element_nodes = []
        pos_start = self.current_tok.pos_start.copy()

        if self.current_tok.type != t.TT_LSQUARE:
            return res.failure(e.InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected '['"
            ))

        res.register_advancement()
        self.advance()

        if self.current_tok.type == t.TT_RSQUARE:
            res.register_advancement()
            self.advance()
        else:
            element_nodes.append(res.register(self.expr()))
            if res.error:
                return res.failure(e.InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected ']', 'VAR', 'IF', 'FOR', 'WHILE', 'FUN', int, float, identifier, '+', '-', '(', '[' or 'NOT'"
                ))

            while self.current_tok.type == t.TT_COMMA:
                res.register_advancement()
                self.advance()

                element_nodes.append(res.register(self.expr()))
                if res.error: return res

            if self.current_tok.type != t.TT_RSQUARE:
                return res.failure(e.InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected ',' or ']'"
                ))

            res.register_advancement()
            self.advance()

        return res.success(n.ListNode(
            element_nodes,
            pos_start,
            self.current_tok.pos_end.copy()
        ))

    def print_expr(self):
        res = stack.Stack()

        if not self.current_tok.matches(t.TT_KEYWORD, 'PRINT'):
            return res.failure(e.InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'PRINT'"
            ))

        res.register_advancement()
        self.advance()

        var_name = res.register(self.expr())
        if res.error: return res

        return res.success(n.PrintNode(var_name))

    def if_expr(self):
        res = stack.Stack()
        cases = []
        else_case = None

        if not self.current_tok.matches(t.TT_KEYWORD, 'IF'):
            return res.failure(e.InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'IF'"
            ))

        res.register_advancement()
        self.advance()

        condition = res.register(self.expr())
        if res.error: return res

        if not self.current_tok.matches(t.TT_KEYWORD, 'THEN'):
            return res.failure(e.InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'THEN'"
            ))

        res.register_advancement()
        self.advance()

        expr = res.register(self.expr())
        if res.error: return res
        cases.append((condition, expr))

        while self.current_tok.matches(t.TT_KEYWORD, 'ELIF'):
            res.register_advancement()
            self.advance()

            condition = res.register(self.expr())
            if res.error: return res

            if not self.current_tok.matches(t.TT_KEYWORD, 'THEN'):
                return res.failure(e.InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected 'THEN'"
                ))

            res.register_advancement()
            self.advance()

            expr = res.register(self.expr())
            if res.error: return res
            cases.append((condition, expr))

        if self.current_tok.matches(t.TT_KEYWORD, 'ELSE'):
            res.register_advancement()
            self.advance()

            else_case = res.register(self.expr())
            if res.error: return res

        return res.success(n.IfNode(cases, else_case))

    def for_expr(self):
        res = stack.Stack()

        if not self.current_tok.matches(t.TT_KEYWORD, 'FOR'):
            return res.failure(e.InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'FOR'"
            ))

        res.register_advancement()
        self.advance()

        if self.current_tok.type != t.TT_IDENTIFIER:
            return res.failure(e.InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected identifier"
            ))

        var_name = self.current_tok
        res.register_advancement()
        self.advance()

        if self.current_tok.type != t.TT_EQ:
            return res.failure(e.InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected '='"
            ))

        res.register_advancement()
        self.advance()

        start_value = res.register(self.expr())
        if res.error: return res

        if not self.current_tok.matches(t.TT_KEYWORD, 'TO'):
            return res.failure(e.InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'TO'"
            ))

        res.register_advancement()
        self.advance()

        end_value = res.register(self.expr())
        if res.error: return res

        if self.current_tok.matches(t.TT_KEYWORD, 'STEP'):
            res.register_advancement()
            self.advance()

            step_value = res.register(self.expr())
            if res.error: return res
        else:
            step_value = None

        if not self.current_tok.matches(t.TT_KEYWORD, 'THEN'):
            return res.failure(e.InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'THEN'"
            ))

        res.register_advancement()
        self.advance()

        body = res.register(self.expr())
        if res.error: return res

        return res.success(n.ForNode(var_name, start_value, end_value, step_value, body))

    def while_expr(self):
        res = stack.Stack()

        if not self.current_tok.matches(t.TT_KEYWORD, 'WHILE'):
            return res.failure(e.InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'WHILE'"
            ))

        res.register_advancement()
        self.advance()

        condition = res.register(self.expr())
        if res.error: return res

        if not self.current_tok.matches(t.TT_KEYWORD, 'THEN'):
            return res.failure(e.InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'THEN'"
            ))

        res.register_advancement()
        self.advance()

        body = res.register(self.expr())
        if res.error: return res

        return res.success(n.WhileNode(condition, body))

    def func_def(self):
        res = stack.Stack()

        if not self.current_tok.matches(t.TT_KEYWORD, 'FUN'):
            return res.failure(e.InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'FUN'"
            ))

        res.register_advancement()
        self.advance()

        if self.current_tok.type == t.TT_IDENTIFIER:
            var_name_tok = self.current_tok
            res.register_advancement()
            self.advance()
            if self.current_tok.type != t.TT_LPAREN:
                return res.failure(e.InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected '('"
                ))
        else:
            var_name_tok = None
            if self.current_tok.type != t.TT_LPAREN:
                return res.failure(e.InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected identifier or '('"
                ))

        res.register_advancement()
        self.advance()
        arg_name_toks = []

        if self.current_tok.type == t.TT_IDENTIFIER:
            arg_name_toks.append(self.current_tok)
            res.register_advancement()
            self.advance()

            while self.current_tok.type == t.TT_COMMA:
                res.register_advancement()
                self.advance()

                if self.current_tok.type != t.TT_IDENTIFIER:
                    return res.failure(e.InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        f"Expected identifier"
                    ))

                arg_name_toks.append(self.current_tok)
                res.register_advancement()
                self.advance()

            if self.current_tok.type != t.TT_RPAREN:
                return res.failure(e.InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected ',' or ')'"
                ))
        else:
            if self.current_tok.type != t.TT_RPAREN:
                return res.failure(e.InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected identifier or ')'"
                ))

        res.register_advancement()
        self.advance()

        if self.current_tok.type != t.TT_ARROW:
            return res.failure(e.InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected '->'"
            ))

        res.register_advancement()
        self.advance()
        node_to_return = res.register(self.expr())
        if res.error: return res

        return res.success(n.FuncDefNode(
            var_name_tok,
            arg_name_toks,
            node_to_return
        ))

    ###################################

    def bin_op(self, func_a, ops, func_b=None):
        if func_b == None:
            func_b = func_a

        res = stack.Stack()
        left = res.register(func_a())
        if res.error: return res

        while self.current_tok.type in ops or (self.current_tok.type, self.current_tok.value) in ops:
            op_tok = self.current_tok
            res.register_advancement()
            self.advance()
            right = res.register(func_b())
            if res.error: return res
            left = n.BinOpNode(left, op_tok, right)

        return res.success(left)


class RTResult:
    def __init__(self):
        self.value = None
        self.error = None

    def register(self, res):
        self.error = res.error
        return res.value

    def success(self, value):
        self.value = value
        return self

    def failure(self, error):
        self.error = error
        return self
