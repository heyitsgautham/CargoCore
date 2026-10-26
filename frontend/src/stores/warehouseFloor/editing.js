// Edit-mode changes to floors, sections, racks, categories and compared zones.
export function useFloorPlanEditing({
    comparedZones,
    floors,
    groups,
    idCounter,
    products,
    racks,
    sections,
}) {
    function addFloor() {
        const nid = Math.max(...floors.value.map(f => f.id), 0) + 1
        floors.value.push({ id: nid, label: `Floor ${nid}` })
        return nid
    }

    function deleteFloor(floorId) {
        if (floors.value.length <= 1) return false
        const rackIds = racks.value
            .filter(r => sections.value.find(s => s.id === r.sectionId)?.floorId === floorId)
            .map(r => r.id)
        products.value = products.value.filter(p => !rackIds.includes(p.rackId))
        racks.value = racks.value.filter(r => !rackIds.includes(r.id))
        sections.value = sections.value.filter(s => s.floorId !== floorId)
        groups.value = groups.value.filter(g => g.floorId !== floorId)
        floors.value = floors.value.filter(f => f.id !== floorId)
        return true
    }

    function renameFloor(floorId, newLabel) {
        const f = floors.value.find(fl => fl.id === floorId)
        if (f && newLabel.trim()) f.label = newLabel.trim()
    }

    function addSection(floorId) {
        const id = 'c' + (idCounter.value++)
        sections.value.push({
            id,
            floorId,
            groupId: null,
            label: `SEC-${idCounter.value}`,
            x: 80 + Math.random() * 200,
            y: 80 + Math.random() * 200,
            w: 120,
            h: 140
        })
        return id
    }

    function deleteSection(sectionId) {
        const rackIds = racks.value.filter(r => r.sectionId === sectionId).map(r => r.id)
        products.value = products.value.filter(p => !rackIds.includes(p.rackId))
        racks.value = racks.value.filter(r => r.sectionId !== sectionId)
        sections.value = sections.value.filter(s => s.id !== sectionId)
    }

    function addRack(sectionId) {
        const id = 'r' + (idCounter.value++)
        racks.value.push({
            id,
            sectionId,
            label: `Rack-${idCounter.value}`,
            x: 30 + Math.random() * 100,
            y: 30 + Math.random() * 100,
            w: 180,
            h: 110,
            cols: 4,
            rows: 3
        })
        return id
    }

    function deleteRack(rackId) {
        products.value = products.value.filter(p => p.rackId !== rackId)
        racks.value = racks.value.filter(r => r.id !== rackId)
    }

    function addGroup(floorId, data) {
        const id = 'g' + Date.now()
        groups.value.push({ id, floorId, ...data })
        return id
    }

    function updateGroup(groupId, data) {
        const g = groups.value.find(g => g.id === groupId)
        if (g) Object.assign(g, data)
    }

    function deleteGroup(groupId) {
        sections.value.forEach(s => { if (s.groupId === groupId) s.groupId = null })
        groups.value = groups.value.filter(g => g.id !== groupId)
    }

    function addComparedZone(zoneId) {
        if (!comparedZones.value.find(z => z.id === zoneId)) {
            const zone = groups.value.find(g => g.id === zoneId)
            if (zone) {
                comparedZones.value.push(zone)
            }
        }
    }

    function removeComparedZone(zoneId) {
        comparedZones.value = comparedZones.value.filter(z => z.id !== zoneId)
    }

    return {
        addFloor,
        deleteFloor,
        renameFloor,
        addSection,
        deleteSection,
        addRack,
        deleteRack,
        addGroup,
        updateGroup,
        deleteGroup,
        addComparedZone,
        removeComparedZone,
     }
}
