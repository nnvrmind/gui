import argparse
from pathlib import Path
from itertools import islice

from mini_fastqc.fastq_reader import FastqReader


def main() -> None:
    """
    Запускает Mini FastQC в консольном или графическом режиме.

    Returns
    -------
    None
        Результаты анализа выводятся в терминал или GUI.
    """
    parser = argparse.ArgumentParser(
        description="Mini FastQC — анализ качества FASTQ-файлов"
    )

    parser.add_argument(
        "filepath",
        type=Path,
        nargs="?",
        help="Путь к FASTQ-файлу"
    )

    parser.add_argument(
        "--gui",
        action="store_true",
        help="Запустить графический интерфейс"
    )

    args = parser.parse_args()

    if args.gui:
        if args.filepath is not None:
            parser.error(
                "При запуске GUI путь к файлу указывать не нужно"
            )

        from mini_fastqc.fastq_gui import main as run_gui
        run_gui()

    else:
        if args.filepath is None:
            parser.error(
                "Для консольного анализа укажите путь к FASTQ-файлу"
            )

        try:
            demo_fastq(args.filepath)

        except FileNotFoundError as error:
            print(f"Файл не найден: {error}")
        except PermissionError as error:
            print(f"Нет доступа к файлу: {error}")
        except ValueError as error:
            print(f"Ошибка данных: {error}")


def demo_fastq(filepath: Path) -> None:
    """
    Демонстрирует чтение и анализ последовательностей из FASTQ-файла.

    Parameters
    ----------
    filepath : Path
        Путь к FASTQ-файлу.

    Returns
    -------
    None
        Функция выводит информацию о последовательностях,
        их количество, среднюю длину и строит графики.
    """
    fastq_reader: FastqReader = FastqReader(filepath)

    print("\nПервые 10 прочтений:")
    for record in islice(fastq_reader, 10):
        print(f"Идентификатор: {record.seq_id}")
        print(f"Последовательность: {record.seq}")
        print(f"Длина: {len(record)}")
        print(f"Качество: {record.quality}")
        print()

    print(f"Количество последовательностей: {fastq_reader.count_sequences()}")
    print(f"Средняя длина последовательностей: {fastq_reader.average_length()}")

    print("Построение графика качества по позициям...")
    fastq_reader.plot_per_base_quality()

    print("Построение графика нуклеотидного состава...")
    fastq_reader.plot_per_base_content()

    print("Построение распределения длин последовательностей...")
    fastq_reader.plot_length_distribution()


if __name__ == "__main__":
    main()
