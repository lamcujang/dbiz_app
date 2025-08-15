import frappe
from frappe import _
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry

class cus_payment_entry(PaymentEntry):
    
    def on_submit(self):
        if self.company_loan and (self.payment_type == 'Receive' or self.payment_type == 'Pay') and not self.scd_id and not self.is_settle_loan:
            loan = frappe.get_doc('Company Loan', self.company_loan)
            frappe.db.set_value('Company Loan', self.company_loan, 'not_paid_amt', loan.not_paid_amt - self.paid_amount)
            frappe.db.set_value('Company Loan', self.company_loan, 'paid_amt', loan.paid_amt + self.paid_amount)
            if loan.contract:
                contract = frappe.get_doc('Loan Contract', loan.contract)
                frappe.db.set_value('Loan Contract', loan.contract, 'limit', contract.limit - self.paid_amount)

        if self.company_loan and (self.payment_type == 'Pay' or self.payment_type == 'Receive') and self.scd_id:
            loan = frappe.get_doc('Company Loan', self.company_loan)
            loan_child_doc = frappe.get_doc('Company Loan Repayment Schedule', self.scd_id)
            
            
            frappe.db.set_value('Company Loan', self.company_loan, 'current_balance', loan.current_balance - loan_child_doc.prin_amt)
            frappe.db.set_value('Company Loan', self.company_loan, 'prin_paid_amt', loan.prin_paid_amt + loan_child_doc.prin_amt)
            if loan.advance_check == 0:
                frappe.db.set_value('Company Loan', self.company_loan, 'int_paid_amt', loan.int_paid_amt + loan_child_doc.int_amt)
            
            frappe.db.set_value("Company Loan Repayment Schedule", loan_child_doc.name, "pe_name", self.name)
            frappe.db.set_value("Company Loan Repayment Schedule", loan_child_doc.name, "paid_amt", loan_child_doc.paid_amt + self.paid_amount)
            
            if loan.contract:
                contract = frappe.get_doc('Loan Contract', loan.contract)
                frappe.db.set_value('Loan Contract', loan.contract, 'limit', contract.limit - self.paid_amount)
            
        if self.company_loan and (self.payment_type == 'Pay' or self.payment_type == 'Receive') and self.is_settle_loan:
            loan_doc = frappe.get_doc('Company Loan', self.company_loan)
            frappe.db.set_value('Company Loan', loan_doc.name, 'settled_amt', self.received_amount)
            frappe.db.set_value('Company Loan', loan_doc.name, 'current_balance', 0)
            frappe.db.set_value('Company Loan', loan_doc.name, 'is_settled', 1)

        if self.taxes:
            for item in self.taxes:
                if item.debt_loan_item:
                    loan = frappe.get_doc("Company Loan Repayment Schedule", item.debt_loan_item)
                    loan.db_set("paid_amt", item.total)
                    
        super().on_submit()
    
    def on_cancel(self):
        if self.company_loan :
            loan = frappe.get_doc('Company Loan', self.company_loan)
            if loan.loan_type == 'Borrow' and self.payment_type =='Receive':
                frappe.db.set_value('Company Loan', self.company_loan, 'not_paid_amt', loan.not_paid_amt + self.paid_amount)
                frappe.db.set_value('Company Loan', self.company_loan, 'paid_amt', loan.paid_amt - self.paid_amount)
                if loan.contract:
                    contract = frappe.get_doc('Loan Contract', loan.contract)
                    frappe.db.set_value('Loan Contract', loan.contract, 'limit', contract.limit + self.paid_amount)
            if loan.loan_type == 'Lend' and self.payment_type =='Pay':
                frappe.db.set_value('Company Loan', self.company_loan, 'not_paid_amt', loan.not_paid_amt + self.paid_amount)
                frappe.db.set_value('Company Loan', self.company_loan, 'paid_amt', loan.paid_amt - self.paid_amount)
                if loan.contract:
                    contract = frappe.get_doc('Loan Contract', loan.contract)
                    frappe.db.set_value('Loan Contract', loan.contract, 'limit', contract.limit + self.paid_amount)
        super().on_cancel()
@frappe.whitelist()
def getCompanyLoanSchedule(type, pay_type, party_type, party):
    doctype = party_type
    id = party
    filters = {
        "type": type,
    }

    doctype_filter = ""
    currency_filter = ""
    if pay_type == 'Pay' and doctype:
        doctype_filter = " and cl.party_type = %(doctype)s and cl.party = %(id)s "
        filters["doctype"] = doctype
        filters["id"] = id
        currency = frappe.db.get_value(doctype, id, "default_currency")
        if currency:
            currency_filter = " and cl.currency = %(currency)s "
            filters["currency"] = currency
        
            

    item = frappe.db.sql(f"""
        select clr.name, 
            clr.pmt_amt,
            cl.name as parent,
            cl.submit_date,
            clr.date,
            clr.prin_amt,
            clr.int_amt
        from `tabCompany Loan Repayment Schedule` clr
        join `tabCompany Loan` cl 
            on clr.parent = cl.name 
            and clr.parenttype = 'Company Loan' 
            and cl.docstatus = 1
            and clr.pmt_amt > 0
            and cl.loan_type = %(type)s
            {doctype_filter}
            {currency_filter}
        where clr.paid_amt = 0 or clr.paid_amt is null 
        order by clr.date asc
    """, filters, as_dict=True)

    frappe.response["message"] = item if item else None