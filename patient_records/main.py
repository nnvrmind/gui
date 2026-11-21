import customtkinter as ctk
from tkinter import ttk
import math
from tkinter import messagebox

from patient import Patient


BG_COLOR = "#F5F8FC"
TEXT_COLOR = "#253746"
ACCENT_COLOR = "#4F9BB8"
HOVER_COLOR = "#3D829D"
CARD_COLOR = "#FFFFFF"
SECONDARY_TEXT_COLOR = "#748694"


class PatientApp:
    """Графическое приложение для учёта пациентов."""

    def __init__(self, root: ctk.CTk) -> None:
        """
        Инициализирует главное окно приложения.

        Parameters
        ----------
        root: ctk.CTk
            Главное окно приложения.
        """
        self.root = root
        self.root.tk.call("::msgcat::mclocale", "ru")
        self.root.title("Учёт пациентов")
        self.root.geometry("1100x700")
        self.root.minsize(850, 550)
        self.root.configure(fg_color=BG_COLOR)

        # первый столбец и третья строка должны расширяться вместе с окном
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(2, weight=1)

        self.configure_table_style()
        self.create_widgets()

    def create_widgets(self) -> None:
        """Создаёт основные элементы интерфейса приложения."""

        # заголовок приложения
        title = ctk.CTkLabel(
            self.root,
            text="Учёт пациентов",
            font=("Arial", 30, "bold"),
            text_color=TEXT_COLOR
        )
        title.grid(
            row=0,
            column=0,
            padx=30,
            pady=(25, 5),
            sticky="w"
        )

        # Панель управления
        toolbar = ctk.CTkFrame(
            self.root,
            fg_color="transparent"
        )
        toolbar.grid(
            row=1,
            column=0,
            padx=30,
            pady=(15, 20),
            sticky="ew"
        )

        buttons = [
            ("+ Добавить пациента", ACCENT_COLOR, HOVER_COLOR),
            ("Редактировать", "#E5F3F8", "#D4EAF2"),
            ("Статистика", "#E5F3F8", "#D4EAF2"),
            ("Удалить", "#FCECED", "#F5D5D8")
        ]

        for column, (text, color, hover_color) in enumerate(buttons):
            button = ctk.CTkButton(
                toolbar,
                text=text,
                width=190,
                height=42,
                corner_radius=10,
                fg_color=color,
                hover_color=hover_color,
                text_color="#FFFFFF" if column == 0 else TEXT_COLOR,
                font=("Arial", 14)
            )
            button.grid(
                row=0,
                column=column,
                padx=(0, 10)
            )

            if text == "+ Добавить пациента":
                button.configure(command=self.open_patient_form)

            elif text == "Редактировать":
                button.configure(command=self.edit_selected_patient)

            elif text == "Удалить":
                button.configure(command=self.delete_selected_patient)

        # область для таблицы пациентов
        table_frame = ctk.CTkFrame(
            self.root,
            fg_color=CARD_COLOR,
            corner_radius=15
        )
        table_frame.grid(
            row=2,
            column=0,
            padx=30,
            pady=(0, 30),
            sticky="nsew"
        )

        table_title = ctk.CTkLabel(
            table_frame,
            text="Список пациентов",
            font=("Arial", 20, "bold"),
            text_color=TEXT_COLOR
        )
        table_title.pack(
            anchor="w",
            padx=20,
            pady=(20, 15)
        )

        self.create_table(table_frame)

    def create_table(self, parent: ctk.CTkFrame) -> None:
        """
        Создаёт таблицу для отображения информации о пациентах.

        Parameters
        ----------
        parent: ctk.CTkFrame
            Контейнер, в котором размещается таблица.
        """
        columns = ("name", "age", "sex", "height", "weight", "bmi")

        self.table = ttk.Treeview(
            parent,
            columns=columns,
            show="headings",
            selectmode="browse",
            style="Patients.Treeview"
        )

        headings = {
            "name": "ФИО",
            "age": "Возраст",
            "sex": "Пол",
            "height": "Рост (см)",
            "weight": "Вес (кг)",
            "bmi": "ИМТ"
        }

        for column, heading in headings.items():
            self.table.heading(column, text=heading)

            self.table.column(
                column,
                width=200 if column == "name" else 100,
                minwidth=70,
                anchor="center",
                stretch=True
            )

        self.table.column("name", anchor="w")

        self.table.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 20)
        )

        patients = [
            ("Иванова Анна", 24, "Ж", 165, 58, 21.3),
            ("Петров Иван", 36, "М", 180, 82, 25.3),
            ("Сидорова Елена", 51, "Ж", 170, 69, 23.9)
        ]

        for patient in patients:
            self.table.insert("", "end", values=patient)

    def configure_table_style(self) -> None:
        """Настраивает внешний вид таблицы пациентов."""
        style = ttk.Style()

        style.theme_use("clam")

        style.configure(
            "Patients.Treeview",
            background=CARD_COLOR,
            foreground=TEXT_COLOR,
            fieldbackground=CARD_COLOR,
            rowheight=38,
            font=("Arial", 13),
            borderwidth=0
        )

        style.configure(
            "Patients.Treeview.Heading",
            background="#E5F3F8",
            foreground=TEXT_COLOR,
            font=("Arial", 13, "bold"),
            padding=12,
            relief="flat"
        )

        style.map(
            "Patients.Treeview",
            background=[("selected", "#D4EAF2")],
            foreground=[("selected", TEXT_COLOR)]
        )

    def open_patient_form(self, item_id: str | None = None) -> None:
        """Открывает форму добавления нового пациента."""
        is_editing = item_id is not None

        self.form_window = ctk.CTkToplevel(self.root)

        self.form_window.title(
            "Редактирование пациента" if is_editing else "Добавление пациента"
        )
        self.form_window.geometry("450x550")
        self.form_window.resizable(False, False)
        self.form_window.configure(fg_color=BG_COLOR)

        self.form_window.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self.form_window,
            text="Редактирование пациента" if is_editing else "Новый пациент",
            font=("Arial", 24, "bold"),
            text_color=TEXT_COLOR
        )
        title.grid(row=0, column=0, padx=30, pady=(25, 20), sticky="w")

        fields = {
            "full_name": "ФИО",
            "age": "Возраст",
            "height": "Рост (см)",
            "weight": "Вес (кг)"
        }

        self.form_entries = {}

        for row, (field_name, label_text) in enumerate(fields.items(), start=1):
            label = ctk.CTkLabel(
                self.form_window,
                text=label_text,
                font=("Arial", 14),
                text_color=TEXT_COLOR
            )
            label.grid(
                row=row * 2 - 1,
                column=0,
                padx=30,
                pady=(5, 0),
                sticky="w"
            )

            entry = ctk.CTkEntry(
                self.form_window,
                height=38,
                corner_radius=8,
                border_width=1,
                border_color="#D4EAF2",
                fg_color=CARD_COLOR
            )
            entry.grid(
                row=row * 2,
                column=0,
                padx=30,
                pady=(0, 10),
                sticky="ew"
            )

            self.form_entries[field_name] = entry

            sex_label = ctk.CTkLabel(
                self.form_window,
                text="Пол",
                font=("Arial", 14),
                text_color=TEXT_COLOR
            )
            sex_label.grid(
                row=9,
                column=0,
                padx=30,
                pady=(5, 0),
                sticky="w"
            )

            self.sex_menu = ctk.CTkOptionMenu(
                self.form_window,
                values=["Женский", "Мужской"],
                height=38,
                fg_color=ACCENT_COLOR,
                button_color=HOVER_COLOR,
                button_hover_color=HOVER_COLOR
            )
            self.sex_menu.grid(
                row=10,
                column=0,
                padx=30,
                pady=(0, 15),
                sticky="ew"
            )

        if is_editing:
            values = self.table.item(item_id, "values")

            self.form_entries["full_name"].insert(0, values[0])
            self.form_entries["age"].insert(0, values[1])
            self.form_entries["height"].insert(0, values[3])
            self.form_entries["weight"].insert(0, values[4])

            self.sex_menu.set(
                "Женский" if values[2] == "Ж" else "Мужской"
            )

        buttons_frame = ctk.CTkFrame(
            self.form_window,
            fg_color="transparent"
        )
        buttons_frame.grid(
            row=11,
            column=0,
            padx=30,
            pady=(10, 20),
            sticky="ew"
        )

        buttons_frame.grid_columnconfigure((0, 1), weight=1)

        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Отмена",
            height=40,
            fg_color="#E5F3F8",
            hover_color="#D4EAF2",
            text_color=TEXT_COLOR,
            command=self.form_window.destroy
        )
        cancel_button.grid(
            row=0,
            column=0,
            padx=(0, 5),
            sticky="ew"
        )

        save_button = ctk.CTkButton(
            buttons_frame,
            text="Сохранить",
            height=40,
            fg_color=ACCENT_COLOR,
            hover_color=HOVER_COLOR,
            command=lambda: self.save_patient(item_id)
        )
        save_button.grid(
            row=0,
            column=1,
            padx=(5, 0),
            sticky="ew"
        )

    def save_patient(self, item_id: str | None = None) -> None:
        """Проверяет введённые данные и добавляет пациента в таблицу."""
        name = self.form_entries["full_name"].get().strip()
        age_text = self.form_entries["age"].get().strip()
        height_text = self.form_entries["height"].get().strip()
        weight_text = self.form_entries["weight"].get().strip()
        sex = self.sex_menu.get()

        if not name:
            messagebox.showerror(
                "Ошибка",
                "Введите ФИО пациента.",
                parent=self.form_window
            )
            return

        try:
            age = int(age_text)
            height = float(height_text.replace(",", "."))
            weight = float(weight_text.replace(",", "."))

        except ValueError:
            messagebox.showerror(
                "Ошибка",
                "Проверьте правильность возраста, роста и веса.",
                parent=self.form_window
            )
            return

        if age < 0 or height <= 0 or weight <= 0:
            messagebox.showerror(
                "Ошибка",
                "Возраст не может быть отрицательным, "
                "а рост и вес должны быть положительными.",
                parent=self.form_window
            )
            return

        if not math.isfinite(height) or not math.isfinite(weight):
            messagebox.showerror(
                "Ошибка",
                "Рост и вес должны быть конечными числами.",
                parent=self.form_window
            )
            return

        patient = Patient(
            full_name=name,
            age=age,
            sex="Ж" if sex == "Женский" else "М",
            height=height,
            weight=weight
        )

        patient_values = (
            patient.full_name,
            patient.age,
            patient.sex,
            f"{patient.height:g}",
            f"{patient.weight:g}",
            f"{patient.bmi:.1f}"
        )

        if item_id is None:
            # создает новую строку
            self.table.insert(
                "",
                "end",
                values=patient_values
            )
        else:
            # обновляет значения существующей строки
            self.table.item(
                item_id,
                values=patient_values
            )

        self.form_window.destroy()

    def edit_selected_patient(self) -> None:

        # возвращает идентификаторы выделенных строк
        selected = self.table.selection()

        if not selected:
            messagebox.showwarning(
                "Предупреждение",
                "Выберите пациента для редактирования.",
                parent=self.root
            )
            return

        item_id = selected[0]
        self.open_patient_form(item_id)

    def delete_selected_patient(self) -> None:
        """Удаляет выбранного пациента после подтверждения."""
        selected = self.table.selection()

        if not selected:
            messagebox.showwarning(
                "Предупреждение",
                "Выберите пациента для удаления.",
                parent=self.root
            )
            return

        item_id = selected[0]
        patient_name = self.table.item(item_id, "values")[0]

        confirmed = messagebox.askyesno(
            "Подтверждение удаления",
            f"Удалить пациента «{patient_name}»?",
            parent=self.root
        )

        if confirmed:
            self.table.delete(item_id)

def main() -> None:
    """Создаёт главное окно и запускает приложение."""
    # установка светлой темы независимо от системной
    ctk.set_appearance_mode("light")

    root = ctk.CTk()
    PatientApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()