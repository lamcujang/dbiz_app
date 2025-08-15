# Copyright (c) 2024, lamnl and contributors
# For license information, please see license.txt

import json
from frappe.model.document import Document


class AssignmentToDo(Document):
	
	def on_submit(self):
		self.assign_to_do()

	def assign_to_do(self):
		from frappe.desk.form.assign_to import add
		args = {
			"assign_to": json.dumps([self.assign_to]),
			"doctype": self.reference_doctype,
			"name": self.reference_name,
			"description": self.comment,
			"assignment_rule": None
		}
		return add(args)
