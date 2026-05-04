import frappe


def execute():
	roles = [
		"Laundry Manager",
		"Laundry Staff",
		"Cashier",
		"Institutional Client",
		"Retail Customer",
	]
	for role_name in roles:
		if not frappe.db.exists("Role", role_name):
			frappe.get_doc({"doctype": "Role", "role_name": role_name}).insert(ignore_permissions=True)
	frappe.db.commit()
