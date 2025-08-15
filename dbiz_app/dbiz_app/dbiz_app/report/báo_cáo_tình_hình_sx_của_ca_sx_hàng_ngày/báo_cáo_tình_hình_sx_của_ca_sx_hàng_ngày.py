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
            "label": "Thứ",
            "fieldname": "day_of_week",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Tháng năm",
            "fieldname": "month_of_year",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Tuần năm",
            "fieldname": "week_of_year",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Ngày",
            "fieldname": "full_date",
            "fieldtype": "Data",
            "width": 100,
        },
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
            "label": "Nhân công",
            "fieldname": "staff",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Sản lượng",
            "fieldname": "output_qty",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": "Phế",
            "fieldname": "scrap_qty",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": "Tỷ lệ phế",
            "fieldname": "scrap_rate",
            "fieldtype": "Data",
            "width": 100,
        },
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    data = frappe.db.sql(
        """
        WITH output_qty AS (
        SELECT
            tjc.operation,
            tojc.employee,
            tojc.shift,
            tojc.`date` AS full_date,
            tojcp.second_qty
        FROM
            `tabOperation Job Card Pallets` tojcp
        LEFT JOIN `tabOperation Job Card` tojc ON
            tojc.name = tojcp.parent
        LEFT JOIN `tabJob Card` tjc ON
            tjc.name = tojc.job_card_name
        WHERE
            tjc.company = %(company)s
            AND tjc.operation IN (
                'CONGDOANCAT', 'CONGDOANTHOI'
            )
        GROUP BY
            tjc.operation,
            tojc.employee,
            tojc.shift,
            tojc.`date`
    ),
    scrap_qty AS (
        SELECT
            tsijc.shift,
            tsijc.employee,
            tsijc.operation,
            tsijc.`date` AS full_date,
            tjcsi.stock_qty
        FROM
            `tabJob Card Scrap Item` tjcsi
        LEFT JOIN `tabScrap Items Job Card` tsijc ON
            tsijc.name = tjcsi.parent
        WHERE
            tsijc.company = %(company)s
            AND tsijc.operation IN (
                'CONGDOANCAT', 'CONGDOANTHOI'
            )
        GROUP BY
                tsijc.operation,
                tsijc.employee,
                tsijc.shift,
                tsijc.`date`
    ),
    detail_data AS (
        SELECT
            DATE_FORMAT(tojc.`date`, '%%W', 'vi_VN') AS day_of_week,
            DATE_FORMAT(tojc.`date`, '%%y-M%%c') AS month_of_year,
            CONCAT(DATE_FORMAT(tojc.`date` + INTERVAL (WEEK(tojc.`date`, 3) = 1 AND MONTH(tojc.`date`) = 12) YEAR, '%%y'), '-W', WEEK(tojc.`date`, 3)) AS week_of_year,
            tojc.`date` AS full_date,
            CASE
                WHEN tjc.operation = 'CONGDOANTHOI' THEN 'Thổi'
                WHEN tjc.operation = 'CONGDOANCAT' THEN 'Cắt'
            END AS operation,
            SUBSTRING(tojc.shift, -1) AS shift,
            te.first_name AS staff,
            oq.second_qty AS output_qty,
            sq.stock_qty AS scrap_qty,
            sq.stock_qty / (
                sq.stock_qty + oq.second_qty
            ) AS scrap_rate
        FROM
            `tabOperation Job Card` tojc
        LEFT JOIN `tabJob Card` tjc ON
            tjc.name = tojc.job_card_name
        LEFT JOIN tabEmployee te ON
            te.name = tojc.employee
        LEFT JOIN output_qty oq ON
            oq.operation = tjc.operation
            AND oq.employee = tojc.employee
            AND oq.shift = tojc.shift
            AND oq.full_date = tojc.`date`
        LEFT JOIN scrap_qty sq ON
            sq.operation = tjc.operation
            AND sq.employee = tojc.employee
            AND sq.shift = tojc.shift
            AND sq.full_date = tojc.`date`
        WHERE
            tjc.company = %(company)s
            AND tjc.operation IN (
                'CONGDOANCAT', 'CONGDOANTHOI'
            )
        GROUP BY
                tojc.`date`,
                tjc.operation,
                tojc.shift,
                tojc.employee
    ),
    summary_data AS (
        SELECT
            NULL AS day_of_week,
            NULL AS month_of_year,
            NULL AS week_of_year,
            full_date,
            operation,
            NULL AS shift,
            NULL AS staff,
            SUM(output_qty) AS output_qty,
            SUM(scrap_qty) AS scrap_qty,
            SUM(scrap_qty) / (
                SUM(scrap_qty) + SUM(output_qty)
            ) AS scrap_rate
        FROM
            detail_data
        GROUP BY
            full_date,
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
            full_date DESC,
            operation,
            CASE
                WHEN staff IS NULL THEN 1
                ELSE 0
            END
    )
    SELECT
        day_of_week,
        month_of_year,
        week_of_year,
        DATE_FORMAT(full_date, '%%d/%%m/%%y') AS full_date,
        operation,
        shift, 
        staff,
        output_qty,
        scrap_qty,
        CONCAT(ROUND(scrap_rate * 100, 2), '%%') AS scrap_rate
    FROM
        combine_data
        WHERE
            YEAR(full_date) = %(year)s
            AND (MONTH(full_date) = %(month)s OR %(month)s IS NULL OR %(month)s = '')
            AND (full_date = DATE(%(start_date)s) OR %(start_date)s IS NULL OR %(start_date)s = '')
            AND (operation = %(operation)s OR %(operation)s IS NULL OR %(operation)s = '')
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
        if not filters.get("month"):
            conditions["month"] = None
        if not filters.get("start_date"):
            conditions["start_date"] = None
        if not filters.get("operation"):
            conditions["operation"] = None
    return conditions
