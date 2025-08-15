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
            "label": "Diễn giải",
            "fieldname": "DIEN_GIAI",
            "fieldtype": "Data",
        },
        {
            "label": "Mã KH",
            "fieldname": "MA_KH",
            "fieldtype": "Data",
        },
        {
            "label": "Tên KH",
            "fieldname": "TEN_KH",
            "fieldtype": "Data",
        },
        {
            "label": "Số hiệu TK",
            "fieldname": "TK",
            "fieldtype": "Data",
        },
        {
            "label": "TK Đối ứng",
            "fieldname": "DOI_UNG",
            "fieldtype": "Data",
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
        {
            "label": "ĐV hạch toán",
            "fieldname": "DV_HACH_TOAN",
            "fieldtype": "Data",
        },
        {
            "label": "Ghi chú",
            "fieldname": "GHI_CHU",
            "fieldtype": "Data",
        },
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    data = frappe.db.sql(
        """
        SELECT 
          DATE_FORMAT(GL.POSTING_DATE, '%%d/%%m/%%Y') NGAY_GHI_SO,
          GL.NAME SO_CHUNG_TU, 
          GL.REMARKS DIEN_GIAI, 
          NULL MA_KH,
          GL.PARTY TEN_KH,
          SUBSTRING_INDEX(GL.AGAINST, ' -', 1) TK,
          SUBSTRING_INDEX(GL.ACCOUNT, ' -', 1) DOI_UNG, 
          GL.CREDIT_IN_ACCOUNT_CURRENCY NO, 
          GL.DEBIT_IN_ACCOUNT_CURRENCY CO,
          NULL DV_HACH_TOAN,
          GL._comments GHI_CHU
        from 
          `tabGL Entry` GL 
          LEFT JOIN `tabCustomer` C ON C.NAME = GL.PARTY
        WHERE 
          (GL.AGAINST = %(account)s OR %(account)s IS NULL OR %(account)s = '')
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
