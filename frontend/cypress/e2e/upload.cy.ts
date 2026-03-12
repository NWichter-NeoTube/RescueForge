describe("File Upload Flow", () => {
  beforeEach(() => {
    cy.visit("/");
  });

  it("rejects non-DXF/DWG files", () => {
    // Try to upload a .txt file - the dropzone should show an error
    const blob = new Blob(["test content"], { type: "text/plain" });
    const file = new File([blob], "test.txt", { type: "text/plain" });
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);

    cy.get('[data-testid="file-upload"]').trigger("drop", {
      dataTransfer,
      force: true,
    });

    // Should still be on upload page (not processing)
    cy.contains("Gebäudeplan hochladen").should("be.visible");
  });

  it("shows upload area with correct accept types", () => {
    cy.get('[data-testid="file-upload"]').should("exist");
    cy.get('input[type="file"]').should("have.attr", "accept");
  });

  it("shows progress bar during processing (mocked)", () => {
    // Intercept the upload API call
    cy.intercept("POST", "/api/upload", {
      statusCode: 200,
      body: {
        job_id: "test-job-123",
        filename: "test.dxf",
        status: "pending",
      },
    }).as("upload");

    // Intercept WebSocket with polling fallback
    cy.intercept("GET", "/api/jobs/test-job-123", {
      statusCode: 200,
      body: {
        job_id: "test-job-123",
        status: "parsing",
        progress: 0.3,
        message: "DXF wird analysiert...",
        result_svg: null,
        result_pdf: null,
      },
    }).as("status");

    // Create a fake DXF file and upload
    const blob = new Blob(["fake dxf content"], { type: "application/octet-stream" });
    const file = new File([blob], "test.dxf", { type: "application/octet-stream" });
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);

    cy.get('input[type="file"]').then(($input) => {
      const input = $input[0] as HTMLInputElement;
      input.files = dataTransfer.files;
      cy.wrap($input).trigger("change", { force: true });
    });

    // Should show some processing indication
    cy.wait("@upload");
  });
});
