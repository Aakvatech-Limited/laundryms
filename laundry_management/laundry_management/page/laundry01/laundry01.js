frappe.pages['laundry01'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Daily Task Schedule',  
        single_column: true
    });


    page.set_primary_action('Schedule Date', function() {
        frappe.msgprint('Schedule Date Action triggered');
    });




	$(frappe.render_template("laundry01_page", {})).appendTo(page.body);
};








