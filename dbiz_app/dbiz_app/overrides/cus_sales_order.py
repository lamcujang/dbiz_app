import frappe
from frappe.utils import today, getdate
from erpnext.selling.doctype.sales_order.sales_order import SalesOrder

class cus_sales_order(SalesOrder):
    def onload(self):
        pass
    
    def before_save(self):
        if self.items:
            for item in self.items:
                item_data = frappe.get_doc("Item", item.item_code)
                second_qty = item.qty * float(item_data.net_kgs_per_carton)
                if item.second_qty != second_qty:
                    item.second_qty = second_qty
        super(cus_sales_order, self).before_save()

    def autoname(self):
        today_date = today()
        year = getdate(today_date).strftime("%y")
        customer_code = "XXX" 
        if self.customer:
            customer_code = frappe.db.get_value("Customer", self.customer, "customer_code") or "XXX"
        current_year = getdate(today_date).year

        count_customer = frappe.db.sql(f"""
            SELECT COUNT(*) as total FROM `tabSales Order`
            WHERE YEAR(creation) = {current_year}
            and customer = '{self.customer}'
        """, as_dict=True)
        
        count_company = frappe.db.sql(f"""
            SELECT COUNT(*) as total FROM `tabSales Order`
            WHERE YEAR(creation) = {current_year}
            and company = '{self.company}'
        """, as_dict=True)
        
        customer_number = count_customer[0]["total"] + 1 if count_customer else 1
        company_number = count_company[0]["total"] + 1 if count_company else 1

        customer_number = f"{customer_number:0{max(2, len(str(customer_number))) }d}"
        company_number = f"{company_number:0{max(2, len(str(company_number))) }d}"

        self.name = f"{year}.{customer_number}.{customer_code}.{company_number}"

@frappe.whitelist()
def get_product_bundle_item(item_code):
    product_bundle_doc = frappe.db.get_value("Product Bundle", {"name": item_code}, "name")
    if product_bundle_doc:
        return product_bundle_doc
    else:
        return None

