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
            "label": "Ngày ghi sổ",
            "fieldname": "creation_date",
            "fieldtype": "Data",
        },
        {
            "label": "Ngày chứng từ",
            "fieldname": "posting_date",
            "fieldtype": "Data",
        },
        {
            "label": "Số hiệu CT (Thu)",
            "fieldname": "voucher_no_receive",
            "fieldtype": "Data",
        },
        {
            "label": "Số hiệu CT (Chi)",
            "fieldname": "voucher_no_pay",
            "fieldtype": "Data",
        },
        {
            "label": "Diễn giải",
            "fieldname": "remarks",
            "fieldtype": "Data",
        },
        {
            "label": "Đối tượng",
            "fieldname": "party",
            "fieldtype": "Data",
        },
        {
            "label": "TK đối ứng",
            "fieldname": "contra_account",
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
            "label": "Tồn",
            "fieldname": "in_stock",
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
        WITH OPENING AS (
            SELECT
                CASE
                    WHEN SUM(tge.credit) < SUM(tge.debit) THEN 'Dư đầu kỳ có'
                    WHEN SUM(tge.credit) > SUM(tge.debit) THEN 'Dư đầu kỳ nợ'
                    ELSE 'Dư đầu kỳ'
                END AS label,
                SUM(COALESCE(tge.credit, 0)) - SUM(COALESCE(tge.debit, 0)) AS qty
            FROM
                `tabGL Entry` tge
            WHERE
                tge.is_cancelled = 0
                AND tge.posting_date < DATE(%(start_date)s)
                AND tge.company = %(company)s
                AND tge.account = %(account)s
        ),
        ranked_entries AS (
            SELECT
                tge.*,
                ROW_NUMBER() OVER (
                ORDER BY
                    tge.posting_date,
                    tge.creation
                ) AS row_num
            FROM
                `tabGL Entry` tge
            WHERE
                tge.is_cancelled = 0
                AND tge.posting_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
                    AND tge.company = %(company)s
                    AND tge.account = %(account)s
        )
        SELECT  
            O.label AS label,
            ABS(O.qty) AS opening_qty,
            DATE_FORMAT(re.creation, '%%d/%%m/%%Y') AS creation_date,
            DATE_FORMAT(re.posting_date, '%%d/%%m/%%Y') AS posting_date,
            CASE
                WHEN re.voucher_subtype = 'Receive' THEN re.voucher_no
                ELSE ''
            END AS voucher_no_receive,
            CASE
                WHEN re.voucher_subtype = 'Pay' THEN re.voucher_no
                ELSE ''
            END AS voucher_no_pay,
            CASE 
                WHEN re.voucher_type = 'Payment Entry' THEN tpe.description
                ELSE re.remarks
            END AS remarks,
            re.party,
            SUBSTRING_INDEX(contra.account, ' - ', 1) AS contra_account,
            contra.credit AS debit,
            contra.debit AS credit,
            COALESCE(O.qty, 0) + SUM(
                COALESCE(contra.credit, 0) - COALESCE(contra.debit, 0)
            ) OVER (
            ORDER BY
                contra.posting_date,
                contra.creation
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) AS in_stock,
            re._comments AS comments
        FROM
            ranked_entries re
        LEFT JOIN `tabPayment Entry` tpe ON
            tpe.name = re.voucher_no
        LEFT JOIN `tabGL Entry` contra ON
            contra.voucher_no = re.voucher_no
            AND contra.voucher_type = re.voucher_type
            AND contra.posting_date = re.posting_date
            AND contra.account != re.account
            AND contra.is_cancelled = 0
        JOIN OPENING O ON
            1 = 1
        """,
        conditions,
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
