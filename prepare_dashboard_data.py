"""
Script de preparación de datos para el dashboard de Olist - Última Milla.
Genera el archivo 'orders_processed.csv' a partir de los datos crudos de Olist.
Simula una fecha "actual" (sim_today) para crear pedidos pendientes y una ventana de 7 días.
"""
import pandas as pd
import numpy as np
from datetime import timedelta
from OlistProject import get_here

# ------------------------------------------------------------------------------
# CONFIGURACIÓN
# ------------------------------------------------------------------------------

# sim_today = 
OLIST_BENEFIT_PCT = 0.15  # Margen del 15% sobre el precio
SIM_DAYS_OFFSET = 10        # Días añadidos a la última fecha de compra para sim_today

# ------------------------------------------------------------------------------
# 1. CARGA DE DATOS (pyarrow backend)
# ------------------------------------------------------------------------------

ROOT = get_here()  # Directorio del script
RAW_DATA = ROOT / "raw-data"
OUTPUT = ROOT / "processed-data"
OUTPUT.mkdir(exist_ok=True)

orders = pd.read_csv(
    RAW_DATA / "olist_orders_dataset.csv",
    engine="pyarrow",
    dtype_backend="pyarrow"
)
order_items = pd.read_csv(
    RAW_DATA / "olist_order_items_dataset.csv",
    engine="pyarrow",
    dtype_backend="pyarrow"
)
order_reviews = pd.read_csv(
    RAW_DATA / "olist_order_reviews_dataset.csv",
    engine="pyarrow",
    dtype_backend="pyarrow"
)
customers = pd.read_csv(
    RAW_DATA / "olist_customers_dataset.csv",
    engine="pyarrow",
    dtype_backend="pyarrow"
)
sellers = pd.read_csv(
    RAW_DATA / "olist_sellers_dataset.csv",
    engine="pyarrow",
    dtype_backend="pyarrow"
)
geolocation = pd.read_csv(
    RAW_DATA / "olist_geolocation_dataset.csv",
    engine="pyarrow",
    dtype_backend="pyarrow"
)

# ------------------------------------------------------------------------------
# 3. CREAR GEOLOCALIZACIÓN POR CIUDAD (lat/lng promedio)
# ------------------------------------------------------------------------------
city_geo = (
    geolocation
    .drop(columns="geolocation_zip_code_prefix")
    .groupby(['geolocation_city', 'geolocation_state'], 
             as_index=False)
    .agg("mean")
)

# ------------------------------------------------------------------------------
# 4. PREPARAR ITEMS POR PEDIDO Y VENDEROR
# ------------------------------------------------------------------------------
items_per_vendor = (
    order_items
    .groupby(["order_id", "seller_id"], as_index=False)
    .agg(
        total_price=("price", "sum"),
        total_freight=("freight_value", "sum"),
        min_shipping_date = ("shipping_limit_date", "min")
    )
    .merge(sellers, how="left", on='seller_id')
    
)

# ------------------------------------------------------------------------------
# 5. UNIFICAR DATOS PRINCIPALES
# ------------------------------------------------------------------------------
# Unir pedidos con clientes, items (y vendedor), reseñas y geolocalización
base = (
    orders
    .merge(customers, on="customer_id", how="left")
    .merge(items_per_vendor, on="order_id", how="left")
    .merge(sellers, on="seller_id", how="left", suffixes=('_customer', '_seller'))
    .merge(order_reviews[['order_id', 'review_score']], on="order_id", how="left")
    .merge(city_geo, on=['customer_city', 'customer_state'], how="left")
)

# ------------------------------------------------------------------------------
# 6. SIMULACIÓN DE LA FECHA ACTUAL (sim_today)
# ------------------------------------------------------------------------------
max_purchase = base["order_purchase_timestamp"].max()

print(f"Última fecha de compra real: {max_purchase}")
print(f"Fecha de simulación (hoy): {sim_today}")

base["sim_today"] = pd.Timestamp(sim_today)  # pyarrow compatible

# ------------------------------------------------------------------------------
# 7. CÁLCULOS DERIVADOS
# ------------------------------------------------------------------------------
# Pedido entregado (según estado o fecha de entrega no nula)
base["is_delivered"] = (
    (base["order_status"] == "delivered") |
    base["order_delivered_customer_date"].notna()
)

