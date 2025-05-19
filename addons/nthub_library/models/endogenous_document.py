from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import base64
import zipfile
import tempfile
import os
import pandas as pd
import logging
_logger = logging.getLogger(__name__)

class LibraryEndogenousDocument(models.Model):
    _name = 'library.endogenous_document'
    _description = 'Tài liệu Nội sinh'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    document_type = fields.Selection([
        ('luan_van', 'Luận văn'),
        ('luan_an', 'Luận án'),
        ('khoa_luan', 'Khóa luận'),
        ('bckh', 'Báo cáo khoa học'),
        ('khac', 'Khác'),
    ], string="Loại tài liệu", required=True, tracking=True)

    organization = fields.Many2one('library.organization', string="Đơn vị công tác / đào tạo")
    department = fields.Many2one('library.department', string="Ngành / Khoa")
    academic_year = fields.Char("Năm học / Năm bảo vệ")

    abstract = fields.Text("Tóm tắt nội dung")
    file = fields.Binary("Tệp đính kèm (PDF)", attachment=True)
    file_filename = fields.Char("Tên tệp")

    state = fields.Selection([
        ('draft', 'Nháp'),
        ('approved', 'Đã duyệt'),
        ('rejected', 'Từ chối'),
    ], default='draft', tracking=True)

    is_public = fields.Boolean("Công khai tra cứu?", default=True)

    import_zip_file = fields.Binary("Import ZIP", help="Upload zip chứa mapping.xlsx + file PDF")
    import_zip_filename = fields.Char("Tên tệp ZIP")
    import_preview_line_ids = fields.One2many(
        'library.endogenous_document.import.line',
        'temp_id',
        string="Xem trước file sẽ import"
    )
    is_assigned = fields.Boolean(string="Đã phân loại", default=False)
    
    def preview_import_zip(self):
        self.ensure_one()
        self.import_preview_line_ids.unlink()

        if not self.import_zip_file:
            raise ValidationError("Vui lòng chọn file ZIP.")

        zip_data = base64.b64decode(self.import_zip_file)
        with tempfile.TemporaryDirectory() as tmpdirname:
            zip_path = os.path.join(tmpdirname, 'upload.zip')
            with open(zip_path, 'wb') as f:
                f.write(zip_data)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdirname)

            # Đường dẫn file mapping
            mapping_path = os.path.join(tmpdirname, 'sample_endogenous_documents', 'mapping.xlsx')
            if not os.path.exists(mapping_path):
                raise ValidationError("Không tìm thấy file mapping.xlsx.")

            df = pd.read_excel(mapping_path)
            df = df.dropna(how='all')  # bỏ dòng rỗng hoàn toàn

            for _, row in df.iterrows():
                values = {'temp_id': self.id}
                is_valid = False

                for field in [
                    'name', 'document_type', 'author', 'code', 'department',
                    'major', 'academic_year', 'teacher', 'is_public', 'filename'
                ]:
                    val = row.get(field)
                    if pd.notna(val) and str(val).strip() != '':
                        values[field] = val
                        is_valid = True

                if not is_valid:
                    continue

                preview_line = self.env['library.endogenous_document.import.line'].create(values)

                # Gán file pdf tương ứng
                filename = row.get('filename')
                if filename:
                    filename = str(filename).strip().replace('–', '-').replace(u'\xa0', ' ')
                    pdf_path = None
                    for root, dirs, files in os.walk(tmpdirname):
                        for f in files:
                            if f.strip().lower() == filename.strip().lower():
                                pdf_path = os.path.join(root, f)
                                break
                        if pdf_path:
                            break

                    if pdf_path and os.path.exists(pdf_path):
                        with open(pdf_path, 'rb') as f:
                            pdf_binary = base64.b64encode(f.read())
                        preview_line.write({
                            'file_download': pdf_binary,
                            'file_download_name': filename,
                        })
                        _logger.info(f"--Đã gán file {filename} cho dòng import {preview_line.id}")
                    else:
                        _logger.warning(f"Không tìm thấy file {filename} trong ZIP.")
                                            
    def action_open_assign_location_wizard(self):
        self.ensure_one()
        return {
            'name': 'Phân loại tài liệu',
            'type': 'ir.actions.act_window',
            'res_model': 'library.endogenous_document.assign_location_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_document_id': self.id,
            }
        }


class EndogenousDocumentImportLine(models.TransientModel):
    _name = 'library.endogenous_document.import.line'
    _description = 'Preview dòng import tài liệu'

    temp_id = fields.Many2one('library.endogenous_document', string="Import")
    name = fields.Char("Tên tài liệu")
    document_type = fields.Char("Loại")
    author = fields.Char("Tác giả")
    code = fields.Char("Mã tài liệu")
    academic_year = fields.Char("Năm học")
    filename = fields.Char("Tên file PDF")
    major = fields.Char("Chuyên ngành")
    teacher = fields.Char("Giáo viên hướng dẫn")
    department = fields.Char("Khoa")
    is_public = fields.Boolean("Công khai tra cứu?", default=True)
    file_download = fields.Binary("Tải PDF", attachment=True)
    file_download_name = fields.Char("Tên tệp PDF")



class libraryorganization(models.Model):
    _name = 'library.organization'
    _description = 'Đơn vị công tác'
    
    name = fields.Char("Tên đơn vị", required=True)
    
class librarydepartment(models.Model):
    _name = 'library.department'
    _description = 'Ngành / Khoa'
    
    name = fields.Char("Tên ngành / khoa", required=True)
    
class AssignLocationWizard(models.TransientModel):
    _name = 'library.endogenous_document.assign_location_wizard'
    _description = 'Phân loại tài liệu nội sinh'

    document_id = fields.Many2one('library.endogenous_document', required=True, readonly=True)

    category_id = fields.Many2one('books.category', string="Danh mục chính", required=True)
    rack_id = fields.Many2one('library.rack', string="Giá sách", required=True)
    shelf_id = fields.Many2one('library.shelf', string="Kệ sách", required=True)
    
    def action_confirm_assign(self):
        BookData = self.env['books.data']
        BookCopies = self.env['book.copies']

        for line in self.document_id.import_preview_line_ids:
            # Tạo books.data nếu chưa có, hoặc tìm theo tên/tác giả
            book = BookData.create({
                'name': line.name,
                'rack_ids': self.rack_id.id,
                'shelf_ids': self.shelf_id.id,
                'category_ids': self.category_id.id,
            })

            # Tạo book.copies tương ứng
            BookCopies.create({
                'name': f"Bản sao của {line.name}",
                'book_id': book.id,
                'serial_number': line.code or book.name,
                'DK_CB': line.code,
                'library_shelf_id': self.shelf_id.id,
                'state': 'available',
                'library_rack_id': self.rack_id.id,
                'endogenous_document_id': True,
                'file_download': line.file_download
            })
        self.document_id.is_assigned = True
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'library.endogenous.import.success',
            'view_mode': 'form',
            'target': 'new',
            'name': 'Đã tạo thành công',
            'context': {
                'default_message': 'Đã tạo thành công các bản sao sách từ tài liệu nội sinh.'
            }
        }


class ImportSuccessMessage(models.TransientModel):
    _name = 'library.endogenous.import.success'
    _description = 'Thông báo thành công'

    message = fields.Text(string="Thông báo", default="Đã tạo các bản sao sách thành công!")


