import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import { useRouter, useParams } from "next/navigation";
import ResourceDetailPage from "../app/resources/[id]/page";

jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
  useParams: jest.fn(),
}));

process.env.NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000";

const mockPush = jest.fn();
const mockResourceId = "test-resource-123";

beforeEach(() => {
  (useRouter as jest.Mock).mockReturnValue({ push: mockPush });
  (useParams as jest.Mock).mockReturnValue({ id: mockResourceId });
  jest.spyOn(console, "error").mockImplementation((error) => {
    if (
      !(error?.message === "Not implemented: navigation (except hash changes)")
    ) {
      console.warn(error);
    }
  });
});

describe("ResourceDetailPage", () => {
  beforeEach(() => {
    localStorage.clear();
    (fetch as jest.MockedFunction<typeof fetch>).mockClear();
    mockPush.mockClear();
    jest.spyOn(Storage.prototype, "setItem").mockImplementation(() => {});
    jest.spyOn(Storage.prototype, "getItem").mockImplementation(() => null);
    jest.spyOn(Storage.prototype, "removeItem").mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("redirects to login if no auth token", () => {
    render(<ResourceDetailPage />);
    expect(mockPush).toHaveBeenCalledWith("/login");
  });

  it("redirects to login if invalid user info", () => {
    jest.spyOn(Storage.prototype, "getItem").mockImplementation((key) => {
      if (key === "auth_token") return "mock-token";
      if (key === "user_info") return "invalid-json";
      return null;
    });
    render(<ResourceDetailPage />);
    expect(localStorage.removeItem).toHaveBeenCalledWith("user_info");
    expect(localStorage.removeItem).toHaveBeenCalledWith("auth_token");
    expect(mockPush).toHaveBeenCalledWith("/login");
  });

  describe("resource fetch", () => {
    it("fetches resource successfully and displays content", async () => {
      jest.spyOn(Storage.prototype, "getItem").mockImplementation((key) => {
        if (key === "auth_token") return "mock-token";
        if (key === "user_info")
          return JSON.stringify({
            id: "1",
            email: "test@example.com",
            display_name: "Test User",
          });
        return null;
      });

      const mockResource = {
        id: mockResourceId,
        url: "https://example.com/article",
        title: "Example Article",
        summary: "A great article about testing",
        tags: ["testing", "javascript"],
        status: "READY" as const,
        content_type: "url",
        original_content: "https://example.com/article",
        created_at: "2024-01-01T10:00:00Z",
      };

      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResource),
      });

      render(<ResourceDetailPage />);

      await waitFor(() => {
        expect(screen.getByText("Example Article")).toBeInTheDocument();
      });

      expect(screen.getByText("A great article about testing")).toBeInTheDocument();
      expect(screen.getByText("testing")).toBeInTheDocument();
      expect(screen.getByText("javascript")).toBeInTheDocument();
      expect(screen.getByText("Ready")).toBeInTheDocument();
      // Check that URL is displayed in a read-only input within Source URL section
      const urlSection = screen.getByText("Source URL").closest("div");
      expect(within(urlSection!).getByDisplayValue("https://example.com/article")).toBeInTheDocument();
    });

    it("shows error on 404 resource not found", async () => {
      jest.spyOn(Storage.prototype, "getItem").mockImplementation((key) => {
        if (key === "auth_token") return "mock-token";
        if (key === "user_info")
          return JSON.stringify({
            id: "1",
            email: "test@example.com",
            display_name: "Test User",
          });
        return null;
      });

      (fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 404,
      });

      render(<ResourceDetailPage />);

      await waitFor(() => {
        expect(screen.getByText("Resource not found")).toBeInTheDocument();
      });

      expect(screen.getByText("Back to Resources")).toBeInTheDocument();
    });

    it("redirects to login on 401 response", async () => {
      jest.spyOn(Storage.prototype, "getItem").mockImplementation((key) => {
        if (key === "auth_token") return "mock-token";
        if (key === "user_info")
          return JSON.stringify({
            id: "1",
            email: "test@example.com",
            display_name: "Test User",
          });
        return null;
      });

      (fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 401,
      });

      render(<ResourceDetailPage />);

      await waitFor(() => {
        expect(localStorage.removeItem).toHaveBeenCalledWith("auth_token");
        expect(localStorage.removeItem).toHaveBeenCalledWith("user_info");
        expect(mockPush).toHaveBeenCalledWith("/login");
      });
    });
  });

  describe("edit form", () => {
    beforeEach(async () => {
      jest.spyOn(Storage.prototype, "getItem").mockImplementation((key) => {
        if (key === "auth_token") return "mock-token";
        if (key === "user_info")
          return JSON.stringify({
            id: "1",
            email: "test@example.com",
            display_name: "Test User",
          });
        return null;
      });

      const mockResource = {
        id: mockResourceId,
        url: "https://example.com/article",
        title: "Example Article",
        summary: "A great article about testing",
        tags: ["testing"],
        status: "READY" as const,
        content_type: "url",
        original_content: "https://example.com/article",
        created_at: "2024-01-01T10:00:00Z",
      };

      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResource),
      });
    });

    it("opens edit form when edit button is clicked", async () => {
      render(<ResourceDetailPage />);

      await waitFor(() => {
        expect(screen.getByText("Example Article")).toBeInTheDocument();
      });

      const editButton = screen.getByRole("button", { name: /edit/i });
      fireEvent.click(editButton);

      expect(screen.getByLabelText("Title")).toBeInTheDocument();
      expect(screen.getByDisplayValue("Example Article")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /save/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
    });

    it("saves edit with valid title", async () => {
      const updatedResource = {
        id: mockResourceId,
        url: "https://example.com/article",
        title: "Updated Article Title",
        summary: "A great article about testing",
        tags: ["testing"],
        status: "READY" as const,
        content_type: "url",
        original_content: "https://example.com/article",
        created_at: "2024-01-01T10:00:00Z",
      };

      (fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            id: mockResourceId,
            url: "https://example.com/article",
            title: "Example Article",
            summary: "A great article about testing",
            tags: ["testing"],
            status: "READY",
            content_type: "url",
            original_content: "https://example.com/article",
            created_at: "2024-01-01T10:00:00Z",
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(updatedResource),
        });

      render(<ResourceDetailPage />);

      await waitFor(() => {
        expect(screen.getByText("Example Article")).toBeInTheDocument();
      });

      const editButton = screen.getByRole("button", { name: /edit/i });
      fireEvent.click(editButton);

      const titleInput = screen.getByLabelText("Title");
      fireEvent.change(titleInput, {
        target: { value: "Updated Article Title" },
      });

      const saveButton = screen.getByRole("button", { name: /save/i });
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith(
          `http://localhost:8000/resources/${mockResourceId}`,
          {
            method: "PATCH",
            headers: {
              Authorization: "Bearer mock-token",
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              title: "Updated Article Title",
            }),
          }
        );
      });

      await waitFor(() => {
        expect(screen.getByText("Updated Article Title")).toBeInTheDocument();
      });
    });

    it("disables save button and shows error when title is empty", async () => {
      render(<ResourceDetailPage />);

      await waitFor(() => {
        expect(screen.getByText("Example Article")).toBeInTheDocument();
      });

      const editButton = screen.getByRole("button", { name: /edit/i });
      fireEvent.click(editButton);

      const titleInput = screen.getByLabelText("Title");
      fireEvent.change(titleInput, { target: { value: "" } });

      const saveButton = screen.getByRole("button", { name: /save/i });
      expect(saveButton).toBeDisabled();
      expect(screen.getByText("Title cannot be empty")).toBeInTheDocument();
    });

    it("disables save button when title has only whitespace", async () => {
      render(<ResourceDetailPage />);

      await waitFor(() => {
        expect(screen.getByText("Example Article")).toBeInTheDocument();
      });

      const editButton = screen.getByRole("button", { name: /edit/i });
      fireEvent.click(editButton);

      const titleInput = screen.getByLabelText("Title");
      fireEvent.change(titleInput, { target: { value: "   " } });

      const saveButton = screen.getByRole("button", { name: /save/i });
      expect(saveButton).toBeDisabled();
      expect(screen.getByText("Title cannot be empty")).toBeInTheDocument();
    });

    it("clears error when entering edit mode", async () => {
      const mockResource = {
        id: mockResourceId,
        url: "https://example.com/article",
        title: "Example Article",
        summary: "A great article about testing",
        tags: ["testing"],
        status: "READY" as const,
        content_type: "url",
        original_content: "https://example.com/article",
        created_at: "2024-01-01T10:00:00Z",
      };

      (fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockResource),
        })
        .mockRejectedValueOnce(new Error("Network error"));

      render(<ResourceDetailPage />);

      await waitFor(() => {
        expect(screen.getByText("Example Article")).toBeInTheDocument();
      });

      // Try to edit and cause an error
      const editButton = screen.getByRole("button", { name: /edit/i });
      fireEvent.click(editButton);

      const titleInput = screen.getByLabelText("Title");
      fireEvent.change(titleInput, {
        target: { value: "Updated Title" },
      });

      const saveButton = screen.getByRole("button", { name: /save/i });
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(screen.getByText("Network error")).toBeInTheDocument();
      });

      // Cancel edit and try again - error should clear
      const cancelButton = screen.getByRole("button", { name: /cancel/i });
      fireEvent.click(cancelButton);

      const newEditButton = screen.getByRole("button", { name: /edit/i });
      fireEvent.click(newEditButton);

      expect(screen.queryByText("Network error")).not.toBeInTheDocument();
    });
  });

  describe("delete functionality", () => {
    beforeEach(async () => {
      jest.spyOn(Storage.prototype, "getItem").mockImplementation((key) => {
        if (key === "auth_token") return "mock-token";
        if (key === "user_info")
          return JSON.stringify({
            id: "1",
            email: "test@example.com",
            display_name: "Test User",
          });
        return null;
      });

      const mockResource = {
        id: mockResourceId,
        url: "https://example.com/article",
        title: "Example Article",
        summary: "A great article about testing",
        tags: ["testing"],
        status: "READY" as const,
        content_type: "url",
        original_content: "https://example.com/article",
        created_at: "2024-01-01T10:00:00Z",
      };

      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResource),
      });
    });

    it("shows confirmation dialog when delete button is clicked", async () => {
      render(<ResourceDetailPage />);

      await waitFor(() => {
        expect(screen.getByText("Example Article")).toBeInTheDocument();
      });

      const deleteButton = screen.getByRole("button", { name: /delete/i });
      fireEvent.click(deleteButton);

      expect(screen.getByText("Delete Resource")).toBeInTheDocument();
      expect(screen.getByText(/are you sure you want to delete this resource/i)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
    });

    it("navigates to resources page after confirmed delete", async () => {
      (fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            id: mockResourceId,
            url: "https://example.com/article",
            title: "Example Article",
            summary: "A great article about testing",
            tags: ["testing"],
            status: "READY",
            content_type: "url",
            original_content: "https://example.com/article",
            created_at: "2024-01-01T10:00:00Z",
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
        });

      render(<ResourceDetailPage />);

      await waitFor(() => {
        expect(screen.getByText("Example Article")).toBeInTheDocument();
      });

      const deleteButton = screen.getByRole("button", { name: /delete/i });
      fireEvent.click(deleteButton);

      const confirmButton = screen.getByRole("button", { name: "Delete" });
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith(
          `http://localhost:8000/resources/${mockResourceId}`,
          {
            method: "DELETE",
            headers: {
              Authorization: "Bearer mock-token",
            },
          }
        );
      });

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith("/resources");
      });
    });

    it("keeps resource when cancel is clicked in delete dialog", async () => {
      render(<ResourceDetailPage />);

      await waitFor(() => {
        expect(screen.getByText("Example Article")).toBeInTheDocument();
      });

      const deleteButton = screen.getByRole("button", { name: /delete/i });
      fireEvent.click(deleteButton);

      const cancelButton = screen.getByRole("button", { name: /cancel/i });
      fireEvent.click(cancelButton);

      // Resource should still be visible
      expect(screen.getByText("Example Article")).toBeInTheDocument();
      // Should not have navigated away
      expect(mockPush).not.toHaveBeenCalledWith("/resources");
    });
  });
});