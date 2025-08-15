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
            "label": "Số hóa đơn",
            "fieldname": "invoice_no",
            "fieldtype": "Data",
        },
        {
            "label": "Ngày lập hóa đơn",
            "fieldname": "posting_date",
            "fieldtype": "Data",
        },
        {
            "label": "Tên người bán",
            "fieldname": "supplier_name",
            "fieldtype": "Data",
        },
        {
            "label": "Mã số thuế",
            "fieldname": "tax_id",
            "fieldtype": "Data",
        },
        {
            "label": "Giá trị HHDV mua vào chưa có thuế",
            "fieldname": "total",
            "fieldtype": "Float",
        },
        {
            "label": "Thuế GTGT đủ điều kiện khấu trừ thuế",
            "fieldname": "total_taxes_and_charges",
            "fieldtype": "Float",
        },
        {
            "label": "Đơn vị",
            "fieldname": "unit",
            "fieldtype": "Data",
        },
        {
            "label": "Số chứng từ",
            "fieldname": "name",
            "fieldtype": "Data",
        },
        {
            "label": "Ghi chú",
            "fieldname": "remarks",
            "fieldtype": "Data",
        },
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    data = frappe.db.sql(
        """
        SELECT
            tpi.taxes_and_charges AS tax_type,
            NULL AS invoice_no,
            DATE_FORMAT(tpi.posting_date, '%%d/%%m/%%Y') AS posting_date,
            ts.supplier_name,
            ts.tax_id,
            ROUND(tpi.total) AS total,
            ROUND(tpi.total_taxes_and_charges) AS total_taxes_and_charges,
            NULL AS unit,
            tpi.name,
            tpi.remarks,
            1 AS sort_order
        FROM
            `tabPurchase Invoice` tpi
        LEFT JOIN tabSupplier ts ON
            ts.name = tpi.supplier
        WHERE
            tpi.docstatus = 1
            AND tpi.posting_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
            AND tpi.company = %(company)s
            AND (tpi.currency = %(currency)s OR %(currency)s IS NULL OR %(currency)s = '')
        UNION ALL
        SELECT
            tpi.taxes_and_charges AS tax_type,
            NULL AS invoice_no,
            NULL AS posting_date,
            NULL AS supplier_name,
            'Tổng:' AS tax_id,
            ROUND(SUM(tpi.total)) AS total,
            ROUND(SUM(tpi.total_taxes_and_charges)) AS total_taxes_and_charges,
            NULL AS unit,
            NULL AS name,
            NULL AS remarks,
            1 AS sort_order
        FROM 
            `tabPurchase Invoice` tpi
        LEFT JOIN 
            tabSupplier ts ON
            ts.name = tpi.supplier 
        WHERE
            tpi.docstatus = 1
            AND tpi.posting_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
            AND tpi.company = %(company)s
            AND (tpi.currency = %(currency)s OR %(currency)s IS NULL OR %(currency)s = '')
        GROUP BY
            tpi.taxes_and_charges
        UNION ALL
        SELECT
            NULL AS tax_type,
            NULL AS invoice_no,
            NULL AS posting_date,
            NULL AS supplier_name ,
            'Tổng doanh thu hàng hóa, dịch vụ mua vào' AS tax_id,
            ROUND(SUM(tpi.total)) AS total,
            NULL AS total_taxes_and_charges,
            NULL AS unit,
            NULL AS name,
            NULL AS remarks,
            2 AS sort_order
        FROM 
            `tabPurchase Invoice` tpi
        LEFT JOIN 
            tabSupplier ts ON
            ts.name = tpi.supplier
        WHERE
            tpi.docstatus = 1
            AND tpi.posting_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
            AND tpi.company = %(company)s
            AND (tpi.currency = %(currency)s OR %(currency)s IS NULL OR %(currency)s = '')
        UNION ALL
        SELECT
            NULL AS tax_type,
            NULL AS invoice_no,
            NULL AS posting_date,
            NULL AS supplier_name,
            'Tổng thuế GTGT của hàng hóa, dịch vụ mua vào' AS tax_id,
            ROUND(SUM(tpi.total_taxes_and_charges)) AS total,
            NULL AS total_taxes_and_charges,
            NULL AS unit,
            NULL AS name,
            NULL AS remarks,
            2 AS sort_order
        FROM 
            `tabPurchase Invoice` tpi
        LEFT JOIN 
            tabSupplier ts ON
            ts.name = tpi.supplier
        WHERE
            tpi.docstatus = 1
            AND tpi.posting_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
            AND tpi.company = %(company)s
            AND (tpi.currency = %(currency)s OR %(currency)s IS NULL OR %(currency)s = '')
        UNION ALL
        SELECT
            NULL AS tax_type,
            NULL AS invoice_no,
            NULL AS posting_date,
            NULL AS supplier_name,
            'Tổng doanh thu hàng hóa, dịch vụ bán ra chịu thuế GTGT' AS tax_id,
            ROUND(SUM(tpi.total) + SUM(tpi.total_taxes_and_charges)) AS total,
            NULL AS total_taxes_and_charges,
            NULL AS unit,
            NULL AS name,
            NULL AS remarks,
            2 AS sort_order
        FROM 
            `tabPurchase Invoice` tpi
        LEFT JOIN 
            tabSupplier ts ON
            ts.name = tpi.supplier 
        WHERE
            tpi.docstatus = 1
            AND tpi.posting_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
            AND tpi.company = %(company)s
            AND (tpi.currency = %(currency)s OR %(currency)s IS NULL OR %(currency)s = '')
        ORDER BY
            sort_order,
            tax_type,
            posting_date DESC;
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
