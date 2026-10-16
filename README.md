# SISMOC-CUMBE
### Sistema Integrado de Gestión Operativa, Asistencia y Conciliación
**Empresa de Transportes El Cumbe S.A.C.** (RUC: `20480397731`)  
Prácticas Pre Profesionales (1IS101) — Universidad Señor de Sipán (2026-II)

---

## 🚀 Tecnologías
- **Backend:** Python 3.12, Django 5.1/6.1, Django Ninja (FastAPI-like REST API), Pandas (Procesamiento de archivos ZKTeco y Excel).
- **Base de Datos:** SQLite (Desarrollo) / PostgreSQL 15 (Docker / Producción).
- **Seguridad:** JWT Bearer Token, Control de Acceso Basado en Roles (RBAC - 7 Roles).
- **Contenerización:** Docker & Docker Compose.

---

## 👥 Matriz de 7 Roles RBAC
1. 👑 **Gerente General** (`GERENTE_GENERAL`)
2. ⚙️ **Administrador del Sistema** (`ADMINISTRADOR`)
3. 📊 **Contadora General** (`CONTADORA`)
4. 🚌 **Conductor / Chofer** (`CONDUCTOR`)
5. 📱 **Operador en Bus / Embarcador** (`OPERADOR_EMBARQUE`)
6. 🎟️ **Vendedor / Boletería** (`BOLETERIA`)
7. 👔 **Empleado / Personal Administrativo** (`ADMINISTRATIVO`)

---

## ⚙️ Despliegue con Docker
```bash
docker-compose up --build
```

## 💻 Ejecución Local
```bash
# Crear entorno e instalar dependencias
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Migrar y poblar datos iniciales
python manage.py migrate
python manage.py seed_sismoc

# Iniciar servidor
python manage.py runserver 8000
```

- **Dashboard:** http://localhost:8000/
- **Swagger Docs:** http://localhost:8000/api/docs
- **Django Admin:** http://localhost:8000/admin/
