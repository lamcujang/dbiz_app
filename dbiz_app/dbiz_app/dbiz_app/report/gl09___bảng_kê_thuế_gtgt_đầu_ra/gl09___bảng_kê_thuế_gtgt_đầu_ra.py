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
            "label": "Loại thuế",
            "fieldname": "tax_type",
            "fieldtype": "Data",
        },
        {
            "label": "Mã hóa đơn",
            "fieldname": "name",
            "fieldtype": "Data",
        },
        {
            "label": "Ngày lập hóa đơn",
            "fieldname": "posting_date",
            "fieldtype": "Data",
        },
        {
            "label": "Người mua",
            "fieldname": "customer_name",
            "fieldtype": "Data",
        },
        {
            "label": "Mã số thuế",
            "fieldname": "tax_id",
            "fieldtype": "Data",
        },
        {
            "label": "Doanh thu chưa có thuế GTGT",
            "fieldname": "total",
            "fieldtype": "Float",
        },
        {
            "label": "Thuế GTGT",
            "fieldname": "total_taxes_and_charges",
            "fieldtype": "Float",
        },
        {
            "label": "Đơn vị",
            "fieldname": "unit",
            "fieldtype": "Data",
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
            tsi.taxes_and_charges AS tax_type,
            tsi.name,
            DATE_FORMAT(tsi.posting_date, '%%d/%%m/%%Y') AS posting_date,
            tsi.customer_name,
            tc.tax_id,
            ROUND(tsi.total) AS total,
            ROUND(tsi.total_taxes_and_charges) AS total_taxes_and_charges,
            NULL AS unit,
            tsi.`_comments` AS comments,
            1 AS sort_order
        FROM
            `tabSales Invoice` tsi
        LEFT JOIN tabCustomer tc ON
            tc.name = tsi.customer
        WHERE
            tsi.docstatus = 1
            AND tsi.posting_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
            AND tsi.company = %(company)s
            AND (tsi.currency = %(currency)s OR %(currency)s IS NULL OR %(currency)s = '')
        UNION ALL
        SELECT
            tsi.taxes_and_charges AS tax_type,
            NULL AS name,
            NULL AS posting_date,
            NULL AS customer_name,
            'Tổng:' AS tax_id,
            ROUND(SUM(tsi.total)) AS total,
            ROUND(SUM(tsi.total_taxes_and_charges)) AS total_taxes_and_charges,
            NULL AS unit,
            NULL AS comments,
            1 AS sort_order
        FROM 
            `tabSales Invoice` tsi
        LEFT JOIN 
            tabCustomer tc ON
            tc.name = tsi.customer
        WHERE
            tsi.docstatus = 1
            AND tsi.posting_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
            AND tsi.company = %(company)s
            AND (tsi.currency = %(currency)s OR %(currency)s IS NULL OR %(currency)s = '')
        GROUP BY
            tsi.taxes_and_charges
        UNION ALL
        SELECT
            NULL AS tax_type,
            NULL AS name,
            NULL AS posting_date,
            NULL AS customer_name,
            'Tổng doanh thu hàng hóa, dịch vụ bán ra' AS tax_id,
            ROUND(SUM(tsi.total)) AS total,
            NULL AS total_taxes_and_charges,
            NULL AS unit,
            NULL AS comments,
            2 AS sort_order
        FROM 
            `tabSales Invoice` tsi
        LEFT JOIN 
            tabCustomer tc ON
            tc.name = tsi.customer
        WHERE
            tsi.docstatus = 1
            AND tsi.posting_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
            AND tsi.company = %(company)s
            AND (tsi.currency = %(currency)s OR %(currency)s IS NULL OR %(currency)s = '')
        UNION ALL
        SELECT
            NULL AS tax_type,
            NULL AS name,
            NULL AS posting_date,
            NULL AS customer_name,
            'Tổng thuế GTGT của hàng hóa, dịch vụ bán ra' AS tax_id,
            ROUND(SUM(tsi.total_taxes_and_charges)) AS total,
            NULL AS total_taxes_and_charges,
            NULL AS unit,
            NULL AS comments,
            2 AS sort_order
        FROM 
            `tabSales Invoice` tsi
        LEFT JOIN 
            tabCustomer tc ON
            tc.name = tsi.customer
        WHERE
            tsi.docstatus = 1
            AND tsi.posting_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
            AND tsi.company = %(company)s
            AND (tsi.currency = %(currency)s OR %(currency)s IS NULL OR %(currency)s = '')
        UNION ALL
        SELECT
            NULL AS tax_type,
            NULL AS name,
            NULL AS posting_date,
            NULL AS customer_name,
            'Tổng doanh thu hàng hóa, dịch vụ bán ra chịu thuế GTGT' AS tax_id,
            ROUND(SUM(tsi.total) + SUM(tsi.total_taxes_and_charges)) AS total,
            NULL AS total_taxes_and_charges,
            NULL AS unit,
            NULL AS comments,
            2 AS sort_order
        FROM 
            `tabSales Invoice` tsi
        LEFT JOIN 
            tabCustomer tc ON
            tc.name = tsi.customer
        WHERE
            tsi.docstatus = 1
            AND tsi.posting_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
            AND tsi.company = %(company)s
            AND (tsi.currency = %(currency)s OR %(currency)s IS NULL OR %(currency)s = '')
        ORDER BY
            sort_order,
            tax_type,
            posting_date DESC
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
        if not filters.get("currency"):
            conditions["currency"] = None
    return conditions


def validate_dates(filters):
    if filters.start_date > filters.end_date:
        frappe.throw(_("From Date must be before To Date"))
