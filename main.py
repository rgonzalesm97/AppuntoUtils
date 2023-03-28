from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from datetime import date
import pandas as pd
from datetime import timedelta
import locale
from fastapi.responses import StreamingResponse


locale.setlocale(locale.LC_ALL, 'es_ES')

class RequestDateAvailabilityDto(BaseModel):
    partner_id: int
    fecha_inicio: date
    fecha_fin: date
    lunes: Optional[str]
    martes: Optional[str]
    miercoles: Optional[str]
    jueves: Optional[str]
    viernes: Optional[str]
    sabado: Optional[str]
    domingo: Optional[str]

app = FastAPI()

days_list = {
    'lunes': 'Lunes',
    'martes': 'Martes',
    'miercoles': 'Miércoles',
    'jueves': 'Jueves',
    'viernes': 'Viernes',
    'sabado': 'Sábado',
    'domingo': 'Domingo'
}

def rango_horas(texto):
    rangos = texto.split(',') # Dividimos el texto en los distintos rangos de horas
    horas = []
    for rango in rangos:
        inicio, fin = map(int, rango.split('-')) # Obtenemos el inicio y el fin del rango
        horas += list(range(inicio, fin+1)) # Agregamos las horas del rango al arreglo
    return horas


def generate_list(requestAvailability: RequestDateAvailabilityDto):
    fecha_inicial = requestAvailability.fecha_inicio
    fecha_final = requestAvailability.fecha_fin
    horas_disponibles_por_dia = {}

    for day_dto in days_list.keys():
        if getattr(requestAvailability, day_dto) != '':
            day = days_list[day_dto]
            horas_disponibles_por_dia[day] = rango_horas(getattr(requestAvailability, day_dto))

    fechas = []
    horas = []
    
    fecha_actual = fecha_inicial
    while fecha_actual <= fecha_final:
        # Verificamos si el día actual está en los días disponibles
        dia_actual = fecha_actual.strftime("%A").capitalize()
        if dia_actual in horas_disponibles_por_dia.keys():
            # Agregamos las horas disponibles para el día actual
            for hora in horas_disponibles_por_dia[dia_actual]:
                fechas.append(fecha_actual)
                horas.append(hora)
        # Avanzamos al siguiente día
        fecha_actual += timedelta(days=1)

    disponibilidad = {
        'id_user':[requestAvailability.partner_id]*len(fechas),
        'id_type_availability':[2]*len(fechas),
        'date_availability': fechas,
        'hour_availability': horas,
        'enable':[1]*len(fechas),
        'status':[1]*len(fechas)
    }

    df = pd.DataFrame(disponibilidad)

    return df.to_csv(index=False)

@app.post("/disponibilidad")
def index(requestAvailability: RequestDateAvailabilityDto):
    csv_list = generate_list(requestAvailability)
    return StreamingResponse(
        iter([csv_list]), 
        media_type="text/csv", 
        headers={"Content-Disposition": "attachment; filename=disponibilidad.csv"})