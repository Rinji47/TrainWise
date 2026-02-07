// Subscription management - no API calls, just page navigation
function subscribePlan(planId) {
  window.location.href = `/subscribe/${planId}/`
}

function renewSubscription() {
  window.location.href = `/subscriptions/renew/`
}

function cancelSubscription() {
  if (confirm("Are you sure you want to cancel your subscription? You will lose access immediately.")) {
    const form = document.createElement("form")
    form.method = "POST"
    form.action = `/subscriptions/cancel/`
    form.innerHTML = `<input type="hidden" name="csrfmiddlewaretoken" value="${getCookie("csrftoken")}">`
    document.body.appendChild(form)
    form.submit()
  }
}

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

document.addEventListener("DOMContentLoaded", () => {
  console.log("[v0] Subscription page loaded")
})
