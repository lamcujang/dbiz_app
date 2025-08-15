# Copyright (c) 2024, lamnl and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    if not filters:
        filters = {}

    if filters.start_date > filters.end_date:
        frappe.throw(_("From Date must be before To Date"))

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {
            "label": "STT",
            "fieldname": "STT",
            "fieldtype": "Int",
            "width": 50,
            "align": "left",
        },
        {
            "label": "Mã kho",
            "fieldname": "warehouse_code",
            "fieldtype": "Data",
            "width": 150,
            "align": "left",
        },
        {
            "label": "Tên kho",
            "fieldname": "warehouse_name",
            "fieldtype": "Data",
            "width": 150,
            "align": "left",
        },
        {
            "label": "Loại giao dịch",
            "fieldname": "transaction_type",
            "fieldtype": "Data",
            "width": 150,
            "align": "left",
        },
        {
            "label": "Ngày",
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 100,
            "align": "left",
        },
        {
            "label": "Số chứng từ xuất kho",
            "fieldname": "stock_entry_no",
            "fieldtype": "Data",
            "width": 150,
            "align": "left",
        },
        {
            "label": "Số đơn hàng/hóa đơn",
            "fieldname": "order_invoice_no",
            "fieldtype": "Data",
            "width": 150,
            "align": "left",
        },
        {
            "label": "Đối tác",
            "fieldname": "customer",
            "fieldtype": "Data",
            "width": 200,
            "align": "left",
        },
        {
            "label": "Diễn giải",
            "fieldname": "description",
            "fieldtype": "Data",
            "width": 200,
            "align": "left",
        },
        {
            "label": "Mã sản phẩm",
            "fieldname": "item_code",
            "fieldtype": "Data",
            "width": 120,
            "align": "left",
        },
        {
            "label": "Tên sản phẩm",
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 200,
            "align": "left",
        },
        {
            "label": "ĐVT",
            "fieldname": "unit_of_measure",
            "fieldtype": "Data",
            "width": 80,
            "align": "left",
        },
        {
            "label": "Giá",
            "fieldname": "rate",
            "fieldtype": "Float",
            "width": 100,
            "align": "left",
        },
        {
            "label": "Slg.",
            "fieldname": "quantity",
            "fieldtype": "Float",
            "width": 80,
            "align": "left",
        },
        {
            "label": "Thành tiền",
            "fieldname": "amount",
            "fieldtype": "Float",
            "width": 120,
            "align": "left",
        },
    ]


def get_data(filters):
    # Build dynamic conditions based on available filters
    conditions, values = get_conditions(filters)
    # INV11
    query = f"""
		SELECT DISTINCT 
            ROW_NUMBER() OVER (ORDER BY tsle.posting_date) AS STT,
            w.name AS warehouse_code, 
            w.warehouse_name AS warehouse_name,  
            CASE 
                WHEN tsle.voucher_type = 'Delivery Note' THEN 'Xuất bán hàng'
                WHEN tsle.voucher_type = 'Stock Entry' AND tse.stock_entry_type = 'Manufacture' THEN 'Xuất NVL chế biến'
                WHEN tsle.voucher_type = 'Stock Entry' AND tse.stock_entry_type = 'Material Transfer' THEN 'Xuất hàng chuyển kho'
                WHEN tsle.voucher_type = 'Stock Entry' AND tse.stock_entry_type = 'Material Issue' THEN 'Xuất khác'
                ELSE NULL
            END AS transaction_type,
            tsle.posting_date AS posting_date, 
            CASE
                WHEN tsle.voucher_type = 'Delivery Note' THEN tdn.name
                WHEN tsle.voucher_type = 'Stock Entry' THEN tse.name
                ELSE NULL
            END AS stock_entry_no, 
            CASE 
                WHEN tsle.voucher_type = 'Delivery Note' THEN tdni.against_sales_order
                ELSE NULL
            END AS order_invoice_no, 
            CASE 
                WHEN tsle.voucher_type = 'Delivery Note' THEN tdn.customer_name 
                WHEN tsle.voucher_type = 'Stock Entry' AND tse.stock_entry_type = 'Material Transfer' THEN tse.to_warehouse 
                ELSE NULL
            END AS customer, 
            tse.description AS description, 
            tsle.item_code AS item_code, 
            ti.item_name AS item_name, 
            tsle.stock_uom AS unit_of_measure, 
            tsle.valuation_rate AS rate, 
            ABS(tsle.actual_qty) AS quantity, 
            ABS(tsle.valuation_rate * tsle.actual_qty) AS amount
        FROM 
            `tabStock Ledger Entry` tsle
        LEFT JOIN 
            `tabWarehouse` w ON tsle.warehouse = w.name
        LEFT JOIN 
            `tabStock Entry` tse ON tsle.voucher_type = 'Stock Entry' AND tse.name = tsle.voucher_no
        LEFT JOIN 
            `tabDelivery Note` tdn ON tsle.voucher_type = 'Delivery Note' AND tdn.name = tsle.voucher_no
        LEFT JOIN 
            `tabDelivery Note Item` tdni ON tdni.parent = tdn.name AND tdni.item_code = tsle.item_code
        INNER JOIN
            `tabItem` ti ON ti.item_code = tsle.item_code
        LEFT JOIN 
            `tabCustomer` cs ON cs.name = tdn.customer
        WHERE
            (tsle.voucher_type = 'Delivery Note'
            OR (tsle.voucher_type = 'Stock Entry' AND tse.stock_entry_type IN ('Manufacture', 'Material Transfer', 'Material Issue')))
            AND tsle.actual_qty > 0
            {conditions}


    """
    # print("Query: ", query)
    data = frappe.db.sql(query, values, as_dict=True)
    return data


def get_conditions(filters):
    # Initialize condition string and parameters dictionary
    conditions = []
    values = {
        "start_date": filters.get("start_date"),
        "end_date": filters.get("end_date"),
        "company": filters.get("company"),
        "account": filters.get("account"),
    }

    conditions.append(
        "tsle.posting_date BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)"
    )
    conditions.append("tsle.company = %(company)s")

    # Dynamically add conditions based on filter availability
    if filters.get("item_group"):
        conditions.append("ti.item_group = %(item_group)s")
        values["item_group"] = filters["item_group"]
    if filters.get("warehouse"):
        conditions.append("w.name = %(warehouse)s")
        values["warehouse"] = filters["warehouse"]
    if filters.get("customer"):
        conditions.append("cs.name = %(customer)s")
        values["customer"] = filters["customer"]
    if filters.get("customer_group"):
        conditions.append("cs.customer_group = %(customer_group)s")
        values["customer_group"] = filters["customer_group"]
    if filters.get("account"):
        conditions.append("(w.account = %(account)s OR %(account)s IS NULL OR %(account)s = '')")
        values["account"] = filters["account"]

    # Combine conditions with " AND " and prepend if any conditions exist
    condition_str = f"AND {' AND '.join(conditions)}" if conditions else ""

    return condition_str, values
