// Copyright (c) 2024, lamnl and contributors
// For license information, please see license.txt

frappe.ui.form.on("QR Item By UOM", {
	refresh(frm) {
        frm.set_df_property('custom_qr_link', 'options', `<div style="text-align: center;">
            <img src="https://quickchart.io/qr?text=${encodeURIComponent(frm.doc.doctype +";" +frm.doc.name)}" 
                 alt="QR Code" 
                 style="max-width: 150px; max-height: 150px;">
         </div>`);
	},
});
