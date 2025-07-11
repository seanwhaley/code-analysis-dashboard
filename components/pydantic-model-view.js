/**
 * Renders a list of Pydantic models, their fields, inheritance, and composition relationships.
 * Expects data as loaded from the API.
 */
function renderPydanticModels(classes) {
    // Filter only pydantic models
    const pydanticModels = classes.filter(cls => cls.class_type === "pydantic_model");

    let html = `<h2>🧬 Pydantic Models</h2>`;
    pydanticModels.forEach(model => {
        html += `
        <div class="pydantic-model">
            <h3>${model.name}</h3>
            <p><strong>File:</strong> ${model.file_path} @ Line ${model.line_number}</p>
            <p><strong>Base Classes:</strong> ${model.base_classes.join(", ")}</p>
            <p><strong>Docstring:</strong> ${model.docstring || "—"}</p>
            <h4>Fields</h4>
            <ul>
                ${model.fields.map(f => `<li><b>${f.name}</b>: ${f.type || "unknown"}${f.default ? " = " + f.default : ""}</li>`).join("")}
            </ul>
            <h4>Validators</h4>
            <ul>
                ${model.validators.map(v => `<li>${v}</li>`).join("") || "<li>None</li>"}
            </ul>
            ${model.config ? `<h4>Config</h4><pre>${model.config}</pre>` : ""}
        </div>
        <hr>
        `;
    });
    document.getElementById("pydanticModelList").innerHTML = html;
}