# Copyright (c) 2024, lamnl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PalletTransfer(Document):
	def on_submit(self):
		self.validate_before_transfer()
		self.tranfer_pallet()
	def validate_before_transfer(self):
		if not self.items:
			frappe.throw("Please add items to transfer")
		pallet_data = frappe.get_doc("Pallet", self.pallet_to)
		item_data = frappe.get_doc("Item", pallet_data.item_code)
		if pallet_data.qty >= item_data.carton_per_pallet:
			frappe.throw("Pallet is full")
		qty = pallet_data.qty + len(self.items)
		if qty > item_data.carton_per_pallet:
			frappe.throw("Pallet available quantity " + str(item_data.carton_per_pallet - pallet_data.qty))
	def tranfer_pallet(self):
		for item in self.items:
			batch = frappe.get_doc("Batch", item.batch_no)
			batch.pallet = self.pallet_to
			batch.save(ignore_permissions=True)
			pallet_from = frappe.get_doc("Pallet", self.pallet_from)
			pallet_from.qty -= batch.batch_qty
			pallet_from.save(ignore_permissions=True)
			pallet_to = frappe.get_doc("Pallet", self.pallet_to)
			pallet_to.qty += batch.batch_qty
			pallet_to.save(ignore_permissions=True)
