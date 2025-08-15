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
            "label": "Số chứng từ nhập kho",
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
            "label": "Nhà cung cấp",
            "fieldname": "supplier_name",
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
    # INV10
    query = f"""
    SELECT DISTINCT 
        ROW_NUMBER() OVER (ORDER BY tsle.posting_date) AS STT,
        w.name AS warehouse_code, 
        w.warehouse_name AS warehouse_name,  
        CASE 
            WHEN tsle.voucher_type = 'Purchase Receipt' THEN 'Nhập mua hàng'
            WHEN tsle.voucher_type = 'Stock Entry' AND tse.stock_entry_type = 'Manufacture' THEN 'Nhập thành phẩm'
            WHEN tsle.voucher_type = 'Stock Entry' AND tse.stock_entry_type = 'Material Transfer for Manufacture' THEN 'Nhập chuyển kho cho sản xuất'
            WHEN tsle.voucher_type = 'Stock Entry' AND tse.stock_entry_type = 'Material Transfer' THEN 'Nhập chuyển kho'
            ELSE 'Other'
        END AS transaction_type,
        tsle.posting_date AS posting_date, 
        CASE
            WHEN tsle.voucher_type = 'Purchase Receipt' THEN tpr.name
            WHEN tsle.voucher_type = 'Stock Entry' THEN tse.name
            ELSE NULL
        END AS stock_entry_no, 
        CASE 
            WHEN tsle.voucher_type = 'Purchase Receipt' THEN tpri.purchase_order
            ELSE NULL
        END AS order_invoice_no, 
        CASE 
            WHEN tsle.voucher_type = 'Purchase Receipt' THEN tpr.supplier_name
            WHEN tse.stock_entry_type = 'Material Transfer for Manufacture' THEN tse.from_warehouse
            ELSE NULL
        END AS supplier_name, 
        NULL AS description,  -- Có thể bổ sung sau nếu cần từ các trường khác
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
        `tabPurchase Receipt` tpr ON tsle.voucher_type = 'Purchase Receipt' AND tpr.name = tsle.voucher_no
    LEFT JOIN 
        `tabPurchase Receipt Item` tpri ON tpri.parent = tpr.name AND tpri.item_code = tsle.item_code
    INNER JOIN
        `tabItem` ti ON ti.item_code = tsle.item_code
    LEFT JOIN 
        `tabSupplier` tsl ON tsl.name = tpr.supplier
    WHERE
        (tsle.voucher_type = 'Purchase Receipt'
        OR (tsle.voucher_type = 'Stock Entry' AND tse.stock_entry_type IN ('Manufacture', 'Material Transfer for Manufacture', 'Material Transfer')))
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
        conditions.append("tpri.item_group = %(item_group)s")
        values["item_group"] = filters["item_group"]
    if filters.get("warehouse"):
        conditions.append("w.name = %(warehouse)s")
        values["warehouse"] = filters["warehouse"]
    if filters.get("supplier"):
        conditions.append("tsl.name = %(supplier)s")
        values["supplier"] = filters["supplier"]
    if filters.get("supplier_group"):
        conditions.append("tsl.supplier_group = %(supplier_group)s")
        values["supplier_group"] = filters["supplier_group"]
    if filters.get("account"):
        conditions.append("(w.account = %(account)s OR %(account)s IS NULL OR %(account)s = '')")
        values["account"] = filters["account"]

    # Combine conditions with " AND " and prepend if any conditions exist
    condition_str = f"AND {' AND '.join(conditions)}" if conditions else ""

    return condition_str, values
