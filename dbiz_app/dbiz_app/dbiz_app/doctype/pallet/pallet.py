# Copyright (c) 2024, lamnl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import json
from frappe.model.naming import make_autoname
from frappe import _
from frappe.utils import (
	now_datetime,
)


class Pallet(Document):
    def before_save(self):
        self.check_isCompleted()
        self.check_accumulated()
    
    def check_isCompleted(self):
        item = frappe.get_doc("Item", self.item_code)
        if self.qty == item.carton_per_pallet and item.carton_per_pallet > 0:
            self.iscompleted = 1
        elif self.qty > item.carton_per_pallet:
            frappe.throw("Pallet quantity is greater than carton per pallet")
        else:
            self.iscompleted = 0
        return False

    def check_accumulated(self):
        item = frappe.get_doc("Item", self.item_code)
        prefix = str(int(self.qty)) + "/" + str(int(item.carton_per_pallet))
        self.accumulated = prefix

@frappe.whitelist()
def make_pallet(job_card, item_code, qty, employee):
	pallet = frappe.new_doc("Pallet")
	pallet.job_card = job_card
	pallet.item_code = item_code
	pallet.employee = employee
	pallet.qty = float(qty)
	pallet.iscompleted = 0
	pallet.save(ignore_permissions=True)
	return pallet.name

@frappe.whitelist()
def update_pallet(id, job_card, item_code, qty):
	pallet = frappe.get_doc("Pallet", id)
	pallet.job_card = job_card
	pallet.item_code = item_code
	pallet.qty += qty
	pallet.save(ignore_permissions=True)
	return pallet.name

@frappe.whitelist()
def check_pallet_available(job_card, item_code):
   if not job_card or not item_code:
       frappe.throw("Job Card and Item Code are required")

   pallet = frappe.db.sql("""
       SELECT pal.name 
       FROM tabPallet pal
       JOIN tabItem item ON item.item_code = pal.item_code
       WHERE COALESCE((
           SELECT SUM(qty_counted) 
           FROM `tabJob Card` job
           JOIN `tabJob Card Item` item ON item.parent = job.name
           WHERE item.pallet = pal.name
           AND job.status != 'Cancelled'
       ), 0) < item.carton_per_pallet
       AND pal.iscompleted = 0
       AND pal.item_code = %(item_code)s
       AND pal.job_card = %(job_card)s
   """, {
       "job_card": job_card,
       "item_code": item_code
   }, as_dict=1)
   
   if pallet:
       return pallet
   else:
       return make_pallet(job_card, item_code, 0)

@frappe.whitelist()
def check_qty_on_pallet(pallet_id, item_id):
    total_qty = frappe.db.sql("""
        SELECT 
            COALESCE(SUM(item.qty_counted), 0) as total_qty
        FROM 
            `tabOperation Job Card` job
        INNER JOIN 
            `tabOperation Job Card Pallets` item ON item.parent = job.name and item.pallet = %(item_id)s
        WHERE 
            item.pallet = %(pallet_id)s
            AND job.status != 'Cancelled'
    """, {"pallet_id": pallet_id,
          "item_id":item_id}, as_dict=1)
    
    return total_qty[0].total_qty

@frappe.whitelist()
def create_or_update_serial_no(data):
    from frappe.model.naming import make_autoname
    data = frappe._dict(json.loads(data))
    if(data.serial_no):
        serial = frappe.get_doc("Serial No", data.serial_no)
        serial.shift = data.shift
        serial.employee = data.employee
        serial.quantity = data.qty
        serial.sec_qty = data.second_qty
        serial.uom = data.uom
        serial.stock_uom = frappe.get_doc("Item", data.item_code).stock_uom
        serial.pallet = data.pallet
        # serial.warehouse = data.warehouse
        serial.status = "Inactive"
        serial.save(ignore_permissions=True)
        return serial.name
    else:
        # number_series = frappe.db.get_value(
        #     "Item", data.item_code, ["serial_no_series"]
        # )
        serial_no = None
        # if number_series:
        #     serial_no = make_autoname(number_series)
        #     prefix = ""
        prefix = ""
        if data.employee:
            employee = frappe.get_doc("Employee", data.employee)
            prefix += employee.manufacturing_code
        if data.shift:
            shift = frappe.get_doc("Shift Type", data.shift)
            prefix += shift.name
        if prefix:
            prefix = f"{prefix}.DD.MM.YY"
            serial_no = make_autoname(prefix)
        serial = frappe.new_doc("Serial No")
        serial.serial_no = serial_no
        serial.item_code = data.item_code
        serial.shift = data.shift
        serial.employee = data.employee
        serial.quantity = data.qty
        serial.sec_qty = data.second_qty
        serial.uom = data.uom
        serial.stock_uom = frappe.get_doc("Item", data.item_code).stock_uom
        serial.pallet = data.pallet
        # serial.warehouse = data.warehouse
        serial.status = "Inactive"
        if data.job_card:
            job_card = frappe.get_doc("Job Card", data.job_card)
            item_finish = frappe.new_doc("Item Finish Options")
            if job_card.final_item:
                item_finish.item_code = job_card.final_item
            else:
                item_finish.item_code = job_card.production_item
            serial.append("item_finish", item_finish)
        serial.save(ignore_permissions=True)
        return serial.name

