/** @odoo-module */

import { ProductListController, ProductListRenderer } from "@pim_view_preference_button/js/pim_view_preference";
import { ListController } from "@web/views/list/list_controller";
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';
import { useOwnedDialogs, useService } from "@web/core/utils/hooks";
import { ListRenderer } from "@web/views/list/list_renderer";
import { useState, Component, onWillStart } from "@odoo/owl";
//import { CheckboxItem } from "@web/core/dropdown/checkbox_item";
import { _t } from "@web/core/l10n/translation";
import { _lt } from "@web/core/l10n/translation";
import { download } from "@web/core/network/download";
import { ExportDataDialog } from "@web/views/view_dialogs/export_data_dialog";
//const componentModel = "product.brand";
import { unique } from "@web/core/utils/arrays";
import { patch } from "@web/core/utils/patch";

//var activeCustomField = [];
var filter;

//function useUniqueDialog() {
//    const displayDialog = useOwnedDialogs();
//    let close = null;
//    return (...args) => {
//        if (close) {
//            close();
//        }
//        close = displayDialog(...args);
//    };
//}

export class MassEditPanel extends Component {
    static template = "pim_mass_edit_panel.MassEditPanel";
    static props = {
//        context: { type: Object },
        currentSelection: { type: Array },
        selection: { type: Array },
        model: { type: Object },
        archInfo: { type: Object },
        optionalActiveFields : { type: Object },
        fields: { type: Object },
//        kanbanModel: { type: Object },
//        canCreate: { type: Boolean },
    };
    /*
    * Re-write to import required services and update props on the component start
    */
    setup() {
        this.orm = useService("orm");
        this.dialogService = useService("dialog");
        this.actionService = useService("action");
        this.rpc = useService("rpc");
        this.state = useState({
            skuCount: 0,
            familyCount: 0,
        });
        onWillStart(async () => {
//            await this._loadMassActions(this.props);
//            await this._loadExportConf(this.props);
        });
    }
     async getExportedFields(model, import_compat, parentParams) {
        const fields = await this.rpc("/web/export/get_fields", { ...parentParams, model, import_compat });
        return fields
    }

  async downloadExport(fields, import_compat, format) {
        let ids = false;
        let recordIds = []
     this.props.currentSelection.forEach(function (record) {
            recordIds.push(record.resId);
        });

        const exportedFields = fields.map((field) => ({
            name: field.name || field.id,
            label: field.label || field.string,
            store: field.store,
            type: field.field_type || field.type,
        }));
        if (import_compat) {
            exportedFields.unshift({
                name: "id",
                label: _t("External ID"),
            });
        }
        await download({
            data: {
                data: JSON.stringify({
                    import_compat,
                    context: this.props.context,
                    domain: this.props.model.root.domain,
                    fields: exportedFields,
                    groupby: this.props.model.root.groupBy,
                    ids:recordIds.length > 0 && recordIds,
                    model: this.props.model.root.resModel,
                }),
            },
            url: `/web/export/${format}`,
        });
    }
        get defaultExportList() {
        return unique(
            this.props.archInfo.columns
                .filter((col) => col.type === "field")
                .filter((col) => !col.optional || this.props.optionalActiveFields[col.name])
                .map((col) => this.props.fields[col.name])
                .filter((field) => field.exportable !== false)
        );
    }

    async onClickCloneProduct() {
        try {
            const selectedRecords = this.props.currentSelection.map(record => record.resId);
            const viewId = await this.orm.call('clone.product.wizard', 'get_clone_product_view_id', []);
            return this.actionService.doAction({
                name: "Clone Product",
                type: "ir.actions.act_window",
                res_model: "clone.product.wizard",
                view_mode: "form",
                target: "new",
                views: [[viewId, "form"]],
                context: {
                    default_active_product_ids: selectedRecords,
                },
            });
        }
        catch (error) {
            this.env.services.notification.add('An error occurred while opening the Clone Product Wizard.', {
                type: 'danger',
            });
            console.error("Error Details:", error);
        }
    }



    async getExportedFields(model, import_compat, parentParams) {
        return await this.rpc("/web/export/get_fields", {
            ...parentParams,
            model,
            import_compat,
        });
    }
    async onClickExport(props){
    console.log("this.props.defaultExportList",this.props.defaultExportList);
    const dialogProps = {
            context: this.props.context,
            defaultExportList: this.defaultExportList,
            download: this.downloadExport.bind(this),
            getExportedFields: this.getExportedFields.bind(this),
            root: this.props.model.root,
        };
        this.dialogService.add(ExportDataDialog, dialogProps);
    }

