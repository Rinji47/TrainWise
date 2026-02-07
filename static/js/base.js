// Mobile menu toggle
const hamburger = document.getElementById("hamburger")
if (hamburger) {
  hamburger.addEventListener("click", () => {
    const navMenu = document.querySelector(".nav-menu")
    navMenu.style.display = navMenu.style.display === "flex" ? "none" : "flex"
  })
}

// Auto-hide alerts
const alerts = document.querySelectorAll(".alert")
alerts.forEach((alert) => {
  setTimeout(() => {
    alert.style.animation = "slideOut 0.3s ease"
    setTimeout(() => {
      alert.remove()
    }, 300)
  }, 5000)
})

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
