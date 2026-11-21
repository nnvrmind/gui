from dataclasses import dataclass


@dataclass
class Patient:
    """Представляет информацию об одном пациенте."""

    full_name: str
    age: int
    sex: str
    height: float
    weight: float

    @property
    def bmi(self) -> float:
        """Вычисляет индекс массы тела пациента."""
        return self.weight / (self.height / 100) ** 2