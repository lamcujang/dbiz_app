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
            "label": "Tên mã hàng",
            "fieldname": "item_code",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Tên sản phẩm",
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Kích thước (mm)",
            "fieldname": "item_size",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Số lượng",
            "fieldname": "qty",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": "Đơn giá",
            "fieldname": "rate",
            "fieldtype": "Float",
            "width": 120,
        },
        {
            "label": "Chất liệu",
            "fieldname": "item_stuff",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Nhóm chất liệu",
            "fieldname": "item_stuff_group",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Loại vật tư",
            "fieldname": "item_group",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "PO/TBSX",
            "fieldname": "purchase_order",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Khách hàng",
            "fieldname": "customer",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Nhà cung cấp",
            "fieldname": "supplier_name",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "ĐVT",
            "fieldname": "uom",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Trạng thái",
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Ngày Oder",
            "fieldname": "transaction_date",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Ngày dự kiến hàng về",
            "fieldname": "schedule_date",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Ngày thực tế hàng về",
            "fieldname": "posting_date",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Số lượng nhận thực tế",
            "fieldname": "received_qty",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": "Chênh lệch",
            "fieldname": "diff_qty",
            "fieldtype": "Float",
            "width": 100,
        },
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    data = frappe.db.sql(
        """
        SELECT
            tpri.item_code,
            tpri.item_name,
            ti.item_size,
            ABS(tpri.qty) AS qty,
            tpri.rate,
            ti.item_stuff,
            ti.item_stuff_group,
            tpri.item_group,
            tpri.purchase_order,
            tpo.customer,
            tpo.supplier_name,
            tpri.uom,
            tpr.status,
            DATE_FORMAT(tpo.transaction_date, '%%d/%%m') AS transaction_date,
            DATE_FORMAT(tpo.schedule_date, '%%d/%%m') AS schedule_date,
            DATE_FORMAT(tpr.posting_date, '%%d/%%m') AS posting_date,
            ABS(tpri.received_qty) AS received_qty,
            ABS(tpri.qty) - ABS(tpri.received_qty) AS diff_qty
        FROM
            `tabPurchase Receipt Item` tpri
        LEFT JOIN `tabPurchase Receipt` tpr ON
            tpr.name = tpri.parent
        LEFT JOIN tabItem ti ON
            ti.name = tpri.item_code
        LEFT JOIN `tabPurchase Order` tpo ON
            tpo.name = tpri.purchase_order
        WHERE
            tpr.company = %(company)s
            AND tpr.posting_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
            AND (tpo.supplier = %(supplier)s OR %(supplier)s IS NULL OR %(supplier)s = '')
            AND (tpri.item_code = %(item_code)s OR %(item_code)s IS NULL OR %(item_code)s = '')
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
        if not filters.get("supplier"):
            conditions["supplier"] = None
        if not filters.get("item_code"):
            conditions["item_code"] = None
    return conditions


def validate_dates(filters):
    if filters.start_date > filters.end_date:
        frappe.throw(_("From Date must be before To Date"))
