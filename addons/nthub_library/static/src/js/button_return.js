/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';

export class SaleListController extends ListController {
   setup() {
       super.setup();
   }

   async OnTestClick() {
       const action = await this.orm.call(
           'library.card', 
           'process_return',
       );
       
       // Perform the action

       if (action) {
         this.actionService.doAction(action);
     }
   }
}

registry.category("views").add("button_in_tree", {
   ...listView,
   Controller: SaleListController,
   buttonTemplate: "library_card.ListView.Buttons",
});