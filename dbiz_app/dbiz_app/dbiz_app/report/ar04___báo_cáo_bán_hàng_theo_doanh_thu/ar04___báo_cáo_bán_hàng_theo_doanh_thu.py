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
            "label": "Mã tài khoản",
            "fieldname": "account_code",
            "fieldtype": "Data",
        },
        {
            "label": "Tên tài khoản",
            "fieldname": "account_name",
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
            "fieldname": "uom",
            "fieldtype": "Data",
        },
        {
            "label": "SL",
            "fieldname": "qty",
            "fieldtype": "Float",
        },
        {
            "label": "Đơn giá",
            "fieldname": "rate",
            "fieldtype": "Float",
        },
        {
            "label": "Thành tiền (Chưa thuế)",
            "fieldname": "net_amount",
            "fieldtype": "Float",
        },
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    data = frappe.db.sql(
        """
        SELECT
            SUBSTRING_INDEX(tsii.income_account, '-', 1) AS account_code,
            ta.account_name,
            tsoi.item_group,
            tsoi.item_code,
            tsoi.item_name,
            tsoi.uom,
            SUM(tsoi.qty) AS qty,
            tsoi.rate,
            SUM(tsoi.net_amount) AS net_amount
        FROM
            `tabSales Order Item` tsoi
        LEFT JOIN `tabSales Order` tso ON
            tso.name = tsoi.parent
        LEFT JOIN `tabSales Invoice Item` tsii ON
            tsii.sales_order = tso.name
        LEFT JOIN tabAccount ta ON
            ta.name = tsii.income_account
        WHERE
            tso.transaction_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
            AND tso.company = %(company)s
        GROUP BY
            tsoi.rate,
            tsoi.item_code,
            tsoi.uom
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
    return conditions


def validate_dates(filters):
    if filters.start_date > filters.end_date:
        frappe.throw(_("From Date must be before To Date"))
