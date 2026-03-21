// Resources mock data and utilities
export const mockResources = [
  {
    id: 'resource_1',
    title: 'Test Resource 1',
    url: 'https://example.com/resource1',
    description: 'This is a test resource',
    tags: ['test', 'example'],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'resource_2',
    title: 'Test Resource 2',
    url: 'https://example.com/resource2',
    description: 'Another test resource',
    tags: ['test', 'sample'],
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  },
];

export const mockResourcesResponse = {
  resources: mockResources,
  total: mockResources.length,
  page: 1,
  limit: 10,
  pages: 1,
};

export const resourcesMockHandlers = {
  getResources: (query?: { search?: string; page?: number; limit?: number }) =>
    Promise.resolve({
      ok: true,
      json: () => {
        let filteredResources = mockResources;
        if (query?.search) {
          filteredResources = mockResources.filter(r =>
            r.title.toLowerCase().includes(query.search!.toLowerCase()) ||
            r.description.toLowerCase().includes(query.search!.toLowerCase())
          );
        }

        const page = query?.page || 1;
        const limit = query?.limit || 10;
        const startIndex = (page - 1) * limit;
        const endIndex = startIndex + limit;
        const paginatedResources = filteredResources.slice(startIndex, endIndex);

        return Promise.resolve({
          resources: paginatedResources,
          total: filteredResources.length,
          page,
          limit,
          pages: Math.ceil(filteredResources.length / limit),
        });
      },
    }),

  getResource: (id: string) =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve(mockResources.find(r => r.id === id)),
    }),

  createResource: (data: any) =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({
        id: `resource_${Date.now()}`,
        ...data,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }),
    }),

  updateResource: (id: string, data: any) =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({
        ...mockResources.find(r => r.id === id),
        ...data,
        updated_at: new Date().toISOString(),
      }),
    }),

  deleteResource: (id: string) =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ message: 'Resource deleted successfully' }),
    }),
};