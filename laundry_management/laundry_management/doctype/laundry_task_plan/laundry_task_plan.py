# Copyright (c) 2024, Asha Melius Kisonga and contributors
# For license information, please see license.txt
from frappe.model.document import Document
import frappe
from frappe import _


class LaundryTaskPlan(Document):
    def on_submit(self):
        self.create_daily_task_schedules()

    def create_daily_task_schedules(self):
        # Iterate through the child table entries in Laundry Task Plan
        for task in self.laundry_task_plan_details:
            # Create a new Daily Task Schedule
            daily_task_schedule = frappe.new_doc("Daily Task Schedule")
            daily_task_schedule.posting_date = self.posting_date
            daily_task_schedule.completion_date = self.completion_date

            # Append task details to the Daily Task child table
            daily_task_schedule.append("daily_task", {
                "task_name": task.task_name,          
                "assigned_to": task.employee_name,    
                "item": task.item,                   
                "qty": task.quantity,                
            })

        
            daily_task_schedule.insert()
            frappe.db.commit()  



##Item part

@frappe.whitelist()
def create_material_request(docname):
    """
    Create a Material Request using items from the child table of Laundry Task Plan.
    """
    # Fetch the Laundry Task Plan document
    laundry_task_plan = frappe.get_doc("Laundry Task Plan", docname)

    
    if not laundry_task_plan.laundry_task_plan_details:
        frappe.throw(_("No items found in the Laundry Task Plan to create a Material Request"))

    # Prepare Material Request items based on the 'item' field in the child table
    items = [
        {
            "item_code": row.item,
            "qty": row.quantity or 1,  
            "schedule_date": frappe.utils.today()
        }
        for row in laundry_task_plan.laundry_task_plan_details
        if row.item  
    ]

    if not items:
        frappe.throw(_("No valid items found in the Laundry Task Plan"))

    # Create a new Material Request
    material_request = frappe.get_doc({
        "doctype": "Material Request",
        "material_request_type": "Material Transfer",
        "items": items
    })

    try:
        material_request.insert()
        material_request.submit()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Material Request Creation Failed")
        frappe.throw(_("Failed to create Material Request: {0}").format(str(e)))

    # Return the name of the created Material Request
    frappe.msgprint(_("Material Request {0} created successfully").format(material_request.name))
    return material_request.name
