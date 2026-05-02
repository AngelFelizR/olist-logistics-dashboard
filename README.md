# Dashboard de Monitoreo Logístico – Olist (Última Milla)

## Contexto
Olist conecta pequeños vendedores con clientes en todo Brasil. Una de las mayores fuentes de costo operativo son las entregas tardías: aunque afectan a menos del 10 % de los pedidos, generan contactos al *call center*, cancelaciones evitables y pérdida de margen. Un análisis exploratorio previo demostró que **predecir retrasos para alertar al cliente no aporta valor financiero** (las cancelaciones se adelantan sin beneficio neto) y que **la mejor estrategia es explicar las causas de los retrasos para eliminarlos desde su origen**.

Este dashboard está diseñado para el **Director de Operaciones Logísticas (Última Milla)**. Su propósito es monitorear diariamente la entrega de pedidos, identificar focos de retraso y facilitar decisiones operativas que reduzcan cancelaciones y protejan la satisfacción del cliente.

---

## Objetivo del Dashboard

| Objetivo | Preguntas de negocio que responde | Métricas asociadas |
|---|---|---|
| **Monitorear la salud de las entregas en tiempo real** | ¿Cuántos pedidos se han entregado a tiempo vs. tarde hoy y en los últimos 7 días? | *On‑Time Delivery Rate* (OTDR), pedidos pendientes, volumen de retrasos |
| **Identificar zonas críticas de retraso** | ¿En qué ciudades los tiempos de entrega están superando la promesa? | Retraso promedio (días), % de pedidos tardíos por ciudad |
| **Cuantificar el impacto de los vendedores** | ¿Cuánto del retraso se origina en la preparación del vendedor y no en la última milla? | Tiempo de manipulación del vendedor vs. tiempo de tránsito, % de retrasos imputables al vendedor |
| **Evaluar el costo de los retrasos** | ¿Cuánto margen y flete estamos perdiendo por cancelaciones atribuibles a entregas tardías? | Pérdida financiera acumulada (margen + flete), número de pedidos cancelados después del envío |
| **Medir la experiencia del cliente** | ¿Las entregas tardías están deteriorando la satisfacción? | Puntuación promedio de reseñas (estrellas) para pedidos a tiempo vs. tardíos |

---

## Usuario del Dashboard

**Cargo:** Director de Operaciones Logísticas (Última Milla)  
**Responsabilidades:**
- Redistribuir flota y rutas de transporte por región.
- Negociar con transportistas externos e incorporar nuevos proveedores logísticos.
- Aportar evidencia para ajustar los plazos de entrega prometidos en la plataforma.
- Explicar el desempeño logístico a la dirección, separando causas internas de las externas (vendedores).

**Forma de uso:** Monitoreo diario/reactivo con perspectiva histórica mensual. El dashboard se recargaría cada pocas horas en un entorno real; aquí se simula con datos históricos de Olist (2016‑2018) tomando una “fecha de hoy” ficticia y mostrando una ventana móvil de 7 días.

---

## Métricas Clave

| Métrica | Descripción | Cálculo |
|---|---|---|
| **On‑Time Delivery Rate (OTDR)** | % de pedidos entregados dentro del plazo estimado (sobre el total de pedidos con estado `delivered`). | `(entregas a tiempo / total entregas) * 100` |
| **Pedidos pendientes** | Órdenes que aún no han sido entregadas al cliente (estado distinto de `delivered` o `canceled`). | Conteo simple + distribución de días restantes hasta la fecha prometida. |
| **Retraso promedio** | Diferencia media entre la fecha real de entrega y la fecha estimada, para pedidos tardíos. | `AVG(order_delivered_customer_date - order_estimated_delivery_date) WHERE delay > 0` |
| **Tasa de cancelación tardía** | Pedidos que se cancelan **después** de haber sido enviados (estado `shipped` + cancelación). | Conteo de cancelados con fecha de envío no nula. |
| **Costo por retrasos** | Suma del margen perdido (15 % del valor del pedido) más el flete en pedidos cancelados tras el envío. | `SUM(margin + freight) WHERE delayed & canceled after shipping` |
| **Satisfacción (estrellas)** | Puntuación promedio de reseñas (`review_score`) para pedidos entregados, segmentada por estado (a tiempo / tarde). | `AVG(review_score)` en cada grupo. |

