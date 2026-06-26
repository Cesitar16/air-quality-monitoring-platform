from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import requests


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
ENDPOINT = f"{API_BASE_URL}/analytics/dataset-modelado"

RAW_PATH = Path("data/raw/dataset_modelado.json")
PROCESSED_PATH = Path("data/processed/dataset_modelado.csv")


def fetch_dataset(limit: int = 1000) -> list[dict]:
    """Descarga el dataset completo usando paginación por limit/offset."""
    all_rows: list[dict] = []
    offset = 0

    while True:
        params = {
            "limit": limit,
            "offset": offset,
        }

        response = requests.get(ENDPOINT, params=params, timeout=30)
        response.raise_for_status()

        rows = response.json()

        if not rows:
            break

        all_rows.extend(rows)
        print(f"Descargadas {len(all_rows)} filas...")

        if len(rows) < limit:
            break

        offset += limit

    return all_rows


def build_dataframe(rows: list[dict]) -> pd.DataFrame:
    """Convierte la respuesta JSON en un DataFrame limpio para análisis."""
    df = pd.DataFrame(rows)

    if df.empty:
        return df

    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"])

    df = df.drop_duplicates(
        subset=["fecha_hora", "codigo_estacion"],
        keep="first",
    )

    df = df.sort_values(["fecha_hora", "region", "comuna", "codigo_estacion"])

    return df


def save_outputs(rows: list[dict], df: pd.DataFrame) -> None:
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)

    with RAW_PATH.open("w", encoding="utf-8") as file:
        json.dump(rows, file, ensure_ascii=False, indent=2)

    df.to_csv(PROCESSED_PATH, index=False, encoding="utf-8")


def print_summary(df: pd.DataFrame) -> None:
    print("\nResumen del dataset")
    print("-------------------")
    print(f"Filas: {df.shape[0]}")
    print(f"Columnas: {df.shape[1]}")

    if df.empty:
        print("El dataset está vacío.")
        return

    print("\nColumnas:")
    for column in df.columns:
        print(f"- {column}")

    print("\nValores nulos por columna:")
    print(df.isna().sum().sort_values(ascending=False))

    print("\nCategorías ICA:")
    print(df["categoria_ica"].value_counts())

    print("\nRango de fechas:")
    print(f"Desde: {df['fecha_hora'].min()}")
    print(f"Hasta: {df['fecha_hora'].max()}")

    print("\nArchivos generados:")
    print(f"- {RAW_PATH}")
    print(f"- {PROCESSED_PATH}")


def main() -> None:
    rows = fetch_dataset()
    df = build_dataframe(rows)
    save_outputs(rows, df)
    print_summary(df)


if __name__ == "__main__":
    main()
