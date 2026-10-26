// Allowed state transitions for each driver job type.
// Each state lists the states a job may move to next, and COMPLETED ends the job.
export const fsmConfig = {
    PARCEL_DELIVERY: {
        IDLE: ['ASSIGNED'],
        ASSIGNED: ['LOAD_VERIFICATION'],
        LOAD_VERIFICATION: ['START_ROUTE'],
        START_ROUTE: ['IN_TRANSIT'],
        IN_TRANSIT: ['ARRIVED'],
        ARRIVED: ['DELIVERY_IN_PROGRESS'],
        DELIVERY_IN_PROGRESS: ['SERVICE_CHECKLIST', 'DELIVERY_EXCEPTION'],
        SERVICE_CHECKLIST: ['POD_CAPTURE'],
        POD_CAPTURE: ['COD_COLLECTION', 'NEXT_STOP', 'COMPLETED'],
        COD_COLLECTION: ['NEXT_STOP', 'COMPLETED'],
        NEXT_STOP: ['IN_TRANSIT'],
        DELIVERY_EXCEPTION: ['IN_TRANSIT', 'COMPLETED'],
        COMPLETED: []
    },
    PARCEL_PICKUP: {
        IDLE: ['ASSIGNED'],
        ASSIGNED: ['START_ROUTE'],
        START_ROUTE: ['IN_TRANSIT_TO_PICKUP'],
        IN_TRANSIT_TO_PICKUP: ['ARRIVE_PICKUP'],
        ARRIVE_PICKUP: ['SCAN_ITEMS'],
        SCAN_ITEMS: ['PICKUP_SIGNATURE'],
        PICKUP_SIGNATURE: ['LOAD_CONFIRM'],
        LOAD_CONFIRM: ['RETURN_TRANSIT'],
        RETURN_TRANSIT: ['WAREHOUSE_ARRIVAL'],
        WAREHOUSE_ARRIVAL: ['UNLOAD_VERIFY'],
        UNLOAD_VERIFY: ['COMPLETED'],
        COMPLETED: []
    },
    HOUSE_SHIFT: {
        IDLE: ['ASSIGNED'],
        ASSIGNED: ['CREW_CHECKIN'],
        CREW_CHECKIN: ['START_ROUTE'],
        START_ROUTE: ['IN_TRANSIT_TO_SOURCE'],
        IN_TRANSIT_TO_SOURCE: ['ARRIVE_SOURCE'],
        ARRIVE_SOURCE: ['PACKING'],
        PACKING: ['LOADING_INVENTORY'],
        LOADING_INVENTORY: ['TRANSIT_TO_DEST'],
        TRANSIT_TO_DEST: ['ARRIVE_DEST'],
        ARRIVE_DEST: ['UNLOADING_INVENTORY'],
        UNLOADING_INVENTORY: ['FINAL_CHECKLIST'],
        FINAL_CHECKLIST: ['POC_CAPTURE'],
        POC_CAPTURE: ['PACKING_RETURN'],
        PACKING_RETURN: ['COMPLETED'],
        COMPLETED: []
    }
}

export const JOB_TYPE_LABELS = {
    'PARCEL_DELIVERY': 'Parcel Delivery',
    'PARCEL_PICKUP': 'Parcel Pickup',
    'HOUSE_SHIFT': 'House Shift'
}

export const JOB_TYPE_BADGE_COLORS = {
    'PARCEL_DELIVERY': 'bg-green-500',
    'PARCEL_PICKUP': 'bg-blue-500',
    'HOUSE_SHIFT': 'bg-purple-500'
}

// Driver-facing label for each job state.
export const STATE_LABELS = {
    'IDLE': 'Waiting',
    'ASSIGNED': 'Job Assigned',
    'LOAD_VERIFICATION': 'Load Verification',
    'START_ROUTE': 'Starting Route',
    'IN_TRANSIT': 'In Transit',
    'IN_TRANSIT_TO_PICKUP': 'En Route to Pickup',
    'IN_TRANSIT_TO_SOURCE': 'En Route to Source',
    'ARRIVE_PICKUP': 'Arrived at Pickup',
    'ARRIVE_SOURCE': 'Arrived at Source',
    'ARRIVED': 'Arrived',
    'DELIVERY_IN_PROGRESS': 'Delivering',
    'POD_CAPTURE': 'Capturing POD',
    'COD_COLLECTION': 'Collecting COD',
    'PICKUP_SIGNATURE': 'Getting Signature',
    'SCAN_ITEMS': 'Scanning Items',
    'LOAD_CONFIRM': 'Loading Confirmed',
    'RETURN_TRANSIT': 'Returning to Warehouse',
    'WAREHOUSE_ARRIVAL': 'At Warehouse',
    'UNLOAD_VERIFY': 'Unloading',
    'PACKING': 'Packing',
    'LOADING_INVENTORY': 'Loading',
    'TRANSIT_TO_DEST': 'In Transit',
    'ARRIVE_DEST': 'Arrived at Destination',
    'UNLOADING_INVENTORY': 'Unloading',
    'FINAL_CHECKLIST': 'Final Walkthrough',
    'POC_CAPTURE': 'Getting Sign-off',
    'NEXT_STOP': 'Moving to Next Stop',
    'DELIVERY_EXCEPTION': 'Exception Reported',
    'COMPLETED': 'Completed'
}

// Map FSM states to backend order statuses
export function mapStateToOrderStatus(state) {
    const stateMap = {
        'ASSIGNED': 'ASSIGNED',
        'LOAD_VERIFICATION': 'CONFIRMED',
        'START_ROUTE': 'IN_TRANSIT',
        'IN_TRANSIT': 'IN_TRANSIT',
        'IN_TRANSIT_TO_PICKUP': 'IN_TRANSIT',
        'IN_TRANSIT_TO_SOURCE': 'IN_TRANSIT',
        'ARRIVED': 'IN_TRANSIT',
        'ARRIVE_PICKUP': 'IN_TRANSIT',
        'ARRIVE_SOURCE': 'IN_TRANSIT',
        'ARRIVE_DEST': 'IN_TRANSIT',
        'DELIVERY_IN_PROGRESS': 'IN_TRANSIT',
        'POD_CAPTURE': 'IN_TRANSIT',
        'COMPLETED': 'DELIVERED',
    }
    return stateMap[state] || null
}
