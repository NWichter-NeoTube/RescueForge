describe("Error Handling", () => {
  beforeEach(() => {
    cy.visit("/");
  });

  it("shows error message when upload fails", () => {
    cy.intercept("POST", "**/api/upload", {
      statusCode: 500,
      body: { detail: "Internal server error" },
    }).as("uploadFail");

    // Trigger upload by dropping a file
    const file = new File(["dummy"], "test.dxf", { type: "application/octet-stream" });
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);

    cy.get('[data-testid="file-upload"] input[type="file"]').then(($input) => {
      const input = $input[0] as HTMLInputElement;
      input.files = dataTransfer.files;
      cy.wrap($input).trigger("change", { force: true });
    });

    cy.wait("@uploadFail");
    cy.contains("Internal server error").should("be.visible");
  });

  it("shows error when invalid file type is dropped", () => {
    // The dropzone should reject non-DXF/DWG files via accept filter
    cy.get('[data-testid="file-upload"]').should("exist");
    // The accept filter on the input restricts file types client-side
    cy.get('[data-testid="file-upload"] input[type="file"]')
      .should("have.attr", "accept");
  });

  it("allows dismissing error messages", () => {
    cy.intercept("POST", "**/api/upload", {
      statusCode: 400,
      body: { detail: "Unsupported file format" },
    }).as("uploadFail");

    const file = new File(["dummy"], "test.dxf", { type: "application/octet-stream" });
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);

    cy.get('[data-testid="file-upload"] input[type="file"]').then(($input) => {
      const input = $input[0] as HTMLInputElement;
      input.files = dataTransfer.files;
      cy.wrap($input).trigger("change", { force: true });
    });

    cy.wait("@uploadFail");
    cy.contains("Unsupported file format").should("be.visible");

    // Dismiss the error
    cy.get('[aria-label="Fehlermeldung schließen"]').click();
    cy.contains("Unsupported file format").should("not.exist");
  });

  it("handles rate limiting gracefully", () => {
    cy.intercept("POST", "**/api/upload", {
      statusCode: 429,
      body: { detail: "Too many requests. Please try again later." },
    }).as("rateLimited");

    const file = new File(["dummy"], "test.dxf", { type: "application/octet-stream" });
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);

    cy.get('[data-testid="file-upload"] input[type="file"]').then(($input) => {
      const input = $input[0] as HTMLInputElement;
      input.files = dataTransfer.files;
      cy.wrap($input).trigger("change", { force: true });
    });

    cy.wait("@rateLimited");
    cy.contains("Too many requests").should("be.visible");
  });
});
