// Copyright (c) 2024, lamnl and contributors
// For license information, please see license.txt

frappe.query_reports["Báo cáo tình hình sx của ca SX lũy kế trong tháng"] = {
    "filters": [
        {
            "fieldname": "date",
            "fieldtype": "Date",
            "label": __("Date"),
            "default": frappe.datetime.now_date(),
            "reqd": 1,
        },
    ]
};
