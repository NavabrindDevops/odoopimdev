/** @odoo-module **/

import { registry } from "@web/core/registry";
import { createElement, append } from "@web/core/utils/xml";
import { Notebook } from "@web/core/notebook/notebook";
import { formView } from "@web/views/form/form_view";
import { FormCompiler } from "@web/views/form/form_compiler";
import { FormRenderer } from "@web/views/form/form_renderer";
import { FormController } from '@web/views/form/form_controller';
import { useService } from "@web/core/utils/hooks";
import { Component, EventBus, onWillStart, useSubEnv, useRef, useState} from "@odoo/owl";
import { useSortable } from "@web/core/utils/sortable_owl";
import { fuzzyLookup } from "@web/core/utils/search";
import { ControlPanel } from "@web/search/control_panel/control_panel";

class categoryController extends FormController {
   setup() {
        super.setup();
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.channels = [];
        this.profiles= [];
        this.unassigned_accounts= [];
        this.profileAccounts = [];
        this.accounts= [];
        this.rootRef = useRef("root");
        this.account_list = [];
        self=this;
        this.searchRef = useRef("search");
        this.state = useState({
            currentChannel: [],
            channelName: '',
            selectedProfileId:  [],
            profiles: [],
            profileAccounts: [],
            unassigned_accounts: [],
            accounts: [],
            isSmall: this.env.isSmall,
            selectedAccounts: [],
            edit_allowed : [],
            categories:'',
            addMode:false,
            currentAddCateg:''
        });

        useSubEnv({
            overviewBus: new EventBus(),
        });
        self.getCategories();

        onWillStart(async () => {

        });
        document.addEventListener('dragstart',this.ondragaccount);
        document.addEventListener("dragover", (ev) => {
          ev.preventDefault();
        });
        document.addEventListener("drop", this.ondropevent);
    }
//            const channel = await this.orm.searchRead("channel.info", [['id','=',this.props.resId]],   ["name"]);
//            this.state.channelName = channel[0].name;
//            if (this.channels.length){
//                this.state.edit_allowed = await self.orm.call('channel.info','check_access', [this.props.resId]);
//            }
//            this.getProfiles();
//    async onPagerUpdate({ offset, resIds }) {
//                const res = super.onPagerUpdate(...arguments);
//                await this.getChannels(resIds[offset]);
//                return res;
//    }

    async ondragaccount(ev){
               console.log("source", ev.target.id);
               ev.dataTransfer.clearData();
               ev.dataTransfer.setData("text/plain", ev.target.id);
    }

    async ondropevent(ev){
                ev.preventDefault();
                const data = ev.dataTransfer.getData("text");
                console.log("drop event",data)
                const account = document.getElementById(data);
                const element = document.getElementById(ev.target.id);
                console.log(data,account,element,ev.target.id)
                const res = await  self.orm.call('pim.category','update_parent_category', [self.props.resId,Number(data),Number(ev.target.id)]);
                self.state.categories = res;

//                if (ev.target.closest(".container")){
//                    const profile = ev.target.closest(".container");
//                    if(profile){
//                            try{
//                                const res = await  self.orm.call('res.partner','update_profile', [Number(account.id),Number(account.id),Number(profile.id),self.props.resId]);
//                                const account_name = self.state.accounts.find(({ id }) => id === Number(account.id)).name;
//                                self.state.selectedAccounts.push({'id':Number(account.id),'name':account_name});
//                                self.state.profileAccounts[profile.id].push({'id':account.id,'name':account_name})
////                                const item = self.state.accounts.findIndex(({ id }) => id === Number(account.id));
////                                self.state.accounts.splice(item, 1);
//                            }
//                            catch{}
//                    }
//                }
    }
    async getCategories(){
        var jstreeData = await this.orm.call('pim.category', "return_categories_hierarchy", [1]);
        Object.assign(this.state, { categories: jstreeData });
        console.log("jstreeData ",jstreeData )
    }
     async show_child_categ(target){
        const ele = target.closest('li')
        if (ele.classList.contains("jstree-closed")){
            ele.classList.remove("jstree-closed");
            ele.classList.add("jstree-open");
        }

        else if (ele.classList.contains("jstree-open")){
            ele.classList.remove("jstree-open");
            ele.classList.add("jstree-closed");
        }
    }
    async open_categ(target){
        const ele = target.closest('li')
        if (ele.classList.contains("jstree-closed")){
            ele.classList.remove("jstree-closed");
            ele.classList.add("jstree-open");
        }
        if (ele.classList.contains("jstree-leaf")){
            ele.classList.remove("jstree-leaf");
            ele.classList.add("jstree-open");
        }
    }

