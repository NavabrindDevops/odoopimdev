/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ImportAction } from "@base_import/import_action/import_action";
import { useService } from "@web/core/utils/hooks";

patch(ImportAction.prototype, {
    setup() {
        super.setup();
        console.log("Setup complete for ImportAction.");
        this.rpcService = useService('rpc'); // Correct initialization of the RPC service
    },

    // Function to extract the model name from the URL
    _getModelNameFromUrl(url) {
        const match = url.match(/model=([^&]+)/);
        return match ? match[1] : null;
    },

    // Function to fetch ir.attachment data and compare with current model name
    async _fetchAndPrintAllAttachments() {
        const currentUrl = window.location.href;
        const modelName = this._getModelNameFromUrl(currentUrl); // Get the current model name
        console.log("Current model name:", modelName);

        // Prepare the RPC call parameters
        const params = {
            model: 'ir.attachment',
            method: 'search_read',
            args: [[], ['name_model', 'datas']],  // Fetch all records
            kwargs: {},  // Explicitly pass kwargs even if empty
        };

        // Perform the RPC call to fetch all attachments
        const attachments = await this.rpcService('/web/dataset/call_kw', params);

        if (attachments.length) {
            console.log("All attachments found:");
            let matchingAttachment = null; // To store the matching attachment

            // Check each attachment's name_model against the current model name
            attachments.forEach(attachment => {
                console.log("Attachment Name:", attachment.name_model); // Print each attachment's name
                if (attachment.name_model === modelName) {
                    console.log("Matching attachment found:", attachment);
                    matchingAttachment = attachment; // Store the matching attachment
                }
            });

            // If a matching attachment is found, show its data
            if (matchingAttachment) {
                this._showAttachment(matchingAttachment.datas); // Show the attachment data
            } else {
                // Display a validation message if no matching attachment is found
                this._showValidationMessage("No matching attachment found for model: " + modelName);
            }
        } else {
            // Display a validation message if no attachments are found
            this._showValidationMessage("No attachments found.");
        }
    },

    // Function to handle showing validation messages
    _showValidationMessage(message) {
        alert(message); // Simple alert for demonstration purposes
    },

    // Function to handle showing attachment data
    _showAttachment(attachmentData) {
        if (!attachmentData) {
            console.log("No attachment data available.");
            return;
        }
        const link = document.createElement('a');
        link.href = 'data:application/octet-stream;base64,' + attachmentData; // Base64 encoding for download
        link.download = 'attachment_data.xlsx'; // You can change the file type or name
        link.click();
    },

    // Button action to fetch and show all attachments
    async _example_excel_sheet() {
        console.log("Fetching all attachments...");
        await this._fetchAndPrintAllAttachments();
    },
});
