from dataclasses import dataclass


@dataclass
class Patient:
    """
    Представляет данные пациента.

    Хранит ФИО, возраст, пол, рост и вес пациента.
    Предоставляет вычисляемое свойство bmi для определения
    индекса массы тела на основе роста и веса.

    Attributes
    ----------
    full_name: str
        Фамилия, имя и отчество пациента.
    age: int
        Возраст пациента в годах.
    sex: str
        Пол пациента: "М" или "Ж".
    height: float
        Рост пациента в сантиметрах.
    weight: float
        Вес пациента в килограммах.
    """
    full_name: str
    age: int
    sex: str
    height: float
    weight: float

    @property
    def bmi(self) -> float:
        """
        Вычисляет индекс массы тела (ИМТ) пациента.

        Рассчитывает ИМТ как отношение массы тела в килограммах
        к квадрату роста в метрах.

        Returns
        -------
        float
            Индекс массы тела пациента в кг/м².
        """
        return self.weight / (self.height / 100) ** 2