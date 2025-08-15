// Copyright (c) 2024, lamnl and contributors
// For license information, please see license.txt

frappe.query_reports["GL18 - Báo cáo lưu chuyển tiền tệ"] = $.extend({}, erpnext.financial_statements);

erpnext.utils.add_dimensions("GL18 - Báo cáo lưu chuyển tiền tệ", 10);

// The last item in the array is the definition for Presentation Currency
// filter. It won't be used in cash flow for now so we pop it. Please take
// of this if you are working here.

frappe.query_reports["GL18 - Báo cáo lưu chuyển tiền tệ"]["filters"].splice(8, 1);

frappe.query_reports["GL18 - Báo cáo lưu chuyển tiền tệ"]["filters"].push({
    fieldname: "include_default_book_entries",
    label: __("Include Default FB Entries"),
    fieldtype: "Check",
    default: 1,
});
