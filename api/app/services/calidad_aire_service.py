def clasificar_calidad_aire_mp25(mp25: float) -> dict[str, str]:
    """Clasificacion simplificada de calidad del aire basada en MP2.5."""
    if mp25 < 0:
        raise ValueError("No se pueden clasificar valores negativos de MP2.5")

    if mp25 < 50:
        return {
            "categoria": "Buena",
            "mensaje_ciudadano": "Calidad del aire favorable para actividades al aire libre.",
            "color_referencial": "verde",
        }
    if mp25 < 80:
        return {
            "categoria": "Regular",
            "mensaje_ciudadano": "Personas sensibles deberian reducir exposicion prolongada.",
            "color_referencial": "amarillo",
        }
    if mp25 < 110:
        return {
            "categoria": "Alerta",
            "mensaje_ciudadano": "Evitar actividad fisica intensa al aire libre.",
            "color_referencial": "naranjo",
        }
    if mp25 < 170:
        return {
            "categoria": "Preemergencia",
            "mensaje_ciudadano": "Reducir actividades al aire libre y priorizar grupos de riesgo.",
            "color_referencial": "rojo",
        }
    return {
        "categoria": "Emergencia",
        "mensaje_ciudadano": "Permanecer en interiores y evitar exposicion al aire libre.",
        "color_referencial": "morado",
    }
