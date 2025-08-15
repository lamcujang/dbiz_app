frappe.ui.form.on('Stock Transfer Job Card', {
    refresh: function (frm) {
        addButtonAndQR(frm);
        setEmployeeFromCurrentUser(frm, 'employee');
        if(!frm.doc.transfer_time){
            frm.set_value('transfer_time', frappe.datetime.now_datetime());
        }
        if(!frm.doc.job_card){
		    setQueryJobCard(frm);
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
    transfer_type: async function(frm){
        const item_data = await get_data_from_doctype('Stock Transfer Job Card Type', frm.doc.transfer_type);
        console.log(item_data);
        frm.doc.target_warehouse = item_data.target_warehouse;
        frm.doc.source_warehouse = item_data.source_warehouse;
        frm.refresh_field('target_warehouse');
        frm.refresh_field('source_warehouse');
        setQueryJobCard(frm);
        
    },
    job_card: async function(frm){
        if(frm.doc.job_card){
            if(!validate_job_card(frm)){
                return;
            }
            frappe.model.clear_table(frm.doc, 'items');
            const jobcard_data = await get_data_from_doctype('Job Card', frm.doc.job_card);
            if(!frm.doc.transfer_type){
                frappe.msgprint("Vui lòng chọn loại chuyển kho");
            }else{
                if(frm.doc.transfer_type == 'CKNVL' && jobcard_data.operation =='CONGDOANTRON'){
                    if(jobcard_data.use_funnel == 'USE_SHARE'){
                        jobcard_data.items.forEach(item => {
                            let child = frappe.model.add_child(frm.doc, 'items');
                            child.item_code = item.item_code;
                            child.item_name = item.item_name;
                            child.uom = item.uom;
                            child.qty = item.convert_qty;
                            child.convert_qty = item.required_qty;
                            child.stock_uom = item.stock_uom;
                            child.conversion_factor = item.conversion_factor;
                            child.source_warehouse = item.source_warehouse
                        });
                        frm.refresh_field('items');
                    }else{
                        // Gộp các mảng lại
                        const all_items = [
                            ...(jobcard_data.items || []),
                            ...(jobcard_data.funnel_b_data || []),
                            ...(jobcard_data.funnel_c_data || [])
                        ];

                        // Gom nhóm và cộng dồn số lượng
                        const grouped = {};
                        all_items.forEach(item => {
                            if(!item.item_code) return;
                            if(!grouped[item.item_code]) {
                                grouped[item.item_code] = {
                                    ...item,
                                    bag_qty_main: Number(item.bag_qty_main) || 0,
                                    kg_qty_main: Number(item.kg_qty_main) || 0,
                                    bag_qty_sec: Number(item.bag_qty_sec) || 0,
                                    kg_qty_sec: Number(item.kg_qty_sec) || 0,
                                    conversion_factor: Number(item.conversion_factor) || 0
                                };
                            } else {
                                grouped[item.item_code].bag_qty_main += Number(item.bag_qty_main) || 0;
                                grouped[item.item_code].kg_qty_main += Number(item.kg_qty_main) || 0;
                                grouped[item.item_code].bag_qty_sec += Number(item.bag_qty_sec) || 0;
                                grouped[item.item_code].kg_qty_sec += Number(item.kg_qty_sec) || 0;
                            }
                        });

                        // Xóa bảng cũ
                        frappe.model.clear_table(frm.doc, 'items');

                        // Thêm từng mặt hàng đã cộng dồn vào bảng
                        Object.values(grouped).forEach(item => {
                            let child = frappe.model.add_child(frm.doc, 'items');
                            const total_qty = Number(item.bag_qty_main) || 0 + Number(item.bag_qty_sec) || 0;
                            const total_convert_qty = Number(item.kg_qty_main) || 0 + Number(item.kg_qty_sec) || 0;
                            child.item_code = item.item_code;
                            child.item_name = item.item_name;
                            child.uom = item.uom;
                            child.qty = total_qty == 0 ? total_convert_qty : total_qty;
                            child.convert_qty = total_convert_qty;
                            child.stock_uom = item.stock_uom;
                            child.conversion_factor = item.conversion_factor == 0 ? 1 : item.conversion_factor;
                        });
                        frm.refresh_field('items');
                    }
                }else if(frm.doc.transfer_type == 'CKXEBTP' || frm.doc.transfer_type == 'CKCUONMANG'){
                    await frappe.call({
        				method: "dbiz_app.dbiz_app.doctype.stock_transfer_job_card.stock_transfer_job_card.make_stock_transfer_job_card",
        				args: {
        					job_card: jobcard_data.name,
        				},
        				callback: async function (r) {
        					if (r.message) {
        						r.message.forEach(item => {
        						    let found = frm.doc.items.some(item => item.batch_no === item.batch_no);
                                    if (!found) {
                                        let child = frappe.model.add_child(frm.doc, 'items');
                                        child.item_code = item.item_code;
                                        child.item_name = item.item_name;
                                        child.uom = item.uom;
                                        child.qty = item.qty;
                                        child.source_warehouse = item.warehouse;
                                        child.batch_no = item.batch_no;  
                                    }
                                });
                                frm.refresh_field('items');
        					}
        				},
        			});
                    
                }
            }
        }
        
    },
    before_save: async function(frm){
        frm.doc.items.forEach(item => {
            item.source_warehouse = frm.doc.source_warehouse
        });
    },
    on_submit: async function(frm){
        frm.doc.items.forEach(item => {
            item.source_warehouse = frm.doc.source_warehouse
        });
    }
});
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

        // Thêm nút vào trường custom_btn #315C2B
        frm.fields_dict.custom_btn.$wrapper.html($buttons);

        // Thêm sự kiện click cho Button 1
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
                frappe.msgprint(__('Error: ') + err.message);
            }
        });
    }else {
        frm.fields_dict.custom_btn.$wrapper.html('');
    }
}
async function scan_qr_code(frm, qrcodeScan){
    frm.doc.items = await frm.doc.items.filter(item => item.item_code);
    let [qrcodeDoctype, qrcodeItem] =await qrcodeScan.split(';');
    if (qrcodeDoctype === 'Item') {
        const item_data = await get_data_from_doctype(qrcodeDoctype, qrcodeItem);
        let found = await frm.doc.items.some(item => item.item_code === item_data.name);

        if (found) {
            await frappe.msgprint({
                title: __('Error'),
                indicator: 'red',
                message: __('Mã nvl/btp {0} đã nằm trong chi tiết: ', [item_data.name])
            });
            return;
        }
        const item = await frm.add_child('items');
        item.item_code = item_data.item_code;
        item.item_name = item_data.item_name;
        item.t_warehouse = frm.doc.target_warehouse;
        item.qty = 1;
        item.uom = item_data.uom;
        await frm.refresh_field('items');
        
    }
    else if(qrcodeDoctype === 'Job Card') {
        frm.set_value('job_card', qrcodeItem);
    }
    else if(qrcodeDoctype === 'Batch') {
        const batch_data = await get_data_from_doctype(qrcodeDoctype, qrcodeItem);
        let found = frm.doc.items.some(item => item.batch_no === batch_data.name);

        if (found) {
            frappe.msgprint({
                title: __('Error'),
                indicator: 'red',
                message: __('Mã lô {0} đã nằm trong chi tiết: ', [batch_data.name])
            });
            return;
        }
        let child = frappe.model.add_child(frm.doc, 'items');
        child.item_code = batch_data.item;
        child.item_name = batch_data.item_name;
        child.uom = batch_data.stock_uom;
        child.qty = batch_data.batch_qty;
        child.batch_no = batch_data.name;
        await frappe.call({
            method: "dbiz_app.dbiz_app.doctype.stock_transfer_job_card.stock_transfer_job_card.get_available_batch_custom",
			args: {
				batch_no: qrcodeItem,
			},
            callback: async function(r) {
                if (r.message) {
                    child.source_warehouse=r.message[0].warehouse;
                }else{
                }
            }
        });
        frm.refresh_field('items');
    }
    else if(qrcodeDoctype === 'Pallet') {
        frappe.call({
            method: "dbiz_app.dbiz_app.doctype.pallet.pallet.get_batch_no_by_pallet",
            args: {
                pallet: qrcodeItem
            },
            callback: function(r) {
                if (r.message) {
                    r.message.forEach(item => {
                        let child = frappe.model.add_child(frm.doc, 'items');
                        child.item_code = item.item;
                        child.item_name = item.item_name;
                        child.uom = item.stock_uom;
                        child.stock_uom = item.stock_uom;
                        child.qty = item.batch_qty;
                        child.batch_no = item.name;
                        child.source_warehouse = item.warehouse;
                    });
                    frm.refresh_field("items");
                }
            }
        });
    }
    else if(qrcodeDoctype === 'Serial No') {
        if(frm.doc.transfer_type == 'CHUYENHANGGIACONG'){
            const serial_data = await get_data_from_doctype(qrcodeDoctype, qrcodeItem);
        
            let found = frm.doc.items.some(i => i.serial_no === serial_data.name);
    
            if (found) {
                frappe.msgprint({
                    title: __('Error'),
                    indicator: 'red',
                    message: __('Mã túi {0} đã nằm trong phiếu này.', [item.name])
                });
                return;
            }
    
            // Đợi kết quả từ get_data_from_doctype với await
            let itemData = await get_data_from_doctype("Item", serial_data.item_code);
            let child = frappe.model.add_child(frm.doc, 'items');
            child.item_code = itemData.item_code;
            child.item_name = itemData.item_name;
            child.uom = serial_data.stock_uom;
            child.qty = serial_data.quantity;
            child.serial_no = serial_data.name;
            child.source_warehouse = serial_data.warehouse;
            frm.refresh_field('items');
        }else{
            frappe.msgprint({
                    title: __('Error'),
                    indicator: 'red',
                    message: __('Chuyển kho loại này không thể quét mã Serial')
                });
        }
    }
    else if(qrcodeDoctype === 'Warehouse') {
        frm.set_value('target_warehouse', qrcodeItem);
    }else if(qrcodeDoctype === 'Employee') {
        frm.set_value('employee', qrcodeItem);
    }

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

function setQueryJobCard(frm){
    if(frm.doc.transfer_type == 'CKNVL'){
        frm.set_query('job_card', function () {
    		return {
                filters: [
                    ['operation', '=', 'CONGDOANTRON'],
                    ['docstatus', '=', 1],
                    // ['posting_date', '>=', frappe.datetime.nowdate()], 
                    // ['posting_date', '<', frappe.datetime.add_days(frappe.datetime.nowdate(), 1)]
                ],
                order_by: 'creation DESC'
    		};
    	});
    }else if(frm.doc.transfer_type == 'CKXEBTP' ){
        frm.set_query('job_card', function () {
    		return {
    			filters: [
                    ['operation', '=', 'CONGDOANTRON'],
                    ['docstatus', '=', 1],
                    // ['posting_date', '>=', frappe.datetime.nowdate()], 
                    // ['posting_date', '<', frappe.datetime.add_days(frappe.datetime.nowdate(), 1)]
                ],
                order_by: 'creation DESC'
    		};
    	});
    }else if(frm.doc.transfer_type == 'CKCUONMANG'){
        const now_date = frappe.datetime.now_datetime();
        frm.set_query('job_card', function () {
    		return {
    			filters: [
                    ['operation', '=', 'CONGDOANTTHOI'],
                    ['docstatus', '=', 1],
                    // ['posting_date', '>=', frappe.datetime.nowdate()], 
                    // ['posting_date', '<', frappe.datetime.add_days(frappe.datetime.nowdate(), 1)]
                ],
                order_by: 'creation DESC'
    		};
    	});
    }
	
}
async function validate_job_card(frm){
    const jobcard_data = await get_data_from_doctype('Job Card', frm.doc.job_card);
    if(jobcard_data.docstatus != 1){
        frappe.msgprint("Lệnh sản xuất hằng ngày chưa được phê duyệt");
        return false;
    }
    return true;
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

frappe.ui.form.on('Stock Transfer Job Card Items', {
	refresh(frm) {
		// your code here
	},
    item_code: async function(frm){
        const item_data = await get_data_from_doctype('Item', frm.doc.item_code);
        frm.doc.item_name = item_data.item_name;
        frm.doc.uom = item_data.sencondary_uom;
        frm.doc.stock_uom = item_data.stock_uom;
        frm.refresh_field('item_name');
    }
})
