// The add and edit vehicle modal, including the insurance and registration
// files that upload as documents once a new vehicle exists.
import { ref } from 'vue'

export function useVehicleForm(store) {
    const isVehicleModalOpen = ref(false)
    const vehicleModalMode = ref('add') // 'add' or 'edit'
    const isSubmitting = ref(false)
    const vehicleFormData = ref({})

    const openVehicleModal = (mode, vehicle = null) => {
        vehicleModalMode.value = mode
        if (mode === 'edit' && vehicle) {
            // Find the driver currently assigned to this vehicle
            const assignedDriver = store.filteredDrivers.find(d => d.vehicle === vehicle.code || d.vehicle === vehicle.id)
            vehicleFormData.value = { ...vehicle, driverId: assignedDriver?.id || null }
        } else {
            vehicleFormData.value = {
                id: `VH-${Math.floor(Math.random() * 9000) + 1000}`,
                licensePlate: '',
                model: '',
                type: 'Delivery Van',
                hubId: store.activeWarehouse === 'all' ? 1 : store.activeWarehouse,
                year: new Date().getFullYear(),
                driverId: null,
            }
        }
        isVehicleModalOpen.value = true
    }


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

    const closeVehicleModal = () => {
        isVehicleModalOpen.value = false
        vehicleFormData.value = {}
    }

    const submitVehicle = async () => {
        try {
            isSubmitting.value = true
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
                await store.updateVehicle(vehicleFormData.value.id, {
                    model: vehicleFormData.value.model,
                    license_plate: vehicleFormData.value.licensePlate,
                    assigned_driver_id: vehicleFormData.value.driverId || null,
                })
            }
        } finally {
            isSubmitting.value = false
            closeVehicleModal()
        }
    }

    return {
        isVehicleModalOpen,
        vehicleModalMode,
        isSubmitting,
        vehicleFormData,
        openVehicleModal,
        handleVehicleDocUpload,
        closeVehicleModal,
        submitVehicle,
    }
}
