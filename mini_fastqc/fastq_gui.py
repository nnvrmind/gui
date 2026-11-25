import sys
from collections import Counter
from io import BytesIO
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
from tkinter import filedialog, messagebox

import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from PIL import Image

from mini_fastqc.fastq_reader import FastqReader


BG_COLOR = "#F5F8FC"
TEXT_COLOR = "#253746"
ACCENT_COLOR = "#4F9BB8"
CARD_COLOR = "#FFFFFF"
SECONDARY_TEXT_COLOR = "#748694"

BASE_COLORS = {
    "A": "#79B69A",
    "C": "#78B7D0",
    "G": "#D6AD73",
    "T": "#E9A7C0",
}


def analyze_fastq(filepath: Path) -> dict:
    """
    Вычисляет статистические показатели FASTQ-файла.

    Последовательно считывает записи с помощью FastqReader.
    Рассчитывает количество и длины прочтений, качество и
    нуклеотидный состав по позициям.

    Parameters
    ----------
    filepath : Path
        Путь к анализируемому FASTQ-файлу.

    Returns
    -------
    dict
        Словарь со сводными показателями и данными для графиков.

    Raises
    ------
    ValueError
        Если файл пуст или содержит некорректные данные.
    OSError
        Если файл невозможно прочитать.
    """
    reader = FastqReader(filepath)

    total_reads = 0
    total_bases = 0

    length_counts = Counter()

    quality_sums = []
    quality_counts = []
    position_counts = []
    base_counts = {base: [] for base in "ACGT"}

    for record in reader:
        sequence = record.seq.upper()
        length = len(record)

        total_reads += 1
        total_bases += length
        length_counts[length] += 1

        for position, character in enumerate(record.quality):
            ascii_code = ord(character)

            if not 33 <= ascii_code <= 126:
                raise ValueError(
                    f"Прочтение {total_reads}: "
                    "некорректный символ качества Phred+33."
                )

            score = ascii_code - 33

            if position == len(quality_sums):
                quality_sums.append(0)
                quality_counts.append(0)
                position_counts.append(0)

                for base in "ACGT":
                    base_counts[base].append(0)

            quality_sums[position] += score
            quality_counts[position] += 1
            position_counts[position] += 1

            nucleotide = sequence[position]

            if nucleotide in base_counts:
                base_counts[nucleotide][position] += 1

    if total_reads == 0:
        raise ValueError("FASTQ-файл не содержит прочтений.")

    average_quality = [
        total / count
        for total, count in zip(quality_sums, quality_counts)
    ]

    base_percentages = {
        base: [
            count / total * 100
            for count, total in zip(
                base_counts[base],
                position_counts
            )
        ]
        for base in "ACGT"
    }

    return {
        "total_reads": total_reads,
        "average_length": total_bases / total_reads,
        "length_counts": length_counts,
        "average_quality_by_position": average_quality,
        "base_percentages": base_percentages,
    }


def create_statistics_figure(
    statistics: dict,
    chart_index: int
) -> Figure:
    """
    Создаёт выбранный статистический график FASTQ.

    Parameters
    ----------
    statistics: dict
        Результаты анализа FASTQ-файла.
    chart_index: int
        Индекс графика от 0 до 2.

    Returns
    -------
    matplotlib.figure.Figure
        Фигура с выбранным графиком.

    Raises
    ------
    ValueError
        Если индекс графика не находится в диапазоне от 0 до 2.
    """
    figure = Figure(figsize=(10, 5.5), dpi=150)
    ax = figure.add_subplot(111)

    if chart_index == 0:
        quality = statistics["average_quality_by_position"]
        positions = range(1, len(quality) + 1)

        ax.plot(
            positions,
            quality,
            color=ACCENT_COLOR,
            linewidth=1.6
        )
        ax.set_title("Среднее качество по позициям")
        ax.set_xlabel("Позиция в прочтении")
        ax.set_ylabel("Phred score")

    elif chart_index == 1:
        quality = statistics["average_quality_by_position"]
        positions = range(1, len(quality) + 1)

        for base, percentages in statistics["base_percentages"].items():
            ax.plot(
                positions,
                percentages,
                color=BASE_COLORS[base],
                linewidth=1.5,
                label=base
            )

        ax.set_title("Нуклеотидный состав по позициям")
        ax.set_xlabel("Позиция в прочтении")
        ax.set_ylabel("Содержание, %")
        ax.set_ylim(0, 100)
        ax.legend(fontsize=10)

    elif chart_index == 2:
        lengths = sorted(statistics["length_counts"])
        counts = [
            statistics["length_counts"][length]
            for length in lengths
        ]

        ax.bar(
            lengths,
            counts,
            color="#78B7D0",
            width=0.8
        )
        ax.set_title("Распределение длин прочтений")
        ax.set_xlabel("Длина, п. н.")
        ax.set_ylabel("Количество прочтений")
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    else:
        raise ValueError("Недопустимый индекс графика")

    ax.set_facecolor("#F5FAFC")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.2)
    ax.set_axisbelow(True)
    ax.title.set_fontsize(13)
    ax.title.set_fontweight("bold")
    ax.tick_params(labelsize=10)

    figure.patch.set_facecolor(CARD_COLOR)
    figure.tight_layout(pad=2.8)

    return figure


