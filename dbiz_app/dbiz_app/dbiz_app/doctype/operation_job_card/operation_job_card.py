# Copyright (c) 2024, lamnl and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import (
	get_link_to_form,
	now_datetime,
)
from datetime import datetime
from frappe.model.naming import make_autoname
from erpnext.manufacturing.doctype.job_card.job_card import JobCard
from erpnext.stock.doctype.batch.batch import get_available_batches


class OperationJobCard(Document):

	def before_submit(self):
		self.end_time = now_datetime()
		if self.operation_type == 'Material Transfer For Job Card':
			sum_qty = sum([item.convert_qty for item in self.items if item.convert_qty])
			self.completed_qty = sum_qty
		elif self.operation_type == 'Manufacture Semi-Finished Goods' and self.job_card_operation_name != 'NKBTPC' and self.job_card_operation_name != 'NKCUONMANG':
			sum_qty = sum([item.convert_qty for item in self.details if item.convert_qty])
			self.completed_qty = sum_qty
		elif self.operation_type == 'Manufacture Semi-Finished Goods' and self.job_card_operation_name == 'NKCUONMANG':
			sum_qty = sum([item.qty for item in self.semi_items if item.qty])
			self.completed_qty = sum_qty
		elif self.operation_type =='Packing':
			sum_qty = sum([item.qty for item in self.boxs if item.qty])
			self.completed_qty = sum_qty
		elif self.operation_type == 'Manufacture Semi-Finished Goods' and self.job_card_operation_name == 'NKBTPC':
			sum_qty = sum([item.qty for item in self.bags if item.qty])
			self.completed_qty = sum_qty

		# Process OCR for pallets if they have images
		# if hasattr(self, 'boxs'):
		# 	from dbiz_app.dbiz_app.custom_hook.ocr_api import openAI_ocr
		# 	for pallet in self.boxs:
		# 		if pallet.image:
		# 			try:
		# 				ocr_result = openAI_ocr(pallet.image)
		# 				pallet.second_qty = ocr_result.get("number")
		# 				pallet.reponse = ocr_result.get("reponse")
		# 			except Exception as e:
		# 				frappe.log_error(f"Error processing OCR for pallet: {str(e)}")


	def on_submit(self):
		self.create_stock_entry()

	def on_cancel(self):
		self.update_qty_finished()
		self.cancel_stock_entry()

	def validate(self):
		self.validate_items()

	def validate_items(self):
		if self.job_card_operation_name == 'Material Transfer For Job Card':
			if not self.items:
				frappe.throw("Please add items to make a Stock Entry")
			for item in self.items:
				if not item.convert_qty or item.convert_qty == 0:
					frappe.throw("Please add quantity to make a Stock Entry")
		elif self.job_card_operation_name == 'Manufacture Semi-Finished Goods' and self.job_card_operation_name != 'NKCUONMANG':
			if not self.details:
				frappe.throw("Please add detail to make a Stock Entry")
			for item in self.details:
				if not item.convert_qty or item.convert_qty == 0:
					frappe.throw("Please add quantity to make a Stock Entry")
		elif self.job_card_operation_name == 'Manufacture Semi-Finished Goods' and self.job_card_operation_name == 'NKCUONMANG':
			if not self.semi_items:
				frappe.throw("Please add detail to make a Stock Entry")
			for item in self.semi_items:
				if not item.qty or item.qty == 0:
					frappe.throw("Please add quantity to make a Stock Entry")
		elif self.job_card_operation_name =='Packing':
			if not self.boxs:
				frappe.throw("Please add box to make a Stock Entry")
			for item in self.boxs:
				if not item.batch_no:
					frappe.throw("Please add batch no to make a Stock Entry")
    
	def create_stock_entry(self):
		operation_data = frappe.get_doc("Operation", self.job_card_operation_name)
		job_card = frappe.get_doc("Job Card", self.job_card_name)
		stock_entry = frappe.new_doc("Stock Entry")
		stock_entry.operation_job_card = self.name
		sum_qty = 0
		completed_qty = 0
		if job_card.operation == "CONGDOANHOANTHIEN" and frappe.get_doc("Product Bundle", job_card.production_item) and self.job_card_operation_name == "GCHOANTHIEN":
			self.create_stock_entry_mixed()
			return
		elif operation_data.operation_type == 'Material Transfer For Job Card':
			#TRON THOI CAT GCHT
			stock_entry.purpose = "Material Consumption for Manufacture"
			stock_entry.stock_entry_type = "Material Consumption for Manufacture"
			stock_entry.work_order_semi_fg = job_card.work_order
			# stock_entry.from_bom = 1
			# stock_entry.use_multi_level_bom = 1
			# stock_entry.bom_no = job_card.bom_no
			# stock_entry.fg_completed_qty = job_card.for_quantity
			stock_entry.company = job_card.company
			stock_entry.job_card_semi_fg = job_card.name
			for item in self.items:
				if item.convert_qty:
					stock_entry_item = frappe.new_doc("Stock Entry Detail")
					item_group = frappe.get_value("Item", item.item_code, "item_group")
					stock_entry_item.s_warehouse = operation_data.raw_material_warehouse
					stock_entry_item.allow_zero_valuation_rate = 1
					stock_entry_item.conversion_factor = 1
					stock_entry_item.item_code = item.item_code
					stock_entry_item.item_name = item.item_name
					stock_entry_item.item_group = item_group
					stock_entry_item.qty = item.convert_qty
					stock_entry_item.transfer_qty = item.convert_qty
					stock_entry_item.uom = item.stock_uom
					stock_entry_item.stock_uom = item.stock_uom
					stock_entry_item.expense_account = job_card.wip_account
					stock_entry_item.batch_no = item.batch_no
					stock_entry_item.use_serial_batch_fields = 1
					stock_entry.append("items", stock_entry_item)
			
			# timelog
			self.update_daily_plan()
			self.create_job_card_time_log()
			#---------------------------------------------------------------
		elif self.operation_type == 'Manufacture Semi-Finished Goods' and self.job_card_operation_name != 'NKBTPC' and self.job_card_operation_name != 'NKCUONMANG':
			stock_entry.purpose = "Repack"
			stock_entry.stock_entry_type = "Manufacture Semi-Finished Goods"
			stock_entry.from_bom = 0
			stock_entry.company = job_card.company
			stock_entry.work_order_semi_fg = job_card.work_order,
			stock_entry.job_card_semi_fg = job_card.name
			#nhap BTP vao kho
			for item in self.details:
				sum_qty += item.convert_qty
				stock_entry.to_warehouse = operation_data.target_warehouse
				stock_entry.from_warehouse = None
				stock_entry_item = frappe.new_doc("Stock Entry Detail")
				stock_entry_item.s_warehouse = None
				stock_entry_item.allow_zero_valuation_rate = 1
				stock_entry_item.conversion_factor = 1
				stock_entry_item.t_warehouse = operation_data.target_warehouse
				stock_entry_item.item_code = operation_data.item_mapping
				stock_entry_item.item_name = frappe.get_value("Item", operation_data.item_mapping, "item_name")
				stock_entry_item.item_group = frappe.get_value("Item", operation_data.item_mapping, "item_group")
				stock_entry_item.qty = item.convert_qty
				stock_entry_item.transfer_qty = item.convert_qty
				stock_entry_item.uom = item.uom
				stock_entry_item.stock_uom = item.uom
				# item_data = frappe.get_doc("Item", item.item_code)
				# accountItem = item_data.get("item_defaults", {"company": self.company})[0].get("account_item")
				# stock_entry_item.expense_account = job_card.wip_account
				# create batch for item
				batch_no = None
				prefix = ""
				# if self.employee:
				# 	employee = frappe.get_doc("Employee", self.employee)
				# 	prefix += employee.manufacturing_code
				# if prefix:
				# 	prefix = f"{prefix}.DD.MM.YY.-"
				# 	batch_no = make_autoname(prefix)
				prefix = "YYYY.DD.MM.-"
				batch_no = make_autoname(prefix)
				if not batch_no:
					frappe.throw(title="Error", msg=_("Batch no series is mandatory for item {0}").format(self.final_item))
				batch_doc = frappe.new_doc("Batch")
				batch_doc.batch_id = batch_no
				batch_doc.item = operation_data.item_mapping
				batch_doc.shift = self.shift
				batch_doc.reference_doctype = "Work Order"
				batch_doc.reference_name = job_card.work_order
				batch_doc.created = now_datetime()
				batch_doc.uom = item.uom
				batch_doc.stock_uom = item.uom
				batch_doc.sec_qty = item.qty
				batch_doc.employee = self.employee
				batch_doc.expiry_date = frappe.get_value("Item", operation_data.item_mapping, "end_of_life")
				# XA thi lay itemfinish ben BOM con lai lay productionItem ben job card
				if self.job_card_operation_name == "XA":
					item_finish = frappe.new_doc("Item Finish Options")
					item_finish.item_code = job_card.production_item
					batch_doc.append("item_finish", item_finish)
					# cap nhat me TRON vao me Xa
					if self.opeartion_job_card_previous_step:
						batch_doc.operation_job_card = self.opeartion_job_card_previous_step
						operation_job_card_historie = frappe.get_doc("Operation Job Card", self.opeartion_job_card_previous_step)
						operation_job_card_historie.db_set("qty_finished", operation_job_card_historie.qty_finished + self.completed_qty)
					else:
						batch_doc.operation_job_card = None
				else:
					item_finish = frappe.new_doc("Item Finish Options")
					item_finish.item_code = job_card.production_item
					batch_doc.append("item_finish", item_finish)
					# cap nhat me THOI vao me CUON
					if self.opeartion_job_card_previous_step:
						batch_doc.operation_job_card = self.opeartion_job_card_previous_step
						operation_job_card_historie = frappe.get_doc("Operation Job Card", self.opeartion_job_card_previous_step)
						operation_job_card_historie.db_set("qty_finished", operation_job_card_historie.qty_finished + self.completed_qty)
					else:
						batch_doc.operation_job_card = None
				batch_doc.save(ignore_permissions=True)
				stock_entry_item.batch_no = batch_doc.name
				stock_entry_item.use_serial_batch_fields = 1
				# cap nhat thong tin batch len workstation
				ws_data = frappe.get_doc("Workstation", item.item_code)
				ws_data.db_set("batch_no", batch_doc.name)
				ws_data.db_set("status", "Production")
				stock_entry.append("items", stock_entry_item)
				operation_job_card_item = frappe.get_doc("Operation Job Card Workstations", item.name)
				operation_job_card_item.db_set("batch_no", batch_no)
			job_card.db_set("total_completed_qty", job_card.total_completed_qty + self.completed_qty)
		elif self.operation_type == 'Manufacture Semi-Finished Goods' and self.job_card_operation_name == 'NKCUONMANG':
			stock_entry.purpose = "Repack"
			stock_entry.stock_entry_type = "Manufacture Semi-Finished Goods"
			stock_entry.from_bom = 0
			stock_entry.company = job_card.company
			stock_entry.work_order_semi_fg = job_card.work_order,
			stock_entry.job_card_semi_fg = job_card.name
			#nhap BTP vao kho
			for item in self.semi_items:
				sum_qty += item.qty
				stock_entry.to_warehouse = operation_data.target_warehouse
				stock_entry.from_warehouse = None
				stock_entry_item = frappe.new_doc("Stock Entry Detail")
				stock_entry_item.s_warehouse = None
				stock_entry_item.allow_zero_valuation_rate = 1
				stock_entry_item.conversion_factor = 1
				stock_entry_item.t_warehouse = operation_data.target_warehouse
				stock_entry_item.item_code = operation_data.item_mapping
				stock_entry_item.item_name = frappe.get_value("Item", operation_data.item_mapping, "item_name")
				stock_entry_item.item_group = frappe.get_value("Item", operation_data.item_mapping, "item_group")
				stock_entry_item.qty = item.qty
				stock_entry_item.transfer_qty = item.qty
				stock_entry_item.uom = item.stock_uom
				stock_entry_item.stock_uom = item.stock_uom
				# item_data = frappe.get_doc("Item", item.item_code)
				# accountItem = item_data.get("item_defaults", {"company": self.company})[0].get("account_item")
				# stock_entry_item.expense_account = job_card.wip_account
				# create batch for item
				batch_no = None
				prefix = ""
				# if self.employee:
				# 	employee = frappe.get_doc("Employee", self.employee)
				# 	prefix += employee.manufacturing_code
				# if prefix:
				# 	prefix = f"{prefix}.DD.MM.YY.-"
				# 	batch_no = make_autoname(prefix)
				prefix = "YYYY.DD.MM.-"
				batch_no = make_autoname(prefix)
				if not batch_no:
					frappe.throw(title="Error", msg=_("Batch no series is mandatory for item {0}").format(self.final_item))
				batch_doc = frappe.new_doc("Batch")
				batch_doc.batch_id = batch_no
				batch_doc.item = operation_data.item_mapping
				batch_doc.shift = self.shift
				batch_doc.reference_doctype = "Work Order"
				batch_doc.reference_name = job_card.work_order
				batch_doc.created = now_datetime()
				batch_doc.uom = item.stock_uom
				batch_doc.stock_uom = item.stock_uom
				batch_doc.sec_qty = item.qty
				batch_doc.employee = self.employee
				batch_doc.expiry_date = frappe.get_value("Item", operation_data.item_mapping, "end_of_life")
				# XA thi lay itemfinish ben BOM con lai lay productionItem ben job card
				item_finish = frappe.new_doc("Item Finish Options")
				item_finish.item_code = job_card.production_item
				batch_doc.append("item_finish", item_finish)
				# cap nhat me THOI vao me CUON
				if self.opeartion_job_card_previous_step:
					batch_doc.operation_job_card = self.opeartion_job_card_previous_step
					operation_job_card_historie = frappe.get_doc("Operation Job Card", self.opeartion_job_card_previous_step)
					operation_job_card_historie.db_set("qty_finished", operation_job_card_historie.qty_finished + self.completed_qty)
				else:
					batch_doc.operation_job_card = None
				batch_doc.save(ignore_permissions=True)
				stock_entry_item.batch_no = batch_doc.name
				stock_entry_item.use_serial_batch_fields = 1
				stock_entry.append("items", stock_entry_item)
				operation_job_card_item = frappe.get_doc("Operation Job Card Semi Items", item.name)
				operation_job_card_item.db_set("batch_no", batch_no)
			job_card.db_set("total_completed_qty", job_card.total_completed_qty + self.completed_qty)
		elif self.operation_type == 'Manufacture Semi-Finished Goods' and self.job_card_operation_name == 'NKBTPC':
			stock_entry.purpose = "Repack"
			stock_entry.stock_entry_type = "Manufacture Semi-Finished Goods"
			stock_entry.from_bom = 0
			stock_entry.company = job_card.company
			stock_entry.work_order_semi_fg = job_card.work_order,
			stock_entry.job_card_semi_fg = job_card.name
			#nhap BTP vao kho
			for item in self.bags:
				sum_qty += item.qty
				stock_entry.to_warehouse = operation_data.target_warehouse
				stock_entry.from_warehouse = None
				stock_entry_item = frappe.new_doc("Stock Entry Detail")
				stock_entry_item.s_warehouse = None
				stock_entry_item.allow_zero_valuation_rate = 1
				stock_entry_item.conversion_factor = 1
				stock_entry_item.t_warehouse = operation_data.target_warehouse
				stock_entry_item.item_code = item.item_code
				stock_entry_item.item_name = frappe.get_value("Item", item.item_code, "item_name")
				stock_entry_item.item_group = frappe.get_value("Item", item.item_code, "item_group")
				stock_entry_item.qty = item.qty
				stock_entry_item.transfer_qty = item.qty
				stock_entry_item.uom = item.stock_uom
				stock_entry_item.stock_uom = item.stock_uom
				# item_data = frappe.get_doc("Item", item.item_code)
				# accountItem = item_data.get("item_defaults", {"company": self.company})[0].get("account_item")
				# stock_entry_item.expense_account = job_card.wip_account
				batch = frappe.get_doc("Batch", item.batch_no)
				# cap nhat me CAT vao me CUON
				if self.opeartion_job_card_previous_step:
					batch.operation_job_card = self.opeartion_job_card_previous_step
					operation_job_card_historie = frappe.get_doc("Operation Job Card", self.opeartion_job_card_previous_step)
					operation_job_card_historie.db_set("qty_finished", operation_job_card_historie.qty_finished + self.completed_qty)
				else:
					batch.operation_job_card = None
    
				batch.sec_qty = item.second_qty
				batch.save(ignore_permissions=True)
				stock_entry_item.batch_no = batch.name
				stock_entry_item.use_serial_batch_fields = 1
				
				stock_entry.append("items", stock_entry_item)
			job_card.db_set("total_completed_qty", job_card.total_completed_qty + self.completed_qty)
		elif self.operation_type == 'Packing':
			#---------------------------------------------------------------
			stock_entry.purpose = "Manufacture"
			stock_entry.stock_entry_type = "Manufacture"
			stock_entry.from_bom = 0
			stock_entry.company = job_card.company
			stock_entry.use_multi_level_bom = 1
			stock_entry.fg_completed_qty = self.completed_qty
			
			stock_entry.work_order_semi_fg = job_card.work_order
			# stock_entry.from_warehouse = job_card.wip_warehouse
			stock_entry.to_warehouse = operation_data.target_warehouse
			
			for item in self.boxs:
				sum_qty += item.qty
				stock_entry_item = frappe.new_doc("Stock Entry Detail")
				stock_entry_item.allow_zero_valuation_rate = 1
				stock_entry_item.conversion_factor = 1
				stock_entry_item.item_code = item.item_code
				stock_entry_item.item_name = item.item_name
				stock_entry_item.item_group = frappe.get_value("Item", item.item_code, "item_group")
				stock_entry_item.qty = item.qty
				stock_entry_item.transfer_qty = item.qty
				stock_entry_item.uom = item.stock_uom
				stock_entry_item.stock_uom = item.stock_uom
				stock_entry_item.batch_no = item.batch_no
				stock_entry_item.use_serial_batch_fields = 1
				item_data = frappe.get_doc("Item", item.item_code)
				# accountItem = item_data.get("item_defaults", {"company": self.company})[0].get("account_item")
				# stock_entry_item.expense_account = accountItem
				stock_entry_item.is_finished_item = 1
				if item.pallet:
					pallet = frappe.get_doc("Pallet", item.pallet)
					pallet.qty = pallet.qty + item.qty
					pallet.save(ignore_permissions=True)
				if item.batch_no:
					batch_no = frappe.get_doc("Batch", item.batch_no)
					batch_no.sec_qty = item.second_qty
					# cap nhat me CAT vao me DONGTHUNG
					if self.opeartion_job_card_previous_step:
						batch_no.operation_job_card = self.opeartion_job_card_previous_step
						operation_job_card_historie = frappe.get_doc("Operation Job Card", self.opeartion_job_card_previous_step)
						operation_job_card_historie.db_set("qty_finished", operation_job_card_historie.qty_finished + self.completed_qty)
					else:
						batch_no.operation_job_card = None
					batch_no.save(ignore_permissions=True)
				stock_entry.append("items", stock_entry_item)
			job_card.db_set("total_completed_qty", job_card.total_completed_qty + self.completed_qty)
      
		stock_entry.insert(ignore_permissions=True)
		stock_entry.submit()
		frappe.msgprint(_("Stock Entry {0} created").format(get_link_to_form("Stock Entry", stock_entry.name)), alert=True)
	
	def create_stock_entry_mixed(self):
		def create_stock_entry_production():
			stock_entry_production = frappe.new_doc("Stock Entry")
			stock_entry_production.purpose = "Manufacture"
			stock_entry_production.stock_entry_type = "Manufacture"
			stock_entry_production.from_bom = 0
			stock_entry_production.operation_job_card = self.name
			stock_entry_production.company = job_card.company
			stock_entry_production.use_multi_level_bom = 1
			stock_entry_production.fg_completed_qty = self.completed_qty
			
			stock_entry_production.work_order_semi_fg = job_card.work_order
			# stock_entry.from_warehouse = job_card.wip_warehouse
			stock_entry_production.to_warehouse = operation_data.target_warehouse
			
			for item in self.boxs:
				stock_entry_item = frappe.new_doc("Stock Entry Detail")
				stock_entry_item.allow_zero_valuation_rate = 1
				stock_entry_item.conversion_factor = 1
				stock_entry_item.item_code = item.item_code
				stock_entry_item.item_name = item.item_name
				stock_entry_item.item_group = frappe.get_value("Item", item.item_code, "item_group")
				stock_entry_item.qty = item.qty
				stock_entry_item.transfer_qty = item.qty
				stock_entry_item.uom = item.stock_uom
				stock_entry_item.stock_uom = item.stock_uom
				stock_entry_item.batch_no = item.batch_no
				stock_entry_item.use_serial_batch_fields = 1
				item_data = frappe.get_doc("Item", item.item_code)
				# accountItem = item_data.get("item_defaults", {"company": self.company})[0].get("account_item")
				# stock_entry_item.expense_account = accountItem
				stock_entry_item.is_finished_item = 1
				if item.pallet:
					pallet = frappe.get_doc("Pallet", item.pallet)
					pallet.qty = pallet.qty + item.qty
					pallet.save(ignore_permissions=True)
				if item.batch_no:
					batch_no = frappe.get_doc("Batch", item.batch_no)
					batch_no.sec_qty = item.second_qty
					# cap nhat me CAT vao me DONGTHUNG
					if self.opeartion_job_card_previous_step:
						batch_no.operation_job_card = self.opeartion_job_card_previous_step
						operation_job_card_historie = frappe.get_doc("Operation Job Card", self.opeartion_job_card_previous_step)
						operation_job_card_historie.db_set("qty_finished", operation_job_card_historie.qty_finished + self.completed_qty)
					else:
						batch_no.operation_job_card = None
					batch_no.save(ignore_permissions=True)
				stock_entry_production.append("items", stock_entry_item)
			job_card.db_set("total_completed_qty", job_card.total_completed_qty + self.completed_qty)
			stock_entry_production.insert(ignore_permissions=True)
			stock_entry_production.submit()
			frappe.msgprint(_("Stock Entry {0} created").format(get_link_to_form("Stock Entry", stock_entry_production.name)), alert=True)
		def create_stock_entry_items(sum_qty):
			stock_entry = frappe.new_doc("Stock Entry")
			stock_entry.purpose = "Material Consumption for Manufacture"
			stock_entry.stock_entry_type = "Material Consumption for Manufacture"
			stock_entry.work_order_semi_fg = job_card.work_order
			stock_entry.company = job_card.company
			stock_entry.job_card_semi_fg = job_card.name

			for item in product_bundle.items:
				item_data = frappe.get_doc("Item", item.item_code)
				qty_needed = item.qty * sum_qty
				if item_data.has_batch_no:
					# Lấy batch theo FIFO, từng kho, đúng nghiệp vụ Serial and Batch Bundle
					batch_warehouse_list = frappe.db.sql('''
						SELECT
							sbe.batch_no,
							sbe.warehouse,
							SUM(sbe.qty) AS qty
						FROM
							`tabStock Ledger Entry` sle
							JOIN `tabSerial and Batch Entry` sbe ON sle.serial_and_batch_bundle = sbe.parent
							JOIN `tabBatch` b ON sbe.batch_no = b.NAME
						WHERE
							b.disabled = 0
							AND sle.is_cancelled = 0
							AND (b.expiry_date >= SYSDATE() OR b.expiry_date IS NULL)
							AND sle.item_code = %s
						GROUP BY
							sbe.batch_no,
							sbe.warehouse
						HAVING
							qty > 0
						ORDER BY
							b.creation ASC
					''', (item_data.item_code,), as_dict=True)

					remaining_qty = qty_needed
					for bw in batch_warehouse_list:
						if remaining_qty <= 0:
							break
						export_qty = min(bw["qty"], remaining_qty)
						stock_entry_item = frappe.new_doc("Stock Entry Detail")
						stock_entry_item.s_warehouse = bw["warehouse"]
						stock_entry_item.allow_zero_valuation_rate = 1
						stock_entry_item.conversion_factor = 1
						stock_entry_item.item_code = item_data.item_code
						stock_entry_item.item_name = item_data.item_name
						stock_entry_item.item_group = item_data.item_group
						stock_entry_item.qty = export_qty
						stock_entry_item.transfer_qty = export_qty
						stock_entry_item.uom = item.uom
						stock_entry_item.stock_uom = item.uom
						stock_entry_item.batch_no = bw["batch_no"]
						stock_entry_item.expense_account = job_card.wip_account
						stock_entry_item.use_serial_batch_fields = 1
						stock_entry.append("items", stock_entry_item)
						remaining_qty -= export_qty

					if remaining_qty > 0:
						frappe.throw(f"Không đủ tồn kho cho item {item_data.item_code}")
				else:
					stock_entry_item = frappe.new_doc("Stock Entry Detail")
					stock_entry_item.s_warehouse = operation_data.raw_material_warehouse
					stock_entry_item.allow_zero_valuation_rate = 1
					stock_entry_item.conversion_factor = 1
					stock_entry_item.item_code = item_data.item_code
					stock_entry_item.item_name = item_data.item_name
					stock_entry_item.item_group = item_data.item_group
					stock_entry_item.qty = qty_needed
					stock_entry_item.transfer_qty = qty_needed
					stock_entry_item.uom = item.uom
					stock_entry_item.stock_uom = item.uom
					stock_entry_item.expense_account = job_card.wip_account
					stock_entry.append("items", stock_entry_item)
			# Save và submit stock entry
			stock_entry.insert(ignore_permissions=True)
			stock_entry.submit()

			self.create_job_card_time_log()

		operation_data = frappe.get_doc("Operation", self.job_card_operation_name)
		job_card = frappe.get_doc("Job Card", self.job_card_name)
		product_bundle = frappe.get_doc("Product Bundle", job_card.production_item)
		sum_qty = sum([item.qty for item in self.boxs if item.qty])
		# Nhap kho thanh pham
		create_stock_entry_production()
		# xuat kho nguyen lieu
		create_stock_entry_items(sum_qty)

	def create_job_card_time_log(self):
		durations = 0
		datetime_format = "%Y-%m-%d %H:%M:%S"
		start_dt = None
		end_dt = None
		if self.start_time and self.end_time:
			if isinstance(self.start_time, str):
				start_dt = datetime.strptime(self.start_time, datetime_format)
			else:
				start_dt = self.start_time

			if isinstance(self.end_time, str):
				end_dt = datetime.strptime(self.end_time, datetime_format)
			else:
				end_dt = self.end_time
			time_diff = end_dt - start_dt  # Note: Changed order to end - start
			durations = time_diff.total_seconds() / 60
		job_card = frappe.get_doc("Job Card", self.job_card_name)
		job_card_time_log = frappe.new_doc("Job Card Time Log")
		job_card_time_log.parent = self.job_card_name
		job_card_time_log.parenttype = "Job Card"
		job_card_time_log.parentfield = "time_logs"
		job_card_time_log.operation = self.job_card_operation_name
		job_card_time_log.employee = self.employee
		job_card_time_log.from_time = start_dt	
		job_card_time_log.to_time = end_dt
		job_card_time_log.time_in_mins = durations
		job_card_time_log.completed_qty = self.completed_qty
		job_card_time_log.insert()
		# job_card.db_set("total_completed_qty", job_card.total_completed_qty + self.completed_qty)
		work_order = frappe.get_doc("Work Order", job_card.work_order)
		if work_order.status == "Not Started" or work_order.status == "Open" or work_order.status == "Submitted":
			frappe.db.set_value('Work Order', work_order.name, 'status', 'Work In Progress')
   
	def update_daily_plan(self):
		job_card = frappe.get_doc("Job Card", self.job_card_name)
		datetime_format = "%Y-%m-%d %H:%M:%S"
		start_time = None
		if isinstance(self.start_time, str):
			start_time = datetime.strptime(self.start_time, datetime_format)
		else:
			start_time = self.start_time
		if job_card.daily_plans:
			for daily_plan in job_card.daily_plans:
				row = frappe.get_doc("Daily Plan Items", daily_plan.name)
				if job_card.use_funnel == 'USE_SHARE' and daily_plan.plan_start_date <= start_time.date() and daily_plan.plan_end_date >= start_time.date():
					if self.mortar == 'MORTAR_MAIN':
						row.db_set("completed_qty", row.completed_qty + self.completed_qty)
						row.db_set("completed_mortal_qty", row.completed_mortal_qty + 1 if self.remaining_mixed_qty >= 1 else self.remaining_mixed_qty)
					else:
						row.db_set("completed_sec_qty", row.completed_sec_qty + self.completed_qty)
						row.db_set("completed_mortal_sec_qty", row.completed_mortal_sec_qty + 1 if self.remaining_mixed_qty >= 1 else self.remaining_mixed_qty)
				elif job_card.use_funnel == 'USE_PRIVATE' and daily_plan.funnel == self.funnel and daily_plan.plan_start_date <= start_time.date() and daily_plan.plan_end_date >= start_time.date():
					if self.mortar == 'MORTAR_MAIN':
						row.db_set("completed_qty", row.completed_qty + self.completed_qty)
						row.db_set("completed_mortal_qty", row.completed_mortal_qty + 1 if self.remaining_mixed_qty >= 1 else self.remaining_mixed_qty)
					else:
						row.db_set("completed_sec_qty", row.completed_sec_qty + self.completed_qty)
						row.db_set("completed_mortal_sec_qty", row.completed_mortal_sec_qty + 1 if self.remaining_mixed_qty >= 1 else self.remaining_mixed_qty)
	
	def cancel_stock_entry(self):
		stock_entry_name = frappe.db.get_value("Stock Entry", {"operation_job_card": self.name}, "name")
		stock_entry = frappe.get_doc("Stock Entry", stock_entry_name)
		if stock_entry.docstatus == 1:
			# for item in stock_entry.items:
			# 	if item.serial_and_batch_bundle:
			# 		serial_batch_and_bundle = frappe.get_doc("Serial and Batch Bundle", item.serial_and_batch_bundle)
			# 		serial_batch_and_bundle.cancel()
			return stock_entry.cancel()
		else:
			return None

	def update_qty_finished(self):
		job_card = frappe.get_doc("Job Card", self.job_card_name)
		job_card.db_set("total_completed_qty", job_card.total_completed_qty - self.completed_qty)

