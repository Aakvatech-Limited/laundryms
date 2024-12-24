// Copyright (c) 2024, Asha Melius Kisonga and contributors
// For license information, please see license.txt


frappe.ui.form.on('Laundry Task Plan Detail', {
    employee_type: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.employee_type) {
            // Reset the Employee field whenever Employee Type is changed
            frappe.model.set_value(cdt, cdn, "employee", null);
        }
    },
    employee: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.employee_type) {
            frm.fields_dict['laundry_task_plan_details'].grid.get_field('employee').get_query = function() {
                return {
                    filters: {
                        doctype: row.employee_type
                    }
                };
            };
        }
    }
});


//part of Item filtering and button to request
frappe.ui.form.on('Laundry Task Plan', {
    refresh: function (frm) {
        frm.add_custom_button(__('Request Materials'), function () {
            // Ensure the document is saved
            if (!frm.doc.name) {
                frappe.msgprint(__('Please save the document before requesting materials.'));
                return;
            }

            // Call the server method to create the Material Request
            frappe.call({
                method: 'laundry_management.laundry_management.doctype.laundry_task_plan.laundry_task_plan.create_material_request',
                args: {
                    docname: frm.doc.name  // Pass the document name
                },
                callback: function (response) {
                    if (response.message) {
                        frappe.msgprint(__('Material Request Created: {0}', [response.message]));
                    } else {
                        frappe.msgprint(__('Material Request creation failed.'));
                    }
                }
            });
        }, __('Actions'));
    }
});
