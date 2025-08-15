import frappe
from frappe import _
from frappe.utils import comma_and, get_link_to_form, today, getdate
from erpnext.manufacturing.doctype.production_plan.production_plan import ProductionPlan

class cusproductionplan(ProductionPlan):
    def onload(self):
        pass

    def autoname(self):
        today_date = today()
        current_year = getdate(today_date).year
        max_result = frappe.db.sql(f"""
                SELECT MAX(CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(name, '-', 2), '-', -1) AS UNSIGNED)) as max_number 
                FROM `tabProduction Plan`
                WHERE YEAR(creation) = {current_year}
            """, as_dict=True)
        last_number = max_result[0]["max_number"] + 1 if max_result and max_result[0]["max_number"] else 1
        formatted_number = f"{last_number:04d}"
        
        if self.sales_orders:
            so = frappe.get_doc("Sales Order", self.sales_orders[0].sales_order)
            customer = frappe.get_doc("Customer", so.customer)
            self.name = f"{current_year}-{formatted_number}-{customer.customer_code if customer.customer_code else 'CUS'}"
        else:
            self.name = f"{current_year}-{formatted_number}-{'LP'}"
    
    def before_save(self):
        if self.sales_orders:
            for so in self.sales_orders:
                pp_names = frappe.get_list("Production Plan", filters=[['Production Plan Sales Order', 'sales_order', '=', so.sales_order],
                                                                       ['docstatus','!=',2]], pluck="name")
                so_doc = frappe.get_doc("Sales Order", so.sales_order)
                if self.name not in pp_names:
                    pp_names.append(self.name)
                so_doc.db_set("production_plans", ", ".join(pp_names))
    
    def before_cancel(self):
        if self.sales_orders:
            for so in self.sales_orders:
                pp_names = frappe.get_list("Production Plan", filters=[['Production Plan Sales Order', 'sales_order', '=', so.sales_order],
                                                                       ['docstatus','!=',2],['name','!=',self.name]], pluck="name")
                so_doc = frappe.get_doc("Sales Order", so.sales_order)
                so_doc.db_set("production_plans", ", ".join(pp_names))
    
def pp_before_delete(doc, method=None):
    if doc.sales_orders:
        for so in doc.sales_orders:
            pp_names = frappe.get_list("Production Plan", filters=[['Production Plan Sales Order', 'sales_order', '=', so.sales_order], ['name','!=',doc.name]], pluck="name")
            so_doc = frappe.get_doc("Sales Order", so.sales_order)
            so_doc.db_set("production_plans", ", ".join(pp_names))

