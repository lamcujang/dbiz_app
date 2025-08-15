import frappe
from frappe import _
from erpnext.stock.doctype.item.item import Item
from frappe.utils.nestedset import get_descendants_of
import re

class cus_item(Item):
    def onload(self):
        pass
    def before_save(self):
        self.item_code = self.name
        if self.item_group in ['BTP', 'BTPTRON', 'BTPCAT', 'BTPTHOI'] and (not self.valuation_rate or self.valuation_rate == 0):
            self.valuation_rate = 1000
        descendant_groups = get_descendants_of("Item Group", 'THANHPHAM')
    
        all_groups = ['THANHPHAM'] + descendant_groups
        if self.item_group in all_groups and self.bag_type:
            bag_type = frappe.db.get_value('Bag Type', self.bag_type, ['code', 'name1'], as_dict=True) or {}
            film_color = frappe.db.get_value('Film Color', self.film_color, ['code', 'name1'], as_dict=True) or {}
            if bag_type.get("code") == 'DL':
                roll_stamp_code = ("DL" + 
                                 ('' + str(film_color.get("code", ""))) +  
                                 ('' + str(self.item_height) + 'M' if self.item_height else '') + 
                                 ('' + str(self.item_width) if self.item_width else '') + 
                                 ('' + str(self.item_material) if self.item_material else '') +
                                 ('/' + str(self.used_for_item) if self.used_for_item else ''))
                
                self.roll_stamp_code = roll_stamp_code
    def on_update(self):
        super(cus_item, self).on_update()
        descendant_groups = get_descendants_of("Item Group", 'THANHPHAM')
    
        all_groups = ['THANHPHAM'] + descendant_groups
        if self.item_group in all_groups:
            bag_type = frappe.db.get_value('Bag Type', self.bag_type, ['code', 'name1'], as_dict=True) or {}
            film_color = frappe.db.get_value('Film Color', self.film_color, ['code', 'name1'], as_dict=True) or {}
            customer = frappe.db.get_value('Customer', self.customer_new, ['name','customer_code'], as_dict=True) or {}

            if not bag_type or not film_color or not customer:
                frappe.throw(_("Missing required fields for generating item code"))

            # Create the initial part of the item code
            name_new = str(self.code_item_by_customter) + str(bag_type.get("code", "")) + str(customer.get("customer_code", ""))

            # 55DPMAU54_TT2 lấy 2 số phía trước dấu _
            number = str(self.item_code).split('_')[0]
            first_part = str(self.item_code).split('_')[0]
            match = re.findall(r"(\d+)", first_part)
            if match:
                number = match[-1]
            if not number:
                numb = frappe.db.sql("""
                    SELECT
                        MAX(CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(ti.item_code, %s, -1), '_', 1) AS UNSIGNED)) AS current_number
                    FROM `tabItem` ti
                    WHERE ti.item_code LIKE %s AND ti.item_code REGEXP '_';
                """, (str(customer.get("customer_code", "")), '%'+ str(customer.get("customer_code", "")) + '%'), as_dict=True)
                
                # Handle the next number logic
                next_number = (numb[0].current_number + 1) if numb and numb[0].current_number else 1
                next_number_formatted = str(next_number).zfill(2) if next_number < 10 else str(next_number)
                number = next_number_formatted

            small_box = ''
            if self.small_box in ["Yes", "Có"]:
                small_box = "2"
            elif self.small_box in ["No", "Không"]:
                small_box = "1"

            # Create the final item_code
            id_new = name_new + number + '_' + str(film_color.get("code", "")) + str(small_box)
            item_name_new = ''
            if bag_type.get("code") == 'DL':
                item_name_new = ("Dây" + 
                                 (' ' + str(self.item_material) if self.item_material else '') + 
                                 (' ' + str(film_color.get("name1", ""))) +  
                                 (' ' + str(self.item_height) + 'mic x' if self.item_height else '') +
                                 (' ' + str(self.item_width) + 'mm' if self.item_width else ''))
            else:
                item_name_new = (str(bag_type.get("name1", "")) + 
                             (', ' + str(film_color.get("name1", ""))) +  
                             (', ' + str(self.item_roughness) if self.item_roughness else '') + 
                             #  (', ' + str(self.print_color_qty) if self.print_color_qty else '') + 
                             (', mùi ' + str(self.item_smell) if self.item_smell else '') + 
                             (', ' + str(self.item_material) if self.item_material else '') +
                             (', rộng ' + str(self.item_width) + 'mm' if self.item_width else '') + 
                             (', dài ' + str(self.item_lenght) + 'mm' if self.item_lenght else ''))
            if id_new != self.item_code:
                frappe.db.set_value('Item', self.name, 'item_name', item_name_new)
                frappe.db.set_value('Item', self.name, 'item_code', id_new)
                frappe.rename_doc('Item', self.name, id_new, force=True)
        
    def autoname(self):
        descendant_groups = get_descendants_of("Item Group", 'THANHPHAM')
    
        all_groups = ['THANHPHAM'] + descendant_groups
        # if self.item_group == 'DAYQUAI':
        #     wire_color = frappe.db.get_value('Film Color', self.wire_color, ['code', 'name1'], as_dict=True) or {}
        #     wire_height = float(self.wire_height) if self.wire_height else 0
        #     wire_height = int(wire_height) if wire_height.is_integer() else round(wire_height, 2)
        #     wire_width = float(self.wire_width) if self.wire_width else 0
        #     wire_width = int(wire_width) if wire_width.is_integer() else round(wire_width, 2)
        #     item_code_new = 'D'+ str(wire_color.code) + str(wire_height) + 'M' + str(wire_width) + str(self.wire_material)
        #     self.item_code = item_code_new
        #     self.name = self.item_code
        #     # Name
        #     item_name_new = ('Dây luồn ') + str(wire_color.get("name1", "")).lower() +' ' + str(wire_height) + 'mic ' + str(wire_width) + 'cm ' + str(self.wire_material)
        #     check_name = frappe.db.get_value('Item', {'item_name': item_name_new}, 'name')
        #     if check_name:
        #         item_name_new = item_name_new + ' ' + str(self.item_code)
        #     self.item_name = item_name_new
            
        #     self.has_batch_no = 1
        #     if not self.valuation_rate or self.valuation_rate == 0:
        #         self.valuation_rate = 1000
        if self.item_group in all_groups:
            bag_type = frappe.db.get_value('Bag Type', self.bag_type, ['code', 'name1'], as_dict=True) or {}
            film_color = frappe.db.get_value('Film Color', self.film_color, ['code', 'name1'], as_dict=True) or {}
            customer = frappe.db.get_value('Customer', self.customer_new, ['name','customer_code'], as_dict=True) or {}

            if not bag_type or not film_color or not customer:
                frappe.throw(_("Missing required fields for generating item code"))

            # Create the initial part of the item code
            name_new = str(self.code_item_by_customter) + str(bag_type.get("code", "")) + str(customer.get("customer_code", ""))

            numb = frappe.db.sql("""
                SELECT
                    MAX(CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(ti.item_code, %s, -1), '_', 1) AS UNSIGNED)) AS current_number
                FROM `tabItem` ti
                WHERE ti.item_code LIKE %s AND ti.item_code REGEXP '_';
            """, (str(customer.get("customer_code", "")), '%'+ str(customer.get("customer_code", "")) + '%'), as_dict=True)
            
            # Handle the next number logic
            next_number = (numb[0].current_number + 1) if numb and numb[0].current_number else 1
            next_number_formatted = str(next_number).zfill(2) if next_number < 10 else str(next_number)
            
            small_box = ''
            if self.small_box in ["Yes", "Có"]:
                small_box = "2"
            elif self.small_box in ["No", "Không"]:
                small_box = "1"

            # Create the final item_code
            self.item_code = name_new + next_number_formatted + '_' + str(film_color.get("code", "")) + str(small_box)
            self.name = self.item_code
            item_name_new = ''
            if bag_type.get("code") == 'DL':
                item_name_new = ("Dây" + 
                                 (' ' + str(self.item_material) if self.item_material else '') + 
                                 (' ' + str(film_color.get("name1", ""))) +  
                                 (' ' + str(self.item_height) + 'mic x' if self.item_height else '') +
                                 (' ' + str(self.item_width) + 'mm' if self.item_width else ''))
            else:
                item_name_new = (str(bag_type.get("name1", "")) + 
                             (', ' + str(film_color.get("name1", ""))) +  
                             (', ' + str(self.item_roughness) if self.item_roughness else '') + 
                             #  (', ' + str(self.print_color_qty) if self.print_color_qty else '') + 
                             (', mùi ' + str(self.item_smell) if self.item_smell else '') + 
                             (', ' + str(self.item_material) if self.item_material else '') +
                             (', rộng ' + str(self.item_width) + 'mm' if self.item_width else '') + 
                             (', dài ' + str(self.item_lenght) + 'mm' if self.item_lenght else ''))
            check_name = frappe.db.get_value('Item', {'item_name': item_name_new}, 'name')
            if check_name:
                item_name_new = item_name_new + ((', ' + str(self.bags_per_stack)+' túi/thếp (cuộn) ') if self.bags_per_stack else '')
                check_name = frappe.db.get_value('Item', {'item_name': item_name_new}, 'name')
                if check_name:
                    item_name_new = item_name_new + ' ' + str(self.item_code)
            self.item_name = item_name_new
            
            self.has_batch_no = 1
            if not self.valuation_rate or self.valuation_rate == 0:
                self.valuation_rate = 1000
        else:
            self.name = self.item_code
            
    def update_defaults_from_item_group(self):
        """Get defaults from Item Group"""
        if self.item_defaults or not self.item_group:
            return

        item_defaults = frappe.db.get_values(
			"Item Default",
			{"parent": self.item_group},
			[
				"company",
				"default_warehouse",
				"default_price_list",
				"buying_cost_center",
				"default_supplier",
				"expense_account",
				"account_item",
				"selling_cost_center",
				"income_account",
			],
			as_dict=1,
		)
        if item_defaults:
            for item in item_defaults:
                self.append(
					"item_defaults",
					{
						"company": item.company,
						"default_warehouse": item.default_warehouse,
						"default_price_list": item.default_price_list,
						"buying_cost_center": item.buying_cost_center,
						"default_supplier": item.default_supplier,
						"expense_account": item.expense_account,
						"account_item": item.account_item,
						"selling_cost_center": item.selling_cost_center,
						"income_account": item.income_account,
					},
				)
        else:
            defaults = frappe.defaults.get_defaults() or {}

            # To check default warehouse is belong to the default company
            if (
                defaults.get("default_warehouse")
                and defaults.company
                and frappe.db.exists(
                    "Warehouse", {"name": defaults.default_warehouse, "company": defaults.company}
                )
            ):
                self.append(
                    "item_defaults",
                    {"company": defaults.get("company"), "default_warehouse": defaults.default_warehouse},
                )
