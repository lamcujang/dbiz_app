import json

import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt

from erpnext.controllers.buying_controller import BuyingController

form_grid_templates = {"items": "templates/form_grid/item_grid.html"}

@frappe.whitelist()
def make_purchase_order(source_name, target_doc=None, args=None):
        if args is None:
            args = {}

        if isinstance(args, str):
            args = json.loads(args)

        def set_missing_values(source, target):
            target.run_method("set_missing_values")
            target.run_method("get_schedule_dates")
            target.run_method("calculate_taxes_and_totals")
            
        def select_item(d):
            source_doc = frappe.get_doc("Supplier Quotation", d.parent)

            if source_doc.status in ["Stopped", "Expired"]:
                frappe.msgprint(_("This Supplier Quotation is {0}. Item cannot be selected.".format(source_doc.status)), raise_exception=True)
                return False

            
            filtered_items = args.get("filtered_children", [])
            child_filter = d.name in filtered_items if filtered_items else True

            # if not child_filter:
            # 	# In thông báo khi item không được chọn
            #     frappe.msgprint(_("Item {0} is not eligible for selection due to status.").format(d.name))

            return child_filter


        def update_item(obj, target, source_parent):
            target.stock_qty = flt(obj.qty) * flt(obj.conversion_factor)

        doclist = get_mapped_doc(
            "Supplier Quotation",
            source_name,
            {
                "Supplier Quotation": {
                    "doctype": "Purchase Order",
                    "validation": {
                        "docstatus": ["=", 1],
                    },
                },
                "Supplier Quotation Item": {
                    "doctype": "Purchase Order Item",
                    "field_map": [
                        ["name", "supplier_quotation_item"],
                        ["parent", "supplier_quotation"],
                        ["material_request", "material_request"],
                        ["material_request_item", "material_request_item"],
                        ["sales_order", "sales_order"],
                        ["total_qty", "total_qty"],
                    ],
                    "postprocess": update_item,
                    "condition": select_item,
                },
                "Purchase Taxes and Charges": {
                    "doctype": "Purchase Taxes and Charges",
                },
            },
            target_doc,
            set_missing_values,
        )

        return doclist