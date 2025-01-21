import frappe
from frappe import _



@frappe.whitelist(allow_guest=True)
def get_daily_task_schedule():
    """
    Fetch data from the Daily Task Schedule with employee names and laundry location details.
    """
    try:
        schedules = frappe.db.sql("""
            SELECT
                dts.name AS schedule_name,
                ll.facility_name AS location,
                dts.schedule_date AS schedule_date,
                dtst.task_name AS task_name,
                CASE
                    WHEN emp.employee_name IS NOT NULL THEN emp.employee_name
                    WHEN ext_emp.full_name IS NOT NULL THEN ext_emp.full_name
                    ELSE dtst.assigned_to
                END AS assigned_to,
                dts.status AS task_status
            FROM
                `tabDaily Task Schedule` dts
            INNER JOIN
                `tabDaily Task` dtst ON dtst.parent = dts.name
            LEFT JOIN
                `tabEmployee` emp ON emp.name = dtst.assigned_to
            LEFT JOIN
                `tabExternal Employee` ext_emp ON ext_emp.name = dtst.assigned_to
            LEFT JOIN
                `tabLaundry Location` ll ON ll.name = dts.location
            ORDER BY
                dts.modified DESC
        """, as_dict=True)

        if schedules:
            frappe.logger().info(f"Fetched {len(schedules)} records successfully.")
        else:
            frappe.logger().warning("No records found in Daily Task Schedule.")
        
        return schedules

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error Fetching Daily Task Schedule")
        frappe.throw(_("An error occurred while fetching task schedules. Please check the error logs for more details."))