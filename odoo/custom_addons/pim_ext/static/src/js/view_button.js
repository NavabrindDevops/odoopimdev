/** @odoo-module */
import {
    deleteConfirmationMessage,
    ConfirmationDialog,
} from "@web/core/confirmation_dialog/confirmation_dialog";
import { ListController } from "@web/views/list/list_controller";
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';
import { useOwnedDialogs, useService } from "@web/core/utils/hooks";
import { ListRenderer } from "@web/views/list/list_renderer";
import { useState, Component, onWillStart } from "@odoo/owl";
import { CheckboxItem } from "@web/core/dropdown/checkbox_item";
import { _t } from "@web/core/l10n/translation";
import { _lt } from "@web/core/l10n/translation";
import { download } from "@web/core/network/download";
import { ExportDataDialog } from "@web/views/view_dialogs/export_data_dialog";
const componentModel = "product.brand";
import { unique } from "@web/core/utils/arrays";

var activeCustomField = [];
var filter;

function useUniqueDialog() {
    const displayDialog = useOwnedDialogs();
    let close = null;
    return (...args) => {
        if (close) {
            close();
        }
        close = displayDialog(...args);
    };
}

export class ProductRightPanel extends Component {
    static template = "pim_ext.ProductRightPanel";
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

       const result = await this.orm.search("family.category",[]);
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
     let categ_list = []
     this.props.currentSelection.forEach(function (record) {
            idlist.push(record.resId);
        });

