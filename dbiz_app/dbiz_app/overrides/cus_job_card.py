import frappe
import re
from frappe.model.mapper import get_mapped_doc
from frappe.utils import (
	get_link_to_form,
	now_datetime,
)
from frappe.utils import (
	flt,
)
from erpnext.manufacturing.doctype.job_card.job_card import JobCard

class cus_job_card(JobCard):
    def onload(self):
        pass
    def on_submit(self):
        if self.operation == "CONGDOANTHOI" and self.workstation_blow:
            jc_mix_list = frappe.get_all("Job Card", filters={"work_order": self.work_order, "operation": "CONGDOANTRON", "docstatus": 0})
            for jc in jc_mix_list:
                job_card_mix = frappe.get_doc("Job Card", jc.name)
                job_card_mix.workstation_blow = []
                for workstation in self.workstation_blow:
                    workstation_blow_new = frappe.new_doc("Workstation Options")
                    workstation_blow_new.workstation = workstation.workstation
                    job_card_mix.append("workstation_blow", workstation_blow_new)
                job_card_mix.save(ignore_permissions=True)

    def autoname(self):
        operation_data = frappe.get_doc("Operation", self.operation)
        parts = self.production_plan.split('-')
        
        if len(parts) != 3:
            return self.production_plan
        
        middle_number = parts[1]
        
        year_last_two = parts[0][-2:]
        
        pp_prefix = f"{middle_number}.{year_last_two}"
        item_suffix = None
        match = re.search(r'[A-Z]{3}\d{2}', self.production_item)
        if match:
            item_suffix = match.group(0)
        else:
            item_suffix = self.production_item.split('-')[0]
        name_prefix = f"{operation_data.short_key}{pp_prefix}{item_suffix}"
        new_name = f"{name_prefix}/1"
        self.times_of_issuance = 1
        if frappe.db.exists("Job Card", new_name):
            count_operation = frappe.get_all("Job Card", filters={"work_order": self.work_order, "operation": self.operation})
            new_name = f"{name_prefix}/{len(count_operation) + 1}"
            self.times_of_issuance = len(count_operation) + 1
        
        self.name = new_name

    def set_status(self, update_status=False):
        if self.status == "On Hold" and self.docstatus == 0:
            return

        self.status = {0: "Open", 1: "Submitted", 2: "Cancelled"}[self.docstatus or 0]

        if self.docstatus < 2:
            # if flt(self.for_quantity) <= flt(self.transferred_qty):
            #     self.status = "Material Transferred"

            if self.docstatus == 1 and (self.for_quantity <= self.total_completed_qty):
                self.status = "Completed"

            if update_status:
                self.db_set("status", self.status)

            if self.status in ["Completed", "Work In Progress"]:
                status = {
                    "Completed": "Off",
                    "Work In Progress": "Production",
                }.get(self.status)

                self.update_status_in_workstation(status)

    def before_insert(self):
        if self.is_copy:
            job_card_copy = frappe.get_doc("Job Card", self.job_card_copy)
            def strip_standard_fields(item):
                standard_fields = {'idx', 'name', 'parent', 'parentfield', 'parenttype',
                                'owner', 'creation', 'modified', 'modified_by', 'docstatus'}
                item_dict = item.as_dict()
                return {
                    k: v for k, v in item_dict.items()
                    if k not in standard_fields and not k.startswith('__') and not k.startswith('_')
                }

            def compare_table_data(list1, list2):
                if len(list1) != len(list2):
                    return False
                for item1, item2 in zip(list1, list2):
                    a = strip_standard_fields(item1)
                    b = strip_standard_fields(item2)
                    if a != b:
                        return False
                return True

            if self.use_funnel == 'USE_SHARE':
                if compare_table_data(self.items, job_card_copy.items):
                    frappe.throw("Nguyên vật liệu giống hoàn toàn bản gốc. Hãy thay đổi ít nhất một mục để lưu.")
            else:
                if not compare_table_data(self.items, job_card_copy.items):
                    return 
                if not compare_table_data(self.funnel_b_data, job_card_copy.funnel_b_data):
                    return
                if not compare_table_data(self.funnel_c_data, job_card_copy.funnel_c_data):
                    return

                frappe.throw("Nguyên vật liệu giống hoàn toàn bản gốc. Hãy thay đổi ít nhất một mục để lưu.")

        if self.times_of_issuance == 0 or not self.times_of_issuance:
            count_operation = frappe.get_all("Job Card", filters={"work_order": self.work_order, "operation": self.operation})
            self.times_of_issuance = len(count_operation) + 1

    def before_submit(self):
        if self.use_funnel == 'USE_SHARE' and self.operation == "CONGDOANTRON":
            if not self.workstation:
                frappe.throw("Máy trộn không được để trống.")
        elif self.use_funnel == 'USE_PRIVATE' and self.operation == "CONGDOANTRON":
            if self.items and not self.workstation_a:
                frappe.throw("Máy trộn phễu A không được để trống.")
            if self.funnel_b_data and not self.workstation_b:
                frappe.throw("Máy trộn phễu B không được để trống.")
            if self.funnel_c_data and not self.workstation_c:
                frappe.throw("Máy trộn phễu C không được để trống.")
                
    def update_bom(self):
        def update_bom_item(bom_no,qty_need,workstation, details):
            workstation = frappe.get_doc("Workstation", workstation)
            bom = None
            if frappe.db.exists("BOM", bom_no):
                bom = frappe.get_doc("BOM", bom_no)
            else:
                bom = frappe.new_doc("BOM")
            bom.item = self.production_item
            bom.company = self.company
            bom.quantity = qty_need
            # operation
            if bom.operations:
                for operation in bom.operations:
                    if operation.operation == self.operation:
                        operation.workstation_type = workstation.workstation_type
                        break
            else:
                bom.append("operations", {
                    "operation": self.operation,
                    "workstation_type": workstation.workstation_type
                })
            # item
            if bom.items:
                bom.items = []
            for item in details:
                bom_item = frappe.new_doc("BOM Item")
                item = frappe.get_doc("Item", item.item_code)
                bom_item.item_code = item.item_code
                bom_item.item_name = item.item_name
                bom_item.description = item.description
                bom_item.qty = item.kg_qty_main
                bom_item.uom = item.uom
                bom_item.conversion_factor = item.conversion_factor
                bom_item.stock_uom = item.stock_uom
                bom_item.stock_qty = item.stock_qty
                bom.items.append(bom_item)  
            # bom.submit()             
        
        if self.use_funnel == 'USE_SHARE':
            update_bom_item(self.bom_no, self.volume_real_mixed, self.workstation, self.items)
        elif self.use_funnel == 'USE_PRIVATE':
            if self.items:
                update_bom_item(self.bom_no, self.volume_real_mixed_a, self.workstation_a, self.items)
            if self.funnel_b_data:
                update_bom_item(self.bom_no_b, self.volume_real_mixed_b, self.workstation_b, self.funnel_b_data)
            if self.funnel_c_data and not self.workstation_c:
                update_bom_item(self.bom_no_c, self.volume_real_mixed_c, self.workstation_c, self.funnel_c_data)


