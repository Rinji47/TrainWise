const getValue = (id) => document.getElementById(id)?.value || ""

function filterPayments() {
  const params = new URLSearchParams()
  const status = getValue("paymentFilter")
  const date = getValue("dateFilter")

  if (status) params.set("status", status)
  if (date) params.set("date", date)

  const query = params.toString()
  if (query) {
    window.location.search = query
  }
}

function downloadReceipt(paymentId) {
  window.location.href = `/payments/${paymentId}/receipt/`
}

function retryPayment(paymentId) {
  if (confirm("Retry payment for this transaction?")) {
    window.location.href = `/payments/${paymentId}/retry/`
  }
}
