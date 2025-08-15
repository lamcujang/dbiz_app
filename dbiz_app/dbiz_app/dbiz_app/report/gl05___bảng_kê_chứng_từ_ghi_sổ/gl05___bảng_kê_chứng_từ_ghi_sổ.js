// Copyright (c) 2024, lamnl and contributors
// For license information, please see license.txt

frappe.query_reports["GL05 - Bảng kê chứng từ ghi sổ"] = {
	"filters": [
		{
			"fieldname": "start_date",
			"fieldtype": "Date",
			"label": __("From Date"),
			default: frappe.datetime.add_months(frappe.datetime.now_date(), -1),
			"reqd": 1,
			"wildcard_filter": 0
		},
		{
			"fieldname": "end_date",
			"fieldtype": "Date",
			"label": __("To Date"),
			default: frappe.datetime.now_date(),
			"reqd": 1,
			"wildcard_filter": 0
		},
		{
			"fieldname": "company",
			"fieldtype": "Link",
			"label": __("Company"),
			"reqd": 1,
			"options": "Company",
			"wildcard_filter": 0,
			"default": frappe.defaults.get_user_default("Company"),
			"get_query": function () {
				return {
					filters: [
						["Company", "is_group", "=", "0"]
					]
				}
			},
			on_change: function (query_report) {
				const company = frappe.query_report.get_filter_value("company");

				frappe.db.get_value("Company", company, ["company_name", "tax_id"], (r) => {
					frappe.query_report.set_filter_value("company_name", r.company_name);
					frappe.query_report.set_filter_value("tax_id", r.tax_id);
				});

				// Get Address Linked to the Company
				frappe.call({
					method: "dbiz_app.api.get_company_address",
					args: {
						company: company
					},
					callback: function (r) {
						if (r.message) {
							frappe.query_report.set_filter_value("company_address", r.message);
						}
					}
				});
			},
		},
		{
			"fieldname": "account",
			"fieldtype": "Link",
			"label": __("Account"),
			// "reqd": 1,
			"options": "Account",
			// "wildcard_filter": 0,
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
			"fieldtype": "Data",
			"hidden": 1,
		},
		{
			fieldname: "company_address",
			fieldtype: "Data",
			hidden: 1, // Hidden as it is used only for display in the HTML when printing
		},
		{
			"fieldname": "tax_id",
			"fieldtype": "Data",
			"hidden": 1,
		},
		{
			"fieldname": "account_name",
			"fieldtype": "Data",
			"hidden": 1,
		},
		{
			"fieldname": "account_number",
			"fieldtype": "Data",
			"hidden": 1,
		}
	],
	// Trigger on_change manually after the report loads
	onload: function (query_report) {
		const company = frappe.query_report.get_filter_value("company");

		if (company) {
			query_report.get_filter("company").on_change(query_report);
		}

		window.format_number_js = (
			value,
			decimals = 0,
			number_format = frappe.boot.sysdefaults.number_format || "#.###,##"
		) => {
			const decimal_places =
				decimals === "default"
					? frappe.boot.sysdefaults.float_precision
					: decimals;
			return !isNaN(value)
				? format_number(parseFloat(value), number_format, decimal_places)
				: "";
		};
	}
};
