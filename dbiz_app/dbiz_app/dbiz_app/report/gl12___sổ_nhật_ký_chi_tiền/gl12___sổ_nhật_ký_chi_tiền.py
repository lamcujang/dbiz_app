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
            "label": "Ngày tháng",
            "fieldname": "posting_date",
            "fieldtype": "Data",
        },
        {
            "label": "Số hiệu",
            "fieldname": "name",
            "fieldtype": "Data",
        },
        {
            "label": "Khách hàng",
            "fieldname": "party",
            "fieldtype": "Data",
        },
        {
            "label": "Diễn giải",
            "fieldname": "remarks",
            "fieldtype": "Data",
        },
        {
            "label": "TK nợ",
            "fieldname": "paid_to",
            "fieldtype": "Data",
        },
        {
            "label": "TK có",
            "fieldname": "paid_from",
            "fieldtype": "Data",
        },
        {
            "label": "Số phát sinh",
            "fieldname": "paid_amount",
            "fieldtype": "Float",
        },
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    data = frappe.db.sql(
        """
        SELECT
            DATE_FORMAT(tpe.posting_date , '%%d/%%m/%%Y') AS posting_date,
            tpe.name,
            tpe.party,
            tpe.remarks,
            SUBSTRING_INDEX(tpe.paid_to, '-', 1) AS paid_to,
            SUBSTRING_INDEX(tpe.paid_from, '-', 1) AS paid_from,
            ROUND(tpe.paid_amount) AS paid_amount
        FROM
            `tabPayment Entry` tpe
        WHERE
            tpe.docstatus <> 2
            AND tpe.payment_type = 'Pay'
            AND tpe.posting_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
            AND tpe.company = %(company)s
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
