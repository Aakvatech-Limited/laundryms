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
                    docname: frm.doc.name  
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

// //multiple selection for item
// frappe.ui.form.on('Laundry Task Plan Details', {
//     select_items_button: function(frm, cdt, cdn) {
//         let row = locals[cdt][cdn];

        
//         frappe.call({
//             method: "frappe.client.get_list",
//             args: {
//                 doctype: "Item",
//                 filters: { disabled: 0 }, 
//                 fields: ["name"]         
//             },
//             callback: function(response) {
//                 if (response.message) {
//                     let item_list = response.message.map(item => item.name);

                    
//                     let dialog = new frappe.ui.Dialog({
//                         title: "Select Items",
//                         fields: [
//                             {
//                                 label: "Items",
//                                 fieldname: "items",
//                                 fieldtype: "MultiCheck",
//                                 options: item_list.map(item => ({ label: item, value: item }))
//                             }
//                         ],
//                         primary_action_label: "Add Selected Items",
//                         primary_action(values) {
                            
//                             if (values.items && values.items.length > 0) {
//                                 row.item = values.items.join(", ");
//                                 frm.refresh_field("laundry_task_plan_details");
//                             } else {
//                                 frappe.msgprint("No items were selected.");
//                             }
//                             dialog.hide();
//                         }
//                     });

//                     dialog.show();
//                 } else {
//                     frappe.msgprint("No items found in the Stock module.");
//                 }
//             }
//         });
//     },
    
    //refresh: function(frm) {
        
        //frm.fields_dict['laundry_task_plan_details'].grid.fields_map['select_items_button'].wrapper.style.backgroundColor = "#28a745"; 
        //frm.fields_dict['laundry_task_plan_details'].grid.fields_map['select_items_button'].wrapper.style.color = "#fff"; 
        //frm.fields_dict['laundry_task_plan_details'].grid.fields_map['select_items_button'].wrapper.style.fontWeight = "bold"; 
    //}
//});

