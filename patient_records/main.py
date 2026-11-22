import customtkinter as ctk
from tkinter import ttk
import math
from tkinter import messagebox
import json
from dataclasses import asdict
from pathlib import Path
from io import BytesIO
from PIL import Image

from patient import Patient
from statistics_charts import create_statistics_figure


BG_COLOR = "#F5F8FC"
TEXT_COLOR = "#253746"
ACCENT_COLOR = "#4F9BB8"
HOVER_COLOR = "#3D829D"
CARD_COLOR = "#FFFFFF"
SECONDARY_TEXT_COLOR = "#748694"

DATA_FILE = Path(__file__).resolve().parent / "patients.json"

class PatientApp:
    """
    Графическое приложение для учёта пациентов.

    Обеспечивает добавление, редактирование и удаление записей
    пациентов, их отображение в таблице, сохранение данных
    в JSON-файл и визуализацию статистики.

    Attributes
    ----------
    root: ctk.CTk
        Главное окно приложения.
    patients: dict[str, Patient]
        Словарь объектов пациентов, ключами которого являются
        идентификаторы строк таблицы.
    table: ttk.Treeview
        Таблица с информацией о пациентах.
    patient_count_label: ctk.CTkLabel
        Метка с текущим количеством пациентов.
    data_load_failed: bool
        Признак ошибки загрузки данных из JSON-файла.
    """

    def __init__(self, root: ctk.CTk) -> None:
        """
        Инициализирует приложение для учёта пациентов.

        Настраивает главное окно, создаёт словарь пациентов,
        применяет стили таблицы, формирует элементы интерфейса
        и загружает сохранённые данные из JSON-файла.

        Parameters
        ----------
        root: ctk.CTk
            Главное окно приложения.
        """
        self.root = root
        self.root.title("Учёт пациентов")
        self.root.geometry("1100x700")
        self.root.minsize(850, 550)
        self.root.configure(fg_color=BG_COLOR)

        # первый столбец и третья строка должны расширяться вместе с окном
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(2, weight=1)

        self.patients: dict[str, Patient] = {}

        self.configure_table_style()
        self.create_widgets()

        self.load_patients()

    def create_widgets(self) -> None:
        """
        Создаёт и размещает основные элементы интерфейса приложения.

        Формирует заголовок окна, панель управления с кнопками
        добавления, редактирования, просмотра статистики и удаления
        пациентов, а также контейнер для таблицы пациентов
        с заголовком и счётчиком записей.

        Для создания таблицы вызывает метод create_table().
        """
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
            ("+ Добавить пациента", ACCENT_COLOR),
            ("Редактировать", "#E5F3F8", "#D4EAF2"),
            ("Статистика", "#E5F3F8", "#D4EAF2"),
            ("Удалить", "#FCECED", "#F5D5D8")
        ]

        for column, (text, color) in enumerate(buttons):
            button = ctk.CTkButton(
                toolbar,
                text=text,
                width=190,
                height=42,
                corner_radius=10,
                fg_color=color,
                hover=False,
                text_color="#FFFFFF" if column == 0 else TEXT_COLOR,
                font=("Arial", 16)
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

            elif text == "Статистика":
                button.configure(command=self.open_statistics_window)

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

        # заголовок и количество пациентов
        table_header = ctk.CTkFrame(
            table_frame,
            fg_color="transparent"
        )
        table_header.pack(
            fill="x",
            padx=20,
            pady=(20, 15)
        )

        table_title = ctk.CTkLabel(
            table_header,
            text="Список пациентов",
            font=("Arial", 20, "bold"),
            text_color=TEXT_COLOR
        )
        table_title.pack(side="left")

        self.patient_count_label = ctk.CTkLabel(
            table_header,
            text=f"Всего пациентов: {len(self.patients)}",
            font=("Arial", 18, "bold"),
            text_color=TEXT_COLOR
        )
        self.patient_count_label.pack(side="right")

        self.create_table(table_frame)

    def create_table(self, parent: ctk.CTkFrame) -> None:
        """
        Создаёт таблицу пациентов с вертикальной полосой прокрутки.

        Настраивает столбцы для отображения ФИО, возраста, пола,
        роста, веса и ИМТ пациентов. Устанавливает заголовки,
        ширину и выравнивание столбцов, а также обеспечивает
        возможность выделения нескольких строк.

        Parameters
        ----------
        parent : ctk.CTkFrame
            Контейнер, в котором размещаются таблица и полоса прокрутки.
        """
        columns = ("name", "age", "sex", "height", "weight", "bmi")

        self.table = ttk.Treeview(
            parent,
            columns=columns,
            show="headings",
            selectmode="extended",
            style="Patients.Treeview"
        )

        # отображение полосы покрутки
        scrollbar = ctk.CTkScrollbar(
            parent,
            orientation="vertical",
            command=self.table.yview,
            width=16,
            corner_radius=12,
            fg_color="#FFFFFF",
            button_color="#78B7D0",
            button_hover_color="#509FC0"
        )

        self.table.configure(
            yscrollcommand=scrollbar.set
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
                width=280 if column == "name" else 100,
                minwidth=230 if column == "name" else 70,
                anchor="center",
                stretch=True
            )

        self.table.column("name", anchor="w")

        scrollbar.pack(
            side="right",
            fill="y",
            padx=(0, 10),
            pady=(0, 15)
        )

        self.table.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(20, 0),
            pady=(0, 15)
        )

    def configure_table_style(self) -> None:
        """
        Настраивает оформление таблицы пациентов и её заголовков.

        Применяет тему оформления ttk, устанавливает цвета,
        шрифты, высоту строк и отступы заголовков. Убирает
        стандартную рамку таблицы и задаёт светло-голубой
        цвет выделенных строк.

        Обеспечивает постоянное оформление заголовков столбцов
        при наведении курсора и нажатии.
        """
        style = ttk.Style()

        style.theme_use("clam")

        style.configure(
            "Patients.Treeview",
            background=CARD_COLOR,
            foreground=TEXT_COLOR,
            fieldbackground=CARD_COLOR,
            rowheight=44,
            font=("Arial", 16),
            borderwidth=0,
            relief="flat"
        )

        style.configure(
            "Patients.Treeview.Heading",
            background="#E5F3F8",
            foreground=TEXT_COLOR,
            font=("Arial", 16, "bold"),
            padding=14,
            relief="flat"
        )

        # убирает стандартную рамку таблицы
        style.layout(
            "Patients.Treeview",
            [("Treeview.treearea", {"sticky": "nswe"})]
        )

        # выделение строк
        style.map(
            "Patients.Treeview",
            background=[
                ("selected", "#D4EAF2")
            ],
            foreground=[
                ("selected", TEXT_COLOR)
            ]
        )

        # заголовки столбцов не меняют цвет при наведении и нажатии
        style.map(
            "Patients.Treeview.Heading",
            background=[
                ("active", "#E5F3F8"),
                ("pressed", "#E5F3F8")
            ],
            foreground=[
                ("active", TEXT_COLOR),
                ("pressed", TEXT_COLOR)
            ],
            relief=[
                ("active", "flat"),
                ("pressed", "flat")
            ]
        )

    def open_patient_form(self, item_id: str | None = None) -> None:
        """
        Открывает форму добавления или редактирования пациента.

        Создаёт отдельное окно с полями для ввода ФИО, возраста,
        роста, веса и выбора пола пациента.

        Если передан идентификатор существующей строки таблицы,
        заполняет поля формы данными выбранного пациента.
        В противном случае открывает пустую форму для добавления
        новой записи.

        Parameters
        ----------
        item_id: str or None, optional
            Идентификатор строки пациента в таблице.
            Если None, создаётся форма добавления нового пациента.
            По умолчанию None.
        """
        is_editing = item_id is not None

        self.form_window = ctk.CTkToplevel(self.root)

        self.form_window.title(
            "Редактирование пациента" if is_editing else "Добавление пациента"
        )
        self.form_window.geometry("450x630")
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
                font=("Arial", 16),
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
                height=42,
                corner_radius=8,
                border_width=1,
                border_color="#D4EAF2",
                fg_color=CARD_COLOR,
                font=("Arial", 16),
                text_color=TEXT_COLOR
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
            font=("Arial", 16),
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
            height=42,
            font=("Arial", 16),
            dropdown_font=("Arial", 16),
            fg_color=ACCENT_COLOR,
            button_color=HOVER_COLOR,
            button_hover_color=HOVER_COLOR,
            text_color="#FFFFFF"
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
            height=44,
            font=("Arial", 16),
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
            height=44,
            font=("Arial", 16),
            fg_color=ACCENT_COLOR,
            hover_color=HOVER_COLOR,
            text_color="#FFFFFF",
            command=lambda: self.save_patient_form(item_id)
        )
        save_button.grid(
            row=0,
            column=1,
            padx=(5, 0),
            sticky="ew"
        )

    def save_patient_form(self, item_id: str | None = None) -> None:
        """
        Проверяет и сохраняет данные пациента из формы.

        Получает значения полей формы и проверяет корректность
        ФИО, возраста, роста и веса. При обнаружении ошибок
        выводит соответствующее сообщение и прекращает сохранение.

        Если идентификатор строки не передан, добавляет нового
        пациента в таблицу. В противном случае обновляет
        существующую запись.

        После успешного сохранения закрывает форму, обновляет
        счётчик пациентов и записывает данные в JSON-файл.

        Parameters
        ----------
        item_id : str or None, optional
            Идентификатор строки редактируемого пациента.
            Если None, создаётся новая запись.
            По умолчанию None.
        """
        if self.data_load_failed:
            messagebox.showerror(
                "Ошибка",
                "Изменение данных недоступно: "
                "не удалось загрузить файл пациентов."
            )
            return

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
            item_id = self.table.insert(
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

        # сохранение нового или обновлённого объекта пациента
        self.patients[item_id] = patient

        self.form_window.destroy()
        self.update_patient_count()
        self.save_patients()

    def edit_selected_patient(self) -> None:
        """
        Открывает форму редактирования выбранного пациента.

        Получает идентификаторы выделенных строк таблицы.
        Если ни одна строка не выбрана, выводит предупреждение.

        При наличии выделенных строк передаёт идентификатор
        первой из них методу open_patient_form() для открытия
        формы с данными пациента.
        """
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

    def open_statistics_window(self) -> None:
        """
        Открывает окно со статистикой пациентов.

        Создаёт отдельное окно для отображения сводных показателей
        и графиков. Рассчитывает общее количество пациентов,
        средний возраст и средний индекс массы тела (ИМТ).

        Формирует четыре графика с помощью функции
        create_statistics_figure(): распределение пациентов по полу
        и возрасту, распределение ИМТ по полу и зависимость
        ИМТ от возраста.

        Если список пациентов пуст, отображает сообщение
        об отсутствии данных для построения статистики.
        """
        window = ctk.CTkToplevel(self.root)
        window.title("Статистика пациентов")
        window.geometry("1100x800")
        window.configure(fg_color="#F5FAFC")

        title = ctk.CTkLabel(
            window,
            text="Статистика пациентов",
            font=("Arial", 24, "bold"),
            text_color=TEXT_COLOR
        )
        title.pack(pady=(25, 15))

        if not self.patients:
            message = ctk.CTkLabel(
                window,
                text="Нет данных для построения статистики.",
                font=("Arial", 16),
                text_color=TEXT_COLOR
            )
            message.pack(pady=30)
            return

        patients = list(self.patients.values())

        total_patients = len(patients)

        average_age = sum(
            patient.age for patient in patients
        ) / total_patients

        average_bmi = sum(
            patient.bmi for patient in patients
        ) / total_patients

        stats_frame = ctk.CTkFrame(
            window,
            fg_color="transparent"
        )
        stats_frame.pack(
            fill="x",
            padx=30,
            pady=(10, 15)
        )

        for column in range(3):
            stats_frame.grid_columnconfigure(column, weight=1)

        summary = [
            ("Всего пациентов", str(total_patients)),
            ("Средний возраст", f"{average_age:.1f} лет"),
            ("Средний ИМТ", f"{average_bmi:.1f}")
        ]

        for column, (label, value) in enumerate(summary):
            card = ctk.CTkFrame(
                stats_frame,
                fg_color="#FFFFFF",
                corner_radius=12
            )
            card.grid(
                row=0,
                column=column,
                sticky="ew",
                padx=8
            )

            ctk.CTkLabel(
                card,
                text=label,
                font=("Arial", 13),
                text_color="#607D8B"
            ).pack(pady=(12, 4))

            ctk.CTkLabel(
                card,
                text=value,
                font=("Arial", 22, "bold"),
                text_color=TEXT_COLOR
            ).pack(pady=(0, 12))

        fig = create_statistics_figure(patients)

        buffer = BytesIO()
        fig.savefig(buffer, format="png", dpi=200)
        buffer.seek(0)

        image = Image.open(buffer).copy()
        buffer.close()

        chart_image = ctk.CTkImage(
            light_image=image,
            dark_image=image,
            size=(1000, 650)
        )

        chart_label = ctk.CTkLabel(
            window,
            text="",
            image=chart_image
        )

        chart_label.pack(
            padx=20,
            pady=(0, 20)
        )

    def delete_selected_patient(self) -> None:
        """
        Удаляет выбранных пациентов после подтверждения пользователя.

        Проверяет доступность изменения данных и наличие выделенных
        строк в таблице. Если пациенты не выбраны, отображает
        предупреждение.

        Запрашивает подтверждение удаления. При положительном
        ответе удаляет выбранные строки из таблицы и соответствующие
        объекты из словаря пациентов.

        После удаления обновляет счётчик пациентов и сохраняет
        изменения в JSON-файл.
        """
        if self.data_load_failed:
            messagebox.showerror(
                "Ошибка",
                "Изменение данных недоступно: "
                "не удалось загрузить файл пациентов."
            )
            return

        selected = self.table.selection()

        if not selected:
            messagebox.showwarning(
                "Предупреждение",
                "Выберите хотя бы одного пациента."
            )
            return

        confirmed = messagebox.askyesno(
            "Подтверждение удаления",
            f"Удалить выбранных пациентов ({len(selected)})?",
            parent=self.root
        )

        if confirmed:
            for item_id in selected:
                self.table.delete(item_id)
                del self.patients[item_id]

            self.update_patient_count()
            self.save_patients()

    def save_patients(self) -> None:
        """
        Сохраняет данные пациентов в JSON-файл.

        Проверяет успешность загрузки исходных данных.
        Преобразует объекты Patient из словаря пациентов
        в список словарей с помощью функции asdict().

        Записывает полученные данные в файл patients.json
        в кодировке UTF-8 с сохранением кириллицы.

        Raises
        ------
        RuntimeError
            Если при загрузке исходных данных произошла ошибка
            и сохранение было заблокировано.
        """
        if self.data_load_failed:
            raise RuntimeError(
                "Сохранение запрещено: данные не были загружены."
            )

        data = [asdict(patient) for patient in self.patients.values()]

        with DATA_FILE.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    def load_patients(self) -> None:
        """
        Загружает и проверяет данные пациентов из JSON-файла.

        Проверяет наличие файла patients.json и считывает его
        содержимое. Для каждой записи создаёт объект Patient
        и проверяет корректность ФИО, возраста, пола, роста и веса.

        Если данные успешно загружены, добавляет пациентов
        в таблицу и словарь self.patients, после чего обновляет
        счётчик записей.

        При ошибке чтения или проверки данных устанавливает
        флаг data_load_failed и отображает сообщение об ошибке.
        Это предотвращает перезапись исходного JSON-файла
        некорректными или неполными данными.
        """
        self.data_load_failed = False

        if not DATA_FILE.exists():
            return

        try:
            with DATA_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, list):
                raise ValueError("Ожидался список пациентов.")

            patients = []

            for index, patient_data in enumerate(data, start=1):
                if not isinstance(patient_data, dict):
                    raise ValueError(
                        f"Запись №{index} должна быть словарём."
                    )

                patient = Patient(**patient_data)

                if (
                        not isinstance(patient.full_name, str)
                        or not patient.full_name.strip()
                        or type(patient.age) is not int
                        or patient.age < 0
                        or patient.sex not in ("М", "Ж")
                        or type(patient.height) not in (int, float)
                        or type(patient.weight) not in (int, float)
                        or not math.isfinite(patient.height)
                        or not math.isfinite(patient.weight)
                        or patient.height <= 0
                        or patient.weight <= 0
                ):
                    raise ValueError(
                        f"Некорректные данные пациента №{index}."
                    )

                patients.append(patient)

        except (OSError, UnicodeError, json.JSONDecodeError,
                TypeError, ValueError) as error:
            self.data_load_failed = True

            messagebox.showerror(
                "Ошибка загрузки данных",
                f"Не удалось загрузить пациентов:\n{error}\n\n"
                "Исходный JSON-файл не будет перезаписан.",
                parent=self.root
            )
            return

        for patient in patients:
            patient_values = (
                patient.full_name,
                patient.age,
                patient.sex,
                f"{patient.height:g}",
                f"{patient.weight:g}",
                f"{patient.bmi:.1f}"
            )

            item_id = self.table.insert(
                "",
                "end",
                values=patient_values
            )

            self.patients[item_id] = patient

        self.update_patient_count()

    def update_patient_count(self) -> None:
        """
        Обновляет счётчик пациентов в главном окне приложения.

        Определяет текущее количество пациентов по числу
        элементов словаря self.patients и обновляет текст
        метки patient_count_label.
        """
        self.patient_count_label.configure(
            text=f"Всего пациентов: {len(self.patients)}"
        )


def main() -> None:
    """
    Создаёт главное окно и запускает приложение учёта пациентов.

    Устанавливает светлую тему оформления CustomTkinter,
    создаёт главное окно и экземпляр класса PatientApp.

    Запускает основной цикл обработки событий графического
    интерфейса с помощью метода mainloop().
    """
    # установка светлой темы независимо от системной
    ctk.set_appearance_mode("light")

    root = ctk.CTk()
    PatientApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()