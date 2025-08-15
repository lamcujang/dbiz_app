import frappe
from frappe.utils import today, getdate
from erpnext.stock.doctype.pick_list.pick_list import PickList

class cus_pick_list(PickList):
    
    def before_save(self):
        if not self.pick_manually:
            self.pick_manually = 1
        super(cus_pick_list, self).before_save()

