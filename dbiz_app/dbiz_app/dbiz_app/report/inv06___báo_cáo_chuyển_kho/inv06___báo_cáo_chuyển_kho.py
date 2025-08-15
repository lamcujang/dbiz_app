# Copyright (c) 2024, lamnl and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    if not filters:
        filters = {}

    if filters.start_date > filters.end_date:
        frappe.throw(_("From Date must be before To Date"))

    # Define columns
    columns = get_columns()

    # SQL query with parameters from filters
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {
            "label": "STT",
            "fieldname": "stt",
            "fieldtype": "Int",
            "width": 100,
        },
        {
            "label": "Loại phiếu",
            "fieldname": "transaction_type",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Ngày nhập, xuất",
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 100,
        },
        {
            "label": "Số phiếu",
            "fieldname": "voucher_no",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": "Diễn giải",
            "fieldname": "description",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": "Mã sản phẩm",
            "fieldname": "item_code",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": "Tên sản phẩm",
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": "Số lượng",
            "fieldname": "quantity",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": "Kho nhập/xuất",
            "fieldname": "warehouse",
            "fieldtype": "Data",
            "width": 150,
        },
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    data = frappe.db.sql(
        """
        SELECT 
            ROW_NUMBER() OVER (ORDER BY sl.posting_date) AS stt,
            CASE 
                WHEN sl.actual_qty > 0 THEN 'Nhập Kho' 
                WHEN sl.actual_qty < 0 THEN 'Xuất Kho' 
            END AS transaction_type,
            sl.posting_date AS posting_date,
            sl.voucher_no AS voucher_no,
            NULL AS description,
            sl.item_code AS item_code,
            it.item_name AS item_name,
            ABS(sl.actual_qty) AS quantity,
            CASE
                WHEN sl.actual_qty > 0 THEN w_from.warehouse_name  
                WHEN sl.actual_qty < 0 THEN w_to.warehouse_name 
            END AS warehouse
        FROM 
            `tabStock Ledger Entry` sl
            LEFT JOIN `tabItem` it ON sl.item_code = it.item_code 
            LEFT JOIN `tabStock Entry` se ON sl.voucher_no = se.name
            LEFT JOIN `tabWarehouse` w_from ON w_from.name = se.from_warehouse
            LEFT JOIN `tabWarehouse` w_to ON w_to.name = se.to_warehouse
        WHERE 
            sl.posting_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
            AND sl.company = %(company)s 
            AND (sl.warehouse = COALESCE(%(warehouse)s, sl.warehouse)
                OR %(warehouse)s IS NULL
                    OR %(warehouse)s = '')
            AND se.stock_entry_type IN ('Material Transfer', 'Material Transfer for Manufacture')
        ORDER BY 
            sl.posting_date;

    """,
        conditions,
        as_dict=True,
    )
    return data


def get_conditions(filters):
    conditions = {}
    print(filters.items())
    for key, value in filters.items():
        if filters.get(key):
            conditions[key] = value
        if not filters.get("warehouse"):
            conditions["warehouse"] = None
    return conditions
