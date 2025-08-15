# Copyright (c) 2025, lamnl and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    if not filters:
        filters = {}

    # Define columns
    columns = get_columns()

    # SQL query with parameters from filters
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {
            "label": "Tên TSCĐ",
            "fieldname": "asset_name",
            "fieldtype": "Data",
        },
        {
            "label": "Mã số",
            "fieldname": "name",
            "fieldtype": "Data",
        },
        {
            "label": "Nơi sử dụng",
            "fieldname": "location",
            "fieldtype": "Data",
        },
        {
            "label": "Số lượng theo sổ KT",
            "fieldname": "asset_quantity",
            "fieldtype": "Float",
        },
        {
            "label": "Nguyên giá theo sổ KT",
            "fieldname": "book_value",
            "fieldtype": "Float",
        },
        {
            "label": "Giá trị còn lại theo sổ KT",
            "fieldname": "book_remain",
            "fieldtype": "Float",
        },
        {
            "label": "SL theo kiểm kê",
            "fieldname": "paid_amount",
            "fieldtype": "Float",
        },
        {
            "label": "Nguyên giá theo kiểm kê",
            "fieldname": "new_value",
            "fieldtype": "Float",
        },
        {
            "label": "Giá trị còn lại theo kiểm kê",
            "fieldname": "new_remain",
            "fieldtype": "Float",
        },
        {
            "label": "Chênh lệch về số lượng",
            "fieldname": "qty_diff",
            "fieldtype": "Float",
        },
        {
            "label": "Chênh lệch về nguyên giá",
            "fieldname": "value_diff",
            "fieldtype": "Float",
        },
        {
            "label": "Chênh lệch về giá trị còn lại",
            "fieldname": "remain_diff",
            "fieldtype": "Float",
        },
        {
            "label": "Ghi chú",
            "fieldname": "note",
            "fieldtype": "Data",
        },
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    data = frappe.db.sql(
        """
        SELECT 
			ta.asset_name,
			ta.name,
			ta.location,
			ta.asset_quantity,
			tard.book_value,
			tard.book_remain,
			tard.actual_qty,
			tard.new_value,
			tard.new_remain,
			tard.qty - tard.actual_qty AS qty_diff,
			tard.book_value - tard.new_value AS value_diff,
			tard.book_remain - tard.new_remain AS remain_diff,
			NULL AS note
		FROM 
			`tabAsset Reconciliation` tar
		LEFT JOIN `tabAsset Reconciliation Details` tard ON
			tar.name = tard.parent
		LEFT JOIN `tabAsset` ta ON
			tard.asset_name = ta.name
		WHERE 
			tar.posting_date < %(end_date)s
			AND tar.company = %(company)s
			AND ta.booked_fixed_asset = 1
			AND ta.STATUS IN('Submitted', 'Partially Depreciated', 'Fully Depreciated', 'Scrapped')
        """,
        conditions,  # filters
        as_dict=True,
    )
    return data


def get_conditions(filters):
    conditions = {}
    for key, value in filters.items():
        if filters.get(key):
            conditions[key] = value
    return conditions
