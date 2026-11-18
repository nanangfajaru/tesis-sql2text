"""
sqlgen.py — Penerjemah template SQL kunci ke 3 versi skema (OLTP, star, snowflake).

Template SQL memakai placeholder {nama}. {FROM} diganti tabel dasar + JOIN yang
dibutuhkan oleh placeholder lain di template tersebut. Dengan cara ini satu logika
soal menghasilkan 3 SQL kunci yang setara secara makna; kesetaraan HASIL tetap
diverifikasi dengan eksekusi (validasi_soal.py).
"""
import re

# ---------------- ekspresi per skema ----------------
EXPR = {
    "star": {
        "order": "f.order_id", "item_id": "f.order_item_id",
        "price": "f.price", "freight": "f.freight_value", "total": "f.total_value",
        "year": "d.year", "month": "d.month", "quarter": "d.quarter", "ym": "(d.year*100+d.month)",
        "dow": "d.day_of_week", "weekend": "d.is_weekend", "pdate": "d.full_date",
        "ddate": "dd.full_date", "edate": "de.full_date", "adate": "da.full_date", "cdate": "dc.full_date",
        "cstate": "c.state", "ccity": "c.city", "cust": "c.customer_unique_id",
        "sstate": "s.state", "scity": "s.city", "seller": "s.seller_id",
        "cat": "p.category_name", "product": "p.product_id", "weight": "p.weight_g",
        "status": "os.order_status",
    },
    "snowflake": {
        "order": "f.order_id", "item_id": "f.order_item_id",
        "price": "f.price", "freight": "f.freight_value", "total": "f.total_value",
        "year": "dm.year_key", "month": "dm.month", "quarter": "dm.quarter", "ym": "dm.month_key",
        "dow": "d.day_of_week", "weekend": "d.is_weekend", "pdate": "d.full_date",
        "ddate": "dd.full_date", "edate": "de.full_date", "adate": "da.full_date", "cdate": "dc.full_date",
        "cstate": "cst.state_code", "ccity": "cci.city_name", "cust": "c.customer_unique_id",
        "sstate": "sst.state_code", "scity": "sci.city_name", "seller": "s.seller_id",
        "cat": "k.category_name", "product": "p.product_id", "weight": "p.weight_g",
        "status": "os.order_status",
    },
    "oltp": {
        "order": "oi.order_id", "item_id": "oi.order_item_id",
        "price": "oi.price", "freight": "oi.freight_value", "total": "(oi.price + oi.freight_value)",
        "year": "EXTRACT(YEAR FROM o.order_purchase_timestamp)::int",
        "month": "EXTRACT(MONTH FROM o.order_purchase_timestamp)::int",
        "quarter": "EXTRACT(QUARTER FROM o.order_purchase_timestamp)::int",
        "ym": "(EXTRACT(YEAR FROM o.order_purchase_timestamp)*100 + EXTRACT(MONTH FROM o.order_purchase_timestamp))::int",
        "dow": "EXTRACT(ISODOW FROM o.order_purchase_timestamp)::int",
        "weekend": "(EXTRACT(ISODOW FROM o.order_purchase_timestamp) IN (6, 7))",
        "pdate": "o.order_purchase_timestamp::date",
        "ddate": "o.order_delivered_customer_date::date", "edate": "o.order_estimated_delivery_date::date",
        "adate": "o.order_approved_at::date", "cdate": "o.order_delivered_carrier_date::date",
        "cstate": "cu.customer_state", "ccity": "cu.customer_city", "cust": "cu.customer_unique_id",
        "sstate": "se.seller_state", "scity": "se.seller_city", "seller": "oi.seller_id",
        "cat": "t.product_category_name_english", "product": "oi.product_id", "weight": "pr.product_weight_g",
        "status": "o.order_status",
    },
}

