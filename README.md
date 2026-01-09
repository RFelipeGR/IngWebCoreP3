# 🚌 Proyecto SmartBus – Ing. Web Project

![Django](https://img.shields.io/badge/Django-5.2.x-092E20?style=flat&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat&logo=python)
![Render](https://img.shields.io/badge/Deployed%20on-Render-46E3B7?style=flat&logo=render)

## Gestión de ocupación y transferencias atómicas de pasajeros
Este proyecto implementa un sistema en Django para la administración de buses interprovinciales, gestionando:
- Horarios de salida
- Reserva de pasajeros
- Ocupación de buses
- Transferencia atómica de pasajeros entre buses
- Panel de administración para operadores

La lógica principal del proyecto gira en torno a optimizar la ocupación de buses, permitiendo mover pasajeros desde rutas con baja ocupación hacia otras más rentables, manteniendo **consistencia y seguridad transaccional**.

En la etapa final del proyecto se incorporaron **principios SOLID** y **patrones de diseño**, con el objetivo de mejorar la mantenibilidad, extensibilidad y organización del código, sin alterar el funcionamiento principal del sistema.

> **⚠️ Nota importante:**  
Este repositorio documenta una versión funcional y evaluable del sistema. A lo largo del desarrollo se aplicaron mejoras progresivas, aunque aún existen oportunidades de refactorización.

---

## 🌐 Proyecto deployado en Render

🔗 https://ingwebcore.onrender.com

Funcionalidades disponibles en producción:
- Dashboard para operadores
- Gestión de horarios y buses
- Reservas con asignación de asientos
- Transferencias atómicas
- Logs de transferencias
- Panel de administración de Django

> **Nota:** Render puede tardar unos segundos en iniciar por *cold start*.

---

## 🏗️ Arquitectura general del proyecto

- smartbus/ → Configuración global (settings, urls, wsgi)
- core/ → Lógica de transferencias y servicios
- administracion/ → Gestión de operadores, buses y horarios
- reservas/ → Reservas de asientos y ocupación


### 1️⃣ core/
Contiene la lógica crítica del sistema:
- Transferencias atómicas
- Validaciones de negocio
- Cálculo de ocupación
- Registro de transferencias (**TransferLog**)

### 2️⃣ administracion/
Gestión operativa:
- Modelos: Bus, Operador, Ruta, Horario
- Formularios
- Vistas administrativas
- Scripts de carga inicial

### 3️⃣ reservas/
Gestión de pasajeros:
- Modelo Reserva
- Validación de asientos
- Cálculo de ocupación
- Generación de datos de prueba

---

## 🔄 Flujo principal de transferencia de pasajeros

1. Selección de reservas del bus origen.
2. Selección del horario destino.
3. Validaciones:
   - El bus destino no ha salido
   - Capacidad disponible suficiente
   - Reservas válidas
4. Asignación de nuevos asientos.
5. Persistencia en base de datos.
6. Registro en TransferLog.

Todo el proceso se ejecuta dentro de una transacción atómica.

---

## 🧠 Principios SOLID aplicados

### ✅ Single Responsibility Principle (SRP)
- Las vistas manejan únicamente solicitudes HTTP.
- La lógica de negocio se concentra en servicios.
- Los modelos representan solo datos.

Cada componente tiene una responsabilidad clara y única.

### ✅ Dependency Inversion Principle (DIP)
- Las vistas dependen de funciones de servicio y no de implementaciones directas.
- La lógica de negocio puede modificarse sin afectar las vistas.

Esto reduce el acoplamiento y mejora la extensibilidad.

---

## 🧩 Patrones de diseño implementados

### 🏭 Service Layer Pattern
La lógica de negocio se encapsula en una capa de servicios (`core/services.py`):
- Transferencias
- Validaciones
- Cálculos

Evita lógica compleja dentro de las vistas.

### 📦 Repository-like Pattern
El acceso a datos se realiza a través de servicios que encapsulan:
- Consultas
- Validaciones
- Operaciones complejas

Esto desacopla la lógica de negocio del ORM.

---

## 🧪 Scripts incluidos en el repositorio
- core/seed_real.py
- Scripts de creación de operadores
- Scripts de generación de horarios

---

## ⚙️ Instalación y ejecución

### Requisitos
- Python 3.10+
- pip
- Entorno virtual recomendado

### Clonar repositorio
```bash
git clone https://github.com/RFelipeGR/IngWebCore.git
cd IngWebCore
```

### Entorno virtual
```bash
python -m venv env
source env/bin/activate
```
---

### Dependencias
```bash
pip install -r requirements.txt
```
---

### Migraciones
```bash
python manage.py makemigrations
python manage.py migrate
```
---

### Ejecutar servidor
```bash
python manage.py runserver
```
---

## 🚨 Limitaciones y mejoras futuras

-Código duplicado en algunas áreas

-Scripts que pueden convertirse en management commands

-Tests limitados

-Validaciones de concurrencia por mejorar

---

## 🎯 Estado actual del sistema

-Sistema funcional

-Transferencias atómicas con logs

-Aplicación de SOLID

-Uso de patrones de diseño

-Base sólida para futuras mejoras

---

## 👤 Autores

**Víctor A. Suquilanda** | **Roberto F. Guaña**

📧 Carrera de Ingeniería de Software

📅 Año: 2026

---