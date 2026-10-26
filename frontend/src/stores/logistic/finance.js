// Finance actions for the logistics store: ledger entries, the scoped summary, funds, payouts and payroll runs.
import { apiRequest, authHeaders } from './api'
import { asStringId, asWarehouseId, financeScopeFor } from './mappers'

export function useLogisticFinance({
    activeWarehouse,
    creditBalance,
    financeCodRecords,
    financeDriverRecords,
    financeStaffRecords,
    financeSummary,
    transactions,
}) {
    async function addTransaction(tx) {
        const created = await apiRequest('/logistics/transactions', {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({
                warehouse_id: tx.hubId && tx.hubId !== 'all' ? tx.hubId : null,
                description: tx.desc,
                transaction_type: tx.type,
                amount: tx.amount,
                status: tx.status || 'Completed',
            }),
        })

        transactions.value = [{
            id: asStringId(created.id),
            hubId: asWarehouseId(created.hub_id),
            transactionCode: created.transaction_code || '',
            date: created.date,
            desc: created.desc,
            type: created.type,
            amount: created.amount,
            status: created.status,
            metadataJson: created.metadata_json || {},
            relatedOrder: created.related_order || null,
        }, ...transactions.value]

        if (created.amount > 0) {
            financeSummary.value.total_revenue = (financeSummary.value.total_revenue || 0) + created.amount
            creditBalance.value += created.amount
        } else {
            const expense = Math.abs(created.amount)
            // Only update the Expenses counter — never touch Revenue.
            // Revenue = what customers paid; Expenses = what we spent. They are separate.
            // Capital absorbs the shortfall if expenses exceed revenue.
            financeSummary.value.total_expenses = (financeSummary.value.total_expenses || 0) + expense
            financeSummary.value.capital_invested = Math.max(0, (financeSummary.value.capital_invested || 0) - expense)
        }
    }

    async function fetchFinanceSummary(warehouseId = activeWarehouse.value) {
        try {
            const scope = financeScopeFor(warehouseId)
            const query = scope === 'all' ? '' : `?warehouse_id=${encodeURIComponent(scope)}`
            const data = await apiRequest(`/finance/summary${query}`, { headers: authHeaders() })
            financeSummary.value = {
                ...data,
                _warehouseScope: scope,
            }
            return financeSummary.value
        } catch (e) {
            console.warn('[fetchFinanceSummary] failed (non-fatal):', e)
            return financeSummary.value
        }
    }

    function addFunds(amount) {
        if (amount > 0) creditBalance.value += amount
    }

    function markFinanceRecordPaid(collection, id) {
        const targetCollections = {
            cod: financeCodRecords.value,
            staff: financeStaffRecords.value,
            drivers: financeDriverRecords.value,
        }
        const items = targetCollections[collection]
        if (!items) return
        const item = items.find((entry) => entry.id === id)
        if (item) item.status = collection === 'cod' ? 'Completed' : 'Paid'
    }

    async function runPayroll(userPayouts) {
        // userPayouts: [{user_id, amount, record_type, name}]
        const result = await apiRequest('/finance/payroll/run', {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ user_payouts: userPayouts }),
        })
        // Payroll is an outflow — only update Expenses and Capital, never Revenue.
        const total = result.total || 0
        if (total > 0) {
            financeSummary.value.total_expenses = (financeSummary.value.total_expenses || 0) + total
            financeSummary.value.capital_invested = Math.max(0, (financeSummary.value.capital_invested || 0) - total)
        }
        return result
    }

    return {
        addTransaction,
        fetchFinanceSummary,
        addFunds,
        markFinanceRecordPaid,
        runPayroll,
     }
}
