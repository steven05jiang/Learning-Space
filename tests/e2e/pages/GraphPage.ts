import { Page, Locator, expect } from '@playwright/test';

export class GraphPage {
  readonly page: Page;
  readonly graphContainer: Locator;
  readonly graphCanvas: Locator;
  readonly nodeDetails: Locator;
  readonly resourcePanel: Locator;
  readonly searchBox: Locator;
  readonly zoomInButton: Locator;
  readonly zoomOutButton: Locator;
  readonly resetViewButton: Locator;
  readonly layoutSelect: Locator;

  constructor(page: Page) {
    this.page = page;

    // Graph visualization elements
    this.graphContainer = page.locator('[data-testid="graph-container"]');
    this.graphCanvas = page.locator('[data-testid="graph-canvas"]');
    this.nodeDetails = page.locator('[data-testid="node-details"]');
    this.resourcePanel = page.locator('[data-testid="resource-panel"]');

    // Graph controls
    this.searchBox = page.locator('[data-testid="graph-search"]');
    this.zoomInButton = page.getByRole('button', { name: 'Zoom In' });
    this.zoomOutButton = page.getByRole('button', { name: 'Zoom Out' });
    this.resetViewButton = page.getByRole('button', { name: 'Reset View' });
    this.layoutSelect = page.locator('[data-testid="layout-select"]');
  }

  async goto() {
    await this.page.goto('/graph');
    await this.page.waitForLoadState('networkidle');
  }

  async waitForGraphLoad() {
    // Wait for graph to be rendered
    await this.graphContainer.waitFor({ state: 'visible' });
    await this.page.waitForTimeout(1000); // Allow time for graph rendering
  }

  async clickNode(nodeId: string) {
    // Click on a specific node in the graph
    const node = this.graphCanvas.locator(`[data-node-id="${nodeId}"]`);
    await node.click();
  }

  async doubleClickNode(nodeId: string) {
    // Double-click to expand a node
    const node = this.graphCanvas.locator(`[data-node-id="${nodeId}"]`);
    await node.dblclick();
  }

  async searchNodes(query: string) {
    await this.searchBox.fill(query);
    await this.searchBox.press('Enter');
  }

  async changeLayout(layout: string) {
    await this.layoutSelect.selectOption(layout);
  }

  async zoomIn() {
    await this.zoomInButton.click();
  }

  async zoomOut() {
    await this.zoomOutButton.click();
  }

  async resetView() {
    await this.resetViewButton.click();
  }

  async expectNodeVisible(nodeId: string) {
    const node = this.graphCanvas.locator(`[data-node-id="${nodeId}"]`);
    await expect(node).toBeVisible();
  }

  async expectNodeDetailsVisible() {
    await expect(this.nodeDetails).toBeVisible();
  }

  async expectResourcePanelVisible() {
    await expect(this.resourcePanel).toBeVisible();
  }

  async getNodeByLabel(label: string) {
    return this.graphCanvas.locator(`[data-node-label="${label}"]`);
  }

  async expectNodeByLabel(label: string) {
    const node = await this.getNodeByLabel(label);
    await expect(node).toBeVisible();
  }

  async clickResourceInPanel(resourceTitle: string) {
    const resourceItem = this.resourcePanel.locator(`[data-testid="resource-item"]`).filter({
      hasText: resourceTitle
    });
    await resourceItem.click();
  }

  async expectGraphHasNodes() {
    // Check that graph has at least one node
    const nodes = this.graphCanvas.locator('[data-testid*="node"]');
    await expect(nodes.first()).toBeVisible();
  }

  async expectGraphEmpty() {
    // Check that graph has no nodes
    const emptyMessage = this.graphContainer.locator('[data-testid="empty-graph"]');
    await expect(emptyMessage).toBeVisible();
  }
}