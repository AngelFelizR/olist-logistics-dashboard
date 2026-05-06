"""
Script de preparación de datos para el dashboard de Olist - Última Milla.
Genera el archivo 'orders_processed.csv' a partir de los datos crudos de Olist.
"""

# ------------------------------------------------------------------------------
# CONFIGURACIÓN
# ------------------------------------------------------------------------------

OLIST_BENEFIT_PCT = 0.15  # Margen del 15% sobre el precio
CURRENT_DATE = '2018-08-31'

# ------------------------------------------------------------------------------
# CARGANDO FUNCIONES
# ------------------------------------------------------------------------------

import pandas as pd
import numpy as np
from pathlib import Path

def groupbycustom(df, by, **kwargs):
    return df.groupby(by, sort=False, observed=True, as_index=False, **kwargs)

# ------------------------------------------------------------------------------
# 1. CARGA DE DATOS (pyarrow backend)
# ------------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
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
order_products = pd.read_csv(
    RAW_DATA / "olist_products_dataset.csv",
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
# 2. ORDER PRODUCT DETAILS BY ORDER
# ------------------------------------------------------------------------------

category_mapping = [
    # Arts & crafts
    (r'artes(?:_e_artesanato)?', 'arts_crafts'),
    # Seasonal & events
    (r'artigos_de_festas|artigos_de_natal', 'seasonal_events'),
    # Babies (you had it grouped with toys, but missing explicit match)
    (r'^bebes$', 'sports_toys'),
    # Photo & imaging
    (r'cine_foto', 'electronics'),
    # Climate / appliances
    (r'climatizacao', 'home_furniture'),
    # Generic “cool stuff” → treat as gifts
    (r'cool_stuff', 'gifts'),
    # Appliances (missing!)
    (r'eletrodomesticos(?:_2)?|eletroportateis', 'home_furniture'),
    # Flowers
    (r'flores', 'gifts'),
    # Kitchen (French label in dataset)
    (r'la_cuisine', 'home_furniture'),
    # Travel / bags
    (r'malas_acessorios', 'fashion'),
    # Marketplace (ambiguous → business)
    (r'market_place', 'industry_business'),
    # Portable kitchen appliances
    (r'portateis_casa_forno_e_cafe', 'home_furniture'),
    # Services / insurance
    (r'seguros_e_servicos', 'industry_business'),
    # Health & beauty
    (r'beleza_saude|perfumaria|higiene', 'health_beauty'),
    # Electronics & tech
    (r'eletronicos|informatica_acessorios|audio|telefonia|telefonia_fixa|tablets_impressao_imagem|pcs|pc_gamer|consoles_games', 'electronics'),
    # Home & furniture
    (r'cama_mesa_banho|moveis_decoracao|utilidades_domesticas|casa_conforto|moveis_quarto|moveis_sala|moveis_escritorio|moveis_cozinha|cozinha|moveis_colchao', 'home_furniture'),
    # Auto
    (r'automotivo', 'auto'),
    # Sports & leisure
    (r'esporte_lazer|brinquedos', 'sports_toys'),
    # Fashion & accessories
    (r'fashion_|moda|calcados|bolsas|roupa|underwear', 'fashion'),
    # Food & beverages
    (r'alimentos|bebidas', 'food_drink'),
    # Construction & tools
    (r'construcao|ferramentas|jardim|iluminacao|seguranca', 'construction_tools'),
    # Pet shop
    (r'pet_shop', 'pet_supplies'),
    # Books & media
    (r'livros|cds|dvds|musica', 'books_media'),
    # Office & stationery
    (r'papelaria', 'stationery'),
    # Gifts & watches
    (r'relogios_presentes', 'gifts'),
    # Agro & industry
    (r'agro_industria|industria_comercio|comercio', 'industry_business')
]

products_details_by_order = (
    order_products
    .query('~product_category_name.isna()')
    .assign(
        product_volume_cm3=lambda x: (
            x.product_length_cm *
            x.product_height_cm * 
            x.product_width_cm
        ),
        category_group=lambda x: pd.Categorical(
            np.select(
                [x.product_category_name.str.contains(p, case=False, regex=True, na=False)
                 for p, _ in category_mapping],
                [c for _, c in category_mapping],
                default='unmatched'
            ),
            categories=pd.Series([c for _, c in category_mapping]).unique().tolist() + ['unmatched']
        )
    )
    [['product_id', 'category_group', 'product_weight_g', 'product_volume_cm3']] 
    .merge(order_items.drop(columns='order_item_id'),
           on='product_id',
           how="right",
           validate="1:m")
    .drop(columns='product_id')
    .assign(
        total_price=lambda x: (
            x.pipe(groupbycustom, ['order_id', 'category_group'])
            ['price']
            .transform('sum')
        )
    )
    .sort_values(['order_id', 'total_price'], ascending=[True, False])
    .pipe(groupbycustom, 'order_id')
    .agg(
        order_main_category=('category_group', 'first'),
        order_main_seller=('seller_id','first'),
        order_last_shipping_date=('shipping_limit_date','max'),
        order_volume_cm3=('product_volume_cm3', 'sum'),
        order_weight_g=('product_weight_g', 'sum'),
        order_price=('price','sum'),
        order_freight=('freight_value','sum')
    )
)


# ------------------------------------------------------------------------------
# 3. CREAR GEOLOCALIZACIÓN POR CIUDAD (lat/lng promedio)
# ------------------------------------------------------------------------------
city_geo = (
    geolocation
    .drop(columns="geolocation_zip_code_prefix")
    .pipe(groupbycustom, ['geolocation_city', 'geolocation_state'])
    .agg("mean")
)

# ------------------------------------------------------------------------------
# 4. TOMAR LA ÚLTIMA REVIEW DE CADA ORDEN
# ------------------------------------------------------------------------------

order_last_review = pd.concat(
    [(
    order_reviews
    .query('~review_answer_timestamp.isna()')
    .sort_values('review_answer_timestamp', ascending=False)
    .drop_duplicates('order_id', keep='first')
    ), 
     order_reviews.query('review_answer_timestamp.isna()')], 
    ignore_index=True
)[['order_id', 'review_score','review_creation_date','review_answer_timestamp']]


# ------------------------------------------------------------------------------
# 5. DEFINIR DATOS A EXPORTAR
# ------------------------------------------------------------------------------

def add_geo_coords(df, geo_df, city_col, state_col):
    """Add latitude and longitude coordinates from city_geo dataframe."""
    return (df
        .merge(geo_df,
               left_on=[city_col, state_col],
               right_on=['geolocation_city', 'geolocation_state'],
               how='left',
               validate='m:1')
        .drop(columns=['geolocation_city', 'geolocation_state'])
        .rename(columns={'geolocation_lat': f'{city_col.replace("_city", "")}_lat',
                        'geolocation_lng': f'{city_col.replace("_city", "")}_lng'}))

current_ts = pd.Timestamp(CURRENT_DATE)

orders_processed = (
    orders
    .query('order_purchase_timestamp <= @current_ts')
    .merge(order_last_review, on="order_id", how="left", validate="1:1")
    .merge(products_details_by_order, on="order_id", how="left", validate="1:1")
    .merge(customers[['customer_id','customer_unique_id','customer_city','customer_state']],
           on="customer_id", how="left", validate="m:1")
    .drop(columns='customer_id')
    .pipe(add_geo_coords, city_geo, 'customer_city', 'customer_state')
    .merge(sellers[['seller_id','seller_city','seller_state']],
           left_on='order_main_seller', right_on="seller_id", how="left", validate="m:1")
    .pipe(add_geo_coords, city_geo, 'seller_city', 'seller_state')
    # CÁLCULOS DERIVADOS
    .assign(
        # Pedido entregado (según estado o fecha de entrega no nula)
        is_delivered=lambda x: (
            (x.order_status == "delivered")
            | x.order_delivered_customer_date.notna()
        ),

        # Pedidos pendientes
        is_pending=lambda x: (~x.is_delivered) & x.review_creation_date.isna(),
        is_canceled =lambda x: (
            (x.order_status == "canceled") |
            (
                (x.order_status != "delivered") &
                x.order_delivered_customer_date.isna() &
                x.review_creation_date.notna()
            )
        ),

        # Días de retraso respecto a la fecha prometida 
        delay_days=lambda x: (
            np.where(
                x.is_delivered | x.is_canceled,
                (x.order_delivered_customer_date.fillna(x.review_creation_date)
                 - x.order_estimated_delivery_date).dt.days.clip(lower=0),
                np.nan
            ).astype("float64")
        ),

        # Flags
        is_on_time=lambda x: (x.delay_days == 0) & x.is_delivered,
        is_delayed=lambda x: x.delay_days > 0,

        # Retrasos activos (pedidos pendientes cuya fecha prometida ya venció)
        active_delay_days=lambda x:(
            np.where(
                x.is_pending,
                (current_ts - x.order_estimated_delivery_date).dt.days.clip(lower=0),
                np.nan
            ).astype("float64")
        ),

        # Margen (15% del precio total del pedido)
        total_margin=lambda x: x.order_price * OLIST_BENEFIT_PCT,

        # Coste de cancelación

        cancelation_cost=lambda x: np.select(
            [x.is_canceled & x.is_delivered,
             x.is_canceled & (~x.is_delivered)],
            [x.total_margin + x.order_freight,
            x.total_margin],
            default=0.0
        ).astype("float64"),

        # Tiempos de manipulación del vendedor y tránsito (en días)
        seller_handling_days=lambda x: np.where(
            x.order_approved_at.notna() & x.order_delivered_carrier_date.notna(),
            (x.order_delivered_carrier_date - x.order_approved_at).dt.days.astype("float64"),
            np.nan
        ),
        transit_days=lambda x: np.where(
            x.order_delivered_carrier_date.notna() & x.order_delivered_customer_date.notna(),
            (x.order_delivered_customer_date - x.order_delivered_carrier_date).dt.days.astype("float64"),
            np.nan
        )
    )
    .convert_dtypes(dtype_backend="pyarrow")
)


# ------------------------------------------------------------------------------
# 6. CONVERTIR BOOLEANOS A 1/0 ANTES DE EXPORTAR
# ------------------------------------------------------------------------------

# Identificar columnas booleanas (tipo bool o boolean)
bool_columns = orders_processed.select_dtypes(include=['bool', 'boolean']).columns

# Convertir True -> 1, False -> 0
orders_processed[bool_columns] = orders_processed[bool_columns].astype(int)

# ------------------------------------------------------------------------------
# 7. EXPORTAR A EXCEL
# ------------------------------------------------------------------------------
output_path = OUTPUT / "orders_processed.xlsx"
orders_processed.to_excel(output_path, index=False)
final_rows, final_cols = orders_processed.shape
print(f"Archivo generado: {output_path}")
print(f"Filas: {final_rows}, Columnas: {final_cols}")
