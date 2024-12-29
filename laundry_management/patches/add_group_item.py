import frappe

def execute():
    """This is for auto create of Item Group: Housekeeping Item"""

    # Create Laundry Items Group
    if not frappe.db.exists("Item Group", "Laundry Items"):
        laundry_item_group = {
            "doctype": "Item Group",
            "item_group_name": "Laundry Items",
            "parent_item_group": "All Item Groups",
        }
        frappe.get_doc(laundry_item_group).insert(ignore_permissions=True)
        frappe.db.commit()

    # Create Housekeeping Items Group
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

    # Create Laundry Items with Auto-generated Item Codes
    for idx, item in enumerate(laundry_items, start=1):
        item_code = f"LAUNDRY-{idx:03}"  
        if not frappe.db.exists("Item", item_code):
            laundry_item = {
                "doctype": "Item",
                "item_code": item_code,
                "item_name": item,
                "item_group": "Laundry Items",
                "is_stock_item": 1,  
            }
            frappe.get_doc(laundry_item).insert(ignore_permissions=True)
            frappe.db.commit()

    # Create Housekeeping Items with Auto-generated Item Codes
    for idx, item in enumerate(housekeeping_items, start=1):
        item_code = f"HOUSEKEEP-{idx:03}"  # Generate item code
        if not frappe.db.exists("Item", item_code):
            housekeeping_item = {
                "doctype": "Item",
                "item_code": item_code,
                "item_name": item,
                "item_group": "Housekeeping Items",
                "is_stock_item": 1, 
            }
            frappe.get_doc(housekeeping_item).insert(ignore_permissions=True)
            frappe.db.commit()
