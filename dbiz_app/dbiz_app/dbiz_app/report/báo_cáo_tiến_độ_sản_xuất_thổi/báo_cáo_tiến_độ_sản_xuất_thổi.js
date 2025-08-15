// Copyright (c) 2024, lamnl and contributors
// For license information, please see license.txt

frappe.query_reports["Báo Cáo tiến độ sản xuất thổi"] = {
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

    // "formatter": function (value, row, column, data, default_formatter) {
    //     value = default_formatter(value, row, column, data);
    //     if (!value)
    //         value = " "
    //     if (column.id == "delivery_date" || column.id == "export_cont_date" || column.id == "customer_name" || column.id == "production_plan" || column.id == "production_item") {
    //         var dir = {
    //             "Not Started": "grey",
    //             "Cancelled": "yellow",
    //             "In Process": "blue",
    //             "Completed": "green",
    //         }
    //         value = "<div style='background-color:" + dir[data["status"]] + ";font-weight:bold;'>" + value + "</div>";
    //     }
    //     if (column.id == "produced_qty") {
    //         value = "<div style='color:grey;'>" + value + "</div>";
    //     }
    //     if (column.id == "shortage_qty") {
    //         value = "<div style='background-color:pink;'>" + value + "</div>";
    //     }
    //     return value;
    // }
};

function getYearOptions() {
    const currentYear = new Date().getFullYear();
    return Array.from({ length: 11 }, (_, i) => currentYear - i).join("\n");
}
