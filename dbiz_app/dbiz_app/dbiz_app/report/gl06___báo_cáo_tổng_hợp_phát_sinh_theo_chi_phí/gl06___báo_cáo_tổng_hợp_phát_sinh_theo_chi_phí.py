# Copyright (c) 2024, lamnl and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):  # -> tuple[list[Any], list[Any]]:
    if not filters:
        filters = {}

    if filters.start_date > filters.end_date:
        frappe.throw(_("From Date must be before To Date"))

    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "label": "Mã TK",
            "fieldname": "MA_TK",
            "fieldtype": "Data",
        },
        {
            "label": "Tên TK",
            "fieldname": "TEN_TK",
            "fieldtype": "Data",
        },
        {
            "label": "Ngày ghi sổ",
            "fieldname": "NGAY_GHI_SO",
            "fieldtype": "Data",
        },
        {
            "label": "Số chứng từ",
            "fieldname": "SO_CHUNG_TU",
            "fieldtype": "Data",
        },
        {
            "label": "Chứng từ ghi sổ",
            "fieldname": "CHUNG_TU_GHI_SO",
            "fieldtype": "Data",
        },
        {
            "label": "Diễn giải",
            "fieldname": "DIEN_GIAI",
            "fieldtype": "Data",
        },
        {
            "label": "Số tiền",
            "fieldname": "SO_TIEN",
            "fieldtype": "Float",
        },
        {
            "label": "Phát sinh nợ",
            "fieldname": "NO",
            "fieldtype": "Float",
        },
        {
            "label": "Phát sinh có",
            "fieldname": "CO",
            "fieldtype": "Float",
        },
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    data = frappe.db.sql(
        """
        SELECT 
          SUBSTRING_INDEX(GL.ACCOUNT, ' -', 1) MA_TK,
          TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(GL.ACCOUNT, ' -', 2), ' -', -1)) TEN_TK,
          DATE_FORMAT(GL.CREATION, '%%e/%%c/%%Y') NGAY_GHI_SO,
          GL.VOUCHER_NO SO_CHUNG_TU, 
          DATE_FORMAT(GL.POSTING_DATE, '%%e/%%c/%%Y') CHUNG_TU_GHI_SO,
          GL.REMARKS DIEN_GIAI,
          GL.DEBIT - GL.CREDIT SO_TIEN,
          GL.CREDIT NO, 
          GL.DEBIT CO
        from 
          `tabGL Entry` GL 
          LEFT JOIN `tabCustomer` C ON C.CUSTOMER_NAME = GL.PARTY
        WHERE 
          (GL.ACCOUNT = %(account)s OR %(account)s IS NULL OR %(account)s = '')
          AND IS_CANCELLED = 0
          AND POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
          AND COMPANY = %(company)s
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
