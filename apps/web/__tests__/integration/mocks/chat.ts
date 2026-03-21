// Chat mock data and utilities
export const mockConversations = [
  {
    id: 'conv_1',
    title: 'Test Conversation',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

export const mockMessages = [
  {
    id: 'msg_1',
    conversation_id: 'conv_1',
    role: 'user' as const,
    content: 'Hello, test message',
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'msg_2',
    conversation_id: 'conv_1',
    role: 'assistant' as const,
    content: 'Hello! This is a mock response from the AI assistant.',
    created_at: '2024-01-01T00:01:00Z',
  },
];

export const chatMockHandlers = {
  getConversations: (query?: { page?: number; limit?: number }) =>
    Promise.resolve({
      ok: true,
      json: () => {
        const page = query?.page || 1;
        const limit = query?.limit || 20;
        const startIndex = (page - 1) * limit;
        const endIndex = startIndex + limit;
        const paginatedConversations = mockConversations.slice(startIndex, endIndex);

        return Promise.resolve({
          conversations: paginatedConversations,
          total: mockConversations.length,
          page,
          limit,
          pages: Math.ceil(mockConversations.length / limit),
        });
      },
    }),

  getConversation: (id: string) =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve(mockConversations.find(c => c.id === id)),
    }),

  createConversation: (data: { title?: string }) =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({
        id: `conv_${Date.now()}`,
        title: data.title || 'New Conversation',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }),
    }),

  getMessages: (conversationId: string, query?: { page?: number; limit?: number }) =>
    Promise.resolve({
      ok: true,
      json: () => {
        const conversationMessages = mockMessages.filter(m => m.conversation_id === conversationId);
        const page = query?.page || 1;
        const limit = query?.limit || 50;
        const startIndex = (page - 1) * limit;
        const endIndex = startIndex + limit;
        const paginatedMessages = conversationMessages.slice(startIndex, endIndex);

        return Promise.resolve({
          messages: paginatedMessages,
          total: conversationMessages.length,
          page,
          limit,
          pages: Math.ceil(conversationMessages.length / limit),
        });
      },
    }),

  sendMessage: (conversationId: string, content: string) =>
    Promise.resolve({
      ok: true,
      json: () => {
        const userMessage = {
          id: `msg_${Date.now()}`,
          conversation_id: conversationId,
          role: 'user' as const,
          content,
          created_at: new Date().toISOString(),
        };

        const assistantMessage = {
          id: `msg_${Date.now() + 1}`,
          conversation_id: conversationId,
          role: 'assistant' as const,
          content: `This is a mock AI response to: "${content}"`,
          created_at: new Date().toISOString(),
        };

        return Promise.resolve({
          userMessage,
          assistantMessage,
        });
      },
    }),

  streamChat: (content: string) => {
    // Mock streaming response
    const chunks = [
      'This ',
      'is ',
      'a ',
      'mock ',
      'streaming ',
      'response ',
      'to: ',
      `"${content}"`,
    ];

    return Promise.resolve({
      ok: true,
      body: {
        getReader: () => ({
          read: (() => {
            let index = 0;
            return () => {
              if (index >= chunks.length) {
                return Promise.resolve({ done: true, value: undefined });
              }
              const chunk = chunks[index++];
              const encoder = new TextEncoder();
              const data = `data: ${JSON.stringify({ content: chunk, done: false })}\n\n`;
              return Promise.resolve({ done: false, value: encoder.encode(data) });
            };
          })(),
        }),
      },
      headers: {
        get: (header: string) => {
          if (header === 'content-type') return 'text/event-stream';
          return null;
        },
      },
    });
  },

  deleteConversation: (id: string) =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ message: 'Conversation deleted successfully' }),
    }),
};