class FastQCApp:
    """
    Графическое приложение для анализа FASTQ-файлов.

    Позволяет выбрать файл через диалоговое окно, выполнить
    анализ в отдельном потоке и отобразить статистические
    показатели и графики.

    Attributes
    ----------
    root: ctk.CTk
        Главное окно приложения.
    selected_file: Path or None
        Путь к выбранному FASTQ-файлу.
    result_queue: Queue
        Очередь передачи результатов анализа в основной поток.
    """

    def __init__(self, root: ctk.CTk) -> None:
        """
        Инициализирует главное окно и элементы интерфейса.

        Parameters
        ----------
        root: ctk.CTk
            Главное окно приложения.
        """
        self.root = root
        self.root.title("Mini FastQC")
        self.root.geometry("1150x900")
        self.root.minsize(850, 650)
        self.root.configure(fg_color=BG_COLOR)

        self.selected_file: Path | None = None
        self.result_queue = Queue()
        self.chart_image = None
        self.chart_source_image = None
        self.chart_images = []
        self.current_chart_index = 0
        self.analyzing = False

        self.create_widgets()

        self.root.bind("<Configure>", self.resize_charts)

    def create_widgets(self) -> None:
        """
        Создаёт и размещает элементы графического интерфейса.

        Формирует заголовок приложения, область выбора FASTQ-файла,
        строку состояния, карточки со сводной статистикой и область
        отображения графиков. Добавляет кнопки переключения между
        тремя графиками и счётчик текущего графика.
        """
        self.content = ctk.CTkFrame(
            self.root,
            fg_color="transparent"
        )
        self.content.pack(fill="both", expand=True, padx=30, pady=25)

        ctk.CTkLabel(
            self.content,
            text="Mini FastQC",
            font=("Arial", 30, "bold"),
            text_color=TEXT_COLOR
        ).pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(
            self.content,
            text="Анализ качества данных секвенирования",
            font=("Arial", 16),
            text_color=SECONDARY_TEXT_COLOR
        ).pack(anchor="w", pady=(0, 20))

        file_frame = ctk.CTkFrame(
            self.content,
            fg_color=CARD_COLOR,
            corner_radius=15
        )
        file_frame.pack(fill="x", pady=(0, 10))

        self.select_button = ctk.CTkButton(
            file_frame,
            text="Выбрать FASTQ",
            width=180,
            height=44,
            corner_radius=10,
            fg_color=ACCENT_COLOR,
            hover=False,
            font=("Arial", 16),
            text_color="#FFFFFF",
            command=self.select_file
        )
        self.select_button.pack(side="left", padx=20, pady=10)

        self.file_label = ctk.CTkLabel(
            file_frame,
            text="Файл не выбран",
            font=("Arial", 15),
            text_color=TEXT_COLOR,
            anchor="w"
        )
        self.file_label.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 20)
        )

        self.status_label = ctk.CTkLabel(
            self.content,
            text="Выберите файл для начала анализа.",
            font=("Arial", 15),
            text_color=SECONDARY_TEXT_COLOR
        )
        self.status_label.pack(anchor="w", pady=(0, 10))

        self.summary_frame = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )
        self.summary_frame.pack(fill="x", pady=(0, 10))

        self.summary_labels = {}

        cards = [
            ("total_reads", "Количество прочтений"),
            ("average_length", "Средняя длина"),
        ]

        for column, (key, title) in enumerate(cards):
            self.summary_frame.grid_columnconfigure(column, weight=1)

            card = ctk.CTkFrame(
                self.summary_frame,
                fg_color=CARD_COLOR,
                corner_radius=12
            )
            card.grid(
                row=0,
                column=column,
                sticky="ew",
                padx=5
            )

            ctk.CTkLabel(
                card,
                text=title,
                font=("Arial", 13),
                text_color=SECONDARY_TEXT_COLOR
            ).pack(side="left", padx=(20, 10), pady=12)

            value_label = ctk.CTkLabel(
                card,
                text="—",
                font=("Arial", 23, "bold"),
                text_color=TEXT_COLOR
            )
            value_label.pack(side="right", padx=(10, 20), pady=12)

            self.summary_labels[key] = value_label

        self.chart_label = ctk.CTkLabel(
            self.content,
            text="Графики появятся после анализа файла.",
            font=("Arial", 16),
            text_color=SECONDARY_TEXT_COLOR
        )

        self.chart_label.pack(
            fill="both",
            expand=True,
            pady=(10, 10)
        )

        navigation_frame = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )
        navigation_frame.pack(pady=(0, 10))

        self.previous_button = ctk.CTkButton(
            navigation_frame,
            text="← Назад",
            width=120,
            height=40,
            fg_color=ACCENT_COLOR,
            text_color="#FFFFFF",
            hover=False,
            state="disabled",
            command=lambda: self.change_chart(-1)
        )
        self.previous_button.pack(side="left", padx=10)

        self.chart_counter = ctk.CTkLabel(
            navigation_frame,
            text="0 / 3",
            font=("Arial", 15),
            text_color=TEXT_COLOR
        )
        self.chart_counter.pack(side="left", padx=15)

        self.next_button = ctk.CTkButton(
            navigation_frame,
            text="Далее →",
            width=120,
            height=40,
            fg_color=ACCENT_COLOR,
            text_color="#FFFFFF",
            hover=False,
            state="disabled",
            command=lambda: self.change_chart(1)
        )
        self.next_button.pack(side="left", padx=10)

    def select_file(self) -> None:
        """
        Открывает диалог выбора FASTQ-файла.

        Позволяет выбрать файл с расширением .fastq или .fq,
        сохраняет путь к нему, обновляет название файла
        в интерфейсе и запускает анализ.

        Если пользователь отменяет выбор, функция завершает
        работу без изменения текущего состояния приложения.
        """
        filepath = filedialog.askopenfilename(
            parent=self.root,
            title="Выберите FASTQ-файл",
            filetypes=[
                ("FASTQ-файлы", "*.fastq *.fq"),
                ("Все файлы", "*.*"),
            ]
        )

        if not filepath:
            return

        self.selected_file = Path(filepath)
        self.file_label.configure(text=self.selected_file.name)
        self.start_analysis()

    def start_analysis(self) -> None:
        """
        Подготавливает интерфейс и запускает анализ FASTQ-файла.

        Проверяет наличие выбранного файла и отсутствие другого
        выполняющегося анализа. Сбрасывает предыдущие результаты,
        очищает графики и временно отключает элементы управления.

        Запускает обработку файла в отдельном потоке, чтобы
        графический интерфейс оставался отзывчивым, и начинает
        проверку очереди результатов.
        """
        if self.selected_file is None or self.analyzing:
            return

        self.analyzing = True
        self.select_button.configure(state="disabled")
        self.status_label.configure(text="Анализ файла выполняется...")

        self.chart_label.configure(image=None)
        self.chart_label.configure(text="Анализ данных...")

        self.chart_image = None
        self.chart_source_image = None
        self.chart_images = []
        self.current_chart_index = 0

        self.chart_counter.configure(text="0 / 3")
        self.previous_button.configure(state="disabled")
        self.next_button.configure(state="disabled")

        for label in self.summary_labels.values():
            label.configure(text="—")

        worker = Thread(
            target=self.analyze_in_background,
            args=(self.selected_file,),
            daemon=True
        )
        worker.start()

        self.check_results()

    def analyze_in_background(self, filepath: Path) -> None:
        """
        Вычисляет статистику в рабочем потоке.

        Parameters
        ----------
        filepath: Path
            Путь к FASTQ-файлу.
        """
        try:
            result = analyze_fastq(filepath)
            self.result_queue.put(("success", result))
        except (OSError, UnicodeError, ValueError, TypeError) as error:
            self.result_queue.put(("error", str(error)))

    def check_results(self) -> None:
        """
        Проверяет очередь результатов фонового анализа.

        Если результат ещё не получен, планирует повторную
        проверку через 100 миллисекунд.

        После завершения анализа восстанавливает доступность
        кнопки выбора файла. При успешной обработке отображает
        статистику и графики, а при ошибке выводит сообщение
        с описанием возникшей проблемы.
        """
        try:
            status, result = self.result_queue.get_nowait()
        except Empty:
            if self.analyzing:
                self.root.after(100, self.check_results)
            return

        self.analyzing = False
        self.select_button.configure(state="normal")

        if status == "error":
            self.status_label.configure(text="Ошибка анализа файла.")
            self.chart_label.configure(text="Не удалось построить графики.")
            messagebox.showerror(
                "Ошибка FASTQ",
                result,
                parent=self.root
            )
            return

        try:
            self.show_statistics(result)
        except Exception as error:
            self.status_label.configure(text="Ошибка отображения статистики.")
            messagebox.showerror(
                "Ошибка графиков",
                str(error),
                parent=self.root
            )

    def show_statistics(self, statistics: dict) -> None:
        """
        Отображает сводные показатели и статистические графики.

        Parameters
        ----------
        statistics: dict
            Результаты анализа FASTQ-файла.
        """
        values = {
            "total_reads": f"{statistics['total_reads']:,}".replace(",", " "),
            "average_length": f"{statistics['average_length']:.1f} п. н.",
        }

        for key, value in values.items():
            self.summary_labels[key].configure(text=value)

        self.chart_images = []

        for index in range(3):
            figure = create_statistics_figure(statistics, index)

            buffer = BytesIO()
            figure.savefig(buffer, format="png", dpi=150)
            buffer.seek(0)

            self.chart_images.append(
                Image.open(buffer).copy()
            )

            buffer.close()
            figure.clear()

        self.show_chart(0)

        self.status_label.configure(text="Анализ FASTQ-файла завершён.")

    def change_chart(self, direction: int) -> None:
        """
        Переключает отображаемый статистический график.

        Parameters
        ----------
        direction: int
            Направление переключения: -1 назад, 1 вперёд.
        """
        new_index = self.current_chart_index + direction

        if 0 <= new_index < len(self.chart_images):
            self.show_chart(new_index)

    def show_chart(self, index: int) -> None:
        """
        Отображает график с указанным индексом.

        Parameters
        ----------
        index: int
            Индекс графика в списке изображений.
        """
        if not 0 <= index < len(self.chart_images):
            return

        self.current_chart_index = index
        self.chart_source_image = self.chart_images[index]

        if self.chart_image is None:
            self.chart_image = ctk.CTkImage(
                light_image=self.chart_source_image,
                dark_image=self.chart_source_image,
                size=(600, 330)
            )
        else:
            self.chart_image.configure(
                light_image=self.chart_source_image,
                dark_image=self.chart_source_image
            )

        self.chart_label.configure(image=self.chart_image)
        self.chart_label.configure(text="")

        self.chart_counter.configure(
            text=f"{index + 1} / {len(self.chart_images)}"
        )

        self.previous_button.configure(
            state="normal" if index > 0 else "disabled"
        )

        self.next_button.configure(
            state="normal"
            if index < len(self.chart_images) - 1
            else "disabled"
        )

        self.root.after_idle(self.resize_charts)

    def resize_charts(self, event=None) -> None:
        """
        Масштабирует текущий график по доступной области окна.

        Сохраняет пропорции изображения и учитывает пространство,
        необходимое для элементов интерфейса и кнопок навигации.

        Parameters
        ----------
        event: tkinter.Event, optional
            Событие изменения размеров окна.
        """
        if event is not None and event.widget is not self.root:
            return

        if self.chart_image is None or self.chart_source_image is None:
            return

        available_width = max(
            1,
            self.chart_label.winfo_width() - 20
        )
        available_height = max(
            1,
            self.chart_label.winfo_height() - 20
        )

        aspect_ratio = (
                self.chart_source_image.width
                / self.chart_source_image.height
        )

        new_width = min(
            available_width,
            int(available_height * aspect_ratio)
        )
        new_width = max(1, new_width)

        new_height = max(
            1,
            int(new_width / aspect_ratio)
        )

        self.chart_image.configure(
            size=(new_width, new_height)
        )


def main() -> None:
    """
    Инициализирует и запускает графическое приложение Mini FastQC.

    Устанавливает светлую тему CustomTkinter. Для Linux
    выбирает способ отрисовки элементов интерфейса,
    создаёт главное окно и экземпляр FastQCApp.

    Запускает основной цикл обработки событий Tkinter.
    """
    ctk.set_appearance_mode("light")

    if sys.platform.startswith("linux"):
        ctk.DrawEngine.preferred_drawing_method = "circle_shapes"

    root = ctk.CTk()
    FastQCApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
