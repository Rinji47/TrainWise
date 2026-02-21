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
    let errors = [];
    const username = document.getElementById("username").value.trim();
    const firstName = document.getElementById("first_name").value.trim();
    const lastName = document.getElementById("last_name").value.trim();
    const email = document.getElementById("email").value.trim();
    const phone = document.getElementById("phone").value.trim();
    const password = document.getElementById("password").value;
    const passwordConfirm = document.getElementById("password_confirm").value;
    const gender = document.getElementById("gender").value;
    const agreeTerms = document.querySelector("input[name='agree_terms']").checked;

    if (!username) errors.push("Username is required.");
    if (!firstName) errors.push("First name is required.");
    if (!lastName) errors.push("Last name is required.");
    if (!email) errors.push("Email is required.");
    if (!phone) errors.push("Phone number is required.");
    if (!password) errors.push("Password is required.");
    if (!passwordConfirm) errors.push("Password confirmation is required.");
    if (!gender) errors.push("Please select a gender.");
    if (!agreeTerms) errors.push("You must agree to the Terms of Service.");

    if (password !== passwordConfirm) {
      errors.push("Passwords do not match.");
    }
    if (password.length < 8) {
      errors.push("Password must be at least 8 characters.");
    }

    if (errors.length > 0) {
      e.preventDefault();
      showRegisterErrors(errors);
    }
  });
}

function showRegisterErrors(errors) {
  let errorDiv = document.getElementById("registerErrorMessages");
  if (!errorDiv) {
    errorDiv = document.createElement("div");
    errorDiv.id = "registerErrorMessages";
    errorDiv.className = "error-alert";
    const form = document.getElementById("registerForm");
    form.parentNode.insertBefore(errorDiv, form);
  }
  errorDiv.innerHTML = errors.map(e => `<p>${e}</p>`).join("");
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
