# Copyright (c) 2024, Asha Melius Kisonga and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class LaundryRequest(Document):
    def on_submit(self):
        self.create_laundry_task_plan()

    def create_laundry_task_plan(self):
        laundry_task_plan = frappe.new_doc("Laundry Task Plan")
        laundry_task_plan.laundry_request_id = self.name  
        #laundry_task_plan.posting_date = self.posting_date  
        laundry_task_plan.completion_date = self.completion_date  
        laundry_task_plan.supervisor_name = None  

        ## Populate the Laundry Task Plan Details
        laundry_task_plan.append("laundry_task_plan_details", {
            "item": None,                             
            "quantity": 1, 
            "task_name":f"{self.task_type}",
            "location":self.location,  
            "task_type": self.task_type,  
            "employee_name": None,        
                  
        }
        )
        
        laundry_task_plan.insert()
        frappe.db.commit()
        
        self.notify_manager_to_fill_supervisor_name(laundry_task_plan.name)
        frappe.msgprint(_("Laundry Task Plan has been created successfully."))
    
    def notify_manager_to_fill_supervisor_name(self, laundry_task_plan_name):
        manager_email= frappe.get_all(
        "Has Role",
        filters={
            "role": ["in", ["Manager"]],
            "parenttype": "User",
            "parent": ["in", frappe.get_all("User", filters={"enabled": 1}, pluck="name")]
        },
        fields=["parent"] )
        if manager_email:
           
    # Check if manager_email is a list, and extract the email if so
           if isinstance(manager_email, list):
               manager_email_address = manager_email[0].get('parent')

        
    

        if manager_email_address:
            message = f"""
                A new Laundry Task Plan <b>{laundry_task_plan_name}</b> has been created.
                Please update the Supervisor Name field.
                """
            frappe.sendmail(
                recipients=[manager_email_address],
                subject="Action Required: Fill Supervisor Name",
                message=message
            )
        else:
            frappe.msgprint(_("Manager notification failed: No manager email found."), alert=True)
