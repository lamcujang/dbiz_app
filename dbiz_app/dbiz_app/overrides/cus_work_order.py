import frappe
import json
from frappe.utils import flt, today, getdate, get_link_to_form
from frappe import _
from erpnext.manufacturing.doctype.work_order.work_order import WorkOrder
from erpnext.manufacturing.doctype.bom.bom import get_children as get_bom_children
from erpnext.manufacturing.doctype.production_plan.production_plan import get_bin_details

class cus_work_order(WorkOrder):
    
    
    def before_insert(self):
        pass
        self.skip_transfer = 1
    def get_sub_assembly_items(self,bom_no, bom_data, to_produce_qty, company, warehouse=None, indent=0):
        data = get_bom_children(parent=bom_no)
        for d in data:
            if d.expandable:
                parent_item_code = frappe.get_cached_value("BOM", bom_no, "item")
                stock_qty = (d.stock_qty / d.parent_bom_qty) * flt(to_produce_qty)

                if warehouse:
                    bin_details = get_bin_details(d, company, for_warehouse=warehouse)

                    for _bin_dict in bin_details:
                        if _bin_dict.projected_qty > 0:
                            if _bin_dict.projected_qty > stock_qty:
                                stock_qty = 0
                                continue
                            else:
                                stock_qty = stock_qty - _bin_dict.projected_qty

                if stock_qty > 0:
                    bom_data.append(
                        frappe._dict(
                            {
                                "parent_item_code": parent_item_code,
                                "description": d.description,
                                "production_item": d.item_code,
                                "item_name": d.item_name,
                                "stock_uom": d.stock_uom,
                                "uom": d.stock_uom,
                                "bom_no": d.value,
                                "is_sub_contracted_item": d.is_sub_contracted_item,
                                "bom_level": indent,
                                "indent": indent,
                                "stock_qty": stock_qty,
                            }
                        )
                    )

                    if d.value:
                        self.get_sub_assembly_items(
                            d.value, bom_data, stock_qty, company, warehouse, indent=indent + 1
                        )
                        return bom_data
    
    def on_update(self):
        if self.core_tube:
            frappe.db.set_value('Item', self.production_item, 'core_tubo_wo', self.core_tube)
        if self.item_height_real:
            frappe.db.set_value('Item', self.production_item, 'item_thickness_supplies', self.item_height_real)

@frappe.whitelist()
def setItemBomTable(itemCodeParam,bomParam,qtyParam,woDoc):
    qtyParam = float(qtyParam)
    doc = frappe.get_doc('Work Order', woDoc)

    def get_bom_items(bom_no):
        items = []
        if not bom_no:
            return items
        stack = [bom_no]

        while stack:
            current_bom = stack.pop()
            bom_items = frappe.get_all(
                "BOM Item",
                filters={"parent": current_bom},
                fields=["item_code", "bom_no"]
            )

            for row in bom_items:
                if row.bom_no:
                    items.append({"item_code": row.item_code, "bom_no": row.bom_no})
                    stack.append(row.bom_no)
        return items

    bomItems = get_bom_items(bomParam)


    # if not doc.item_bom_table:
    #     doc.qty = qtyParam
    # else:
    #     doc.qty = doc.qty + qtyParam
    doc.qty = qtyParam

    found = 0
    for bomItem in doc.item_bom_table:
        if bomItem.item == itemCodeParam:
            bomItem.qty = bomItem.qty + qtyParam
            found = 1
            break
    if not found:
        itemQtyRow = frappe.new_doc('Production Plan To Sales Order')
        bomDoc = frappe.get_doc('BOM', bomParam)
        itemQtyRow.operation = bomDoc.operations[0].operation
        itemQtyRow.bom = bomParam
        itemQtyRow.item = itemCodeParam
        itemQtyRow.qty = qtyParam
        doc.append('item_bom_table', itemQtyRow)
        fgItem = frappe.new_doc('FG Items Operation')
        fgItem.item = itemCodeParam
        doc.append('fg_items', fgItem)

    doc.save()
    frappe.response.message = 'Success'

