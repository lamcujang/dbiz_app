// Copyright (c) 2024, lamnl and contributors
// For license information, please see license.txt

frappe.query_reports["Báo cáo tiến độ sản xuất cắt"] = {
    "filters": [
        {
            "fieldname": "start_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.now_date(), -1),
            "reqd": 1,
        },
        {
            "fieldname": "end_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.now_date(),
            "reqd": 1,
        },
        {
            "fieldname": "item",
            "label": __("Item"),
            "fieldtype": "Link",
            "options": "Item",
            "reqd": 0,
        },
    ],

    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname === 'status' && data) {
            if (value === 'Chậm tiến độ xuất') {
                value = `<span style="background-color: #ff3300">${value}</span>`
            } else if (value === 'Đã xong') {
                value = `<span style="background-color: #a8d08d">${value}</span>`
            }
            else if (value === 'Đang sản xuất') {
                value = `<span style="background-color: #8eaadb">${value}</span>`
            }
            else if (value === 'Close') {
                value = `<span style="background-color: #ffff00">${value}</span>`
            }
            else if (value === 'Đã xuất') {
                value = `<span style="background-color: #ffd965">${value}</span>`
            }
            else if (value === 'Chuẩn bị sản xuất') {
                value = `<span style="background-color: #bfbfbf">${value}</span>`
            }
        }

        return value;
    }
};
