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
            "label": "Ngày tháng",
            "fieldname": "ngay_ghi_so",
            "fieldtype": "Data",
        },
        {
            "label": "Số hiệu",
            "fieldname": "so_chung_tu",
            "fieldtype": "Data",
        },
        {
            "label": "Khách hàng",
            "fieldname": "ten_kh",
            "fieldtype": "Data",
        },
        {
            "label": "Diễn giải",
            "fieldname": "dien_giai",
            "fieldtype": "Data",
        },
        {
            "label": "TK nợ",
            "fieldname": "tk",
            "fieldtype": "Data",
        },
        {
            "label": "TK có",
            "fieldname": "doi_ung",
            "fieldtype": "Data",
        },
        {
            "label": "Số phát sinh",
            "fieldname": "phat_sinh",
            "fieldtype": "Currency",
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

    # Truy vấn dữ liệu GL Entry
    data = frappe.db.sql(
        """
        SELECT 
            DATE_FORMAT(posting_date , '%%d/%%c/%%Y') AS ngay_ghi_so,
            GL.NAME AS so_chung_tu,
            GL.PARTY AS ten_kh,
            GL.REMARKS AS dien_giai,
            SUBSTRING_INDEX(GL.AGAINST, ' -', 1) AS tk,
            SUBSTRING_INDEX(GL.ACCOUNT, ' -', 1) AS doi_ung,
            ABS(DEBIT - CREDIT) AS phat_sinh
        FROM 
            `tabGL Entry` GL 
        WHERE 
            GL.COMPANY = %(company)s
            AND GL.POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
            AND IS_CANCELLED = 0
            AND GL.PARTY IS NOT NULL
            AND GL.VOUCHER_SUBTYPE = 'Receive'
        """,
        conditions,  # filters
        as_dict=True,
    )

    # Thêm tổng số phát sinh vào mỗi dòng dữ liệu
    total = frappe.db.sql(
        """
    SELECT
        ABS(SUM(DEBIT - CREDIT)) AS total_phat_sinh
    FROM 
        `tabGL Entry` GL 
    WHERE 
        GL.COMPANY = %(company)s
        AND GL.POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
        AND IS_CANCELLED = 0
        AND PARTY IS NOT NULL
        AND GL.VOUCHER_SUBTYPE = 'Receive'
    """,
        conditions,  # filters
        as_dict=True,
    )

    # Thêm thông tin tổng số vào từng dòng dữ liệu
    for row in data:
        row["total_phat_sinh"] = (
            total[0]["total_phat_sinh"]
            if total and total[0]["total_phat_sinh"] is not None
            else 0
        )

    return data
