import ast
import operator
import math

def evaluate(expression: str) -> float:
    """
    Вычисляет арифметическое выражение с помощью AST.

    Поддерживает основные арифметические операции,
    унарные знаки и квадратный корень.

    Parameters
    ----------
    expression: str
        Математическое выражение в синтаксисе Python.

    Returns
    -------
    float
        Результат вычисления выражения.

    Raises
    ------
    SyntaxError
        Если выражение содержит синтаксическую ошибку.
    ValueError
        Если выражение содержит недопустимые конструкции.
    ZeroDivisionError
        Если происходит деление на ноль.
    OverflowError
        Если результат вычисления слишком велик.
    """
    operations = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv
    }

    unary_operations = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg
    }

    def calculate_node(node: ast.expr) -> float:
        """
        Рекурсивно вычисляет значение узла AST.

        Обрабатывает числовые константы, бинарные и унарные
        арифметические операции, а также квадратный корень.

        Parameters
        ----------
        node : ast.expr
            Узел абстрактного синтаксического дерева.

        Returns
        -------
        float
            Результат вычисления узла.

        Raises
        ------
        ValueError
            Если узел содержит недопустимое значение,
            операцию или вызов функции.
        ZeroDivisionError
            Если происходит деление на ноль.
        """
        if isinstance(node, ast.Constant):
            if type(node.value) in (int, float):
                return float(node.value)
            raise ValueError("недопустимое значение")

        if isinstance(node, ast.BinOp):
            operation = operations.get(type(node.op))

            if operation is None:
                raise ValueError("недопустимая операция")

            left = calculate_node(node.left)
            right = calculate_node(node.right)

            return operation(left, right)

        if isinstance(node, ast.Call):
            if (
                    isinstance(node.func, ast.Name)
                    and node.func.id == "sqrt"
                    and len(node.args) == 1
                    and not node.keywords
            ):
                argument = calculate_node(node.args[0])
                return math.sqrt(argument)

            raise ValueError("недопустимая функция")

        if isinstance(node, ast.UnaryOp):
            operation = unary_operations.get(type(node.op))

            if operation is None:
                raise ValueError("недопустимая операция")

            return operation(calculate_node(node.operand))

        raise ValueError("Некорректное выражение")

    tree = ast.parse(expression, mode="eval")
    return calculate_node(tree.body)