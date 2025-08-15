# Copyright (c) 2025, lamnl and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
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
            "label": "Ngày phiếu nhập",
            "fieldname": "posting_date",
            "fieldtype": "Date",
        },
        {
            "label": "Số phiếu nhập",
            "fieldname": "name",
            "fieldtype": "Data",
        },
        {
            "label": "Mã khách hàng",
            "fieldname": "supplier",
            "fieldtype": "Data",
        },
        {
            "label": "Tên khách hàng",
            "fieldname": "supplier_name",
            "fieldtype": "Data",
        },
        {
            "label": "Diễn giải",
            "fieldname": "remarks",
            "fieldtype": "Data",
        },
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    # INV12
    data = frappe.db.sql(
        """
           SELECT 
                tpr.posting_date, 
                tpr.name, 
                tpr.supplier,  
                tpr.supplier_name, 
                tpr.remarks
            FROM 
                `tabPurchase Receipt` tpr 
            LEFT JOIN 
                `tabPurchase Receipt Item` tpri 
            ON
                tpr.name = tpri.parent 
            WHERE 
                tpri.purchase_invoice IS NULL
                and tpr.posting_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
                and tpr.company =  %(company)s
                and (tpri.expense_account = %(account)s OR %(account)s IS NULL OR %(account)s = '')
            GROUP BY tpr.name 
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