    async onClickImport(){
     const { context, resModel } = this.env.searchModel;
        this.actionService.doAction({
            type: "ir.actions.client",
            tag: "import",
            params: { model: 'family.attribute', context:this.props.context },
        });
    }
    async onClickComplementaryCategory(){
       let idlist = []
     let categ_list = []
     this.props.currentSelection.forEach(function (record) {
            idlist.push(record.resId);
        });

       const result = await this.orm.search("pim.category",[]);
       for (const categ of result)
       {
            let categ_line = {
                'category_id':categ
            }
            categ_list.push((0, 0, categ_line))
        }
        return this.actionService.doAction({
            name: "Add Category",
            type: "ir.actions.act_window",
            res_model: "category.wizard",
            views: [[false, "form"]],
            view_mode: "form",
            target: "new",
            context:{'default_family_ids':idlist,
                     'default_category_ids':categ_list,
                     'default_mode':'add_comp'
             }
        });
    }
     async onClickSubstitutefamily(){
     let idlist = []
     let family_list = []
     this.props.currentSelection.forEach(function (record) {
            idlist.push(record.resId);
        });

       const result = await this.orm.search("family.attribute",[]);
       for (const  family of result)
       {
            let family_line = {
                'family_id': family
            }
            family_list.push((0, 0, family_line))
       }
        return this.actionService.doAction({
            name: "Add Substitute Family",
            type: "ir.actions.act_window",
            res_model: "sub.family.wizard",
            views: [[false, "form"]],
            view_mode: "form",
            target: "new",
            context:{'default_family_ids':idlist,
                     'default_sub_family_ids':family_list
             }
        });
     }
     async onClickAddCatgeory(props){
     let idlist = []
//     let categ_list = []
     this.props.currentSelection.forEach(function (record) {
            idlist.push(record.resId);
        });

       const result = await this.orm.search("pim.category",[]);

        return this.actionService.doAction({
            name: "Add Category",
            type: "ir.actions.act_window",
            res_model: "category.wizard",
            views: [[false, "form"]],
            view_mode: "form",
            target: "new",
            context:{'default_product_ids':idlist,
//
             }
        });

     }
     async onClickCloneSKU(){
     let idlist = []
     this.props.currentSelection.forEach(function (record) {
            idlist.push(record.resId);
        });

        let sku_list = [];
        const view_id = await this.orm.call('family.attribute','get_sku_grid_view', [idlist[0]]);
        const res_id = await this.orm.call('family.attribute','create_sku_wizard', [idlist[0],'clone']);
           return this.actionService.doAction({
            name: "Choose SKU",
            type: "ir.actions.act_window",
            res_model: "sku.grid.wizard",
            views: [[view_id, "form"]],
            view_mode: "form",
            res_id: res_id,
            target: "new",
        });
     }
     async onClickMoveSKU(){
     let idlist = []
     this.props.currentSelection.forEach(function (record) {
            idlist.push(record.resId);
        });

        let sku_list = [];
        const view_id = await this.orm.call('family.attribute','get_sku_grid_view', [idlist[0]]);
        const res_id = await this.orm.call('family.attribute','create_sku_wizard', [idlist[0],'move']);
           return this.actionService.doAction({
            name: "Choose SKU",
            type: "ir.actions.act_window",
            res_model: "sku.grid.wizard",
            views: [[view_id, "form"]],
            view_mode: "form",
            res_id: res_id,
            target: "new",
        });
     }
     async onClickMoveSKUnewfamily(){
         let idlist = []
     this.props.currentSelection.forEach(function (record) {
            idlist.push(record.resId);
        });

        let sku_list = [];
        const view_id = await this.orm.call('family.attribute','get_sku_grid_view', [idlist[0]]);
        const res_id = await this.orm.call('family.attribute','create_sku_wizard', [idlist[0],'move_new']);
           return this.actionService.doAction({
            name: "Choose SKU",
            type: "ir.actions.act_window",
            res_model: "sku.grid.wizard",
            views: [[view_id, "form"]],
            view_mode: "form",
            res_id: res_id,
            target: "new",
        });
     }
     async onclickAddFamily(){
     let idlist = []
//     let family_list = []
     this.props.currentSelection.forEach(function (record) {
            idlist.push(record.resId);
        });

       const result = await this.orm.search("family.attribute",[]);
//       for (const  family of result)
//       {
//            let family_line = {
//                'family_id': family
//            }
//            family_list.push((0, 0, family_line))
//       }
        return this.actionService.doAction({
            name: "Add Related Family",
            type: "ir.actions.act_window",
            res_model: "family.wizard",
            views: [[false, "form"]],
            view_mode: "form",
            target: "new",
            context:{'default_product_ids':idlist,
//                     'default_related_family_ids':family_list
             }
        });
     }

    async get_family_count(){
       const result = await this.orm.search("family.attribute", []);
       this.state.familyCount = result.length;
    }

    get family_count(){
        this.get_family_count();
        return this.state.familyCount;
    }

    async get_sku_length(res_id){
        if (this.props.currentSelection){
              const result = await this.orm.search("family.products", [['family_id','=',this.props.currentSelection[0].resId]]);
              this.state.skuCount = result.length;
        }
    }

    get sku_len() {
        this.get_sku_length();
        return this.state.skuCount;
    }

    get records() {
        console.log('-----------------------records',this.props.currentSelection.length)
        return this.props.currentSelection.length;
    }
};

patch(ProductListRenderer.prototype, {

getProductManagerProps() {
    console.log("this.optionalActiveFields",this.props.list.selection)
        return {
            currentSelection: this.props.list.selection || [],
            selection: this.props.list.model.selectedRecords || [],
            model: this.props.list.model,
            archInfo : this.props.archInfo,
            optionalActiveFields : this.optionalActiveFields,
            fields: this.fields
        };
    }
});



ProductListRenderer.template = "pim_mass_edit_panel.ProductRenderer";
ProductListRenderer.components = Object.assign({}, ListRenderer.components, {
    MassEditPanel
});