@frappe.whitelist()
def createCustomJobCard(owsName,woName,workstation,conversionFactor,semiAmt,start_date,end_date):
    woDoc = frappe.get_doc('Work Order', woName)
    owsDoc = frappe.get_doc('Operation Workstations', owsName)
    bomDoc = frappe.get_doc('BOM', owsDoc.bom_no)
    job_card = frappe.new_doc("Job Card")
    semiAmtMix = float(semiAmt)
    semiAmt = float(semiAmt) * float(conversionFactor)

    job_card.work_order = woDoc.name
    job_card.operation = owsDoc.operation
    job_card.bom_no = owsDoc.bom_no
    job_card.workstation = workstation
    job_card.production_item = woDoc.production_item
    job_card.workstation_type = owsDoc.workstation_type
    job_card.multiplier_fg = owsDoc.multiplier_fg
    job_card.multiplier = owsDoc.multiplier
    job_card.for_quantity = semiAmt / (owsDoc.multiplier_fg if owsDoc.multiplier_fg else 1)
    job_card.total_completed_qty = 0
    job_card.semi_fg = owsDoc.item_semi_fg
    job_card.for_semi_quantity = semiAmt
    job_card.total_completed_semi_qty = 0
    job_card.company = woDoc.company
    job_card.operation_workstation = owsDoc.name
    job_card.job_card_sales_order = owsDoc.sales_order
    job_card.operation_row_number = owsDoc.name
    job_card.expected_start_date = start_date
    job_card.expected_end_date = end_date
    if float(conversionFactor) != 1:
        job_card.mix_batch_qty = semiAmtMix

    for item in bomDoc.items:
        material = frappe.new_doc('Job Card Item')
        material.item_code = item.item_code
        material.item_name = item.item_name
        material.description = item.description
        work_order_item = next((item for item in woDoc.required_items if item.item_code == item.item_code), None)
        if work_order_item:
            material.source_warehouse = work_order_item.source_warehouse
        else:
            material.source_warehouse = item.source_warehouse
        material.uom = item.uom
        material.stock_uom = item.stock_uom
        material.conversion_factor = item.conversion_factor
        material.convert_qty = (item.stock_qty * semiAmt / bomDoc.quantity) / item.conversion_factor if (item.conversion_factor and item.conversion_factor != 0) else 1
        material.required_qty = item.stock_qty * semiAmt / bomDoc.quantity
        material.allow_alternative_item = item.allow_alternative_item
        
        job_card.append('items', material)



    job_card.insert()
    frappe.response.message = job_card.name

@frappe.whitelist()
def createJobCard(woName,operations):
    if isinstance(operations, str):
        operations = json.loads(operations)
    woDoc = frappe.get_doc('Work Order', woName)
    for operation in operations:
        operation = frappe._dict(operation)
        job_card = frappe.new_doc("Job Card")
        job_card.work_order = woDoc.name
        job_card.operation = operation.get("operation")
        # job_card.workstation = operation.workstation_type
        job_card.production_item = woDoc.production_item
        job_card.production_plan = woDoc.production_plan
        if operation.get("operation") == "CONGDOANTRON":
            job_card.for_quantity = woDoc.qty
            job_card.volume_need_mixed = woDoc.qty
        elif operation.get("operation") == "CONGDOANTHOI":
            job_card.for_quantity = woDoc.volume_blow_need
        elif operation.get("operation") == "CONGDOANCAT":
            job_card.for_quantity = woDoc.volume_carton_need
        elif operation.get("operation") == "CONGDOANHOANTHIEN":
            job_card.for_quantity = woDoc.qty_mixed
            pp = frappe.get_doc('Production Plan', woDoc.production_plan)
            for item in pp.po_items:
                child = frappe.new_doc('Job Card Product Mixed Items')
                child.item_code = item.item_code
                # child.qty = item.planned_qty
                # child.second_qty = item.second_qty
                item_doc = frappe.get_doc('Item', item.item_code)
                child.uom = item_doc.stock_uom
                child.second_uom = item_doc.sencondary_uom

                conversion_factor = 1
                for uom_row in item_doc.uoms:
                    if uom_row.uom == child.uom:
                        conversion_factor = uom_row.conversion_factor
                        break
                child.conversion_factor = conversion_factor
                job_card.append('mixed_items', child)
                
        job_card.wip_warehouse = woDoc.wip_warehouse
        job_card.target_warehouse = woDoc.fg_warehouse
        job_card.company = woDoc.company
        job_card.expected_start_date = today()
        job_card.expected_end_date = today()
        job_card.insert()
        frappe.msgprint(_("Job Card {0} created").format(get_link_to_form("Job Card", job_card.name)), alert=True)
        
    