       const result = await this.orm.search("family.category",[]);
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
                     'default_mode':'add_taxonomy'
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
     async onclickAddRelatedFamily(){
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
            name: "Add Related Family",
            type: "ir.actions.act_window",
            res_model: "related.family.wizard",
            views: [[false, "form"]],
            view_mode: "form",
            target: "new",
            context:{'default_family_ids':idlist,
                     'default_related_family_ids':family_list
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

//
//export class ManagementListController extends ListController {
//        setup() {
//               super.setup();
//               this.actionService = useService("action");
//
//           }
//        showarchived() {
//                var domain = "[['active', 'in', [false, true]]]";
//                var view_id = this.env.config.viewId;
//                this.actionService.doAction({
//                  type: 'ir.actions.act_window',
//                  res_model: 'product.attribute',
//                  name:'Families',
//                  view_mode: 'list,form',
//                  view_type: 'list,form',
//                  views: [[this.env.config.viewId || false, "list"],[false, "form"],[false, "kanban"]],
//                  domain: domain,
//                  target:'main'
//              });
//           }
//           hidearchived() {
//                var domain = "[['active', 'in', [true]]]";
//                var view_id = this.env.config.viewId;
//                this.actionService.doAction({
//                  type: 'ir.actions.act_window',
//                  res_model: 'product.attribute',
//                  name:'Families',
//                  view_mode: 'list,form',
//                  view_type: 'list,form',
//                  views: [[this.env.config.viewId || false, "list"],[false, "form"],[false, "kanban"]],
//                  domain: domain,
//                  target:'main'
//              });
//           }
//};
//ManagementListController.template = "pim_ext.ProductButtonListView";


export class ProductListController extends ListController {
   setup() {
       super.setup();
       this.actionService = useService("action");
       this.orm = useService("orm");
       this.state = useState({
            columns: this.props.list,
            views_list: [],
            selected_view : '',
            selected_view_filter : '',
            selected_view_name : '',


        });
       this._fetch_data();
       this.views_list = [];
       this.default_view = '';
       this.selected_view = '';
       this.selected_view_filter = '';
       this.selected_view_name = '';
       this.list_count;
       this.fName;
       this.button_name = this.props.button_name || "Default View";
       this.displayDialog = useUniqueDialog();
   }

   customList(ev) {
        var view_id = ev.srcElement.id;
        var view_name = ev.srcElement.outerText;
        var fName = '';
        var valueId, itemId;
        console.log('--------------------customList',view_id)
        this.orm.call("ir.ui.view", "update_custom_list", [parseInt(view_id), view_id]).then(function(result){
            var fName = result;
         })
        window.location.reload();
//        const name = ev.target.getAttribute('data-name');
//        this.button_name = view_name;
   }

   updateList(ev) {
        var view_id = ev.srcElement.id;
        var view_name = ev.srcElement.outerText;
        const favorites = this.env.searchModel.getSearchItems(
            (searchItem) => searchItem.type === "favorite"
        );
        console.log('favorites -- ', favorites);
        let itemId;
        let filterName;
        for (let i = 0; i < favorites.length; i++) {
            if (favorites[i].isActive) {
                itemId = favorites[i].id;
                filterName = favorites[i].description;
                break;
            }
        }
        console.log('updateList -- ', filterName);
        this.orm.call("ir.ui.view", "update_saved_list", [view_id, view_id, activeCustomField, filterName]);

//        window.location.reload();

   }

   DefaultListview(ev) {
        var view_id = ev.srcElement.id;
        var view_name = ev.srcElement.outerText;
        console.log('------------DefaultListview',view_id )
        this.orm.call("ir.ui.view", "update_default_custom_list", [parseInt(view_id),view_id]);
        window.location.reload();
   }
   RemoveList(ev) {
        var view_id = ev.srcElement.id;

        this.displayDialog(ConfirmationDialog, {
            title: _t("Bye-bye, record!"),
            body: deleteConfirmationMessage,
            confirm: () => {
                this.orm.call("ir.ui.view", "delete_custom_list", [view_id, view_id]);
                window.location.reload();

            },
            confirmLabel: _t("Delete"),
            cancel: () => {
                // `ConfirmationDialog` needs this prop to display the cancel
                // button but we do nothing on cancel.
            },
            cancelLabel: _t("No, keep it"),
        });
   }
    showarchived() {
        var domain = "[['active', 'in', [false, true]]]";
        var view_id = this.env.config.viewId;
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            res_model: 'product.management',
            name: 'Product Management',
            view_mode: 'list,form',
            view_type: 'list,form',
            views: [[this.env.config.viewId || false, "list"], [false, "form"]],
            domain: domain,
            target: 'main'
        });
    }
    hidearchived() {
        var domain = "[['active', 'in', [true]]]";
        var view_id = this.env.config.viewId;
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            res_model: 'product.management',
            name: 'Product Management',
            view_mode: 'list,form',
            view_type: 'list,form',
            views: [[this.env.config.viewId || false, "list"], [false, "form"]],
            domain: domain,
            target: 'main'
        });
    }


    _fetch_data(){
        var span_val = "";
        var self = this;
        var button_name = self.button;
        var selected_view = self.selected_view;
        var selected_view_name = self.selected_view_name;
        var selected_view_filter = '';
        var searchData = this.env.searchModel;
        const favorites = this.env.searchModel.getSearchItems(
            (searchItem) => searchItem.type === "favorite"
        );
        this.orm.call("ir.ui.view", "get_custom_view_list", [this.env.config.viewId]).then(function(result){
            var views_list = self.views_list;
            var default_view = self.default_view;
            var selected_view_filter = result.selected_view_filter;

            self.views_list = result.list_views;
            self.state.views_list = result.list_views;
            self.default_view = result.default_view;
            self.selected_view = result.selected_view;
            self.state.selected_view = result.selected_view;
            self.selected_view_name = result.selected_view_name;
            self.state.selected_view_name = result.selected_view_name;
            console.log(self.state.selected_view_name,'---',self.selected_view_name,'selected_view-----------', self.state.selected_view,'-----', self.selected_view_filter, '------', self.default_view)
            if(selected_view_filter){
                console.log("----------------selected_view_filter", selected_view_filter)
                var valueId = favorites.filter((data) => {return data.description == selected_view_filter})
                var itemId = valueId[0].id;

                searchData.toggleSearchItem(itemId);
            }
        })
    };



   saveFavorites(ev) {
         var description = this.state.description;
         var baseURI = this.archInfo.xmlDoc.baseURI;
         var view_id = this.env.config.viewId;
         var resModel = this.props.resModel;
         var optionalFields = [];
         var allFields = [];
         var list_count = 0;
         const favorites = this.env.searchModel.getSearchItems(
            (searchItem) => searchItem.type === "favorite"
         );
         let itemId;
         let filterName;
         for (let i = 0; i < favorites.length; i++) {
            if (favorites[i].isActive) {
                itemId = favorites[i].id;
                filterName = favorites[i].description;
                break;
            }
         }
//
//         if (itemId) {
//            this.env.searchModel.toggleSearchItem(itemId);
//         }

         const allColumns = this.archInfo.columns;
         for (const val of allColumns) {
            var everyField = {
                label: val.label,
                name: val.name,
                value: this.optionalActiveFields[val.name],
                column: val.column_invisible,
            };
            allFields.push(everyField);
            }
         const optionalColumns = this.archInfo.columns.filter(
            (col) => col.optional && !col.column_invisible
         );
         for (const col of optionalColumns) {
            var optionalField = {
                label: col.label,
                name: col.name,
                value: this.optionalActiveFields[col.name],
                widget: col.widget,
            };
            optionalFields.push(optionalField);
            }
         var filter_name = filterName || false;

         this.orm.call("ir.ui.view", "save_custom_list", [view_id, description, view_id, resModel, optionalFields, filterName]).then(function(result){
            var list_count = result;
            if (list_count < 10){
                window.location.reload();
            }
         })

    }


    /**
    * @param {KeyboardEvent} ev
    */
    onInputKeydown(ev) {
    switch (ev.key) {
        case "Enter":
            ev.preventDefault();
            this.saveFavorites();
            break;
        case "Escape":
            ev.preventDefault();
            ev.target.blur();
            break;
    }
    }


}
ProductListController.template = "pim_ext.ProductButtonListView";


export class ProductListRenderer extends ListRenderer {
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

    async toggleOptionalField(fieldName) {
        this.optionalActiveFields[fieldName] = !this.optionalActiveFields[fieldName];
        let newObj = {};
        let is_true = activeCustomField.some((data)=> {return data.objName == fieldName})
        if (!is_true) {
            newObj.objName = fieldName;
            newObj.status = this.optionalActiveFields[fieldName];
            activeCustomField.push(newObj);
        }else if (is_true){
            let objIndex = activeCustomField.findIndex((data,index)=> {return data.objName == fieldName})
            activeCustomField[objIndex].status = this.optionalActiveFields[fieldName];
        }

        if (this.props.onOptionalFieldsChanged) {
            this.props.onOptionalFieldsChanged(this.optionalActiveFields);

        }
        this.state.columns = this.getActiveColumns(this.props.list);
//        this.saveOptionalActiveFields(
//            this.allColumns.filter((col) => this.optionalActiveFields[col.name] && col.optional)
//        );
    }

}
ProductListRenderer.template = "pim_ext.ProductRenderer";
ProductListRenderer.components = Object.assign({}, ListRenderer.components, {
    ProductRightPanel
});

registry.category("views").add("buttons_in_tree", {
   ...listView,
   Renderer: ProductListRenderer,
   Controller: ProductListController,
   buttonTemplate: "button_sale.ListView.Buttons",
});
