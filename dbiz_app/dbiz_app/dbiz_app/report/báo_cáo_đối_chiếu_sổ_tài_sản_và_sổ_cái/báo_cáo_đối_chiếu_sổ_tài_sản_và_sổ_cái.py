import frappe
from frappe import _


def execute(filters=None):
    if not filters:
        filters = {}

    if filters.from_date > filters.to_date:
        frappe.throw(_("From Date must be before To Date"))

    # Định nghĩa cột
    columns = [
        # Sổ tài sản
        {
            "label": "Ngày ghi sổ",
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 100,
        },
        {
            "label": "Ngày CT",
            "fieldname": "voucher_date",
            "fieldtype": "Date",
            "width": 100,
        },
        {
            "label": "Số CT",
            "fieldname": "voucher_no",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": "Loại chứng từ",
            "fieldname": "voucher_type",
            "fieldtype": "Data",
            "width": 120,
        },
        {"label": "Số tiền", "fieldname": "amount", "fieldtype": "float", "width": 120},
        # Sổ cái
        {
            "label": "Ngày HT",
            "fieldname": "gl_posting_date",
            "fieldtype": "Date",
            "width": 100,
        },
        {
            "label": "Ngày CT",
            "fieldname": "gl_voucher_date",
            "fieldtype": "Date",
            "width": 100,
        },
        {
            "label": "Số CT",
            "fieldname": "gl_voucher_no",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": "Diễn giải",
            "fieldname": "remarks",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": "Số tiền",
            "fieldname": "gl_amount",
            "fieldtype": "float",
            "width": 120,
        },
        # Chênh lệch
        {
            "label": "Chênh lệch",
            "fieldname": "difference",
            "fieldtype": "float",
            "width": 120,
        },
    ]

    # Lấy dữ liệu
    data = get_asset_gl_comparison(filters)

    return columns, data


def get_asset_gl_comparison(filters):
    # Query dữ liệu tài sản
    asset_data = frappe.db.sql(
        """
        SELECT 
            a.name AS asset_code,
            a.asset_name,
            SUM(a.gross_purchase_amount) AS amount,
            a.purchase_date AS posting_date,
            a.purchase_date AS voucher_date,
            CASE 
                WHEN a.purchase_receipt IS NOT NULL THEN CONCAT(a.purchase_receipt)
                WHEN a.purchase_invoice IS NOT NULL THEN CONCAT(a.purchase_invoice)
            END AS voucher_no,
            'Ghi tăng tài sản cố định' AS voucher_type
        FROM 
            `tabAsset` a
        WHERE 
            a.company = %(company)s 
            AND a.purchase_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY 
            a.name, a.purchase_receipt, a.purchase_invoice
    """,
        filters,
        as_dict=True,
    )

    comparison_data = []

    for asset in asset_data:
        gl_entries = []

        # Kiểm tra voucher_no trước khi xử lý
        voucher_no = asset.get("voucher_no")
        if not voucher_no:
            # print("Voucher_no is None")
            # Nếu voucher_no bị None hoặc rỗng, bỏ qua vòng lặp
            continue
        # print("Voucher_no: ", asset["voucher_no"])
        # Phân loại chứng từ để truy vấn GL Entry
        conditions = get_conditions(filters, asset_voucher_no=asset["voucher_no"])
        gl_entries = frappe.db.sql(
            """
            SELECT 
                gl.posting_date AS gl_posting_date,
                gl.posting_date AS gl_voucher_date,
                gl.voucher_no AS gl_voucher_no,
                gl.remarks AS remarks,
                SUM(gl.debit_in_account_currency - gl.credit_in_account_currency) AS gl_amount
            FROM 
                `tabGL Entry` gl
            WHERE 
                gl.voucher_no = %(voucher_no)s
                AND gl.company = %(company)s
                AND (gl.account = COALESCE(%(account)s, gl.account)
                OR %(account)s IS NULL
                    OR %(account)s = '')
            GROUP BY 
                gl.posting_date, gl.voucher_no, gl.remarks
        """,
            conditions,
            as_dict=True,
        )

        # Tổng hợp dữ liệu
        total_gl = sum(entry["gl_amount"] for entry in gl_entries) if gl_entries else 0
        # print("Total GL: ", total_gl)
        total_diff = asset["amount"] - total_gl

        if gl_entries:
            for gl_entry in gl_entries:
                # print("123",gl_entry["gl_amount"])
                comparison_data.append(
                    {
                        "posting_date": asset["posting_date"],
                        "voucher_date": asset["voucher_date"],
                        "voucher_no": asset["voucher_no"],
                        "voucher_type": asset["voucher_type"],
                        "amount": asset["amount"],
                        "gl_posting_date": gl_entry["gl_posting_date"],
                        "gl_voucher_date": gl_entry["gl_voucher_date"],
                        "gl_voucher_no": gl_entry["gl_voucher_no"],
                        "remarks": gl_entry["remarks"],
                        "gl_amount": gl_entry["gl_amount"],
                        "difference": asset["amount"] - gl_entry["gl_amount"],
                    }
                )
        else:
            pass
            # print("No GL Entry found for voucher_no: ", asset["voucher_no"])
            # comparison_data.append({
            #     "posting_date": asset["posting_date"],
            #     "voucher_date": asset["voucher_date"],
            #     "voucher_no": asset["voucher_no"],
            #     "voucher_type": asset["voucher_type"],
            #     "amount": asset["amount"],
            #     "gl_posting_date": None,
            #     "gl_voucher_date": None,
            #     "gl_voucher_no": None,
            #     "remarks": None,
            #     "gl_amount": 0,
            #     "difference": total_diff
            # })

    # Tính tổng cộng
    summary = {
        "posting_date": "",
        "voucher_date": "",
        "voucher_no": "",
        "voucher_type": "Tổng cộng",
        "amount": sum(row["amount"] for row in comparison_data),
        "gl_posting_date": "",
        "gl_voucher_date": "",
        "gl_voucher_no": "",
        "remarks": "",
        "gl_amount": sum(row["gl_amount"] for row in comparison_data),
        "difference": sum(row["difference"] for row in comparison_data),
    }
    comparison_data.append(summary)

    return comparison_data


def get_conditions(filters, asset_voucher_no=None):
    conditions = {}
    print(filters.items())
    for key, value in filters.items():
        if filters.get(key):
            conditions[key] = value
        if not filters.get("account"):
            conditions["account"] = None
    if asset_voucher_no:
        conditions["voucher_no"] = asset_voucher_no

    return conditions
