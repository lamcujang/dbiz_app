# Copyright (c) 2025, lamnl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BagType(Document):
	pass

@frappe.whitelist()
def get_list_docfields(doctype):
	docfields = frappe.get_doc("DocType", doctype).fields
	docfields = [df for df in docfields if df.fieldname not in ['name', 'owner', 'creation', 'modified', 'modified_by', 'parent', 'parentfield', 'parenttype', 'idx','docstatus','disiable']]
	docfields = [df for df in docfields if df.fieldtype not in ['Section Break', 'Column Break', 'HTML', 'Button', 'Table', 'Tab Break']]
	# docfields = [df for df in docfields if df.read_only == 0 and df.hidden == 0]
	return docfields
