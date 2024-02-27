import math

# 统计Halstead 操作数和操作符数量
def halstead_cal(codes):
    Ioc_blank = 0
    op, op_key = all_operators()
    operators = op_key
    operands = {}
    isAllowed = True
    for text in codes:
        # 统计空白行
        if text == '':
            Ioc_blank += 1
        else:
            # 统计操作符和操作数的数量
            if text.startswith("/*"):
                isAllowed = False
            if (not text.startswith("//")) and isAllowed == True:
                text_tmp = ' ' + text.split('//')[0]
                for key in operators.keys():
                    if key not in op:
                        count = text_tmp.count(' ' + key + ' ')
                        operators[key] = operators[key] + count
                        if count > 0:
                            text_tmp = text_tmp.replace(' ' + key + ' ', ' ')
                    else:
                        operators[key] = operators[key] + text_tmp.count(key)
                        text_tmp = text_tmp.replace(key, ' ')
                for key in text_tmp.split():
                    if key in operands:
                        operands[key] = operands[key] + 1
                    else:
                        if key != '':
                            operands[key] = 1

            if text.endswith("*/"):
                isAllowed = True
        # 计算操作符数量和操作符种类数量
        operators.pop(')')
        operators.pop(']')
        operators.pop('}')
        num_operators = 0
        num_unique_operators = 0
        for k, v in operators.items():
            num_operators += v
            if v != 0:
                num_unique_operators += 1
        # 计算操作数数量和操作数种类数量
        num_operands = 0
        num_unique_operands = 0
        for m, n in operands.items():
            num_operands += n
            if n != 0:
                num_unique_operands += 1
        h = halstead_fun(num_operators, num_operands, num_unique_operators, num_unique_operands)
        return h, Ioc_blank


# java 操作数&操作符
def all_operators():
    op = {'(': 0, ')': 0, '{': 0, '}': 0, '[': 0, ']': 0, ',': 0, '.': 0, ':': 0, '>': 0, '<': 0, '!': 0,
          '~': 0, '?': 0, '::': 0, '<:': 0, '>:': 0, '!:': 0, '&&': 0, '||': 0, '++': 0, '--': 0, '+': 0,
          '-': 0, '*': 0, '/': 0, '&': 0, '|': 0, '^': 0, '%': 0, '->': 0, '::': 0, '+:': 0, '-:': 0, '*:': 0, '/:': 0,
          '&:': 0, '|:': 0, '^:': 0, '%:': 0, '<<:': 0, '>>:': 0, '>>>:': 0, '@': 0, '...': 0, '==': 0, '=': 0}

    op_key = {'(': 0, ')': 0, '{': 0, '}': 0, '[': 0, ']': 0, ';': 0, ',': 0, '.': 0, ':': 0, '>': 0, '<': 0, '!': 0,
              '~': 0, '?': 0, '::': 0, '<:': 0, '>:': 0, '!:': 0, '&&': 0, '||': 0, '++': 0, '--': 0, '+': 0,
              '-': 0, '*': 0, '/': 0, '&': 0, '|': 0, '^': 0, '%': 0, '->': 0, '::': 0, '+:': 0, '-:': 0, '*:': 0,
              '/:': 0, '&:': 0, '|:': 0, '^:': 0, '%:': 0, '<<:': 0, '>>:': 0, '>>>:': 0, '@': 0, '...': 0, '==': 0,
              '=': 0, 'abstract': 0, 'assert': 0, 'boolean': 0, 'break': 0, 'byte': 0, 'case': 0, 'catch': 0, 'char': 0,
              'class': 0, 'const': 0, 'continue': 0, 'default': 0, 'do': 0, 'double': 0, 'else': 0, 'enum': 0,
              'extends': 0, 'final': 0, 'finally': 0, 'float': 0, 'for': 0, 'if': 0, 'goto': 0, 'implements': 0,
              'import': 0, 'instanceof': 0, 'int': 0, 'interface': 0, 'long': 0, 'native': 0, 'new': 0, 'package': 0,
              'private': 0, 'protected': 0, 'public': 0, 'return': 0, 'short': 0, 'static': 0, 'strictfp': 0,
              'super': 0, 'switch': 0, 'synchronized': 0, 'this': 0, 'throw': 0, 'throws': 0, 'transient': 0,
              'try': 0, 'void': 0, 'volatile': 0, 'while': 0, 'null': 0, 'Integer': 0, 'Long': 0,
              'String': 0, 'Double': 0, 'Float': 0}

    return op, op_key


# 计算Halstead复杂度
def halstead_fun(n1, n2, u1, u2):
    N = n1 + n2
    U = u1 + u2
    V = N * math.log(U, 2)
    D = (u1 * n2) / (2 * u2)
    E = D * V
    T = E / 18
    B = (E ** (2 / 3)) / 3000
    L = 1 / D
    h = {'h_N': N, 'h_U': U, 'h_V': V, 'h_D': D, 'h_E': E, 'h_B': B, 'h_T': T, 'h_L': L, 'h_n1': n1, 'h_n2': n2, 'h_u1': u1, 'h_u2': u2}
    return h