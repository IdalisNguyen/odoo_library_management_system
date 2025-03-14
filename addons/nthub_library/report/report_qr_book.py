from odoo import models, fields, api

class ReportBookCopyLabels(models.AbstractModel):
    _name = 'report.nthub_library.report_book_copy_labels'
    _description = "Báo cáo in nhãn sách"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['report.nthub_library.report_book_copy_labels'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'report.nthub_library.report_book_copy_labels',
            'docs': docs,
        }
