import json
import random
from dataclasses import asdict
from pathlib import Path

from faker import Faker

from patient import Patient


DATA_FILE = Path(__file__).resolve().parent / "patients.json"

fake = Faker("ru_RU")
rng = random.Random()

def generate_patients(count: int = 500) -> list[Patient]:
    """
    Генерирует список пациентов с вымышленными данными.

    Создаёт объекты Patient со случайными значениями пола,
    возраста, роста и веса. ФИО генерируются с помощью
    библиотеки Faker с учётом пола пациента.

    Возраст выбирается в диапазоне от 18 до 85 лет,
    рост — в зависимости от пола. Вес рассчитывается
    на основе случайного значения ИМТ от 17 до 35 кг/м².

    Parameters
    ----------
    count: int, optional
        Количество генерируемых пациентов.
        По умолчанию 500.

    Returns
    -------
    list[Patient]
        Список объектов Patient с вымышленными данными.
    """
    patients = []

    for _ in range(count):
        sex = rng.choice(["М", "Ж"])

        if sex == "М":
            full_name = (
                f"{fake.last_name_male()} "
                f"{fake.first_name_male()} "
                f"{fake.middle_name_male()}"
            )
            height = round(rng.uniform(160, 195), 1)
        else:
            full_name = (
                f"{fake.last_name_female()} "
                f"{fake.first_name_female()} "
                f"{fake.middle_name_female()}"
            )
            height = round(rng.uniform(150, 185), 1)

        age = rng.randint(18, 85)

        bmi = rng.uniform(17, 35)
        weight = round(bmi * (height / 100) ** 2, 1)

        patient = Patient(
            full_name=full_name,
            age=age,
            sex=sex,
            height=height,
            weight=weight
        )

        patients.append(patient)

    return patients


if __name__ == "__main__":
    if DATA_FILE.exists():
        answer = input(
            "Файл patients.json уже существует. "
            "Перезаписать его? (да/нет): "
        ).strip().lower()

        if answer != "да":
            print("Генерация отменена.")
            raise SystemExit

    patients = generate_patients(500)
    data = [asdict(patient) for patient in patients]

    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    print(f"Создано пациентов: {len(patients)}")
    print(f"Файл: {DATA_FILE}")
