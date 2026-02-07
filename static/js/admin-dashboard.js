// User management
function editUser(userId) {
  window.location.href = `/admin/users/${userId}/edit/`
}

function deleteUser(userId) {
  if (confirm("Are you sure you want to delete this user?")) {
    const form = document.createElement("form")
    form.method = "POST"
    form.action = `/admin/users/${userId}/delete/`
    form.innerHTML = `<input type="hidden" name="csrfmiddlewaretoken" value="${getCookie("csrftoken")}">`
    document.body.appendChild(form)
    form.submit()
  }
}

function filterUsers() {
  const role = document.getElementById("roleFilter").value
  window.location.href = `/admin/users/?role=${role}`
}

function searchUsers() {
  const query = document.getElementById("searchUsers").value
  window.location.href = `/admin/users/?search=${query}`
}

// Subscription management
function filterSubscriptions(status) {
  window.location.href = `/admin/subscriptions/?status=${status}`
}

function editSubscription(subscriptionId) {
  window.location.href = `/admin/subscriptions/${subscriptionId}/edit/`
}

// Plan management
function editPlan(planId) {
  window.location.href = `/admin/plans/${planId}/edit/`
}

function deletePlan(planId) {
  if (confirm("Are you sure you want to delete this plan?")) {
    const form = document.createElement("form")
    form.method = "POST"
    form.action = `/admin/plans/${planId}/delete/`
    form.innerHTML = `<input type="hidden" name="csrfmiddlewaretoken" value="${getCookie("csrftoken")}">`
    document.body.appendChild(form)
    form.submit()
  }
}

// Payment management
function filterPayments() {
  const status = document.getElementById("statusFilter").value
  const method = document.getElementById("methodFilter").value
  window.location.href = `/admin/payments/?status=${status}&method=${method}`
}

function viewPayment(paymentId) {
  window.location.href = `/admin/payments/${paymentId}/`
}

// Booking management
function viewBooking(bookingId) {
  window.location.href = `/admin/bookings/${bookingId}/`
}

// Helper function to get CSRF token
function getCookie(name) {
  let cookieValue = null
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";")
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim()
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
        break
      }
    }
  }
  return cookieValue
}

// Load admin dashboard
document.addEventListener("DOMContentLoaded", () => {
  // Admin dashboard loaded
})
