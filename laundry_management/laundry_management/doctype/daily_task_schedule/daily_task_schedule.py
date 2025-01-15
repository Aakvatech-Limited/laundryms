# Copyright (c) 2024, Asha Melius Kisonga and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DailyTaskSchedule(Document):
    def before_insert(self):
    
        if not self.schedule_date:
            self.schedule_date = frappe.utils.nowdate()  
