# Copyright (c) 2024, lamnl and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import (
	get_link_to_form,
)
from frappe.model.document import Document


class ScrapItemsJobCard(Document):
	
	def validate(self):
		if self.transfer_type =='SCRAP_EXPORT':
			if not self.link_scrap_job_card:
				frappe.throw(_("Vui lòng quét mã QR của phiếu nhập phế liệu!"))
			count = frappe.db.count("Scrap Items Job Card", {"link_scrap_job_card": self.link_scrap_job_card}, 
                           filters={"scrap_type": "SCRAP_IMPORT", "docstatus": 1})
			if count > 0:
				frappe.throw(_("Phiếu nhập phế liệu {0} đã được xuất phế liệu!").format(self.link_scrap_job_card))


	def on_submit(self):
		if self.transfer_type =='SCRAP_IMPORT':
			job_card = frappe.get_doc("Job Card", self.job_card)
    
			# Thêm dòng mới vào child table
			job_card.append("scrap_items", {
				"item_code": self.item_code,
				"item_name": self.item_name,
				"stock_qty": self.stock_qty,
				"stock_uom": self.stock_uom,
				"source_scrap_warehouse": self.scrap_warehouse
			})
			
			# Lưu với ignore_permissions=True
			job_card.save(ignore_permissions=True)
		# Create Scrap Stock Entry
		stock_entry = frappe.new_doc("Stock Entry")
		if self.transfer_type =='SCRAP_IMPORT':
			stock_entry.stock_entry_type = "NHAPPHE"
			stock_entry.purpose = "Material Receipt"
			stock_entry.company = frappe.get_doc("Job Card", self.job_card).company
			stock_entry.to_warehouse = self.scrap_warehouse
		elif self.transfer_type =='SCRAP_EXPORT':
			stock_entry.stock_entry_type = "XUATPHE"
			stock_entry.purpose = "Material Issue"
			stock_entry.from_warehouse = self.scrap_warehouse
			
		stock_entry.append("items", {
			"allow_zero_valuation_rate": 1,
			"item_code": self.item_code,
			"qty": self.stock_qty,
			"uom": self.stock_uom,
			"s_warehouse": self.scrap_warehouse
		})
		
		stock_entry.save(ignore_permissions=True)
		stock_entry.submit()
		
		# Save the stock_entry reference before submitting
		self.db_set('stock_entry', stock_entry.name, update_modified=False)
		frappe.msgprint(_("Stock Entry {0} created").format(get_link_to_form("Stock Entry", stock_entry.name)), alert=True)	
