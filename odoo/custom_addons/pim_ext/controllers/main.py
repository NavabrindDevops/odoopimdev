from odoo import http
from odoo.addons.html_editor.controllers.main import HTML_Editor
from odoo.http import request
import base64
import time
from werkzeug.utils import secure_filename
from odoo.addons.html_editor.tools import get_video_url_data
from odoo.http import Response
import json

class CustomHTML_Editor(HTML_Editor):

    @http.route(['/web_editor/video_url/data', '/html_editor/video_url/data'], type='json', auth='user', website=True)
    def video_url_data(self, video_url, autoplay=False, loop=False,
                       hide_controls=False, hide_fullscreen=False,
                       hide_dm_logo=False, hide_dm_share=False):
        # Check if the URL is an uploaded video (starts with /web/content/)
        if video_url.startswith('/web/content/'):
            # Extract attachment ID from URL (e.g., /web/content/123?...)
            try:
                attachment_id = int(video_url.split('/web/content/')[1].split('?')[0])
                attachment = request.env['ir.attachment'].browse(attachment_id).exists()
                if not attachment:
                    return {'error': 'Attachment not found'}

                # Return data for uploaded video
                return {
                    'embed_url': video_url,
                    'video_id': str(attachment_id),
                    'params': '',  # No additional params needed for uploaded videos
                    'platform': 'uploaded',  # Explicitly set platform
                }
            except (ValueError, IndexError):
                return {'error': 'Invalid uploaded video URL'}

        # Delegate to existing logic for external video platforms
        return get_video_url_data(
            video_url, autoplay=autoplay, loop=loop,
            hide_controls=hide_controls, hide_fullscreen=hide_fullscreen,
            hide_dm_logo=hide_dm_logo, hide_dm_share=hide_dm_share
        )

    @http.route('/web_editor/video_upload', type='http', auth='user', website=True, methods=['POST'], csrf=False)
    def video_upload(self, **kwargs):
        print("Entering video_upload function")  # Debugging print statement

        if 'file' not in request.httprequest.files:
            print("No file uploaded")  # Debugging print statement
            return request.make_json_response({'error': 'No file uploaded'}, status=400)

        file = request.httprequest.files['file']
        if not file:
            print("No file uploaded")  # Debugging print statement
            return request.make_json_response({'error': 'No file uploaded'}, status=400)

        # Sanitize the filename
        safe_filename = secure_filename(file.filename)
        print(f"Sanitized filename: {safe_filename}")  # Debugging print statement

        # Read the file content and encode it in base64
        file_content = file.read()
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        print("File read and encoded in base64")  # Debugging print statement

        # Determine MIME type
        mimetype = 'video/mp4'  # Default to MP4
        if safe_filename.lower().endswith('.webm'):
            mimetype = 'video/webm'
        elif safe_filename.lower().endswith('.ogg'):
            mimetype = 'video/ogg'
        print(f"Detected MIME type: {mimetype}")  # Debugging print statement

        try:
            # Create an ir.attachment record
            attachment = request.env['ir.attachment'].create({
                'name': safe_filename,
                'datas': file_base64,
                'res_model': 'html_editor.video',
                'res_id': 0,
                'type': 'binary',
                'mimetype': mimetype,
                'public': True,  # Make the attachment publicly accessible
            })
            print(f"Attachment created with ID: {attachment.id}")  # Debugging print statement

            # Generate the URL for the uploaded video
            video_url = f'/web/content/{attachment.id}?download=true&t={int(time.time())}'
            print(f"Generated video URL: {video_url}")  # Debugging print statement

            return request.make_json_response({'url': video_url, 'video_id': attachment.id})
        except Exception as e:
            print(f"Error creating attachment: {e}")  # Debugging print statement
            return request.make_json_response({'error': str(e)}, status=500)