@frappe.whitelist()
def make_custom_work_order(docName):

    doc = frappe.get_doc('Production Plan', docName)

    wo_list= []
    po_list = []
    subcontracted_po = {}

    def create_work_order(item):

        # if float(item.get("qty")) <= 0:
        #     return

        wo = frappe.new_doc("Work Order")
        wo.percent_scrap_mixed = 1
        wo.percent_scrap_blow = 1.5
        wo.percent_scrap_cut = 1.5
        wo.total_percent_scrap = 4
        wo.update(item)
        wo.planned_start_date = item.get("planned_start_date") or item.get("schedule_date")

        if item.get("warehouse"):
            wo.fg_warehouse = item.get("warehouse")

        # wo.set_work_order_operations()
        # wo.set_required_items()   

        try:
            wo.flags.ignore_mandatory = True
            wo.flags.ignore_validate = True
            wo.flags.ispp = True
            wo.insert()
            return wo.name
        except Exception as e:
            pass


    def get_production_items():
        item_dict = {}

        d_has_bom = [d for d in doc.po_items]
        for d in d_has_bom:
            item_details = {
                "production_item": d.item_code,
                # "use_multi_level_bom": d.include_exploded_items,
                "sales_order": d.sales_order,
                "sales_order_item": d.sales_order_item,
                "material_request": d.material_request,
                "material_request_item": d.material_request_item,
                # "bom_no": d.bom_no,
                "description": d.description,
                "stock_uom": d.stock_uom,
                "company": doc.company,
                "fg_warehouse": d.warehouse,
                "production_plan": doc.name,
                "production_plan_item": d.name,
                "product_bundle_item": d.product_bundle_item,
                "planned_start_date": d.planned_start_date,
                "project": doc.project,
            }

            key = (d.item_code, d.sales_order, d.sales_order_item, d.warehouse)
            if doc.combine_items:
                key = (d.item_code, d.sales_order, d.warehouse)

            if not d.sales_order:
                key = (d.name, d.item_code, d.warehouse)

            if not item_details["project"] and d.sales_order:
                item_details["project"] = frappe.get_cached_value("Sales Order", d.sales_order, "project")

            if doc.get_items_from == "Material Request":
                item_details.update({"qty": d.planned_qty})
                item_dict[(d.item_code, d.material_request_item, d.warehouse)] = item_details
            else:
                item_details.update(
                    {"qty": float(item_dict.get(key, {}).get("qty") or 0) + (float(d.planned_qty or 0) - float(d.ordered_qty or 0))}
                )

                item_dict[key] = item_details

        return item_dict

        
        
    def set_default_warehouses(row, default_warehouses):
        for field in ["wip_warehouse", "fg_warehouse"]:
            if not row.get(field):
                row[field] = default_warehouses.get(field)

    def show_list_created_message(doctype, doc_list=None):
        if not doc_list:
            return

        frappe.flags.mute_messages = False
        if doc_list:
            doc_list = [get_link_to_form(doctype, p) for p in doc_list]
            frappe.msgprint(_("{0} created").format(comma_and(doc_list)))


    def make_work_order_for_finished_goods(wo_list, default_warehouses):
        items_data = get_production_items()

        # Loop through the items in items_data but only process the first one
        for i, (key, item) in enumerate(items_data.items()):
            set_default_warehouses(item, default_warehouses)
            work_order = create_work_order(item)
            if work_order:
                wo_list.append(work_order)


    defaultWarehouseDoc = frappe.get_cached_doc("Manufacturing Settings")
    default_warehouses = {
        "wip_warehouse": defaultWarehouseDoc.default_wip_warehouse,
        "fg_warehouse": defaultWarehouseDoc.default_fg_warehouse,
        "scrap_warehouse": defaultWarehouseDoc.default_scrap_warehouse,
    }
        
    make_work_order_for_finished_goods(wo_list, default_warehouses)

    if not wo_list:
        frappe.msgprint(_("No Work Orders were created"))
    else:
        for wo in wo_list:
            frappe.msgprint(_("Work Order {0} created").format(get_link_to_form("Work Order", wo)), alert=True)
        frappe.response.message = wo_list

@frappe.whitelist()
def make_wo_product_mixed(docName):
    doc = frappe.get_doc('Production Plan', docName)
    so = frappe.get_doc('Sales Order', doc.sales_orders[0].sales_order)
    for fg_item in doc.fg_items:
        product_mixed = fg_item.item
        product_mixed_doc = frappe.get_doc('Product Bundle', product_mixed)
        if not product_mixed_doc:
            break
        so_item = next((x for x in so.items if x.item_code == product_mixed), None)
        wo = frappe.new_doc("Work Order")
        wo.product_mixed = 1
        defaultWarehouseDoc = frappe.get_cached_doc("Manufacturing Settings")
        default_warehouses = {
            "wip_warehouse": defaultWarehouseDoc.default_wip_warehouse,
            "fg_warehouse": defaultWarehouseDoc.default_fg_warehouse,
            "scrap_warehouse": defaultWarehouseDoc.default_scrap_warehouse,
        }
        wo.wip_warehouse = default_warehouses["wip_warehouse"]
        wo.fg_warehouse = default_warehouses["fg_warehouse"]
        wo.scrap_warehouse = default_warehouses["scrap_warehouse"]
        wo.planned_start_date = today()
        wo.production_plan = docName
        wo.production_item = doc.fg_items[0].item
        wo.sales_order = so.name
        wo.sales_order_item = so_item.name
        wo.qty_mixed = so_item.qty
        wo.qty = so_item.qty

        try:
            wo.flags.ignore_mandatory = True
            wo.flags.ignore_validate = True
            wo.flags.ispp = True
            wo.insert()
            frappe.msgprint(_("Work Order {0} created").format(get_link_to_form("Work Order", wo.name)), alert=True)
            frappe.response.message = wo.name
        except Exception as e:
            pass
    

