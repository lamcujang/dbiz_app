import frappe
@frappe.whitelist()
def get_wo_by_workstaion_in_jobcard(workstation):
    try:
        work_orders = frappe.db.sql("""
            SELECT 
                wo.name, 
                jc.name AS jc_name, 
                jct.employee, 
                jc.shift
            FROM 
                `tabWorkstation` ws
            JOIN 
                `tabJob Card` jc ON jc.workstation = ws.name AND jc.docstatus = 1
            JOIN 
                `tabWork Order` wo ON wo.name = jc.work_order AND wo.docstatus = 1
            JOIN 
                `tabJob Card Time Log` jct ON jct.parent = jc.name
            WHERE 
                ws.name = %(workstation)s
                AND jc.creation = (
                    SELECT MAX(jc2.creation)
                    FROM `tabJob Card` jc2
                    WHERE jc2.work_order = wo.name
                    AND jc2.workstation = ws.name
                    AND jc2.docstatus = 1
                )
            and jc.posting_date BETWEEN CURDATE() - INTERVAL 2 DAY AND CURDATE()
            order by jc.posting_date desc""",
            {"workstation": workstation}, as_dict=True)
        return work_orders if work_orders else []
    except Exception as e:
        return []
    