frappe.ui.form.on("Shift Change Report", {
	refresh(frm) {
        if(frm.doc.docstatus == 0){
            if(frm.doc.docstatus == 0){
                frm.add_custom_button(__('Quét QRcode'), function() {
                    frm.events.open_barcode_scanner(frm);
                });
                //khoi tao Employee
                if(!frm.doc.handover_employee){
                    frappe.call({
                        method: 'frappe.client.get_value',
                        args: {
                            doctype: 'Employee',
                            filters: { user_id: frappe.session.user },
                            fieldname: ['name']
                        },
                        callback: function(r) {
                            if (r.message) {
                                frm.set_value('handover_employee', r.message.name);
                            }
                        }
                    });
                }
            }
        }
	},
    onload: async function(frm) {
        if (frm.fields_dict.custom_btn && frm.doc.docstatus == 0) {
            let $buttons = $(`
                <div style="text-align: center; margin-top: 10px;">
                    <button id="btn1" class="btn btn-primary" style="margin-right: 20px;">Quét Qrcode</button>
                    <button id="btn2" class="btn btn-success">Hoàn thành</button>
                </div>
            `);
    
            // Thêm nút vào trường custom_btn
            frm.fields_dict.custom_btn.$wrapper.html($buttons);
    
            // Thêm sự kiện click cho Button 1
            $('#btn1').on('click', function() {
                frm.events.open_barcode_scanner(frm);
            });
    
            // Thêm sự kiện click cho Button 2 (Hoàn thành)
            $('#btn2').on('click', async function() {
                try {
                    if (frm.is_dirty()) {
                        await frm.save();
                    } 
                    await frappe.call({
                        method: "submit_doc_type",
                        args: {
                            doc_type: frm.doc.doctype,
                            name: frm.doc.name,      
                        },
                        callback: function (r) {
                            if (!r.exc) {
                                frappe.msgprint(__('Document has been successfully submitted.'));
                                frm.reload_doc(); 
                            }
                        },
                    });
                } catch (err) {
                    frappe.msgprint(__('Error: ') + err.message);
                }
            });
        } 
    },
    open_barcode_scanner(frm) {
        new frappe.ui.Scanner({
            dialog: true,
            multiple: false, 
            on_scan(data) {
                frm.events.scan_qr_code(frm, data.decodedText);
            }
        });
    },
    async scan_qr_code(frm, qrcodeScan) {
        let [qrcodeDoctype, qrcodeItem] = qrcodeScan.split(';');
        if (qrcodeDoctype === 'Employee') {
            if(!frm.doc.handover_employee){
                frm.set_value('handover_employee', qrcodeItem);
            }else{
                frm.set_value('receiving_staff', qrcodeItem);
            }
        }else if(qrcodeDoctype === 'Item'){
            var item = await get_data_from_doctype('Item', qrcodeItem);
            let found = frm.doc.shift_change_item.some(i => i.item_code === item_data.item_code);
            if (found) {
                frappe.msgprint({
                    title: __('Error'),
                    indicator: 'red',
                    message: __('Mã {0} đã nằm trong danh sách.', [item_data.item_code])
                });
                return;
            }
            if(item){
                frm.add_child("shift_change_item", {
                    item_name: item.item_name,
                    uom: item.stock_uom,
                    qty: 1,
                    item_code: item.item_code
                });
                frm.refresh_field("shift_change_item");
            }
        }else if(qrcodeDoctype === 'Shift Type'){
            frm.set_value('shift', qrcodeItem);
        }
    },
});
async function get_data_from_doctype(doctype, Id) {
    return new Promise((resolve, reject) => {
        frappe.call({
            method: 'frappe.client.get',
            args: { doctype: doctype, name: Id },
            callback: function(r) {
                if (r.message) {
                    resolve(r.message);
                } else {
                    frappe.msgprint(__(doctype + ' ' + Id + ' not exist'));
                    resolve(null);
                }
            }
        });
    });
}