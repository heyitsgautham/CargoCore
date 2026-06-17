import sys
import re

path = 'c:/Users/pruth/Downloads/Login Signup Flow Design/src/LWD-views/LogisticManager/FleetManagement.vue'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update vehicleFormData initialization in openVehicleModal
open_vehicle_modal_orig = '''        vehicleFormData.value = {
            id: \VH-\\,
            licensePlate: '',
            model: '',
            type: 'Delivery Van',
            hubId: store.activeWarehouse === 'all' ? 1 : store.activeWarehouse,
            year: new Date().getFullYear()
        }'''

open_vehicle_modal_new = '''        vehicleFormData.value = {
            id: \VH-\\,
            licensePlate: '',
            model: '',
            type: 'Delivery Van',
            hubId: store.activeWarehouse === 'all' ? 1 : store.activeWarehouse,
            year: new Date().getFullYear(),
            insuranceExpiry: '',
            insuranceFile: null,
            insuranceFileName: '',
            registrationExpiry: '',
            registrationFile: null,
            registrationFileName: ''
        }'''

content = content.replace(open_vehicle_modal_orig, open_vehicle_modal_new)

# 2. Add File Handlers below openVehicleModal
file_handlers = '''
const handleVehicleDocUpload = (event, docType) => {
    const file = event.target.files[0]
    if (file) {
        const reader = new FileReader()
        reader.onload = (e) => {
            if (docType === 'insurance') {
                vehicleFormData.value.insuranceFile = e.target.result
                vehicleFormData.value.insuranceFileName = file.name
            } else if (docType === 'registration') {
                vehicleFormData.value.registrationFile = e.target.result
                vehicleFormData.value.registrationFileName = file.name
            }
        }
        reader.readAsDataURL(file)
    }
}
'''
content = content.replace('const closeVehicleModal = () => {', file_handlers + '\nconst closeVehicleModal = () => {')


# 3. Modify submitVehicle
submit_vehicle_orig = '''const submitVehicle = () => {
    if (vehicleModalMode.value === 'add') {
        store.addVehicle({ ...vehicleFormData.value })
    } else {
        // Mock update handler
        // store.updateVehicle({...})
    }
    closeVehicleModal()
}'''

submit_vehicle_new = '''const submitVehicle = async () => {
    if (vehicleModalMode.value === 'add') {
        await store.addVehicle({ ...vehicleFormData.value })
        
        let targetHub = vehicleFormData.value.hubId
        if (targetHub === 'all' || targetHub === 1) targetHub = null

        if (vehicleFormData.value.insuranceFile && vehicleFormData.value.insuranceExpiry) {
            await store.uploadDocument({
                entity_type: 'VEHICLE',
                entity_id: vehicleFormData.value.id,
                hub_id: targetHub,
                doc_type: 'Insurance Policy',
                document_url: vehicleFormData.value.insuranceFile,
                expiry_date: new Date(vehicleFormData.value.insuranceExpiry).toISOString()
            })
        }
        
        if (vehicleFormData.value.registrationFile && vehicleFormData.value.registrationExpiry) {
            await store.uploadDocument({
                entity_type: 'VEHICLE',
                entity_id: vehicleFormData.value.id,
                hub_id: targetHub,
                doc_type: 'Vehicle Registration',
                document_url: vehicleFormData.value.registrationFile,
                expiry_date: new Date(vehicleFormData.value.registrationExpiry).toISOString()
            })
        }
    } else {
        // Mock update handler
    }
    closeVehicleModal()
}'''
content = content.replace(submit_vehicle_orig, submit_vehicle_new)

# 4. Inject Form HTML for Documents in Add Mode
hub_html_orig = '''                        <div v-if=\"vehicleModalMode === 'add'\">
                            <label class=\"block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1\">Hub
                                Assignment</label>
                            <div class=\"relative\">
                                <select v-model=\"vehicleFormData.hubId\"
                                    class=\"w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50\">
                                    <option value=\"all\" class=\"bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100\">Global (All Warehouses)</option>
                                    <option v-for=\"h in store.hubs\" :key=\"h.id\" :value=\"h.id\" class=\"bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100\">{{ h.name }}</option>
                                </select>
                            </div>
                        </div>'''

hub_html_new = hub_html_orig + '''

                        <!-- Required Documentation Section -->
                        <div v-if=\"vehicleModalMode === 'add'\" class=\"border-t border-gray-200 dark:border-white/10 pt-4 mt-6 space-y-4\">
                            <h4 class=\"text-xs font-bold text-gray-500 uppercase tracking-wider mb-2\">Required Documents</h4>
                            
                            <!-- Insurance Policy -->
                            <div class=\"bg-gray-50 dark:bg-white/5 p-4 rounded-xl space-y-3\">
                                <p class=\"text-xs font-bold text-gray-900 dark:text-white\">Insurance Policy</p>
                                <div class=\"grid grid-cols-2 gap-3\">
                                    <div>
                                        <label class=\"block text-[10px] text-gray-500 mb-1\">Expiry Date</label>
                                        <input type=\"date\" v-model=\"vehicleFormData.insuranceExpiry\" class=\"w-full text-xs bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50\">
                                    </div>
                                    <div>
                                        <label class=\"block text-[10px] text-gray-500 mb-1\">Upload File</label>
                                        <label class=\"w-full flex items-center justify-center gap-2 cursor-pointer bg-white dark:bg-black/20 hover:bg-gray-50 dark:hover:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-xs font-medium text-gray-600 dark:text-gray-300 transition-colors\">
                                            <span class=\"material-symbols-outlined text-[14px]\">upload</span>
                                            <span class=\"truncate\">{{ vehicleFormData.insuranceFileName || 'Attach Policy' }}</span>
                                            <input type=\"file\" class=\"hidden\" accept=\"image/*,.pdf\" @change=\"e => handleVehicleDocUpload(e, 'insurance')\">
                                        </label>
                                    </div>
                                </div>
                            </div>

                            <!-- Vehicle Registration -->
                            <div class=\"bg-gray-50 dark:bg-white/5 p-4 rounded-xl space-y-3\">
                                <p class=\"text-xs font-bold text-gray-900 dark:text-white\">Vehicle Registration</p>
                                <div class=\"grid grid-cols-2 gap-3\">
                                    <div>
                                        <label class=\"block text-[10px] text-gray-500 mb-1\">Expiry Date</label>
                                        <input type=\"date\" v-model=\"vehicleFormData.registrationExpiry\" class=\"w-full text-xs bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50\">
                                    </div>
                                    <div>
                                        <label class=\"block text-[10px] text-gray-500 mb-1\">Upload File</label>
                                        <label class=\"w-full flex items-center justify-center gap-2 cursor-pointer bg-white dark:bg-black/20 hover:bg-gray-50 dark:hover:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-xs font-medium text-gray-600 dark:text-gray-300 transition-colors\">
                                            <span class=\"material-symbols-outlined text-[14px]\">upload</span>
                                            <span class=\"truncate\">{{ vehicleFormData.registrationFileName || 'Attach Registration' }}</span>
                                            <input type=\"file\" class=\"hidden\" accept=\"image/*,.pdf\" @change=\"e => handleVehicleDocUpload(e, 'registration')\">
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>'''

content = content.replace(hub_html_orig, hub_html_new)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Add Vehicle flow patched successfully!')
