// Add or extend this method for Pydantic model graphs
async showPydanticModelGraph() {
    const response = await fetch('/api/classes?limit=5000');
    const result = await response.json();
    const pydanticModels = result.data.filter(cls => cls.class_type === "pydantic_model");
    let mermaidCode = 'graph TD\n';
    // Add inheritance links
    pydanticModels.forEach(model => {
        const modelName = model.name.replace(/[^a-zA-Z0-9_]/g, '_');
        model.base_classes.forEach(base => {
            const baseName = base.replace(/[^a-zA-Z0-9_]/g, '_');
            mermaidCode += `${baseName} --> ${modelName}\n`;
        });
    });
    // Add composition links ("composes" relationship from backend)
    // ... fetch and iterate relationships as needed
    this.renderMermaidDiagram(mermaidCode, 'Pydantic Model Inheritance');
}