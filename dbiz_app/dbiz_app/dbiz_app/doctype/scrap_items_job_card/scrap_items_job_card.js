frappe.ui.form.on('Scrap Items Job Card', {
    refresh: async function(frm){
        frm.clear_custom_buttons();
        addButtonAndQR(frm);
        if(frm.doc.docstatus === 0){
            setEmployeeFromCurrentUser(frm, 'employee');
        
            frm.set_query('item_code', function(){
                return {
                    filters: [
                        ['item_group', '=', 'PHELIEU']
                    ]
                }
            });
            frm.set_query('scrap_type', function(){
                return {
                    filters: [
                        ['item_group', '=', 'LOAIPHE']
                    ]
                }
            });
            frm.set_query('workstation', function(){
                return {
                    filters: [
                        ['workstation_type', 'not in', ['XEBTPTRON','LOIBTPTHOI','TRUCIN']]
                    ]
                }
            });
            if(frm.doc.transfer_type){
                frm.events.transfer_type(frm);
            }
        }
    },
    transfer_type: async function(frm){
        frm.set_df_property('scrap_warehouse', 'reqd', 1);
        if(frm.doc.transfer_type === 'SCRAP_IMPORT'){
            frm.set_df_property('workstation', 'reqd', 1);
            frm.set_df_property('job_card', 'reqd', 1);
            frm.set_df_property('shift', 'reqd', 1);
            frm.set_df_property('employee', 'reqd', 1);
            frm.set_df_property('workstation', 'hidden', 0);
            frm.set_df_property('job_card', 'hidden', 0);
            frm.set_df_property('shift', 'hidden', 0);
        }else if(frm.doc.transfer_type === 'SCRAP_EXPORT'){
            frm.set_df_property('workstation', 'hidden', 1);
            frm.set_df_property('job_card', 'hidden', 1);
            frm.set_df_property('shift', 'hidden', 1);
            frm.set_df_property('workstation', 'reqd', 0);
            frm.set_df_property('job_card', 'reqd', 0);
            frm.set_df_property('shift', 'reqd', 0);
            frm.set_df_property('employee', 'reqd', 0);
        }
    },
    workstation: async function(frm){
        if(frm.doc.workstation){
            const itemDataFilter = await frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Operation Job Card',
                    filters: [
                        ['workstation', '=', frm.doc.workstation],
                        ['docstatus', '=', 1]
                    ],
                    fields: ['name', 'job_card_name','employee','shift'],
                    order_by: 'creation desc', 
                }
            });

            let JobCardList =  itemDataFilter.message;
            let jobCardArray = JobCardList.map(jobCard => jobCard.job_card_name);
            await setQueryJobCardFromWorkstation(frm, jobCardArray);

            if (itemDataFilter.message.length > 0) {
                frm.set_value('job_card', itemDataFilter.message[0].job_card_name);
                frm.set_value('employee', itemDataFilter.message[0].employee);
                frm.set_value('shift', itemDataFilter.message[0].shift);
            }
        }
    },
    onload: async function(frm) {
    },
    async on_submit(frm) {
        //await makeSEAndJC(frm);
    },
    job_card: async function(frm){
        if(frm.doc.job_card){
            const jobcard_data = await get_data_from_doctype('Job Card', frm.doc.job_card);
            // if(jobcard_data.shift) frm.set_value('shift', jobcard_data.shift);
            // const bom_data = await get_data_from_doctype('BOM', jobcard_data.bom_no);
            // if(bom_data.scrap_items){
            //     const scrap_item_code_arr = bom_data.scrap_items.map(item => item.item_code);
            //     frm.set_query('item_code', function(){
            //         return {
            //             filters: [
            //                 ['item_code', 'in', scrap_item_code_arr]
            //             ]
            //         }
            //     });
            //     frm.set_value('item_code', scrap_item_code_arr[0]);
            //     frm.set_value('stock_qty', bom_data.scrap_items[0].stock_qty);
            //     frm.set_value('stock_uom', bom_data.scrap_items[0].stock_uom);
            // }else{
            //     frm.set_query('item_code', function(){
            //         return {
            //             filters: [
            //                 ['item_group', '=', 'PHELIEU']
            //             ]
            //         }
            //     });
            // }
            frm.set_query('item_code', function(){
                return {
                    filters: [
                        ['item_group', '=', 'PHELIEU']
                    ]
                }
            });
        }
    },
    operation: async function(frm){
        if(frm.doc.operation){
            const operation_data = await get_data_from_doctype('Operation', frm.doc.operation);
            frm.set_value('scrap_warehouse', operation_data.scrap_warehouse);
            
        }
    },
    
    open_barcode_scanner(frm) {
        new frappe.ui.Scanner({
            dialog: true,
            multiple: false, 
            on_scan(data) {
                scan_qr_code(frm, data.decodedText);
            }
        });
    },
});

