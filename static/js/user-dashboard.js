// Cancel a class booking
function cancelBooking(bookingId) {
  if (confirm("Are you sure you want to cancel this booking?")) {
    const form = document.createElement("form")
    form.method = "POST"
    form.action = `/bookings/${bookingId}/cancel/`
    form.innerHTML = `<input type="hidden" name="csrfmiddlewaretoken" value="${getCookie("csrftoken")}">`
    document.body.appendChild(form)
    form.submit()
  }
}

// Helper to get CSRF token
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

// Load dashboard on page load
document.addEventListener("DOMContentLoaded", () => {})
