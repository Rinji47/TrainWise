const loginForm = document.getElementById("loginForm")
if (loginForm) {
  loginForm.addEventListener("submit", (e) => {
    const email = document.getElementById("email").value
    const password = document.getElementById("password").value

    if (!email || !password) {
      e.preventDefault()
      alert("Please fill in all fields")
    }
  })
}

const registerForm = document.getElementById("registerForm")
if (registerForm) {
  registerForm.addEventListener("submit", (e) => {
    const password = document.getElementById("password").value
    const passwordConfirm = document.getElementById("password_confirm").value

    if (password !== passwordConfirm) {
      e.preventDefault()
      alert("Passwords do not match")
    }

    if (password.length < 8) {
      e.preventDefault()
      alert("Password must be at least 8 characters")
    }
  })
}

const passwordInput = document.getElementById("password")
if (passwordInput) {
  passwordInput.addEventListener("input", function () {
    const strength = calculatePasswordStrength(this.value)
    const indicator = document.getElementById("passwordStrengthIndicator")
    if (indicator) {
      indicator.style.width = `${strength * 25}%`
      indicator.style.backgroundColor = strength >= 4 ? "green" : strength >= 2 ? "orange" : "red"
    }
  })
}

function calculatePasswordStrength(password) {
  let strength = 0
  if (password.length >= 8) strength++
  if (/[a-z]/.test(password)) strength++
  if (/[A-Z]/.test(password)) strength++
  if (/[0-9]/.test(password)) strength++
  if (/[^A-Za-z0-9]/.test(password)) strength++
  return strength
}
