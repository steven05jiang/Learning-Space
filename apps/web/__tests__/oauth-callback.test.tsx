import { render, screen, waitFor } from "@testing-library/react";
import { useRouter, useSearchParams } from "next/navigation";
import OAuthCallbackContent from "../app/auth/callback/[provider]/OAuthCallbackContent";

// Mock Next.js navigation
jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
  useSearchParams: jest.fn(),
}));

// Mock environment variable
process.env.NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000";

const mockPush = jest.fn();
const mockGet = jest.fn();

beforeEach(() => {
  (useRouter as jest.Mock).mockReturnValue({
    push: mockPush,
  });
  (useSearchParams as jest.Mock).mockReturnValue({
    get: mockGet,
  });
});

describe("OAuthCallbackPage Integration Tests", () => {
  beforeEach(() => {
    localStorage.clear();
    (fetch as jest.MockedFunction<typeof fetch>).mockClear();
    mockPush.mockClear();
    mockGet.mockClear();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("successfully processes OAuth callback with valid state", async () => {
    // Set up stored state
    localStorage.setItem("oauth_state_github", "valid-state-token");

    // Mock search params
    mockGet.mockImplementation((param: string) => {
      if (param === "code") return "auth-code-123";
      if (param === "state") return "valid-state-token";
      return null;
    });

    // Mock successful backend response
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({
        access_token: "jwt-token-123",
        token_type: "bearer",
        user: {
          id: "user-123",
          email: "user@example.com",
          display_name: "Test User",
          avatar_url: "https://example.com/avatar.jpg",
        },
      }),
    };
    (fetch as jest.Mock).mockResolvedValue(mockResponse);

    render(<OAuthCallbackContent provider="github" />);

    // Should show loading state initially
    expect(screen.getByText("Completing Github login…")).toBeInTheDocument();

    // Wait for success state
    await waitFor(() => {
      expect(screen.getByText("Login successful!")).toBeInTheDocument();
    });

    // Verify API call was made correctly
    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8000/auth/callback/github?code=auth-code-123&state=valid-state-token",
    );

    // Verify tokens are stored
    expect(localStorage.getItem("auth_token")).toBe("jwt-token-123");
    expect(JSON.parse(localStorage.getItem("user_info") || "{}")).toEqual({
      id: "user-123",
      email: "user@example.com",
      display_name: "Test User",
      avatar_url: "https://example.com/avatar.jpg",
    });

    // Verify state is cleaned up
    expect(localStorage.getItem("oauth_state_github")).toBeNull();

    // Should redirect to dashboard after delay
    await waitFor(
      () => {
        expect(mockPush).toHaveBeenCalledWith("/dashboard");
      },
      { timeout: 2000 },
    );
  });

  it("rejects callback with invalid state (CSRF protection)", async () => {
    // Set up different stored state
    localStorage.setItem("oauth_state_github", "correct-state-token");

    // Mock search params with wrong state
    mockGet.mockImplementation((param: string) => {
      if (param === "code") return "auth-code-123";
      if (param === "state") return "malicious-state-token";
      return null;
    });

    render(<OAuthCallbackContent provider="github" />);

    // Should show error state
    await waitFor(() => {
      expect(screen.getByText("Authentication failed")).toBeInTheDocument();
      expect(
        screen.getByText("Invalid state parameter - possible CSRF attack"),
      ).toBeInTheDocument();
    });

    // Should not make API call
    expect(fetch).not.toHaveBeenCalled();

    // Should clean up state and redirect to login
    expect(localStorage.getItem("oauth_state_github")).toBeNull();
    await waitFor(
      () => {
        expect(mockPush).toHaveBeenCalledWith("/login?error=auth_failed");
      },
      { timeout: 4000 },
    );
  });

  it("rejects callback with missing state parameter", async () => {
    mockGet.mockImplementation((param: string) => {
      if (param === "code") return "auth-code-123";
      if (param === "state") return null; // Missing state
      return null;
    });

    render(<OAuthCallbackContent provider="github" />);

    await waitFor(() => {
      expect(screen.getByText("State parameter missing")).toBeInTheDocument();
    });

    expect(fetch).not.toHaveBeenCalled();
  });

  it("rejects callback with missing authorization code", async () => {
    localStorage.setItem("oauth_state_github", "valid-state-token");

    mockGet.mockImplementation((param: string) => {
      if (param === "code") return null; // Missing code
      if (param === "state") return "valid-state-token";
      return null;
    });

    render(<OAuthCallbackContent provider="github" />);

    await waitFor(() => {
      expect(
        screen.getByText("Authorization code not received"),
      ).toBeInTheDocument();
    });

    expect(fetch).not.toHaveBeenCalled();
  });

  it("handles backend authentication failure", async () => {
    localStorage.setItem("oauth_state_github", "valid-state-token");

    mockGet.mockImplementation((param: string) => {
      if (param === "code") return "auth-code-123";
      if (param === "state") return "valid-state-token";
      return null;
    });

    // Mock failed backend response
    const mockResponse = {
      ok: false,
      status: 400,
      json: jest.fn().mockResolvedValue({
        detail: "Invalid authorization code",
      }),
    };
    (fetch as jest.Mock).mockResolvedValue(mockResponse);

    render(<OAuthCallbackContent provider="github" />);

    await waitFor(() => {
      expect(screen.getByText("Authentication failed")).toBeInTheDocument();
      expect(
        screen.getByText("Invalid authorization code"),
      ).toBeInTheDocument();
    });

    // Should clean up state on error
    expect(localStorage.getItem("oauth_state_github")).toBeNull();
  });

  it("handles localStorage quota exceeded during token storage", async () => {
    localStorage.setItem("oauth_state_github", "valid-state-token");

    mockGet.mockImplementation((param: string) => {
      if (param === "code") return "auth-code-123";
      if (param === "state") return "valid-state-token";
      return null;
    });

    // Mock successful backend response
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({
        access_token: "jwt-token-123",
        token_type: "bearer",
        user: {
          id: "user-123",
          email: "user@example.com",
          display_name: "Test User",
        },
      }),
    };
    (fetch as jest.Mock).mockResolvedValue(mockResponse);

    // First call throws, subsequent calls succeed (no-op fine for test)
    let setItemCallCount = 0;
    jest.spyOn(Storage.prototype, "setItem").mockImplementation(function (key) {
      if (key === "auth_token" && setItemCallCount === 0) {
        setItemCallCount++;
        throw new Error("QuotaExceededError");
      }
      // no-op on retry — sufficient to verify component doesn't crash
    });

    const clearSpy = jest
      .spyOn(Storage.prototype, "clear")
      .mockImplementation(() => {});

    render(<OAuthCallbackContent provider="github" />);

    await waitFor(() => {
      expect(screen.getByText("Login successful!")).toBeInTheDocument();
    });

    // Should have cleared localStorage and retried
    expect(clearSpy).toHaveBeenCalled();
  });

  it("handles persistent localStorage quota exceeded error", async () => {
    localStorage.setItem("oauth_state_github", "valid-state-token");

    mockGet.mockImplementation((param: string) => {
      if (param === "code") return "auth-code-123";
      if (param === "state") return "valid-state-token";
      return null;
    });

    // Mock successful backend response
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({
        access_token: "jwt-token-123",
        token_type: "bearer",
        user: {
          id: "user-123",
          email: "user@example.com",
          display_name: "Test User",
        },
      }),
    };
    (fetch as jest.Mock).mockResolvedValue(mockResponse);

    // Mock localStorage.setItem to always throw
    jest.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("QuotaExceededError");
    });

    render(<OAuthCallbackContent provider="github" />);

    await waitFor(() => {
      expect(
        screen.getByText("Unable to save login session. Please try again."),
      ).toBeInTheDocument();
    });
  });

  it("redirects to /coming-soon when backend redirects non-allowlisted user", async () => {
    localStorage.setItem("oauth_state_github", "valid-state-token");

    mockGet.mockImplementation((param: string) => {
      if (param === "code") return "auth-code-123";
      if (param === "state") return "valid-state-token";
      return null;
    });

    // Simulate backend 302 → /coming-soon: fetch follows redirect,
    // lands on the HTML page (ok: true, redirected: true).
    // response.json() must NOT be called — the fix returns early.
    const mockJsonFn = jest.fn().mockRejectedValue(
      new SyntaxError("Unexpected token '<', \"<!DOCTYPE \"... is not valid JSON"),
    );
    const mockResponse = {
      ok: true,
      redirected: true,
      url: "http://localhost:3000/coming-soon",
      json: mockJsonFn,
    };
    (fetch as jest.Mock).mockResolvedValue(mockResponse);

    render(<OAuthCallbackContent provider="github" />);

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/coming-soon");
    });

    // Must not attempt JSON parse on the HTML body
    expect(mockJsonFn).not.toHaveBeenCalled();

    // Must not show any error to the user
    expect(screen.queryByText("Authentication failed")).not.toBeInTheDocument();
  });

  it("shows loading state initially", () => {
    localStorage.setItem("oauth_state_github", "valid-state-token");

    mockGet.mockImplementation((param: string) => {
      if (param === "code") return "auth-code-123";
      if (param === "state") return "valid-state-token";
      return null;
    });
    (fetch as jest.Mock).mockImplementation(() => new Promise(() => {})); // never resolves

    render(<OAuthCallbackContent provider="github" />);

    expect(screen.getByText("Completing Github login…")).toBeInTheDocument();
    expect(
      screen.getByText("Please wait while we authenticate your account."),
    ).toBeInTheDocument();
  });
});
