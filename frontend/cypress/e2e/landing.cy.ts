describe("Landing Page", () => {
  beforeEach(() => {
    cy.visit("/");
  });

  it("shows the RescueForge header", () => {
    cy.contains("RescueForge").should("be.visible");
    cy.contains("CAD zu Feuerwehr-Orientierungsplänen").should("be.visible");
  });

  it("shows the upload section", () => {
    cy.contains("Gebäudeplan hochladen").should("be.visible");
    cy.contains("DWG/DXF").should("be.visible");
  });

  it("shows the feature cards", () => {
    cy.contains("Automatische Bereinigung").should("be.visible");
    cy.contains("AI Raumklassifikation").should("be.visible");
    cy.contains("FKS-konform").should("be.visible");
  });

  it("has language toggle", () => {
    // Default locale is DE — switch to EN
    cy.get('button[aria-label="Switch language"]').click();
    cy.contains("CAD to Fire Department Orientation Plans").should("be.visible");

    // Switch back to DE
    cy.get('button[aria-label="Switch language"]').click();
    cy.contains("CAD zu Feuerwehr-Orientierungsplänen").should("be.visible");
  });

  it("toggles dark mode", () => {
    // Click dark mode button (uses Lucide Moon/Sun icons, find by aria-label)
    cy.get('button[aria-label="Zu dunklem Modus wechseln"]').click();
    cy.get("html").should("have.class", "dark");

    // Click again to toggle back
    cy.get('button[aria-label="Zu hellem Modus wechseln"]').click();
    cy.get("html").should("not.have.class", "dark");
  });
});
