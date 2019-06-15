# python3 main.py test.kiv
import interpreter as inter
import lexer as lex
import parser as pars
import sys
import re

#######################################
# RUN
#######################################

global_symbol_table = inter.SymbolTable()
global_symbol_table.set("NULL", inter.Number(0))
global_symbol_table.set("FALSE", inter.Number(0))
global_symbol_table.set("TRUE", inter.Number(1))


def run(text):
    # Generate tokens
    # print("RUN1")
    lexer = lex.Lexer(text)
    tokens, error = lexer.make_tokens()
    if error:
        print()
        # return None, error

    # Generate AST
    print("RUN2 | Токены: ", tokens)
    parser = pars.Parser(tokens)
    ast = parser.parse()
    # print(ast.node)
    # if ast.error:
        # print()
        # return (ast.error)

    # Run program
    print("RUN3 | АСТ:", ast.node)
    interpreter = inter.Interpreter()
    context = inter.Context('<program>')
    context.symbol_table = global_symbol_table
    result = interpreter.visit(ast.node, context)
    print(result.value)
    return result.error


def usage():
    sys.stdout.write('\nНе верное расширение файла!!!\nЯ читаю только файлы .kiv расширения\n\n')
    sys.exit(1)


if __name__ == '__main__':
    match = re.search(r'\.\D*', sys.argv[1])  # поиск расширения файла (после точки три НЕ цифры)
    if match[0] != '.kiv':
        usage()
    filename = sys.argv[1]
    text = open(filename).read()  # считали содержимое файла

    run(text)
