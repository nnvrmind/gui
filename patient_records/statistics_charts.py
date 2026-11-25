from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
import random


def plot_sex_distribution(ax, patients) -> None:
    """
    Строит столбчатую диаграмму распределения пациентов по полу.

    Подсчитывает количество мужчин и женщин в списке пациентов
    и отображает результаты на переданной области графика.
    Добавляет подписи значений над столбцами и настраивает
    вертикальную ось для отображения целых чисел.

    Parameters
    ----------
    ax: matplotlib.axes.Axes
        Область графика, на которой строится диаграмма.
    patients: list[Patient]
        Список объектов пациентов, содержащих информацию о поле.
    """
    male_count = sum(p.sex == "М" for p in patients)
    female_count = sum(p.sex == "Ж" for p in patients)

    counts = [male_count, female_count]

    # построение столбчатой диаграммы
    bars = ax.bar(
        ["Мужчины", "Женщины"],
        counts,
        color=["#78B7D0", "#E9A7C0"],
        width=0.4
    )

    ax.set_title("Распределение по полу")
    ax.set_ylabel("Количество пациентов")

    ax.set_ylim(0, max(counts) * 1.15 if max(counts) > 0 else 1)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    # добавление числовых значений над столбцами
    ax.bar_label(
        bars,
        padding=5,
        fontsize=11,
        fontweight="bold",
        color="#243746"
    )


def plot_age_distribution(ax, patients) -> None:
    """
    Строит гистограмму распределения пациентов по возрасту.

    Извлекает возраст каждого пациента и группирует значения
    по десятилетним интервалам. Настраивает подписи осей
    и целочисленные деления вертикальной оси.

    Parameters
    ----------
    ax: matplotlib.axes.Axes
        Область графика, на которой строится гистограмма.
    patients: list[Patient]
        Список объектов пациентов, содержащих информацию
        о возрасте.
    """
    ages = [p.age for p in patients]

    # построение гистограммы
    counts, _, _ = ax.hist(
        ages,
        bins=range(0, max(ages) + 20, 10),
        color="#78B7D0",
        edgecolor="white",
        rwidth=0.7
    )

    ax.set_title("Распределение по возрасту")
    ax.set_xlabel("Возраст, лет")
    ax.set_ylabel("Количество пациентов")

    ax.set_ylim(0, max(counts) + 1)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))


def plot_bmi_by_sex(ax, patients) -> None:
    """
    Строит диаграмму распределения ИМТ пациентов по полу.

    Отображает значения ИМТ отдельных пациентов в двух
    группах в зависимости от пола. Добавляет небольшое
    случайное смещение точек по горизонтали для уменьшения
    их наложения.

    Для воспроизводимости расположения точек использует
    генератор случайных чисел с фиксированным начальным
    значением.

    Parameters
    ----------
    ax: matplotlib.axes.Axes
        Область графика, на которой строится диаграмма.
    patients: list[Patient]
        Список объектов пациентов, содержащих информацию
        о поле и индексе массы тела.
    """
    rng = random.Random(42)

    for patient in patients:
        x = 0 if patient.sex == "М" else 1
        # добавление смещения точек для уменьшения наложения
        x += rng.uniform(-0.15, 0.15)

        color = "#78B7D0" if patient.sex == "М" else "#E9A7C0"

        ax.scatter(
            x,
            patient.bmi,
            color=color,
            s=15,
            alpha=0.5
        )

    ax.set_xticks([0, 1], ["Мужчины", "Женщины"])
    ax.set_xlim(-0.5, 1.5)
    ax.set_title("ИМТ по полу")
    ax.set_ylabel("ИМТ, кг/м²")


def plot_bmi_vs_age(ax, patients) -> None:
    """
    Строит диаграмму зависимости ИМТ пациентов от возраста.

    Извлекает значения возраста и индекса массы тела
    пациентов и отображает их в виде диаграммы рассеяния.
    Возраст откладывается по горизонтальной оси,
    а ИМТ — по вертикальной.

    Parameters
    ----------
    ax: matplotlib.axes.Axes
        Область графика, на которой строится диаграмма.
    patients: list[Patient]
        Список объектов пациентов, содержащих информацию
        о возрасте и индексе массы тела.
    """
    ages = [p.age for p in patients]
    bmi_values = [p.bmi for p in patients]

    ax.scatter(
        ages,
        bmi_values,
        color="#78B7D0",
        s=15,
        alpha=0.5
    )
    ax.set_title("ИМТ и возраст")
    ax.set_xlabel("Возраст, лет")
    ax.set_ylabel("ИМТ, кг/м²")


def style_axes(ax) -> None:
    """
    Применяет единое оформление к области графика.

    Устанавливает цвет фона, осей, подписей и делений.
    Убирает верхнюю и правую границы, настраивает
    размер и начертание заголовка, а также добавляет
    горизонтальную сетку под графическими элементами.

    Parameters
    ----------
    ax: matplotlib.axes.Axes
        Область графика, к которой применяется оформление.
    """
    title_color = "#243746"

    ax.set_facecolor("#F5FAFC")

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.spines["left"].set_color(title_color)
    ax.spines["bottom"].set_color(title_color)

    ax.tick_params(
        axis="both",
        colors=title_color,
        labelsize=10
    )

    ax.title.set_fontsize(13)
    ax.title.set_fontweight("bold")
    ax.title.set_color(title_color)

    ax.xaxis.label.set_fontsize(10)
    ax.yaxis.label.set_fontsize(10)

    ax.xaxis.label.set_color(title_color)
    ax.yaxis.label.set_color(title_color)

    ax.set_axisbelow(True)
    ax.grid(
        axis="y",
        color="#DCE8EE",
        linewidth=0.8
    )


def create_statistics_figure(patients) -> Figure:
    """
    Создаёт фигуру с четырьмя статистическими графиками.

    Формирует фигуру Matplotlib с расположением графиков
    в два ряда и два столбца. Строит распределения
    пациентов по полу и возрасту, распределение ИМТ
    по полу и зависимость ИМТ от возраста.

    Настраивает расположение графиков и применяет
    к каждой области единое оформление с помощью
    функции style_axes().

    Parameters
    ----------
    patients: list[Patient]
        Список объектов пациентов для построения статистики.

    Returns
    -------
    matplotlib.figure.Figure
        Фигура Matplotlib с четырьмя графиками.
    """

    fig = Figure(figsize=(10, 6.5), dpi=200)

    axes = fig.subplots(2, 2)

    plot_sex_distribution(axes[0, 0], patients)
    plot_age_distribution(axes[0, 1], patients)
    plot_bmi_by_sex(axes[1, 0], patients)
    plot_bmi_vs_age(axes[1, 1], patients)

    fig.tight_layout(pad=2.5)

    fig.patch.set_facecolor("#F5FAFC")

    for ax in axes.flat:
        style_axes(ax)

    return fig
