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
            "label": "Ngày xuất theo y/c Khách hàng",
            "fieldname": "delivery_date",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Ngày dự kiến xuất của nhà máy",
            "fieldname": "export_cont_date",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Khách hàng",
            "fieldname": "customer",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "TBSX",
            "fieldname": "production_plan",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Tên hàng",
            "fieldname": "production_item",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "PO",
            "fieldname": "po",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "BTP sx trong tháng",
            "fieldname": "btp_month",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": "Số hộp còn trong kho (t.kê)",
            "fieldname": "stock_qty",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": "Hàng đã xuất (Hộp)",
            "fieldname": "exported_qty",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": "KHSX (Hộp)",
            "fieldname": "planned_qty_carton",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": "KHSX (TL/Hộp)",
            "fieldname": "net_kgs_per_carton",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": "KHSX (Kg)",
            "fieldname": "planned_qty_kg",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": "Đầu kỳ (TP)",
            "fieldname": "opening_qty_tp",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": "Đầu kỳ (BTP)",
            "fieldname": "opening_qty_btp",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": "Sản xuất trong tháng (Hộp)",
            "fieldname": "produced_qty_carton",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": "Sản xuất trong tháng (Kg)",
            "fieldname": "produced_qty_kg",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": "Thiếu KH (Hộp)",
            "fieldname": "shortage_qty_carton",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": "Thiếu KH (Kg)",
            "fieldname": "shortage_qty_kg",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": "%% hoàn thành kế hoạch",
            "fieldname": "percentage",
            "fieldtype": "Data",
            "width": 80,
        },
        {
            "label": "Tình trạng/Ghi chú",
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 100,
        },
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    data = frappe.db.sql(
        """
        WITH ranked_entries AS (
        SELECT
            tsle.item_code,
            tsle.qty_after_transaction,
            ROW_NUMBER() OVER (PARTITION BY tsle.item_code
        ORDER BY
            tsle.name DESC) AS row_num,
            ROW_NUMBER() OVER (PARTITION BY tsle.item_code
        ORDER BY
            tsle.name ASC) AS row_num_desc
        FROM
            `tabStock Ledger Entry` tsle
        WHERE
            tsle.posting_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
            AND tsle.warehouse = 'Kho TP - S'
        ),
        stock_balance AS (
        SELECT
            re.item_code,
            re.qty_after_transaction
        FROM
            ranked_entries re
        WHERE
            re.row_num = 1
        ),
        opening_stock_balance AS (
        SELECT
            re.item_code,
            re.qty_after_transaction
        FROM
            ranked_entries re
        WHERE
            re.row_num_desc = 1
        ),
        exported_qty AS (
        SELECT
            tdni.item_code,
            SUM(tdni.qty) AS qty
        FROM
            `tabDelivery Note Item` tdni
        GROUP BY
            tdni.item_code
        ),
        produced_qty AS (
        SELECT
            tojcp.item_code,
            SUM(tojcp.qty) AS qty,
            SUM(tojcp.second_qty) AS second_qty
        FROM
            `tabOperation Job Card Pallets` tojcp
        LEFT JOIN `tabOperation Job Card` tojc ON
            tojc.name = tojcp.parent
        LEFT JOIN `tabJob Card` tjc ON
            tjc.name = tojc.job_card_name
        WHERE
            tojc.job_card_operation_name = 'DONGTHUNG'
            AND tojc.`date` BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
        GROUP BY
                tojcp.item_code
        )
        SELECT
            DATE_FORMAT(tso.delivery_date, '%%d/%%m/%%Y') AS delivery_date,
            DATE_FORMAT(two.export_cont_date, '%%d/%%m/%%Y') AS export_cont_date,
            tso.customer,
            two.production_plan,
            tjc.production_item,
            tso.name AS po,
            NULL AS btp_month,
            sb.qty_after_transaction AS in_stock,
            eq.qty AS exported_qty,
            tsoi.qty AS planned_qty_carton,
            ti.net_kgs_per_carton,
            tsoi.qty * ti.net_kgs_per_carton AS planned_qty_kg,
            osb.qty_after_transaction AS opening_qty_tp,
            NULL AS opening_qty_btp,
            pq.qty AS produced_qty_carton,
            pq.second_qty AS produced_qty_kg,
            NULL AS shortage_qty_carton,
            NULL AS shortage_qty_kg,
            NULL AS percentage,
            two.status
        FROM
            `tabJob Card` tjc
        LEFT JOIN `tabWork Order` two ON
            two.name = tjc.work_order
        LEFT JOIN `tabSales Order` tso ON
            tso.name = tjc.job_card_sales_order
        LEFT JOIN `tabSales Order Item` tsoi ON
            tsoi.parent = tso.name
        LEFT JOIN tabItem ti ON
            ti.name = tjc.production_item
        LEFT JOIN `tabOperation Job Card` tojc ON
            tojc.job_card_name = tjc.name
        LEFT JOIN `tabOperation Job Card Pallets` tojcp ON
            tojcp.parent = tojc.name
        LEFT JOIN stock_balance sb ON
            sb.item_code = tjc.production_item
        LEFT JOIN opening_stock_balance osb ON
            osb.item_code = tjc.production_item
        LEFT JOIN exported_qty eq ON
            eq.item_code = tjc.production_item
        LEFT JOIN produced_qty pq ON
            pq.item_code = tjc.production_item
        WHERE
            tojc.job_card_operation_name = 'DONGTHUNG'
            AND (tjc.production_item  = %(item)s OR %(item)s IS NULL OR %(item)s = '')
        GROUP BY
            two.production_plan,
            tso.name,
            tjc.production_item
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
        if not filters.get("item"):
            conditions["item"] = None
    return conditions


def validate_dates(filters):
    if filters.start_date > filters.end_date:
        frappe.throw(_("From Date must be before To Date"))
