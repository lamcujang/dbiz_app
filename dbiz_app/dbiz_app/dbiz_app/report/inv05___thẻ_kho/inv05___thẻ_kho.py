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
            "label": "Ngày, tháng",
            "fieldname": "posting_date",
            "fieldtype": "Data",
        },
        {
            "label": "Số chứng từ nhập",
            "fieldname": "voucher_no_input",
            "fieldtype": "Data",
        },
        {
            "label": "Số chứng từ xuất",
            "fieldname": "voucher_no_output",
            "fieldtype": "Data",
        },
        {
            "label": "Diễn giải",
            "fieldname": "description",
            "fieldtype": "Data",
        },
        {
            "label": "Ngày nhập, xuất",
            "fieldname": "posting_date2",
            "fieldtype": "Data",
        },
        {
            "label": "Số lượng nhập",
            "fieldname": "qty_input",
            "fieldtype": "Float",
        },
        {
            "label": "Số lượng xuất",
            "fieldname": "qty_output",
            "fieldtype": "Float",
        },
        {
            "label": "Tồn cuối kỳ",
            "fieldname": "qty_after_transaction",
            "fieldtype": "Float",
        },
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    data = frappe.db.sql(
        """
        SELECT 
            DATE_FORMAT(tsle.posting_date, '%%d/%%m/%%Y') AS posting_date, 
            CASE
                WHEN tsle.actual_qty > 0 THEN tsle.voucher_no
                ELSE NULL
            END AS voucher_no_input,
            CASE
                WHEN tsle.actual_qty < 0 THEN tsle.voucher_no
                ELSE NULL
            END AS voucher_no_output,
            NULL AS description,
            DATE_FORMAT(tsle.posting_date, '%%d/%%m/%%Y') AS posting_date2,
            GREATEST(tsle.actual_qty, 0) AS qty_input,
            ABS(LEAST(tsle.actual_qty, 0)) AS qty_output,
            tsle.qty_after_transaction
        FROM 
            `tabStock Ledger Entry` tsle
        LEFT JOIN tabWarehouse tw ON 
            tw.name = tsle.warehouse
        WHERE 
            tsle.posting_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
            AND tsle.company = %(company)s 
            AND (tsle.warehouse = %(warehouse)s OR %(warehouse)s IS NULL OR %(warehouse)s = '')
            AND (tsle.item_code = %(item_code)s OR %(item_code)s IS NULL OR %(item_code)s = '')
            AND (tw.account = %(account)s OR %(account)s IS NULL OR %(account)s = '')
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
        if not filters.get("item_code"):
            conditions["item_code"] = None
        if not filters.get("account"):
            conditions["account"] = None
    return conditions


def validate_dates(filters):
    if filters.start_date > filters.end_date:
        frappe.throw(_("From Date must be before To Date"))