@frappe.whitelist()
def get_list_job_card_from_work_order(work_order, operation):
	return frappe.get_all("Job Card", filters={"work_order": work_order, "operation": operation,
                                            # "expected_start_date": ("<=", now_datetime()), "expected_end_date": (">=", now_datetime()),
                                            "status": ("in", ["Work in Progress", "Open"]),
                                            },order_by="expected_start_date desc", fields=["name","completed_qty","for_semi_quantity"])
 
@frappe.whitelist()
def get_conversion_factor(item_code, uom):
	item = frappe.db.sql("""
		SELECT 
			uom_conversion_detail.conversion_factor, 
			item.item_code
		FROM 
			`tabUOM Conversion Detail` uom_conversion_detail 
		JOIN 
			`tabItem` item 
		ON 
			uom_conversion_detail.parent = item.name 
		WHERE 
			item.item_code = %(item_code)s
		AND 
			uom_conversion_detail.uom = %(uom)s
	""", {
		"item_code": item_code, 
		"uom": uom
	}, as_dict=True)

	return item[0].conversion_factor if item else 0

@frappe.whitelist()
def get_pre_step_op_jc(job_card_name, operation_name):
	operation_historie = frappe.db.sql("""
			select name from `tabOperation Job Card`
			where job_card_name = %(job_card_name)s
			and job_card_operation_name = %(operation_name)s
			and creation = (SELECT max(creation)  from `tabOperation Job Card`
			where job_card_name = %(job_card_name)s
			and job_card_operation_name = %(operation_name)s
			and docstatus = 1)
			and docstatus = 1
		""", {
		"job_card_name": job_card_name,
		"operation_name": operation_name
	}, as_dict=True)

	return operation_historie[0].name if len(operation_historie) > 0 else None