> **Nota sobre la simulación de datos vivos:**  
> El dataset histórico de Kaggle se trata como si la fecha máxima disponible fuera el día actual. Se define una “fecha de simulación” (`sim_today`) y todos los pedidos con `order_purchase_timestamp` anterior se consideran pasados. Los que aún no tienen `order_delivered_customer_date` y cuyo estado no es `canceled` se consideran **pendientes**. La ventana de análisis diario se limita a los 7 días anteriores a `sim_today`.

---

## Relación Decisiones ↔ Visualizaciones

A continuación se detalla cada decisión que el director puede tomar, el efecto observable en los datos y la visualización recomendada en Looker Studio.

| **Decisión** | **¿Dónde se ve el efecto?** | **Visualización en Looker Studio** | **Cómo interpretar y actuar** |
|---|---|---|---|
| **1. Redistribuir camiones / rutas en una región** | Concentración de pedidos retrasados por ciudad y volumen de pedidos pendientes. | **Mapa de calor de Brasil** por código postal/ciudad, coloreado según % de pedidos tardíos en los últimos 7 días. Complementado con una **tabla Top 10 ciudades** con peor OTDR y volumen de pedidos pendientes. | Si una ciudad muestra más de X % de retraso (ej. > 8 %) y tiene un volumen alto de pedidos, se refuerza con más vehículos o se rediseña la ruta. La serie histórica mensual permite ver si la medida funcionó. |
| **2. Contratar un transportista externo en una zona crítica** | Tiempo de tránsito excesivo en una ciudad que afecta a muchos clientes. | **Gráfico de barras horizontales** con el retraso promedio (días) y el volumen de pedidos entregados por ciudad. Se puede añadir un umbral de referencia (ej. 1 día). | Ciudades con retraso promedio consistentemente >1 día y alto volumen → candidatas a incorporar un transportista alternativo. Al comparar el antes/después en la gráfica de línea mensual, se valida el impacto del nuevo transportista. |
| **3. Solicitar extensión de las fechas de entrega prometidas** | Diferencia entre entrega real y promesa a nivel de categoría de producto o región de envío. | **Gráfico de distribución de la brecha** (días de retraso) para las 5 categorías o regiones con peores resultados. Se puede mostrar con un diagrama de caja o un histograma con percentiles 50, 90 y 95. | Si el percentil 90 de la brecha supera los 2‑3 días en una categoría/región, es señal de que la promesa actual es estructuralmente inalcanzable. El director lleva esta evidencia a los dueños de la plataforma para ajustar los *estimated delivery dates*. |
| **4. Reportar vendedores que causan retrasos (fuera de su control)** | Retrasos donde la causa raíz no es la última milla sino la preparación del producto por el vendedor. | **Gráfico de barras apiladas** de la duración de la demora desglosada en: *Tiempo de manipulación del vendedor* (entre `order_approved_at` y `order_delivered_carrier_date`) y *Tiempo de tránsito* (entre `order_delivered_carrier_date` y `order_delivered_customer_date`). Se filtra solo para pedidos tardíos, agrupados por **vendedor** o **ciudad del vendedor**. | Si el tiempo de manipulación del vendedor representa más del 50 % del retraso total, la causa no es logística. El director usa este gráfico para demostrar ante la dirección que el problema es del *seller* y derivarlo al departamento comercial. |
| **5. Monitorear el costo de las cancelaciones** | Margen y flete perdidos por pedidos que se cancelaron después de haber sido enviados. | **Indicador numérico (scorecard)** con la pérdida acumulada en el período (diaria/mensual), acompañado de un **gráfico de barras diario** mostrando la evolución. | Si la pérdida diaria aumenta súbitamente, se investiga de inmediato qué zona o vendedor está generando las cancelaciones. La serie histórica sirve para medir el éxito de las acciones correctivas. |
| **6. Evaluar el impacto en satisfacción del cliente** | Relación entre retraso y puntuación en reseñas. | **Dos gráficos de barras verticales** que comparan el promedio de estrellas (`review_score`) para pedidos entregados a tiempo vs. entregados tarde, desglosados por mes. | Si la brecha entre ambos promedios se amplía (>0.5 estrellas), es una alerta temprana de que los retrasos están dañando la experiencia del cliente, incluso si aún no se refleja en cancelaciones. |

