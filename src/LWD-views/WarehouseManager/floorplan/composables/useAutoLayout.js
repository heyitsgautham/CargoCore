/**
 * Auto-layout engine for warehouse floor sections.
 * Clusters sections by group with configurable gap rules.
 */
export function useAutoLayout() {
    /**
     * Run auto-layout on sections for a given floor.
     * Arranges sections left-to-right, wrapping at maxWidth.
     *
     * @param {Array} sections - sections on the current floor
     * @param {Array} groups - groups on the current floor
     * @param {Object} [options]
     * @param {number} [options.startX=40]
     * @param {number} [options.startY=60]
     * @param {number} [options.maxWidth=1100]
     * @param {number} [options.rowGap=20]
     */
    function runAutoLayout(sections, groups, options = {}) {
        const { startX = 40, startY = 60, maxWidth = 1100, rowGap = 20 } = options

        // Separate manual vs auto sections
        const autoSections = sections.filter(s => !s.manualPosition)
        if (!autoSections.length) return

        // Group sections by groupId
        const groupMap = new Map()
        const ungrouped = []
        for (const sec of autoSections) {
            if (sec.groupId) {
                if (!groupMap.has(sec.groupId)) groupMap.set(sec.groupId, [])
                groupMap.get(sec.groupId).push(sec)
            } else {
                ungrouped.push(sec)
            }
        }

        // Build ordered list of clusters: [{ groupId, sections, internalGap, externalGap }]
        const clusters = []
        for (const g of groups) {
            const secs = groupMap.get(g.id)
            if (secs && secs.length) {
                clusters.push({
                    groupId: g.id,
                    sections: secs,
                    internalGap: g.internalGap ?? 2,
                    externalGap: g.externalGap ?? 10
                })
            }
        }
        if (ungrouped.length) {
            clusters.push({
                groupId: null,
                sections: ungrouped,
                internalGap: 4,
                externalGap: 14
            })
        }

        // Lay out left-to-right with wrapping
        let cursorX = startX
        let cursorY = startY
        let rowHeight = 0

        for (let ci = 0; ci < clusters.length; ci++) {
            const cluster = clusters[ci]

            // External gap before this cluster (except first)
            if (ci > 0) {
                cursorX += cluster.externalGap
            }

            for (let si = 0; si < cluster.sections.length; si++) {
                const sec = cluster.sections[si]

                // Check if wrapping needed
                if (cursorX + sec.w > maxWidth && cursorX > startX) {
                    cursorX = startX
                    cursorY += rowHeight + rowGap
                    rowHeight = 0
                }

                sec.x = cursorX
                sec.y = cursorY
                cursorX += sec.w + cluster.internalGap
                rowHeight = Math.max(rowHeight, sec.h)
            }
        }
    }

    /**
     * Reflow sections: re-run auto-layout, preserving manually positioned sections.
     */
    function reflowSections(sections, groups, options) {
        runAutoLayout(sections, groups, options)
    }

    /**
     * Mark a section as manually positioned (opt-out of auto-layout).
     */
    function setManualPosition(section, manual = true) {
        section.manualPosition = manual
    }

    return {
        runAutoLayout,
        reflowSections,
        setManualPosition
    }
}