# Fecha de entrega (para pedidos entregados)
base["delivery_date"] = base["order_delivered_customer_date"].dt.date

# Días de retraso respecto a la fecha prometida (para pedidos entregados)
base["delay_days"] = np.where(
    base["is_delivered"] & base["delivery_date"].notna(),
    (base["order_delivered_customer_date"] - base["order_estimated_delivery_date"]).dt.days.clip(lower=0),
    np.nan
).astype("float64")  # PyArrow requiere float explícito

# Flags
base["is_on_time"] = (base["delay_days"] == 0) & base["is_delivered"]
base["is_delayed"] = base["delay_days"] > 0

# Pedidos pendientes a sim_today (no entregados ni cancelados y compra realizada antes de hoy)
base["is_pending"] = (
    (~base["is_delivered"]) &
    (base["order_status"] != "canceled") &
    (base["order_purchase_timestamp"] <= sim_today)
)

# Retrasos activos (pedidos pendientes cuya fecha prometida ya venció)
base["active_delay_days"] = np.where(
    base["is_pending"] & base["order_estimated_delivery_date"].notna(),
    np.maximum(
        0,
        (pd.Timestamp(sim_today).date() - base["order_estimated_delivery_date"].dt.date).apply(
            lambda td: td.days if pd.notna(td) else np.nan
        )
    ),
    np.nan
).astype("float64")

# Margen (15% del precio total del pedido)
base["total_margin"] = base["total_price"] * OLIST_BENEFIT_PCT

# Coste de cancelación (pedidos cancelados que ya habían sido enviados)
base["was_shipped_before_cancel"] = (
    (base["order_status"] == "canceled") &
    base["order_delivered_carrier_date"].notna()
)
base["cancellation_cost"] = np.where(
    base["was_shipped_before_cancel"],
    base["total_margin"] + base["total_freight"],
    0.0
)

# Tiempos de manipulación del vendedor y tránsito (en días)
base["seller_handling_days"] = np.where(
    base["order_approved_at"].notna() & base["order_delivered_carrier_date"].notna(),
    (base["order_delivered_carrier_date"] - base["order_approved_at"]).dt.days.astype("float64"),
    np.nan
)
base["transit_days"] = np.where(
    base["order_delivered_carrier_date"].notna() & base["order_delivered_customer_date"].notna(),
    (base["order_delivered_customer_date"] - base["order_delivered_carrier_date"]).dt.days.astype("float64"),
    np.nan
)

# Ventana de 7 días (entregas en la última semana respecto a sim_today)
base["delivery_within_last_7d"] = (
    base["is_delivered"] &
    (base["order_delivered_customer_date"] >= sim_today - timedelta(days=7)) &
    (base["order_delivered_customer_date"] <= sim_today)
)

# Meses para tendencias históricas
base["purchase_month"] = base["order_purchase_timestamp"].dt.to_period("M").astype(str)
base["delivery_month"] = base["order_delivered_customer_date"].dt.to_period("M").astype(str)  # NaN si no entregado

# ------------------------------------------------------------------------------
# 8. SELECCIÓN DE COLUMNAS FINALES
# ------------------------------------------------------------------------------
output_cols = [
    # Identificadores y fechas
    "order_id", "customer_id", "seller_id",
    "order_status",
    "order_purchase_timestamp", "order_approved_at",
    "order_delivered_carrier_date", "order_delivered_customer_date",
    "order_estimated_delivery_date", "delivery_date",
    # Simulación
    "sim_today",
    # Ubicaciones
    "customer_city", "customer_state", "city_lat", "city_lng",
    "seller_city", "seller_state",
    # Items
    "total_price", "total_freight", "total_margin",
    # Reseñas
    "review_score",
    # Flags y métricas
    "is_delivered", "is_pending", "is_on_time", "is_delayed",
    "delay_days", "active_delay_days",
    "cancellation_cost", "was_shipped_before_cancel",
    "seller_handling_days", "transit_days",
    "delivery_within_last_7d",
    "purchase_month", "delivery_month"
]

final_df = base[output_cols].copy()

# ------------------------------------------------------------------------------
# 9. EXPORTAR A CSV
# ------------------------------------------------------------------------------
output_path = OUTPUT / "orders_processed.csv"
final_df.to_csv(output_path, index=False)
print(f"Archivo generado: {output_path}")
print(f"Filas: {len(final_df)}, Columnas: {len(final_df.columns)}")
