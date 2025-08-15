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
            "label": "Mã kho",
            "fieldname": "warehouse_code",
            "fieldtype": "Data",
        },
        {
            "label": "Tên kho",
            "fieldname": "warehouse_name",
            "fieldtype": "Data",
        },
        {
            "label": "Loại xuất kho",
            "fieldname": "ct_type",
            "fieldtype": "Data",
        },
        {
            "label": "Ngày",
            "fieldname": "posting_date",
            "fieldtype": "Data",
        },
        {
            "label": "Số CT xuất kho",
            "fieldname": "ct_code",
            "fieldtype": "Data",
        },
        {
            "label": "Số đơn hàng/hoá đơn",
            "fieldname": "order_no",
            "fieldtype": "Data",
        },
        {
            "label": "Trạng thái",
            "fieldname": "status",
            "fieldtype": "Data",
        },
        {
            "label": "Diễn giải",
            "fieldname": "description",
            "fieldtype": "Data",
        },
        {
            "label": "Mã sản phẩm",
            "fieldname": "item_code",
            "fieldtype": "Data",
        },
        {
            "label": "Tên sản phẩm",
            "fieldname": "item_name",
            "fieldtype": "Data",
        },
        {
            "label": "ĐVT",
            "fieldname": "stock_uom",
            "fieldtype": "Data",
        },
        {
            "label": "Giá",
            "fieldname": "rate",
            "fieldtype": "Float",
        },
        {
            "label": "SL",
            "fieldname": "stock_qty",
            "fieldtype": "Float",
        },
        {
            "label": "Thành tiền",
            "fieldname": "total_amount",
            "fieldtype": "Float",
        },
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    data = frappe.db.sql(
        """
        SELECT 
            tdni.warehouse AS warehouse_code,
            tw.warehouse_name,
            'Xuất bán hàng' AS ct_type,
            DATE_FORMAT(tdn.posting_date, '%%d/%%m/%%Y') AS posting_date,
            tdn.name AS ct_code,
            tdni.against_sales_order AS order_no,
            tdn.status,
            tdni.description,
            tdni.item_code,
            tdni.item_name,
            tdni.stock_uom,
            tdni.rate,
            ABS(tdni.stock_qty) AS stock_qty,
            tdni.rate * ABS(tdni.stock_qty) AS total_amount
        FROM
            `tabDelivery Note Item` tdni
        LEFT JOIN `tabDelivery Note` tdn ON
            tdn.name = tdni.parent
        LEFT JOIN `tabWarehouse` tw ON
            tw.name = tdni.warehouse
        LEFT JOIN `tabSales Order` tso ON
            tso.name = tdni.against_sales_order
        WHERE
            tdn.posting_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
            AND tdn.company = %(company)s
            AND (tdni.warehouse = %(warehouse)s OR %(warehouse)s IS NULL OR %(warehouse)s = '')
            AND (tdn.customer = %(customer)s OR %(customer)s IS NULL OR %(customer)s = '')
            AND (tdni.item_group = %(item_group)s OR %(item_group)s IS NULL OR %(item_group)s = '')
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
        if not filters.get("customer"):
            conditions["customer"] = None
        if not filters.get("item_group"):
            conditions["item_group"] = None
        if not filters.get("account"):
            conditions["account"] = None
    return conditions


def validate_dates(filters):
    if filters.start_date > filters.end_date:
        frappe.throw(_("From Date must be before To Date"))
