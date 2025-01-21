// Copyright (c) 2025, Asha Melius Kisonga and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Laundry Task Plan", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on('Laundry Task Plan', {
    refresh: function (frm) {
        // Add a custom button in the toolbar
        frm.add_custom_button(__('Create Material Request'), function () {
            frappe.confirm(
                __('Are you sure you want to create a Material Request from this Task Plan?'),
                function () {
                    // Call the server-side method
                    frappe.call({
                        method: "laundry_management.laundry_management.doctype.laundry_task_plan.laundry_task_plan.create_material_request",
                        args: {
                            docname: frm.doc.name
                        },
                        callback: function (response) {
                            if (response.message) {
                                frappe.msgprint(
                                    __('Material Request {0} created successfully.', [response.message])
                                );
                                frm.reload_doc(); // Reload the form to reflect changes
                            }
                        },
                        error: function (error) {
                            frappe.msgprint(
                                __('Failed to create Material Request. See error logs.')
                            );
                            console.error(error);
                        }
                    });
                }
            );
        });
    }
});

