import frappe
from frappe import _

def execute(filters=None):
    if not filters:
        filters = {}
        
    if filters.from_date > filters.to_date:
        frappe.throw(_("From Date must be before To Date"))
    
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        # Thông tin chung
        {
            "label": _("Kỳ đối chiếu"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 100
        },
        # Theo sổ cái
        {
            "label": _("Phát sinh Nợ"),
            "fieldname": "debit",
            "fieldtype": "float",
            "width": 150,
            "options": "float"
        },
        {
            "label": _("Phát sinh Có"),
            "fieldname": "credit",
            "fieldtype": "float",
            "width": 150,
            "options": "float"
        },
        {
            "label": _("Số dư"),
            "fieldname": "balance",
            "fieldtype": "float",
            "width": 150,
            "options": "float"
        },
        # Theo sổ kho
        {
            "label": _("Nhập kho"),
            "fieldname": "stock_in",
            "fieldtype": "float",
            "width": 150,
            "options": "float"
        },
        {
            "label": _("Xuất kho"),
            "fieldname": "stock_out",
            "fieldtype": "float",
            "width": 150,
            "options": "float"
        },
        {
            "label": _("Tồn kho"),
            "fieldname": "stock_balance",
            "fieldtype": "float",
            "width": 150,
            "options": "float"
        },
        # Chênh lệch
        {
            "label": _("PS Nợ - Nhập kho"),
            "fieldname": "debit_stock_in_diff",
            "fieldtype": "float",
            "width": 150,
            "options": "float"
        },
        {
            "label": _("PS Có - Xuất kho"),
            "fieldname": "credit_stock_out_diff",
            "fieldtype": "float",
            "width": 150,
            "options": "float"
        },
        {
            "label": _("Số dư - Tồn kho"),
            "fieldname": "balance_diff",
            "fieldtype": "float",
            "width": 150,
            "options": "float"
        }
    ]

def get_data(filters):
    # Lấy dữ liệu từ sổ cái (GL Entry)
    gl_entries = frappe.db.sql("""
        SELECT 
            DATE(posting_date) as posting_date,
            SUM(debit_in_account_currency) as debit,
            SUM(credit_in_account_currency) as credit,
            SUM(debit_in_account_currency - credit_in_account_currency) as balance
        FROM 
            `tabGL Entry`
        WHERE 
            docstatus = 1
            AND posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND company = %(company)s
            AND account = %(inventory_account)s
        GROUP BY 
            DATE(posting_date)
        ORDER BY 
            posting_date
    """, filters, as_dict=1)

    # Lấy dữ liệu từ sổ kho (Stock Ledger Entry)
    stock_entries = frappe.db.sql("""
        SELECT 
            DATE(posting_date) as posting_date,
            SUM(CASE WHEN actual_qty > 0 THEN stock_value_difference ELSE 0 END) as stock_in,
            SUM(CASE WHEN actual_qty < 0 THEN ABS(stock_value_difference) ELSE 0 END) as stock_out,
            SUM(stock_value_difference) as stock_value_change
        FROM 
            `tabStock Ledger Entry`
        WHERE 
            docstatus = 1
            AND posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND company = %(company)s
            AND warehouse IN (SELECT name FROM `tabWarehouse` WHERE company = %(company)s)
        GROUP BY 
            DATE(posting_date)
        ORDER BY 
            posting_date
    """, filters, as_dict=1)

    # Tính toán số dư lũy kế
    opening_balance = frappe.db.sql("""
        SELECT 
            SUM(debit_in_account_currency - credit_in_account_currency) as balance
        FROM 
            `tabGL Entry`
        WHERE 
            docstatus = 1
            AND posting_date < %(from_date)s
            AND company = %(company)s
            AND account = %(inventory_account)s
    """, filters, as_dict=1)[0].balance or 0

    opening_stock = frappe.db.sql("""
        SELECT 
            SUM(stock_value_difference) as stock_value
        FROM 
            `tabStock Ledger Entry`
        WHERE 
            docstatus = 1
            AND posting_date < %(from_date)s
            AND company = %(company)s
            AND warehouse IN (SELECT name FROM `tabWarehouse` WHERE company = %(company)s)
    """, filters, as_dict=1)[0].stock_value or 0

    # Kết hợp và tính toán chênh lệch
    data = []
    current_gl_balance = opening_balance
    current_stock_balance = opening_stock
    
    # Add opening balance row
    data.append({
        "posting_date": filters.get("from_date"),
        "debit": 0,
        "credit": 0,
        "balance": current_gl_balance,
        "stock_in": 0,
        "stock_out": 0,
        "stock_balance": current_stock_balance,
        "debit_stock_in_diff": 0,
        "credit_stock_out_diff": 0,
        "balance_diff": current_gl_balance - current_stock_balance
    })

    # Combine GL and Stock entries
    all_dates = sorted(list(set(
        [d.posting_date for d in gl_entries] + 
        [d.posting_date for d in stock_entries]
    )))

    for date in all_dates:
        gl_entry = next((d for d in gl_entries if d.posting_date == date), None)
        stock_entry = next((d for d in stock_entries if d.posting_date == date), None)
        
        if gl_entry:
            current_gl_balance += gl_entry.balance or 0
        if stock_entry:
            current_stock_balance += stock_entry.stock_value_change or 0

        row = {
            "posting_date": date,
            "debit": gl_entry.debit if gl_entry else 0,
            "credit": gl_entry.credit if gl_entry else 0,
            "balance": current_gl_balance,
            "stock_in": stock_entry.stock_in if stock_entry else 0,
            "stock_out": stock_entry.stock_out if stock_entry else 0,
            "stock_balance": current_stock_balance
        }

        # Calculate differences
        row.update({
            "debit_stock_in_diff": (row["debit"] or 0) - (row["stock_in"] or 0),
            "credit_stock_out_diff": (row["credit"] or 0) - (row["stock_out"] or 0),
            "balance_diff": current_gl_balance - current_stock_balance
        })

        data.append(row)

    return data