# placeholder -> grup join
GROUP = {
    "year": "date", "month": "date", "quarter": "date", "ym": "date", "dow": "date", "weekend": "date",
    "pdate": "date", "ddate": "ddate", "edate": "edate", "adate": "adate", "cdate": "cdate",
    "cstate": "cust", "ccity": "cust", "cust": "cust",
    "sstate": "sell", "scity": "sell", "seller": "sell",
    "cat": "prod", "product": "prod", "weight": "prod", "status": "status",
}

JOINS = {
    "star": {
        "_base": "fact_sales f",
        "date": ["JOIN dim_date d ON d.date_key = f.purchase_date_key"],
        "ddate": ["LEFT JOIN dim_date dd ON dd.date_key = f.delivered_customer_date_key"],
        "edate": ["JOIN dim_date de ON de.date_key = f.estimated_delivery_date_key"],
        "adate": ["LEFT JOIN dim_date da ON da.date_key = f.approved_date_key"],
        "cdate": ["LEFT JOIN dim_date dc ON dc.date_key = f.delivered_carrier_date_key"],
        "cust": ["JOIN dim_customer c ON c.customer_key = f.customer_key"],
        "sell": ["JOIN dim_seller s ON s.seller_key = f.seller_key"],
        "prod": ["JOIN dim_product p ON p.product_key = f.product_key"],
        "status": ["JOIN dim_order_status os ON os.order_status_key = f.order_status_key"],
    },
    "snowflake": {
        "_base": "fact_sales f",
        "date": ["JOIN dim_date d ON d.date_key = f.purchase_date_key",
                 "JOIN dim_month dm ON dm.month_key = d.month_key"],
        "ddate": ["LEFT JOIN dim_date dd ON dd.date_key = f.delivered_customer_date_key"],
        "edate": ["JOIN dim_date de ON de.date_key = f.estimated_delivery_date_key"],
        "adate": ["LEFT JOIN dim_date da ON da.date_key = f.approved_date_key"],
        "cdate": ["LEFT JOIN dim_date dc ON dc.date_key = f.delivered_carrier_date_key"],
        "cust": ["JOIN dim_customer c ON c.customer_key = f.customer_key",
                 "JOIN dim_city cci ON cci.city_key = c.city_key",
                 "JOIN dim_state cst ON cst.state_key = cci.state_key"],
        "sell": ["JOIN dim_seller s ON s.seller_key = f.seller_key",
                 "JOIN dim_city sci ON sci.city_key = s.city_key",
                 "JOIN dim_state sst ON sst.state_key = sci.state_key"],
        "prod": ["JOIN dim_product p ON p.product_key = f.product_key",
                 "JOIN dim_category k ON k.category_key = p.category_key"],
        "status": ["JOIN dim_order_status os ON os.order_status_key = f.order_status_key"],
    },
    "oltp": {
        "_base": "order_items oi\nJOIN orders o ON o.order_id = oi.order_id",
        "date": [], "ddate": [], "edate": [], "adate": [], "cdate": [], "status": [],
        "cust": ["JOIN customers cu ON cu.customer_id = o.customer_id"],
        "sell": ["JOIN sellers se ON se.seller_id = oi.seller_id"],
        "prod": ["JOIN products pr ON pr.product_id = oi.product_id",
                 "JOIN product_category_name_translation t ON t.product_category_name = pr.product_category_name"],
    },
}

ORDER_GROUPS = ["date", "ddate", "edate", "adate", "cdate", "cust", "sell", "prod", "status"]
PH = re.compile(r"\{(\w+)\}")


def render(template: str, schema: str) -> str:
    used = set(PH.findall(template)) - {"FROM"}
    unknown = used - set(EXPR[schema])
    if unknown:
        raise KeyError(f"placeholder tidak dikenal: {unknown}")
    groups = {GROUP[u] for u in used if u in GROUP}
    j = JOINS[schema]
    parts = [j["_base"]] + [line for g in ORDER_GROUPS if g in groups for line in j[g]]
    frm = "\n".join(parts)
    out = template.replace("{FROM}", frm)
    return PH.sub(lambda m: EXPR[schema][m.group(1)], out).strip()
