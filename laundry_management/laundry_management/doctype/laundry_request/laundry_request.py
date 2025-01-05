# Copyright (c) 2024, Asha Melius Kisonga and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class LaundryRequest(Document):
    def on_submit(self):
        # Create Laundry Task Plan on submit
        self.create_laundry_task_plan()

    def create_laundry_task_plan(self):
        
        # Create a new Laundry Task Plan document
        laundry_task_plan = frappe.new_doc("Laundry Task Plan")
        
        laundry_task_plan.laundry_request_id = self.name  
        laundry_task_plan.posting_date = self.posting_date  
        laundry_task_plan.completion_date = self.completion_date  
        laundry_task_plan.supervisor_name = None  

        ## Populate the Laundry Task Plan Details
        laundry_task_plan.append("laundry_task_plan_details", {
            "item": None,                             # Item to be laundered
            "quantity": 1, 
            "task_name":f"{self.task_type}",
            "location":{self.location},  # Generate a dynamic task name
            "task_type": self.task_type,  # Task type from Laundry Request
            "employee_name": None,        # Assign employee if needed, leave blank if not available
                  
        }
        )
        
        
        laundry_task_plan.insert()
        frappe.db.commit()

        
        #Notify the user (e.g., Manager) to fill Supervisor Name
        self.notify_manager_to_fill_supervisor_name(laundry_task_plan.name)

        # Notify the user about task plan creation
        frappe.msgprint(_("Laundry Task Plan has been created successfully."))
    
    def notify_manager_to_fill_supervisor_name(self, laundry_task_plan_name):
        # Notify the manager to fill in the supervisor name
        manager_email = frappe.db.get_value("customer", {"role": "Manager"}, "email")
        if manager_email:
            message = f"""
                A new Laundry Task Plan <b>{laundry_task_plan_name}</b> has been created.
                Please update the Supervisor Name field.
                """
            frappe.sendmail(
                recipients=[manager_email],
                subject="Action Required: Fill Supervisor Name",
                message=message
            )
        else:
            frappe.msgprint(_("Manager notification failed: No manager email found."), alert=True)
