// Copyright (c) 2024, lamnl and contributors
// For license information, please see license.txt

frappe.query_reports["Báo cáo tình hình sản xuất trong tháng"] = {
	"filters": [
		{
			"fieldname": "month",
			"label": __("Month"),
			"fieldtype": "Select",
			"reqd": 1,
			"default": new Date().getMonth() + 1,
			"options": [
				{ "label": __("January"), "value": 1 },
				{ "label": __("February"), "value": 2 },
				{ "label": __("March"), "value": 3 },
				{ "label": __("April"), "value": 4 },
				{ "label": __("May"), "value": 5 },
				{ "label": __("June"), "value": 6 },
				{ "label": __("July"), "value": 7 },
				{ "label": __("August"), "value": 8 },
				{ "label": __("September"), "value": 9 },
				{ "label": __("October"), "value": 10 },
				{ "label": __("November"), "value": 11 },
				{ "label": __("December"), "value": 12 },
			],
		},
		{
			"fieldname": "year",
			"label": __("Year"),
			"fieldtype": "Select",
			"reqd": 1,
			"default": new Date().getFullYear(),
			"options": getYearOptions(),
		},
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1,
			on_change: function (query_report) {
				const company = frappe.query_report.get_filter_value("company");

				frappe.db.get_value("Company", company, ["company_name", "tax_id"], (r) => {
					frappe.query_report.set_filter_value("company_name", r.company_name);
					frappe.query_report.set_filter_value("tax_id", r.tax_id);
				});
			},
		},
		{
			"fieldname": "company_name",
			"fieldtype": "Data",
			"hidden": 1, // Hidden as it is used only for display in the HTML when printing
		},
		{
			"fieldname": "tax_id",
			"fieldtype": "Data",
			"hidden": 1, // Hidden as it is used only for display in the HTML when printing
		},
	],
	// Trigger on_change manually after the report loads
	onload: function (query_report) {
		const company = frappe.query_report.get_filter_value("company");
		if (company) {
			query_report.get_filter("company").on_change(query_report);
		}
	}
};


function getYearOptions() {
	const currentYear = new Date().getFullYear();
	return Array.from({ length: 11 }, (_, i) => currentYear - i).join("\n");
}