async function scan_qr_code(frm, qrcodeScan){
    let [qrcodeDoctype, qrcodeItem] = await qrcodeScan.split(';');
    console.log([qrcodeDoctype, qrcodeItem]);
    if (qrcodeDoctype === 'Item') {
        const item_data = await get_data_from_doctype(qrcodeDoctype, qrcodeItem);
        frm.set_value('item_code', item_data.item_code);
        frm.set_value('item_name', item_data.item_name);
        frm.set_value('stock_qty', 1);
        frm.set_value('stock_uom', item_data.stock_uom);
    }
    else if(qrcodeDoctype === 'Job Card') {
        frm.set_value('job_card', qrcodeItem);
        // const job_card_data = await get_data_from_doctype(qrcodeDoctype, qrcodeItem);
        // frm.set_value('workstation',job_card_data.workstation);
        // frm.set_value('shift',job_card_data.shift);
    }else if(qrcodeDoctype === 'Workstation') {
        frm.set_value('workstation', qrcodeItem);
    }else if(qrcodeDoctype === 'Employee') {
        frm.set_value('employee', qrcodeItem);
    }else if(qrcodeDoctype === 'Scrap Items Job Card'){
        const itemData = await get_data_from_doctype(qrcodeDoctype, qrcodeItem);
        if(itemData.transfer_type !== 'SCRAP_IMPORT'){
            frappe.msgprint('Chỉ được quét mã QR của phiếu nhập phế liệu!');
        }else{
            frm.set_value('scrap_warehouse',itemData.scrap_warehouse);
            frm.set_value('scrap_type',itemData.scrap_type);
            frm.set_value('item_code',itemData.item_code);
            frm.set_value('item_name',itemData.item_name);
            frm.set_value('stock_qty',itemData.stock_qty);
            frm.set_value('stock_uom',itemData.stock_uom);
            frm.set_value('transfer_type','SCRAP_EXPORT');
            frm.set_value('link_scrap_job_card',itemData.name);
        }
    }
}


async function setQueryJobCardFromWorkstation(frm, jobCards){
    frm.set_query('job_card', function() {
        return {
            filters: [
                ['name', 'in', jobCards]
            ]
        };
    });
}

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

function addButtonAndQR(frm){
    if (frm.fields_dict.custom_btn && frm.doc.docstatus == 0) {
        let $buttons = $(`
            <div class="button-container" style="
                margin-top:20px;
                margin-bottom: 35px;
              display: flex; 
              justify-content: center; 
              gap: 16px; ">
              
              <button id="btn1" style="
                padding: 10px 20px; 
                font-size: 13px; 
                font-weight: 500; 
                color: #fff; 
                background-color: #8E8E8E; 
                border: none;
                border-radius: 8px;
                width: 135px;
                height: 45px;">
                Quét QR
              </button>
            
              <button id="btn2" style="
                padding: 10px 20px; 
                font-size: 13px; 
                color: #fff; 
                background-color: #2B8320; 
                border: none; 
                border-radius: 8px;
                width: 135px;
                height: 45px;"> 
                Hoàn thành
              </button>
            </div>`);

        frm.fields_dict.custom_btn.$wrapper.html($buttons);
        $('#btn1').on('click', function() {
            if(frm.doc.docstatus!==1){
                frm.events.open_barcode_scanner(frm);
            }else{
                frappe.msgprint(`Đã hoàn thành!
                Vui lòng tạo mới!`);
            }
            
        });

        $('#btn2').on('click', async function() {
            try {
                if(frm.doc.docstatus!==1){
                    
                    if (frm.is_dirty()) {
                        await frm.save();
                    } 
                    await frappe.show_alert({
                        message: __('Đang xử lý. Vui lòng chờ!'),
                        indicator: 'orange'
                    });
                    await frappe.call({
                        method: "submit_doc_type",
                        args: {
                            doc_type: frm.doc.doctype,
                            name: frm.doc.name,      
                        },
                        callback: function (r) {
                            if (r.exc) {
                                frappe.msgprint(__('Lỗi khi lưu: ') + r.exc);
                            } else {
                                frappe.show_alert({
                                    message: __('Đã hoàn thành!'),
                                    indicator: 'green'
                                });
                                frm.reload_doc();
                            }
                        },
                    });
                }else{
                    frappe.msgprint(`Đã hoàn thành!
                    Vui lòng tạo mới!`);
                }
            } catch (err) {
                frappe.msgprint(__('Lỗi: ') + err.message);
            }
        });
    }else if(frm.doc.docstatus ===1){
        if(frm.doc.transfer_type === 'SCRAP_IMPORT'){
            frm.set_df_property('custom_btn', 'options', `<div style="text-align: center;">
                <img src="https://quickchart.io/qr?text=${encodeURIComponent(frm.doc.doctype +";" +frm.doc.name)}" 
                    alt="QR Code" 
                    style="max-width: 150px; max-height: 150px;">
            </div>`);
        }
    }
}
function setEmployeeFromCurrentUser(frm, employeeField) {
    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Employee",
            filters: { "user_id": frappe.session.user },
            fields: ["name"]
        },
        callback: function(response) {
            if (response.message && response.message.length > 0) {
                let employee = response.message[0].name;
                frm.set_value(employeeField, employee);
                frm.refresh_field(employeeField);
            }
        }
    });
}

