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
            "label": "Ngày tạo",
            "fieldname": "creation_date",
            "fieldtype": "Data",
        },
        {
            "label": "Số hiệu",
            "fieldname": "name",
            "fieldtype": "Data",
        },
        {
            "label": "Ngày ghi sổ",
            "fieldname": "posting_date",
            "fieldtype": "Data",
        },
        {
            "label": "Diễn giải",
            "fieldname": "remarks",
            "fieldtype": "Data",
        },
        {
            "label": "Số hiệu TK đối ứng",
            "fieldname": "against",
            "fieldtype": "Data",
        },
        {
            "label": "Nợ",
            "fieldname": "debit",
            "fieldtype": "Float",
        },
        {
            "label": "Có",
            "fieldname": "credit",
            "fieldtype": "Float",
        },
        {
            "label": "Ghi chú",
            "fieldname": "comments",
            "fieldtype": "Data",
        },
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    data = frappe.db.sql(
        """
        SELECT
            NULL AS creation_date,
            NULL AS name,
            NULL AS posting_date,
            NULL AS remarks,
            'Dư đầu kỳ nợ:' AS against,
            COALESCE(SUM(tge.debit_in_account_currency - tge.credit_in_account_currency), 0) AS debit,
            NULL AS credit,
            NULL AS comments
        FROM
            `tabGL Entry` tge
        WHERE
            tge.is_cancelled = 0
            AND tge.posting_date < DATE(%(start_date)s)
            AND tge.company = %(company)s
            AND(tge.account = %(account)s OR %(account)s IS NULL OR %(account)s = '')
        UNION ALL
        SELECT 
            NULL AS creation_date,
            NULL AS name,
            NULL AS posting_date,
            NULL AS remarks,
            'Phát sinh trong kỳ:' AS against, 
            COALESCE(SUM(tge.debit_in_account_currency), 0) AS debit, 
            COALESCE(SUM(tge.credit_in_account_currency), 0) AS credit,
            NULL AS comments
        FROM
            `tabGL Entry` tge
        WHERE
            tge.is_cancelled = 0
            AND tge.posting_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
            AND tge.company = %(company)s
            AND(tge.account = %(account)s OR %(account)s IS NULL OR %(account)s = '')
        UNION ALL
        SELECT 
            NULL AS creation_date,
            NULL AS name,
            NULL AS posting_date,
            NULL AS remarks,
            'Dư cuối kỳ nợ:' AS against,
            COALESCE(SUM(tge.debit_in_account_currency - credit_in_account_currency), 0) AS debit,
            NULL AS credit,
            NULL AS comments
        FROM
            `tabGL Entry` tge
        WHERE
            tge.is_cancelled = 0
            AND tge.posting_date <= DATE(%(end_date)s)
            AND tge.company = %(company)s
            AND(tge.account = %(account)s OR %(account)s IS NULL OR %(account)s = '')
        UNION ALL
        SELECT
            DATE_FORMAT(tge.creation, '%%d/%%m/%%Y') AS creation_date,
            tge.name,
            DATE_FORMAT(tge.posting_date, '%%d/%%m/%%Y') AS posting_date,
            tge.remarks,
            SUBSTRING_INDEX(tge.against, ' - ', 1) against,
            tge.debit_in_account_currency AS debit,
            tge.credit_in_account_currency AS credit,
            tge.`_comments` AS comments
        FROM
            `tabGL Entry` tge
        WHERE 
            tge.is_cancelled = 0
            AND tge.posting_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
            AND tge.company = %(company)s
            AND(tge.account = %(account)s OR %(account)s IS NULL OR %(account)s = '')
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
        if not filters.get("account"):
            conditions["account"] = None
    return conditions


def validate_dates(filters):
    if filters.start_date > filters.end_date:
        frappe.throw(_("From Date must be before To Date"))
