frappe.pages['dongthung'].on_page_load = function(wrapper) {
	
	var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("Đóng thùng"),
        single_column: true,
    });

    $(wrapper).html('<div style="text-align:center;margin-top:40px;"><button class="btn btn-primary" id="create-ojc">Đóng thùng</button></div>');

    $(wrapper).find('#create-ojc').on('click', function() {
        frappe.route_options = {
			'work_time': frappe.datetime.get_today(),
			'start_time': frappe.datetime.get_today(),
			'job_card_operation_name': 'DONGTHUNG',
		};

		frappe.new_doc('Operation Job Card');
    });

	$(wrapper).find('#create-ojc').trigger('click');
}