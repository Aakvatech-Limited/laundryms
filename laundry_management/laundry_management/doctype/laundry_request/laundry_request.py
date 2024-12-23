# Copyright (c) 2024, Asha Melius Kisonga and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LaundryRequest(Document):
    def before_insert(self):
        # Get the last used Laundry Request ID
        last_id = frappe.db.get_value("Laundry Request", {}, "max(laundry_request_id)")
        
        # Set the laundry_request_id to the next value
        self.laundry_request_id = (last_id or 0) + 1