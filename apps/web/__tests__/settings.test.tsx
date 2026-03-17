import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { useRouter } from "next/navigation";
import { useMock } from "@/lib/mock/hooks";
import SettingsPage from "@/app/settings/page";

// Mock dependencies
jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
}));

jest.mock("@/lib/mock/hooks", () => ({
  useMock: jest.fn(),
}));

const mockRouter = {
  push: jest.fn(),
  back: jest.fn(),
  forward: jest.fn(),
  refresh: jest.fn(),
  replace: jest.fn(),
  prefetch: jest.fn(),
};

const mockUseMock = useMock as jest.MockedFunction<typeof useMock>;
const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>;

// Mock fetch globally
global.fetch = jest.fn();

describe("SettingsPage", () => {
  beforeEach(() => {
    mockUseRouter.mockReturnValue(mockRouter);
    mockRouter.push.mockClear();
    (global.fetch as jest.Mock).mockClear();
  });

  afterEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  describe("Authentication", () => {
    it("redirects to login when no auth token is present", async () => {
      mockUseMock.mockReturnValue(false);

      render(<SettingsPage />);

      await waitFor(() => {
        expect(mockRouter.push).toHaveBeenCalledWith("/login");
      });
    });

    it("redirects to login when user info is invalid", async () => {
      mockUseMock.mockReturnValue(false);
      localStorage.setItem("auth_token", "valid-token");
      localStorage.setItem("user_info", "invalid-json");

      render(<SettingsPage />);

      await waitFor(() => {
        expect(mockRouter.push).toHaveBeenCalledWith("/login");
      });
    });
  });

  describe("Mock Mode", () => {
    it("displays mock user data and accounts", async () => {
      mockUseMock.mockReturnValue(true);

      render(<SettingsPage />);

      await waitFor(() => {
        expect(screen.getByText("alex@learningspace.dev")).toBeInTheDocument();
        expect(screen.getByText("Alex Chen")).toBeInTheDocument();
      });

      // Check that GitHub account is shown as connected
      expect(screen.getByText("Connected as alexchen")).toBeInTheDocument();

      // Check that Google account is shown as connected
      expect(screen.getByText("Connected as alex@learningspace.dev")).toBeInTheDocument();

      // Check that Twitter is shown as not connected
      expect(screen.getByText("Not connected")).toBeInTheDocument();
    });

    it("shows mock unlink behavior", async () => {
      mockUseMock.mockReturnValue(true);

      // Mock alert
      window.alert = jest.fn();

      render(<SettingsPage />);

      await waitFor(() => {
        expect(screen.getByText("Alex Chen")).toBeInTheDocument();
      });

      // Click disconnect button for GitHub
      const disconnectButtons = screen.getAllByText("Disconnect");
      fireEvent.click(disconnectButtons[0]);

      expect(window.alert).toHaveBeenCalledWith("Mock: Would unlink GitHub account");
    });
  });

  describe("API Mode", () => {
    beforeEach(() => {
      mockUseMock.mockReturnValue(false);
      localStorage.setItem("auth_token", "valid-token");
      localStorage.setItem("user_info", JSON.stringify({
        id: "1",
        email: "test@example.com",
        display_name: "Test User",
      }));
    });

    it("fetches and displays user data successfully", async () => {
      const mockUserResponse = {
        id: "1",
        email: "test@example.com",
        display_name: "Test User",
        accounts: [
          {
            id: 1,
            provider: "github",
            provider_account_id: "testuser",
            created_at: "2026-03-17T10:00:00Z",
          }
        ],
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockUserResponse),
      });

      render(<SettingsPage />);

      await waitFor(() => {
        expect(screen.getByText("test@example.com")).toBeInTheDocument();
        expect(screen.getByText("Test User")).toBeInTheDocument();
        expect(screen.getByText("Connected as testuser")).toBeInTheDocument();
      });

      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8000/auth/me",
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: "Bearer valid-token",
          }),
        })
      );
    });

    it("handles 401 response by redirecting to login", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 401,
      });

      render(<SettingsPage />);

      await waitFor(() => {
        expect(mockRouter.push).toHaveBeenCalledWith("/login");
      });
    });

    it("handles API errors gracefully", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: "Internal Server Error",
      });

      render(<SettingsPage />);

      await waitFor(() => {
        expect(screen.getByText(/Failed to fetch user data/)).toBeInTheDocument();
      });
    });
  });

  describe("Account Management", () => {
    beforeEach(() => {
      mockUseMock.mockReturnValue(false);
      localStorage.setItem("auth_token", "valid-token");
      localStorage.setItem("user_info", JSON.stringify({
        id: "1",
        email: "test@example.com",
        display_name: "Test User",
      }));
    });

    it("shows connect button for unlinked accounts", async () => {
      const mockUserResponse = {
        id: "1",
        email: "test@example.com",
        display_name: "Test User",
        accounts: [],
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockUserResponse),
      });

      render(<SettingsPage />);

      await waitFor(() => {
        // All providers should show connect buttons
        expect(screen.getAllByText("Connect")).toHaveLength(3);
      });
    });

    it("handles successful account unlinking", async () => {
      const mockUserResponse = {
        id: "1",
        email: "test@example.com",
        display_name: "Test User",
        accounts: [
          {
            id: 1,
            provider: "github",
            provider_account_id: "testuser",
            created_at: "2026-03-17T10:00:00Z",
          },
          {
            id: 2,
            provider: "google",
            provider_account_id: "test@example.com",
            created_at: "2026-03-17T10:00:00Z",
          }
        ],
      };

      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: () => Promise.resolve(mockUserResponse),
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 204,
        });

      render(<SettingsPage />);

      await waitFor(() => {
        expect(screen.getByText("Connected as testuser")).toBeInTheDocument();
      });

      // Click disconnect for GitHub account
      const githubDisconnectButton = screen.getAllByText("Disconnect")[0];
      fireEvent.click(githubDisconnectButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          "http://localhost:8000/auth/accounts/1",
          expect.objectContaining({
            method: "DELETE",
            headers: expect.objectContaining({
              Authorization: "Bearer valid-token",
            }),
          })
        );
      });
    });

    it("handles CANNOT_UNLINK_LAST_ACCOUNT error", async () => {
      const mockUserResponse = {
        id: "1",
        email: "test@example.com",
        display_name: "Test User",
        accounts: [
          {
            id: 1,
            provider: "github",
            provider_account_id: "testuser",
            created_at: "2026-03-17T10:00:00Z",
          }
        ],
      };

      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: () => Promise.resolve(mockUserResponse),
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 400,
          json: () => Promise.resolve({
            code: "CANNOT_UNLINK_LAST_ACCOUNT",
            detail: "Cannot unlink last account",
          }),
        });

      render(<SettingsPage />);

      await waitFor(() => {
        expect(screen.getByText("Connected as testuser")).toBeInTheDocument();
      });

      // Try to disconnect the last account
      const disconnectButton = screen.getByText("Disconnect");
      fireEvent.click(disconnectButton);

      await waitFor(() => {
        expect(screen.getByText(/Cannot disconnect your last account/)).toBeInTheDocument();
      });
    });
  });

  describe("Provider Integration", () => {
    it("renders connect buttons for all providers when no accounts linked", async () => {
      mockUseMock.mockReturnValue(false);
      localStorage.setItem("auth_token", "valid-token");
      localStorage.setItem("user_info", JSON.stringify({
        id: "1",
        email: "test@example.com",
        display_name: "Test User",
      }));

      const mockUserResponse = {
        id: "1",
        email: "test@example.com",
        display_name: "Test User",
        accounts: [],
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockUserResponse),
      });

      render(<SettingsPage />);

      await waitFor(() => {
        expect(screen.getAllByText("Connect")).toHaveLength(3);
        expect(screen.getByText("GitHub")).toBeInTheDocument();
        expect(screen.getByText("Google")).toBeInTheDocument();
        expect(screen.getByText("X (Twitter)")).toBeInTheDocument();
      });
    });
  });
});