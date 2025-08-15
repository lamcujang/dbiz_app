// Copyright (c) 2024, lamnl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Pallet Transfer", {
	refresh(frm) {
        frm.set_df_property('items', 'cannot_add_rows', true);
        if(frm.doc.docstatus == 0){
            frm.add_custom_button(__('Scan QRcode'), function() {
                frm.events.open_barcode_scanner(frm);
            });
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
            if(!frm.doc.date_transfer){
                frm.set_value('date_transfer', frappe.datetime.get_today());
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
    
            frm.fields_dict.custom_btn.$wrapper.html($buttons);
    
            $('#btn1').on('click', function() {
                frm.events.open_barcode_scanner(frm);
            });
    
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
        if (qrcodeDoctype === 'Pallet') {
            if(!frm.doc.pallet_from){
                frm.set_value('pallet_from', qrcodeItem);
            }else{
                frm.set_value('pallet_to', qrcodeItem);
            }
        }else if(qrcodeDoctype === 'Serial No'){
            var serialNo = get_data_from_doctype('Serial No', qrcodeItem);
            if(!frm.doc.pallet_from){
                frappe.msgprint(__('Please scan Pallet first'));
                return;
            }
            if(serialNo.pallet != frm.doc.pallet_from){
                frappe.msgprint(__('Serial No not belong to Pallet From'));
                return;
            }
            if(serialNo){
                frm.add_child("items", {
                    serial_no: serialNo.name,
                    item_name: serialNo.item_name,
                    warehouse: serialNo.warehouse,
                    pallet: serialNo.pallet,
                    item_code: serialNo.item
                });
                frm.refresh_field("items");
            }
        }
        else if(qrcodeDoctype === 'Batch'){
            var batch = get_data_from_doctype('Batch', qrcodeItem);
            if(!frm.doc.pallet_from){
                frappe.msgprint(__('Please scan Pallet first'));
                return;
            }
            if(batch.pallet != frm.doc.pallet_from){
                frappe.msgprint(__('Serial No not belong to Pallet From'));
                return;
            }
            if(batch){
                let child = frappe.model.add_child(frm.doc, 'items');
                child.batch_no = batch.name;
                child.item_name = batch.item_name;
                // child.warehouse = batch.warehouse;
                child.pallet = batch.pallet;
                child.item_code = batch.item;
                var model = {
                    'item_code': batch.item,
                    'warehouse': null,
                    'posting_date': null,
                    'posting_time': null,
                    'batch_no': batch.name,
                    'ignore_voucher_nos': null,
                    'for_stock_levels': '0',
                };
                await frappe.call({
                    method: "erpnext.stock.doctype.batch.batch.get_avilable_batch_custom",
                    args: {
                        data:model
                    },
                    callback: async function(r) {
                        if (r.message) {
                            child.s_warehouse = r.message[0].warehouse;
                        }else{
                        }
                    }
                });
                frm.refresh_field("items");
            }
        }
        else if(qrcodeDoctype === 'Employee'){
            var employee = get_data_from_doctype('Employee', qrcodeItem);
            if(employee){
                frm.set_value('employee', employee.name);
            }
        }
    },
    pallet_from: async function(frm) {
        frappe.model.clear_table(frm.doc, 'items');
        frm.refresh_field("items");
        if(frm.doc.pallet_from){
            frappe.call({
                method: "dbiz_app.dbiz_app.doctype.pallet.pallet.get_batch_no_by_pallet",
                args: {
                    pallet: frm.doc.pallet_from
                },
                callback: function(r) {
                    if (r.message) {
                        r.message.forEach(item => {

                            frm.add_child("items", {
                                batch_no: item.name,
                                item_name: item.item_name,
                                warehouse: item.warehouse,
                                pallet: frm.doc.pallet_from,
                                item_code: item.item
                            });
                        });
                        frm.refresh_field("items");
                    }
                }
            });
        }
    }
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