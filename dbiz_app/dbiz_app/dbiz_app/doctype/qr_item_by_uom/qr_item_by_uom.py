# Copyright (c) 2024, lamnl and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import (
	get_link_to_form,
)
from frappe.model.document import Document


class QRItemByUOM(Document):

	def before_save(self):
		self.validate_by_qty()
	
	def validate_by_qty(self):
		check = frappe.db.sql("""
			SELECT 
				name
			FROM 
				`tabQR Item By UOM`
			WHERE 
				quantity = %s
				AND uom = %s
				AND item_code = %s
		""", (self.quantity, self.uom, self.item_code), as_dict=True)
		if check:
			duplicate_name = check[0].get("name")
			frappe.throw(_("This UOM and Qty by item {0} already exists in document {1}").format(self.item_code, get_link_to_form("QR Item By UOM", duplicate_name)))
