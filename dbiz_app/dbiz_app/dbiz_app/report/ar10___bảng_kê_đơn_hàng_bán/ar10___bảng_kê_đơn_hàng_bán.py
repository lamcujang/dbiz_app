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
            "label": "Ca bán hàng",
            "fieldname": "ca_ban_hang",
            "fieldtype": "Data",
        },
        {
            "label": "POS (Outlet)",
            "fieldname": "pos",
            "fieldtype": "Data",
        },
        {
            "label": "Loại đơn hàng bán",
            "fieldname": "order_type",
            "fieldtype": "Data",
        },
        {
            "label": "Số CT",
            "fieldname": "name",
            "fieldtype": "Data",
        },
        {
            "label": "Ghi chú",
            "fieldname": "note",
            "fieldtype": "Data",
        },
        {
            "label": "Diễn giải",
            "fieldname": "description",
            "fieldtype": "Data",
        },
        {
            "label": "Mã SP",
            "fieldname": "item_code",
            "fieldtype": "Data",
        },
        {"label": "SL", "fieldname": "qty", "fieldtype": "Float",},
        {
            "label": "Giá bán",
            "fieldname": "rate",
            "fieldtype": "Float",
        },
        {
            "label": "Tiền bán hàng",
            "fieldname": "net_amount",
            "fieldtype": "Float",
        },
        {
            "label": "Thuế",
            "fieldname": "tax_amount",
            "fieldtype": "Float",
        },
        {
            "label": "Giá vốn",
            "fieldname": "gia_von",
            "fieldtype": "Float",
        },
        {
            "label": "Tiền vốn",
            "fieldname": "tien_von",
            "fieldtype": "Float",
        },
        {
            "label": "Mã KH",
            "fieldname": "customer_code",
            "fieldtype": "Data",
        },
        {
            "label": "Tên KH",
            "fieldname": "customer_name",
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
        GROUP BY
            tsoi.item_code
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
            NULL AS ca_ban_hang,
            NULL AS pos,
            tso.order_type,
            tso.name,
            NULL AS note,
            tsoi.description AS description,
            ti.item_code AS item_code,
            tsoi.qty,
            tsoi.rate,
            tsoi.amount AS net_amount,
            COALESCE(TA.allocated_tax_to_item, 0) AS tax_amount,
            '' AS gia_von,
            '' AS tien_von,
            tc.name AS customer_code,
            tc.customer_name
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
        WHERE
            tsoi.transaction_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
            AND tso.company = %(company)s
        ORDER BY
            tso.name ASC
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
