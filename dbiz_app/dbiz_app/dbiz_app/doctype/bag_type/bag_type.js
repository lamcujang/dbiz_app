// Copyright (c) 2025, lamnl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bag Type", {
	async refresh(frm) {
        frm.add_custom_button(__('Get Item Fields'), async function() {
            frm.trigger('get_item_fields');
        });

        frm.add_custom_button(__('Copy Formula'), async function() {
            frm.trigger('get_formula');
        });

        await frappe.call({
            method: "dbiz_app.dbiz_app.doctype.bag_type.bag_type.get_list_docfields",
            args: {
                "doctype": "Item"
            },
            callback: function(r) {
                if (r.message) {
                    let options = r.message.map(field => `${__(field.label)} {${field.fieldname}}`).join('\n');
                    
                    frm.fields_dict["details"].grid.update_docfield_property(
                        'field', 
                        'options', 
                        options
                    );

                    frm.refresh_field('details');
                }
            }
        });
	},
    async get_item_fields(frm) {
        frappe.prompt([
            {
                fieldname: 'bag_type',
                fieldtype: 'Link',
                options: 'Bag Type',
                label: 'Bag Type',
                get_query: () => {
                    return {
                        filters: {
                            'name': ['!=', frm.doc.name]
                        }
                    };
                },
                reqd: 1,
            }
        ], async function(values) {
            let bag_type = await get_data_from_doctype('Bag Type', values.bag_type);
            if (bag_type.details) {
                frm.fields_dict["details"].grid.remove_all();
                bag_type.details.forEach(item => {
                    let child = frappe.model.add_child(frm.doc, 'details');
                    child.field = item.field;
                    child.enable = item.enable;
                    child.required = item.required;
                });
                frm.refresh_field('details');
                frappe.msgprint(__("Details copied successfully"));
            }
        });
    },
    async get_formula(frm) {
        frappe.prompt([
            {
                fieldname: 'bag_type',
                fieldtype: 'Link',
                options: 'Bag Type',
                label: 'Bag Type',
                get_query: () => {
                    return {
                        filters: {
                            'name': ['!=', frm.doc.name]
                        }
                    };
                },
                reqd: 1,
            }
        ], async function(values) {
            let bag_type = await get_data_from_doctype('Bag Type', values.bag_type);
            if (!bag_type) {
                frappe.msgprint(__("Failed to fetch source Bag Type"));
                return;
            }

            const standard_fields = [
                "name", "owner", "creation", "modified", "modified_by","code","name1",
                "docstatus", "idx", "title", "naming_series", "image",
                "is_published", "doctype", "details","__last_sync_o"
            ];

            const table_fields = ["details"];

            const updates = {};

            Object.keys(bag_type).forEach(key => {
                if (!standard_fields.includes(key) && !table_fields.includes(key)) {
                    updates[key] = bag_type[key];
                }
            });

            for (const [key, value] of Object.entries(updates)) {
                if(key !== '__last_sync_on')
                    await frm.set_value(key, value);
            }

            frappe.msgprint(__("Formulas copied successfully"));
        });
    }
});
frappe.ui.form.on("Bag Type Details", {
	refresh(frm) {
        
	},
    field(frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        if (row.field) {
            let checkexist = frm.doc.details.filter(item => item.field == row.field);
            if (checkexist.length > 1) {
                frappe.msgprint(__(`Field ${row.field} already exists`));
                row.field = '';
                frm.refresh_field('details');
            }
        }
    }
});

async function get_data_from_doctype(doctype, Id) {
    return await frappe.db.get_doc(doctype, Id).then(doc => {
        return doc;
    }).catch(err => {
        console.error(err);
        return null;
    });
}
