# dbiz_app/custom_hook/gl_custom.py
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import set_name_from_naming_options

class GLCustom(Document):
    def rename_temporarily_named_docs(self, doctype):
        """Rename temporarily named docs using autoname options"""
        docs_to_rename = frappe.get_all(doctype, {"to_rename": "1"}, order_by="creation", limit=50000)
        
        for doc in docs_to_rename:
            oldname = doc.name
            set_name_from_naming_options(frappe.get_meta(doctype).autoname, doc)
            newname = doc.name
            
            frappe.db.sql(
                f"UPDATE `tab{doctype}` SET name = %s, to_rename = 0 where name = %s",
                (newname, oldname),
                auto_commit=True,
            )
            
            if doctype == 'GL Entry' and doc.voucher_type == 'Company Loan':
                frappe.db.sql(
                    "UPDATE `tabCompany Loan Repayment Schedule` SET int_gl = %s where int_gl = %s",
                    (newname, oldname),
                    auto_commit=True,
                )