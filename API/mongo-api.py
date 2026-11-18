"""
Taller 3 – Integración APEX + MongoDB (ISIS1511)
API REST (FastAPI) que actúa como intermediario entre APEX y MongoDB.

Variables de entorno (Render → Environment):
  MONGO_URI   mongodb://<usuario>:<contraseña>@157.253.236.88:8087
  MONGO_DB    nombre de su base de datos (ISIS*******)

Ejecutar local:
  export MONGO_URI="mongodb://usuario:clave@157.253.236.88:8087"
  export MONGO_DB="ISIS1511xxxx"
  uvicorn mongo-api:app --reload        (o: uvicorn main:app si renombra el archivo)

Start command en Render:
  uvicorn mongo-api:app --host 0.0.0.0 --port $PORT
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from datetime import datetime
import os

app = FastAPI(title="DrinkAdvisor NoSQL API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Conexión al servidor Admonsis (credenciales por variable de entorno, nunca en GitHub)
client = MongoClient(os.environ["MONGO_URI"])
db = client[os.environ["MONGO_DB"]]

# Nombres de colecciones (el enunciado usa comentarios_bares en los puntos 3-4)
COL_COMENTARIOS = os.environ.get("COL_COMENTARIOS", "comentarios_bares")
COL_EVENTOS = os.environ.get("COL_EVENTOS", "eventos")


def limpiar(datos: dict) -> dict:
    """Quita campos vacíos para que el documento solo tenga lo que el usuario llenó."""
    return {k: v for k, v in datos.items() if v not in (None, "", [], {})}


@app.get("/")
def inicio():
    return {"estado": "API funcionando correctamente"}


# ---------------------------------------------------------------- Punto 3
@app.get('/bares/{bar_id}/comentarios')
def get_comentarios(bar_id: int):
    comentarios = list(db[COL_COMENTARIOS].find(
        {"bar_id": bar_id},          # filtro: comentarios de este bar
        {"_id": 0}                   # proyección: ObjectId no es serializable a JSON
    ).sort("fecha", -1))             # más recientes primero
    return comentarios


# ---------------------------------------------------------------- Punto 4
@app.post('/bares/{bar_id}/comentarios')
def post_comentario(bar_id: int, datos: dict):
    datos = limpiar(datos)
    if not str(datos.get("texto", "")).strip():
        raise HTTPException(status_code=400, detail="El campo texto es obligatorio")
    if "calificacion" in datos:
        try:
            datos["calificacion"] = int(datos["calificacion"])
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="calificacion debe ser un entero")
        if not 1 <= datos["calificacion"] <= 5:
            raise HTTPException(status_code=400, detail="calificacion debe estar entre 1 y 5")
    datos['bar_id'] = bar_id
    datos['fecha'] = datetime.now().isoformat()
    db[COL_COMENTARIOS].insert_one(datos)
    return {'mensaje': 'Comentario guardado'}


# ---------------------------------------------------------------- Punto 5
@app.get('/bares/{bar_id}/eventos')
def get_eventos(bar_id: int):
    eventos = list(db[COL_EVENTOS].find(
        {"bar_id": bar_id},
        {"_id": 0}
    ).sort("fecha_creacion", -1))
    return eventos


# ---------------------------------------------------------------- Punto 6
@app.post('/bares/{bar_id}/eventos')
def post_evento(bar_id: int, datos: dict):
    datos = limpiar(datos)           # solo los campos que el usuario completó
    if not str(datos.get("nombre", "")).strip():
        raise HTTPException(status_code=400, detail="El campo nombre es obligatorio")
    datos['bar_id'] = bar_id
    datos['fecha_creacion'] = datetime.now().isoformat()
    db[COL_EVENTOS].insert_one(datos)
    return {'mensaje': 'Evento registrado'}
