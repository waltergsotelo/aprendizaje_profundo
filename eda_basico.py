"""EDA básico y preparación de ``dataset_compras.csv``.

No requiere librerías externas. Ejecutar desde la carpeta del proyecto:
    python3 eda_basico.py
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median


INPUT_FILE = Path("dataset_compras.csv")
OUTPUT_FILE = Path("dataset_compras_procesado.csv")
REPORT_FILE = Path("reporte_eda.txt")

# El orden natural de los rangos es preferible a un label encoding arbitrario.
AGE_ENCODER = {
    "0-17": 0,
    "18-25": 1,
    "26-35": 2,
    "36-45": 3,
    "46-50": 4,
    "51-55": 5,
    "55+": 6,
}


def top_counts(counter: Counter[str], n: int = 10) -> list[str]:
    """Devuelve las categorías más frecuentes para el informe."""
    return [f"  - {value}: {count:,}" for value, count in counter.most_common(n)]


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"No se encontró el archivo de entrada: {INPUT_FILE}")

    age_counts: Counter[str] = Counter()
    stay_counts: Counter[str] = Counter()
    city_counts: Counter[str] = Counter()
    null_subcategory_2 = 0
    purchases: list[float] = []
    purchases_by_gender: defaultdict[str, list[float]] = defaultdict(list)
    rows = 0

    with INPUT_FILE.open("r", encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        required = {
            "Age",
            "Stay_In_Current_City_Years",
            "Product_Subcategory_2",
            "Purchase",
        }
        missing_columns = required - set(reader.fieldnames or [])
        if missing_columns:
            raise ValueError(f"Faltan columnas requeridas: {sorted(missing_columns)}")

        fieldnames = list(reader.fieldnames or []) + [
            "Age_Encoded",
            "Stay_In_Current_City_Years_Encoded",
        ]
        with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as destination:
            writer = csv.DictWriter(destination, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                age = row["Age"].strip()
                stay = row["Stay_In_Current_City_Years"].strip()

                if age not in AGE_ENCODER:
                    raise ValueError(f"Valor inesperado en Age: {age!r}")
                if stay not in {"0", "1", "2", "3", "4", "5+"}:
                    raise ValueError(
                        "Valor inesperado en Stay_In_Current_City_Years: "
                        f"{stay!r}"
                    )

                # Un nulo representa que ese producto no tiene segunda
                # subcategoría. El 0 se reserva como categoría "sin dato".
                if not row["Product_Subcategory_2"].strip():
                    row["Product_Subcategory_2"] = "0"
                    null_subcategory_2 += 1

                row["Age_Encoded"] = str(AGE_ENCODER[age])
                # Convierte "5+" a 5 y mantiene el resto como años enteros.
                row["Stay_In_Current_City_Years_Encoded"] = str(
                    5 if stay == "5+" else int(stay)
                )
                writer.writerow(row)

                purchase = float(row["Purchase"])
                purchases.append(purchase)
                purchases_by_gender[row["Gender"]].append(purchase)
                age_counts[age] += 1
                stay_counts[stay] += 1
                city_counts[row["City_Category"]] += 1
                rows += 1

    report = [
        "EDA BÁSICO - DATASET DE COMPRAS",
        "=" * 34,
        f"Observaciones: {rows:,}",
        f"Columnas originales: {len(fieldnames) - 2}",
        f"Nulos originales en Product_Subcategory_2: {null_subcategory_2:,} "
        f"({null_subcategory_2 / rows:.2%})",
        "",
        "Purchase",
        f"  - mínimo: {min(purchases):,.2f}",
        f"  - máximo: {max(purchases):,.2f}",
        f"  - promedio: {mean(purchases):,.2f}",
        f"  - mediana: {median(purchases):,.2f}",
        "",
        "Distribución de Age",
        *top_counts(age_counts),
        "",
        "Distribución de Stay_In_Current_City_Years",
        *top_counts(stay_counts),
        "",
        "Distribución de City_Category",
        *top_counts(city_counts),
        "",
        "Compra promedio por Gender",
        *[
            f"  - {gender}: {mean(values):,.2f} ({len(values):,} observaciones)"
            for gender, values in sorted(purchases_by_gender.items())
        ],
        "",
        "Transformaciones aplicadas",
        "  - Age_Encoded: codificación ordinal de 0-17=0 hasta 55+=6.",
        "  - Stay_In_Current_City_Years_Encoded: años como entero; 5+=5.",
        "  - Product_Subcategory_2: nulos reemplazados por 0 (sin subcategoría).",
    ]
    REPORT_FILE.write_text("\n".join(report) + "\n", encoding="utf-8")

    print(f"Reporte creado: {REPORT_FILE}")
    print(f"Dataset procesado creado: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
