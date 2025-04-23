/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';

export class BookBorrowListController extends ListController {
   setup() {
       super.setup();
   }

   async OnTestClick() {
       const action = await this.orm.call(
           'books.borrows', 
           'check_reserve',
       );
       
       // Perform the action

       if (action) {
         this.actionService.doAction(action);
     }
   }
}

registry.category("views").add("button_check_reserve_in_tree", {
   ...listView,
   Controller: BookBorrowListController,
   buttonTemplate: "books_borrows.ListView.Buttons",
});