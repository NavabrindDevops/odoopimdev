/** @odoo-module **/

import {patch} from "@web/core/utils/patch";
import {useService} from "@web/core/utils/hooks";
import {_t} from "@web/core/l10n/translation";
import { ExportDataDialog } from "@web/views/view_dialogs/export_data_dialog";
const defaultFamilyFields = ["name","description",'product_families_ids'];
const defaultAttributeFields = ['name','attribute_group','display_type','attribute_types','is_mandatory','is_required_is_clone','is_completeness','value_ids']
const defaultAttributeGroup = ['name','product_attribute_id']
const defaultBrandExportFields = ['name','website','description']
const defaultSupplierExportFields = ["name","website","name",
                               "street","city","website","notes"]
patch(ExportDataDialog.prototype, {
    async setup() {
        super.setup();
    },
    isFieldSelectedExtend(current)
    {
        let no_addable = ['product_family_ids'];
        console.log("current",current);
        if (no_addable.includes(current))
        {
        return false;
        }
        return this.props.exportList.find(({ id }) => id === current);
    },
    isFieldExpandable(id) {
        let non_expandable = ['supplier_id','brand_id','manufacture_id','buyer_id','attribute1_id',
        "related_families", 'substitute_families',
        'attribute2_id','attribute3_id','custom_harmonization_code','alternate_harmonization_code']
        if (non_expandable.includes(id))
        {
        return false;
        }
        return this.knownFields[id].children && id.split("/").length < 3;
    },
 async loadFields(id, preventLoad = false) {
        let model = this.props.root.resModel;
        if(model == 'family.attribute')
        {
            let parentField, parentParams;
            if (id) {
                if (this.expandedFields[id]) {
                return this.expandedFields[id].fields;
                }
                parentField = this.knownFields[id];
                model = parentField.params && parentField.params.model;
                parentParams = {
                ...parentField.params,
                parent_field_type: parentField.field_type,
                parent_field: parentField,
                parent_name: parentField.string,
                exclude: [parentField.relation_field],
                };
            }
            if (preventLoad) {
                return;
            }
            const fields = await this.props.getExportedFields(
                model,
                this.state.isCompatible,
                parentParams
            );
            const new_field_list = [];
            if (!id){
                for (const field of fields) {
                if (defaultFamilyFields.includes(field.id)){
                new_field_list.push(field);
                field.parent = parentField;
                if (!this.knownFields[field.id]) {
                    this.knownFields[field.id] = field;
                }
                }
                }
                return new_field_list;
            }

            for (const field of fields) {
                field.parent = parentField;
                if (!this.knownFields[field.id]) {
                    this.knownFields[field.id] = field;
                }
            }
            if (id) {
                this.expandedFields[id] = { fields };
            }
            return fields;
            }
        else if(model == 'product.brand')
        {
            let parentField, parentParams;
            if (id) {
                if (this.expandedFields[id]) {
                // we don't make a new RPC if the value is already known
                return this.expandedFields[id].fields;
                }
                parentField = this.knownFields[id];
                model = parentField.params && parentField.params.model;
                parentParams = {
                ...parentField.params,
                parent_field_type: parentField.field_type,
                parent_field: parentField,
                parent_name: parentField.string,
                exclude: [parentField.relation_field],
                };
            }
            if (preventLoad) {
                return;
            }
            const fields = await this.props.getExportedFields(
                model,
                this.state.isCompatible,
                parentParams
            );
            const new_field_list = [];
            if (!id){
                for (const field of fields) {
                if (defaultBrandExportFields.includes(field.id)){
                new_field_list.push(field);
                field.parent = parentField;
                if (!this.knownFields[field.id]) {
                    this.knownFields[field.id] = field;
                }
                }
                }
                return new_field_list;
            }

            for (const field of fields) {
                field.parent = parentField;
                if (!this.knownFields[field.id]) {
                    this.knownFields[field.id] = field;
                }
            }
            if (id) {
                this.expandedFields[id] = { fields };
            }
            return fields;
            }
        else if(model == 'supplier.info')
        {
            let parentField, parentParams;
            if (id) {
                if (this.expandedFields[id]) {
                // we don't make a new RPC if the value is already known
                return this.expandedFields[id].fields;
                }
                parentField = this.knownFields[id];
                model = parentField.params && parentField.params.model;
                parentParams = {
                ...parentField.params,
                parent_field_type: parentField.field_type,
                parent_field: parentField,
                parent_name: parentField.string,
                exclude: [parentField.relation_field],
                };
            }
            if (preventLoad) {
                return;
            }
            const fields = await this.props.getExportedFields(
                model,
                this.state.isCompatible,
                parentParams
            );
            const new_field_list = [];
            if (!id){
                for (const field of fields) {
                if (defaultSupplierExportFields.includes(field.id)){
                new_field_list.push(field);
                field.parent = parentField;
                if (!this.knownFields[field.id]) {
                    this.knownFields[field.id] = field;
                }
                }
                }
                return new_field_list;
            }

            for (const field of fields) {
                field.parent = parentField;
                if (!this.knownFields[field.id]) {
                    this.knownFields[field.id] = field;
                }
            }
            if (id) {
                this.expandedFields[id] = { fields };
            }
            return fields;
        }
        else if(model == 'product.attribute')
        {
            let parentField, parentParams;
            if (id) {
                if (this.expandedFields[id]) {
                // we don't make a new RPC if the value is already known
                return this.expandedFields[id].fields;
                }
                parentField = this.knownFields[id];
                model = parentField.params && parentField.params.model;
                parentParams = {
                ...parentField.params,
                parent_field_type: parentField.field_type,
                parent_field: parentField,
                parent_name: parentField.string,
                exclude: [parentField.relation_field],
                };
            }
            if (preventLoad) {
                return;
            }
            const fields = await this.props.getExportedFields(
                model,
                this.state.isCompatible,
                parentParams
            );
            const new_field_list = [];
            if (!id){
                for (const field of fields) {
                if (defaultAttributeFields.includes(field.id)){
                new_field_list.push(field);
                field.parent = parentField;
                if (!this.knownFields[field.id]) {
                    this.knownFields[field.id] = field;
                }
                }
                }
                return new_field_list;
            }

            for (const field of fields) {
                field.parent = parentField;
                if (!this.knownFields[field.id]) {
                    this.knownFields[field.id] = field;
                }
            }
            if (id) {
                this.expandedFields[id] = { fields };
            }
            return fields;
        }
         else if(model == 'attribute.group')
        {
            let parentField, parentParams;
            if (id) {
                if (this.expandedFields[id]) {
                // we don't make a new RPC if the value is already known
                return this.expandedFields[id].fields;
                }
                parentField = this.knownFields[id];
                model = parentField.params && parentField.params.model;
                parentParams = {
                ...parentField.params,
                parent_field_type: parentField.field_type,
                parent_field: parentField,
                parent_name: parentField.string,
                exclude: [parentField.relation_field],
                };
            }
            if (preventLoad) {
                return;
            }
            const fields = await this.props.getExportedFields(
                model,
                this.state.isCompatible,
                parentParams
            );
            const new_field_list = [];
            if (!id){
                for (const field of fields) {
                if (defaultAttributeGroup.includes(field.id)){
                new_field_list.push(field);
                field.parent = parentField;
                if (!this.knownFields[field.id]) {
                    this.knownFields[field.id] = field;
                }
                }
                }
                return new_field_list;
            }

            for (const field of fields) {
                field.parent = parentField;
                if (!this.knownFields[field.id]) {
                    this.knownFields[field.id] = field;
                }
            }
            if (id) {
                this.expandedFields[id] = { fields };
            }
            return fields;
        }
        else
        {
            return super.loadFields(id, preventLoad = false);
        }
    }
});
