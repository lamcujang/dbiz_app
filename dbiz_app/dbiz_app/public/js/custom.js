$(document).on('app_ready', async function () {
    var doctypes = ""; 
    await frappe.call({ 
        method: "frappe.client.get_list", 
        args: { 
            doctype: "DocType", 
            fields: ["name"], 
            filters: { istable: 0 }, 
            limit_page_length: 1000 
        }, 
        callback: function (r) { 
            if (r.message) { 
                doctypes = r.message.map(doc => doc.name); 
            } 
        } 
    }); 

    $.each(doctypes, function (i, doctype) { 
        frappe.ui.form.on(doctype, "refresh", function (frm) { 
            if (frm.page.custom_buttons && frm.page.custom_buttons['Back']) {
                frm.page.custom_buttons['Back'].remove();
                delete frm.page.custom_buttons['Back'];
            }

            frm.add_custom_button( 
                `<i class="fa fa-arrow-left" style="margin-right: 5px;"></i> ${__('Back')}`, 
                function () { 
                    if (window.history.length > 1) { 
                        window.history.back(); 
                    } else { 
                        frappe.set_route('List', frm.doctype); 
                    } 
                } 
            ).addClass('btn-primary');
        }); 
    });
});

frappe.ui.form.Form.prototype.add_custom_button = function(label, fn, group) {
    if (group && group.indexOf("fa fa-") !== -1) group = null;
    let btn = this.page.add_inner_button(label, fn, group);
    this.custom_buttons[label] = btn;
    return btn;
};


