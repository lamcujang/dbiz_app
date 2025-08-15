frappe.pages['workstation-plan'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Workstation Plan',
        single_column: true
    });

    // Thêm bộ lọc tháng
    let month_field = page.add_field({
        title: 'Tháng',
        label: __("Month"),
        fieldname: 'month',
        fieldtype: 'Select',
        reqd: 1,
        options: [
            { label: "Tháng 1", value: "1" },
            { label: "Tháng 2", value: "2" },
            { label: "Tháng 3", value: "3" },
            { label: "Tháng 4", value: "4" },
            { label: "Tháng 5", value: "5" },
            { label: "Tháng 6", value: "6" },
            { label: "Tháng 7", value: "7" },
            { label: "Tháng 8", value: "8" },
            { label: "Tháng 9", value: "9" },
            { label: "Tháng 10", value: "10" },
            { label: "Tháng 11", value: "11" },
            { label: "Tháng 12", value: "12" }
        ],
        default: new Date().getMonth() + 1,  // Mặc định tháng hiện tại
        change: function() {
        	load_table(month_field,year_field,operation_field,table_container);
        }
    });

    // Thêm bộ lọc năm
    let year_field = page.add_field({
        label: 'Năm',
        fieldname: 'year',
        fieldtype: 'Select',
        reqd: 1,
        options: Array.from({length: 11}, (_, i) => (new Date().getFullYear() + i).toString()),  // 5 năm trước -> 5 năm sau
        default: new Date().getFullYear(),
        change: function() {
			load_table(month_field,year_field,operation_field,table_container);
        }
    });
	// Thêm bộ lọc công đoạn
	let operation_field = page.add_field({
		label: 'Công đoạn',
		fieldname: 'operation',
		fieldtype: 'Select',
        reqd: 1,
		options: [
            { label: "Trộn", value: "TRON" },
            { label: "Thổi", value: "THOIIN" },
            { label: "Cắt", value: "CAT" },
        ],
		default: 'TRON',
		change: function() {
			load_table(month_field,year_field,operation_field,table_container);
		}
	});
    // Nút Lọc
    page.add_inner_button('Lọc', function() {
        load_table(month_field,year_field,operation_field,table_container);
    });
	let table_container = $('<div id="workstation-table" style="margin-top: 20px;"></div>').appendTo(page.body);
    load_table(month_field,year_field,operation_field,table_container);
    
};
function load_table(month_field, year_field,operation_field, table_container) {
	let month = month_field.get_value();
	let year = year_field.get_value();
	let operation = operation_field.get_value();

	list_date = [];
	frappe.call({
		method: 'frappe.client.get_list',
		async: false,  // Để dữ liệu trả về ngay lập tức
		args: {
			doctype: 'Dim Date',
			fields: ['full_date', 'week_of_year', 'month', 'year', 'day_name'], 
			filters: [['month', '=', month], ['year', '=', year]],
			order_by: 'week_of_year asc, full_date asc',
			limit_page_length: 1000
		},
		callback: function (response) {
			if (response.message) {
				let list_date = response.message;
				renderTable(list_date,month,year,operation);
			}
		}
	});
	
}
function renderTable(list_date, month, year, operation) {
    let list_workstation = [];
    let job_cards = [];

    // Lấy danh sách Workstation theo operation
    frappe.call({
        method: 'frappe.client.get_list',
        async: false,
        args: {
            doctype: 'Workstation',
            fields: ['name', 'workstation_name'],
            filters: [['workstation_type', '=', operation]],
            order_by: 'name asc',
            limit_page_length: 1000
        },
        callback: function (response) {
            if (response.message) {
                list_workstation = response.message;
                let workstation_names = list_workstation.map(ws => ws.name);

                // Lấy danh sách Job Card nhưng chỉ trong Workstation đã lọc
                frappe.call({
                    method: 'frappe.client.get_list',
                    async: false,
                    args: {
                        doctype: 'Job Card',
                        fields: ['workstation', 'expected_start_date', 'expected_end_date', 'name', 'production_item', 'for_semi_quantity', 'mix_batch_qty'],
                        filters: [
                            ['workstation', 'in', workstation_names],
                            ['expected_start_date', '<=', list_date[list_date.length - 1].full_date],
                            ['expected_end_date', '>=', list_date[0].full_date]
                        ],
                        order_by: 'expected_start_date asc',
                        limit_page_length: 1000
                    },
                    callback: function (response) {
                        if (response.message) {
                            job_cards = response.message;
                        }
                    }
                });
            }
        }
    });

    let table_html = `<div style="overflow-x: auto; white-space: nowrap; max-width: 100%;">
        <table class="table table-bordered" style="width: auto; min-width: 100%;">`;

    let grouped_by_week = {};
    list_date.forEach(row => {
        if (!grouped_by_week[row.week_of_year]) {
            grouped_by_week[row.week_of_year] = [];
        }
        grouped_by_week[row.week_of_year].push(row);
    });

    let week_keys = Object.keys(grouped_by_week);
    let total_columns = list_date.length + week_keys.length + 1;

    table_html += `<tr><th colspan="${total_columns}" style="text-align: center; font-size: 18px; background-color: #ffcc80; border: 2px solid black;">
        KẾ HOẠCH SẢN XUẤT BỘ PHẬN ${operation == "TRON" ? 'TRỘN': operation == "THOIIN" ?'THỔI':'CẮT'} - THÁNG ${month}/${year}
        </th></tr>`;

    table_html += '<tr><th rowspan="1" style="text-align: center; vertical-align: middle; border: 2px solid black;">Tuần</th>';
    week_keys.forEach(week => {
        let days_in_week = grouped_by_week[week].length;
        table_html += `<th colspan="${days_in_week}" style="text-align: center; border: 2px solid black;">Tuần ${week}</th>`;
        table_html += `<th style="text-align: center; border: 2px solid black;">Tổng</th>`;
    });
    table_html += '</tr>';

    table_html += '<tr><th rowspan="2" style="text-align: center; vertical-align: middle; border: 2px solid black;">Máy</th>';
    week_keys.forEach(week => {
        grouped_by_week[week].forEach(day => {
            let borderStyle = day.day_name === 'Sunday' ? 'border-right: 2px solid black;' : '';
            let formatted_date = day.full_date.split('-').reverse().join('/');
            table_html += `<th style="${borderStyle}">${formatted_date}</th>`;
        });
        table_html += `<th style="border: 2px solid black;">-</th>`;
    });
    table_html += '</tr>';

    table_html += '<tr>';
    week_keys.forEach(week => {
        grouped_by_week[week].forEach(day => {
            let borderStyle = day.day_name === 'Sunday' ? 'border-right: 2px solid black;' : '';
            let color = day.day_name === 'Sunday' ? 'background-color: red; color: white;' : '';
            table_html += `<td style="${color} ${borderStyle}">${day.day_name}</td>`;
        });
        table_html += `<td style="border: 2px solid black;">-</td>`;
    });
    table_html += '</tr>';

    let week_totals = {};
    list_workstation.forEach(ws => {
        table_html += `<tr><td style="font-weight: bold; border: 2px solid black;">${ws.workstation_name}</td>`;

        let workstation_total = 0;
        week_keys.forEach(week => {
            let weekly_total = 0;
            grouped_by_week[week].forEach(day => {
                let current_date = day.full_date.substring(0, 10);
                let is_sunday = day.day_name === 'Sunday';

                let job_list = job_cards.filter(jc => {
                    let start_date = jc.expected_start_date.substring(0, 10);
                    let end_date = jc.expected_end_date.substring(0, 10);
                    return jc.workstation === ws.name && start_date <= current_date && end_date >= current_date;
                });

                let job_details = job_list.map(jc => {
                    let semi_quantity_ton = (jc.for_semi_quantity || 0) / 1000;
                    weekly_total += semi_quantity_ton;
                    return `${jc.name} (${jc.production_item}) - ${semi_quantity_ton.toFixed(2)} Tấn`;
                }).join('<br>');

                let borderStyle = is_sunday ? 'border-right: 2px solid black;' : '';
                table_html += `<td style="background-color: ${job_list.length > 0 ? '#c8e6c9' : '#f0f0f0'}; text-align: center; ${borderStyle}">${job_list.length > 0 ? job_details : 'Nghỉ'}</td>`;
            });

            table_html += `<td style="font-weight: bold; text-align: center; background-color: #ffe0b2; border: 2px solid black;">${weekly_total.toFixed(2)}</td>`;
            workstation_total += weekly_total;
            week_totals[week] = (week_totals[week] || 0) + weekly_total;
        });

        table_html += `<td style="font-weight: bold; text-align: center; background-color: #ffab91; border: 2px solid black;">${workstation_total.toFixed(2)}</td>`;
        table_html += '</tr>';
    });

    table_html += `<tr><td style="font-weight: bold; text-align: center; background-color: #ffcc80; border: 2px solid black;">Tổng</td>`;
    week_keys.forEach(week => {
        let total = week_totals[week] || 0;
        table_html += `<td colspan="${grouped_by_week[week].length}" style="background-color: #ffcc80; text-align: center; border: 2px solid black;">${total.toFixed(2)}</td>`;
        table_html += `<td style="background-color: #ffcc80; text-align: center; border: 2px solid black;">${total.toFixed(2)}</td>`;
    });
    table_html += '</tr>';

    table_html += `</table></div>`;
    $("#workstation-table").html(table_html);
}


