describe("Results View (mocked)", () => {
  beforeEach(() => {
    // Mock all API endpoints for a completed job
    cy.intercept("POST", "/api/upload", {
      statusCode: 200,
      body: {
        job_id: "mock-job-001",
        filename: "office.dxf",
        status: "pending",
      },
    }).as("upload");

    // Mock WebSocket by having status immediately return completed
    cy.intercept("GET", "/api/jobs/mock-job-001", {
      statusCode: 200,
      body: {
        job_id: "mock-job-001",
        status: "completed",
        progress: 1.0,
        message: "Verarbeitung abgeschlossen",
        result_svg: "/api/jobs/mock-job-001/svg",
        result_pdf: "/api/jobs/mock-job-001/pdf",
      },
    }).as("jobStatus");

    cy.intercept("GET", "/api/jobs/mock-job-001/svg", {
      statusCode: 200,
      headers: { "content-type": "image/svg+xml" },
      body: '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect width="100" height="100" fill="white"/><text x="10" y="50">Test Plan</text></svg>',
    }).as("svg");

    cy.intercept("GET", "/api/jobs/mock-job-001/cover-sheet", {
      statusCode: 200,
      headers: { "content-type": "image/svg+xml" },
      body: '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><text x="10" y="50">Deckblatt</text></svg>',
    }).as("coverSheet");

    cy.intercept("GET", "/api/jobs/mock-job-001/situation-plan", {
      statusCode: 200,
      headers: { "content-type": "image/svg+xml" },
      body: '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><text x="10" y="50">Situationsplan</text></svg>',
    }).as("situationPlan");

    cy.intercept("GET", "/api/jobs/mock-job-001/original-svg", {
      statusCode: 200,
      headers: { "content-type": "image/svg+xml" },
      body: '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><text x="10" y="50">Original</text></svg>',
    }).as("originalSvg");

    cy.intercept("GET", "/api/jobs/mock-job-001/data", {
      statusCode: 200,
      body: {
        filename: "office.dxf",
        rooms: [
          { id: 1, room_type: "office", label: "Büro 1", area: 5000 },
          { id: 2, room_type: "corridor", label: "Korridor", area: 8000 },
        ],
        walls: [],
        bounds: [0, 0, 200, 100],
      },
    }).as("data");

    cy.intercept("GET", "/api/jobs/mock-job-001/metrics", {
      statusCode: 200,
      body: {
        dxf_parsing_ms: 450,
        room_detection_ms: 280,
        room_classification_ms: 5200,
        svg_generation_ms: 95,
        pdf_export_ms: 1800,
        supplementary_plans_ms: 18,
        total_pipeline_ms: 12500,
        rooms_detected: 14,
        rooms_classified: 14,
      },
    }).as("metrics");
  });

  it("shows the result view with tabs after upload", () => {
    cy.visit("/");

    // Trigger upload
    const blob = new Blob(["fake dxf"], { type: "application/octet-stream" });
    const file = new File([blob], "office.dxf", { type: "application/octet-stream" });
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);

    cy.get('input[type="file"]').then(($input) => {
      const input = $input[0] as HTMLInputElement;
      input.files = dataTransfer.files;
      cy.wrap($input).trigger("change", { force: true });
    });

    // Wait for completion — check for German tab label
    cy.contains("Orientierungsplan", { timeout: 15000 }).should("be.visible");

    // Check tabs exist (German labels since default locale is DE)
    cy.contains("Geschossplan").should("be.visible");
    cy.contains("Deckblatt").should("be.visible");
    cy.contains("Situationsplan").should("be.visible");
    cy.contains("Vergleich").should("be.visible");
  });

  it("switches between plan tabs", () => {
    cy.visit("/");

    const blob = new Blob(["fake dxf"], { type: "application/octet-stream" });
    const file = new File([blob], "office.dxf", { type: "application/octet-stream" });
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);

    cy.get('input[type="file"]').then(($input) => {
      const input = $input[0] as HTMLInputElement;
      input.files = dataTransfer.files;
      cy.wrap($input).trigger("change", { force: true });
    });

    cy.contains("Orientierungsplan", { timeout: 15000 }).should("be.visible");

    // Switch to Deckblatt
    cy.contains("Deckblatt").click();
    cy.wait("@coverSheet");

    // Switch to Situationsplan
    cy.contains("Situationsplan").click();
    cy.wait("@situationPlan");

    // Switch to Vergleich
    cy.contains("Vergleich").click();

    // Back to Geschossplan
    cy.contains("Geschossplan").click();
  });

  it("shows the export dropdown", () => {
    cy.visit("/");

    const blob = new Blob(["fake dxf"], { type: "application/octet-stream" });
    const file = new File([blob], "office.dxf", { type: "application/octet-stream" });
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);

    cy.get('input[type="file"]').then(($input) => {
      const input = $input[0] as HTMLInputElement;
      input.files = dataTransfer.files;
      cy.wrap($input).trigger("change", { force: true });
    });

    cy.contains("Orientierungsplan", { timeout: 15000 }).should("be.visible");

    // Open export dropdown (German label)
    cy.contains("Exportieren").click();
    cy.contains("Orientierungsplan (SVG)").should("be.visible");
    cy.contains("Orientierungsplan (PDF)").should("be.visible");
    cy.contains("Deckblatt (SVG)").should("be.visible");
    cy.contains("Situationsplan (SVG)").should("be.visible");
  });

  it("can start a new plan", () => {
    cy.visit("/");

    const blob = new Blob(["fake dxf"], { type: "application/octet-stream" });
    const file = new File([blob], "office.dxf", { type: "application/octet-stream" });
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);

    cy.get('input[type="file"]').then(($input) => {
      const input = $input[0] as HTMLInputElement;
      input.files = dataTransfer.files;
      cy.wrap($input).trigger("change", { force: true });
    });

    cy.contains("Orientierungsplan", { timeout: 15000 }).should("be.visible");

    // Click "Neuer Plan" (German)
    cy.contains("Neuer Plan").click();
    cy.contains("Gebäudeplan hochladen").should("be.visible");
  });
});
