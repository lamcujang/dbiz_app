import frappe
from frappe.model.mapper import get_mapped_doc
from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice
from frappe.utils import flt
from erpnext.stock.doctype.item.item import get_item_defaults, get_last_purchase_details
from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
class cus_purchase_invoice(PurchaseInvoice):
    def onload(self):
        pass
    def on_submit(self):
        super(cus_purchase_invoice, self).on_submit()
        self.update_status_expense_claim()
        
    def update_status_expense_claim(self):
        for item in self.items:
            if item.expense_claim:
                frappe.db.set_value("Expense Claim", item.expense_claim, "status", "Paid")
    
@frappe.whitelist()
def make_landed_cost_voucher(source_name, target_doc=None):
    purchase_invoice = frappe.get_doc("Purchase Invoice", source_name)
    
    company = purchase_invoice.company
    company_doc = frappe.get_doc("Company", company)
    company_currency = company_doc.default_currency
    
    doclist = get_mapped_doc(
		"Purchase Invoice",
		source_name,
		{
			"Purchase Invoice": {
				"doctype": "Landed Cost Voucher",
				"field_map": {
					"company": "company",
					"name": "purchase_invoice",
				},
			},
			"Purchase Invoice Item": {
                "doctype": "Landed Cost Taxes and Charges",
                "field_map": {
                    "expense_account": "expense_account",
                    "amount": "amount"
                },
                "postprocess": lambda source, target, source_parent: (
                    setattr(target, "description", source.item_code if source.item_code else source.item_name),
                    setattr(target, "account_currency", company_currency)
                ),
            },
            
		},
	)

    return doclist

@frappe.whitelist()
def make_purchase_invoice_from_expense_claim(source_name, target_doc=None):
	return get_mapped_expense_claim(source_name, target_doc)

def get_mapped_expense_claim(source_name, target_doc=None, ignore_permissions=False):
	def postprocess(source, target):
		target.flags.ignore_permissions = ignore_permissions
		# set_missing_values(source, target)

		# set tax_withholding_category from Purchase Order
		# if source.apply_tds and source.tax_withholding_category and target.apply_tds:
		# 	target.tax_withholding_category = source.tax_withholding_category

		# Get the advance paid Journal Entries in Purchase Invoice Advance
		# if target.get("allocate_advances_automatically"):
		# 	target.set_advances()

		# target.set_payment_schedule()
		# target.credit_to = get_party_account("Supplier", source.supplier, source.company)

	def update_item(obj, target, source_parent):
		target.amount = flt(obj.amount)
		target.base_amount = target.amount
		target.rate = target.amount
		target.qty = 1
		target.uom = 'Nos'
		expense_claim_type = frappe.get_doc("Expense Claim Type", obj.expense_type)
		account = expense_claim_type.get("accounts", {"company": source_parent.company})[0].get("default_account")
		target.expense_account = account
		target.invoice_date = obj.invoice_date
		# item = get_item_defaults(target.item_code, source_parent.company)
		# item_group = get_item_group_defaults(target.item_code, source_parent.company)
		# target.cost_center = (
		# 	obj.cost_center
		# 	or frappe.db.get_value("Project", obj.project, "cost_center")
		# 	or item.get("buying_cost_center")
		# 	or item_group.get("buying_cost_center")
		# )

	fields = {
		"Expense Claim": {
			"doctype": "Purchase Invoice",
			"field_map": {
				"company": "company",
			},
		},
		"Expense Claim Detail": {
			"doctype": "Purchase Invoice Item",
			"field_map": {
				"name": "expense_claim_detail",
				"parent": "expense_claim",
				"invoice_sign": "invoice_sign",
				"invoice_date": "invoice_date",
				"address": "address",
				"location_address": "location_address",
				"invoice_search_code": "invoice_search_code",
				"invoice_number": "invoice_number",
				"vendor_name": "vendor_name",
				"tax_code": "tax_code",
				"invoice_link": "invoice_link",
				"item_tax_template": "item_tax_template",
				"expense_type": "item_name",
			},
			"postprocess": update_item,
		},
		"Expense Taxes and Charges": {"doctype": "Purchase Taxes and Charges", "add_if_empty": True},
	}

	doc = get_mapped_doc(
		"Expense Claim",
		source_name,
		fields,
		target_doc,
		postprocess,
		ignore_permissions=ignore_permissions,
	)

	return doc

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def expense_claim_search(doctype, txt, searchfield, start, page_len, filters, as_dict=None, reference_doctype=None):
    filters = filters or {}
    company = filters.get("company")

    conds = [
        "ec.docstatus = 1",
        "(%(company)s IS NULL OR ec.company = %(company)s)",
        "ec.status NOT IN ('Cancelled','Rejected')",
        "ec.name LIKE %(txt)s",
        """NOT EXISTS (
            SELECT 1 FROM `tabPurchase Invoice Item` pii
            JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
            WHERE pi.docstatus < 2 AND pii.expense_claim = ec.name
        )"""
    ]
    params = {
        "company": company,
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len,
    }

    def add_cond(field, column):
        v = filters.get(field)
        if not v: return
        if isinstance(v, (list, tuple)) and len(v) >= 2:
            op = str(v[0]).lower()
            val = v[1]
            if op in ("like", "not like") and val:
                conds.append(f"{column} {op.upper()} %({field})s")
                params[field] = val
            elif op in ("equals", "=","!=",">","<",">=","<=") and val:
                conds.append(f"{column} {('=' if op=='equals' else op)} %({field})s")
                params[field] = val
        else:
            conds.append(f"{column} = %({field})s")
            params[field] = v

    if filters:
        for filter in filters:
            add_cond(filter, "ec." + filter)

    sql = f"""
        SELECT ec.name, ec.employee, ec.employee_name, ec.posting_date
        FROM `tabExpense Claim` ec
        WHERE {' AND '.join(conds)}
        ORDER BY ec.creation DESC
        LIMIT %(start)s, %(page_len)s
    """
    return frappe.db.sql(sql, params, as_dict=True)