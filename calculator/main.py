import sys
import customtkinter as ctk
from evaluator import evaluate

BG_COLOR = "#30252D" # фон окна
DIGIT_COLOR = "#66535F" # цифровые кнопки
UTILITY_COLOR = "#A88498" # служебные кнопки
OPERATION_COLOR = "#E8A3BD" # арифметические операции
TEXT_COLOR = "#FFFFFF" # текст

class Calculator:
    """
    Графический калькулятор на основе CustomTkinter.

    Обеспечивает ввод арифметических выражений с клавиатуры
    и кнопочной панели, вычисление результатов и обработку
    некорректных выражений.

    Attributes
    ----------
    root: ctk.CTk
        Главное окно приложения.
    entry: ctk.CTkEntry
        Поле ввода выражений и отображения результатов.
    buttons_frame: ctk.CTkFrame
        Контейнер кнопочной панели.
    """

    def __init__(self, root: ctk.CTk) -> None:
        """
        Инициализирует калькулятор и его графический интерфейс.

        Parameters
        ----------
        root: ctk.CTk
            Главное окно приложения.
        """
        self.root = root
        self.root.title("Калькулятор")
        self.root.geometry("480x620")
        self.root.resizable(False, False)
        self.root.configure(fg_color=BG_COLOR)

        self.create_widgets()

        self.root.bind("<Return>", lambda event: self.calculate())
        self.root.bind("<Escape>", lambda event: self.clear())


    def create_widgets(self) -> None:
        """
        Создаёт поле ввода и кнопочную панель калькулятора.

        Настраивает расположение, внешний вид кнопок
        и обработчики нажатий.
        """
        # создание однострочного поля ввода
        self.entry = ctk.CTkEntry(
            self.root,
            font=("Arial", 40),
            justify="right",
            fg_color = BG_COLOR,
            border_width=0,
        )
        self.entry.pack(padx=15, pady=(25, 20), fill="x")

        # создание сетки из 4 столбцов и 5 строк
        self.buttons_frame = ctk.CTkFrame(
            self.root,
            width=440,
            height=460,
            fg_color="transparent"
        )

        self.buttons_frame.pack(pady=(0, 15))
        self.buttons_frame.grid_propagate(False)

        for column in range(4):
            self.buttons_frame.grid_columnconfigure(
                column,
                weight=1,
                uniform="buttons"
            )

        for row in range(5):
            self.buttons_frame.grid_rowconfigure(
                row,
                weight=1,
                uniform="buttons"
            )

        buttons = [
            ["⌫", "AC", "²√x", "÷"],
            ["7", "8", "9", "×"],
            ["4", "5", "6", "−"],
            ["1", "2", "3", "+"],
            ["()", "0", ",", "="]
        ]
        for row, button_row in enumerate(buttons):
            for column, button in enumerate(button_row):
                if button in ["÷", "×", "−", "+", "="]:
                    button_font = ("Arial", 20)
                    color = OPERATION_COLOR

                elif button in ["⌫", "AC", "²√x"]:
                    button_font = ("Arial", 16)
                    color = UTILITY_COLOR

                else:
                    button_font = ("Arial", 20)
                    color = DIGIT_COLOR


                widget = ctk.CTkButton(
                    self.buttons_frame,
                    text=button,
                    width=65,
                    height=65,
                    corner_radius=24 if button in ["⌫", "AC", "²√x"] else 28,
                    fg_color=color,
                    hover=False,
                    text_color=TEXT_COLOR,
                    font=button_font,
                    command=lambda b=button: self.on_button_click(b)
                )

                widget.bind(
                    "<Button-1>",
                    lambda event, w=widget, c=color: self.button_feedback(w, c)
                )

                widget.grid(
                    row=row,
                    column=column,
                    padx=5,
                    pady=5,
                    sticky="nsew"
                )


    def insert_symbol(self, symbol: str) -> None:
        """
        Добавляет символ в конец поля ввода.

        Parameters
        ----------
        symbol: str
            Вставляемая цифра или математический символ.
        """
        self.entry.insert(ctk.END, symbol)


    def on_button_click(self, symbol: str) -> None:
        """
        Обрабатывает нажатие кнопки калькулятора.

        В зависимости от выбранной кнопки выполняет ввод
        символа, вычисление выражения, очистку поля
        или удаление последнего символа.

        Parameters
        ----------
        symbol : str
            Обозначение нажатой кнопки.
        """
        if symbol == "⌫":
            if self.entry.get():
                self.entry.delete(len(self.entry.get()) - 1, ctk.END)
        elif symbol == "AC":
            self.clear()
        elif symbol == "²√x":
            self.entry.insert(ctk.END, "√(")
        elif symbol.isdigit() or symbol in ["+", "−", "×", "÷", ","]:
            self.insert_symbol(symbol)
        elif symbol == "=":
            self.calculate()
        elif symbol == "()":
            self.insert_bracket()


    def insert_bracket(self) -> None:
        """
        Вставляет открывающую или закрывающую скобку.

        Выбирает тип скобки с учётом текущего выражения
        и количества уже введённых скобок.
        """
        expression = self.entry.get()

        open_count = expression.count("(")
        close_count = expression.count(")")

        if not expression or expression[-1] in "+−×÷(":
            bracket = "("
        elif open_count > close_count:
            bracket = ")"
        else:
            bracket = "("

        self.entry.insert(ctk.END, bracket)


    def calculate(self) -> None:
        """
        Вычисляет выражение из поля ввода.

        Преобразует математические символы в синтаксис Python,
        дополняет недостающие закрывающие скобки и передаёт
        выражение функции evaluate().

        Отображает результат вычисления или сообщение
        об ошибке при некорректном выражении.
        """
        expression = self.entry.get()

        expression = (
            expression.replace("×", "*")
            .replace("÷", "/")
            .replace("−", "-")
            .replace(",", ".")
            .replace("√(", "sqrt(")
        )

        open_count = expression.count("(")
        close_count = expression.count(")")

        if open_count > close_count:
            expression += ")" * (open_count - close_count)

        try:
            result = evaluate(expression)
            result_text = f"{result:g}".replace(".", ",")

        except (ValueError, SyntaxError, ZeroDivisionError,
                OverflowError, RecursionError):
            result_text = "ошибка"

        self.entry.delete(0, ctk.END)
        self.entry.insert(0, result_text)


    def clear(self) -> None:
        """Очищает поле ввода калькулятора."""
        self.entry.delete(0, ctk.END)


    def button_feedback(self, widget: ctk.CTkButton, original_color: str) -> None:
        """
        Создаёт визуальный эффект нажатия кнопки.

        Временно изменяет цвет кнопки и восстанавливает
        исходный цвет через 120 миллисекунд.

        Parameters
        ----------
        widget : ctk.CTkButton
            Кнопка, для которой создаётся эффект нажатия.
        original_color : str
            Исходный цвет кнопки в формате HEX.
        """
        pressed_colors = {
            DIGIT_COLOR: "#806A79",
            UTILITY_COLOR: "#BB9AAC",
            OPERATION_COLOR: "#F0B8CE"
        }

        widget.configure(fg_color=pressed_colors[original_color])

        widget.after(
            120,
            lambda: widget.configure(fg_color=original_color)
        )


def main() -> None:
    """Создаёт главное окно и запускает калькулятор."""
    ctk.set_appearance_mode("dark")

    if sys.platform.startswith("linux"):
        ctk.DrawEngine.preferred_drawing_method = "circle_shapes"

    ctk.set_widget_scaling(1.0)
    ctk.set_window_scaling(1.0)

    root = ctk.CTk() # создание главного окна
    Calculator(root)
    root.mainloop()

if __name__ == "__main__":
    main()