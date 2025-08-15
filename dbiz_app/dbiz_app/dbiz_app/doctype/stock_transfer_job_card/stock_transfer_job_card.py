# Copyright (c) 2024, lamnl and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import (
	get_link_to_form,
	now_datetime,
)


class StockTransferJobCard(Document):
	
	def on_submit(self):
		if self.transfer_type in ["CKCUONMANG", "CKXEBTP","CHUYENKHOTHANHPHAM","CHUYENHANGGIACONG"]:
			self.create_stock_entry()
		else:
			self.create_material_request()

	def validate(self):
		if self.transfer_type in ["CKCUONMANG", "CKXEBTP"]:
			for item in self.items:
				if not item.batch_no:
					frappe.throw("Batch No is required for this transfer type")

	def create_stock_entry(self):
		stock_entry = frappe.new_doc("Stock Entry")
		stock_entry.purpose = "Material Transfer"
		stock_entry.stock_entry_type = "Material Transfer"
		stock_entry.company = frappe.get_value("Warehouse", self.target_warehouse, "company")
		stock_entry.to_warehouse = self.target_warehouse
		stock_entry.from_warehouse = self.source_warehouse
		for item in self.items:
			stock_entry_item = frappe.new_doc("Stock Entry Detail")
			stock_entry_item.allow_zero_valuation_rate = 1
			stock_entry_item.s_warehouse = item.source_warehouse
			stock_entry_item.t_warehouse = self.target_warehouse
			stock_entry_item.conversion_factor = 1
			stock_entry_item.item_code = item.item_code
			stock_entry_item.item_name = item.item_name
			stock_entry_item.item_group = frappe.get_value("Item", item.item_code, "item_group")
			stock_entry_item.qty = item.qty
			stock_entry_item.transfer_qty = item.qty
			stock_entry_item.uom = item.uom
			stock_entry_item.stock_uom = item.uom
			if item.batch_no:
				stock_entry_item.use_serial_batch_fields = 1
				stock_entry_item.batch_no = item.batch_no
			if item.serial_no:
				stock_entry_item.use_serial_batch_fields = 1
				stock_entry_item.serial_no = item.serial_no
			stock_entry.append("items", stock_entry_item)
		stock_entry.save(ignore_permissions=True)
		stock_entry.submit()
		frappe.msgprint(_("Stock Entry {0} created").format(get_link_to_form("Stock Entry", stock_entry.name)), alert=True)
	
	def create_material_request(self):
		material_request = frappe.new_doc("Material Request")
		material_request.transaction_date = now_datetime()
		material_request.set_warehouse = self.target_warehouse
		material_request.company = frappe.get_value("Warehouse", self.target_warehouse, "company")
		material_request.material_request_type = "Material Transfer"
		for item in self.items:
			material_request_item = frappe.new_doc("Material Request Item")
			material_request_item.from_warehouse = self.source_warehouse
			material_request_item.warehouse = self.target_warehouse
			material_request_item.set_from_warehouse = self.source_warehouse
			material_request_item.item_code = item.item_code
			material_request_item.item_name = item.item_name
			material_request_item.item_group = frappe.get_value("Item", item.item_code, "item_group")
			material_request_item.qty = item.qty
			material_request_item.uom = item.uom
			material_request_item.stock_uom = item.stock_uom
			material_request_item.stock_qty = item.convert_qty
			material_request_item.conversion_factor = item.conversion_factor if item.conversion_factor != 0 else 1
			material_request_item.schedule_date = now_datetime()
			material_request.append("items", material_request_item)
		material_request.save(ignore_permissions=True)
		material_request.submit()
		frappe.msgprint(_("Material Request {0} created").format(get_link_to_form("Material Request", material_request.name)), alert=True)

@frappe.whitelist()
def make_stock_transfer_job_card(job_card):
	result = []
	job_card = frappe.get_doc("Job Card", job_card)
	batchs = frappe.get_all("Batch", filters={"reference_name": job_card.name, "reference_doctype": "Job Card", "batch_qty": (">", 0)}, fields=["name"])
	if batchs:
		for batch in batchs:
			batch_qty_warhouse = get_available_batch_custom(batch.name)
			if batch_qty_warhouse:
				for batch_qty in batch_qty_warhouse:
					result.append({
						"batch_no": batch_qty.name,
						"item_code": batch_qty.item,
						"item_name": batch_qty.item_name,
						"uom": batch_qty.stock_uom,
						"qty": batch_qty.get("qty", 0),
						"warehouse": batch_qty.get("warehouse")
					})
	return result

@frappe.whitelist()
def get_available_batch_custom(batch_no):
	items = frappe.db.sql("""
		SELECT
			b.name,
			sbe.warehouse,
			SUM( sbe.qty ) AS qty ,
			b.item, b.item_name,b.stock_uom
		FROM
			`tabStock Ledger Entry` sle
			JOIN `tabSerial and Batch Entry` sbe ON sle.serial_and_batch_bundle = sbe.parent
			JOIN `tabBatch` b ON sbe.batch_no = b.NAME 
		WHERE
			b.disabled = 0 
			AND sle.is_cancelled = 0 
			AND ( b.expiry_date >= SYSDATE() OR b.expiry_date IS NULL ) 
			AND b.name = %s 
		GROUP BY
			b.name,
			sbe.warehouse,
			b.item, b.item_name,b.stock_uom 
		HAVING
			qty > 0 
		ORDER BY
			b.creation ASC;
	""", batch_no, as_dict=1)

	return items