let isStarted = false;
frappe.ui.form.on('Operation Job Card', {
    refresh: async function (frm) {
        frm.count_camera = 0;
        addButtonAndQR(frm);
        setEmployeeFromCurrentUser(frm, 'employee');
        // const jobcard_data = await get_data_from_doctype("Job Card", frm.doc.job_card_name);
        //frm.set_df_property('boxs', 'cannot_add_rows', true);
        if(!frm.doc.amended_from && frm.doc.job_card_name && frm.doc.job_card_operation_name ==='TRON'){
            // frm.add_custom_button(
			// 	__("Material Request"),
			// 	() => {
			// 		frm.trigger("make_material_request");
			// 	},
			// 	__("Create")
			// );
            frm.set_df_property('items', 'cannot_add_rows', true);
        }
        if(!frm.doc.source_warehouse && frm.doc.job_card_name){
            const warehouse  = await default_source_warehouse(frm);
            
            frm.set_value('source_warehouse', warehouse);
        }
        if(!frm.doc.start_time ){
            const now_date = frappe.datetime.now_datetime();
            frm.set_value('start_time', now_date);
        }
        //Cái này cứ save là counted_qty cho Trộn về 0
//         if(frm.doc.job_card_operation_name && frm.doc.docstatus ==0){
//             frm.events.job_card_operation_name(frm);
//         }
//         if(frm.doc.job_card_name && frm.doc.docstatus ==0){
//             frm.events.job_card_operation_name(frm);
//         }
		if(!frm.doc.job_card_operation_name){
		    setQueryJobCard(frm, '');
		}
        if(frm.doc.job_card_operation_name ==="DONGTHUNG" || frm.doc.job_card_operation_name ==="GCHOANTHIEN"){
            // const wo_data = await get_data_from_doctype("Work Order", jobcard_data.work_order);
            frm.fields_dict['boxs'].grid.get_field('item_code').get_query = function(doc, cdt, cdn) {
                return {
                    filters: {
                        item_code: ["in", jobcard_data.production_item],
                    }
                };
            };
            frm.fields_dict['boxs'].grid.get_field('pallet').get_query = function(doc, cdt, cdn) {
                return {
                    filters: {
                        job_card: ["in", frm.doc.job_card_name]
                    }
                };
            };
        }
        if(frm.doc.amended_from){
            frm.set_df_property('items', 'readonly', false);
            frm.set_df_property('employee', 'readonly', false);
            frm.set_df_property('shift', 'readonly', false);
            frm.set_df_property('workstation', 'readonly', false);
            frm.set_df_property('job_card_name', 'readonly', true);
            frm.set_df_property('job_card_operation_name', 'readonly', true);
            frm.set_df_property('mortar', 'readonly', true);
            frm.refresh_field('items');
            frm.refresh_field('employee');
            frm.refresh_field('shift');
            frm.refresh_field('workstation');
            frm.refresh_field('job_card_name');
            frm.refresh_field('job_card_operation_name');
            frm.refresh_field('mortar');
        }
    },
    work_order: async function(frm){
        if(frm.doc.work_order){
            
        }
    },
    job_card_name: async function(frm){
        if(frm.doc.job_card_name && frm.doc.job_card_name !="" ){
            const jobcard_data = await get_data_from_doctype("Job Card", frm.doc.job_card_name);
            const val_daily_plan = await validate_daily_plan(frm,jobcard_data);
            // if(!val_daily_plan)
            //     return
            default_workstation(frm, jobcard_data);
            frm.set_value('production_item', jobcard_data.production_item);
            if(!frm.doc.work_order){
                frm.set_value('work_order', jobcard_data.work_order);
            }
            frm.set_query('job_card_operation_name', function () {
                return {
                    filters: [
                        ['name', 'in', get_operations_from_job_card(frm.doc.job_card_name)]
                    ]
                };
            });
            if(!frm.doc.source_warehouse ){
                const warehouse  = await default_source_warehouse(frm);
                
                frm.set_value('source_warehouse', warehouse);
            }
            if(frm.doc.job_card_operation_name){
                if(frm.doc.job_card_operation_name ==='TRON'){
                    frappe.model.clear_table(frm.doc, 'items');
                    const { rows, volume_need_mixed, mix_batch_qty_main, mix_batch_qty_sec, workstation, prefix } = get_funnel_config(jobcard_data, jobcard_data.use_funnel=== 'USE_SHARE' ? 'A' : frm.doc.funnel);
                    rows.forEach(async item => {
                        let child = frappe.model.add_child(frm.doc, 'items');
                        child.item_code = item.item_code;
                        child.item_name = item.item_name;
                        child.uom = item.uom;
                        child.qty = item.bag_qty_main ? item.bag_qty_main : item.kg_qty_main;
                        child.stock_uom = item.stock_uom;
                        child.conversion_factor = item.conversion_factor;
                        if( item.conversion_factor == 0 ){
                            await frappe.call({
                                method: "dbiz_app.dbiz_app.doctype.operation_job_card.operation_job_card.get_conversion_factor",
                                args: {
                                    item_code: item.item_code,
                                    uom: item.uom
                                },
                                callback: function (r) {
                                    child.conversion_factor = r.message || 0;
                                }
                            });
                        }
                    });
                    frm.refresh_field('items');
                }else if(['DONGTHUNG', 'GCHOANTHIEN'].includes(frm.doc.job_card_operation_name)){
                    frm.fields_dict['boxs'].grid.get_field('item_code').get_query = function(doc, cdt, cdn) {
                        return {
                            filters: {
                                item_code: ["in", jobcard_data.production_item],
                            }
                        };
                    };
                    frm.fields_dict['boxs'].grid.get_field('pallet').get_query = function(doc, cdt, cdn) {
                        return {
                            filters: {
                                job_card: ["in", frm.doc.job_card_name]
                            }
                        };
                    };
                    let new_row = frm.add_child("boxs");
                    const item_data = await get_data_from_doctype("Item", jobcard_data.production_item);
                    new_row.item_code = jobcard_data.production_item;
                    new_row.uom = 'Kg';
                    new_row.stock_uom = item_data.stock_uom;
                    new_row.qty = 1;
                    new_row.second_qty = 1;
                    
                    frm.refresh_field("boxs");
                    
                }else if(frm.doc.job_card_operation_name ==="NKBTPC"){
                    if(frm.doc.job_card_name){
                        frm.fields_dict['bags'].grid.get_field('item_code').get_query = function(doc, cdt, cdn) {
                            return {
                                filters: {
                                    item_code: ["in", jobcard_data.final_item]
                                }
                            };
                        };
                        let new_row = frm.add_child("bags");
                        const item_data = await get_data_from_doctype("Item", jobcard_data.production_item);
                        new_row.item_code = jobcard_data.production_item;
                        new_row.uom = 'Kg';
                        new_row.stock_uom = item_data.stock_uom;
                        new_row.qty = 1;
                        new_row.second_qty = 1;
                        
                        frm.refresh_field("bags");
                    }
                } 
                if(['XA', 'NKCUONMANG', 'DONGTHUNG', 'GCHOANTHIEN'].includes(frm.doc.job_card_operation_name)){
                    const type_op_jc = frm.doc.job_card_operation_name === "XA" ? "TRON" 
                                    : frm.doc.job_card_operation_name ==='NKCUONMANG' ? 'THOI' 
                                    : frm.doc.job_card_operation_name ==='DONGTHUNG' ? 'CAT' 
                                    : frm.doc.job_card_operation_name ==='GCHOANTHIEN' ? 'CAT' : 'CAT';
                    const pre_step_op_jc = await frappe.call({
                        method: "dbiz_app.dbiz_app.doctype.operation_job_card.operation_job_card.get_pre_step_op_jc",
                        args: {
                            job_card_name: frm.doc.job_card_name,
                            operation_name: type_op_jc
                        }
                    });
                    if(pre_step_op_jc.message){
                        const pre_step_op_jc_data = await get_data_from_doctype("Operation Job Card", pre_step_op_jc.message);
                        frm.set_value('opeartion_job_card_previous_step', pre_step_op_jc_data.name);
                        frm.set_value('employee', pre_step_op_jc_data.employee);
                        frm.set_value('shift', pre_step_op_jc_data.shift);
                        frm.set_value('workstation', pre_step_op_jc_data.workstation);
                    }
                }
            }
        }
    },
    job_card_operation_name: async function(frm){
        addButtonAndQR(frm);
        if(frm.doc.job_card_operation_name){
            clearDetail(frm);
            const operation_data = await get_data_from_doctype("Operation", frm.doc.job_card_operation_name);
            frm.set_value('operation_type', operation_data.operation_type);
            
            if(frm.doc.job_card_operation_name ==="LNVLTRON"){
                // frm.fields_dict['items'].grid.get_field('item_code').get_query = function(doc, cdt, cdn) {
                //     return {
                //         filters: {
                //             item_group: ["in", item_code]
                //         }
                //     };
                // };
            }else if(frm.doc.job_card_operation_name ==="TRON"){
				setQueryJobCard(frm, 'CONGDOANTRON');
                
            }else if(frm.doc.job_card_operation_name ==="XA"){
               frm.fields_dict['details'].grid.get_field('item_code').get_query = function(doc, cdt, cdn) {
                    return {
                        filters: {
                            workstation_type: ["in", ['XEBTPTRON']]
                        }
                    };
                };
				setQueryJobCard(frm, 'CONGDOANTRON');
            }else if(frm.doc.job_card_operation_name ==="THOI"){
				setQueryJobCard(frm, 'CONGDOANTHOI')
            }else if(frm.doc.job_card_operation_name ==="NKCUONMANG"){
                // frm.fields_dict['details'].grid.get_field('item_code').get_query = function(doc, cdt, cdn) {
                //     return {
                //         filters: {
                //             workstation_type: ["in", ['LOIBTPTHOI']]
                //         }
                //     };
                // };
				setQueryJobCard(frm, 'CONGDOANTHOI');
            }else if(frm.doc.job_card_operation_name ==="LBTPTHOI"){
				setQueryJobCard(frm, 'CONGDOANCAT');
            }else if(frm.doc.job_card_operation_name ==="CAT"){
				frm.fields_dict['items'].grid.get_field('item_code').get_query = function(doc, cdt, cdn) {
                    return {
                        filters: {
                            item_group: ["in", 'BTPTHOI']
                        }
                    };
                };
            }else if(['DONGTHUNG', 'GCHOANTHIEN'].includes(frm.doc.job_card_operation_name)){
                if(frm.doc.job_card_name){
                    const jobcard_data = await get_data_from_doctype("Job Card", frm.doc.job_card_name);
                    
                    const wo_data = await get_data_from_doctype("Work Order", jobcard_data.work_order);
                    frm.fields_dict['boxs'].grid.get_field('item_code').get_query = function(doc, cdt, cdn) {
                        return {
                            filters: {
                                item_code: ["in", jobcard_data.final_item]
                            }
                        };
                    };
                    frm.fields_dict['boxs'].grid.get_field('pallet').get_query = function(doc, cdt, cdn) {
                        return {
                            filters: {
                                job_card: ["in", frm.doc.job_card_name]
                            }
                        };
                    };
                    
                }
                
                setQueryJobCard(frm, frm.doc.job_card_operation_name == 'DONGTHUNG' ? 'CONGDOANCAT' : 'CONGDOANHOANTHIEN');
            }else if(frm.doc.job_card_operation_name ==="GCHOANTHIEN"){
                
            }else if(frm.doc.job_card_operation_name ==="NKBTPC"){
				setQueryJobCard(frm, 'CONGDOANCAT');
                if(frm.doc.job_card_name){
                    const jobcard_data = await get_data_from_doctype("Job Card", frm.doc.job_card_name);
                    
                    frm.fields_dict['bags'].grid.get_field('item_code').get_query = function(doc, cdt, cdn) {
                        return {
                            filters: {
                                item_code: ["in", jobcard_data.final_item]
                            }
                        };
                    };
                }
            }
        }
        
        if(frm.doc.job_card_name){
            frm.trigger("job_card_name");
        }
    },
    mortar: async function(frm){
        if(frm.doc.mortar){
            if(frm.doc.job_card_name){
                const jobcard_data = await get_data_from_doctype("Job Card", frm.doc.job_card_name);
                await validate_daily_plan(frm,jobcard_data);
                frappe.model.clear_table(frm.doc, 'items');
                const { rows, volume_need_mixed, mix_batch_qty_main, mix_batch_qty_sec, workstation, prefix } = get_funnel_config(jobcard_data, jobcard_data.use_funnel=== 'USE_SHARE' ? 'A' : frm.doc.funnel);
                rows.forEach(item => {
                    let child = frappe.model.add_child(frm.doc, 'items');
                    child.item_code = item.item_code;
                    child.item_name = item.item_name;
                    child.uom = item.uom;
                    child.qty = frm.doc.mortar =='MORTAR_MAIN' ? (item.bag_qty_main ? item.bag_qty_main : item.kg_qty_main) : (item.bag_qty_sec ? item.bag_qty_sec : item.kg_qty_sec);
                    child.stock_uom = item.stock_uom;
                    child.conversion_factor = item.conversion_factor;
                });
                frm.set_value('workstation', workstation);
                frm.refresh_field('items');
            }
        }
    },
    scan_button: function(frm, cdt, cdn){
        frm.events.open_barcode_scanner(frm);
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
    company: function(frm){
        frm.set_query('employee', function () {
            return {
                filters: [
                    ['company', '=', frm.doc.company],
                ]
            };
        });
    },
    re_open: function(frm){
        frm.set_value('reopen', true);
        frm.doc.docstatus = 0;
        frm.doc.status = 'Re Open';
        frm.doc.workflow_state = 'Re Open';
        frm.set_df_property('items', 'cannot_add_rows', false);
        frm.doc.items.forEach(row => {
            row.docstatus = 0;
            const gridRow = frm.fields_dict['items'].grid.grid_rows_by_docname[row.name];
            if (gridRow && typeof gridRow.toggle_editable === 'function') {
                gridRow.toggle_editable('item_code', true);
                gridRow.toggle_editable('counted_qty', true);
            }
        });
        frm.set_df_property('items', 'readonly', false);
        frm.set_df_property('employee', 'readonly', false);
        frm.set_df_property('shift', 'readonly', false);
        frm.set_df_property('workstation', 'readonly', false);
        frm.refresh_field('items');
        frm.refresh_field('employee');
        frm.refresh_field('shift');
        frm.refresh_field('workstation');
        frm.refresh_field('docstatus');
        frm.refresh_field('status');
        frm.refresh_field('workflow_state');
        frm.trigger("refresh");
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
                font-weight: 500; 
                color: #fff; 
                background-color:rgb(167, 149, 211); 
                border: none;
                border-radius: 8px;
                width: 135px;
                height: 45px;">
                Chụp ảnh
              </button>

              <button id="btn3" style="
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
        if(['XA', 'NKCUONMANG', 'DONGTHUNG', 'GCHOANTHIEN'].includes(frm.doc.job_card_operation_name)){
            $('#btn2').on('click', function() {
                    if((frm.doc.boxs.length > 0 && ['DONGTHUNG','GCHOANTHIEN'].includes(frm.doc.job_card_operation_name)) 
                        || (frm.doc.details.length > 0 && ['XA'].includes(frm.doc.job_card_operation_name))
                        || (frm.doc.semi_items.length > 0 && ['NKCUONMANG'].includes(frm.doc.job_card_operation_name))){
                        if(frm.doc.docstatus!==1){
                            open_camera_dialog(frm);
                        }else
                        {
                            frappe.msgprint(`Đã hoàn thành!
                                Vui lòng tạo mới!`);
                        }
                    } else {
                        frappe.msgprint(`Vui lòng thêm thông tin vào bảng chi tiết trước khi chụp ảnh!`);
                    }
            });
        }else{
            $('#btn2').hide();
        }

        $('#btn3').on('click', async function() {
            
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
    let [qrcodeDoctype, qrcodeItem,funnel] = qrcodeScan.split(';');
    if (qrcodeDoctype === 'Job Card Operation') {
        if(!frm.doc.amended_from){
            const jobCardOperation = await get_data_from_doctype_ignore_permission(qrcodeDoctype, qrcodeItem);
            frm.set_value('job_card_operation_name', jobCardOperation.sub_operation);
            frm.set_value('workstation', jobCardOperation.workstation);
            frm.set_value('job_card_name', jobCardOperation.parent);
        }
    } else if (qrcodeDoctype === 'Workstation') {
        const wt_data = await get_data_from_doctype(qrcodeDoctype, qrcodeItem);
        
        if(!['LOIBTPTHOI', 'XEBTPTRON', 'THOIIN'].includes(wt_data.workstation_type)){
            frm.set_value('workstation', qrcodeItem);
        }else{
            if(['XA'].includes(frm.doc.job_card_operation_name)){
                if(wt_data.status != "Off"){
                    if(frm.doc.job_card_operation_name == 'XA'){
                        frappe.msgprint("Xe đang sử dụng hoặc đang bị hỏng, vui lòng dùng xe khác");
                        
                    }else{
                        frappe.msgprint("Lõi đang sử dụng hoặc đang bị hỏng, vui lòng dùng lõi khác");
                    }
                }else{
                    let child = frappe.model.add_child(frm.doc, 'details');
                    child.item_code = wt_data.name;
                    child.item_name = wt_data.workstation_name;
                    child.uom = "Kg";
                    child.qty = 1;
                    child.weight = wt_data.workstation_weight;
                    frm.refresh_field('details');
                }
                
            }else if(['LBTPTRON','LBTPTTHOI','LBTPCAT','THOI','CAT'].includes(frm.doc.job_card_operation_name)){
                if(!wt_data.batch_no){
                    frappe.msgprint("Không có lô BTP nào");
                }else{
                    const batch_data = await get_data_from_doctype('Batch', wt_data.batch_no);
                    let child = frappe.model.add_child(frm.doc, 'items');
                    child.item_code = batch_data.item;
                    child.item_name = batch_data.item_name;
                    child.uom = batch_data.stock_uom;
                    child.stock_uom = batch_data.stock_uom;
                    child.qty = batch_data.batch_qty;
                    child.counted_qty = batch_data.batch_qty;
                    child.convert_qty = batch_data.batch_qty;
                    child.batch_no = batch_data.name;
                    child.qty = batch_data.batch_qty;
                    frm.refresh_field('details');
                }
                
            }else {
                frappe.msgprint("Công đoạn này không xử dụng máy này");
            } 
            
        }
        
    } else if (qrcodeDoctype === 'Employee') {
        frm.set_value('employee', qrcodeItem);
    } else if (qrcodeDoctype === 'Batch') {
        const batch_data = await get_data_from_doctype(qrcodeDoctype, qrcodeItem);
        if(['LBTPTRON','LBTPTHOI','LBTPCAT','THOI','CAT'].includes(frm.doc.job_card_operation_name)){
            let found = frm.doc.items.some(item => item.batch_no === batch_data.name);

            if (found) {
                frappe.msgprint({
                    title: __('Error'),
                    indicator: 'red',
                    message: __('Mã lô {0} đã nằm trong mẻ này.', [batch_data.name])
                });
                return;
            }
            if(frm.doc.job_card_name){
                const jobcard_data = await get_data_from_doctype("Job Card", frm.doc.job_card_name);
                const item_codes = (batch_data.item_finish || []).map(item => item.item_code);
                if(jobcard_data.production_item){
                    let found = batch_data.item_finish.some(item => item.item_code === jobcard_data.production_item);
            
                    if (!found) {
                        //const invalidCodes = invalidItems.map(item => item.item_code).join(", ");
                        frappe.throw(
                            __("Mã BTP không dùng để sản xuất Thành phẩm này{0}", jobcard_data.production_item)
                        );
                    }
                }
            }
            
            var itemData = await get_data_from_doctype('Item', batch_data.item);
            
            let child = frappe.model.add_child(frm.doc, 'items');
            child.item_code = itemData.item_code;
            child.item_name = itemData.item_name;
            child.stock_uom = itemData.stock_uom;
            child.uom = itemData.stock_uom;
            child.conversion_factor = 1;
            child.qty = batch_data.batch_qty;
            child.convert_qty = batch_data.batch_qty;
            child.batch_no = batch_data.name;
            child.counted_qty = batch_data.counted_qty;
            frm.refresh_field('items');
        }
    } else if (qrcodeDoctype === 'Item') {
        const itemData = await get_data_from_doctype(qrcodeDoctype, qrcodeItem);
        if(['DONGTHUNG', 'GCHOANTHIEN'].includes(frm.doc.job_card_operation_name)){
            let child = frappe.model.add_child(frm.doc, 'details');
            child.item_code = itemData.item_code;
            child.item_name = itemData.item_name;
            child.stock_uom = itemData.stock_uom;
            child.uom = 'Kg';
            child.qty = 1;
            child.second_qty = 1;
            frm.refresh_field('boxs');
        }else{
            frappe.msgprint({
                    title: __('Error'),
                    indicator: 'red',
                    message: ('Phải quét mã lô ở đây')
                });
            return;
        }
    } else if (qrcodeDoctype === 'Shift') {
        frm.set_value('shift', qrcodeItem);
    } else if(qrcodeDoctype === 'QR Item By UOM'){
        const qr_data = await get_data_from_doctype('QR Item By UOM', qrcodeItem);
        
    } else if(qrcodeDoctype === 'Job Card'){
        if(!frm.doc.amended_from){
            if(funnel) frm.set_value('funnel', funnel); else frm.set_value('funnel', 'A');
            const job_card_data = await get_data_from_doctype('Job Card', qrcodeItem);
            if(job_card_data.docstatus != 1){
                frappe.msgprint(__('Lệnh sản xuất {0} chưa được phê duyệt!',[job_card_data.name]));
                return;
            }
            frm.set_value('job_card_name', qrcodeItem);
            // frm.events.job_card_name(frm);
        }
    } else if(qrcodeDoctype === 'Work Order'){
        frm.set_value('work_order', qrcodeItem);
        let [doctype, name, operation] = qrcodeScan.split(';');
        await work_order_trigger(frm,operation);
    }
}

async function work_order_trigger(frm, operation){
    const work_order_data = await get_data_from_doctype("Work Order", frm.doc.work_order);
    await frappe.call({
        method: "dbiz_app.dbiz_app.doctype.operation_job_card.operation_job_card.get_list_job_card_from_work_order",
        args: {
            work_order: frm.doc.work_order,
            operation: operation,
        },
        callback: function (r) {
            if (r.message.length > 0) {
                if(r.message.length > 1)
                    open_job_card_popup(frm, r.message); 
                else
                    frm.set_value('job_card_name', r.message[0].name)
            }else{
                frappe.msgprint(__('Không có lệnh sản xuất hàng ngày theo lệnh này {0}.',[frm.doc.work_order]));
            }
        },
    });
    
}

window.open_job_card_popup = function(frm, job_card_list) {
    if (!job_card_list || job_card_list.length === 0) {
        frappe.msgprint(__('Không có Job Card nào để chọn.'));
        return;
    }

    let tableHTML = 
        `<table class="table table-bordered">
            <thead>
                <tr>
                    <th>Lệnh sản xuất hàng ngày</th>
                    <th>Chọn</th>
                </tr>
            </thead>
            <tbody>`;

    job_card_list.forEach(job_card => {
        tableHTML += 
            `<tr>
                <td>${job_card.name}</td>
                <td>
                    <button class="btn-select-job-card"
                            data-job-card-name="${job_card.name}" 
                            style="background-color: white; border: 0.45px solid #ddd; border-radius: 5px; padding: 6px 12px; cursor: pointer;">
                            Chọn
                    </button>
                </td>
            </tr>`;
    });

    tableHTML += `</tbody></table>`;

    let d = new frappe.ui.Dialog({
        title: 'Chọn lệnh sản xuất hằng ngày',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'job_card_list',
                options: tableHTML
            }
        ],
        size: 'large'
    });

    d.show();

    // Bắt sự kiện click ngay sau khi dialog hiển thị
    d.$wrapper.find('.btn-select-job-card').on('click', function() {
        let job_card = $(this).data('job-card-name');
        frm.set_value('job_card_name', job_card);
        d.hide(); // Đóng dialog
    });
};

function get_operations_from_job_card(job_card_name) {
    let sub_operations = [];
    if(job_card_name){
        frappe.call({
            method: 'frappe.client.get',
            async: false,
            args: {
                doctype: 'Job Card',
                name: job_card_name
            },
            callback: function (response) {
                if (response.message) {
                    sub_operations = (response.message.sub_operations || []).map(row => row.sub_operation);
                }
            }
        });
        return sub_operations;
    }else{
        let sub_operations = [];
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Operation',
                fields: ['name'], 
                filters: [
                    ['operation_type', 'in', ['Manufacture Semi-Finished Goods', 'Material Transfer For Job Card', 'Packing']]
                ],
                limit_page_length: 1000 
            },
            callback: function (response) {
                if (response.message) {
                    sub_operations = response.message.map(row => row.name);
                }
            },
            async: false 
        });
        return sub_operations;
    }
}

