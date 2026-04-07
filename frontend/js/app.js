// frontend/js/app.js

const API = "http://localhost:5000/api";

// Login
async function login(email, password) {
    const res = await fetch(`${API}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (data.token) {
        localStorage.setItem("token", data.token);
        localStorage.setItem("name", data.name);
        window.location.href = "/dashboard";
    } else {
        alert(data.error);
    }
}

// Enviar análisis a Claude
async function analyzeResults(params, studyType, studyDate) {
    const res = await fetch(`${API}/analyze`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${localStorage.getItem("token")}`
        },
        body: JSON.stringify({ params, study_type: studyType, study_date: studyDate })
    });
    return await res.json();
}

// Cargar historial
async function loadResults() {
    const res = await fetch(`${API}/results`, {
        headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
    });
    return await res.json();
}