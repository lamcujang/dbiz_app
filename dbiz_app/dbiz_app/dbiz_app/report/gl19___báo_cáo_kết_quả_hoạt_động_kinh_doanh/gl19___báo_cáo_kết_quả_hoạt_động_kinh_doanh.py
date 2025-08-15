# Copyright (c) 2024, lamnl and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    if not filters:
        filters = {}
    if filters.start_date > filters.end_date:
        frappe.throw(_("From Date must be before To Date"))
    columns, data = get_columns(), get_data(filters)
    print("data: ", data)
    return columns, data


def get_columns():
    return [
        {
            "label": "Chỉ tiêu",
            "fieldname": "RPT_NAME",
            "fieldtype": "Data",
            "width": 300,
        },
        {"label": "Mã số", "fieldname": "RPT_KEY", "fieldtype": "Data", "width": 100},
        {
            "label": "Tháng này",
            "fieldname": "AMT",
            "fieldtype": "Currency",
            "width": 150,
        },
        {
            "label": "Tháng trước",
            "fieldname": "P_AMT",
            "fieldtype": "Currency",
            "width": 150,
        },
    ]


def get_conditions(filters):
    conditions = {}
    for key, value in filters.items():
        if filters.get(key):
            conditions[key] = value
    return conditions


def get_data(filters):
    conditions = get_conditions(filters)

    data = frappe.db.sql(
        """
        WITH NAME_TMP AS (
        SELECT '1. Doanh thu bán hàng và cung cấp dịch vụ' RPT_NAME, '01' RPT_KEY 
        UNION ALL
        SELECT '2. Các khoản giảm trừ doanh thu' RPT_NAME, '02' RPT_KEY 
        UNION ALL
        SELECT '3. Doanh thu thuần về bán hàng và cung cấp dịch vụ (10 = 01 - 02)' RPT_NAME, '10' RPT_KEY 
        UNION ALL
        SELECT '4. Giá vốn hàng bán' RPT_NAME, '11' RPT_KEY 
        UNION ALL
        SELECT '5. Lợi nhuận gộp về bán hàng và cung cấp dịch vụ (20 = 10 - 11)' RPT_NAME, '20' RPT_KEY 
        UNION ALL
        SELECT '6. Doanh thu hoạt động tài chính' RPT_NAME, '21' RPT_KEY 
        UNION ALL
        SELECT '7. Chi phí tài chính' RPT_NAME, '22' RPT_KEY 
        UNION ALL
        SELECT '8. Chi phí bán hàng' RPT_NAME, '24' RPT_KEY 
        UNION ALL
        SELECT '9. Chi phí quản lý doanh nghiệp' RPT_NAME, '25' RPT_KEY 
        UNION ALL
        SELECT '10. Lợi nhuận thuần từ hoạt động kinh doanh {30 = 20 + (21 - 22) - (24 + 25)}' RPT_NAME, '30' RPT_KEY 
        UNION ALL
        SELECT '11. Thu nhập khác' RPT_NAME, '31' RPT_KEY  
        UNION ALL
        SELECT '12. Chi phí khác' RPT_NAME, '32' RPT_KEY  
        UNION ALL
        SELECT '13. Lợi nhuận khác (40 = 31 - 32)' RPT_NAME, '40' RPT_KEY  
        UNION ALL
        SELECT '14. Tổng lợi nhuận kế toán trước thuế (50 = 30 + 40)' RPT_NAME, '50' RPT_KEY  
        UNION ALL
        SELECT '15. Chi phí thuế TNDN hiện hành' RPT_NAME, '51' RPT_KEY  
        UNION ALL
        SELECT '16. Chi phí thuế TNDN hoãn lại' RPT_NAME, '52' RPT_KEY  
        UNION ALL
        SELECT '17. Lợi nhuận sau thuế thu nhập doanh nghiệp (60 = 50 – 51 - 52)' RPT_NAME, '60' RPT_KEY  
        UNION ALL
        SELECT '18. Lãi cơ bản trên cổ phiếu (*)' RPT_NAME, '70' RPT_KEY  
        )
    , TMP0 AS(  
    SELECT '01' RPT_KEY, 
    C.AMT AMT,
    P.AMT P_AMT
    FROM (
        SELECT 
        SUM(GL.CREDIT_IN_ACCOUNT_CURRENCY - GL.DEBIT_IN_ACCOUNT_CURRENCY) AMT
        FROM `tabGL Entry` GL
        WHERE GL.COMPANY =%(company)s
        AND GL.POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
        AND GL.ACCOUNT like '511%%'
        AND IS_CANCELLED = 0
        ) C 
    LEFT JOIN (
        SELECT 
        SUM(GL.CREDIT_IN_ACCOUNT_CURRENCY - GL.DEBIT_IN_ACCOUNT_CURRENCY) AMT
        FROM `tabGL Entry` GL
        WHERE GL.COMPANY =%(company)s
        AND GL.POSTING_DATE < DATE(%(start_date)s)
        AND GL.ACCOUNT like '511%%'
        AND IS_CANCELLED = 0
        ) P ON 1=1

    UNION ALL

    SELECT '02' RPT_KEY, 
    C.AMT AMT,
    P.AMT P_AMT
    FROM (
        SELECT 
        SUM(GL.CREDIT_IN_ACCOUNT_CURRENCY - GL.DEBIT_IN_ACCOUNT_CURRENCY) AMT
        FROM `tabGL Entry` GL
        WHERE GL.COMPANY =%(company)s
        AND GL.POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
        AND GL.ACCOUNT like '521%%'
        AND IS_CANCELLED = 0
        ) C 
    LEFT JOIN (
        SELECT 
        SUM(GL.CREDIT_IN_ACCOUNT_CURRENCY - GL.DEBIT_IN_ACCOUNT_CURRENCY) AMT
        FROM `tabGL Entry` GL
        WHERE GL.COMPANY =%(company)s
        AND GL.POSTING_DATE < DATE(%(start_date)s)
        AND GL.ACCOUNT like '521%%'
        AND IS_CANCELLED = 0
        ) P ON 1=1
        
    UNION ALL

    SELECT '11' RPT_KEY, 
    C.AMT AMT,
    P.AMT P_AMT
    FROM (
        SELECT 
        SUM(GL.CREDIT_IN_ACCOUNT_CURRENCY - GL.DEBIT_IN_ACCOUNT_CURRENCY) AMT
        FROM `tabGL Entry` GL
        WHERE GL.COMPANY =%(company)s
        AND GL.POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
        AND GL.ACCOUNT like '632%%'
        AND IS_CANCELLED = 0
        ) C 
    LEFT JOIN (
        SELECT 
        SUM(GL.CREDIT_IN_ACCOUNT_CURRENCY - GL.DEBIT_IN_ACCOUNT_CURRENCY) AMT
        FROM `tabGL Entry` GL
        WHERE GL.COMPANY =%(company)s
        AND GL.POSTING_DATE < DATE(%(start_date)s)
        AND GL.ACCOUNT like '632%%'
        AND IS_CANCELLED = 0
        ) P ON 1=1
        
    UNION ALL

    SELECT '21' RPT_KEY, 
    C.AMT AMT,
    P.AMT P_AMT
    FROM (
        SELECT 
        SUM(GL.CREDIT_IN_ACCOUNT_CURRENCY - GL.DEBIT_IN_ACCOUNT_CURRENCY) AMT
        FROM `tabGL Entry` GL
        WHERE GL.COMPANY =%(company)s
        AND GL.POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
        AND GL.ACCOUNT like '515%%'
        AND IS_CANCELLED = 0
        ) C 
    LEFT JOIN (
        SELECT 
        SUM(GL.CREDIT_IN_ACCOUNT_CURRENCY - GL.DEBIT_IN_ACCOUNT_CURRENCY) AMT
        FROM `tabGL Entry` GL
        WHERE GL.COMPANY =%(company)s
        AND GL.POSTING_DATE < DATE(%(start_date)s)
        AND GL.ACCOUNT like '515%%'
        AND IS_CANCELLED = 0
        ) P ON 1=1
        
    UNION ALL

    SELECT '22' RPT_KEY, 
    C.AMT AMT,
    P.AMT P_AMT
    FROM (
        SELECT 
        SUM(GL.CREDIT_IN_ACCOUNT_CURRENCY - GL.DEBIT_IN_ACCOUNT_CURRENCY) AMT
        FROM `tabGL Entry` GL
        WHERE GL.COMPANY =%(company)s
        AND GL.POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
        AND GL.ACCOUNT like '635%%'
        AND IS_CANCELLED = 0
        ) C 
    LEFT JOIN (
        SELECT 
        SUM(GL.CREDIT_IN_ACCOUNT_CURRENCY - GL.DEBIT_IN_ACCOUNT_CURRENCY) AMT
        FROM `tabGL Entry` GL
        WHERE GL.COMPANY =%(company)s
        AND GL.POSTING_DATE < Date(%(start_date)s)
        AND GL.ACCOUNT like '635%%'
        AND IS_CANCELLED = 0
        ) P ON 1=1
        
    UNION ALL

    SELECT '24' RPT_KEY, 
    C.AMT AMT,
    P.AMT P_AMT
    FROM (
        SELECT 
        SUM(GL.CREDIT_IN_ACCOUNT_CURRENCY - GL.DEBIT_IN_ACCOUNT_CURRENCY) AMT
        FROM `tabGL Entry` GL
        WHERE GL.COMPANY =%(company)s
        AND GL.POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
        AND GL.ACCOUNT like '641%%'
        AND IS_CANCELLED = 0
        ) C 
    LEFT JOIN (
        SELECT 
        SUM(GL.CREDIT_IN_ACCOUNT_CURRENCY - GL.DEBIT_IN_ACCOUNT_CURRENCY) AMT
        FROM `tabGL Entry` GL
        WHERE GL.COMPANY =%(company)s
        AND GL.POSTING_DATE < Date(%(start_date)s)
        AND GL.ACCOUNT like '641%%'
        AND IS_CANCELLED = 0
        ) P ON 1=1
        
    UNION ALL

    SELECT '25' RPT_KEY, 
    C.AMT AMT,
    P.AMT P_AMT
    FROM (
        SELECT 
        SUM(GL.CREDIT_IN_ACCOUNT_CURRENCY - GL.DEBIT_IN_ACCOUNT_CURRENCY) AMT
        FROM `tabGL Entry` GL
        WHERE GL.COMPANY =%(company)s
        AND GL.POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
        AND GL.ACCOUNT like '642%%'
        AND IS_CANCELLED = 0
        ) C 
    LEFT JOIN (
        SELECT 
        SUM(GL.CREDIT_IN_ACCOUNT_CURRENCY - GL.DEBIT_IN_ACCOUNT_CURRENCY) AMT
        FROM `tabGL Entry` GL
        WHERE GL.COMPANY =%(company)s
        AND GL.POSTING_DATE < Date(%(start_date)s)
        AND GL.ACCOUNT like '642%%'
        AND IS_CANCELLED = 0
        ) P ON 1=1
        
    UNION ALL

    SELECT '31' RPT_KEY, 
    C.AMT AMT,
    P.AMT P_AMT
    FROM (
        SELECT 
        SUM(GL.CREDIT_IN_ACCOUNT_CURRENCY - GL.DEBIT_IN_ACCOUNT_CURRENCY) AMT
        FROM `tabGL Entry` GL
        WHERE GL.COMPANY =%(company)s
        AND GL.POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
        AND GL.ACCOUNT like '711%%'
        AND IS_CANCELLED = 0
        ) C 
    LEFT JOIN (
        SELECT 
        SUM(GL.CREDIT_IN_ACCOUNT_CURRENCY - GL.DEBIT_IN_ACCOUNT_CURRENCY) AMT
        FROM `tabGL Entry` GL
        WHERE GL.COMPANY =%(company)s
        AND GL.POSTING_DATE < Date(%(start_date)s)
        AND GL.ACCOUNT like '711%%'
        AND IS_CANCELLED = 0
        ) P ON 1=1
        
    UNION ALL

    SELECT '32' RPT_KEY, 
    C.AMT AMT,
    P.AMT P_AMT
    FROM (
        SELECT 
        SUM(GL.CREDIT_IN_ACCOUNT_CURRENCY - GL.DEBIT_IN_ACCOUNT_CURRENCY) AMT
        FROM `tabGL Entry` GL
        WHERE GL.COMPANY =%(company)s
        AND GL.POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
        AND GL.ACCOUNT like '811%%'
        AND IS_CANCELLED = 0
        ) C 
    LEFT JOIN (
        SELECT 
        SUM(GL.CREDIT_IN_ACCOUNT_CURRENCY - GL.DEBIT_IN_ACCOUNT_CURRENCY) AMT
        FROM `tabGL Entry` GL
        WHERE GL.COMPANY =%(company)s
        AND GL.POSTING_DATE < Date(%(start_date)s)
        AND GL.ACCOUNT like '811%%'
        AND IS_CANCELLED = 0
        ) P ON 1=1
        
    UNION ALL

    SELECT '51' RPT_KEY, 
    C.AMT AMT,
    P.AMT P_AMT
    FROM (
        SELECT 
        SUM(GL.CREDIT_IN_ACCOUNT_CURRENCY - GL.DEBIT_IN_ACCOUNT_CURRENCY) AMT
        FROM `tabGL Entry` GL
        WHERE GL.COMPANY =%(company)s
        AND GL.POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
        AND GL.ACCOUNT like '8211%%'
        AND IS_CANCELLED = 0
        ) C 
    LEFT JOIN (
        SELECT 
        SUM(GL.CREDIT_IN_ACCOUNT_CURRENCY - GL.DEBIT_IN_ACCOUNT_CURRENCY) AMT
        FROM `tabGL Entry` GL
        WHERE GL.COMPANY =%(company)s
        AND GL.POSTING_DATE < Date(%(start_date)s)
        AND GL.ACCOUNT like '8211%%'
        AND IS_CANCELLED = 0
        ) P ON 1=1
        
    UNION ALL
        
    SELECT '52' RPT_KEY, 
    C.AMT AMT,
    P.AMT P_AMT
    FROM (
        SELECT 
        SUM(GL.CREDIT_IN_ACCOUNT_CURRENCY - GL.DEBIT_IN_ACCOUNT_CURRENCY) AMT
        FROM `tabGL Entry` GL
        WHERE GL.COMPANY =%(company)s
        AND GL.POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
        AND GL.ACCOUNT like '8212%%'
        AND IS_CANCELLED = 0
        ) C 
    LEFT JOIN (
        SELECT 
        SUM(GL.CREDIT_IN_ACCOUNT_CURRENCY - GL.DEBIT_IN_ACCOUNT_CURRENCY) AMT
        FROM `tabGL Entry` GL
        WHERE GL.COMPANY =%(company)s
        AND GL.POSTING_DATE < Date(%(start_date)s)
        AND GL.ACCOUNT like '8212%%'
        AND IS_CANCELLED = 0
        ) P ON 1=1
    ),
    TMP1 AS (
    SELECT '10' RPT_KEY, 
    C.AMT AMT,
    P.AMT P_AMT
    FROM (
        SELECT 
        SUM(T.AMT) AMT
        FROM TMP0 T
        WHERE RPT_KEY IN ('01','02')
        ) C 
    LEFT JOIN (
        SELECT 
        SUM(T.P_AMT) AMT
        FROM TMP0 T
        WHERE RPT_KEY IN ('01','02')
        ) P ON 1=1
        
    UNION ALL

    SELECT '20' RPT_KEY, 
    C.AMT AMT,
    P.AMT P_AMT
    FROM (
        SELECT 
        SUM(T.AMT) AMT
        FROM TMP0 T
        WHERE RPT_KEY IN ('01','02','11')
        ) C 
    LEFT JOIN (
        SELECT 
        SUM(T.P_AMT) AMT
        FROM TMP0 T
        WHERE RPT_KEY IN ('01','02','11')
        ) P ON 1=1
        
    UNION ALL

    SELECT '30' RPT_KEY, 
    C.AMT AMT,
    P.AMT P_AMT
    FROM (
        SELECT 
        SUM(T.AMT) AMT
        FROM TMP0 T
        WHERE RPT_KEY IN ('01','02','11','21','22','24','25')
        ) C 
    LEFT JOIN (
        SELECT 
        SUM(T.P_AMT) AMT
        FROM TMP0 T
        WHERE RPT_KEY IN ('01','02','11','21','22','24','25')
        ) P ON 1=1
        
    UNION ALL

    SELECT '40' RPT_KEY, 
    C.AMT AMT,
    P.AMT P_AMT
    FROM (
        SELECT 
        SUM(T.AMT) AMT
        FROM TMP0 T
        WHERE RPT_KEY IN ('31','32')
        ) C 
    LEFT JOIN (
        SELECT 
        SUM(T.P_AMT) AMT
        FROM TMP0 T
        WHERE RPT_KEY IN ('31','32')
        ) P ON 1=1
    ),
    TMP2 AS
    (
    SELECT '50' RPT_KEY, 
    C.AMT AMT,
    P.AMT P_AMT
    FROM (
        SELECT 
        SUM(T.AMT) AMT
        FROM TMP1 T
        WHERE RPT_KEY IN ('30','40')
        ) C 
    LEFT JOIN (
        SELECT 
        SUM(T.P_AMT) AMT
        FROM TMP1 T
        WHERE RPT_KEY IN ('30','40')
        ) P ON 1=1
        
    UNION ALL

    SELECT '60' RPT_KEY, 
    C.AMT AMT,
    P.AMT P_AMT
    FROM (
        SELECT 
        SUM(T.AMT) AMT
        FROM TMP1 T
        WHERE RPT_KEY IN ('30','40','51','52')
        ) C 
    LEFT JOIN (
        SELECT 
        SUM(T.P_AMT) AMT
        FROM TMP1 T
        WHERE RPT_KEY IN ('30','40','51','52')
        ) P ON 1=1
    )
    SELECT 
        A1.RPT_NAME, 
        A1.RPT_KEY, 
        A2.AMT, 
        A2.P_AMT
    FROM NAME_TMP A1
    LEFT JOIN (
        SELECT * FROM TMP0
        UNION ALL
        SELECT * FROM TMP1
        UNION ALL
        SELECT * FROM TMP2
    ) A2 ON A2.RPT_KEY = A1.RPT_KEY
    """,
        conditions,  # filters
        as_dict=True,
    )

    return data
