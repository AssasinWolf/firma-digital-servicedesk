# Firma Digital ServiceDesk

Este proyecto permite integrar una solución de firma digital de documentos PDF en flujos de solicitudes de ServiceDesk u otros sistemas similares, a través de un visor HTML y un backend FastAPI.

## ✨ Características

- Visualización de datos de la solicitud
- Firma desde canvas y generación de PDF embebido
- Envío automático del PDF al backend y almacenamiento
- Asociación del documento firmado a una solicitud mediante API
- Funcionalidades adicionales de descarga y eliminación de PDF

## 📦 Estructura del proyecto

```
backend/
│   └── firma_v1.0_limpio.py
frontend/
│   ├── firma_V1.0_limpio.html
│   └── visor_pdf_v1.0_limpio.html
README.md
.gitignore
```

## 🚀 Tecnologías utilizadas

- **Backend**: Python + FastAPI
- **Frontend**: HTML5, JavaScript, jsPDF, Canvas
- **Comunicación**: API RESTful + tokens temporales
- **Autenticación**: Token de acceso para interacción con la API externa

## ⚙️ Requisitos

- Python 3.8+
- FastAPI
- Ruta de almacenamiento para PDFs (editable en el backend)

## 🔒 Seguridad

- Token temporal con expiración para acciones sobre PDFs
- Validación del nombre de archivo
- Separación backend/frontend

## 📄 Licencia

Código disponible para uso educativo y demostrativo.
