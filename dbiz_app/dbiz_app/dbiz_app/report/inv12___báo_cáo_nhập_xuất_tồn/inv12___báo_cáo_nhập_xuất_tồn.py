import frappe
from frappe import _


def execute(filters=None):
    if not filters:
        filters = {}

    if filters.start_date > filters.end_date:
        frappe.throw(_("From Date must be before To Date"))

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {
            "label": "STT",
            "fieldname": "stt",
            "fieldtype": "Int",
            "width": 50,
            "align": "left",
        },
        {
            "label": "Mã kho",
            "fieldname": "warehouse_code",
            "fieldtype": "Data",
            "width": 150,
            "align": "left",
        },
        {
            "label": "Tên kho",
            "fieldname": "warehouse_name",
            "fieldtype": "Data",
            "width": 200,
            "align": "left",
        },
        {
            "label": "Nhóm sản phẩm",
            "fieldname": "product_category",
            "fieldtype": "Data",
            "width": 150,
            "align": "left",
        },
        {
            "label": "Mã Vật Tư",
            "fieldname": "item_code",
            "fieldtype": "Data",
            "width": 150,
            "align": "left",
        },
        {
            "label": "Tên Vật Tư",
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 200,
            "align": "left",
        },
        {
            "label": "ĐVT",
            "fieldname": "unit",
            "fieldtype": "Data",
            "width": 100,
            "align": "left",
        },
        {
            "label": "Số Dư Đầu Kỳ (SL)",
            "fieldname": "opening_qty",
            "fieldtype": "Float",
            "width": 120,
            "align": "left",
        },
        {
            "label": "Số Dư Đầu Kỳ (Giá trị)",
            "fieldname": "opening_amount",
            "fieldtype": "Float",
            "width": 150,
            "align": "left",
        },
        {
            "label": "Nhập Kho (SL)",
            "fieldname": "stock_in_qty",
            "fieldtype": "Float",
            "width": 120,
            "align": "left",
        },
        {
            "label": "Nhập Kho (Giá trị)",
            "fieldname": "stock_in_amount",
            "fieldtype": "Float",
            "width": 150,
            "align": "left",
        },
        {
            "label": "Xuất Kho (SL)",
            "fieldname": "stock_out_qty",
            "fieldtype": "Float",
            "width": 120,
            "align": "left",
        },
        {
            "label": "Xuất Kho (Giá trị)",
            "fieldname": "stock_out_amount",
            "fieldtype": "Float",
            "width": 150,
            "align": "left",
        },
        {
            "label": "Dư Cuối Kỳ (SL)",
            "fieldname": "closing_qty",
            "fieldtype": "Float",
            "width": 120,
            "align": "left",
        },
        {
            "label": "Dư Cuối Kỳ (Giá trị)",
            "fieldname": "closing_amount",
            "fieldtype": "Float",
            "width": 150,
            "align": "left",
        },
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    # INV12
    data = frappe.db.sql(
        """
            WITH opening_balance AS (
                SELECT 
                    tsle.warehouse,
                    tw.warehouse_name,
                    ti.item_group,
                    tsle.item_code,
                    ti.item_name,
                    ti.stock_uom,
                    SUM(tsle.actual_qty) as opening_qty,
                    SUM(tsle.stock_value_difference) as opening_value
                FROM `tabStock Ledger Entry` tsle
                LEFT JOIN `tabItem` ti ON ti.name = tsle.item_code
                LEFT JOIN `tabWarehouse` tw ON tw.name = tsle.warehouse
                WHERE 
                    tsle.company = %(company)s
                    AND tsle.posting_date < %(start_date)s
                    AND tsle.is_cancelled = 0
                    AND tsle.stock_queue IS NOT NULL
                    AND (tsle.warehouse = %(warehouse)s OR %(warehouse)s IS NULL OR %(warehouse)s = '')
                    AND (ti.item_group = %(item_group)s OR %(item_group)s IS NULL OR %(item_group)s = '')
                    AND (tw.account = %(account)s OR %(account)s IS NULL OR %(account)s = '')
                GROUP BY tsle.warehouse, tw.warehouse_name, ti.item_group, tsle.item_code, ti.item_name, ti.stock_uom
            ),
            period_movements AS (
                SELECT
                    tsle.warehouse,
                    tw.warehouse_name,
                    ti.item_group,
                    tsle.item_code,
                    ti.item_name,
                    ti.stock_uom,
                    SUM(CASE 
                        WHEN tsle.actual_qty > 0 THEN tsle.actual_qty
                        ELSE 0
                    END) AS stock_in_qty,
                    SUM(CASE 
                        WHEN tsle.actual_qty > 0 THEN tsle.stock_value_difference
                        ELSE 0
                    END) AS stock_in_value,
                    SUM(CASE 
                        WHEN tsle.actual_qty < 0 THEN ABS(tsle.actual_qty)
                        ELSE 0
                    END) AS stock_out_qty,
                    SUM(CASE 
                        WHEN tsle.actual_qty < 0 THEN ABS(tsle.stock_value_difference)
                        ELSE 0
                    END) AS stock_out_value,
                    ti.valuation_rate AS unit_price
                FROM `tabStock Ledger Entry` tsle
                LEFT JOIN `tabItem` ti ON ti.name = tsle.item_code
                LEFT JOIN `tabWarehouse` tw ON tw.name = tsle.warehouse
                WHERE 
                    tsle.company = %(company)s 
                    AND tsle.is_cancelled = 0
                    AND tsle.stock_queue IS NOT NULL
                    AND (tsle.warehouse = %(warehouse)s OR %(warehouse)s IS NULL OR %(warehouse)s = '')
                    AND (ti.item_group = %(item_group)s OR %(item_group)s IS NULL OR %(item_group)s = '')
                    AND (tw.account = %(account)s OR %(account)s IS NULL OR %(account)s = '')
                GROUP BY tsle.warehouse, tw.warehouse_name, ti.item_group, tsle.item_code, ti.item_name, ti.stock_uom
            )
            SELECT 
                ROW_NUMBER() OVER (ORDER BY pm.warehouse, pm.item_group, pm.item_code) as stt,
                pm.warehouse as warehouse_code,
                pm.warehouse_name,
                pm.item_group as product_category,
                pm.item_code,
                pm.item_name,
                pm.stock_uom as unit,
                unit_price,
                COALESCE(ob.opening_qty, 0) as opening_qty,
                CASE 
                    WHEN COALESCE(ob.opening_qty, 0) = 0 THEN 0 
                    ELSE COALESCE(ob.opening_value, 0) / COALESCE(ob.opening_qty, 1)
                END as opening_price,
                COALESCE(ob.opening_value, 0) as opening_amount,
                COALESCE(pm.stock_in_qty, 0) as stock_in_qty,
                COALESCE(pm.stock_in_value, 0) as stock_in_amount,
                COALESCE(pm.stock_out_qty, 0) as stock_out_qty,
                COALESCE(pm.stock_out_value, 0) as stock_out_amount,
                COALESCE(ob.opening_qty, 0) + COALESCE(pm.stock_in_qty, 0) - COALESCE(pm.stock_out_qty, 0) as closing_qty,
                CASE 
                    WHEN (COALESCE(ob.opening_qty, 0) + COALESCE(pm.stock_in_qty, 0) - COALESCE(pm.stock_out_qty, 0)) = 0 THEN 0
                    ELSE (COALESCE(ob.opening_value, 0) + COALESCE(pm.stock_in_value, 0) - COALESCE(pm.stock_out_value, 0)) /
                        (COALESCE(ob.opening_qty, 0) + COALESCE(pm.stock_in_qty, 0) - COALESCE(pm.stock_out_qty, 0))
                END as closing_price,
                COALESCE(ob.opening_value, 0) + COALESCE(pm.stock_in_value, 0) - COALESCE(pm.stock_out_value, 0) as closing_amount
            FROM period_movements pm
            LEFT JOIN opening_balance ob 
                ON ob.warehouse = pm.warehouse 
                AND ob.item_code = pm.item_code
            ORDER BY pm.warehouse, pm.item_group, pm.item_code;
        """,
        conditions,  # filters
        as_dict=True,
    )
    return data


def get_conditions(filters):
    conditions = {}
    for key, value in filters.items():
        if filters.get(key):
            conditions[key] = value
        if not filters.get("warehouse"):
            conditions["warehouse"] = None
        if not filters.get("item_group"):
            conditions["item_group"] = None
        if not filters.get("account"):
            conditions["account"] = None
    return conditions
