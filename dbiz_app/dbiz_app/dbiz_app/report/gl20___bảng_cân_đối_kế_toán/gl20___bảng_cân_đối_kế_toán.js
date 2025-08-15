// Copyright (c) 2025, lamnl and contributors
// For license information, please see license.txt

frappe.query_reports["GL20 - Bảng cân đối kế toán"] = $.extend({}, erpnext.financial_statements);

erpnext.utils.add_dimensions("GL20 - Bảng cân đối kế toán", 10);

frappe.query_reports["GL20 - Bảng cân đối kế toán"]["filters"].push({
    fieldname: "selected_view",
    label: __("Select View"),
    fieldtype: "Select",
    options: [
        { value: "Report", label: __("Report View") },
        { value: "Growth", label: __("Growth View") },
    ],
    default: "Report",
    reqd: 1,
});

frappe.query_reports["GL20 - Bảng cân đối kế toán"]["filters"].push({
    fieldname: "accumulated_values",
    label: __("Accumulated Values"),
    fieldtype: "Check",
    default: 1,
});

frappe.query_reports["GL20 - Bảng cân đối kế toán"]["filters"].push({
    fieldname: "include_default_book_entries",
    label: __("Include Default FB Entries"),
    fieldtype: "Check",
    default: 1,
});
