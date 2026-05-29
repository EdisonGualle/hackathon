# 🗂️ MODELO DE DATOS — FRAUDIA

Este documento define de forma estructurada las tablas, campos, tipos de datos y relaciones del modelo de datos del reto **Aseguradora del Sur**, utilizado por **FRAUDIA** para la detección y puntuación del riesgo de fraude.

---

## 1. Relaciones de la Base de Datos

El sistema ingesta un dataset estructurado en Excel compuesto por 5 hojas clave vinculadas de la siguiente manera:

```mermaid
erDiagram
    1_Siniestros }|--|| 2_Polizas : "ID Póliza"
    1_Siniestros }|--|| 3_Asegurados : "ID Asegurado"
    1_Siniestros }|--|| 4_Proveedores : "ID Proveedor"
    5_Documentos }|--|| 1_Siniestros : "ID Siniestro"
```

---

## 2. Definición de Hojas y Atributos

### 📋 Hoja 1: 1_Siniestros
Es la tabla transaccional principal de los siniestros reportados por los clientes.

| Campo | Tipo | Descripción |
| :--- | :---: | :--- |
| **ID Siniestro** | String | Clave primaria del siniestro (Formato `SIN-XXXX`). |
| **ID Póliza** | String | Clave foránea vinculada a la póliza contratada. |
| **ID Asegurado** | String | Clave foránea que identifica al asegurado. |
| **Ramo** | String | Categoría del seguro (ej: Vehículos, Salud, Hogar). |
| **Placa Vehículo Asegurado** | String | Placa identificativa del bien (en caso de Vehículos). |
| **Cobertura** | String | Tipo de cobertura afectada (ej: Choque, Robo, Daño). |
| **Fecha Ocurrencia** | Date | Fecha exacta en la que sucedió el accidente. |
| **Fecha Reporte** | Date | Fecha en la que se notificó a la aseguradora. |
| **Monto Reclamado ($)** | Float | Valor solicitado para cobertura por el cliente/proveedor. |
| **Monto Estimado ($)** | Float | Valor estimado de liquidación calculado por la aseguradora. |
| **Estado** | String | Estado de la reclamación (ej: Reserva, Pago Total, Negativa). |
| **Sucursal** | String | Ciudad/sucursal donde se atiende el siniestro. |
| **ID Proveedor** | String | Clave foránea del taller o centro médico que atiende. |
| **Descripción del Evento** | Text | Detalle libre narrado por el asegurado del siniestro. |
| **Docs Completos** | Boolean | Indicador de si se entregó toda la documentación (Sí/No). |
| **Prov. Lista Restrictiva** | Boolean | Indicador de si el taller/proveedor está sancionado (Sí/No). |
| **Días desde Inicio Póliza** | Integer | Días transcurridos entre inicio de póliza y accidente. |
| **Días hasta Fin Póliza** | Integer | Días faltantes para finalizar la vigencia de la póliza. |
| **N° Reclamos Previos Asegurado**| Integer | Cantidad de siniestros anteriores reportados por el cliente. |
| **Suma Asegurada ($)** | Float | Valor total máximo asegurado del bien. |
| **Similitud Narrativa Máx.** | Float | Coeficiente NLP de similitud contra descripciones previas. |

---

### 👤 Hoja 3: 3_Asegurados
Contiene el perfil histórico y demográfico de los clientes de la aseguradora.

| Campo | Tipo | Descripción |
| :--- | :---: | :--- |
| **ID Asegurado** | String | Clave primaria del cliente (Formato `ASEG-XXXX`). |
| **Nombres Asegurado** | String | Nombres y apellidos completos del cliente. |
| **Segmento** | String | Perfil comercial de cliente (ej: Masivo, Corporativo, Premium). |
| **Ciudad** | String | Ciudad de residencia registrada. |
| **Antigüedad (años)** | Integer | Años que el cliente lleva afiliado a la aseguradora. |
| **N° Pólizas Activas** | Integer | Cantidad de contratos vigentes actualmente. |
| **N° Reclamos Últimos 12 Meses**| Integer | Frecuencia de reclamos en el último período anual. |
| **N° Reclamos Histórico Total** | Integer | Historial acumulativo total de siniestros. |
| **Reclamos RC sin Tercero** | Integer | Casos de Responsabilidad Civil sin terceros identificados. |
| **Perfil Riesgo Histórico** | String | Clasificación comercial de riesgo (Bajo, Medio, Alto). |

---

### 🏢 Hoja 4: 4_Proveedores
Información de los talleres automotrices, clínicas médicas y peritos externos autorizados.

| Campo | Tipo | Descripción |
| :--- | :---: | :--- |
| **ID Proveedor** | String | Clave primaria del proveedor (Formato `PROV-XXXX`). |
| **Nombre Proveedor** | String | Nombre comercial del taller, clínica o perito. |
| **Tipo** | String | Categoría del proveedor (ej: Taller, Clínica, Perito). |
| **Ciudad** | String | Ciudad de ubicación física del proveedor. |
| **N° Siniestros Asociados** | Integer | Cantidad de casos asignados en los últimos 18 meses. |
| **En Lista Restrictiva** | Boolean | Indicador de si se encuentra sancionado por fraudes (Sí/No). |
| **Motivo Restricción** | String | Justificación de la sanción o sospecha histórica. |
| **Promedio Monto ($)** | Float | Costo medio de facturación por siniestro del proveedor. |
