# Copyright (c) 2024, lamnl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, nowdate
from frappe import _
from erpnext.accounts.general_ledger import make_gl_entries

class CompanyLoan(Document):
	def before_submit(self):
		if not self.rp_scd:
			frappe.throw(_("Vui lòng tạo lịch thanh toán trước khi Gửi!"))
		if self.contract:
			contract = frappe.get_doc('Loan Contract', self.contract)
			if contract.docstatus != 1:
				frappe.throw(_("Hợp đồng chưa được duyệt!"))
   
	def validate(self):

		if self.advance_check and self.currency != 'VND' :
			frappe.throw('Không hỗ trợ trả trước với vay ngoại tệ!')
		if self.advance_check and self.loan_type == 'Lend' :
			frappe.throw('Không hỗ trợ trả trước với khoản cho vay!')
		if self.contract:
			if self.expire_date:
				if getdate(nowdate()) > getdate(self.expire_date):
					frappe.throw('Hợp đồng đã hết hạn!')
			if self.is_limit and self.total_loan > self.limit:
				frappe.throw('Tiền vay đã vượt quá hạn mức!')
