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
    нуклеотидный состав по позициям, а также распределение
    среднего качества отдельных прочтений.

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
    mean_quality_counts = Counter()

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

        read_quality = 0

        for position, character in enumerate(record.quality):
            ascii_code = ord(character)

            if not 33 <= ascii_code <= 126:
                raise ValueError(
                    f"Прочтение {total_reads}: "
                    "некорректный символ качества Phred+33."
                )

            score = ascii_code - 33

            read_quality += score

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

        mean_score = read_quality / length
        mean_quality_counts[int(mean_score)] += 1

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
        "mean_quality_counts": mean_quality_counts,
        "average_quality_by_position": average_quality,
        "base_percentages": base_percentages,
    }


def create_statistics_figure(statistics: dict) -> Figure:
    """
    Создаёт фигуру с четырьмя графиками статистики FASTQ.

    Parameters
    ----------
    statistics : dict
        Результаты анализа, полученные функцией analyze_fastq().

    Returns
    -------
    matplotlib.figure.Figure
        Фигура с графиками качества, нуклеотидного состава,
        распределения длин и среднего качества прочтений.
    """
    figure = Figure(figsize=(10, 7), dpi=150)
    axes = figure.subplots(2, 2)

    quality = statistics["average_quality_by_position"]
    positions = range(1, len(quality) + 1)

    ax = axes[0, 0]
    ax.plot(positions, quality, color=ACCENT_COLOR, linewidth=1.6)
    ax.set_title("Среднее качество по позициям")
    ax.set_xlabel("Позиция в прочтении")
    ax.set_ylabel("Phred score")

    ax = axes[0, 1]

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
    ax.legend(fontsize=9)

    ax = axes[1, 0]
    lengths = sorted(statistics["length_counts"])
    counts = [statistics["length_counts"][length] for length in lengths]

    ax.bar(lengths, counts, color="#78B7D0", width=0.8)
    ax.set_title("Распределение длин прочтений")
    ax.set_xlabel("Длина, п. н.")
    ax.set_ylabel("Количество прочтений")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    ax = axes[1, 1]
    quality_scores = sorted(statistics["mean_quality_counts"])
    quality_amounts = [
        statistics["mean_quality_counts"][score]
        for score in quality_scores
    ]

    ax.bar(
        quality_scores,
        quality_amounts,
        color="#E9A7C0",
        width=0.85
    )
    ax.set_title("Распределение среднего качества")
    ax.set_xlabel("Средний Phred score (целая часть)")
    ax.set_ylabel("Количество прочтений")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    for ax in axes.flat:
        ax.set_facecolor("#F5FAFC")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="y", alpha=0.2)
        ax.set_axisbelow(True)
        ax.title.set_fontsize(11)
        ax.title.set_fontweight("bold")
        ax.tick_params(labelsize=9)

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
    root : ctk.CTk
        Главное окно приложения.
    selected_file : Path or None
        Путь к выбранному FASTQ-файлу.
    result_queue : Queue
        Очередь передачи результатов анализа в основной поток.
    """

    def __init__(self, root: ctk.CTk) -> None:
        """
        Инициализирует главное окно и элементы интерфейса.

        Parameters
        ----------
        root : ctk.CTk
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
        self.analyzing = False

        self.create_widgets()

    def create_widgets(self) -> None:
        """Создаёт основные элементы графического интерфейса."""
        self.content = ctk.CTkScrollableFrame(
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
        file_frame.pack(fill="x", pady=(0, 15))

        self.select_button = ctk.CTkButton(
            file_frame,
            text="Выбрать FASTQ",
            width=180,
            height=44,
            corner_radius=10,
            fg_color=ACCENT_COLOR,
            hover=False,
            font=("Arial", 16),
            command=self.select_file
        )
        self.select_button.pack(side="left", padx=20, pady=20)

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
        self.status_label.pack(anchor="w", pady=(0, 15))

        self.summary_frame = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )
        self.summary_frame.pack(fill="x", pady=(0, 15))

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
            ).pack(pady=(16, 5))

            value_label = ctk.CTkLabel(
                card,
                text="—",
                font=("Arial", 23, "bold"),
                text_color=TEXT_COLOR
            )
            value_label.pack(pady=(0, 16))

            self.summary_labels[key] = value_label

        self.chart_label = ctk.CTkLabel(
            self.content,
            text="Графики появятся после анализа файла.",
            font=("Arial", 16),
            text_color=SECONDARY_TEXT_COLOR
        )
        self.chart_label.pack(fill="x", pady=(10, 20))

    def select_file(self) -> None:
        """Открывает диалог выбора FASTQ-файла и запускает анализ."""
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
        """Запускает обработку выбранного файла в отдельном потоке."""
        if self.selected_file is None or self.analyzing:
            return

        self.analyzing = True
        self.select_button.configure(state="disabled")
        self.status_label.configure(text="Анализ файла выполняется...")

        self.chart_image = None
        self.chart_label.configure(
            text="Анализ данных...",
            image=None
        )

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
        filepath : Path
            Путь к FASTQ-файлу.
        """
        try:
            result = analyze_fastq(filepath)
            self.result_queue.put(("success", result))
        except (OSError, UnicodeError, ValueError, TypeError) as error:
            self.result_queue.put(("error", str(error)))

    def check_results(self) -> None:
        """Проверяет очередь результатов и обновляет интерфейс."""
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
        statistics : dict
            Результаты анализа FASTQ-файла.
        """
        values = {
            "total_reads": f"{statistics['total_reads']:,}".replace(",", " "),
            "average_length": f"{statistics['average_length']:.1f} п. н.",
        }

        for key, value in values.items():
            self.summary_labels[key].configure(text=value)

        figure = create_statistics_figure(statistics)

        buffer = BytesIO()
        figure.savefig(buffer, format="png", dpi=150)
        buffer.seek(0)

        image = Image.open(buffer).copy()
        buffer.close()
        figure.clear()

        self.chart_image = ctk.CTkImage(
            light_image=image,
            dark_image=image,
            size=(1000, 700)
        )

        self.chart_label.configure(
            text="",
            image=self.chart_image
        )

        self.status_label.configure(
            text="Анализ FASTQ-файла завершён."
        )


def main() -> None:
    """Создаёт главное окно и запускает Mini FastQC."""
    ctk.set_appearance_mode("light")

    root = ctk.CTk()
    FastQCApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
