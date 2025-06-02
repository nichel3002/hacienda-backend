from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Almacenamiento temporal en memoria
transacciones = []
contador_id = 1

class Transaccion(BaseModel):
    id: int | None = None
    fecha: str
    tipo: str  # 'ingreso' o 'gasto'
    descripcion: str
    categoria: str
    monto: float

@app.get("/api/transacciones", response_model=List[Transaccion])
def get_transacciones():
    return transacciones

@app.post("/api/transacciones")
def add_transaccion(t: Transaccion):
    global contador_id
    t.id = contador_id
    contador_id += 1
    transacciones.append(t)
    return {"message": "Transacción agregada", "id": t.id}

@app.delete("/api/transacciones/{trans_id}")
def delete_transaccion(trans_id: int):
    global transacciones
    transacciones = [t for t in transacciones if t.id != trans_id]
    return {"message": "Transacción eliminada"}