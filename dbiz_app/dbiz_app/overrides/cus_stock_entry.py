import frappe
from frappe.utils import today, getdate
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry

class cus_stock_entry(StockEntry):
    def onload(self):
        pass

    def on_submit(self):
        if self.stock_entry_type == "Material Consumption for Manufacture":
            for item in self.items:
                if item.batch_no:
                    workstation = frappe.get_all("Workstation", filters={"batch_no": item.batch_no}, fields=["name"])
                    if workstation:
                        for work in workstation:
                            workstation_data = frappe.get_doc("Workstation", work.name)
                            workstation_data.db_set("status", "Off")
                            workstation_data.db_set("batch_no", None)
        super().on_submit()
                    


