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
            "label": "Loại chứng từ",
            "fieldname": "ct_type",
            "fieldtype": "Data",
        },
        {
            "label": "Ngày",
            "fieldname": "posting_date",
            "fieldtype": "Data",
        },
        {
            "label": "Số CT nhập kho",
            "fieldname": "ct_code",
            "fieldtype": "Data",
        },
        {
            "label": "Số đơn hàng/hoá đơn",
            "fieldname": "order_no",
            "fieldtype": "Data",
        },
        {
            "label": "Nhà cung cấp",
            "fieldname": "supplier_name",
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
            tpri.warehouse AS warehouse_code,
            tw.warehouse_name,
            'Nhập mua hàng' AS ct_type,
            DATE_FORMAT(tpr.posting_date, '%%d/%%m/%%Y') AS posting_date,
            tpr.name AS ct_code,
            tpri.purchase_order AS order_no,
            tpr.supplier_name,
            tpr.status,
            tpri.description,
            tpri.item_group,
            tpri.item_code,
            tpri.item_name,
            tpri.stock_uom,
            tpri.rate,
            ABS(tpri.stock_qty) AS stock_qty,
            tpri.rate * ABS(tpri.stock_qty) AS total_amount
        FROM
            `tabPurchase Receipt Item` tpri
        LEFT JOIN `tabPurchase Receipt` tpr ON
            tpr.name = tpri.parent
        LEFT JOIN `tabWarehouse` tw ON
            tw.name = tpri.warehouse
        LEFT JOIN `tabPurchase Order` tpo ON
            tpo.name = tpri.purchase_order
        WHERE
            tpr.posting_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
            AND tpr.company = %(company)s
            AND (tpri.warehouse = %(warehouse)s OR %(warehouse)s IS NULL OR %(warehouse)s = '')
            AND (tpr.supplier = %(supplier)s OR %(supplier)s IS NULL OR %(supplier)s = '')
            AND (tpri.item_group = %(item_group)s OR %(item_group)s IS NULL OR %(item_group)s = '')
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
        if not filters.get("supplier"):
            conditions["supplier"] = None
        if not filters.get("item_group"):
            conditions["item_group"] = None
        if not filters.get("account"):
            conditions["account"] = None
    return conditions


def validate_dates(filters):
    if filters.start_date > filters.end_date:
        frappe.throw(_("From Date must be before To Date"))
