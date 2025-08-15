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
        # Chứng từ chi phí mua hàng
        {
            "label": _("Ngày hạch toán"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 100
        },
        {
            "label": _("Ngày chứng từ"),
            "fieldname": "bill_date",
            "fieldtype": "Date",
            "width": 100
        },
        {
            "label": _("Số chứng từ"),
            "fieldname": "bill_no",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Số tiền"),
            "fieldname": "total_amount",
            "fieldtype": "float",
            "width": 150,
            "options": "float"
        },
        # Chứng từ mua hàng được phân bổ
        {
            "label": _("Ngày hạch toán (PB)"),
            "fieldname": "allocated_posting_date",
            "fieldtype": "Date",
            "width": 100
        },
        {
            "label": _("Ngày chứng từ (PB)"),
            "fieldname": "allocated_bill_date",
            "fieldtype": "Date",
            "width": 100
        },
        {
            "label": _("Số chứng từ (PB)"),
            "fieldname": "allocated_bill_no",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Số tiền (PB)"),
            "fieldname": "allocated_amount",
            "fieldtype": "float",
            "width": 150,
            "options": "float"
        },
        {
            "label": _("Chênh lệch"),
            "fieldname": "difference",
            "fieldtype": "float",
            "width": 150,
            "options": "float"
        }
    ]

def get_data(filters):
    # Get purchase costs from Purchase Invoice and related taxes
    purchase_costs = frappe.db.sql("""
        SELECT 
            pi.posting_date,
            pi.bill_date,
            pi.bill_no,
            pi.name as invoice_no,
            pi.supplier,
            pi.base_grand_total as total_amount,
            pi.docstatus
        FROM 
            `tabPurchase Invoice` pi
        WHERE 
            pi.docstatus = 1
            AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND pi.company = %(company)s
    """, filters, as_dict=1)

    # Get allocated purchase documents from Purchase Receipt
    # We'll match based on supplier and similar amounts
    allocated_purchases = frappe.db.sql("""
        SELECT 
            pr.posting_date as allocated_posting_date,
            pr.posting_date as allocated_bill_date,
            pr.name as allocated_bill_no,
            pr.base_grand_total as allocated_amount,
            pr.supplier,
            pr.docstatus,
            pr.journal_entry
        FROM 
            `tabPurchase Receipt` pr
        WHERE 
            pr.docstatus = 1
            AND pr.posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND pr.company = %(company)s
            AND pr.journal_entry IS NOT NULL
        ORDER BY 
            pr.posting_date
    """, filters, as_dict=1)

    # Get the journal entries for linking
    je_entries = None
    if allocated_purchases:
        je_list = [d.journal_entry for d in allocated_purchases if d.journal_entry]
        if je_list:
            je_entries = frappe.db.sql("""
                SELECT 
                    je.name,
                    je.posting_date,
                    je.cheque_date,
                    jea.reference_name,
                    jea.reference_type,
                    jea.debit_in_account_currency as amount
                FROM 
                    `tabJournal Entry` je
                LEFT JOIN 
                    `tabJournal Entry Account` jea 
                ON 
                    je.name = jea.parent
                WHERE 
                    je.name IN %(je_list)s
                    AND je.docstatus = 1
            """, {'je_list': je_list}, as_dict=1)

    # Combine and calculate differences
    data = []
    total_purchase_cost = 0
    total_allocated = 0
    
    for cost in purchase_costs:
        row = {
            "posting_date": cost.posting_date,
            "bill_date": cost.bill_date,
            "bill_no": cost.bill_no,
            "total_amount": cost.total_amount
        }
        
        # Find matching allocations through journal entries
        matching_allocations = []
        if je_entries:
            # First find JE entries referencing this invoice
            je_matches = [je for je in je_entries if je.reference_name == cost.invoice_no]
            if je_matches:
                # Then find PR entries with these JE references
                matching_allocations = [
                    alloc for alloc in allocated_purchases 
                    if any(je.name == alloc.journal_entry for je in je_matches)
                ]
        
        allocated_total = 0
        if matching_allocations:
            for idx, alloc in enumerate(matching_allocations):
                if idx == 0:
                    # First allocation goes in the same row
                    row.update({
                        "allocated_posting_date": alloc.allocated_posting_date,
                        "allocated_bill_date": alloc.allocated_bill_date,
                        "allocated_bill_no": alloc.allocated_bill_no,
                        "allocated_amount": alloc.allocated_amount
                    })
                else:
                    # Additional allocations go in new rows
                    data.append({
                        "allocated_posting_date": alloc.allocated_posting_date,
                        "allocated_bill_date": alloc.allocated_bill_date,
                        "allocated_bill_no": alloc.allocated_bill_no,
                        "allocated_amount": alloc.allocated_amount
                    })
                allocated_total += alloc.allocated_amount
        
        total_purchase_cost += cost.total_amount
        total_allocated += allocated_total
        row["difference"] = cost.total_amount - allocated_total
        data.append(row)
    
    # Add subtotal row
    data.append({
        "bill_no": "Cộng",
        "total_amount": total_purchase_cost,
        "allocated_amount": total_allocated,
        "difference": total_purchase_cost - total_allocated
    })
    
    # Add total row
    data.append({
        "bill_no": "Tổng cộng",
        "total_amount": total_purchase_cost,
        "allocated_amount": total_allocated,
        "difference": total_purchase_cost - total_allocated
    })
    
    return data