# Copyright (c) 2024, lamnl and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    if not filters:
        filters = {}

    # Define columns
    columns = get_columns()

    # SQL query with parameters from filters
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {
            "label": "Công đoạn",
            "fieldname": "operation",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Ca",
            "fieldname": "shift",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "SL ngày",
            "fieldname": "output_qty",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Sản lượng lũy kế ",
            "fieldname": "output_qty_cumulative",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": "Phế luỹ kế",
            "fieldname": "scrap_qty_cumulative",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": "Tỷ lệ phế theo ca sx",
            "fieldname": "scrap_rate",
            "fieldtype": "Data",
            "width": 100,
        },
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    data = frappe.db.sql(
        """
        WITH output_qty_day AS (
        SELECT
            tojc.`date` AS full_date,
            tjc.operation,
            tojc.employee,
            SUM(tojcp.second_qty) AS second_qty
        FROM
            `tabOperation Job Card Pallets` tojcp
        LEFT JOIN `tabOperation Job Card` tojc ON
            tojc.name = tojcp.parent
        LEFT JOIN `tabJob Card` tjc ON
            tjc.name = tojc.job_card_name
        WHERE
            tjc.operation IN ('CONGDOANCAT', 'CONGDOANTHOI')
            AND tojc.`date` = DATE(%(date)s)
        GROUP BY
            tjc.operation,
            tojc.employee
        ),
        output_qty_cumulative AS (
        SELECT
            tjc.operation,
            tojc.employee,
            SUM(tojcp.second_qty) AS second_qty
        FROM
            `tabOperation Job Card Pallets` tojcp
        LEFT JOIN `tabOperation Job Card` tojc ON
            tojc.name = tojcp.parent
        LEFT JOIN `tabJob Card` tjc ON
            tjc.name = tojc.job_card_name
        WHERE
            tjc.operation IN ('CONGDOANCAT', 'CONGDOANTHOI')
            AND tojc.`date` BETWEEN LAST_DAY(DATE(%(date)s)) - INTERVAL 1 MONTH + INTERVAL 1 DAY AND DATE(%(date)s)
        GROUP BY
            tjc.operation,
            tojc.employee
        ),
        scrap_qty_cumulative AS (
        SELECT
            tsijc.operation,
            tsijc.employee,
            SUM(tjcsi.stock_qty) AS stock_qty
        FROM
            `tabJob Card Scrap Item` tjcsi
        LEFT JOIN `tabScrap Items Job Card` tsijc ON
            tsijc.name = tjcsi.parent
        WHERE
            tsijc.operation IN ('CONGDOANCAT', 'CONGDOANTHOI')
            AND tsijc.`date` BETWEEN LAST_DAY(DATE(%(date)s)) - INTERVAL 1 MONTH + INTERVAL 1 DAY AND DATE(%(date)s)
        GROUP BY
            tsijc.operation,
            tsijc.employee
        ),
        detail_data AS (
        SELECT
            CASE 
                WHEN tjc.operation = 'CONGDOANTHOI' THEN 'Thổi'
                WHEN tjc.operation = 'CONGDOANCAT' THEN 'Cắt'
            END AS operation,
            te.first_name AS 'shift',
            oqd.second_qty AS output_qty,
            oqc.second_qty AS output_qty_cumulative,
            sqc.stock_qty AS scrap_qty_cumulative,
            sqc.stock_qty / (sqc.stock_qty + oqc.second_qty) AS scrap_rate
        FROM
            `tabOperation Job Card` tojc
        LEFT JOIN `tabJob Card` tjc ON
            tjc.name = tojc.job_card_name
        LEFT JOIN tabEmployee te ON
            te.name = tojc.employee
        LEFT JOIN output_qty_day AS oqd ON 
            oqd.full_date = tojc.`date`
            AND oqd.operation = tjc.operation
            AND oqd.employee = tojc.employee
        LEFT JOIN output_qty_cumulative AS oqc ON 
            oqc.operation = tjc.operation
            AND oqc.employee = tojc.employee
        LEFT JOIN scrap_qty_cumulative AS sqc ON 
            sqc.operation = tjc.operation
            AND sqc.employee = tojc.employee
        WHERE
            tjc.operation IN ('CONGDOANCAT', 'CONGDOANTHOI')
            AND tojc.`date` = DATE(%(date)s)
        GROUP BY
            tjc.operation,
            tojc.employee
        ),
        summary_data AS (
        SELECT
            operation,
            NULL AS shift, 
            SUM(output_qty) AS output_qty,
            SUM(output_qty_cumulative) AS output_qty_cumulative,
            SUM(scrap_qty_cumulative) AS scrap_qty_cumulative,
            SUM(scrap_qty_cumulative) / (SUM(scrap_qty_cumulative) + SUM(output_qty_cumulative)) AS scrap_rate
        FROM
            detail_data
        GROUP BY
            operation
        ),
        combine_data AS (
        SELECT
            *
        FROM
            detail_data
        UNION ALL
        SELECT
            *
        FROM
            summary_data
        ORDER BY
            operation,
            CASE
                WHEN shift IS NULL THEN 1
                ELSE 0
            END
        )
        SELECT
            operation,
            shift,
            output_qty,
            output_qty_cumulative,
            scrap_qty_cumulative,
            CONCAT(ROUND(scrap_rate * 100, 1), '%%') AS scrap_rate
        FROM
            combine_data
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
