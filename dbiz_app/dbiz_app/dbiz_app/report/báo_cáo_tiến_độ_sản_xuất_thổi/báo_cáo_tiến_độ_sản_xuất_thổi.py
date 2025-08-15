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
            "label": "Ngày dự kiến xuất theo khách hàng",
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
            "label": "Kế hoạch",
            "fieldname": "planned_qty",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": "Tồn+thổi",
            "fieldname": "in_stock",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": "Sản xuất trong tháng",
            "fieldname": "produced_qty",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": "Thiếu KH",
            "fieldname": "shortage_qty",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": "Tình trạng",
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Máy thổi",
            "fieldname": "workstation",
            "fieldtype": "Data",
            "width": 100,
        },
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    data = frappe.db.sql(
        """
        WITH planned_produced_qty AS (
        SELECT
            tjc.production_item,
            ROUND(SUM(tjc.for_quantity)) AS for_quantity,
            ROUND(SUM(tjc.total_completed_qty)) AS total_completed_qty
        FROM
            `tabJob Card` tjc
        WHERE
            tjc.operation = 'CONGDOANTHOI'
            AND tjc.posting_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
        GROUP BY
            tjc.production_item
        )
        SELECT
            tso.delivery_date,
            two.export_cont_date,
            tso.customer,
            two.production_plan,
            tjc.production_item,
            ppq.for_quantity AS planned_qty,
            NULL AS in_stock,
            ppq.total_completed_qty AS produced_qty,
            NULL AS shortage_qty,
            CASE
                WHEN tjc.status = 'Completed' THEN 'Xong'
                ELSE 'Chưa xong'
            END AS status,
            tjc.workstation
        FROM
            `tabJob Card` tjc
        LEFT JOIN `tabSales Order` tso ON
            tso.name = tjc.job_card_sales_order
        LEFT JOIN `tabWork Order` two ON
            two.name = tjc.work_order
        LEFT JOIN planned_produced_qty ppq ON
            ppq.production_item = tjc.production_item
        WHERE
            tjc.operation = 'CONGDOANTHOI'
            AND tjc.posting_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
            AND (tjc.production_item = %(item)s OR %(item)s IS NULL OR %(item)s = '')
        GROUP BY
            two.production_plan,
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