---

## Boceto del Panel (Looker Studio)

El dashboard se organiza en **tres franjas verticales**, con filtros superiores para `Fecha de actualización (sim_today)` y `Ciudad` (selector desplegable). Se priorizan gráficos sencillos y directos, tal como prefiere el director.

**Fila 1 – KPIs de un vistazo (tarjetas numéricas)**
- *On‑Time Delivery Rate* (hoy y promedio 7 días)
- Pedidos pendientes de entrega
- Retrasos activos (pedidos con entrega pasada la fecha prometida y aún no entregados)
- Costo total por cancelaciones tardías (última semana)

**Fila 2 – Mapa de calor geográfico + Top ciudades**
- Mapa de Brasil coloreado por % de retraso (datos de los últimos 7 días; al pasar el cursor se ve la ciudad y el OTDR).
- Tabla/línea de las 10 ciudades con mayor número de retrasos o peor OTDR.

**Fila 3 – Análisis de causa raíz (Vendedor vs. Transporte)**
- Gráfico de barras apiladas con la demora desglosada para los **5 sellers con más pedidos retrasados**.
- Tabla de detalle que muestra para cada seller: total de pedidos, % de retraso, % de demora atribuible al vendedor.

**Fila 4 – Históricos para seguimiento mensual**
- Línea de tendencia del *On‑Time Delivery Rate* mensual.
- Barras mensuales de costo por cancelaciones y promedio de estrellas en reseñas (a tiempo vs. tarde).
- Permiten evaluar el impacto de las decisiones tomadas y reportar avances a la dirección.

---

## Datos y Transformaciones

- **Fuente:** Dataset público de Olist (Kaggle). Todas las tablas originales se limpian y unen según el proceso documentado en `01-defining-opp-operations.md`.
- **Simulación de entorno vivo:** Se define `sim_today = MAX(order_purchase_timestamp) + INTERVAL 'X days'` para que existan pedidos aún en tránsito. Los pedidos con fecha de entrega nula y estado `shipped` o `approved` se consideran pendientes. La ventana de monitoreo diario se aplica usando `sim_today - 7 days`.
- **Cálculo de demora del vendedor:** `seller_handling_days = DATEDIFF(order_delivered_carrier_date, order_approved_at)`. La fracción de responsabilidad del vendedor se calcula como `seller_handling_days / total_delay_days` cuando `total_delay_days > 0`.
- **Cálculo de costo de retraso:** El margen se estima como el 15 % del precio del ítem, y el flete se toma de `freight_value`. Solo se contabiliza en pedidos con estado `canceled` y que tuvieron `order_status = 'shipped'` previamente (o `order_delivered_carrier_date` no nulo).

---

## Próximos pasos

- Incorporar la predicción de retrasos como una capa informativa adicional en el mapa (sin alertar al cliente), solo para que el director anticipe picos de trabajo.
- Automatizar un sistema de alertas que notifique por correo a los supervisores regionales cuando una ciudad supere el umbral de retrasos durante dos días consecutivos.
- Conectar con datos reales de telemetría de los transportistas (si Olist integra GPS) para una visión aún más precisa.

---

**Conclusión:** Este dashboard transforma los datos de entregas en una herramienta de acción diaria. En lugar de reaccionar tarde a las quejas, el director puede redistribuir recursos, negociar con transportistas o presentar evidencia a otros departamentos **antes** de que los retrasos se traduzcan en cancelaciones y malas reseñas.
