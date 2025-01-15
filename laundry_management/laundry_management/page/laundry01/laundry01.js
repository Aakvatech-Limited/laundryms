frappe.pages['laundry01'].on_page_load = function (wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Daily Task Schedule',
        single_column: true,
    });

    const title_container = $('<div>').addClass('title-container');

    
    const marquee_title = $('<h2>')
        .addClass('marquee-title')
        .text('Daily Task Schedule');

    
    title_container.append(marquee_title);

    
    $(wrapper).find('.page-content').prepend(title_container);

    // Append HTML
    $(frappe.render_template('laundry01_page')).appendTo(page.body);
    

    frappe.call({
        method: "laundry_management.laundry_management.page.laundry01.laundry01.get_daily_task_schedule",
        callback: function(response) {
            if (response.message) {
                const data = response.message;
                let tableBody = document.getElementById("task_schedule_table");
                tableBody.innerHTML = ""; 
                
                
                data.forEach(row => {
                    let tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td>${row.schedule_name}</td>
                        <td>${row.task_name}</td>
                        <td>${row.assigned_to}</td>
                        <td>${row.location}</td>
                        <td>${row.task_status}</td>
                        <td>${row.schedule_date}</td>
                    `;
                    tableBody.appendChild(tr);
                });
            } else {
                console.error("No data returned from server.");
            }
        },
        error: function(error) {
            console.error("Error in API call:", error);
        }
    });
}