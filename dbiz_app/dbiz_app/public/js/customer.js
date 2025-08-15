frappe.ui.form.on('Customer', {
    refresh: function(frm) {
        frm.add_custom_button('Get Tax Information', function() {
            let dialog = new frappe.ui.Dialog({
                title: 'Get Tax Information',
                fields: [
                    {
                        fieldname: 'tax_information',
                        fieldtype: 'Data',
                        label: 'Tax ID',
                        default: frm.doc.tax_id,
                        reqd: 1
                    }
                ],
                primary_action_label: 'Get Tax Information',
                primary_action: async function (values) {
                    await frappe.call({
                        method: 'dbiz_app.dbiz_app.custom_hook.customer_custom.get_tax_information',
                        args: {
                            tax_id: values.tax_information
                        },
                        callback: function(r) {
                            var tax_information = r.message;
                            if(tax_information.code != "00"){
                                frappe.throw(tax_information.desc);
                            }
                            dialog.hide();
                            let dialog2 = new frappe.ui.Dialog({
                                title: 'Tax Information',
                                fields: [
                                    {
                                        fieldname: 'tax_id',
                                        fieldtype: 'Data',
                                        label: 'Tax ID',
                                        default: tax_information.data.id,
                                        reqd: 1
                                    },
                                    {
                                        fieldname: 'name',
                                        fieldtype: 'Small Text',
                                        label: 'Name',
                                        default: tax_information.data.name,
                                        width: '100px',
                                        reqd: 1
                                    },
                                    {
                                        fieldname: 'address',
                                        fieldtype: 'Small Text',
                                        label: 'Address',
                                        default: tax_information.data.address,
                                        width: '100px',
                                        reqd: 1
                                    },
                                ],
                                primary_action_label: 'Update Address',
                                primary_action: async function (values){
                                    frm.set_value('customer_name', values.name);
                                    await frappe.call({
                                        method: 'dbiz_app.dbiz_app.custom_hook.customer_custom.address_from_tax_id',
                                        args: {
                                            addressId: frm.doc.customer_primary_address || null,
                                            address: values.address,
                                            name: values.name
                                        },
                                        callback: function(r){
                                            frm.set_value('customer_primary_address', r.message);
                                            dialog2.hide();
                                        }
                                    });
                                }
                            });
                            dialog2.show();
                        }
                    });
                }
            });
            dialog.show();
        });
    },
    
}); 