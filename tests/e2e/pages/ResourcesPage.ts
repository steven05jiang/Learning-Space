import { Page, Locator, expect } from '@playwright/test';

export class ResourcesPage {
  readonly page: Page;
  readonly addResourceButton: Locator;
  readonly resourceList: Locator;
  readonly searchInput: Locator;
  readonly filterSelect: Locator;
  readonly submitForm: Locator;
  readonly urlInput: Locator;
  readonly titleInput: Locator;
  readonly descriptionInput: Locator;
  readonly submitButton: Locator;

  constructor(page: Page) {
    this.page = page;

    // Resource list page elements
    this.addResourceButton = page.getByRole('button', { name: 'Add Resource' });
    this.resourceList = page.locator('[data-testid="resource-list"]');
    this.searchInput = page.locator('[data-testid="search-input"]');
    this.filterSelect = page.locator('[data-testid="filter-select"]');

    // Resource form elements
    this.submitForm = page.locator('[data-testid="resource-form"]');
    this.urlInput = page.locator('[data-testid="url-input"]');
    this.titleInput = page.locator('[data-testid="title-input"]');
    this.descriptionInput = page.locator('[data-testid="description-input"]');
    this.submitButton = page.getByRole('button', { name: 'Submit' });
  }

  async goto() {
    await this.page.goto('/resources');
    await this.page.waitForLoadState('networkidle');
  }

  async gotoAddResource() {
    await this.page.goto('/resources/add');
    await this.page.waitForLoadState('networkidle');
  }

  async gotoResourceDetail(resourceId: string) {
    await this.page.goto(`/resources/${resourceId}`);
    await this.page.waitForLoadState('networkidle');
  }

  async submitResource(resource: {
    url: string;
    title?: string;
    description?: string;
  }) {
    await this.urlInput.fill(resource.url);

    if (resource.title) {
      await this.titleInput.fill(resource.title);
    }

    if (resource.description) {
      await this.descriptionInput.fill(resource.description);
    }

    await this.submitButton.click();
  }

  async searchResources(query: string) {
    await this.searchInput.fill(query);
    await this.searchInput.press('Enter');
  }

  async filterByStatus(status: string) {
    await this.filterSelect.selectOption(status);
  }

  async getResourceByTitle(title: string) {
    return this.resourceList.locator(`[data-testid="resource-item"]`).filter({
      hasText: title
    });
  }

  async expectResourceExists(title: string) {
    const resource = await this.getResourceByTitle(title);
    await expect(resource).toBeVisible();
  }

  async expectResourceNotExists(title: string) {
    const resource = await this.getResourceByTitle(title);
    await expect(resource).not.toBeVisible();
  }

  async clickEditResource(title: string) {
    const resource = await this.getResourceByTitle(title);
    await resource.getByRole('button', { name: 'Edit' }).click();
  }

  async clickDeleteResource(title: string) {
    const resource = await this.getResourceByTitle(title);
    await resource.getByRole('button', { name: 'Delete' }).click();

    // Confirm deletion if confirmation dialog appears
    await this.page.getByRole('button', { name: 'Confirm' }).click();
  }
}