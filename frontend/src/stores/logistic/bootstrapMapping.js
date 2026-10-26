// Maps the GET /logistics/bootstrap payload onto the shapes the logistics store keeps.
// Every section is a plain array or object, so the mapping is testable without Pinia.
import { asArray, asStringId, asWarehouseId, mapReturnRecord } from './mappers'

/** Bootstrap sections keyed by the store field each one fills. */
export function mapBootstrap(payload, normalizeUserRecord) {
    const stats = payload.dashboard_stats || {}

    const dashboardStats = {
        ordersToday: stats.orders_today || 0,
        activeDeliveries: stats.active_deliveries || 0,
        processing: stats.processing || 0,
        deliverySuccess: stats.delivery_success || 0,
        revenueToday: stats.revenue_today || 0,
        ordersTrend: stats.orders_trend || 0,
        revenueTrend: stats.revenue_trend || 0,
        slaCompliance: { week: asArray(stats.sla_week), month: asArray(stats.sla_week) },
        revenue: { week: asArray(stats.revenue_week), month: asArray(stats.revenue_week) },
        orders: { week: asArray(stats.orders_week), month: asArray(stats.orders_week) },
    }

    const hubs = asArray(payload.hubs).map((hub) => ({
        id: asStringId(hub.id),
        hubCode: hub.hub_code,
        name: hub.name,
        location: hub.location,
        address: hub.address,
        lat: hub.lat || null,
        lng: hub.lng || null,
        manager: hub.manager,
        managerInitials: hub.manager_initials,
        capacity: hub.capacity,
        efficiency: hub.efficiency,
        staffActive: hub.staff_active,
        staffTotal: hub.staff_total,
        vehiclesActive: hub.vehicles_active,
        vehiclesTotal: hub.vehicles_total,
        processRate: hub.process_rate,
        status: hub.status || 'Active',
        isActive: (hub.status || 'Active') !== 'Archived',
        statusColor: hub.status_color,
        bg: hub.bg,
    }))

    const alerts = asArray(payload.alerts).map((alert) => ({
        id: asStringId(alert.id),
        type: alert.type,
        title: alert.title,
        description: alert.description,
        severity: alert.severity,
        icon: alert.icon || 'warning',
        timestamp: alert.timestamp,
    }))

    const drivers = asArray(payload.drivers).map((driver) => ({
        id: asStringId(driver.id),
        hubId: asWarehouseId(driver.hub_id ?? driver.hubId),
        name: driver.name,
        status: driver.status || 'Active',
        location: driver.location || '',
        vehicle: driver.vehicle || '',
        efficiency: Number(driver.efficiency ?? 0),
        rating: Number(driver.rating ?? 0),
        safetyIncidents: Number(driver.safety_incidents ?? driver.safetyIncidents ?? 0),
        fuelEfficiencyScore: driver.fuel_efficiency_score || driver.fuelEfficiencyScore || '',
        avgSpeed: driver.avg_speed || driver.avgSpeed || '',
        phone: driver.phone || '',
        currentJob: driver.current_job || driver.currentJob || '',
        avatarColor: driver.avatar_color || driver.avatarColor || 'bg-blue-600',
        chatHistory: asArray(driver.chat_history ?? driver.chatHistory),
    }))

    const topDrivers = asArray(payload.top_drivers).map((driver) => {
        const linkedDriver = drivers.find((item) =>
            item.id === asStringId(driver.id) || item.name === driver.name
        )

        return {
            id: asStringId(driver.id),
            hubId: asWarehouseId(driver.hubId ?? driver.hub_id ?? linkedDriver?.hubId),
            name: driver.name,
            rating: Number(driver.rating ?? linkedDriver?.rating ?? 0),
            trips: Number(driver.trips ?? 0),
            ontime: Number(driver.ontime ?? 0),
            avatar: driver.avatar || null,
            avatarColor: linkedDriver?.avatarColor || 'bg-blue-600',
            status: linkedDriver?.status || 'Active',
            vehicle: linkedDriver?.vehicle || '',
            currentJob: linkedDriver?.currentJob || '',
        }
    })

    const vehicles = asArray(payload.vehicles).map((vehicle) => ({
        id: asStringId(vehicle.id),
        hubId: asWarehouseId(vehicle.hub_id ?? vehicle.hubId),
        code: vehicle.code || asStringId(vehicle.id),
        type: vehicle.type || vehicle.vehicle_type || '',
        model: vehicle.model || '',
        year: vehicle.year || null,
        licensePlate: vehicle.license_plate || vehicle.licensePlate || '',
        status: vehicle.status || 'Active',
        driver: vehicle.driver || 'Unassigned',
        fuelEfficiency: vehicle.fuel_efficiency || vehicle.fuelEfficiency || '',
        mileage: vehicle.mileage ?? 0,
        nextService: vehicle.next_service || vehicle.nextService || '',
        issue: vehicle.maintenance_issue || vehicle.issue || null,
        fuelLevelPct: vehicle.fuel_level_pct ?? vehicle.fuelLevelPct ?? null,
        rangeKm: vehicle.range_km ?? vehicle.rangeKm ?? null,
        seatCapacity: vehicle.seat_capacity ?? vehicle.seatCapacity ?? null,
        cargoCapacityTons: vehicle.cargo_capacity_tons ?? vehicle.cargoCapacityTons ?? null,
        telemetryStatus: vehicle.telemetry_status || vehicle.telemetryStatus || null,
        telemetryLastSeen: vehicle.telemetry_last_seen || vehicle.telemetryLastSeen || null,
    }))

    const maintenance = asArray(payload.maintenance).map((item) => ({
        id: asStringId(item.id),
        hubId: asWarehouseId(item.hub_id ?? item.hubId),
        issue: item.issue || '',
        status: item.status || '',
        statusClass: item.status_class || item.statusClass || '',
    }))

    const users = asArray(payload.users).map(normalizeUserRecord)

    const returns = asArray(payload.returns).map(mapReturnRecord)

    const equipmentLedger = asArray(payload.equipment_ledger).map((eq) => ({
        id: asStringId(eq.id),
        hubId: asWarehouseId(eq.hub_id),
        itemType: eq.item_type,
        issuedCount: eq.issued_count,
        returnedCount: eq.returned_count,
        referenceCode: eq.reference_code,
        status: eq.status,
    }))

    const zones = asArray(payload.zones).map((zone) => ({
        id: asStringId(zone.id),
        hubId: asWarehouseId(zone.hub_id),
        name: zone.name,
        type: zone.type,
        radius: zone.radius,
        status: zone.status,
        color: zone.color,
        lat: zone.lat ?? null,
        lng: zone.lng ?? null,
    }))

    const chats = asArray(payload.chats).map((chat) => ({
        id: asStringId(chat.id),
        hubId: asWarehouseId(chat.hub_id),
        name: chat.name,
        time: chat.time,
        lastMessage: chat.last_message,
        status: chat.status,
        phone: chat.phone,
        muted: chat.muted,
        messages: asArray(chat.messages),
    }))

    const escalations = asArray(payload.escalations).map((item) => ({
        id: asStringId(item.id),
        hubId: asWarehouseId(item.hub_id),
        title: item.title,
        priority: item.priority,
        from: item.from_name,
        role: item.role,
        time: item.time,
        description: item.description,
        actionDetails: item.action_details,
        status: item.status,
    }))

    const inventory = asArray(payload.inventory).map((item) => ({
        ...item,
        id: asStringId(item.id),
        hubId: asWarehouseId(item.hubId),
    }))

    const notifications = asArray(payload.notifications).map((item) => ({
        id: asStringId(item.id),
        title: item.title,
        message: item.message,
        time: item.time,
        createdAt: item.created_at,
        read: item.read,
        type: item.type,
    }))

    const tasks = asArray(payload.tasks).map((task) => ({
        id: asStringId(task.id),
        text: task.text,
        status: task.status,
        targetTime: task.target_time,
        repeat: task.repeat,
        createdAt: task.created_at,
        lastAlertTime: task.last_alert_time,
        silenced: task.silenced,
        remaining: '',
    }))

    const aiSuggestionChips = asArray(payload.ai_suggestion_chips)
    const aiMessages = asArray(payload.ai_messages).map((message, index) => ({
        id: message.id || `ai-${index}`,
        role: message.role,
        text: message.text,
        data: message.data || null,
        time: message.time,
    }))
    // Bootstrap correctly computes total_revenue, total_expenses, total_payroll_due, pending_cod
    const financeSummary = payload.finance_summary || {}

    // ── Transactions (Overview tab) ────────────────────────────────────────
    const transactions = asArray(payload.transactions).map((tx) => ({
        id: asStringId(tx.id),
        hubId: asWarehouseId(tx.hub_id),
        transactionCode: tx.transaction_code || '',
        date: tx.date,
        desc: tx.desc || tx.description || '',
        type: tx.type || tx.transaction_type || '',
        amount: Number(tx.amount ?? 0),
        status: tx.status || 'Completed',
        metadataJson: tx.metadata_json || {},
        relatedOrder: tx.related_order || null,
    }))

    // ── Report history (Reports > Analytics & History) ──────────────────────
    const reports = asArray(payload.reports).map((report) => ({
        id: asStringId(report.id),
        hubId: asWarehouseId(report.hub_id),
        title: report.title,
        date: report.date,
        icon: report.icon,
        color: report.color,
    }))

    const financeCodRecords = asArray(payload.finance_cod_records).map((item) => ({ ...item, id: asStringId(item.id), hubId: asWarehouseId(item.hubId ?? item.hub_id ?? item.warehouse_id) }))
    const financeStaffRecords = asArray(payload.finance_staff_records).map((item) => ({ ...item, id: asStringId(item.id), userId: asStringId(item.userId), hubId: asWarehouseId(item.hubId ?? item.hub_id ?? item.warehouse_id) }))
    const financeDriverRecords = asArray(payload.finance_driver_records).map((item) => ({ ...item, id: asStringId(item.id), userId: asStringId(item.userId), hubId: asWarehouseId(item.hubId ?? item.hub_id ?? item.warehouse_id) }))
    const fleetLogs = payload.fleet_logs || {}
    const vehicleDocuments = asArray(payload.vehicle_documents).map((item) => ({ ...item, id: asStringId(item.id), hubId: asWarehouseId(item.hubId ?? item.hub_id ?? item.warehouse_id) }))
    const driverDocuments = asArray(payload.driver_documents).map((item) => ({ ...item, id: asStringId(item.id), driverId: asStringId(item.driverId), hubId: asWarehouseId(item.hubId ?? item.hub_id ?? item.warehouse_id) }))
    const reportAiInsights = asArray(payload.report_ai_insights)
    const reportDamageClaims = asArray(payload.report_damage_claims)
    const reportSecurityLogs = asArray(payload.report_security_logs)
    const reportMetrics = payload.report_metrics || {}

    const creditBalance = transactions
        .filter((item) => item.amount > 0)
        .reduce((sum, item) => sum + item.amount, 0)

    return {
        dashboardStats,
        hubs,
        alerts,
        drivers,
        topDrivers,
        vehicles,
        maintenance,
        users,
        returns,
        equipmentLedger,
        zones,
        chats,
        escalations,
        inventory,
        notifications,
        tasks,
        aiSuggestionChips,
        aiMessages,
        financeSummary,
        transactions,
        reports,
        financeCodRecords,
        financeStaffRecords,
        financeDriverRecords,
        fleetLogs,
        vehicleDocuments,
        driverDocuments,
        reportAiInsights,
        reportDamageClaims,
        reportSecurityLogs,
        reportMetrics,
        creditBalance,
    }
}
