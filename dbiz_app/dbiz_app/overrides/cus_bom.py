import frappe
from frappe.utils import today, getdate
from erpnext.manufacturing.doctype.bom.bom import BOM

class cus_bom(BOM):
    def onload(self):
        pass

    def autoname(self):
        today_date = today()
        current_year = getdate(today_date).year
        item_finish = self.item_finish[0].item_code if self.item_finish else "XXX"
        item = self.item
        name = str(current_year)+"-"+item+"-"+item_finish
        existing_docs = frappe.get_all(
            'BOM',
            filters={'name': ['like', f"{name}%"]},
            fields=['name']
        )
        if existing_docs:
            name = f"{name}-{len(existing_docs) if len(existing_docs) == 1 else len(existing_docs)+1}"
        
        self.name = name
