// Payment filtering - redirect with query params
function filterPayments() {
  const status = document.getElementById("paymentFilter").value
  const date = document.getElementById("dateFilter").value

  const params = new URLSearchParams()
  if (status) params.append("status", status)
  if (date) params.append("date", date)

  if (params.toString()) {
    window.location.search = params.toString()
  }
}

// Download receipt
function downloadReceipt(paymentId) {
  window.location.href = `/payments/${paymentId}/receipt/`
}

// Retry payment
function retryPayment(paymentId) {
  if (confirm("Retry payment for this transaction?")) {
    window.location.href = `/payments/${paymentId}/retry/`
  }
}

document.addEventListener("DOMContentLoaded", () => {
  console.log("[v0] Payment history page loaded")
})
