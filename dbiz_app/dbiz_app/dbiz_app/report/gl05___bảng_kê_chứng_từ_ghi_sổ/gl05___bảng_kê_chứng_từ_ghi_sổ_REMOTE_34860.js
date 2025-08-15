// Copyright (c) 2024, lamnl and contributors
// For license information, please see license.txt

frappe.query_reports["GL05 - Bảng kê chứng từ ghi sổ"] = {
	"filters": [
		{
			"fieldname": "start_date",
			"fieldtype": "Date",
			"label": "Ng\u00e0y b\u1eaft \u0111\u1ea7u",
			"mandatory": 1,
			"wildcard_filter": 0
		},
		{
			"fieldname": "end_date",
			"fieldtype": "Date",
			"label": "Ng\u00e0y k\u1ebft th\u00fac",
			"mandatory": 1,
			"wildcard_filter": 0
		},
		{
			"fieldname": "company",
			"fieldtype": "Link",
			"label": "C\u00f4ng ty",
			"mandatory": 1,
			"options": "Company",
			"wildcard_filter": 0,
			"default": "Leepak",
			"get_query": function () {
				return {
					filters: [
						["Company", "is_group", "=", "0"]
					]
				}
			},
			on_change: function (query_report) {
				const company = frappe.query_report.get_filter_value("company");

				if (company) {
					frappe.db.get_value("Company", company, ["company_name", "tax_id"], (r) => {
						frappe.query_report.set_filter_value("company_name", r.company_name);
						frappe.query_report.set_filter_value("tax_id", r.tax_id);
					});
				} else {
					frappe.query_report.set_filter_value("company_name", "");
					frappe.query_report.set_filter_value("tax_id", "");
				}
			},
		},
		{
			"fieldname": "account",
			"fieldtype": "Link",
			"label": "T\u00e0i kho\u1ea3n ",
			"mandatory": 1,
			"options": "Account",
			"wildcard_filter": 0,
			"get_query": function () {
				let company = frappe.query_report.get_filter_value("company") || "";
				return {
					filters: {
						'root_type': ['in', 'Expense'],
						'is_group': ['=', '0'],
						'company': ['=', company]
					}
				}
			},
			on_change: function (query_report) {
				const account = frappe.query_report.get_filter_value("account");

				if (account) {
					frappe.db.get_value("Account", account, ["account_name", "account_number"], (r) => {
						console.log(r.account_name)
						console.log(r.account_number)
						frappe.query_report.set_filter_value("account_name", r.account_name);
						frappe.query_report.set_filter_value("account_number", r.account_number);
					});
				} else {
					frappe.query_report.set_filter_value("account_name", "");
					frappe.query_report.set_filter_value("account_number", "");
				}
			},
		},
		{
			"fieldname": "company_name",
			"label": "Tên công ty",
			"default": "Leepak",
			"fieldtype": "Data",
			"hidden": 1, 
		},
		{
			"fieldname": "tax_id",
			"label": "Mã số thuế",
			"default": "1232431",
			"fieldtype": "Data",
			"hidden": 1, 
		},
		{
			"fieldname": "account_name",
			"label": "Mã số thuế",
			"fieldtype": "Data",
			"hidden": 1,
		},
		{
			"fieldname": "account_number",
			"label": "Mã số thuế",
			"fieldtype": "Data",
			"hidden": 1,
		}
	]
};
