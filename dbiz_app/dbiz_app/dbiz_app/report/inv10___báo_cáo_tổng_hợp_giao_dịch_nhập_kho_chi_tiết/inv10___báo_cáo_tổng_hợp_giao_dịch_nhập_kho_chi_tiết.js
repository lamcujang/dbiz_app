// Copyright (c) 2024, lamnl and contributors
// For license information, please see license.txt

frappe.query_reports["INV10 - Báo cáo tổng hợp giao dịch nhập kho chi tiết"] = {
	"filters": [
		{
			"fieldname": "start_date",
			"label": "Ngày bắt đầu",
			"fieldtype": "Date",
			default: frappe.datetime.add_months(frappe.datetime.now_date(), -1),
			"reqd": 1,
		},
		{
			"fieldname": "end_date",
			"label": "Ngày kết thúc",
			"fieldtype": "Date",
			"default": frappe.datetime.now_date(),
			"reqd": 1,
		},
		{
			"fieldname": "company",
			"label": "Công ty",
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
			"fieldname": "company_name",
			"label": "Tên công ty",
			"fieldtype": "Data",
			"hidden": 1, // Hidden as it is used only for display in the HTML when printing
		},
		{
			fieldname: "company_address",
			fieldtype: "Data",
			hidden: 1, // Hidden as it is used only for display in the HTML when printing
		},
		{
			"fieldname": "tax_id",
			"label": "Mã số thuế",
			"fieldtype": "Data",
			"hidden": 1, // Hidden as it is used only for display in the HTML when printing
		},
		{
			"fieldname": "warehouse",
			"label": "Kho",
			"fieldtype": "Link",
			"options": "Warehouse",
			"reqd": 0,
			on_change: function (query_report) {
				const warehouse = frappe.query_report.get_filter_value("warehouse");

				if (warehouse) {
					frappe.db.get_value("Warehouse", warehouse, "warehouse_name", (r) => {
						frappe.query_report.set_filter_value("warehouse_name", r.warehouse_name || "Unknown");
					});
				} else {
					frappe.query_report.set_filter_value("warehouse_name", "");
				}
			},
		},
		{
			"fieldname": "warehouse_name",
			"label": "Tên kho",
			"fieldtype": "Data",
			"hidden": 1, // Hidden as it is used only for display in the HTML when printing
		},
		{
			"fieldname": "item_group",
			"label": "Nhóm sản phẩm",
			"fieldtype": "Link",
			"options": "Item Group",
		},
		{
			"fieldname": "supplier",
			"label": "Đối tác",
			"fieldtype": "Link",
			"options": "Supplier",
		},
		{
			"fieldname": "supplier_group",
			"label": "Nhóm đối tác",
			"fieldtype": "Link",
			"options": "Supplier Group",
		},
		{
			fieldname: "account",
			label: "Tài khoản",
			fieldtype: "Link",
			options: "Account",
			get_query: () => ({
                filters: {
                    company: frappe.query_report.get_filter_value("company"),
                    is_group: 0,
                }
            }),
		},
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
