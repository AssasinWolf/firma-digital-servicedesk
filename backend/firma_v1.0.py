
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
import os
import requests
import json
import time
from uuid import uuid4
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()
AUTH_TOKEN = os.getenv("AUTH_TOKEN")  # Reemplaza con tu token en .env

SAVE_DIR = "./pdf"
os.makedirs(SAVE_DIR, exist_ok=True)
SDP_URL = "https://example.com"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


import logging
from datetime import datetime

# Configuración de logging
LOG_FILE = "./logs/firma_digital.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def log_event(action, request_id="", filename="", token="", ip=""):
    logging.info(f"[{action}] request_id={request_id} filename={filename} token={token} ip={ip}")


# Almacenamiento temporal de tokens: {token: {"request_id": str, "filename": str, "expires": timestamp}}
token_store = {}

class PDFRequest(BaseModel):
    action: str
    request_id: str
    pdf_base64: str
    pdf_filename: str

class PDFActionRequest(BaseModel):
    request_id: str
    pdf_filename: str
    access_token: str

@app.post("/token/generar")
async def generar_token(request: Request):
    data = await request.json()
    request_id = data.get("request_id")
    filename = data.get("pdf_filename")

    if not request_id or not filename:
        return {"status": "error", "message": "Parámetros faltantes"}

    token = str(uuid4())
    token_store[token] = {
        "request_id": request_id,
        "filename": filename,
        "expires": time.time() + 120  # 2 minutos de validez
    }
    log_event("TOKEN_GENERADO", request_id, filename, token)
    return {"status": "success", "access_token": token}

@app.post("/firmar")
async def firmar_pdf(payload: PDFRequest):
    try:
        if not payload.pdf_filename.endswith('.pdf') or '/' in payload.pdf_filename or '..' in payload.pdf_filename:
            return {"status": "error", "message": "Nombre de archivo inválido"}

        pdf_data = base64.b64decode(payload.pdf_base64)
        save_path = os.path.join(SAVE_DIR, payload.pdf_filename)
        with open(save_path, "wb") as f:
            f.write(pdf_data)

        update_url = f"{SDP_URL}/api/v3/requests/{payload.request_id}"
        input_data = {
            "request": {
                "description": f"Se adjunta el documento firmado: <a href='https://example.com/pdf/{payload.pdf_filename}' onclick=\"window.open(this.href, 'visor_pdf', 'width=800,height=600'); return false;\">{payload.pdf_filename}</a>"
            }
        }
        response = requests.put(
            update_url,
            data={"input_data": json.dumps(input_data)},
            headers={"authtoken": AUTH_TOKEN}
        )

        if not response.ok:
            return {"status": "error", "message": f"Error al actualizar descripción: {response.status_code} - {response.text}"}

        return {
            "status": "success",
            "message": "PDF guardado y nombre actualizado.",
            "filename": payload.pdf_filename
        }

    except Exception as e:
        return {"status": "error", "message": f"Error inesperado: {str(e)}"}

@app.post("/pdf/descargar")
async def descargar_pdf(request: Request):
    data = await request.json()
    filename = data.get("pdf_filename")
    token = data.get("access_token")

    if not validar_token(token, filename):
        return {"status": "error", "message": "Token inválido o expirado"}

    filepath = os.path.join(SAVE_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, "rb") as f:
            log_event("DESCARGA", filename, filename, token, request.client.host)
            return {"status": "success", "pdf_base64": base64.b64encode(f.read()).decode()}
    return {"status": "error", "message": "Archivo no encontrado"}

@app.post("/pdf/eliminar")
async def eliminar_pdf(payload: PDFActionRequest):
    if not validar_token(payload.access_token, payload.pdf_filename):
        return {"status": "error", "message": "Token inválido o expirado"}

    try:
        file_path = os.path.join(SAVE_DIR, payload.pdf_filename)
        if os.path.exists(file_path):
            os.remove(file_path)

        update_url = f"{SDP_URL}/api/v3/requests/{payload.request_id}"
        input_data = {
            "request": {
                "description": ""
            }
        }
        response = requests.put(
            update_url,
            data={"input_data": json.dumps(input_data)},
            headers={"authtoken": AUTH_TOKEN}
        )

        if not response.ok:
            return {"status": "error", "message": f"Error al limpiar descripción: {response.status_code} - {response.text}"}

        log_event("ELIMINACION", payload.request_id, payload.pdf_filename, payload.access_token)
        return {"status": "success", "message": "PDF eliminado correctamente"}

    except Exception as e:
        return {"status": "error", "message": f"Error al eliminar PDF: {str(e)}"}

def validar_token(token: str, filename: str) -> bool:
    token_info = token_store.get(token)
    if not token_info:
        return False
    if token_info["filename"] != filename:
        return False
    if token_info["expires"] < time.time():
        del token_store[token]
        return False
    return True
