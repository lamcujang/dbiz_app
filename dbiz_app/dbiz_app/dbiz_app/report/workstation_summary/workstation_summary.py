import frappe
from frappe import _
from frappe.utils import getdate
from datetime import datetime, timedelta

import frappe.utils

def get_chart_data(data, filters):
    labels = []
    datasets = {"Completed": [], "Total": []}
    work_order_accumulated = {}  # Dictionary để lưu giá trị cộng dồn theo Work Order

    # Duyệt qua dữ liệu
    for d in data:
        plan_date = getdate(d.plan_date).strftime("%Y-%m-%d")
        
        # Kiểm tra xem plan_date đã có trong labels chưa
        if plan_date not in labels:
            label = plan_date + " - " + (d.work_order if d.work_order else 'No Plan Date')
            labels.append(label)

        # Kiểm tra nếu d.work_order là None, sử dụng giá trị thay thế
        work_order_key = d.work_order if d.work_order else 'No Work Order'

        # Cộng dồn Completed chỉ khi Work Order trùng
        if work_order_key not in work_order_accumulated:
            work_order_accumulated[work_order_key] = 0  # Khởi tạo giá trị tích lũy

        work_order_accumulated[work_order_key] += (d.qty_completed if d.qty_completed else 0)

        # Thêm dữ liệu vào các tập dữ liệu
        datasets["Completed"].append(work_order_accumulated[work_order_key])
        datasets["Total"].append(d.total_qty_work_order)  # Thêm Total kèm Work Order


    # Cấu trúc dữ liệu biểu đồ
    chart = {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": "Completed (Accumulated)",
                    "values": datasets["Completed"]
                },
                {
                    "name": "Total",
                    "values": datasets["Total"]  
                },
            ],
        },
        "type": "bar",  
    }

    return chart

def generate_date_range(from_date, to_date):
    start_date = datetime.strptime(from_date, "%Y-%m-%d")
    end_date = datetime.strptime(to_date, "%Y-%m-%d")
    delta = timedelta(days=1)
    dates = []
    while start_date <= end_date:
        dates.append(start_date.strftime("%Y-%m-%d"))
        start_date += delta
    return dates

def execute(filters=None):
    columns, data = [], []
    data = get_data(filters)
    columns = get_columns(filters)
    chart_data = get_chart_data(data, filters)
    return columns, data, None, chart_data

