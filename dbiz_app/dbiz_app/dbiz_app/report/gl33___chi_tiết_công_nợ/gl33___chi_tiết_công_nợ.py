# Copyright (c) 2024, lamnl and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    if not filters:
        filters = {}

    # Validate the dates
    validate_dates(filters)

    # Define columns
    columns = get_columns()

    # SQL query to get raw data
    data = get_data(filters)
    # print(data)

    return columns, data


def get_columns():
    return [
        {
            "label": "Ngày ghi sổ",
            "fieldname": "entry_date",
            "fieldtype": "Data",
        },
        {
            "label": "Số hóa đơn",
            "fieldname": "invoice_no",
            "fieldtype": "Data",
        },
        {
            "label": "Số hiệu",
            "fieldname": "name",
            "fieldtype": "Data",
        },
        {
            "label": "Ngày tháng",
            "fieldname": "posting_date",
            "fieldtype": "Data",
        },
        {
            "label": "Đơn vị",
            "fieldname": "unit",
            "fieldtype": "Data",
        },
        {
            "label": "Diễn giải",
            "fieldname": "remarks",
            "fieldtype": "Data",
        },
        {
            "label": "TK đối ứng",
            "fieldname": "against",
            "fieldtype": "Data",
        },
        {
            "label": "Thời hạn được chiết khấu",
            "fieldname": "discount_date",
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
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    data = frappe.db.sql(
        """
        SELECT
            NULL AS entry_date,
            NULL AS invoice_no,
            NULL AS name,
            NULL AS posting_date,
            NULL AS unit,
            NULL AS remarks,
            NULL AS against,
            'Dư đầu kỳ có:' AS discount_date,
            CASE
                WHEN SUM(tge.debit_in_account_currency - tge.credit_in_account_currency) > 0 THEN ROUND(SUM(tge.debit_in_account_currency - tge.credit_in_account_currency))
                ELSE NULL
            END AS debit,
            CASE
                WHEN SUM(tge.credit_in_account_currency - tge.debit_in_account_currency) > 0 THEN ROUND(SUM(tge.credit_in_account_currency - tge.debit_in_account_currency))
                ELSE 0
            END AS credit
        FROM
            `tabPurchase Invoice` tpi
        LEFT JOIN `tabGL Entry` tge ON
            tge.voucher_no = tpi.name
        LEFT JOIN 
            (
            SELECT
                purchase_order,
                parent
            FROM
                `tabPurchase Invoice Item`
            GROUP BY
                purchase_order
            ) tpii ON
            tpii.parent = tpi.name
        LEFT JOIN (
            SELECT
                discount,
                discounted_amount,
                discount_date,
                parent
            FROM
                `tabPayment Schedule`
            ORDER BY
                discount_date ASC
            LIMIT 1
            ) tps ON
            (tps.discount <> 0
                AND tps.discounted_amount <> 0)
            AND tps.parent = tpii.purchase_order
        WHERE
            tge.party IS NOT NULL
            AND tge.is_cancelled = 0
            AND tge.posting_date < DATE(%(start_date)s)
            AND tpi.company = %(company)s
            AND (tpi.supplier = %(supplier)s OR %(supplier)s IS NULL OR %(supplier)s = '')
            AND (tpi.currency = %(currency)s OR %(currency)s IS NULL OR %(currency)s = '')
            AND (tge.against = %(account)s OR %(account)s IS NULL OR %(account)s = '')
        UNION ALL
        SELECT
            NULL AS entry_date,
            NULL AS invoice_no,
            NULL AS name,
            NULL AS posting_date,
            NULL AS unit,
            NULL AS remarks,
            NULL AS against,
            'Phát sinh trong kỳ:' AS discount_date,
            ROUND(SUM(tge.debit_in_account_currency)) AS debit,
            ROUND(SUM(tge.credit_in_account_currency)) AS credit
        FROM
            `tabPurchase Invoice` tpi
        LEFT JOIN `tabGL Entry` tge ON
            tge.voucher_no = tpi.name
        LEFT JOIN 
            (
            SELECT
                purchase_order,
                parent
            FROM
                `tabPurchase Invoice Item`
            GROUP BY
                purchase_order
            ) tpii ON
            tpii.parent = tpi.name
        LEFT JOIN (
            SELECT
                discount,
                discounted_amount,
                discount_date,
                parent
            FROM
                `tabPayment Schedule`
            ORDER BY
                discount_date ASC
            LIMIT 1
            ) tps ON
            (tps.discount <> 0
                AND tps.discounted_amount <> 0)
            AND tps.parent = tpii.purchase_order
        WHERE
            tge.party IS NOT NULL
            AND tge.is_cancelled = 0
            AND tge.posting_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
            AND tpi.company = %(company)s
            AND (tpi.supplier = %(supplier)s OR %(supplier)s IS NULL OR %(supplier)s = '')
            AND (tpi.currency = %(currency)s OR %(currency)s IS NULL OR %(currency)s = '')
            AND (tge.against = %(account)s OR %(account)s IS NULL OR %(account)s = '')
        UNION ALL
        SELECT
            NULL AS entry_date,
            NULL AS invoice_no,
            NULL AS name,
            NULL AS posting_date,
            NULL AS unit,
            NULL AS remarks,
            NULL AS against,
            'Dư cuối kỳ có:' AS discount_type,
            CASE
                WHEN SUM(tge.debit_in_account_currency - tge.credit_in_account_currency) > 0 THEN ROUND(SUM(tge.debit_in_account_currency - tge.credit_in_account_currency))
                ELSE NULL
            END AS debit,
            CASE
                WHEN SUM(tge.credit_in_account_currency - tge.debit_in_account_currency) > 0 THEN ROUND(SUM(tge.credit_in_account_currency - tge.debit_in_account_currency))
                ELSE 0
            END AS credit
        FROM
            `tabPurchase Invoice` tpi
        LEFT JOIN `tabGL Entry` tge ON
            tge.voucher_no = tpi.name
        LEFT JOIN 
            (
            SELECT
                purchase_order,
                parent
            FROM
                `tabPurchase Invoice Item`
            GROUP BY
                purchase_order
            ) tpii ON
            tpii.parent = tpi.name
        LEFT JOIN (
            SELECT
                discount,
                discounted_amount,
                discount_date,
                parent
            FROM
                `tabPayment Schedule`
            ORDER BY
                discount_date ASC
            LIMIT 1
                ) tps ON
            (tps.discount <> 0
                AND tps.discounted_amount <> 0)
            AND tps.parent = tpii.purchase_order
        WHERE
            tge.party IS NOT NULL
            AND tge.is_cancelled = 0
            AND tge.posting_date <= DATE(%(end_date)s)
            AND tpi.company = %(company)s
            AND (tpi.supplier = %(supplier)s OR %(supplier)s IS NULL OR %(supplier)s = '')
            AND (tpi.currency = %(currency)s OR %(currency)s IS NULL OR %(currency)s = '')
            AND (tge.against = %(account)s OR %(account)s IS NULL OR %(account)s = '')
        UNION ALL
        SELECT
            DATE_FORMAT(tge.posting_date, '%%d/%%m/%%Y') AS entry_date,
            NULL AS invoice_no,
            tpi.name,
            DATE_FORMAT(tpi.posting_date, '%%d/%%m/%%Y') AS posting_date,
            NULL AS unit,
            tge.remarks,
            SUBSTRING_INDEX(tge.against, '-', 1) AS against,
            tps.discount_date,
            ROUND(tge.debit_in_account_currency) AS debit,
            ROUND(tge.credit_in_account_currency) AS credit
        FROM
            `tabPurchase Invoice` tpi
        LEFT JOIN `tabGL Entry` tge ON
            tge.voucher_no = tpi.name
        LEFT JOIN
            (
            SELECT
                purchase_order,
                parent
            FROM
                `tabPurchase Invoice Item`
            GROUP BY
                purchase_order
            )
        tpii ON
            tpii.parent = tpi.name
        LEFT JOIN (
            SELECT
                discount,
                discounted_amount,
                discount_date,
                parent
            FROM
                `tabPayment Schedule`
            ORDER BY
                discount_date ASC
            LIMIT 1
            ) tps ON
            (tps.discount <> 0
                AND tps.discounted_amount <> 0)
            AND tps.parent = tpii.purchase_order
        WHERE
            tge.party IS NOT NULL
            AND tge.is_cancelled = 0
            AND tge.posting_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
            AND tpi.company = %(company)s
            AND (tpi.supplier = %(supplier)s OR %(supplier)s IS NULL OR %(supplier)s = '')
            AND (tpi.currency = %(currency)s OR %(currency)s IS NULL OR %(currency)s = '')
            AND (tge.against = %(account)s OR %(account)s IS NULL OR %(account)s = '')
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
        if not filters.get("currency"):
            conditions["currency"] = None
        if not filters.get("account"):
            conditions["account"] = None
    return conditions


def validate_dates(filters):
    if filters.start_date > filters.end_date:
        frappe.throw(_("From Date must be before To Date"))
