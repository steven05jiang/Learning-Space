import { Page } from '@playwright/test'

export class ResourcesPage {
  constructor(private page: Page) {}

  async submitUrl(url: string) {
    await this.page.fill('[data-testid="url-input"]', url)
    await this.page.click('[data-testid="submit-resource"]')
  }

  async waitForStatus(resourceTitle: string, status: string) {
    await this.page.waitForSelector(
      `[data-testid="resource-card"]:has-text("${resourceTitle}") [data-status="${status}"]`,
      { timeout: 15000 }
    )
  }
}

export class GraphPage {
  constructor(private page: Page) {}

  async clickNode(label: string) {
    await this.page.click(`[data-node-label="${label}"]`)
  }

  async waitForPanel() {
    await this.page.waitForSelector('[data-testid="node-resource-panel"]')
  }
}