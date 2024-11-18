/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { ProductListController, ProductListRenderer } from "@pim_view_preference_button/js/pim_view_preference";
import { useService } from "@web/core/utils/hooks";


patch(ProductListController.prototype, {
    setup() {
       super.setup();
       this.actionService = useService("action");
       },

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
        },

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

});



ProductListController.template = "pim_toggle_button.PimDiscontinueButtonListView";
//PimListController.template = "pim_view_preference_button.PimDiscontinueButtonListView";

//patch(PimListRenderer.prototype,{
//
//});
