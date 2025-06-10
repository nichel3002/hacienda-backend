from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List
from jose import jwt, JWTError

app = FastAPI()

# Configurar CORS para permitir peticiones desde tu frontend Angular
origins = [
    "https://hacienda-crud.vercel.app"  # Cambia a la URL donde está tu frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # aquí el frontend autorizado
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Usuarios hardcodeados para demo
fake_users_db = {
    "admin": {"username": "admin", "password": "admin123", "role": "admin"},
    "user": {"username": "user", "password": "user123", "role": "user"},
}

SECRET_KEY = "secretkey123"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str
    role: str

def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if not user or user["password"] != password:
        return None
    return user

def create_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos")
    token = create_token({"sub": user["username"], "role": user["role"]})
    return {"access_token": token, "token_type": "bearer"}

async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token inválido")
    username = payload.get("sub")
    role = payload.get("role")
    return User(username=username, role=role)

# Modelo de transacción
class Transaccion(BaseModel):
    id: int = None
    fecha: str
    tipo: str  # ingreso o gasto
    descripcion: str
    categoria: str
    monto: float
    owner: str = None

# Almacenamos transacciones en memoria (lista)
transacciones = []
contador_id = 1

@app.get("/api/transacciones", response_model=List[Transaccion])
def get_transacciones(current_user: User = Depends(get_current_user)):
    if current_user.role == "admin":
        return transacciones
    return [t for t in transacciones if t.owner == current_user.username]

@app.post("/api/transacciones")
def add_transaccion(t: Transaccion, current_user: User = Depends(get_current_user)):
    global contador_id
    t.id = contador_id
    contador_id += 1
    t.owner = current_user.username
    transacciones.append(t)
    return {"message": "Transacción agregada", "id": t.id}

@app.delete("/api/transacciones/{trans_id}")
def delete_transaccion(trans_id: int, current_user: User = Depends(get_current_user)):
    global transacciones
    t = next((x for x in transacciones if x.id == trans_id), None)
    if not t:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    if current_user.role != "admin" and t.owner != current_user.username:
        raise HTTPException(status_code=403, detail="No autorizado")
    transacciones = [x for x in transacciones if x.id != trans_id]
    return {"message": "Transacción eliminada"}
