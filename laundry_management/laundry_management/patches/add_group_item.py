iimport frappe

def execute():
    
    if not frappe.db.exists("Item Group", "Laundry Items"):
        laundry_item_group = {
            "doctype": "Item Group",
            "item_group_name": "Laundry Items",
            "parent_item_group": "All Item Groups",
        }
        frappe.get_doc(laundry_item_group).insert(ignore_permissions=True)
        frappe.db.commit()

    
    if not frappe.db.exists("Item Group", "Housekeeping Items"):
        housekeeping_item_group = {
            "doctype": "Item Group",
            "item_group_name": "Housekeeping Items",
            "parent_item_group": "All Item Groups",
        }
        frappe.get_doc(housekeeping_item_group).insert(ignore_permissions=True)
        frappe.db.commit()

    
    laundry_items = [
        "Bed Sheets", "Towels", "Patient Gowns", "Scrubs",
        "Curtains", "Pillow Covers", "Blankets", "Lab Coats",
        "Duvet Covers", "Tablecloths"
    ]

    
    housekeeping_items = [
        "Mop", "Disinfectant Spray", "Cleaning Cloths", "Dusting Brushes",
        "Garbage Bags", "Vacuum Cleaners", "Floor Cleaners", "Window Cleaners",
        "Air Fresheners", "Stain Removers"
    ]

    
    for item_name in laundry_items:
        if not frappe.db.exists("Item", item_name):
            laundry_item = {
                "doctype": "Item",
                "item_name": item_name,
                "item_group": "Laundry Items",
            }
            frappe.get_doc(laundry_item).insert(ignore_permissions=True)
            frappe.db.commit()

    
    for item_name in housekeeping_items:
        if not frappe.db.exists("Item", item_name):
            housekeeping_item = {
                "doctype": "Item",
                "item_name": item_name,
                "item_group": "Housekeeping Items",
            }
            frappe.get_doc(housekeeping_item).insert(ignore_permissions=True)
            frappe.db.commit()
