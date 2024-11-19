/** @odoo-module **/

import { NavBar } from "@web/webclient/navbar/navbar";
import { useService, useBus } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";
import { useRef } from "@odoo/owl";


const actionRegistry = registry.category("actions");
function spaceHide(loopValue, stringValue){
     loopValue.forEach((item) => {
        return item.style.display = `${stringValue}`
        })
}

patch(NavBar.prototype, {
    setup() {
        super.setup();
        this.orm = useService('orm')
        this.actionService = useService("action");
        this._fetch_data();
        this.menu_name = '';
        this.router = useService("router");
        const onChangeValues=(ev)=>{
            let hasValue = !!ev.target.closest(".family_redirect")
            let hasBrandValue = !!ev.target.closest(".brand_redirect")
            let hasSupplierValue = !!ev.target.closest(".supplier_redirect")
            let hasCustomValue = !!ev.target.closest(".sku_custom_redirect")
            let hasSkuName = !!ev.target.closest(".sku_name_redirect")
            let hasSkuId = !!ev.target.closest(".sku_id_redirect")
            let hasFamilyList = !!ev.target.closest(".family_list_redirect")
            let hasCategorylist = !!ev.target.closest(".category_list_redirect")
            let dropdownId = document.getElementById("search_sugest")
            let dropdownChange = !!ev.target.closest("#search_sugest")
            let customSearchInput = !!ev.target.closest("#custom_search_input")
            if (hasValue || hasBrandValue || hasSupplierValue || hasCustomValue || hasSkuName || hasSkuId || hasFamilyList || hasCategorylist) {
                var view_id = ev.srcElement.id;
                var viewIdList = view_id.split(",");
                var view_name = ev.srcElement.outerText;
                var domain;
                if (hasFamilyList){
                   domain = view_id;
                   document.getElementById('custom_search_input').value = '';
                   return this.actionService.doAction({
                        name: _t("Product Families"),
                        type: "ir.actions.act_window",
                        res_model: "family.attribute",
                        res_id: parseInt(view_id),
                        domain: [["id", "=", view_id]],
                        views: [[false, "list"],[false, "form"]],
                        view_mode: "list,form",
                        target: "current",
                        });

                }
                if (hasBrandValue){
                    domain = viewIdList;
                    if (dropdownId) dropdownId.style.display = 'none';
                    document.getElementById('custom_search_input').value = '';
                    return this.actionService.doAction({
                        name: _t("Product Brand"),
                        type: "ir.actions.act_window",
                        res_model: "product.brand",
                        domain: [["id", "in", domain]],
                        views: [[false, "list"], [false, "form"]],
                        view_mode: "list,form",
                        target: "current",
                        });
                }
                if (hasCategorylist){
                    domain = viewIdList;
                    if (dropdownId) dropdownId.style.display = 'none';
                    document.getElementById('custom_search_input').value = '';
                    return this.actionService.doAction({
                        name: _t("Pim Category"),
                        type: "ir.actions.act_window",
                        res_model: "pim.category",
                        domain: [["id", "in", domain]],
                        views: [[false, "list"], [false, "form"]],
                        view_mode: "list,form",
                        target: "current",
                        });
                }

            }

            if (dropdownChange == false && customSearchInput == false){
                if(dropdownId) dropdownId.style.display = 'none';
            }
        }

        const onTestKeydown=(ev)=>{
        let customSearchInput = !!ev.target.closest("#custom_search_input");
    }
        document.addEventListener('click',onChangeValues);

    },

    _fetch_data(){
        var self = this;
        var menu_name = self.menu_name;

        var menuId = window.location.href;
        this.orm.call("search.info", "get_menu_name", [menuId, menuId]).then(function(result){
            if (result){
                self.menu_name = result;
            }
            else {
                self.menu_name = 'False';
            }
        })
    },


    onSearchInputVal(ev) {
        var self = this;
        const query = ev.target.value;
        $('search_sugest').show();
        var closeButton = document.getElementById('button_close');
        var searchSuggest = document.querySelector('#search_sugest');
        var familyIdList = document.querySelectorAll('#family_dropdown');
        var brandList = document.querySelectorAll('#brand_dropdown');
        var supplierList = document.querySelectorAll('#supplier_search');
        var skuNameList = document.querySelectorAll('#sku_name_search');
        var skuIdList = document.querySelectorAll('#sku_id_search');
        var categorylist = document.querySelectorAll('#category_list_search');
        var familyList = document.querySelectorAll('#family_id_dropdown');
        var customField= document.querySelectorAll('#custom_field_search');
        var inputValue = ev.target.value.trim();
        let dropdownId = document.getElementById("search_sugest")
        let dropdownNot = document.getElementById("results_not_found")

        $('#family_dropdown').empty();
        $('#brand_dropdown').empty();
        $('#brand_search').empty();
        $('#supplier_search').empty();
        $('#family_search').empty();
        $('#custom_field_search').empty();
        $('#sku_name_search').empty();
        $('#sku_id_search').empty();
        $('#category_list_search').empty();
        if (inputValue?.length > 0) {
            this.orm.call("search.info", "get_search_values_list", [inputValue, inputValue]).then(function(result){
            var {family_info,family_relevant_data,category_list_data,brand_info} = result;
            if (family_info.length > 0 || family_relevant_data.length > 0 || category_list_data.length > 0 || brand_info.length > 0){
                dropdownId.style.display = 'block';
                dropdownNot.style.display = 'none';
            }
            else {
                dropdownId.style.display = 'none';
                dropdownNot.style.display = 'block';
                searchSuggest.classList.remove('show');
            }
            if (family_relevant_data.length > 0){
                for (let i = 0; i < family_relevant_data.length; i++) {
                    $('#family_dropdown').append("<div class='family_relavant_search' style='background-color: #269b8f;padding: 5px;color: white;border: 1px solid white;margin-top: 1px;height: 50px;margin: auto;align-content: center;' id='family_relavant_search'><a class='family_list_redirect' style='color: white;' id='"+ family_relevant_data[i].id + "'>View Families has: " + family_relevant_data[i].name + " </a> </div>");

                }
                 spaceHide(familyIdList, "block");

            }else {
                spaceHide(familyIdList, "none");
            }
            if (category_list_data.length > 0){
                for (let i = 0; i < category_list_data.length; i++) {
                    $('#category_list_search').append("<div class='category_relevant_search' style='background-color: #269b8f;padding: 5px;color: white;border: 1px solid white;margin-top: 1px;height: 50px;margin: auto;align-content: center;' id='category_relevant_search'><a class='category_list_redirect' style='color: white;' id='"+ category_list_data[i].id + "'>View Category has: " + category_list_data[i].name + " </a> </div>");

                }
                 spaceHide(categorylist, "block");

            }else {
                spaceHide(categorylist, "none");
            }

            if (brand_info.length > 0){
                $('#brand_dropdown').show();
                for (let i = 0; i < brand_info.length; i++) {
                        $('#brand_dropdown').append("<div class='brand_search' style='background-color: rgb(197, 29, 29);padding: 5px;color: white;border: 1px solid white;margin-top: 1px;height: 50px;margin: auto;align-content: center;' id='brand_search'><a class='brand_redirect' style='color: white;' id='"+ brand_info[i].id + "'>View Brand has: " + brand_info[i].name + " </a> </div>");
                }
                   spaceHide(brandList, "block");
            }else {
                   spaceHide(brandList, "none");

            }
         })
        }
//        else {
//            searchSuggest.classList.remove('show');
//            closeButton.style.display = 'none';
////            closeButton.classList.remove('show');
//            dropdownId.style.display = 'none';
////            document.getElementById('custom_search_input').value = '';
//
//        }
    },

    ButtonCancel(){
        var closeButton = document.getElementById('button_close');
        closeButton.style.display = 'none';
        document.getElementById('custom_search_input').value = '';
    }
});

