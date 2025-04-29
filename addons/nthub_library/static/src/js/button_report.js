/** @odoo-module **/

import { PivotRenderer } from "@web/views/pivot/pivot_renderer";
import { patch } from "@web/core/utils/patch";
import { download } from "@web/core/network/download";

patch(PivotRenderer.prototype,{
    /**
     * Thêm method mới để in Pivot theo mẫu Excel tự cấu hình
     */
    onClickDownloadCustomPivotXlsx() {
        if (this.model.getTableWidth() > 16384) {
            throw new Error(
                _t(
                    "For Excel compatibility, data cannot be exported if there are more than 16384 columns.\n\nTip: try to flip axis, filter further or reduce the number of measures."
                )
            );
        }
        const table = this.model.exportData();
        download({
            url: "/nthub_library/custom_borrow_report_xlsx",
            data: { data: JSON.stringify(table) },
        });
    },


});
