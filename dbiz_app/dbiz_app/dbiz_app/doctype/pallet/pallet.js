// Copyright (c) 2024, lamnl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Pallet", {
	async refresh(frm) {
        // QRcode
		frm.set_df_property('custom_qr_link', 'options', `<div style="text-align: center;">
            <img src="https://quickchart.io/qr?text=${encodeURIComponent(frm.doc.doctype +";" +frm.doc.name)}" 
                 alt="QR Code" 
                 style="max-width: 150px; max-height: 150px;">
         </div>`);
        if(!frm.doc.employee){
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Employee',
                    filters: { user_id: frappe.session.user },
                    fieldname: ['name']
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('employee', r.message.name);
                    }
                }
            });
        }
	},
});
