import math

import pandas as pd

from etl import config
from etl.extract import extraer_todas_las_fuentes
from etl.run_pipeline import main
from etl.transform import (
    convertir_fecha,
    convertir_numero,
    normalizar_comuna,
    normalizar_region,
    preparar_clima,
    preparar_mediciones,
    transformar_fuentes,
    unir_mediciones_con_clima,
)


def test_normalizar_region_bio_bio():
    assert normalizar_region("Bio Bio") == "Biobío"


def test_normalizar_region_nuble():
    assert normalizar_region("Nuble") == "Ñuble"


def test_normalizar_comuna_chillan():
    assert normalizar_comuna(" Chillan ") == "Chillán"


def test_normalizar_comuna_concepcion():
    assert normalizar_comuna("Concepcion") == "Concepción"


def test_convertir_numero_coma_decimal():
    assert convertir_numero("45,2") == 45.2


def test_convertir_numero_ausente_devuelve_nan():
    assert math.isnan(convertir_numero("ausente"))


def test_convertir_fecha_formato_mixto_no_devuelve_nat():
    resultado = convertir_fecha("03/06/2026 12:00")

    assert not pd.isna(resultado)


def test_preparar_mediciones_agrega_fuente_dato():
    fuentes = extraer_todas_las_fuentes()

    df = preparar_mediciones(fuentes["mediciones_oficiales"], fuente="oficial")

    assert "fuente_dato" in df.columns
    assert set(df["fuente_dato"]) == {"oficial"}


def test_preparar_clima_convierte_columnas_numericas():
    fuentes = extraer_todas_las_fuentes()

    df = preparar_clima(fuentes["clima_historico"])

    for columna in (
        "velocidad_viento",
        "direccion_viento_grados",
        "temperatura",
        "humedad",
    ):
        assert pd.api.types.is_float_dtype(df[columna])


def test_transformar_fuentes_devuelve_tres_claves():
    fuentes = extraer_todas_las_fuentes()

    transformadas = transformar_fuentes(fuentes)

    assert set(transformadas) == {
        "mediciones_limpias",
        "industrias_limpias",
        "clima_limpio",
    }


def test_unir_mediciones_con_clima_conserva_cantidad_de_mediciones():
    fuentes = extraer_todas_las_fuentes()
    mediciones = pd.concat(
        [
            preparar_mediciones(fuentes["mediciones_oficiales"], fuente="oficial"),
            preparar_mediciones(fuentes["sensores_comunitarios"], fuente="comunitaria"),
        ],
        ignore_index=True,
    )
    clima = preparar_clima(fuentes["clima_historico"])

    resultado = unir_mediciones_con_clima(mediciones, clima)

    assert len(resultado) == len(mediciones)


def test_run_pipeline_genera_los_tres_csv_procesados():
    main()

    assert config.SALIDA_MEDICIONES_LIMPIAS.exists()
    assert config.SALIDA_INDUSTRIAS_LIMPIAS.exists()
    assert config.SALIDA_CLIMA_LIMPIO.exists()
