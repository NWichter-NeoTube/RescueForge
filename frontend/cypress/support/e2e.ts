// Cypress E2E support file
// Add custom commands here

Cypress.Commands.add("uploadDxf", (filename: string) => {
  cy.get('[data-testid="file-upload"]').should("exist");
  cy.fixture(filename, "binary").then((fileContent) => {
    const blob = Cypress.Blob.binaryStringToBlob(fileContent, "application/octet-stream");
    const file = new File([blob], filename, { type: "application/octet-stream" });
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);

    cy.get('[data-testid="file-upload"] input[type="file"]').then(($input) => {
      const input = $input[0] as HTMLInputElement;
      input.files = dataTransfer.files;
      cy.wrap($input).trigger("change", { force: true });
    });
  });
});

declare global {
  namespace Cypress {
    interface Chainable {
      uploadDxf(filename: string): Chainable<void>;
    }
  }
}