def get_batch_fifo_with_stock(item_code, qty_needed):
    """
    Lấy batch theo FIFO với tồn kho thực tế
    """
    # Lấy tất cả batch có stock trong kho, sắp xếp theo thời gian tạo (FIFO)
    batches = frappe.db.sql("""
        SELECT 
            b.name as batch_no,
            b.item,
            b.batch_qty,
            b.creation,
            sle.actual_qty as stock_qty,
            sle.warehouse
        FROM `tabBatch` b
        INNER JOIN `tabStock Ledger Entry` sle ON sle.batch_no = b.name
        WHERE b.item = %s 
        AND sle.actual_qty > 0
        ORDER BY b.creation ASC
    """, (item_code), as_dict=True)
    
    if not batches:
        return None, 0
    
    # Tính toán số lượng cần lấy từ từng batch
    remaining_qty = qty_needed
    batch_allocations = []
    
    for batch in batches:
        available_qty = min(batch.stock_qty, remaining_qty)
        if available_qty > 0:
            batch_allocations.append({
                'batch_no': batch.batch_no,
                'qty': available_qty,
                'warehouse': batch.warehouse,
                'stock_qty': batch.stock_qty  # Tồn kho thực tế của batch
            })
            remaining_qty -= available_qty
            
        if remaining_qty <= 0:
            break
    
    return batch_allocations, qty_needed - remaining_qty