@frappe.whitelist()
def create_or_update_batch_no(data):
    data = frappe._dict(json.loads(data))
    if(data.batch_no):
        job_card = frappe.get_doc("Job Card", data.job_card)
        item = frappe.get_doc("Item", data.item_code)
        batch_doc = frappe.get_doc("Batch", data.batch_no)
        batch_doc.item = data.item_code
        batch_doc.shift = data.shift
        batch_doc.reference_doctype = "Work Order"
        batch_doc.reference_name = job_card.work_order
        batch_doc.created = now_datetime()
        batch_doc.uom = data.uom
        batch_doc.stock_uom = item.stock_uom
        batch_doc.sec_qty = data.second_qty
        batch_doc.batch_qty = data.qty
        batch_doc.employee = data.employee
        batch_doc.expiry_date = item.end_of_life
        batch_doc.pallet = data.pallet
        batch_doc.save(ignore_permissions=True)
        return batch_doc.name
    else:
        prefix = "YYYY.DD.MM.-"
        batch_no = make_autoname(prefix)
        # if not batch_no:
        #     frappe.throw(title="Error", msg=_("Batch no series is mandatory for item {0}").format(self.final_item))
        job_card = frappe.get_doc("Job Card", data.job_card)
        item = frappe.get_doc("Item", data.item_code)
        batch_doc = frappe.new_doc("Batch")
        batch_doc.batch_id = batch_no
        batch_doc.item = data.item_code
        batch_doc.shift = data.shift
        batch_doc.reference_doctype = "Work Order"
        batch_doc.reference_name = job_card.work_order
        batch_doc.created = now_datetime()
        batch_doc.uom = data.uom
        batch_doc.stock_uom = item.stock_uom
        batch_doc.sec_qty = data.second_qty
        batch_doc.batch_qty = data.qty
        batch_doc.employee = data.employee
        batch_doc.pallet = data.pallet
        batch_doc.expiry_date = item.end_of_life
        item_finish = frappe.new_doc("Item Finish Options")
        item_finish.item_code = job_card.production_item
        batch_doc.append("item_finish", item_finish)
        batch_doc.operation_job_card = data.opeartion_job_card_previous_step
        batch_doc.save(ignore_permissions=True)
        return batch_doc.name

@frappe.whitelist()
def get_serial_no_by_pallet(pallet):
    item = frappe.db.sql("""
            select item_code,
            item_name,
            batch_no,
            uom,
            warehouse,
            quantity,
            sec_qty,
            pallet,
            name
            from `tabSerial No`
            where pallet = %(pallet)s
            and status = 'Active'
        """, {
        "pallet": pallet
    }, as_dict=True)
    
    return item if item else None

@frappe.whitelist()
def get_batch_no_by_pallet(pallet):
    from dbiz_app.dbiz_app.doctype.stock_transfer_job_card.stock_transfer_job_card import get_available_batch_custom
    item = frappe.get_all("Batch", filters={"pallet": pallet}, fields=["name", "item", "batch_qty", "sec_qty", "uom", "stock_uom", "item_name"])
    if item:
        for i in item:
            batch = get_available_batch_custom(i.name)
            if batch:
                i["warehouse"] = batch[0].warehouse
    return item if item else None

@frappe.whitelist()
def get_sales_order_from_wo(pallet):
    item = frappe.db.sql("""
            select 
            pll.name,
            so.name sales_order, 
            bat.batch_qty qty,
            bat.sec_qty sec_qty,
            bat.name as batch_no,
            sle.warehouse, 
            bat.uom, 
            bat.stock_uom, 
            bat.item,
		    soi.name sales_order_item 
    from `tabPallet` pll
    join `tabBatch` bat on bat.pallet = pll.name and bat.disabled = 0
		join `tabStock Ledger Entry` sl on sl.item_code = bat.item and sl.is_cancelled = 0
		join `tabSerial and Batch Entry` sle on sl.serial_and_batch_bundle = sle.parent  and bat.name = sle.batch_no
    join `tabJob Card` jc on jc.name = pll.job_card
    join `tabWork Order` wo on wo.name = jc.work_order
    join `tabProduction Plan` pp on pp.name = wo.production_plan
    join `tabProduction Plan Sales Order` pso on pso.parent = pp.name
    join `tabSales Order` so on so.name = pso.sales_order
    join `tabSales Order Item` soi on soi.parent = so.name and soi.item_code = pll.item_code and soi.is_sample_item = 0
    where pallet = %(pallet)s
        """, {
        "pallet": pallet
    }, as_dict=True)
    
    return item if item else None
    