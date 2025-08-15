frappe.pages['shif_change_report'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("Shift Change Report"),
        single_column: true,
    });

    $(wrapper).html('<div style="text-align:center;margin-top:40px;"><button class="btn btn-primary" id="create-ojc">Tạo mới thay đổi ca</button></div>');

    $(wrapper).find('#create-ojc').on('click', function() {
        frappe.route_options = {
			'creation_date': frappe.datetime.get_today(),
		};

		frappe.new_doc('Shift Change Report');
    });
    $(wrapper).find('#create-ojc').trigger('click');
}