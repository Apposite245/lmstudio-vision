import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "LMStudio.Vision",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "LMStudioVision") return;

        const origOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            if (origOnNodeCreated) origOnNodeCreated.apply(this, arguments);

            const self = this;

            this.addWidget("button", "Refresh Models", null, async () => {
                const baseUrlWidget = self.widgets.find(w => w.name === "base_url");
                const modelWidget = self.widgets.find(w => w.name === "model");

                if (!baseUrlWidget || !modelWidget) return;

                const baseUrl = encodeURIComponent(baseUrlWidget.value);
                let data;
                try {
                    const resp = await fetch(`/lmstudio_vision/models?base_url=${baseUrl}`);
                    data = await resp.json();
                } catch (e) {
                    alert("LM Studio not reachable: " + e.message);
                    return;
                }

                if (data.error) {
                    alert("Error: " + data.error);
                    return;
                }

                modelWidget.options.values = data.models;
                if (!data.models.includes(modelWidget.value)) {
                    modelWidget.value = data.models[0] ?? "";
                }
                app.graph.setDirtyCanvas(true);
            });
        };
    },
});
