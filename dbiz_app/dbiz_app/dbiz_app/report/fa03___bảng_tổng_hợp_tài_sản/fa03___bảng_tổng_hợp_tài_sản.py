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
            "label": "Đơn vị",
            "fieldname": "company",
            "fieldtype": "Data",
        },
        {
            "label": "Mã, tên tài sản/Công cụ dụng cụ",
            "fieldname": "asset",
            "fieldtype": "Data",
        },
        {
            "label": "Ngày đưa vào sử dụng",
            "fieldname": "available_for_use_date",
            "fieldtype": "Date",
        },
        {
            "label": "Số tháng khấu hao",
            "fieldname": "total_number_of_depreciations",
            "fieldtype": "Float",
        },
        {
            "label": "Khấu hao hàng tháng",
            "fieldname": "depreciation_amount",
            "fieldtype": "Float",
        },
        {
            "label": "Số kỳ đã K/Hao",
            "fieldname": "opening_number_of_booked_depreciations",
            "fieldtype": "Float",
        },
        {
            "label": "Đầu kỳ Nguyên giá",
            "fieldname": "total_asset_cost",
            "fieldtype": "Float",
        },
        {
            "label": "Đầu kỳ đã khấu hao",
            "fieldname": "opening_accumulated_depreciations",
            "fieldtype": "Float",
        },
        {
            "label": "Đầu kỳ còn lại",
            "fieldname": "remaining_opening",
            "fieldtype": "Float",
        },
        {
            "label": "Khấu hao trong kỳ",
            "fieldname": "depreciation_amount",
            "fieldtype": "Float",
        },
        {
            "label": "Cuối kỳ nguyên giá",
            "fieldname": "total_asset_cost",
            "fieldtype": "Float",
        },
        {
            "label": "Cuối kỳ đã KH",
            "fieldname": "remaining_opening",
            "fieldtype": "Float",
        },
        {
            "label": "Cuối kỳ còn lại",
            "fieldname": "depreciation_balance",
            "fieldtype": "Float",
        },
        {
            "label": "Số lượng",
            "fieldname": "asset_quantity",
            "fieldtype": "Float",
        },
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    data = frappe.db.sql(
        """
        SELECT 
            TA.company AS company,
            CONCAT(TA.NAME, ', ', TA.ASSET_NAME) AS asset,
            AVAILABLE_FOR_USE_DATE AS available_for_use_date,
            OP_DE.TOTAL_NUMBER_OF_DEPRECIATIONS AS total_number_of_depreciations,
            DEPRECIATION_AMOUNT AS depreciation_amount,
            OPENING_NUMBER_OF_BOOKED_DEPRECIATIONDS AS opening_number_of_booked_depreciations,
            TOTAL_ASSET_COST AS total_asset_cost,
            OPENING_ACCUMULATED_DEPRECIATIONDS AS opening_accumulated_depreciations,
            TOTAL_ASSET_COST - OPENING_ACCUMULATED_DEPRECIATIONDS AS remaining_opening,
            DEPRECIATION_AMOUNT AS depreciation_amount,
            TOTAL_ASSET_COST AS total_asset_cost,
            DEPRECIATION_AMOUNT + OPENING_ACCUMULATED_DEPRECIATIONDS AS depreciation_balance,
            TOTAL_ASSET_COST - OPENING_ACCUMULATED_DEPRECIATIONDS - DEPRECIATION_AMOUNT AS remaining_balance,
            TA.ASSET_QUANTITY AS asset_quantity
        FROM 
            tabAsset TA 
        LEFT JOIN
        (
            SELECT * 
            FROM 
                `tabAsset Depreciation Schedule` ADS 
            LEFT JOIN 
            (
                SELECT SUM(DEPRECIATION_AMOUNT) AS OPENING_ACCUMULATED_DEPRECIATIONDS, COUNT(*) AS OPENING_NUMBER_OF_BOOKED_DEPRECIATIONDS, PARENT
                FROM
                    `tabDepreciation Schedule`
                WHERE 
                    SCHEDULE_DATE < DATE(%(start_date)s)
                GROUP BY PARENT
            ) AS DS
            ON DS.PARENT = ADS.NAME
            WHERE ADS.DOCSTATUS = 1
            AND ADS.finance_book = %(finance_book)s
        ) AS OP_DE
        ON TA.NAME = OP_DE.ASSET
        LEFT JOIN 
        (
            SELECT * 
            FROM 
                `tabAsset Depreciation Schedule` ADS 
            LEFT JOIN 
            (
                SELECT SUM(DEPRECIATION_AMOUNT) AS DEPRECIATION_AMOUNT, PARENT
                FROM
                    `tabDepreciation Schedule`
                WHERE 
                    SCHEDULE_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
                GROUP BY PARENT
            ) AS DS
            ON DS.PARENT = ADS.NAME
            WHERE ADS.DOCSTATUS = 1
            AND ADS.finance_book = %(finance_book)s
        ) AS END_DE
        ON TA.NAME = END_DE.ASSET
        WHERE TA.COMPANY = (%(company)s)
        AND TA.STATUS IN ('Submitted', 'Partially Depreciated', 'Fully Depreciated')
        GROUP BY TA.NAME;
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