async function get_data_from_doctype(doctype, Id) {
    return await frappe.db.get_doc(doctype, Id).then(doc => {
        return doc;
    }).catch(err => {
        console.error(err);
        return null;
    });
}

async function get_data_from_doctype_ignore_permission(doctype, Id) {
    return new Promise((resolve, reject) => {
        frappe.call({
            method: 'get_doc_data_ignore_permissions',
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

async function default_source_warehouse(frm) {
    const jobcard_data = await get_data_from_doctype('Job Card', frm.doc.job_card_name);
    const operation_data = await get_data_from_doctype('Operation', jobcard_data.operation);
    var warehouse = '';
    if(['LBTPTRON','LBTPTHOI','LBTPCAT','TRON','THOI','CAT'].includes(frm.doc.job_card_operation_name)){
        warehouse = operation_data.raw_material_warehouse
    }else if(['XA','NKCUONMANG','DONGTHUNG','NKTP','GCHOANTHIEN','NKBTPC'].includes(frm.doc.job_card_operation_name)){
        warehouse = jobcard_data.target_warehouse
        if( !warehouse){
            warehouse = operation_data.target_warehouse
        }
    }
    return warehouse
}

async function default_workstation(frm, jobcard_data) {
    const { rows, volume_need_mixed, mix_batch_qty_main, mix_batch_qty_sec, workstation, prefix } = get_funnel_config(jobcard_data, jobcard_data.use_funnel=== 'USE_SHARE' ? 'A' : frm.doc.funnel);
    frm.set_value('workstation', workstation);
}
frappe.ui.form.on('Operation Job Card Items', {
	refresh(frm) {
		// your code here
	},
	item_code: async function(frm, cdt, cdn){
        if(frm.doc.amended_from){
            var data = locals[cdt][cdn];
            const item_data = await get_data_from_doctype("Item", data.item_code);
            frappe.model.set_value(cdt, cdn, 'stock_uom', item_data.stock_uom);
            frm.fields_dict['items'].grid.grid_rows_by_docname[cdn].toggle_editable('qty', true);
        }
        
	    await cal_convert_qty_items(frm, cdt, cdn);
	},
	counted_qty: async function(frm, cdt, cdn){
	    await cal_convert_qty_items(frm, cdt, cdn);
	},
	conversion_factor: async function(frm, cdt, cdn){
	    await cal_convert_qty_items(frm, cdt, cdn);
	},
	uom: async function(frm, cdt, cdn){
        var data = locals[cdt][cdn];
	    await cal_convert_qty_items(frm, cdt, cdn);
	    frappe.call({
            async: false,
            method: "dbiz_app.dbiz_app.doctype.operation_job_card.operation_job_card.get_conversion_factor",
            args: {
                item_code: data.item_code,
                uom: data.uom,
            },
            callback: async function(r) {
                if (r.message) {
                    frappe.model.set_value(cdt, cdn, 'conversion_factor', r.message);
                    frappe.model.set_value(cdt, cdn, 'convert_qty', Number((data.counted_qty / (r.message || 1)).toFixed(1)));
                }else{
                    frappe.model.set_value(cdt, cdn, 'conversion_factor', 0);
                    frappe.model.set_value(cdt, cdn, 'convert_qty', 0);
                }
            }
        });
	},
	
})


frappe.ui.form.on('Operation Job Card Workstations', {
	refresh(frm) {
		// your code here
	},
	item_code: async function(frm, cdt, cdn){
	    await set_workstation_qty_details(frm, cdt, cdn);
	},
	qty: async function(frm, cdt, cdn){
	    await set_workstation_qty_details(frm, cdt, cdn);
	},
})

frappe.ui.form.on('Operation Job Card Pallets', {
	refresh(frm) {
		// your code here
	},
	boxs_add: async function (frm, cdt, cdn) {
        var data = locals[cdt][cdn];
        const item_data = await get_data_from_doctype("Item", frm.doc.production_item);
        frappe.model.set_value(cdt, cdn, 'item_code', frm.doc.production_item);
        frappe.model.set_value(cdt, cdn, 'uom', 'Kg');
        frappe.model.set_value(cdt, cdn, 'stock_uom', item_data.stock_uom);
        frappe.model.set_value(cdt, cdn, 'qty', 1);
        frappe.model.set_value(cdt, cdn, 'second_qty', 1);
    },
	item_code: async function(frm, cdt, cdn){
	    var data = locals[cdt][cdn];
        const item_data = await get_data_from_doctype("Item", data.item_code);
        frappe.model.set_value(cdt, cdn, 'uom', 'Kg');
        frappe.model.set_value(cdt, cdn, 'stock_uom', item_data.stock_uom);
        frappe.model.set_value(cdt, cdn, 'qty', 1);
        frappe.model.set_value(cdt, cdn, 'second_qty', 1);
	},
	second_qty: async function(frm, cdt, cdn){
	    var data = locals[cdt][cdn];
        if(data.pallet){
	        
            var model = {
                'batch_no':data.batch_no,
                'item_code':data.item_code,
                'job_card':frm.doc.job_card_name,
                'employee':frm.doc.employee,
                'shift':frm.doc.shift,
                'qty': data.qty,
                'second_qty':data.second_qty,
                'pallet':data.pallet,
                'warehouse':frm.doc.source_warehouse,
                'uom':data.uom,
                'opeartion_job_card_previous_step':frm.doc.opeartion_job_card_previous_step
            }
            await frappe.call({
                method: "dbiz_app.dbiz_app.doctype.pallet.pallet.create_or_update_batch_no",
                args: {
                    data: model
                },
                callback: async function(r) {
                    if (r.message ) {
                        frappe.model.set_value(cdt, cdn, 'batch_no', r.message);
                    }else{
                        
                    }
                }
            });
	    }
	},
	qty: async function(frm, cdt, cdn){
	    var data = locals[cdt][cdn];
        if(data.pallet){
            var model = {
                'batch_no':data.batch_no,
                'item_code':data.item_code,
                'job_card':frm.doc.job_card_name,
                'employee':frm.doc.employee,
                'shift':frm.doc.shift,
                'qty': data.qty,
                'second_qty':data.second_qty,
                'pallet':data.pallet,
                'warehouse':frm.doc.source_warehouse,
                'uom':data.uom,
                'opeartion_job_card_previous_step':frm.doc.opeartion_job_card_previous_step
            }
            await frappe.call({
                method: "dbiz_app.dbiz_app.doctype.pallet.pallet.create_or_update_batch_no",
                args: {
                    data: model
                },
                callback: async function(r) {
                    if (r.message ) {
                        frappe.model.set_value(cdt, cdn, 'batch_no', r.message);
                    }else{
                        
                    }
                }
            });
	    }
	},
	pallet: async function(frm, cdt, cdn){
	    var data = locals[cdt][cdn];
	    if(data.pallet){
	        //Minh fix --------------------
	        //cũ: param 1 là Pallet hết
	        var item_data = await get_data_from_doctype('Item', frm.doc.production_item);
	        var pallet_data = await get_data_from_doctype('Pallet', data.pallet);
	        frappe.model.set_value(cdt, cdn, 'item_code', frm.doc.production_item);
	        let palletCount = 0;
            frm.doc.boxs.forEach(item => {
                // cũ: item.pallet === pallet
                if(item.pallet === pallet_data.name) { // && item.name != data.name
                    palletCount += item.qty;
                }
            });
            //----------------------
            if(palletCount > item_data.carton_per_pallet && item.loading_rule == 'Pallet') {
                frappe.throw(__(`Tổng số lượng (${palletCount}) vượt quá số lượng cho phép trong Pallet (${item_data.carton_per_pallet-pallet_data.qty})`));
                frappe.model.set_value(cdt, cdn, 'pallet', null);
                frm.refresh_field('items');
                return
            }
            var model = {
                'batch_no':data.batch_no,
                'item_code':data.item_code,
                'job_card':frm.doc.job_card_name,
                'employee':frm.doc.employee,
                'shift':frm.doc.shift,
                'qty': data.qty,
                'second_qty':data.second_qty,
                'pallet':data.pallet,
                'warehouse':frm.doc.source_warehouse,
                'uom':data.uom,
                'opeartion_job_card_previous_step':frm.doc.opeartion_job_card_previous_step
            }
            await frappe.call({
                method: "dbiz_app.dbiz_app.doctype.pallet.pallet.create_or_update_batch_no",
                args: {
                    data: model
                },
                callback: async function(r) {
                    if (r.message ) {
                        frappe.model.set_value(cdt, cdn, 'batch_no', r.message);
                    }else{
                        
                    }
                }
            });
	    }
	},
})

frappe.ui.form.on('Operation Job Card Bags', {
	refresh(frm) {
		// your code here
	},
	boxs_add: async function (frm, cdt, cdn) {
        const item_data = await get_data_from_doctype("Item", frm.doc.production_item);
        frappe.model.set_value(cdt, cdn, 'item_code', frm.doc.production_item);
        frappe.model.set_value(cdt, cdn, 'uom', 'Kg');
        frappe.model.set_value(cdt, cdn, 'stock_uom', item_data.stock_uom);
        frappe.model.set_value(cdt, cdn, 'qty', 1);
        frappe.model.set_value(cdt, cdn, 'second_qty', 1);
    },
	item_code: async function(frm, cdt, cdn){
	    var data = locals[cdt][cdn];
        const item_data = await get_data_from_doctype("Item", data.item_code);
        frappe.model.set_value(cdt, cdn, 'item_name', item_data.item_name);
        frappe.model.set_value(cdt, cdn, 'uom', 'Kg');
        frappe.model.set_value(cdt, cdn, 'stock_uom', item_data.stock_uom);
        frappe.model.set_value(cdt, cdn, 'qty', 1);
        frappe.model.set_value(cdt, cdn, 'second_qty', 1);
        var model = {
                'batch_no':data.batch_no,
                'item_code':data.item_code,
                'job_card':frm.doc.job_card_name,
                'employee':frm.doc.employee,
                'shift':frm.doc.shift,
                'qty': 1,
                'second_qty':data.second_qty,
                'pallet':null,
                'warehouse':frm.doc.source_warehouse,
                'uom':data.uom,
                'opeartion_job_card_previous_step':frm.doc.opeartion_job_card_previous_step
            }
        await frappe.call({
            method: "dbiz_app.dbiz_app.doctype.pallet.pallet.create_or_update_batch_no",
            args: {
                data: model
            },
            callback: async function(r) {
                if (r.message ) {
                    frappe.model.set_value(cdt, cdn, 'batch_no', r.message);
                }else{
                    
                }
            }
        });
	},
	second_qty: async function(frm, cdt, cdn){
	    var data = locals[cdt][cdn];
        const item_data = await get_data_from_doctype("Item", data.item_code);
        var model = {
                'batch_no':data.batch_no,
                'item_code':data.item_code,
                'job_card':frm.doc.job_card_name,
                'employee':frm.doc.employee,
                'shift':frm.doc.shift,
                'qty': 1,
                'second_qty':data.second_qty,
                'pallet':null,
                'warehouse':frm.doc.source_warehouse,
                'uom':data.uom,
                'opeartion_job_card_previous_step':frm.doc.opeartion_job_card_previous_step
            }
        await frappe.call({
            method: "dbiz_app.dbiz_app.doctype.pallet.pallet.create_or_update_batch_no",
            args: {
                data: model
            },
            callback: async function(r) {
                if (r.message ) {
                    frappe.model.set_value(cdt, cdn, 'batch_no', r.message);
                }else{
                    
                }
            }
        });
	}
})

frappe.ui.form.on('Operation Job Card Semi Items', {
	refresh(frm) {
		// your code here
	},
	semi_items_add: async function (frm, cdt, cdn) {
        var data = locals[cdt][cdn];
        const item_data = await get_data_from_doctype("Operation", frm.doc.job_card_operation_name);
        const item_data_semi = await get_data_from_doctype("Item", item_data.item_mapping);
        frappe.model.set_value(cdt, cdn, 'item_code', item_data.item_mapping);
        frappe.model.set_value(cdt, cdn, 'stock_uom', item_data_semi.stock_uom);
        frappe.model.set_value(cdt, cdn, 'qty', 1);
    },
})
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


async function cal_convert_qty_items(frm, cdt, cdn) {
    var data = locals[cdt][cdn];
    if(data.counted_qty){
        var conversion_factor = (data.conversion_factor === null || data.conversion_factor === undefined || data.conversion_factor === 0) ? 1 : data.conversion_factor;

        frappe.model.set_value(cdt, cdn, 'convert_qty', data.counted_qty * conversion_factor);
    }
    //-------------------------
    // upDetailsTable(frm);
}
async function set_workstation_qty_details(frm, cdt, cdn) {
    var data = locals[cdt][cdn];
    if(data.item_code){
        const wt_data = await get_data_from_doctype("Workstation", data.item_code);
        if(wt_data.status !== "Off"){   
            if(frm.doc.job_card_operation_name == 'XA'){
                frappe.msgprint("Xe đang sử dụng hoặc đang bị hỏng, vui lòng dùng xe khác");
            }else{
                frappe.msgprint("Lõi đang sử dụng hoặc đang bị hỏng, vui lòng dùng lõi khác");
            }
            frappe.model.set_value(cdt, cdn, 'item_code', '');
        }else{
            frappe.model.set_value(cdt, cdn, 'uom', 'Kg');
            frappe.model.set_value(cdt, cdn, 'weight', wt_data.workstation_weight);
            frappe.model.set_value(cdt, cdn, 'convert_qty', data.qty - wt_data.workstation_weight);
        }
        frm.refresh_field('details');
    }
}



//Minh add
// function upDetailsTable(frm){
//     frm.doc.details.forEach(detail => {
//         detail.fg_qty = detail.convert_qty/frm.doc.multiplier_fg;
//     })
//     frm.refresh_field('details');
// }

function setQueryJobCard(frm, operationName){
	if (!operationName){
		frm.set_query('job_card_name', function () {
    		return {
    			filters: []
    		};
    	})
	}else{
    	frm.set_query('job_card_name', function () {
    		return {
    			filters: [
                    ['operation', '=', operationName],
                    ['status', 'in', ['Open', 'Work In Progress','Submitted']],
                    // ['expected_start_date', '>=', frappe.datetime.nowdate()], 
                    // ['expected_end_date', '<', frappe.datetime.nowdate()]
                ],
                order_by: 'creation DESC'
    		};
    	});
	}
}

function clearDetail(frm){
    frappe.model.clear_table(frm.doc, 'items');
    frappe.model.clear_table(frm.doc, 'details');
    frappe.model.clear_table(frm.doc, 'boxs');
    frm.refresh_field('items');
    frm.refresh_field('details');
    frm.refresh_field('boxs');
}

async function validate_jobcard(frm, jobcard_data) {
    if (frm.doc.job_card_operation_name) {
        const has_operation = jobcard_data.sub_operations.find(item => item.sub_operation === frm.doc.job_card_operation_name);
        if (!has_operation) {
            frappe.msgprint(__('Lệnh sản xuất hằng ngày {0} không có công đoạn này.', [jobcard_data.name]));
            return false;
        }
        if(frm.doc.job_card_operation_name == 'TRON'){
            await frappe.call({
                method: "dbiz_app.overrides.cus_job_card.check_mix_qty_jobcard",
                args: {
                    job_card: jobcard_data.name,
                },
                callback: function (r) {
                    if (!r.message) {
                        frappe.msgprint(__('Vuợt quá số lượng mẻ trộn của lệnh {0}.', [jobcard_data.name]));
                        return false;
                    }
                },
            });
        }
    }

    if (!['Open', 'Work In Progress'].includes(jobcard_data.status)) {
        frappe.msgprint(__('Lệnh sản xuất hằng ngày {0} trạng thái chưa thể sử dụng.', [jobcard_data.name]));
        return false;
    }

    if(jobcard_data.expected_end_date < frappe.datetime.nowdate() || jobcard_data.expected_start_date > frappe.datetime.nowdate()){
        frappe.msgprint(__('Lệnh sản xuất hằng ngày {0} không thuộc ngày hôm nay.'));
        return false;
    }

    return true;
}
//ORC
// function open_camera_dialog(frm) {
//     let d = new frappe.ui.Dialog({
//         title: 'Chụp Ảnh',
//         fields: [
//             {
//                 label: 'Chụp Ảnh',
//                 fieldname: 'camera',
//                 fieldtype: 'Attach Image',
//                 options: {
//                     allow_multiple: false,
//                     private: 0,
//                     restrictions: {
//                         allowed_file_types: ['image/*']
//                     }
//                 }
//             }
//         ],
//         primary_action_label: 'Xác nhận',
//         async primary_action(values) {
//             if (!values.camera) {
//                 frappe.msgprint(__('Vui lòng chụp ảnh trước'));
//                 return;
//             }
            
//             await frappe.show_alert({
//                 message: __('Đang xử lý. Vui lòng chờ!'),
//                 indicator: 'orange'
//             });
//             let file_doc;
//             try {
//                 const file_list = await frappe.db.get_list('File', {
//                     filters: { file_url: values.camera },
//                     fields: ['name', 'is_private']
//                 });

//                 if (file_list && file_list.length > 0) {
//                     file_doc = file_list[0];
//                 } 
//                 if (file_doc.is_private) {
//                     await frappe.call({
//                         method: "dbiz_app.dbiz_app.custom_hook.ocr_api.update_file_public",
//                         args: {
//                             file_name: file_doc.name
//                         }
//                     });
//                     file_doc = await frappe.db.get_doc('File', file_doc.name);
//                 }else{
//                     file_doc = await frappe.db.get_doc('File', file_doc.name);
//                 }
//             } catch (error) {
//                 frappe.msgprint(__('Lỗi khi xử lý file: ') + error.message);
//                 return;
//             }
//             const processBoxes = async () => {
//                 try {
//                     if(['XA', 'NKCUONMANG'].includes(frm.doc.job_card_operation_name)){
//                         let currentDetail = frm.doc.details.find(detail => !detail.image);
//                         if (!currentDetail) {
//                             currentDetail = frm.doc.details[0];
//                         }
//                         frappe.model.set_value(currentDetail.doctype, currentDetail.name, 'image', file_doc.file_url);
                        
//                         const r = await frappe.call({
//                             method: "dbiz_app.dbiz_app.custom_hook.ocr_api.openAI_ocr",
//                             args: {
//                                 image_url: file_doc.file_url
//                             }
//                         });
                        
//                         if (r.message) {
//                             frappe.model.set_value(currentDetail.doctype, currentDetail.name, 'qty', r.message.numbers);
//                             // frappe.model.set_value(currentBox.doctype, currentBox.name, 'reponse_api', r.message.reponse);
//                         }
                        
//                         frm.refresh_field('details');
//                         // await frm.save();
//                         d.hide();
//                     }else if(['DONGTHUNG', 'GCHOANTHIEN'].includes(frm.doc.job_card_operation_name)){
//                         let currentBox = frm.doc.boxs.find(box => !box.image);
//                         if (!currentBox) {
//                             currentBox = frm.doc.boxs[0];
//                         }
//                         frappe.model.set_value(currentBox.doctype, currentBox.name, 'image', file_doc.file_url);
                        
//                         const r = await frappe.call({
//                             method: "dbiz_app.dbiz_app.custom_hook.ocr_api.openAI_ocr",
//                             args: {
//                                 image_url: file_doc.file_url
//                             }
//                         });
                        
//                         if (r.message) {
//                             frappe.model.set_value(currentBox.doctype, currentBox.name, 'second_qty', r.message.numbers);
//                             // frappe.model.set_value(currentBox.doctype, currentBox.name, 'reponse_api', r.message.reponse);
//                         }
                        
//                         frm.refresh_field('boxs');
//                         // await frm.save();
//                         d.hide();
//                     }
                    
//                 } catch (error) {
//                     frappe.msgprint(__('Lỗi khi xử lý ảnh: ') + error);
//                 }
//             };
//             processBoxes();
//         }
//     });
//     d.show();
// }
// function auto_open_camera_and_capture(d) {
//     setTimeout(() => {
//         const attachBtn = d.fields_dict.camera.$wrapper.find('button.btn-attach');
//         if (attachBtn.length) {
//             attachBtn[0].click();

//             setTimeout(() => {
//                 const upload_buttons = document.querySelectorAll('.btn-file-upload');
//                 if (upload_buttons.length >= 4) {
//                     upload_buttons[3].click(); // Mở Camera
//                 }
//             }, 300);
//         }
//     }, 300);
// }

// code funnel
function get_funnel_config(job_card, funnel) {
    const configs = {
        A: {
            rows: job_card.items || [],
            volume_need_mixed: job_card.use_funnel === 'USE_SHARE' ? job_card.volume_need_mixed : job_card.volume_need_mixed_a,
            mix_batch_qty_main: job_card.use_funnel === 'USE_SHARE' ? job_card.mix_batch_qty_main : job_card.mix_batch_qty_main_a,
            mix_batch_qty_sec: job_card.use_funnel === 'USE_SHARE' ? job_card.mix_batch_qty_sec : job_card.mix_batch_qty_sec_a,
            workstation: job_card.use_funnel === 'USE_SHARE' ? (job_card.workstation.length > 0 ? job_card.workstation[0].workstation : null ) : (job_card.workstation_a.length > 0 ? job_card.workstation_a[0].workstation : null ),
            prefix: 'a',
        },
        B: {
            rows: job_card.funnel_b_data || [],
            volume_need_mixed: job_card.volume_need_mixed_b,
            mix_batch_qty_main: job_card.mix_batch_qty_main_b,
            mix_batch_qty_sec: job_card.mix_batch_qty_sec_b,
            workstation: (job_card.workstation_b.length > 0 ? job_card.workstation_b[0].workstation : null ),
            prefix: 'b'
        },
        C: {
            rows: job_card.funnel_c_data || [],
            volume_need_mixed: job_card.volume_need_mixed_c,
            mix_batch_qty_main: job_card.mix_batch_qty_main_c,
            mix_batch_qty_sec: job_card.mix_batch_qty_sec_c,
            workstation: (job_card.workstation_c.length > 0 ? job_card.workstation_c[0].workstation : null ),
            prefix: 'c'
        }
    };
    return configs[funnel];
}

// code funnel
async function validate_daily_plan(frm, job_card) {
    if (frm._notified_daily_plan) return true;
    if(frm.doc.job_card_operation_name == 'TRON' && job_card.daily_plans){
        let today = frappe.datetime.nowdate();
        if (job_card.use_funnel == 'USE_SHARE'){        
            found = job_card.daily_plans.find(plan => plan.plan_start_date <= today && plan.plan_end_date >= today);
        }else{
            found = job_card.daily_plans.find(plan => plan.plan_start_date <= today && plan.plan_end_date >= today&& plan.funnel == frm.doc.funnel);
        }
        if(found){
            const job_card_list = await frappe.db.get_list('Operation Job Card', {
                filters: {
                    job_card_operation_name: frm.doc.job_card_operation_name,
                    job_card_name: job_card.name,
                    start_time: ['<=', found.plan_end_date],
                    start_time: ['>=', found.plan_start_date],
                    funnel: frm.doc.funnel,
                    mortar: frm.doc.mortar,
                    docstatus: ['!=', 2],
                },
                fields: ['name', 'mortar','remaining_mixed_qty']
            });
            const count = job_card_list.reduce((acc, item) => {
                if(item.remaining_mixed_qty >= 1){
                    return acc + 1;
                }else{  
                    return acc;
                }
            }, 0);
            if(frm.doc.mortar == 'MORTAR_MAIN'){
                frm.set_value('remaining_mixed_qty', found.qty - count);
            }
            if(frm.doc.mortar == 'MORTAR_SEC'){
                frm.set_value('remaining_mixed_qty', found.sec_qty - count);
            }

            if(frm.doc.mortar == 'MORTAR_MAIN' &&  count >= found.qty){
                const msg = __('Số cối chính cần trộn đã vượt quá số cối trong ngày. Tổng {0}', [count]);
                if(msg != frm._notified_daily_plan){
                    frappe.msgprint(msg);
                    frm._notified_daily_plan = msg;
                }
                
                // frm.set_value('job_card_name', null);
                return false;
            }
            if(frm.doc.mortar == 'MORTAR_SEC' &&  count >= found.sec_qty){
                const msg = __('Số cối phụ cần trộn đã vượt quá số cối trong ngày. Tổng {0}', [count]);
                if(msg != frm._notified_daily_plan){
                    frappe.msgprint(msg);
                    frm._notified_daily_plan = msg;
                }
                // frm.set_value('job_card_name', null);
                return false;
            }
        }else{
            const msg = __('Không có kế hoạch nào cho ngày hôm nay.');
            if(msg != frm._notified_daily_plan){
                frappe.msgprint(msg);
                frm._notified_daily_plan = msg;
            }
            // frm.set_value('job_card_name', null);
            return false;
        }
    }
    return true;
}


function open_camera_dialog(frm) {
	const dialog = new frappe.ui.Dialog({
	  title: 'Chụp Ảnh',
	  fields: [
		{
		  fieldname: 'camera',
		  fieldtype: 'HTML',
		  options: `
			<video
			  class="camera-video"
			  width="100%"
			  style="display:none;"
			  autoplay
			  muted
			  playsinline
			></video>
			<canvas
			  class="camera-canvas"
			  style="display:none; margin:10px; border:2px solid #000;"
			></canvas>
		  `
		},
		{
		  fieldname: 'captured_image',
		  fieldtype: 'HTML',
		  options: `
			<img
			  class="captured-img"
			  width="100%"
			  style="display:none; margin:10px; border:2px solid #000;"
			/>
		  `
		},
		{
		  fieldname: 'button_group',
		  fieldtype: 'HTML',
		  options: `
			<div style="display:flex; justify-content:space-between; gap:10px; margin-top:10px;">
			  <button class="capture-btn btn btn-secondary" style="flex:1;">📸 Chụp ảnh</button>
			  <button class="recapture-btn btn btn-secondary" style="flex:1; display:none;">🔄 Chụp lại</button>
			  <button class="confirm-btn btn btn-success" style="flex:1; display:none;">✅ Xác nhận</button>
			</div>
		  `
		}
	  ]
	});
  
	dialog.photoData = null;
	dialog._listeners_added = false;
  
	dialog.show();
  
	dialog.$wrapper.on('shown.bs.modal', function() {
		console.log('Dialog fully shown, initializing camera...');
		
		setTimeout(() => {
			_reset_elements(dialog);
			
			setTimeout(() => {
				start_camera(dialog);
			}, 100);
		}, 50);
		if (!dialog._listeners_added) {
			dialog._listeners_added = true;
			setTimeout(() => {
				_setup_button_listeners(frm, dialog);
			}, 200);
		}
	});
  
	dialog.onhide = () => {
		console.log('Dialog hiding, stopping camera...');
		stopCamera(dialog);
		dialog._listeners_added = false;
		dialog.$wrapper.off('shown.bs.modal');
	};
  }
  function start_camera(dialog) {
	console.log('Starting camera...');
	const video = dialog.$wrapper.find('.camera-video')[0];
	
	if (!video) {
		console.error('Video element not found in dialog');
		frappe.msgprint(__('Không tìm thấy video element!'));
		return;
	}

	console.log('Video element found in dialog, requesting camera access...');

	const oldStream = video.srcObject;
	if (oldStream) {
		console.log('Stopping old stream...');
		oldStream.getTracks().forEach(track => track.stop());
		video.srcObject = null;
	}
    
    const video_data =  window.innerWidth <= 768 ? "environment" : "user";

	navigator.mediaDevices.getUserMedia({ 
		video: { 
			width: { ideal: 640 },
			height: { ideal: 480 },
			facingMode: video_data 
		} 
	})
	.then(stream => {
		console.log('Camera access granted, setting up video...');
		video.srcObject = stream;
		
		video.style.display = 'block';
		video.style.width = '100%';
		video.style.height = 'auto';
		
		video.onloadedmetadata = () => {
			console.log('Video metadata loaded, starting playback...');
			video.play().then(() => {
				console.log('Video playing successfully');
				console.log('Video dimensions:', video.videoWidth, 'x', video.videoHeight);
				console.log('Video element style:', video.style.display);
			}).catch(err => {
				console.error('Error playing video:', err);
				frappe.msgprint(__('Không thể phát video: ') + err.message);
			});
		};
		setTimeout(() => {
			if (video.readyState === 0) {
				console.log('Forcing video play...');
				video.play().catch(err => console.error('Force play failed:', err));
			}
		}, 1000);
	})
	.catch(err => {
		console.error('Camera error:', err);
		let errorMsg = 'Lỗi không xác định';
		
		if (err.name === 'NotAllowedError') {
			errorMsg = 'Bạn đã từ chối quyền truy cập camera. Vui lòng cấp quyền và thử lại.';
		} else if (err.name === 'NotFoundError') {
			errorMsg = 'Không tìm thấy camera trên thiết bị.';
		} else if (err.name === 'NotReadableError') {
			errorMsg = 'Camera đang được sử dụng bởi ứng dụng khác.';
		}
		
		frappe.msgprint(__('Không thể mở camera: ') + errorMsg);
	});
  }
  
  function stopCamera(dialog) {
	console.log('Stopping camera...');
	const video = dialog.$wrapper.find('.camera-video')[0];
	if (!video) return;
	
	const stream = video.srcObject;
	if (stream) {
		console.log('Stopping camera tracks...');
		stream.getTracks().forEach(track => track.stop());
		video.srcObject = null;
	}
	video.style.display = 'none';
	console.log('Camera stopped');
  }
  function capture_image(frm, dialog) {
	const video = dialog.$wrapper.find('.camera-video')[0];
	const canvas = dialog.$wrapper.find('.camera-canvas')[0];
	const img = dialog.$wrapper.find('.captured-img')[0];
  
	canvas.width = video.videoWidth;
	canvas.height = video.videoHeight;
	canvas.getContext('2d').drawImage(video, 0, 0);
  
	const dataUrl = canvas.toDataURL('image/png');
	img.src = dataUrl;
	img.style.display = 'block';
	canvas.style.display = 'none';
  
	stopCamera(dialog);
  
	dialog.$wrapper.find('.capture-btn').hide();
	dialog.$wrapper.find('.recapture-btn').show();
	dialog.$wrapper.find('.confirm-btn').show();
  
	dialog.photoData = dataUrl;
  }
  
  function restart_camera(dialog) {
	_reset_elements(dialog);
	start_camera(dialog);
  }
  
  function confirm_image(frm, dialog) {
	if (!dialog.photoData) {
	  frappe.msgprint(__('Không có ảnh để upload!'));
	  return;
	}
  
	const upload = () => _upload_image(frm, dialog);
	frm.is_new() ? frm.save().then(upload).catch(() => {
	  frappe.msgprint(__('Không thể lưu bản ghi trước khi upload ảnh!'));
	}) : upload();
  }
  
function _upload_image(frm, dialog) {
    // Kiểm tra dữ liệu ảnh và docname
    if (!dialog.photoData) {
        frappe.msgprint({
            title: __('Lỗi'),
            indicator: 'red',
            message: __('Không tìm thấy dữ liệu ảnh để upload.')
        });
        return;
    }

    if (!frm.docname) {
        frappe.msgprint({
            title: __('Lỗi'),
            indicator: 'red',
            message: __('Không tìm thấy docname của tài liệu.')
        });
        return;
    }

    // Tạo FormData
    const formData = new FormData();
    try {
        // Chuyển đổi base64 sang Blob
        const blob = dataURLtoBlob(dialog.photoData);
        // Tạo tên file duy nhất với timestamp
        const fileName = `${frm.docname}_${new Date().getTime()}.png`;
        formData.append('file', blob, fileName);
        formData.append('is_private', 0);
        formData.append('doctype', frm.doctype);
        formData.append('docname', frm.docname);
    } catch (err) {
        frappe.msgprint({
            title: __('Lỗi'),
            indicator: 'red',
            message: __('Lỗi khi xử lý dữ liệu ảnh: ') + err.message
        });
        return;
    }

    // Gửi yêu cầu upload
    fetch('/api/method/upload_file', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Frappe-CSRF-Token': frappe.csrf_token
        }
    })
        .then(response => {
            // Kiểm tra trạng thái HTTP
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.message?.file_url) {
                const url = data.message?.file_url;
                const processBoxes = async () => {
                    try {
                        if(['XA'].includes(frm.doc.job_card_operation_name)){
                            let currentDetail = frm.doc.details.find(detail => !detail.image);
                            if (!currentDetail) {
                                currentDetail = frm.doc.details[0];
                            }
                            frappe.model.set_value(currentDetail.doctype, currentDetail.name, 'image', url);
                            
                            const r = await frappe.call({
                                method: "dbiz_app.dbiz_app.custom_hook.ocr_api.openAI_ocr",
                                args: {
                                    image_url: url
                                }
                            });
                            
                            if (r.message) {
                                frappe.model.set_value(currentDetail.doctype, currentDetail.name, 'qty', r.message.numbers);
                                // frappe.model.set_value(currentBox.doctype, currentBox.name, 'reponse_api', r.message.reponse);
                            }
                            
                            frm.refresh_field('details');
                            // await frm.save();
                            dialog.hide();
                        }else if(['NKCUONMANG'].includes(frm.doc.job_card_operation_name)){
                            let currentDetail = frm.doc.semi_items.find(detail => !detail.image);
                            if (!currentDetail) {
                                currentDetail = frm.doc.semi_items[0];
                            }
                            frappe.model.set_value(currentDetail.doctype, currentDetail.name, 'image', url);
                            
                            const r = await frappe.call({
                                method: "dbiz_app.dbiz_app.custom_hook.ocr_api.openAI_ocr",
                                args: {
                                    image_url: url
                                }
                            });
                            
                            if (r.message) {
                                frappe.model.set_value(currentDetail.doctype, currentDetail.name, 'qty', r.message.numbers);
                                // frappe.model.set_value(currentBox.doctype, currentBox.name, 'reponse_api', r.message.reponse);
                            }
                            
                            frm.refresh_field('details');
                            // await frm.save();
                            dialog.hide();
                        }else if(['DONGTHUNG', 'GCHOANTHIEN'].includes(frm.doc.job_card_operation_name)){
                            let currentBox = frm.doc.boxs.find(box => !box.image);
                            if (!currentBox) {
                                currentBox = frm.doc.boxs[0];
                            }
                            frappe.model.set_value(currentBox.doctype, currentBox.name, 'image', data.message?.file_url);
                            
                            const r = await frappe.call({
                                method: "dbiz_app.dbiz_app.custom_hook.ocr_api.openAI_ocr",
                                args: {
                                    image_url: url
                                }
                            });
                            
                            if (r.message) {
                                frappe.model.set_value(currentBox.doctype, currentBox.name, 'second_qty', r.message.numbers);
                                // frappe.model.set_value(currentBox.doctype, currentBox.name, 'reponse_api', r.message.reponse);
                            }
                            
                            frm.refresh_field('boxs');
                            // await frm.save();
                            dialog.hide();
                        }
                        
                    } catch (error) {
                        frappe.msgprint(__('Lỗi khi xử lý ảnh: ') + error);
                    }
                };
                processBoxes();
            } else {
                frappe.msgprint({
                    title: __('Lỗi'),
                    indicator: 'red',
                    message: __('Không nhận được URL của ảnh từ server.')
                });
            }
        })
        .catch(err => {
            console.error('Lỗi khi upload ảnh:', err);
            frappe.msgprint({
                title: __('Lỗi'),
                indicator: 'red',
                message: __('Có lỗi xảy ra khi upload ảnh: ') + err.message
            });
        });
}
   
  function dataURLtoBlob(dataurl) {
    let arr = dataurl.split(','), mime = arr[0].match(/:(.*?);/)[1],
        bstr = atob(arr[1]), n = bstr.length, u8arr = new Uint8Array(n);
    while (n--) {
        u8arr[n] = bstr.charCodeAt(n);
    }
    return new Blob([u8arr], { type: mime });
}
   
  function _setup_button_listeners(frm, dialog) {
	console.log('Setting up button listeners...');
	
	const captureBtn = dialog.$wrapper.find('.capture-btn')[0];
	const recaptureBtn = dialog.$wrapper.find('.recapture-btn')[0];
	const confirmBtn = dialog.$wrapper.find('.confirm-btn')[0];
	
	if (captureBtn) {
		captureBtn.addEventListener('click', () => capture_image(frm, dialog));
		console.log('Capture button listener added');
	}
	
	if (recaptureBtn) {
		recaptureBtn.addEventListener('click', () => restart_camera(dialog));
		console.log('Recapture button listener added');
	}
	
	if (confirmBtn) {
		confirmBtn.addEventListener('click', () => confirm_image(frm, dialog));
		console.log('Confirm button listener added');
	}
  }
   
  function _reset_elements(dialog) {
	console.log('Resetting elements...');
	const video = dialog.$wrapper.find('.camera-video')[0];
	const canvas = dialog.$wrapper.find('.camera-canvas')[0];
	const img = dialog.$wrapper.find('.captured-img')[0];

	if (video) {
		video.style.display = 'none';  
		const oldStream = video.srcObject;
		if (oldStream) {
			oldStream.getTracks().forEach(track => track.stop());
		}
		video.srcObject = null;
		console.log('Video element reset');
	}
	if (canvas) {
		canvas.style.display = 'none';
		console.log('Canvas element reset');
	}
	if (img) {
		img.style.display = 'none';
		console.log('Image element reset');
	}

	// Reset buttons
	dialog.$wrapper.find('.capture-btn').show();
	dialog.$wrapper.find('.recapture-btn').hide();
	dialog.$wrapper.find('.confirm-btn').hide();
	
	console.log('All elements reset successfully');
  }