def get_data(filters):
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    date_range = generate_date_range(from_date, to_date)
    
    # Convert date_range list into a string for SQL
    date_cte = " UNION ALL ".join([f"SELECT '{date}' AS plan_date" for date in date_range])
    
    conditions = get_conditions(filters)
    data = frappe.db.sql(
        f"""
        WITH date_range AS (
            {date_cte}
        ),
        workstations AS (
            SELECT name AS workstation FROM `tabWorkstation`
		    where workstation_type in ('TRON','THOIIN','CAT')
        ),
        combined AS (
            SELECT 
                dr.plan_date,
                ws.workstation
            FROM 
                date_range dr
            CROSS JOIN 
                workstations ws
        )

        SELECT 
            c.plan_date,
            c.workstation,
            jc.work_order,
            jc.name jc_name,
            jc.shift,
            jc.operation,
            jc.production_item,
            jc.total_completed_qty AS qty_completed,
            jc.for_semi_quantity AS total_plan_day,
            (select sum(total_semi_fg) from `tabOperation Workstations` too where too.operation = jc.operation and too.parent = wo.name and too.item_semi_fg = jc.semi_fg) total_qty_work_order
        FROM 
            combined c
             left JOIN `tabJob Card` jc ON jc.posting_date = c.plan_date AND jc.workstation = c.workstation 
             left JOIN `tabWork Order` wo ON wo.name = jc.work_order 
        WHERE (c.workstation = COALESCE(%(workstation)s, c.workstation) OR %(workstation)s IS NULL)
        AND (wo.name = COALESCE(%(work_order)s, wo.name) OR %(work_order)s IS NULL)
        AND (jc.name = COALESCE(%(job_card)s, jc.name) OR %(job_card)s IS NULL)
        and (wo.production_item = COALESCE(%(production_item)s, wo.production_item) OR %(production_item)s IS NULL)
        and (jc.operation = COALESCE(%(operation)s, jc.operation) OR %(operation)s IS NULL)
        and c.plan_date <= sysdate()
        GROUP BY 
            c.plan_date,
            c.workstation,
            jc.work_order,
            jc.operation,
            jc.name

        UNION ALL

        SELECT 
            c.plan_date,
            c.workstation,
            jc.work_order,
            jc.name jc_name,
            jc.shift,
            jc.operation,
            jc.production_item,
            jc.total_completed_qty AS qty_completed,
            jc.for_semi_quantity AS total_plan_day,
            (select sum(total_semi_fg) from `tabOperation Workstations` too where too.operation = jc.operation and too.parent = wo.name and too.item_semi_fg = jc.semi_fg) total_qty_work_order
        FROM 
            combined c
             left JOIN `tabJob Card` jc ON jc.posting_date = c.plan_date AND jc.workstation = c.workstation 
             left JOIN `tabWork Order` wo ON wo.name = jc.work_order 
        WHERE (c.workstation = COALESCE(%(workstation)s, c.workstation) OR %(workstation)s IS NULL)
        AND (wo.name = COALESCE(%(work_order)s, wo.name) OR %(work_order)s IS NULL)
        AND (jc.name = COALESCE(%(job_card)s, jc.name) OR %(job_card)s IS NULL)
        and (wo.production_item = COALESCE(%(production_item)s, wo.production_item) OR %(production_item)s IS NULL)
        and (jc.operation = COALESCE(%(operation)s, jc.operation) OR %(operation)s IS NULL)
        and c.plan_date > sysdate()
        GROUP BY 
            c.plan_date,
            c.workstation,
            jc.work_order,
            jc.operation,
            jc.name

        ORDER BY 
            plan_date ASC,
            workstation ASC
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
        if not filters.get("workstation"):
            conditions["workstation"] = None
        if not filters.get("operation"):
            conditions["operation"] = None
        if not filters.get("job_card"):
            conditions["job_card"] = None
        if not filters.get("production_item"):
            conditions["production_item"] = None
        if not filters.get("work_order"):
            conditions["work_order"] = None
    return conditions

def get_columns(filters):
    return [
        {
            "label": "Plan Date",
            "fieldname": "plan_date",
            "fieldtype": "Date",
            "width": 150,
        },
        {
            "label": "Work Order",
            "fieldname": "work_order",
            "fieldtype": "Link",
            "options": "Work Order",
            "width": 200,
        },
        {
            "label": "Job Card",
            "fieldname": "jc_name",
            "fieldtype": "Link",
            "options": "Job Card",
            "width": 200,
        },
        {
            "label": "Workstation",
            "fieldname": "workstation",
            "fieldtype": "Link",
            "options": "Workstation",
            "width": 200,
        },
        {
            "label": "Operation",
            "fieldname": "operation",
            "fieldtype": "Link",
            "options": "Operation",
            "width": 150,
        },
        {
            "label": "Production Item",
            "fieldname": "production_item",
            "fieldtype": "Link",
            "options": "Item",
            "width": 150,
        },
        {
            "label": "Completed Qty",
            "fieldname": "qty_completed",
            "fieldtype": "Float",
            "width": 120,
        },
        {
            "label": "Total Plan Day",
            "fieldname": "total_plan_day",
            "fieldtype": "Float",
            "width": 120,
        },
        {
            "label": "Total Quantity",
            "fieldname": "total_qty_work_order",
            "fieldtype": "Float",
            "width": 120,
        },
    ]