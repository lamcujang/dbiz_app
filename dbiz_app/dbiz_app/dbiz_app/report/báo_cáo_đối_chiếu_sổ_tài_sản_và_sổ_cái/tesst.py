import frappe

def execute(filters=None):
    # Columns definition
    columns = [
        # Sổ tài sản
        {"label": "Ngày ghi sổ", "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
        {"label": "Ngày CT", "fieldname": "voucher_date", "fieldtype": "Date", "width": 100},
        {"label": "Số CT", "fieldname": "voucher_no", "fieldtype": "Link", "options": "Purchase Receipt", "width": 120},
        {"label": "Loại chứng từ", "fieldname": "voucher_type", "fieldtype": "Data", "width": 120},
        {"label": "Số tiền", "fieldname": "amount", "fieldtype": "float", "width": 120},

        # Sổ cái
        {"label": "Ngày HT", "fieldname": "gl_posting_date", "fieldtype": "Date", "width": 100},
        {"label": "Ngày CT", "fieldname": "gl_voucher_date", "fieldtype": "Date", "width": 100},
        {"label": "Số CT", "fieldname": "gl_voucher_no", "fieldtype": "Link", "options": "GL Entry", "width": 120},
        {"label": "Diễn giải", "fieldname": "remarks", "fieldtype": "Data", "width": 200},
        {"label": "Số tiền", "fieldname": "gl_amount", "fieldtype": "float", "width": 120},

        # Chênh lệch
        {"label": "Chênh lệch", "fieldname": "difference", "fieldtype": "float", "width": 120},
    ]

    # Fetch data
    data = get_asset_gl_comparison(filters)

    return columns, data


def get_asset_gl_comparison(filters):
    # Query sổ tài sản
    asset_data = frappe.db.sql("""
        SELECT 
            pri.item_code as asset_code,
            pri.description as asset_name,
            pri.amount as amount,
            pr.posting_date as posting_date,
            pr.posting_date as voucher_date,
            pr.name as voucher_no,
            'Ghi tăng tài sản cố định' as voucher_type
        FROM `tabPurchase Receipt` pr
        INNER JOIN `tabPurchase Receipt Item` pri ON pr.name = pri.parent
        WHERE pr.docstatus = 1
        AND pr.posting_date BETWEEN %(from_date)s AND %(to_date)s
        AND pr.company = %(company)s
    """, filters, as_dict=1)

    # Query sổ cái
    gl_data = frappe.db.sql("""
    SELECT 
        gl.posting_date as gl_posting_date,
        gl.posting_date as gl_voucher_date,
        gl.voucher_no as gl_voucher_no,
        gl.remarks as remarks,
        (gl.debit - gl.credit) as gl_amount
    FROM `tabGL Entry` gl
    WHERE gl.posting_date BETWEEN %(from_date)s AND %(to_date)s
    AND gl.company = %(company)s
    AND gl.account = %(account)s
    AND gl.docstatus = 1
""", filters, as_dict=1)


    # Kết hợp dữ liệu và tính toán chênh lệch
    comparison_data = []

    for asset in asset_data:
        row = {
            "posting_date": asset.posting_date,
            "voucher_date": asset.voucher_date,
            "voucher_no": asset.voucher_no,
            "voucher_type": asset.voucher_type,
            "amount": asset.amount,
            "gl_posting_date": None,
            "gl_voucher_date": None,
            "gl_voucher_no": None,
            "remarks": None,
            "gl_amount": 0,
            "difference": 0
        }

        # Tìm GL Entry tương ứng
        matching_gl = next((gl for gl in gl_data if gl.gl_voucher_no == asset.voucher_no), None)

        if matching_gl:
            row.update({
                "gl_posting_date": matching_gl.gl_posting_date,
                "gl_voucher_date": matching_gl.gl_voucher_date,
                "gl_voucher_no": matching_gl.gl_voucher_no,
                "remarks": matching_gl.remarks,
                "gl_amount": matching_gl.gl_amount,
                "difference": asset.amount - matching_gl.gl_amount
            })

        comparison_data.append(row)

    # Tính tổng cộng
    total_asset = sum(row["amount"] for row in comparison_data)
    total_gl = sum(row["gl_amount"] for row in comparison_data)
    total_difference = sum(row["difference"] for row in comparison_data)

    # Thêm dòng tổng cộng
    comparison_data.append({
        "posting_date": "Cộng",
        "amount": total_asset,
        "gl_amount": total_gl,
        "difference": total_difference
    })

    return comparison_data
