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
            "label": "Ngày CT",
            "fieldname": "transaction_date",
            "fieldtype": "Data",
        },
        {
            "label": "Loại hoá đơn",
            "fieldname": "invoice_type",
            "fieldtype": "Data",
        },
        {
            "label": "Số hoá đơn",
            "fieldname": "invoice_no",
            "fieldtype": "Data",
        },
        {
            "label": "Số đơn hàng",
            "fieldname": "order_no",
            "fieldtype": "Data",
        },
        {
            "label": "Mã sản phẩm",
            "fieldname": "item_code",
            "fieldtype": "Data",
        },
        {
            "label": "Tên sản phẩm",
            "fieldname": "item_name",
            "fieldtype": "Data",
        },
        {
            "label": "ĐVT",
            "fieldname": "stock_uom",
            "fieldtype": "Data",
        },
        {
            "label": "Giá bán",
            "fieldname": "base_price_list_rate",
            "fieldtype": "Float",
        },
        {
            "label": "SL",
            "fieldname": "qty",
            "fieldtype": "Float",
        },
        {
            "label": "Thành tiền (Chưa thuế)",
            "fieldname": "net_amount",
            "fieldtype": "Float",
        },
        {
            "label": "Tiền thuế",
            "fieldname": "tax_amount",
            "fieldtype": "Float",
        },
        {
            "label": "Thành tiền (Sau thuế)",
            "fieldname": "total_amount",
            "fieldtype": "Float",
        },
        {
            "label": "Mã khách hàng",
            "fieldname": "customer_code",
            "fieldtype": "Data",
        },
        {
            "label": "Người mua",
            "fieldname": "customer_type",
            "fieldtype": "Data",
        },
        {
            "label": "Người bán",
            "fieldname": "company",
            "fieldtype": "Data",
        },
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    data = frappe.db.sql(
        """
        WITH Total_Taxes AS (
            SELECT
                tstac.parent AS sales_order_id,
                SUM(tstac.tax_amount) AS total_tax_amount
        FROM
            `tabSales Taxes and Charges` tstac
        GROUP BY
            tstac.parent
        ),
        Item_Totals AS (
        SELECT
            tsoi.parent AS sales_order_id,
            tsoi.item_code,
            tsoi.qty,
            tsoi.base_net_amount AS item_net_amount,
            (tsoi.base_net_amount / (
            SELECT
                SUM(tsoi2.base_net_amount)
            FROM
                `tabSales Order Item` tsoi2
            WHERE
                tsoi2.parent = tsoi.parent)) AS allocation_percentage
        FROM
            `tabSales Order Item` tsoi
        LEFT JOIN `tabSales Order` tso ON
            tso.name = tsoi.parent
        WHERE
            tsoi.transaction_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
            AND tso.company = %(company)s
        ),
        TAX_ALLOCATION AS (
        SELECT
            it.sales_order_id,
            it.item_code,
            it.qty,
            it.item_net_amount,
            it.allocation_percentage,
            tt.total_tax_amount,
            (it.allocation_percentage * tt.total_tax_amount) AS allocated_tax_to_item
        FROM
            Item_Totals it
        LEFT JOIN Total_Taxes tt ON
            it.sales_order_id = tt.sales_order_id
        )
        SELECT
            DATE_FORMAT(tsoi.transaction_date, '%%d/%%m/%%Y') AS transaction_date,
            'Hoá đơn bán hàng (Nhập thủ công)' AS invoice_type,
            tsi.name AS invoice_no,
            tso.name AS order_no,
            ti.item_code,
            ti.item_name,
            ti.stock_uom,
            tsoi.base_price_list_rate,
            tsoi.qty,
            tsoi.net_amount,
            COALESCE(TA.allocated_tax_to_item, 0) AS tax_amount,
            tsoi.net_amount + COALESCE(TA.allocated_tax_to_item, 0) AS total_amount,
            tso.customer AS customer_code,
            tc.customer_type,
            tso.company
        FROM
            `tabSales Order Item` tsoi
        LEFT JOIN `tabSales Order` tso ON
            tso.name = tsoi.parent
        LEFT JOIN `tabItem` ti ON
            ti.item_code = tsoi.item_code
        LEFT JOIN TAX_ALLOCATION TA ON
            TA.sales_order_id = tsoi.parent
            AND TA.item_code = tsoi.item_code
        LEFT JOIN `tabCustomer` tc ON
            tc.name = tso.customer
        LEFT JOIN `tabSales Invoice` tsi ON
            tsi.customer = tc.name
        WHERE
            tsoi.transaction_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
            AND tso.company = %(company)s
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