    SelectCategory(categ_id){
        console.log("SelectCategory",categ_id)
        cat_dialog.state.SelectedCategory = categ_id;
    }

    async addCatgeory(ev,categ_id){
               this.open_categ(ev.target);
//               this.state.addMode != true ||
               if (categ_id != this.state.currentAddCateg){
                    const parentLi = ev.target.closest("li")
                    var ul = parentLi.querySelector("ul");
                    if (!ul){
                        console.log("ullllllllllll")
                        ul = document.createElement("ul");
                        ul.classList.add("jstree-children");
                        parentLi.appendChild(ul);


                    }
                    console.log("ullll",ul);
                    if (!this.state.currentAddCateg){
                        if (ul) {
                              const newLi = document.createElement("li");
                              newLi.classList.add("my-class");
                              const input = document.createElement("input");
                              input.type = "text";
                              input.placeholder = "Enter text";
                              newLi.id = "my-id";
                              newLi.appendChild(input);
                              ul.appendChild(newLi);
                            }
                            this.state.currentAddCateg = categ_id;
                   }
                   else{
                        const liToMove = document.querySelector(".my-class");
                        if (liToMove && ul) {
                          ul.appendChild(liToMove);
                        }
                        this.state.currentAddCateg = categ_id;

                   }

                    this.state.addMode = true;
               }
      }
//    onDoubleClick(id) {
//        if (!this.isAccountSelected(id)) {
//            this.onAddItem(id);
//        }
//    }
//    onAddItem(accountId,accountName) {
//        this.state.profileAccounts.push({'id':accountId,'name':accountName});
//        this.orm.call("res.partner", "update_profile", [accountId,accountId,this.selectedProfileId,this.props.resId]);
//    }
    isAccountSelected(current) {
        return this.state.selectedAccounts.find(({ id }) => id === current);
    }
    get isDebug() {
        return Boolean(odoo.debug);
    }

    async getProfiles(){
            const profiles =  await this.orm.searchRead("customer.profile", [['channel_id','=',this.props.resId]],   ["id", "name","description","default_rule_id"]);
            this.state.profiles = Object.values(profiles);
            for (const profile of profiles) {
            console.log("default_rule",profile.default_rule_id,profile.default_rule_id.length)
                if (!profile.default_rule_id.length){
                    return self.actionService.doAction({
                        name: "Edit Pricing Rule",
                        type: "ir.actions.act_window",
                        res_model: "pricing.rules",
                        view_mode: "form",
                        views: [[false, "form"]],
                        target: "new",
                        context:{'default_profile_id':Number(profile.id),'default_channel_id':this.props.resId,
                                'default_wizard_message':"<h3>New Profile " +profile.name+" Created Successfully!!</h3><h3>Create a new default Pricing Rule for your new profile.</h3>",
                                 'default_return_type':'channel',
                                 'default_is_default_rule':true
                        }
                    });
                }
            }
    }
    async onRecordSaved(record, changes) {
        await super.onRecordSaved(...arguments);
         console.log("record saved",this.props);
        const profiles =  await this.orm.searchRead("customer.profile", [['channel_id','=',this.props.resId]],   ["id", "name"]);
        this.state.profiles = Object.values(profiles);
        this.state.currentChannel = this.model.root.resId;
    }
    onRemoveItemExportList(account_id,acc_name,profile_id) {
        const item = this.state.selectedAccounts.findIndex(({ id }) => id === account_id);
        this.state.selectedAccounts.splice(item, 1);
        const profile_account = this.state.profileAccounts[profile_id].findIndex(({ id }) => id === account_id);
        this.state.profileAccounts[profile_id].splice(profile_account, 1);
        this.orm.call("res.partner", "update_profile", [account_id,account_id,false,self.props.resId]);
        const acc_item = this.state.accounts.findIndex(({ id }) => id === account_id);
    }

    async onAddProfile(){
        self.getProfiles();
        if (self.state.currentChannel){
            return self.actionService.doAction({
                name: "Edit Profile",
                type: "ir.actions.act_window",
                res_model: "customer.profile",
                view_mode: "form",
                views: [[false, "form"]],
                target: "new",
                context:{'default_channel_id':self.state.currentChannel}
            });
        }
        else{
            return self.actionService.doAction({
            type: "ir.actions.client",
            tag: "display_notification",
            params: {
                "message": "Create Channel before adding Pricing Profile",
                "type":"warning"
            },
        });
        }

    }



}

export class categoryControlPanel extends ControlPanel {
    static template = "categoryFormControlPanel";
}


categoryController.template = "categoryFormView";
const categoryFormView = {
    ...formView,
    ControlPanel: categoryControlPanel,
    Controller: categoryController,
};
registry.category("views").add("category_form_view", categoryFormView);
