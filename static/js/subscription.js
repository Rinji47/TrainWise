const redirectTo = (path) => {
  window.location.href = path
}

function subscribePlan(planId) {
  redirectTo(`/subscribe/${planId}/`)
}

function renewSubscription() {
  redirectTo(`/subscriptions/renew/`)
}

function cancelSubscription() {
  if (!confirm("Are you sure you want to cancel your subscription? You will lose access immediately.")) {
    return
  }

  const form = document.createElement("form")
  form.method = "POST"
  form.action = "/subscriptions/cancel/"

  const csrfToken = getCookie("csrftoken")
  if (csrfToken) {
    const input = document.createElement("input")
    input.type = "hidden"
    input.name = "csrfmiddlewaretoken"
    input.value = csrfToken
    form.appendChild(input)
  }

  document.body.appendChild(form)
  form.submit()
}

function getCookie(name) {
  const match = document.cookie.split("; ").find((row) => row.startsWith(`${name}=`))
  return match ? decodeURIComponent(match.split("=")[1]) : null
}
