# Copyright (c) 2025, lamnl and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class LoanContract(Document):
	
	def before_submit(self):
		self.limit = self.og_limit
  
	def before_insert(self):
		if not self.limit or self.limit == 0:
			self.limit = self.og_limit
