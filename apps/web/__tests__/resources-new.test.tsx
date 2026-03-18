import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { useRouter } from "next/navigation";
import NewResourcePage from "../app/resources/new/page";

jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
}));

process.env.NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000";

const mockPush = jest.fn();

beforeEach(() => {
  (useRouter as jest.Mock).mockReturnValue({ push: mockPush });
  jest.spyOn(console, "error").mockImplementation((error) => {
    if (
      !(error?.message === "Not implemented: navigation (except hash changes)")
    ) {
      console.warn(error);
    }
  });
});

describe("NewResourcePage", () => {
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
    render(<NewResourcePage />);
    expect(mockPush).toHaveBeenCalledWith("/login");
  });

  it("redirects to login if invalid user info", () => {
    jest.spyOn(Storage.prototype, "getItem").mockImplementation((key) => {
      if (key === "auth_token") return "mock-token";
      if (key === "user_info") return "invalid-json";
      return null;
    });
    render(<NewResourcePage />);
    expect(localStorage.removeItem).toHaveBeenCalledWith("user_info");
    expect(localStorage.removeItem).toHaveBeenCalledWith("auth_token");
    expect(mockPush).toHaveBeenCalledWith("/login");
  });

  it("renders resource submission form when authenticated", async () => {
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

    render(<NewResourcePage />);

    await waitFor(() => {
      expect(screen.getByText("Add New Resource")).toBeInTheDocument();
    });

    expect(screen.getByLabelText("URL")).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("https://example.com/article"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Add Resource" }),
    ).toBeInTheDocument();
  });

  it("shows error when URL is empty on submit", async () => {
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

    render(<NewResourcePage />);

    await waitFor(() => {
      expect(screen.getByText("Add New Resource")).toBeInTheDocument();
    });

    const urlInput = screen.getByLabelText("URL");
    urlInput.removeAttribute("required");

    const submitButton = screen
      .getAllByRole("button")
      .find((b) => b.getAttribute("type") === "submit")!;
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("URL is required")).toBeInTheDocument();
    });
  });

  it("calls POST /resources with correct payload and auth header on submit", async () => {
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
      ok: true,
      json: () => Promise.resolve({ id: "123" }),
    });

    render(<NewResourcePage />);

    await waitFor(() => {
      expect(screen.getByText("Add New Resource")).toBeInTheDocument();
    });

    const urlInput = screen.getByLabelText("URL");
    const submitButton = screen
      .getAllByRole("button")
      .find((b) => b.getAttribute("type") === "submit")!;

    fireEvent.change(urlInput, {
      target: { value: "https://example.com/article" },
    });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith("http://localhost:8000/resources/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer mock-token",
        },
        body: JSON.stringify({
          content_type: "url",
          original_content: "https://example.com/article",
        }),
      });
    });
  });

  it("shows loading state during submission", async () => {
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
    (fetch as jest.Mock).mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({ ok: true, json: () => Promise.resolve({ id: "123" }) }),
            100,
          ),
        ),
    );

    render(<NewResourcePage />);

    await waitFor(() => {
      expect(screen.getByText("Add New Resource")).toBeInTheDocument();
    });

    const urlInput = screen.getByLabelText("URL");
    const submitButton = screen
      .getAllByRole("button")
      .find((b) => b.getAttribute("type") === "submit")!;

    fireEvent.change(urlInput, {
      target: { value: "https://example.com/article" },
    });
    fireEvent.click(submitButton);

    expect(screen.getByText("Submitting...")).toBeInTheDocument();
    expect(submitButton).toBeDisabled();
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
    (fetch as jest.Mock).mockResolvedValue({ ok: false, status: 401 });

    render(<NewResourcePage />);

    await waitFor(() => {
      expect(screen.getByText("Add New Resource")).toBeInTheDocument();
    });

    const urlInput = screen.getByLabelText("URL");
    const submitButton = screen
      .getAllByRole("button")
      .find((b) => b.getAttribute("type") === "submit")!;

    fireEvent.change(urlInput, {
      target: { value: "https://example.com/article" },
    });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(localStorage.removeItem).toHaveBeenCalledWith("auth_token");
      expect(localStorage.removeItem).toHaveBeenCalledWith("user_info");
      expect(mockPush).toHaveBeenCalledWith("/login");
    });
  });

  it("shows success message on successful submit", async () => {
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
      ok: true,
      json: () => Promise.resolve({ id: "123" }),
    });

    render(<NewResourcePage />);

    await waitFor(() => {
      expect(screen.getByText("Add New Resource")).toBeInTheDocument();
    });

    const urlInput = screen.getByLabelText("URL");
    const submitButton = screen
      .getAllByRole("button")
      .find((b) => b.getAttribute("type") === "submit")!;

    fireEvent.change(urlInput, {
      target: { value: "https://example.com/article" },
    });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(
        screen.getByText(
          "Resource submitted successfully! It will be processed in the background.",
        ),
      ).toBeInTheDocument();
    });
  });

  it("shows error message on API failure", async () => {
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
      status: 400,
      statusText: "Bad Request",
      json: () => Promise.resolve({ detail: "Invalid URL format" }),
    });

    render(<NewResourcePage />);

    await waitFor(() => {
      expect(screen.getByText("Add New Resource")).toBeInTheDocument();
    });

    const urlInput = screen.getByLabelText("URL");
    const submitButton = screen
      .getAllByRole("button")
      .find((b) => b.getAttribute("type") === "submit")!;

    fireEvent.change(urlInput, {
      target: { value: "https://example.com/article" },
    });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("Invalid URL format")).toBeInTheDocument();
    });
  });

  it("shows duplicate URL error message on 409 response", async () => {
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
      status: 409,
      statusText: "Conflict",
      json: () => Promise.resolve({ detail: "This resource has already been added." }),
    });

    render(<NewResourcePage />);

    await waitFor(() => {
      expect(screen.getByText("Add New Resource")).toBeInTheDocument();
    });

    const urlInput = screen.getByLabelText("URL");
    const submitButton = screen
      .getAllByRole("button")
      .find((b) => b.getAttribute("type") === "submit")!;

    fireEvent.change(urlInput, {
      target: { value: "https://example.com/duplicate-url" },
    });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("This resource has already been added.")).toBeInTheDocument();
    });
  });
});
