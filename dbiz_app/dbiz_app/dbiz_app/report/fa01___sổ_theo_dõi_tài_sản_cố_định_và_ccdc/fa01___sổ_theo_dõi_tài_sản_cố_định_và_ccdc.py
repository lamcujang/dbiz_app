# Copyright (c) 2025, lamnl and contributors
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
            "label": "Mã chứng từ ghi tăng",
            "fieldname": "Mã chứng từ ghi tăng",
            "fieldtype": "Data",
        },
        {
            "label": "Thời gian ghi tăng",
            "fieldname": "Thời gian ghi tăng",
            "fieldtype": "Date",
        },
        {
            "label": "Tên, nhãn hiệu, quy cách tài sản cố định và công cụ, dụng cụ",
            "fieldname": "Tên, nhãn hiệu, quy cách tài sản cố định và công cụ, dụng cụ",
            "fieldtype": "Data",
        },
        {
            "label": "Đơn vị",
            "fieldname": "Đơn vị",
            "fieldtype": "Data",
        },
        {
            "label": "Số lượng ghi tăng",
            "fieldname": "Số lượng ghi tăng",
            "fieldtype": "Float",
        },
        {
            "label": "Đơn giá ghi tăng",
            "fieldname": "Đơn giá ghi tăng",
            "fieldtype": "Float",
        },
        {
            "label": "Số tiền ghi tăng",
            "fieldname": "Số tiền ghi tăng",
            "fieldtype": "Float",
        },
        {
            "label": "Số hiệu ghi giảm",
            "fieldname": "Số hiệu ghi giảm",
            "fieldtype": "Data",
        },
        {
            "label": "Lý do",
            "fieldname": "Lý do",
            "fieldtype": "Data",
        },
        {
            "label": "Số lượng ghi giảm",
            "fieldname": "Số lượng ghi giảm",
            "fieldtype": "Float",
        },
        {
            "label": "Số tiền ghi giảm",
            "fieldname": "Số tiền ghi giảm",
            "fieldtype": "Float",
        },
        {
            "label": "Ghi chú",
            "fieldname": "Ghi chú",
            "fieldtype": "Data",
        },
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    data = frappe.db.sql(
        """
        SELECT PURCHASE.NAME AS 'Mã chứng từ ghi tăng',
            PURCHASE.POSTING_DATE AS 'Thời gian ghi tăng',
            AST.NAME AS 'Tên, nhãn hiệu, quy cách tài sản cố định và công cụ, dụng cụ',
            PURCHASE.UOM AS 'Đơn vị',
            PURCHASE.QTY AS 'Số lượng ghi tăng',
            PURCHASE.AMOUNT/PURCHASE.QTY AS 'Đơn giá ghi tăng',
            PURCHASE.AMOUNT AS 'Số tiền ghi tăng',
            SALES.NAME AS 'Số hiệu ghi giảm',
            SALES.REMARKS AS 'Lý do',
            SALES.QTY AS 'Số lượng ghi giảm',
            SALES.AMOUNT AS 'Số tiền ghi giảm',
            PURCHASE.DESCRIPTION AS 'Ghi chú'
        FROM `tabAsset` AST
        LEFT JOIN
        (SELECT PR.NAME,
                PR.REMARKS,
                PRI.QTY,
                PRI.AMOUNT,
                PR.POSTING_DATE,
                PRI.DESCRIPTION,
                PRI.UOM,
                PRI.ITEM_CODE
        FROM `tabPurchase Receipt` PR
        LEFT JOIN `tabPurchase Receipt Item` PRI ON PRI.PARENT = PR.NAME
        WHERE PR.COMPANY = %(company)s
            AND PRI.IS_FIXED_ASSET = 1
            AND PR.POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)) PURCHASE ON PURCHASE.NAME = AST.PURCHASE_RECEIPT
        LEFT JOIN
        (SELECT SI.NAME,
                SI.REMARKS,
                SII.QTY,
                SII.AMOUNT,
                SII.ASSET,
                SI.POSTING_DATE
        FROM `tabSales Invoice` SI
        LEFT JOIN `tabSales Invoice Item` SII ON SII.PARENT = SI.NAME
        WHERE SI.COMPANY = %(company)s
            AND SI.POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)) SALES ON SALES.ASSET = AST.NAME
        WHERE (PURCHASE.POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
            OR SALES.POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s))
            AND AST.STATUS IN('Submitted', 'Partially Depreciated', 'Fully Depreciated', 'Sold', 'Scrapped')
        UNION ALL
        SELECT PURCHASE.NAME,
            PURCHASE.POSTING_DATE AS 'Thời gian ghi tăng',
            AST.NAME AS 'Tên, nhãn hiệu, quy cách tài sản cố định và công cụ, dụng cụ',
            PURCHASE.UOM AS 'Đơn vị',
            PURCHASE.QTY AS 'Số lượng ghi tăng',
            PURCHASE.AMOUNT/PURCHASE.QTY AS 'Đơn giá ghi tăng',
            PURCHASE.AMOUNT AS 'Số tiền ghi tăng',
            SALES.NAME AS 'Số hiệu ghi giảm',
            SALES.REMARKS AS 'Lý do',
            SALES.QTY AS 'Số lượng ghi giảm',
            SALES.AMOUNT AS 'Số tiền ghi giảm',
            PURCHASE.DESCRIPTION AS 'Ghi chú'
        FROM `tabAsset` AST
        LEFT JOIN
        (SELECT PI.NAME,
                PI.POSTING_DATE,
                PI.REMARKS,
                PII.QTY,
                PII.AMOUNT,
                PII.DESCRIPTION,
                PII.UOM,
                PII.ITEM_CODE
        FROM `tabPurchase Invoice` PI
        LEFT JOIN `tabPurchase Invoice Item` PII ON PII.PARENT = PI.NAME
        WHERE PI.COMPANY = %(company)s
            AND PII.IS_FIXED_ASSET = 1
            AND PI.UPDATE_STOCK = 1
            AND PI.POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)) PURCHASE ON PURCHASE.NAME = AST.PURCHASE_INVOICE
        LEFT JOIN
        (SELECT SI.NAME,
                SI.REMARKS,
                SII.QTY,
                SII.ASSET,
                SII.AMOUNT,
                SI.POSTING_DATE
        FROM `tabSales Invoice` SI
        LEFT JOIN `tabSales Invoice Item` SII ON SII.PARENT = SI.NAME
        WHERE SII.IS_FIXED_ASSET = 1
            AND SI.COMPANY = %(company)s
            AND SI.POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)) SALES ON SALES.ASSET = AST.NAME
        WHERE AST.STATUS IN('Submitted', 'Partially Depreciated', 'Fully Depreciated', 'Sold', 'Scrapped')
        AND (PURCHASE.POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
            OR SALES.POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s))
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
