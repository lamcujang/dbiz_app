# Copyright (c) 2024, lamnl and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):  # -> tuple[list[Any], list[Any]]:
    if filters.start_date > filters.end_date:
        frappe.throw(_("From Date must be before To Date"))

    columns = get_columns()
    data = get_data(filters=filters)
    return columns, data


def get_columns():
    return [
        {
            "label": "Số Hiệu Tài Khoản",
            "fieldname": "ACCOUNT_NUMBER",
            "fieldtype": "Data",
        },
        {
            "label": "Tên Tài Khoản Kế Toán",
            "fieldname": "ACCOUNT_NAME",
            "fieldtype": "Data",
        },
        {
            "label": "Số dư nợ đầu tháng",
            "fieldname": "DAU_KY_NO",
            "fieldtype": "FLoat",
        },
        {
            "label": "Số dư có đầu tháng",
            "fieldname": "DAU_KY_CO",
            "fieldtype": "FLoat",
        },
        {
            "label": "Số phát sinh nợ trong tháng",
            "fieldname": "PHAT_SINH_NO",
            "fieldtype": "FLoat",
        },
        {
            "label": "Số phát sinh có trong tháng",
            "fieldname": "PHAT_SINH_CO",
            "fieldtype": "FLoat",
        },
        {
            "label": "Số dư nợ cuối tháng",
            "fieldname": "CUOI_KY_NO",
            "fieldtype": "FLoat",
        },
        {
            "label": "Số dư có cuối tháng",
            "fieldname": "CUOI_KY_CO",
            "fieldtype": "FLoat",
        },
    ]


def get_data(filters):
    if not filters.account:
        filters.account = None

    data = frappe.db.sql(
        """
        WITH TMP AS (
            SELECT 
                SUBSTRING_INDEX(GL.ACCOUNT, ' -', 1) AS ACCOUNT_NUMBER, 
                SUM(GL.DEBIT) AS DEBIT, 
                SUM(GL.CREDIT) AS CREDIT, 
                POSTING_DATE 
            FROM 
                `tabGL Entry` GL 
            WHERE 
                GL.company = %(company)s
                AND GL.is_cancelled = 0 
                AND (GL.account = %(account)s OR %(account)s IS NULL OR %(account)s = '')
            GROUP BY 
                SUBSTRING_INDEX(GL.ACCOUNT, ' -', 1), 
                TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(GL.ACCOUNT, ' -', 2), ' -', -1))
            ) 
            SELECT 
            AC.ACCOUNT_NUMBER, 
            AC.ACCOUNT_NAME, 
            IFNULL(O.OPENING_DEBIT,0) DAU_KY_NO, 
            IFNULL(O.OPENING_CREDIT,0) DAU_KY_CO, 
            IFNULL(GL.DEBIT,0) PHAT_SINH_NO, 
            IFNULL(GL.CREDIT,0) PHAT_SINH_CO, 
            IFNULL(E.ENDING_DEBIT, 0) CUOI_KY_NO, 
            IFNULL(E.ENDING_CREDIT, 0) CUOI_KY_CO 
            FROM 
            `tabAccount` AC 
            LEFT JOIN (
                    SELECT 
                    ACCOUNT_NUMBER, 
                    DEBIT, 
                    CREDIT 
                    FROM 
                    TMP 
                    WHERE 
                    POSTING_DATE >= DATE(
                        %(start_date)s
                    ) 
                    AND POSTING_DATE <= DATE(
                        %(end_date)s
                    )
                ) GL ON GL.ACCOUNT_NUMBER = AC.ACCOUNT_NUMBER
                LEFT JOIN (
                    SELECT 
                    ACCOUNT_NUMBER, 
                    CASE WHEN DEBIT - CREDIT > 0 THEN DEBIT - CREDIT ELSE NULL END AS OPENING_DEBIT, 
                    CASE WHEN CREDIT - DEBIT > 0 THEN CREDIT - DEBIT ELSE NULL END AS OPENING_CREDIT 
                    FROM 
                    TMP 
                    WHERE 
                    POSTING_DATE < DATE(
                        %(start_date)s
                    )
                ) O ON O.ACCOUNT_NUMBER = AC.ACCOUNT_NUMBER 
                LEFT JOIN (
                    SELECT 
                    ACCOUNT_NUMBER, 
                    CASE WHEN DEBIT - CREDIT > 0 THEN DEBIT - CREDIT ELSE 0 END AS ENDING_DEBIT, 
                    CASE WHEN CREDIT - DEBIT > 0 THEN CREDIT - DEBIT ELSE 0 END AS ENDING_CREDIT 
                    FROM 
                    TMP 
                    WHERE 
                    POSTING_DATE <= DATE(%(end_date)s)
                ) E ON E.ACCOUNT_NUMBER = AC.ACCOUNT_NUMBER
            WHERE 
            AC.COMPANY = %(company)s
            AND (AC.name = %(account)s OR %(account)s IS NULL OR %(account)s = '')
            AND AC.IS_GROUP = 0
        """,
        filters,  # filters
        as_dict=True,
    )
    return data
