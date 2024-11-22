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
import { useState, Component } from "@odoo/owl";
import { CheckboxItem } from "@web/core/dropdown/checkbox_item";
import { _t } from "@web/core/l10n/translation";

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



export class ProductListController extends ListController {
   setup() {
       super.setup();
       console.log('<<<<--------')
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

    _fetch_data(){
        console.log("----->>>>")
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
//PimListController.template = "pim_view_preference_button.PimDiscontinueButtonListView";


export class ProductListRenderer extends ListRenderer {
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


registry.category("views").add("button_in_tree", {
   ...listView,
   Renderer: ProductListRenderer,
   Controller: ProductListController,
   buttonTemplate: "button.ListView.Buttons",
});