@frappe.whitelist()
def make_material_request(source_name, target_doc=None):
    def update_item(obj, target, source_parent):
        target.warehouse = source_parent.wip_warehouse

    def set_missing_values(source, target):
        target.material_request_type = "Material Transfer"

    def add_items(doclist, items, job_card_data):
        for jc_item in items:
            # Check if item_code already exists in doclist.items
            matching_item = next((i for i in doclist.items if i.item_code == jc_item.item_code), None)
            if matching_item:
                matching_item.qty += jc_item.required_qty
                matching_item.stock_qty += jc_item.required_qty
            else:
                # Append new item
                item_new = doclist.append("items", {})
                item_new.item_code = jc_item.item_code
                item_new.qty = jc_item.required_qty
                item_new.stock_qty = jc_item.required_qty
                item_new.uom = jc_item.stock_uom
                item_new.stock_uom = jc_item.stock_uom
                item_new.conversion_factor = 1
                item_new.schedule_date = now_datetime()

    # Map Job Card to Material Request
    doclist = get_mapped_doc(
        "Job Card",
        source_name,
        {
            "Job Card": {
                "doctype": "Material Request",
                "field_map": {"name": "job_card"},
            },
        },
        target_doc,
        set_missing_values,
    )

    # Fetch Job Card data
    job_card_data = frappe.get_doc("Job Card", source_name)

    # Process items based on use_funnel
    if job_card_data.use_funnel == 'USE_SHARE':
        add_items(doclist, job_card_data.items, job_card_data)
    else:
        # Add items from job_card_data.items
        add_items(doclist, job_card_data.items, job_card_data)
        # Add items from funnel_b_data if present
        if job_card_data.funnel_b_data:
            add_items(doclist, job_card_data.funnel_b_data, job_card_data)
        # Add items from funnel_c_data if present
        if job_card_data.funnel_c_data:
            add_items(doclist, job_card_data.funnel_c_data, job_card_data)

    return doclist        


@frappe.whitelist()
def check_mix_qty_jobcard(job_card):
    job_card_data = frappe.get_doc("Job Card", job_card)

    items = frappe.get_list(
        "Operation Job Card",
        fields=["name", "job_card_name", "job_card_operation_name", "doc_status"],
        filters=[
            ["job_card_name", "=", job_card],
            ["job_card_operation_name", "=", "TRON"],
            ["docstatus", "=", 1],
        ],
    )

    if job_card_data.mix_batch_qty <= len(items):
        frappe.response.message = False
    else:
        frappe.response.message = True       