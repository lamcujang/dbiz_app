# Copyright (c) 2024, lamnl and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    if not filters:
        filters = {}

    # Validate the dates before proceeding
    validate_dates(filters)

    # Define columns
    columns = get_columns()

    # SQL query with parameters from filters
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {
            "label": "Nhóm sản phẩm",
            "fieldname": "item_group",
            "fieldtype": "Data",
        },
        {
            "label": "Mã sản phẩm",
            "fieldname": "item_code",
            "fieldtype": "Data",
        },
        {
            "label": "Tên sản phảm",
            "fieldname": "item_name",
            "fieldtype": "Data",
        },
        {
            "label": "ĐVT",
            "fieldname": "stock_uom",
            "fieldtype": "Data",
        },
        {
            "label": "Đầu kỳ",
            "fieldname": "original_quantity",
            "fieldtype": "Float",
        },
        {
            "label": "SL nhập",
            "fieldname": "input_quantity",
            "fieldtype": "Float",
        },
        {
            "label": "SL xuất",
            "fieldname": "output_quantity",
            "fieldtype": "Float",
        },
        {
            "label": "Cuối kỳ",
            "fieldname": "total_quantity",
            "fieldtype": "Float",
        },
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    data = frappe.db.sql(
        """
        WITH opening_qty_cte AS (
            SELECT
                tsle.item_code,
                SUM(tsle.actual_qty) AS opening_qty
            FROM
                `tabStock Ledger Entry` tsle
            LEFT JOIN tabWarehouse tw ON 
                tw.name = tsle.warehouse
            WHERE
                tsle.stock_queue IS NOT NULL
                AND tsle.is_cancelled = 0
                AND tsle.posting_date < DATE(%(start_date)s)
                AND tsle.company = %(company)s
                AND (tsle.warehouse = %(warehouse)s OR %(warehouse)s IS NULL OR %(warehouse)s = '')
                AND (tw.account = %(account)s OR %(account)s IS NULL OR %(account)s = '')
            GROUP BY
                tsle.item_code
        ),
        aggregated_data AS (
            SELECT
                ti.item_group,
                tsle.item_code,
                ti.item_name,
                tsle.stock_uom,
                SUM(CASE 
                        WHEN tsle.actual_qty > 0 THEN tsle.actual_qty
                        ELSE 0
                    END) AS input_quantity,
                SUM(CASE 
                        WHEN tsle.actual_qty < 0 THEN ABS(tsle.actual_qty)
                        ELSE 0
                    END) AS output_quantity
            FROM
                `tabStock Ledger Entry` tsle
            LEFT JOIN tabItem ti ON
                ti.name = tsle.item_code
            LEFT JOIN tabWarehouse tw ON 
                tw.name = tsle.warehouse
            WHERE
                tsle.stock_queue IS NOT NULL
                AND tsle.is_cancelled = 0
                AND tsle.posting_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
                AND tsle.company = %(company)s
                AND (tsle.warehouse = %(warehouse)s OR %(warehouse)s IS NULL OR %(warehouse)s = '')
                AND (tw.account = %(account)s OR %(account)s IS NULL OR %(account)s = '')
                GROUP BY
                    tsle.item_code
        )
        SELECT
            ad.item_group,
            ad.item_code,
            ad.item_name,
            ad.stock_uom,
            COALESCE(oq.opening_qty, 0) AS original_quantity,
            ad.input_quantity,
            ad.output_quantity,
            COALESCE(oq.opening_qty, 0) + ad.input_quantity - ad.output_quantity AS total_quantity
        FROM
            aggregated_data ad
        LEFT JOIN opening_qty_cte oq ON 
            oq.item_code = ad.item_code
        ORDER BY
            ad.item_group, ad.item_code
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
        if not filters.get("account"):
            conditions["account"] = None
    return conditions


def validate_dates(filters):
    if filters.start_date > filters.end_date:
        frappe.throw(_("From Date must be before To Date"))
